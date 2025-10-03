from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Content, Chunk
from app.adapters import webdav
from pydantic import BaseModel
from typing import List
import logging
import os
import uuid
from pathlib import Path
from app.workers.tasks import ingest_file as ingest_task, generate_embeddings, simple_chunk, classify_content
from app.parsers.document_processor import DocumentProcessor

router = APIRouter()
log = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# simple_chunk 函数已移动到 workers/tasks.py 中

@router.post("/memo")
def ingest_memo(item: dict, db: Session = Depends(get_db)):
    title = item.get("title") or "memo"
    text  = item.get("text") or ""
    meta  = item.get("meta", {})
    
    # 确定文档类型
    detected_type = meta.get("detected_type", "text")
    modality = 'image' if detected_type == 'image' else 'text'
    
    content = Content(
        title=title, 
        text=text, 
        modality=modality,
        meta=meta, 
        source_uri=item.get("source_uri"), 
        created_by="memo.api"
    )
    db.add(content); db.commit(); db.refresh(content)

    # 切片并入库
    seq = 0
    chunk_ids = []
    for t in simple_chunk(text):
        chunk = Chunk(content_id=content.id, seq=seq, text=t, meta={"source_uri": content.source_uri})
        db.add(chunk)
        seq += 1
    db.commit()
    
    # 获取新创建的 chunk IDs
    db.refresh(content)
    chunk_ids = [str(chunk.id) for chunk in content.chunks]
    
    # 异步生成 embeddings
    if chunk_ids:
        generate_embeddings.delay(chunk_ids)
    
    # 立即进行快速分类（异步，最高优先级）
    from app.workers.quick_tasks import quick_classify_content
    quick_classify_content.apply_async(
        args=[str(content.id)], 
        queue="quick", 
        priority=10,  # 提高优先级确保先执行
        countdown=1
    )
    
    # 智能合集匹配 - 优先同步执行以确保立即生效
    try:
        from app.services.collection_matching_service import CollectionMatchingService
        matching_service = CollectionMatchingService(db)
        matched = matching_service.match_document_to_collections(str(content.id))
        log.info(f"Synchronously matched content {content.id} to {len(matched)} collections")
        
        # 异步任务作为备份（如果同步执行成功，这个任务会快速跳过）
        from app.workers.quick_tasks import match_document_to_collections
        match_document_to_collections.apply_async(
            args=[str(content.id)],
            queue="quick",
            priority=8,
            countdown=8   # 作为备份，延迟8秒执行
        )
        
    except Exception as e:
        log.error(f"Synchronous collection matching failed for {content.id}: {e}")
        # 如果同步失败，依赖异步任务
        try:
            from app.workers.quick_tasks import match_document_to_collections
            match_document_to_collections.apply_async(
                args=[str(content.id)],
                queue="quick",
                priority=9,
                countdown=2  # 更短的延迟
            )
            log.info(f"Fallback: Scheduled async collection matching for content {content.id}")
        except Exception as async_e:
            log.error(f"Both sync and async collection matching failed: {async_e}")
    
    # 异步进行精确AI分类（最后执行，覆盖快速分类）
    classify_content.apply_async(
        args=[str(content.id)], 
        queue="classify", 
        priority=5,
        countdown=6   # 延迟6秒，确保前面的任务都完成
    )
    
    return {"status":"ok","content_id":str(content.id),"chunks":seq}

