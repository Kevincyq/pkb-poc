"""
Embedding 测试和管理 API
提供 embedding 服务的测试、信息查询等接口
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from app.services.embedding_service import EmbeddingService

router = APIRouter()
logger = logging.getLogger(__name__)

class EmbeddingRequest(BaseModel):
    text: str
    dimensions: Optional[int] = None

class BatchEmbeddingRequest(BaseModel):
    texts: List[str]

class SimilarityRequest(BaseModel):
    text1: str
    text2: str

class EmbeddingResponse(BaseModel):
    success: bool
    embedding: Optional[List[float]] = None
    dimension: Optional[int] = None
    error: Optional[str] = None

class BatchEmbeddingResponse(BaseModel):
    success: bool
    embeddings: List[Optional[List[float]]] = []
    dimensions: List[Optional[int]] = []
    error: Optional[str] = None

class SimilarityResponse(BaseModel):
    success: bool
    similarity: Optional[float] = None
    error: Optional[str] = None

@router.get("/info")
def get_embedding_info():
    """
    获取 embedding 服务信息
    
    Returns:
        服务配置和状态信息
    """
    try:
        service = EmbeddingService()
        return service.get_model_info()
    except Exception as e:
        logger.error(f"Error getting embedding info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
def test_embedding_service():
    """
    测试 embedding 服务连接和功能
    
    Returns:
        测试结果
    """
    try:
        service = EmbeddingService()
        return service.test_embedding_connection()
    except Exception as e:
        logger.error(f"Error testing embedding service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/embed", response_model=EmbeddingResponse)
def get_text_embedding(request: EmbeddingRequest):
    """
    获取文本的 embedding
    
    Args:
        request: 包含文本和可选维度的请求
        
    Returns:
        embedding 向量
    """
    try:
        service = EmbeddingService()
        
        if not service.is_enabled():
            raise HTTPException(status_code=503, detail="Embedding service not available")
        
        if request.dimensions:
            embedding = service.get_embedding_with_dimensions(request.text, request.dimensions)
        else:
            embedding = service.get_embedding(request.text)
        
        if embedding is None:
            return EmbeddingResponse(
                success=False,
                error="Failed to generate embedding"
            )
        
        return EmbeddingResponse(
            success=True,
            embedding=embedding,
            dimension=len(embedding)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/embed/batch", response_model=BatchEmbeddingResponse)
def get_batch_embeddings(request: BatchEmbeddingRequest):
    """
    批量获取文本的 embeddings
    
    Args:
        request: 包含文本列表的请求
        
    Returns:
        embedding 向量列表
    """
    try:
        service = EmbeddingService()
        
        if not service.is_enabled():
            raise HTTPException(status_code=503, detail="Embedding service not available")
        
        if len(request.texts) > 100:  # 限制批量大小
            raise HTTPException(status_code=400, detail="Too many texts (max 100)")
        
        embeddings = service.batch_get_embeddings(request.texts)
        dimensions = [len(emb) if emb else None for emb in embeddings]
        
        return BatchEmbeddingResponse(
            success=True,
            embeddings=embeddings,
            dimensions=dimensions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/similarity", response_model=SimilarityResponse)
def calculate_similarity(request: SimilarityRequest):
    """
    计算两个文本的相似度
    
    Args:
        request: 包含两个文本的请求
        
    Returns:
        相似度分数
    """
    try:
        service = EmbeddingService()
        
        if not service.is_enabled():
            raise HTTPException(status_code=503, detail="Embedding service not available")
        
        # 获取两个文本的 embeddings
        embedding1 = service.get_embedding(request.text1)
        embedding2 = service.get_embedding(request.text2)
        
        if embedding1 is None or embedding2 is None:
            return SimilarityResponse(
                success=False,
                error="Failed to generate embeddings for one or both texts"
            )
        
        # 计算相似度
        similarity = service.get_similarity(embedding1, embedding2)
        
        return SimilarityResponse(
            success=True,
            similarity=similarity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
def get_supported_models():
    """
    获取支持的 embedding 模型列表
    
    Returns:
        支持的模型信息
    """
    try:
        service = EmbeddingService()
        
        return {
            "supported_models": service.SUPPORTED_MODELS,
            "current_model": service.current_model,
            "model_info": service.get_model_info()
        }
        
    except Exception as e:
        logger.error(f"Error getting supported models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def embedding_health_check():
    """
    Embedding 服务健康检查
    
    Returns:
        健康状态
    """
    try:
        service = EmbeddingService()
        
        if not service.is_enabled():
            return {
                "status": "disabled",
                "message": "Embedding service is not enabled"
            }
        
        # 尝试一个简单的 embedding 请求
        test_embedding = service.get_embedding("health check")
        
        if test_embedding:
            return {
                "status": "healthy",
                "message": "Embedding service is working properly",
                "dimension": len(test_embedding)
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Embedding service failed to generate test embedding"
            }
            
    except Exception as e:
        logger.error(f"Embedding health check failed: {e}")
        return {
            "status": "error",
            "message": f"Health check error: {str(e)}"
        }
