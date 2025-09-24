from fastapi import APIRouter, Query, Depends
from app.db import SessionLocal
from app.models import Content, Chunk
from app.services.search_service import SearchService
from sqlalchemy.orm import Session
from typing import Optional
import re
import logging
from urllib.parse import unquote

logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()

@router.get("/")
async def search(
    query: str = Query(None, alias="q", description="搜索查询"),
    top_k: int = Query(8, description="返回结果数量"),
    search_type: str = Query("hybrid", description="搜索类型: keyword, semantic, hybrid"),
    modality: Optional[str] = Query(None, description="内容类型过滤"),
    category: Optional[str] = Query(None, description="分类过滤"),
    db: Session = Depends(get_db)
):
    """
    增强搜索接口，支持关键词、语义和混合搜索
    """
    # 构建过滤条件
    filters = {}
    if modality:
        filters["modality"] = modality
    if category:
        filters["category"] = category
    
    try:
        # URL解码查询参数
        decoded_query = unquote(query) if query else ""
        if not decoded_query:
            return {
                "query": "",
                "results": [],
                "total": 0,
                "response_time": 0,
                "search_type": search_type,
                "embedding_enabled": True,
                "error": "Query parameter is required"
            }

        # 使用搜索服务
        search_service = SearchService(db)
        results = search_service.search(decoded_query, top_k, search_type, filters)
        
        # 确保返回有效的JSON
        if not isinstance(results, dict):
            return {
                "query": query,
                "results": [],
                "total": 0,
                "response_time": 0,
                "search_type": search_type,
                "embedding_enabled": True,
                "error": "Invalid search results format"
            }
        
        return results
    except Exception as e:
        logger.error(f"Search API error: {e}")
        return {
            "query": query,
            "results": [],
            "total": 0,
            "response_time": 0,
            "search_type": search_type,
            "embedding_enabled": True,
            "error": str(e)
        }

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="部分查询"),
    limit: int = Query(5, description="建议数量"),
    db: Session = Depends(get_db)
):
    """获取搜索建议"""
    # URL解码查询参数
    decoded_q = unquote(q) if q else ""
    search_service = SearchService(db)
    suggestions = search_service.get_search_suggestions(decoded_q, limit)
    
    return {
        "query": q,
        "suggestions": suggestions
    }

@router.get("/category/{category_id}")
async def search_by_category(
    category_id: str,
    q: Optional[str] = Query(None, description="搜索查询"),
    top_k: int = Query(20, description="返回结果数量"),
    db: Session = Depends(get_db)
):
    """
    按分类搜索内容
    """
    try:
        # URL解码查询参数
        decoded_q = unquote(q) if q else None
        search_service = SearchService(db)
        results = search_service.search_by_category(category_id, decoded_q, top_k)
        
        if not isinstance(results, dict):
            return {
                "category_id": category_id,
                "results": [],
                "total": 0,
                "error": "Invalid search results format"
            }
        
        return results
    except Exception as e:
        logger.error(f"Category search error: {e}")
        return {
            "category_id": category_id,
            "results": [],
            "total": 0,
            "error": str(e)
        }

@router.get("/categories/stats")
async def get_category_search_stats(db: Session = Depends(get_db)):
    """
    获取分类统计信息用于搜索筛选
    """
    search_service = SearchService(db)
    stats = search_service.get_category_stats()
    
    return stats
