"""
快速处理任务 - 高优先级的即时处理任务
"""

from .celery_app import celery_app
from app.db import SessionLocal
from app.services.quick_classification_service import QuickClassificationService
from app.services.collection_matching_service import CollectionMatchingService
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="app.workers.quick_tasks.quick_classify_content", queue="quick", priority=9)
def quick_classify_content(content_id: str):
    """
    快速分类内容 - 高优先级任务
    
    Args:
        content_id: 内容ID
        
    Returns:
        快速分类结果
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting quick classification for content: {content_id}")
        
        # 初始化快速分类服务
        quick_service = QuickClassificationService(db)
        
        # 执行快速分类
        result = quick_service.quick_classify(content_id)
        
        if result["success"]:
            logger.info(f"Quick classified content {content_id} as {result.get('category_name', 'unknown')}")
        else:
            logger.error(f"Failed to quick classify content {content_id}: {result.get('error', 'unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in quick_classify_content task for {content_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="app.workers.quick_tasks.batch_quick_classify", queue="quick", priority=8)
def batch_quick_classify(content_ids: list):
    """
    批量快速分类内容
    
    Args:
        content_ids: 内容ID列表
        
    Returns:
        批量快速分类结果
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting batch quick classification for {len(content_ids)} contents")
        
        # 初始化快速分类服务
        quick_service = QuickClassificationService(db)
        
        # 执行批量快速分类
        result = quick_service.batch_quick_classify(content_ids)
        
        logger.info(f"Batch quick classification completed: {result['success']} success, {result['failed']} failed")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in batch_quick_classify task: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="app.workers.quick_tasks.match_document_to_collections", queue="quick", priority=8)
def match_document_to_collections(content_id: str):
    """
    将文档匹配到合适的用户合集
    
    Args:
        content_id: 内容ID
        
    Returns:
        匹配结果
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting collection matching for content: {content_id}")
        
        # 初始化合集匹配服务
        matching_service = CollectionMatchingService(db)
        
        # 执行匹配
        matched_collections = matching_service.match_document_to_collections(content_id)
        
        if matched_collections:
            logger.info(f"Content {content_id} matched to {len(matched_collections)} collections: {matched_collections}")
        else:
            logger.info(f"Content {content_id} did not match any collections")
        
        return {
            "success": True,
            "content_id": content_id,
            "matched_collections": matched_collections,
            "count": len(matched_collections)
        }
        
    except Exception as e:
        logger.error(f"Error in match_document_to_collections task for {content_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()
