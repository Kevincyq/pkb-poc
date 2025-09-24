"""
文档处理 API
提供文档上传、解析、格式检查等接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import logging
import uuid

from app.db import SessionLocal
from app.services.document_service import DocumentService
from app.models import Content, Chunk, ContentCategory

router = APIRouter()
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DocumentProcessResponse(BaseModel):
    success: bool
    content_id: Optional[str] = None
    title: Optional[str] = None
    chunks_created: Optional[int] = None
    text_length: Optional[int] = None
    file_type: Optional[str] = None
    error: Optional[str] = None

class FileValidationResponse(BaseModel):
    supported: bool
    file_type: str
    parser: Optional[str] = None
    message: str

class DocumentDeleteResponse(BaseModel):
    success: bool
    content_id: str
    title: str
    chunks_deleted: int
    categories_deleted: int
    message: str

# 注意：文件上传通过 Nextcloud 完成，这里不需要直接上传接口
# 使用 /api/ingest/scan 来处理 Nextcloud 中的新文件

@router.get("/validate/{filename}", response_model=FileValidationResponse)
def validate_file_type(filename: str):
    """
    验证文件类型是否支持
    
    Args:
        filename: 文件名
        
    Returns:
        验证结果
    """
    try:
        doc_service = DocumentService(None)  # 不需要数据库连接
        validation = doc_service.validate_file(filename)
        return FileValidationResponse(**validation)
        
    except Exception as e:
        logger.error(f"Error validating file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/formats")
def get_supported_formats():
    """
    获取支持的文档格式信息
    
    Returns:
        支持格式的详细信息
    """
    try:
        doc_service = DocumentService(None)  # 不需要数据库连接
        return doc_service.get_supported_formats()
        
    except Exception as e:
        logger.error(f"Error getting supported formats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse-text", response_model=DocumentProcessResponse)
async def parse_text_content(
    content: str = Query(..., description="要解析的文本内容"),
    title: str = Query("Untitled", description="文档标题"),
    source_uri: str = Query("api://parse-text", description="来源URI"),
    db: Session = Depends(get_db)
):
    """
    解析纯文本内容并存储
    
    Args:
        content: 文本内容
        title: 文档标题
        source_uri: 来源URI
        db: 数据库会话
        
    Returns:
        处理结果
    """
    try:
        doc_service = DocumentService(db)
        result = doc_service.process_and_store_content(
            content, title, source_uri, created_by="api.parse_text"
        )
        
        return DocumentProcessResponse(**result)
        
    except Exception as e:
        logger.error(f"Error parsing text content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
def list_documents(
    limit: int = Query(10, description="返回文档数量"),
    offset: int = Query(0, description="跳过文档数量"),
    db: Session = Depends(get_db)
):
    """
    获取文档列表
    
    Args:
        limit: 返回文档数量
        offset: 跳过文档数量
        db: 数据库会话
        
    Returns:
        文档列表
    """
    try:
        from app.models import Content
        
        documents = db.query(Content).offset(offset).limit(limit).all()
        
        return {
            "documents": [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "source_uri": doc.source_uri,
                    "modality": doc.modality,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "created_by": doc.created_by,
                    "text_length": len(doc.text) if doc.text else 0
                }
                for doc in documents
            ],
            "total": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chunks")
def list_chunks(
    limit: int = Query(10, description="返回块数量"),
    offset: int = Query(0, description="跳过块数量"),
    with_embedding: Optional[bool] = Query(None, description="筛选是否有向量"),
    db: Session = Depends(get_db)
):
    """
    获取文本块列表，检查向量化状态
    
    Args:
        limit: 返回块数量
        offset: 跳过块数量
        with_embedding: True-只返回有向量的块，False-只返回没向量的块，None-返回所有
        db: 数据库会话
        
    Returns:
        文本块列表和向量化状态
    """
    try:
        from app.models import Chunk, Content
        
        query = db.query(Chunk).join(Content)
        
        # 根据向量状态筛选
        if with_embedding is True:
            query = query.filter(Chunk.embedding.is_not(None))
        elif with_embedding is False:
            query = query.filter(Chunk.embedding.is_(None))
        
        chunks = query.offset(offset).limit(limit).all()
        
        return {
            "chunks": [
                {
                    "id": str(chunk.id),
                    "content_id": str(chunk.content_id),
                    "content_title": chunk.content.title if chunk.content else "Unknown",
                    "seq": chunk.seq,
                    "text": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                    "text_length": len(chunk.text),
                    "has_embedding": chunk.embedding is not None,
                    "embedding_dimension": len(chunk.embedding) if chunk.embedding else None,
                    "created_at": chunk.created_at.isoformat() if hasattr(chunk, 'created_at') and chunk.created_at else None
                }
                for chunk in chunks
            ],
            "total": len(chunks),
            "filter": {
                "with_embedding": with_embedding,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
def get_document_stats(db: Session = Depends(get_db)):
    """
    获取文档统计信息
    
    Args:
        db: 数据库会话
        
    Returns:
        统计信息
    """
    try:
        from app.models import Content, Chunk
        from sqlalchemy import func
        
        # 统计文档数量
        total_documents = db.query(func.count(Content.id)).scalar()
        
        # 统计文本块数量
        total_chunks = db.query(func.count(Chunk.id)).scalar()
        
        # 统计各种文档类型
        format_stats = db.query(
            Content.modality,
            func.count(Content.id).label('count')
        ).group_by(Content.modality).all()
        
        # 统计文本长度
        text_length_stats = db.query(
            func.sum(func.length(Content.text)).label('total_chars'),
            func.avg(func.length(Content.text)).label('avg_chars')
        ).first()
        
        return {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "format_distribution": {
                format_type: count for format_type, count in format_stats
            },
            "text_statistics": {
                "total_characters": int(text_length_stats.total_chars or 0),
                "average_characters": int(text_length_stats.avg_chars or 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{content_id}", response_model=DocumentDeleteResponse)
def delete_document(content_id: str, db: Session = Depends(get_db)):
    """
    删除文档及其所有相关数据
    
    Args:
        content_id: 文档ID
        db: 数据库会话
        
    Returns:
        删除结果
    """
    try:
        # 验证content_id格式
        try:
            content_uuid = uuid.UUID(content_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid content ID format")
        
        # 查找文档
        content = db.query(Content).filter(Content.id == content_uuid).first()
        if not content:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # 记录删除信息
        title = content.title
        source_uri = content.source_uri
        logger.info(f"Deleting document: {title} (ID: {content_id})")
        
        # 如果是来自外部源的文件，创建删除记录以防止重新扫描时再次创建
        if source_uri and (source_uri.startswith("nextcloud://") or source_uri.startswith("webdav://")):
            # 创建删除记录（使用 OpsLog 表记录用户删除操作）
            from app.models import OpsLog
            delete_record = OpsLog(
                op_type="user_delete",
                payload={
                    "source_uri": source_uri,
                    "title": title,
                    "content_id": content_id,
                    "deleted_by": "user",
                    "reason": "manual_deletion"
                },
                status="completed"
            )
            db.add(delete_record)
            logger.info(f"Created delete record for external file: {source_uri}")
        
        # 统计要删除的相关数据
        chunks_count = db.query(Chunk).filter(Chunk.content_id == content_uuid).count()
        categories_count = db.query(ContentCategory).filter(ContentCategory.content_id == content_uuid).count()
        
        # 删除相关的chunks（包含向量数据）
        db.query(Chunk).filter(Chunk.content_id == content_uuid).delete()
        logger.info(f"Deleted {chunks_count} chunks for document {content_id}")
        
        # 删除相关的分类关联
        db.query(ContentCategory).filter(ContentCategory.content_id == content_uuid).delete()
        logger.info(f"Deleted {categories_count} category associations for document {content_id}")
        
        # 删除主文档记录
        db.delete(content)
        
        # 提交事务
        db.commit()
        
        logger.info(f"Successfully deleted document: {title} (ID: {content_id})")
        
        return DocumentDeleteResponse(
            success=True,
            content_id=content_id,
            title=title,
            chunks_deleted=chunks_count,
            categories_deleted=categories_count,
            message=f"Document '{title}' and all related data deleted successfully"
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 回滚事务
        db.rollback()
        logger.error(f"Error deleting document {content_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.get("/deleted-records")
def get_deleted_records(db: Session = Depends(get_db)):
    """
    获取用户删除记录，用于调试和恢复
    """
    try:
        from app.models import OpsLog
        
        delete_records = db.query(OpsLog).filter(
            OpsLog.op_type == "user_delete",
            OpsLog.status == "completed"
        ).order_by(OpsLog.created_at.desc()).limit(50).all()
        
        records = []
        for record in delete_records:
            records.append({
                "id": str(record.id),
                "source_uri": record.payload.get("source_uri"),
                "title": record.payload.get("title"),
                "deleted_at": record.created_at.isoformat() if record.created_at else None,
                "content_id": record.payload.get("content_id")
            })
        
        return {
            "success": True,
            "records": records,
            "total": len(records)
        }
        
    except Exception as e:
        logger.error(f"Error getting deleted records: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get deleted records: {str(e)}")

@router.delete("/deleted-records/{record_id}")
def remove_delete_record(record_id: str, db: Session = Depends(get_db)):
    """
    移除删除记录，允许文件在下次扫描时重新创建
    """
    try:
        from app.models import OpsLog
        from uuid import UUID
        
        record_uuid = UUID(record_id)
        delete_record = db.query(OpsLog).filter(
            OpsLog.id == record_uuid,
            OpsLog.op_type == "user_delete"
        ).first()
        
        if not delete_record:
            raise HTTPException(status_code=404, detail="Delete record not found")
        
        source_uri = delete_record.payload.get("source_uri")
        db.delete(delete_record)
        db.commit()
        
        logger.info(f"Removed delete record for: {source_uri}")
        
        return {
            "success": True,
            "message": f"Delete record removed. File will be re-created on next scan if it exists in source.",
            "source_uri": source_uri
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing delete record {record_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove delete record: {str(e)}")

@router.get("/{content_id}")
def get_document(content_id: str, db: Session = Depends(get_db)):
    """
    获取文档详情
    
    Args:
        content_id: 文档ID
        db: 数据库会话
        
    Returns:
        文档详情
    """
    try:
        # 验证content_id格式
        try:
            content_uuid = uuid.UUID(content_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid content ID format")
        
        # 查找文档
        content = db.query(Content).filter(Content.id == content_uuid).first()
        if not content:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # 获取chunks数量
        chunks_count = db.query(Chunk).filter(Chunk.content_id == content_uuid).count()
        
        # 获取分类信息
        categories = db.query(ContentCategory).filter(
            ContentCategory.content_id == content_uuid
        ).all()
        
        return {
            "id": str(content.id),
            "title": content.title,
            "text": content.text,
            "summary": content.summary,
            "source_uri": content.source_uri,
            "modality": content.modality,
            "category": content.category,
            "tags": content.tags,
            "meta": content.meta,
            "created_by": content.created_by,
            "created_at": content.created_at.isoformat() if content.created_at else None,
            "updated_at": content.updated_at.isoformat() if content.updated_at else None,
            "access_count": content.access_count,
            "search_count": content.search_count,
            "last_accessed": content.last_accessed.isoformat() if content.last_accessed else None,
            "chunks_count": chunks_count,
            "categories": [
                {
                    "category_id": str(cat.category_id),
                    "confidence": cat.confidence,
                    "reasoning": cat.reasoning
                }
                for cat in categories
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {content_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