@router.post("/scan")
def ingest_scan(db: Session = Depends(get_db)):
    """
    扫描 Nextcloud WebDAV 的 PKB-Inbox，检查去重后入库，并清理已删除的文件
    """
    docs = webdav.scan_inbox()
    total_chunks = 0
    all_chunk_ids = []
    new_content_ids = []
    new_files = 0
    skipped_files = 0
    deleted_files = 0
    
    # 获取当前扫描到的所有文件的 source_uri
    current_source_uris = {d["source_uri"] for d in docs}
    
    # 查找数据库中所有来自 webdav 的内容
    existing_contents = db.query(Content).filter(
        Content.source_uri.like("nextcloud://%")
    ).all()
    
    # 识别需要删除的内容（在数据库中但不在当前扫描结果中）
    for existing_content in existing_contents:
        if existing_content.source_uri not in current_source_uris:
            log.info(f"File deleted from Nextcloud, removing from database: {existing_content.title}")
            
            # 删除相关的分类关联
            from app.models import ContentCategory
            db.query(ContentCategory).filter(
                ContentCategory.content_id == existing_content.id
            ).delete()
            
            # 删除相关的 chunks（会自动删除 embeddings）
            db.query(Chunk).filter(
                Chunk.content_id == existing_content.id
            ).delete()
            
            # 删除内容记录
            db.delete(existing_content)
            deleted_files += 1
    
    db.commit()
    
    # 处理新文件
    for d in docs:
        # 检查文件是否已经存在（基于 source_uri）
        existing_content = db.query(Content).filter(
            Content.source_uri == d["source_uri"]
        ).first()
        
        if existing_content:
            log.info(f"File already exists, skipping: {d['title']}")
            skipped_files += 1
            continue
        
        # 检查是否是用户主动删除的文件（通过删除记录检查）
        from app.models import OpsLog
        from sqlalchemy import text
        
        # 使用原生 SQL 查询来检查 JSON 字段
        delete_record = db.query(OpsLog).filter(
            OpsLog.op_type == "user_delete",
            text("payload->>'source_uri' = :source_uri"),
            OpsLog.status == "completed"
        ).params(source_uri=d["source_uri"]).first()
        
        if delete_record:
            log.info(f"File was user-deleted, skipping re-creation: {d['title']}")
            skipped_files += 1
            continue
        
        # 确定文档类型
        detected_type = d.get("metadata", {}).get("detected_type", "text")
        modality = 'image' if detected_type == 'image' else 'text'
        
        # 创建新的内容记录
        content = Content(
            title=d["title"], 
            text=d["text"],
            modality=modality,
            meta=d.get("metadata", {}), 
            source_uri=d["source_uri"], 
            created_by="webdav.scan"
        )
        db.add(content)
        db.commit()
        db.refresh(content)
        new_files += 1
        new_content_ids.append(str(content.id))

        # 文本分块
        seq = 0
        for t in simple_chunk(d["text"]):
            chunk = Chunk(
                content_id=content.id, 
                seq=seq, 
                text=t, 
                meta={"source_uri": content.source_uri}
            )
            db.add(chunk)
            seq += 1
        db.commit()
        
        # 收集新创建的 chunk IDs
        db.refresh(content)
        chunk_ids = [str(chunk.id) for chunk in content.chunks]
        all_chunk_ids.extend(chunk_ids)
        total_chunks += seq
        
        log.info(f"Processed new file: {d['title']} ({seq} chunks)")
    
    # 异步生成 embeddings（仅为新文档）
    if all_chunk_ids:
        generate_embeddings.delay(all_chunk_ids)
    
    # 处理新文档的分类和图片处理
    if new_content_ids:
        # 分离图片和非图片内容
        image_content_ids = []
        text_content_ids = []
        
        for content_id in new_content_ids:
            content = db.query(Content).filter(Content.id == content_id).first()
            if content and content.modality == 'image' and content.meta.get("processing_status") == "pending":
                image_content_ids.append(content_id)
            else:
                text_content_ids.append(content_id)
        
        # 立即批量快速分类非图片文档
        if text_content_ids:
            from app.workers.quick_tasks import batch_quick_classify
            batch_quick_classify.apply_async(
                args=[text_content_ids], 
                queue="quick", 
                priority=9
            )
            
            # 延迟进行精确AI分类
            from app.workers.tasks import batch_classify_contents
            batch_classify_contents.apply_async(
                args=[text_content_ids, True],  # force_reclassify=True
                queue="classify", 
                priority=5,
                countdown=30
            )
        
        # 异步处理图片文件
        if image_content_ids:
            from app.workers.tasks import process_image_content
            for content_id in image_content_ids:
                process_image_content.apply_async(
                    args=[content_id],
                    queue="heavy",
                    priority=3,
                    countdown=5  # 5秒后开始处理
                )
    
    return {
        "status": "ok",
        "files_scanned": len(docs),
        "new_files": new_files,
        "skipped_files": skipped_files,
        "deleted_files": deleted_files,
        "new_chunks": total_chunks
    }

