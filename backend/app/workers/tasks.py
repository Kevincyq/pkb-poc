from .celery_app import celery_app
from app.db import SessionLocal
from app.models import Chunk, Content
from app.services.embedding_service import EmbeddingService
from app.services.category_service import CategoryService
from app.parsers.document_processor import DocumentProcessor
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# 文档分块函数
def simple_chunk(text: str, max_len: int = 700):
    """
    简单的文本分块函数
    
    Args:
        text: 要分块的文本
        max_len: 每块最大长度
        
    Returns:
        文本块列表
    """
    if not text:
        return []
    
    buf, chunks = [], []
    for line in text.splitlines():
        if len("".join(buf)) + len(line) > max_len:
            if buf:
                chunks.append("\n".join(buf))
                buf = []
        buf.append(line)
    
    if buf:
        chunks.append("\n".join(buf))
    
    return [c.strip() for c in chunks if c.strip()]

# 入口任务：处理文件摄取
@celery_app.task(name="app.workers.tasks.ingest_file", queue="ingest")
def ingest_file(path: str):
    """
    处理文件摄取任务
    支持本地文件和 WebDAV 文件的解析和入库
    
    Args:
        path: 文件路径（本地路径或 WebDAV URL）
        
    Returns:
        处理结果字典
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting file ingestion for: {path}")
        
        # 检查文件是否存在（本地文件）
        if not path.startswith(('http://', 'https://')) and not os.path.exists(path):
            error_msg = f"File not found: {path}"
            logger.error(error_msg)
            return {"ok": False, "error": error_msg}
        
        # 初始化文档处理器
        processor = DocumentProcessor()
        
        # 处理文件
        if path.startswith(('http://', 'https://')):
            # WebDAV 文件处理
            filename = Path(path).name
            from app.adapters.webdav import download_and_parse_file
            parse_result = download_and_parse_file(path, filename)
        else:
            # 本地文件处理
            parse_result = processor.process_file(path)
        
        # 检查解析结果
        if not parse_result.get('success', True):
            error_msg = f"Failed to parse file: {parse_result.get('metadata', {}).get('error', 'Unknown error')}"
            logger.error(error_msg)
            return {"ok": False, "error": error_msg}
        
        text_content = parse_result.get('text', '')
        if not text_content.strip():
            error_msg = f"No text content extracted from file: {path}"
            logger.warning(error_msg)
            return {"ok": False, "error": error_msg}
        
        # 创建 Content 记录
        filename = parse_result.get('metadata', {}).get('filename', Path(path).name)
        title = parse_result.get('metadata', {}).get('title', filename)
        
        # 确定文档类型
        detected_type = parse_result.get('metadata', {}).get('detected_type', 'text')
        modality = 'image' if detected_type == 'image' else 'text'
        
        content = Content(
            title=title,
            text=text_content,
            modality=modality,
            meta=parse_result.get('metadata', {}),
            source_uri=f"file://{path}",
            created_by="celery.ingest"
        )
        
        db.add(content)
        db.commit()
        db.refresh(content)
        
        # 文本分块
        chunks = simple_chunk(text_content)
        chunk_ids = []
        
        for seq, chunk_text in enumerate(chunks):
            chunk = Chunk(
                content_id=content.id,
                seq=seq,
                text=chunk_text,
                meta={
                    "source_uri": content.source_uri,
                    "chunk_index": seq,
                    "total_chunks": len(chunks)
                }
            )
            db.add(chunk)
            chunk_ids.append(chunk.id)
        
        db.commit()
        
        # 立即进行快速分类（高优先级）
        from app.workers.quick_tasks import quick_classify_content
        quick_classify_content.apply_async(
            args=[str(content.id)], 
            queue="quick", 
            priority=9
        )
        
        # 异步生成 embeddings
        if chunk_ids:
            chunk_ids_str = [str(cid) for cid in chunk_ids]
            generate_embeddings.delay(chunk_ids_str)
        
        # 异步进行精确AI分类（较低优先级，会覆盖快速分类）
        classify_content.apply_async(
            args=[str(content.id)], 
            queue="classify", 
            priority=5,
            countdown=30  # 延迟30秒执行，让用户先看到快速分类结果
        )
        
        result = {
            "ok": True,
            "content_id": str(content.id),
            "chunks_created": len(chunks),
            "title": title,
            "text_length": len(text_content),
            "file_type": parse_result.get('metadata', {}).get('detected_type', 'unknown')
        }
        
        logger.info(f"Successfully ingested file {path}: {len(chunks)} chunks created")
        return result
        
    except Exception as e:
        logger.error(f"Error ingesting file {path}: {e}")
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()

# 生成 embedding 的后台任务
@celery_app.task(name="app.workers.tasks.generate_embeddings", queue="heavy")
def generate_embeddings(chunk_ids: list):
    """
    为指定的 chunks 生成 embedding
    """
    db = SessionLocal()
    embedding_service = EmbeddingService()
    
    try:
        if not embedding_service.is_enabled():
            logger.warning("Embedding service not available")
            return {"ok": False, "error": "Embedding service not configured"}
        
        # 获取需要处理的 chunks
        chunks = db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
        
        if not chunks:
            return {"ok": True, "processed": 0}
        
        # 批量生成 embeddings
        texts = [chunk.text for chunk in chunks]
        embeddings = embedding_service.batch_get_embeddings(texts)
        
        # 更新数据库
        processed_count = 0
        for chunk, embedding in zip(chunks, embeddings):
            if embedding:
                chunk.embedding = embedding
                chunk.char_count = len(chunk.text)
                chunk.token_count = int(len(chunk.text.split()) * 1.3)  # 简单估算
                processed_count += 1
        
        db.commit()
        
        logger.info(f"Generated embeddings for {processed_count} chunks")
        return {"ok": True, "processed": processed_count}
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()

# 可以添加其他处理任务，如文档解析、OCR等
@celery_app.task(name="app.workers.tasks.process_document", queue="heavy")
def process_document(content_id: str, doc_type: str = "text"):
    """
    处理文档的后台任务，如OCR、格式转换等
    """
    logger.info(f"process_document called with content_id: {content_id}, type: {doc_type}")
    return {"ok": True, "content_id": content_id, "processed": True}

@celery_app.task(name="app.workers.tasks.classify_content", queue="classify")
def classify_content(content_id: str):
    """
    对内容进行智能分类
    
    Args:
        content_id: 内容ID
        
    Returns:
        分类结果
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting classification for content: {content_id}")
        
        # 初始化分类服务
        category_service = CategoryService(db)
        
        # 确保系统分类已初始化
        category_service.initialize_system_categories()
        
        # 执行分类
        result = category_service.classify_content(content_id)
        
        if result["success"]:
            logger.info(f"Successfully classified content {content_id} as {result.get('category_name', 'unknown')}")
        else:
            logger.error(f"Failed to classify content {content_id}: {result.get('error', 'unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in classify_content task for {content_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="app.workers.tasks.batch_classify_contents", queue="classify")
def batch_classify_contents(content_ids: list, force_reclassify: bool = False):
    """
    批量分类内容
    
    Args:
        content_ids: 内容ID列表
        force_reclassify: 是否强制重新分类
        
    Returns:
        批量分类结果
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting batch classification for {len(content_ids)} contents")
        
        # 初始化分类服务
        category_service = CategoryService(db)
        
        # 确保系统分类已初始化
        category_service.initialize_system_categories()
        
        # 执行批量分类
        result = category_service.batch_classify(content_ids, force_reclassify)
        
        logger.info(f"Batch classification completed: {result['success']} success, {result['failed']} failed")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in batch_classify_contents task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="app.workers.tasks.process_image_content", queue="heavy")
def process_image_content(content_id: str):
    """
    异步处理图片内容
    
    Args:
        content_id: 内容ID
        
    Returns:
        处理结果
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting image processing for content: {content_id}")
        
        # 获取内容记录
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            logger.error(f"Content not found: {content_id}")
            return {"success": False, "error": "Content not found"}
        
        # 检查是否需要处理
        current_status = content.meta.get("processing_status")
        if current_status == "completed":
            logger.info(f"Content {content_id} already processed")
            return {"success": True, "status": "already_processed"}
        
        # 更新为处理中状态
        content.meta["processing_status"] = "processing"
        content.updated_at = datetime.utcnow()
        db.commit()
        
        # 获取下载URL
        download_url = content.meta.get("download_url")
        if not download_url:
            logger.error(f"No download URL for content {content_id}")
            return {"success": False, "error": "No download URL"}
        
        # 下载并解析图片
        logger.info(f"Processing image content: {content.title}")
        from app.adapters.webdav import download_and_parse_file
        parse_result = download_and_parse_file(download_url, content.title)
        
        if parse_result.get('success', True) and parse_result.get('text'):
            # 更新内容
            content.text = parse_result['text']
            content.meta.update(parse_result.get('metadata', {}))
            content.meta["processing_status"] = "completed"
            content.updated_at = datetime.utcnow()
            
            # 重新分块
            # 删除旧的chunks
            db.query(Chunk).filter(Chunk.content_id == content.id).delete()
            
            # 创建新的chunks
            seq = 0
            chunk_ids = []
            for t in simple_chunk(parse_result['text']):
                chunk = Chunk(
                    content_id=content.id,
                    seq=seq,
                    text=t,
                    meta={"source_uri": content.source_uri}
                )
                db.add(chunk)
                seq += 1
            
            db.commit()
            
            # 获取新的chunk IDs
            db.refresh(content)
            chunk_ids = [str(chunk.id) for chunk in content.chunks]
            
            # 异步生成embeddings
            if chunk_ids:
                generate_embeddings.delay(chunk_ids)
            
            # 触发分类
            from app.workers.quick_tasks import quick_classify_content
            quick_classify_content.apply_async(
                args=[str(content.id)], 
                queue="quick", 
                priority=9
            )
            
            classify_content.apply_async(
                args=[str(content.id)], 
                queue="classify", 
                priority=5,
                countdown=30
            )
            
            logger.info(f"Successfully processed image content: {content.title}")
            return {"success": True, "chunks": seq}
        else:
            # 处理失败
            content.meta["processing_status"] = "failed"
            content.meta["error"] = parse_result.get('metadata', {}).get('error', 'Unknown error')
            db.commit()
            
            logger.error(f"Failed to process image content: {content.title}")
            return {"success": False, "error": content.meta.get("error")}
            
    except Exception as e:
        logger.error(f"Error in process_image_content task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()
