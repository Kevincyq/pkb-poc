"""
分类管理 API
提供分类的创建、查询、管理和统计功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.db import SessionLocal
from app.services.category_service import CategoryService

router = APIRouter()
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CategoryCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

class ClassificationRequest(BaseModel):
    content_id: str
    force_reclassify: bool = False

class BatchClassificationRequest(BaseModel):
    content_ids: List[str]
    force_reclassify: bool = False

@router.get("/")
def get_categories(
    include_stats: bool = Query(False, description="是否包含统计信息"),
    db: Session = Depends(get_db)
):
    """
    获取所有分类列表
    
    Args:
        include_stats: 是否包含每个分类的文档统计
        db: 数据库会话
        
    Returns:
        分类列表
    """
    try:
        category_service = CategoryService(db)
        categories = category_service.get_categories(include_stats=include_stats)
        
        return {
            "categories": categories,
            "total": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize")
def initialize_system_categories(db: Session = Depends(get_db)):
    """
    初始化系统预置分类
    
    Args:
        db: 数据库会话
        
    Returns:
        初始化结果
    """
    try:
        category_service = CategoryService(db)
        success = category_service.initialize_system_categories()
        
        if success:
            return {
                "success": True,
                "message": "System categories initialized successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to initialize system categories"
            }
        
    except Exception as e:
        logger.error(f"Error initializing system categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{category_id}")
def get_category_details(
    category_id: str,
    limit: int = Query(20, description="返回内容数量"),
    offset: int = Query(0, description="跳过内容数量"),
    db: Session = Depends(get_db)
):
    """
    获取分类详情和该分类下的内容
    
    Args:
        category_id: 分类ID
        limit: 返回内容数量
        offset: 跳过内容数量
        db: 数据库会话
        
    Returns:
        分类详情和内容列表
    """
    try:
        category_service = CategoryService(db)
        result = category_service.get_content_by_category(category_id, limit, offset)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting category details {category_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/classify")
def classify_content(
    request: ClassificationRequest,
    db: Session = Depends(get_db)
):
    """
    对单个内容进行分类
    
    Args:
        request: 分类请求
        db: 数据库会话
        
    Returns:
        分类结果
    """
    try:
        category_service = CategoryService(db)
        
        if not category_service.is_enabled():
            raise HTTPException(
                status_code=503, 
                detail="Classification service not available. Please check AI service configuration."
            )
        
        result = category_service.classify_content(
            request.content_id, 
            request.force_reclassify
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error classifying content {request.content_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/classify/batch")
def batch_classify_contents(
    request: BatchClassificationRequest,
    db: Session = Depends(get_db)
):
    """
    批量分类内容
    
    Args:
        request: 批量分类请求
        db: 数据库会话
        
    Returns:
        批量分类结果
    """
    try:
        category_service = CategoryService(db)
        
        if not category_service.is_enabled():
            raise HTTPException(
                status_code=503, 
                detail="Classification service not available. Please check AI service configuration."
            )
        
        # 使用异步任务进行批量分类
        from app.workers.tasks import batch_classify_contents as batch_classify_task
        task_result = batch_classify_task.delay(request.content_ids, request.force_reclassify)
        
        return {
            "success": True,
            "task_id": str(task_result.id),
            "message": f"Batch classification scheduled for {len(request.content_ids)} contents",
            "content_count": len(request.content_ids)
        }
        
    except Exception as e:
        logger.error(f"Error scheduling batch classification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/overview")
def get_classification_stats(db: Session = Depends(get_db)):
    """
    获取分类统计概览
    
    Args:
        db: 数据库会话
        
    Returns:
        分类统计信息
    """
    try:
        category_service = CategoryService(db)
        stats = category_service.get_classification_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting classification stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/service/status")
def get_service_status(db: Session = Depends(get_db)):
    """
    获取分类服务状态
    
    Args:
        db: 数据库会话
        
    Returns:
        服务状态信息
    """
    try:
        category_service = CategoryService(db)
        
        return {
            "enabled": category_service.is_enabled(),
            "model": getattr(category_service, 'classification_model', 'Not configured'),
            "system_categories": len(CategoryService.SYSTEM_CATEGORIES),
            "api_configured": category_service.openai_enabled if hasattr(category_service, 'openai_enabled') else False
        }
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content/{content_id}/status")
def get_content_classification_status(
    content_id: str,
    db: Session = Depends(get_db)
):
    """
    获取内容的分类状态
    
    Args:
        content_id: 内容ID
        db: 数据库会话
        
    Returns:
        分类状态信息
    """
    try:
        from app.models import ContentCategory, Category
        from app.services.quick_classification_service import QuickClassificationService
        
        # 转换content_id为UUID格式
        from uuid import UUID
        try:
            content_uuid = UUID(content_id) if isinstance(content_id, str) else content_id
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid content_id format")
        
        # 检查内容是否存在
        from app.models import Content
        content = db.query(Content).filter(Content.id == content_uuid).first()
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # 获取分类信息
        content_category = db.query(ContentCategory, Category).join(Category).filter(
            ContentCategory.content_id == content_uuid
        ).first()
        
        if not content_category:
            return {
                "classified": False,
                "content_id": content_id,
                "status": "pending"
            }
        
        category_rel, category = content_category
        
        # 判断是否为快速分类
        quick_service = QuickClassificationService(db)
        is_quick = quick_service.is_quick_classification(content_id)
        
        return {
            "classified": True,
            "content_id": content_id,
            "category": {
                "id": str(category.id),
                "name": category.name,
                "color": category.color
            },
            "confidence": float(category_rel.confidence),
            "reasoning": category_rel.reasoning,
            "is_quick_classification": is_quick,
            "status": "quick" if is_quick else "ai_classified",
            "created_at": category_rel.created_at.isoformat() if category_rel.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting classification status for {content_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reclassify/all")
def reclassify_all_contents(
    force: bool = Query(False, description="是否强制重新分类已分类的内容"),
    db: Session = Depends(get_db)
):
    """
    重新分类所有内容
    
    Args:
        force: 是否强制重新分类已分类的内容
        db: 数据库会话
        
    Returns:
        重新分类任务信息
    """
    try:
        from app.models import Content
        from sqlalchemy import func
        
        # 获取需要分类的内容ID
        if force:
            # 重新分类所有内容
            content_ids = db.query(Content.id).all()
        else:
            # 只分类未分类的内容
            from app.models import ContentCategory
            classified_content_ids = db.query(ContentCategory.content_id).distinct().subquery()
            content_ids = db.query(Content.id).filter(
                ~Content.id.in_(classified_content_ids)
            ).all()
        
        content_ids = [str(cid[0]) for cid in content_ids]
        
        if not content_ids:
            return {
                "success": True,
                "message": "No contents need classification",
                "content_count": 0
            }
        
        # 使用异步任务进行批量分类
        from app.workers.tasks import batch_classify_contents as batch_classify_task
        task_result = batch_classify_task.delay(content_ids, force)
        
        return {
            "success": True,
            "task_id": str(task_result.id),
            "message": f"Reclassification scheduled for {len(content_ids)} contents",
            "content_count": len(content_ids),
            "force_reclassify": force
        }
        
    except Exception as e:
        logger.error(f"Error scheduling reclassification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 以下是自定义分类管理接口（可选功能）
@router.post("/custom")
def create_custom_category(
    request: CategoryCreateRequest,
    db: Session = Depends(get_db)
):
    """
    创建自定义分类（预留接口）
    
    Args:
        request: 分类创建请求
        db: 数据库会话
        
    Returns:
        创建结果
    """
    # 这是预留接口，当前版本只支持系统预置分类
    raise HTTPException(
        status_code=501, 
        detail="Custom categories not implemented in current version. Only system categories are supported."
    )

@router.put("/{category_id}")
def update_category(
    category_id: str,
    request: CategoryUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新分类信息（预留接口）
    
    Args:
        category_id: 分类ID
        request: 更新请求
        db: 数据库会话
        
    Returns:
        更新结果
    """
    # 这是预留接口，当前版本不支持修改系统分类
    raise HTTPException(
        status_code=501, 
        detail="Category modification not implemented in current version. System categories are read-only."
    )

@router.delete("/{category_id}")
def delete_category(
    category_id: str,
    db: Session = Depends(get_db)
):
    """
    删除分类（预留接口）
    
    Args:
        category_id: 分类ID
        db: 数据库会话
        
    Returns:
        删除结果
    """
    # 这是预留接口，当前版本不支持删除系统分类
    raise HTTPException(
        status_code=501, 
        detail="Category deletion not implemented in current version. System categories cannot be deleted."
    )

@router.post("/initialize-system-categories")
def initialize_system_categories_api(db: Session = Depends(get_db)):
    """初始化和修复系统分类"""
    try:
        from app.services.category_service import CategoryService
        
        category_service = CategoryService(db)
        success = category_service.initialize_system_categories()
        
        if success:
            return {
                "success": True,
                "message": "System categories initialized and fixed successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to initialize system categories"
            }
            
    except Exception as e:
        logger.error(f"Failed to initialize system categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize system categories: {str(e)}")