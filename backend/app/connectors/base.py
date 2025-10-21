"""
云盘存储连接器抽象基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class CloudStorageConnector(ABC):
    """云盘存储连接器抽象基类"""
    
    @abstractmethod
    async def authenticate(self, user_id: str) -> Dict[str, Any]:
        """用户认证，返回认证URL或状态"""
        pass
    
    @abstractmethod
    async def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        """处理OAuth回调"""
        pass
    
    @abstractmethod
    async def upload_file(self, file_content: bytes, filename: str, user_id: str) -> Dict[str, Any]:
        """上传文件"""
        pass
    
    @abstractmethod
    async def download_file(self, file_id: str, user_id: str) -> bytes:
        """下载文件"""
        pass
    
    @abstractmethod
    async def get_thumbnail(self, file_id: str, user_id: str) -> bytes:
        """获取缩略图"""
        pass
    
    @abstractmethod
    async def create_folder(self, folder_name: str, user_id: str) -> str:
        """创建专用文件夹"""
        pass
    
    @abstractmethod
    async def list_files(self, user_id: str, folder_path: str = None) -> List[Dict]:
        """列出文件"""
        pass
    
    @abstractmethod
    async def refresh_token(self, user_id: str) -> bool:
        """刷新访问令牌"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取云盘提供商名称"""
        pass
