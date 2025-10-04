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
    # MVP限制：验证单个文件大小
    max_single_size = 20 * 1024 * 1024  # 20MB
    if file.size and file.size > max_single_size:
        raise HTTPException(
            status_code=400,
            detail=f"MVP阶段单个文件不能超过20MB，当前文件 {file.filename} 大小为 {file.size / 1024 / 1024:.1f}MB"
        )
    
    return await _process_single_file(file, db)

@router.post("/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """
    多文件批量上传接口
    """
    try:
        results = []
        
        # MVP限制：验证文件数量限制
        if len(files) > 5:  # MVP阶段限制最多5个文件
            raise HTTPException(
                status_code=400,
                detail="MVP阶段一次最多只能上传5个文件"
            )
        
        # MVP限制：验证单个文件大小
        max_single_size = 20 * 1024 * 1024  # 20MB
        oversized_files = [f for f in files if f.size and f.size > max_single_size]
        if oversized_files:
            oversized_names = [f"{f.filename}({f.size / 1024 / 1024:.1f}MB)" for f in oversized_files]
            raise HTTPException(
                status_code=400,
                detail=f"MVP阶段单个文件不能超过20MB，以下文件超限：{', '.join(oversized_names)}"
            )
        
        # MVP限制：验证总文件大小
        total_size = sum(file.size for file in files if file.size)
        max_total_size = 100 * 1024 * 1024  # 100MB (5个文件×20MB)
        if total_size > max_total_size:
            raise HTTPException(
                status_code=400,
                detail=f"MVP阶段批量上传总大小不能超过100MB，当前：{total_size / 1024 / 1024:.1f}MB"
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
        
        # 3. 快速检测文件类型和基本信息（同步，快速）
        file_size = len(content)
        file_extension = Path(file.filename).suffix.lower()
        
        # 判断文件类型
        is_image = file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        is_large_file = file_size > 10 * 1024 * 1024  # 10MB
        
        # 基本元数据（不需要解析文件内容）
        basic_metadata = {
            "source_type": "webui",
            "file_size": file_size,
            "file_extension": file_extension,
            "is_image": is_image,
            "is_large_file": is_large_file,
            "upload_timestamp": str(uuid.uuid4())
        }
        
        log.info(f"📁 File uploaded: {file.filename} ({file_size/1024/1024:.1f}MB, {'image' if is_image else 'document'})")
        
        # 4. 立即创建Content记录（上传完成，等待解析）
        content_record = Content(
            title=file.filename,  # 始终保存用户原始文件名
            text="",  # 文本内容将在异步解析后填充
            modality='image' if is_image else 'text',
            meta={
                **basic_metadata,
                "classification_status": "pending",     # 分类状态
                "show_classification": True,            # 🔥 关键修复：立即允许显示状态
                "processing_status": "uploaded",        # 上传完成，等待解析
                "parsing_status": "pending",            # 解析状态
                "file_path": str(temp_file_path),       # 保存实际文件路径
                "original_filename": file.filename,     # 用户上传的原始文件名
                "stored_filename": actual_filename,     # 实际存储的文件名
            },
            source_uri=f"webui://{actual_filename}",  # 使用实际存储的文件名
            created_by="webui.upload"
        )
        
        db.add(content_record)
        db.commit()
        db.refresh(content_record)
        
        # 5. 异步任务调度 - 优化时序和优先级
        content_id = str(content_record.id)
        
        # 立即调度文件解析任务（最高优先级）
        from app.workers.tasks import parse_and_chunk_file
        parse_and_chunk_file.apply_async(
            args=[content_id, str(temp_file_path)],
            queue="quick",
            priority=10,  # 最高优先级
            countdown=0.1  # 几乎立即执行
        )
        
        log.info(f"🚀 Scheduled parsing for content {content_id}: {file.filename}")
        
        # 6. 图片文件特殊处理
        if is_image:
            # 异步生成缩略图
            from app.workers.tasks import generate_image_thumbnail
            generate_image_thumbnail.apply_async(
                args=[content_id, str(temp_file_path)],
                queue="heavy",
                priority=7,
                countdown=0.5
            )
        
        # 7. 分类任务链 - 优化执行顺序确保完整分类
        # 快速分类（2秒后执行，给解析任务时间）
        from app.workers.quick_tasks import quick_classify_content
        quick_classify_content.apply_async(
            args=[content_id],
            queue="quick",
            priority=9,
            countdown=2  # 等待解析完成
        )
        
        # AI精确分类（4秒后执行）
        classify_content.apply_async(
            args=[content_id],
            queue="classify",
            priority=8,
            countdown=4
        )
        
        # 🔥 关键修复：智能合集匹配在AI分类完成后执行
        from app.workers.quick_tasks import match_document_to_collections
        match_document_to_collections.apply_async(
            args=[content_id],
            queue="quick",
            priority=7,
            countdown=10  # 确保AI分类完成后再执行（4s启动 + 3s执行 + 2s缓冲）
        )
        
        # 8. 返回结果 - 立即响应
        return {
            "status": "success",
            "content_id": content_id,
            "title": file.filename,
            "processing_status": "uploaded",  # 上传完成
            "parsing_status": "pending",      # 等待解析
            "file_size": file_size,
            "file_type": "image" if is_image else "document",
            "estimated_processing_time": 3 if is_image else (8 if is_large_file else 5),  # 预估处理时间（秒）
            "message": f"文件上传成功！{'图片' if is_image else '文档'}正在后台解析和分类..."
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
        
        # 获取详细状态信息
        meta = content.meta or {}
        classification_status = meta.get("classification_status", "pending")
        show_classification = meta.get("show_classification", False)
        processing_status = meta.get("processing_status", "unknown")
        parsing_status = meta.get("parsing_status", "pending")
        
        # 智能状态判断：如果解析完成但分类未开始，显示分类中
        if parsing_status == "completed" and classification_status == "pending":
            classification_status = "quick_processing"
        
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
            "parsing_status": parsing_status,
            "classification_status": classification_status,
            "show_classification": show_classification,
            "file_type": meta.get("file_type", "document"),
            "file_size": meta.get("file_size", 0),
            "estimated_time": meta.get("estimated_processing_time", 5),
            "created_at": content.created_at.isoformat() if content.created_at else None
        }
        
        # 只有在允许显示分类时才返回分类信息
        if show_classification and categories:
            # 分离主分类和次要分类
            primary_categories = []
            secondary_categories = []
            
            for cat in categories:
                category_info = {
                    "id": str(cat.category_id),
                    "name": cat.category.name if cat.category else "Unknown",
                    "confidence": cat.confidence,
                    "reasoning": cat.reasoning,
                    "role": cat.role,
                    "source": cat.source
                }
                
                if cat.role == "primary_system":
                    primary_categories.append(category_info)
                elif cat.role == "secondary_system":
                    secondary_categories.append(category_info)
                else:
                    # 其他角色（如用户规则）也包含在内
                    primary_categories.append(category_info)
            
            result["categories"] = primary_categories + secondary_categories
            result["primary_categories"] = primary_categories
            result["secondary_categories"] = secondary_categories
        else:
            result["categories"] = []
            result["primary_categories"] = []
            result["secondary_categories"] = []
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