class IngestRequest(BaseModel):
    path: str

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """单文件上传接口"""
    return await _process_single_file(file, db)

@router.post("/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """
    多文件批量上传接口
    """
    try:
        results = []
        
        # 验证文件数量限制
        if len(files) > 20:  # 限制最多20个文件
            raise HTTPException(
                status_code=400,
                detail="一次最多只能上传20个文件"
            )
        
        # 验证总文件大小
        total_size = sum(file.size for file in files if file.size)
        max_total_size = 500 * 1024 * 1024  # 500MB
        if total_size > max_total_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件总大小不能超过500MB，当前：{total_size / 1024 / 1024:.1f}MB"
            )
        
        # 处理每个文件
        for i, file in enumerate(files):
            try:
                result = await _process_single_file(file, db)
                results.append({
                    "index": i,
                    "filename": file.filename,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                log.error(f"Failed to process file {file.filename}: {e}")
                results.append({
                    "index": i,
                    "filename": file.filename,
                    "status": "error",
                    "error": str(e)
                })
        
        # 统计结果
        success_count = len([r for r in results if r["status"] == "success"])
        error_count = len([r for r in results if r["status"] == "error"])
        
        return {
            "status": "completed",
            "total_files": len(files),
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
            "message": f"批量上传完成：{success_count}个成功，{error_count}个失败"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Batch upload error: {e}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")

async def _process_single_file(file: UploadFile, db: Session):
    """
    WebUI文件上传接口 - 立即入库，异步处理
    """
    try:
        # 1. 验证文件类型
        processor = DocumentProcessor()
        if not processor.is_supported(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file.filename}"
            )
        
        # 2. 保存文件到持久化目录
        upload_dir = Path("/app/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用原始文件名，处理重名冲突
        def get_unique_filename(upload_dir: Path, original_filename: str) -> str:
            """生成唯一文件名，重名时添加时间戳"""
            base_path = upload_dir / original_filename
            
            if not base_path.exists():
                return original_filename
            
            # 生成时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_part = Path(original_filename).stem
            extension = Path(original_filename).suffix
            
            return f"{name_part}_{timestamp}{extension}"
        
        actual_filename = get_unique_filename(upload_dir, file.filename)
        temp_file_path = upload_dir / actual_filename
        
        # 保存上传的文件
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 2.5. 如果是图片文件，立即预生成缩略图
        try:
            from app.api.files import pregenerate_thumbnail_if_image
            if pregenerate_thumbnail_if_image(Path(temp_file_path)):
                log.info(f"Pre-generated thumbnail for uploaded image: {actual_filename}")
        except Exception as e:
            log.warning(f"Failed to pre-generate thumbnail for {actual_filename}: {e}")
        
        # 3. 立即解析文件内容
        try:
            parsed_result = processor.process_file(str(temp_file_path))
            file_text = parsed_result.get("text", "")
            file_metadata = parsed_result.get("metadata", {})
        except Exception as e:
            log.error(f"文件解析失败: {e}")
            file_text = ""
            file_metadata = {"parse_error": str(e)}
        
        # 4. 立即创建Content记录（processing状态）
        content_record = Content(
            title=file.filename,  # 始终保存用户原始文件名
            text=file_text,
            modality='image' if file_metadata.get('detected_type') == 'image' else 'text',
            meta={
                **file_metadata,
                "source_type": "webui",
                "classification_status": "pending",  # 分类状态
                "show_classification": False,        # 是否向前端显示分类结果
                "processing_status": "processing",
                "file_size": len(content),
                "file_path": str(temp_file_path),     # 保存实际文件路径
                "original_filename": file.filename,   # 用户上传的原始文件名
                "stored_filename": actual_filename,   # 实际存储的文件名
                "upload_timestamp": str(uuid.uuid4())  # 临时用作唯一标识
            },
            source_uri=f"webui://{actual_filename}",  # 使用实际存储的文件名
            created_by="webui.upload"
        )
        
        db.add(content_record)
        db.commit()
        db.refresh(content_record)
        
        # 5. 立即进行文本分块
        chunk_ids = []
        if file_text:
            seq = 0
            for chunk_text in simple_chunk(file_text):
                chunk = Chunk(
                    content_id=content_record.id,
                    seq=seq,
                    text=chunk_text,
                    meta={"source_uri": content_record.source_uri}
                )
                db.add(chunk)
                seq += 1
            
            db.commit()
            db.refresh(content_record)
            chunk_ids = [str(chunk.id) for chunk in content_record.chunks]
        
        # 6. 异步处理任务（高优先级）
        # 生成向量embeddings
        if chunk_ids:
            generate_embeddings.apply_async(
                args=[chunk_ids],
                queue="heavy",
                priority=8
            )
        
        # 方案A：并行执行，6秒内完成所有分类任务
        
        # 快速分类（1秒后执行，后台执行不显示给用户）
        from app.workers.quick_tasks import quick_classify_content
        quick_classify_content.apply_async(
            args=[str(content_record.id)],
            queue="quick",
            priority=10,  # 最高优先级
            countdown=1   # 1秒后执行
        )
        
        # AI精确分类（2秒后执行，与快速分类并行）
        classify_content.apply_async(
            args=[str(content_record.id)],
            queue="classify",
            priority=9,   # 高优先级
            countdown=2   # 2秒后执行，与快速分类并行
        )
        
        # 智能合集匹配（5秒后执行，基于AI分类结果）
        from app.workers.quick_tasks import match_document_to_collections
        match_document_to_collections.apply_async(
            args=[str(content_record.id)],
            queue="quick",
            priority=8,   # 次高优先级
            countdown=5   # 5秒后执行，基于AI分类结果
        )
        
        # 7. 保留文件（持久化存储，不删除）
        # 文件现在保存在持久化目录中，不需要删除
        
        # 8. 返回结果
        return {
            "status": "success",
            "content_id": str(content_record.id),
            "title": file.filename,
            "processing_status": "processing",
            "chunks_created": len(chunk_ids),
            "file_size": len(content),
            "message": "文件上传成功，正在后台处理分类..."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/status/{content_id}")
def get_processing_status(content_id: str, db: Session = Depends(get_db)):
    """
    查询文件处理状态和分类状态
    """
    try:
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取分类状态信息
        classification_status = content.meta.get("classification_status", "pending") if content.meta else "pending"
        show_classification = content.meta.get("show_classification", False) if content.meta else False
        processing_status = content.meta.get("processing_status", "unknown") if content.meta else "unknown"
        
        # 检查分类结果
        from app.models import ContentCategory
        categories = db.query(ContentCategory).filter(
            ContentCategory.content_id == content_id
        ).all()
        
        # 构建返回结果
        result = {
            "content_id": content_id,
            "title": content.title,
            "processing_status": processing_status,
            "classification_status": classification_status,
            "show_classification": show_classification,
            "created_at": content.created_at.isoformat() if content.created_at else None
        }
        
        # 只有在允许显示分类时才返回分类信息
        if show_classification and categories:
            result["categories"] = [
                {
                    "id": str(cat.category_id),
                    "name": cat.category.name if cat.category else "Unknown",
                    "confidence": cat.confidence,
                    "reasoning": cat.reasoning
                }
                for cat in categories
            ]
        else:
            result["categories"] = []
            result["message"] = "分类中..." if classification_status == "pending" else "分类处理中"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"查询状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询状态失败: {str(e)}")

@router.post("/file")
async def ingest_file_endpoint(req: IngestRequest):
    log.info("INGEST schedule: %s", req.path)
    result = ingest_task.apply_async(args=[req.path], queue="ingest")
    payload = {"task_id": str(result.id), "message": f"File {req.path} scheduled for ingest"}
    return JSONResponse(content=payload, status_code=202)

