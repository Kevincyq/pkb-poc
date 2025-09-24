"""
向量嵌入服务
支持 OpenAI Embeddings 和本地模型（可选）
"""
import os
import numpy as np
from typing import List, Optional, Dict, Any
import logging

# OpenAI 客户端导入
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

# 可选导入 sentence_transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class EmbeddingService:
    # 支持的模型配置（Turing 平台格式）
    SUPPORTED_MODELS = {
        "turing/text-embedding-3-large": {"dimension": 3072, "cost_tier": "premium"},
        "turing/text-embedding-3-small": {"dimension": 1536, "cost_tier": "standard"}, 
        "text-embedding-3-large": {"dimension": 3072, "cost_tier": "premium"},  # OpenAI 官方
        "text-embedding-3-small": {"dimension": 1536, "cost_tier": "standard"}, 
        "text-embedding-ada-002": {"dimension": 1536, "cost_tier": "legacy"},
    }
    
    def __init__(self):
        # 检查 OpenAI 可用性
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI library not available. Install with: pip install openai>=1.0.0")
        
        # 支持 OpenAI 原生和 Turing 平台
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("TURING_API_KEY")
        self.openai_enabled = bool(self.openai_api_key and OPENAI_AVAILABLE)
        self.local_model_enabled = (
            os.getenv("USE_LOCAL_EMBEDDING", "false").lower() == "true" 
            and SENTENCE_TRANSFORMERS_AVAILABLE
        )
        
        # 当前使用的模型
        self.current_model = self._get_current_model()
        
        # 初始化 OpenAI 客户端
        self.openai_client = None
        if self.openai_enabled:
            try:
                # 配置 API Base（支持 Turing 平台）
                api_base = os.getenv("TURING_API_BASE") or os.getenv("OPENAI_API_BASE")
                
                self.openai_client = OpenAI(
                    api_key=self.openai_api_key,
                    base_url=api_base
                )
                
                if os.getenv("TURING_API_KEY"):
                    logger.info(f"Turing platform embedding client initialized with base: {api_base}")
                else:
                    logger.info("OpenAI official embedding client initialized")
                    
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_enabled = False
        
        # 初始化本地模型
        if self.local_model_enabled:
            try:
                model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
                # 强制使用 CPU，适合无 GPU 环境
                self.local_model = SentenceTransformer(model_name, device='cpu')
                logger.info(f"Local embedding model loaded on CPU: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load local embedding model: {e}")
                self.local_model_enabled = False
        elif os.getenv("USE_LOCAL_EMBEDDING", "false").lower() == "true":
            logger.warning("Local embedding requested but sentence-transformers not available. Install with: pip install sentence-transformers")
    
    def _get_current_model(self) -> str:
        """获取当前配置的模型名称"""
        if os.getenv("TURING_API_KEY"):
            # Turing 平台使用带前缀的模型名
            base_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
            if not base_model.startswith("turing/"):
                return f"turing/{base_model}"
            return base_model
        else:
            # OpenAI 官方 API
            return os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    def get_model_dimension(self, model_name: str = None) -> int:
        """获取指定模型的向量维度"""
        model_name = model_name or self.current_model
        return self.SUPPORTED_MODELS.get(model_name, {}).get("dimension", 3072)
    
    def is_enabled(self) -> bool:
        """检查是否有可用的嵌入服务"""
        return self.openai_enabled or self.local_model_enabled
    
    def get_embedding(self, text: str, model: str = "auto") -> Optional[List[float]]:
        """
        获取文本的向量嵌入
        
        Args:
            text: 输入文本
            model: 模型选择 ("openai", "local", "auto")
        
        Returns:
            向量列表或 None
        """
        if not text.strip():
            return None
        
        # 自动选择模型
        if model == "auto":
            if self.openai_enabled:
                model = "openai"
            elif self.local_model_enabled:
                model = "local"
            else:
                return None
        
        try:
            if model == "openai" and self.openai_enabled:
                return self._get_openai_embedding(text)
            elif model == "local" and self.local_model_enabled:
                return self._get_local_embedding(text)
            else:
                logger.warning(f"Requested model '{model}' not available")
                return None
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
    
    def batch_get_embeddings(self, texts: List[str], model: str = "auto") -> List[Optional[List[float]]]:
        """
        批量获取向量嵌入
        
        Args:
            texts: 文本列表
            model: 模型选择
        
        Returns:
            向量列表的列表
        """
        if not texts:
            return []
        
        # 过滤空文本
        valid_texts = [(i, text) for i, text in enumerate(texts) if text.strip()]
        if not valid_texts:
            return [None] * len(texts)
        
        try:
            if model == "auto":
                if self.openai_enabled:
                    model = "openai"
                elif self.local_model_enabled:
                    model = "local"
                else:
                    return [None] * len(texts)
            
            if model == "openai" and self.openai_enabled:
                embeddings = self._batch_get_openai_embeddings([text for _, text in valid_texts])
            elif model == "local" and self.local_model_enabled:
                embeddings = self._batch_get_local_embeddings([text for _, text in valid_texts])
            else:
                return [None] * len(texts)
            
            # 重新排列结果
            results = [None] * len(texts)
            for (original_idx, _), embedding in zip(valid_texts, embeddings):
                results[original_idx] = embedding
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch embedding: {e}")
            return [None] * len(texts)
    
    def _get_openai_embedding(self, text: str) -> List[float]:
        """使用 OpenAI API 获取嵌入"""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        # 使用当前配置的模型
        model = self.current_model
        
        try:
            response = self.openai_client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting OpenAI embedding with model {model}: {e}")
            raise
    
    def _batch_get_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量获取 OpenAI 嵌入"""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        # 使用当前配置的模型
        model = self.current_model
        
        try:
            response = self.openai_client.embeddings.create(
                model=model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error getting batch OpenAI embeddings with model {model}: {e}")
            raise
    
    def get_embedding_with_dimensions(self, text: str, dimensions: Optional[int] = None) -> Optional[List[float]]:
        """
        获取指定维度的文本嵌入（仅适用于 text-embedding-3-small 和 text-embedding-3-large）
        
        Args:
            text: 输入文本
            dimensions: 指定维度（可选）
            
        Returns:
            向量列表或 None
        """
        if not self.openai_client or not text.strip():
            return None
        
        model = self.current_model
        
        try:
            # 构建请求参数
            params = {
                "model": model,
                "input": text
            }
            
            # 如果指定了维度且模型支持，添加 dimensions 参数
            if dimensions and ("text-embedding-3" in model):
                params["dimensions"] = dimensions
            
            response = self.openai_client.embeddings.create(**params)
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error getting embedding with dimensions {dimensions}: {e}")
            return None
    
    def test_embedding_connection(self) -> Dict[str, Any]:
        """
        测试 embedding 连接和功能
        
        Returns:
            测试结果字典
        """
        test_results = {
            "openai_available": OPENAI_AVAILABLE,
            "client_initialized": self.openai_client is not None,
            "model": self.current_model,
            "api_platform": "turing" if os.getenv("TURING_API_KEY") else "openai",
            "tests": {}
        }
        
        if not self.openai_enabled:
            test_results["error"] = "OpenAI embedding not enabled"
            return test_results
        
        # 测试单个文本嵌入
        try:
            test_text = "Hello, this is a test embedding."
            embedding = self._get_openai_embedding(test_text)
            test_results["tests"]["single_embedding"] = {
                "success": True,
                "dimension": len(embedding),
                "sample_values": embedding[:3] if len(embedding) >= 3 else embedding
            }
        except Exception as e:
            test_results["tests"]["single_embedding"] = {
                "success": False,
                "error": str(e)
            }
        
        # 测试批量嵌入
        try:
            test_texts = ["Hello world", "Python programming", "Machine learning"]
            embeddings = self._batch_get_openai_embeddings(test_texts)
            test_results["tests"]["batch_embedding"] = {
                "success": True,
                "count": len(embeddings),
                "dimensions": [len(emb) for emb in embeddings]
            }
        except Exception as e:
            test_results["tests"]["batch_embedding"] = {
                "success": False,
                "error": str(e)
            }
        
        # 测试自定义维度（如果支持）
        if "text-embedding-3" in self.current_model:
            try:
                custom_embedding = self.get_embedding_with_dimensions("Custom dimension test", 512)
                test_results["tests"]["custom_dimensions"] = {
                    "success": custom_embedding is not None,
                    "dimension": len(custom_embedding) if custom_embedding else None
                }
            except Exception as e:
                test_results["tests"]["custom_dimensions"] = {
                    "success": False,
                    "error": str(e)
                }
        
        return test_results
    
    def _get_local_embedding(self, text: str) -> List[float]:
        """使用本地模型获取嵌入"""
        if not self.local_model_enabled:
            raise RuntimeError("Local embedding model not available")
        embedding = self.local_model.encode(text)
        return embedding.tolist()
    
    def _batch_get_local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量获取本地模型嵌入"""
        if not self.local_model_enabled:
            raise RuntimeError("Local embedding model not available")
        embeddings = self.local_model.encode(texts)
        return [emb.tolist() for emb in embeddings]
    
    def get_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # 计算余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        local_model_name = None
        if self.local_model_enabled and hasattr(self, 'local_model'):
            # 尝试获取模型名称，不同版本的 sentence-transformers 可能不同
            if hasattr(self.local_model, '_model_name'):
                local_model_name = self.local_model._model_name
            elif hasattr(self.local_model, 'model_name'):
                local_model_name = self.local_model.model_name
            else:
                local_model_name = "unknown"
        
        # 检测使用的 API 平台
        api_platform = "disabled"
        api_base_url = None
        if self.openai_enabled:
            if os.getenv("TURING_API_KEY"):
                api_platform = "turing"
                api_base_url = os.getenv("TURING_API_BASE")
            elif os.getenv("OPENAI_API_KEY"):
                api_platform = "openai_official"
                api_base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            else:
                api_platform = "openai_compatible"
                api_base_url = os.getenv("OPENAI_API_BASE")
        
        # 获取当前模型的维度
        current_dimension = None
        if self.openai_enabled:
            current_dimension = self.get_model_dimension(self.current_model)
        elif self.local_model_enabled:
            current_dimension = 384  # 默认本地模型维度
        
        return {
            "openai_available": OPENAI_AVAILABLE,
            "openai_enabled": self.openai_enabled,
            "client_initialized": self.openai_client is not None,
            "current_model": self.current_model,
            "api_platform": api_platform,
            "api_base_url": api_base_url,
            "local_model_enabled": self.local_model_enabled,
            "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
            "local_model_name": local_model_name,
            "embedding_dimension": current_dimension,
            "supported_models": list(self.SUPPORTED_MODELS.keys()),
            "custom_dimensions_supported": "text-embedding-3" in self.current_model if self.current_model else False
        }