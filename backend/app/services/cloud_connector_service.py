"""
云盘连接器管理服务
"""
import os
import logging
from typing import Dict, Any, Optional
from .google_drive import GoogleDriveConnector
from .nextcloud import NextcloudConnector
from .base import CloudStorageConnector

logger = logging.getLogger(__name__)

class CloudConnectorService:
    """云盘连接器管理服务"""
    
    def __init__(self):
        self.connectors = {
            "google_drive": GoogleDriveConnector(),
            "nextcloud": NextcloudConnector(),
            # 未来可以添加更多云盘
            # "onedrive": OneDriveConnector(),
            # "dropbox": DropboxConnector(),
        }
        self.default_provider = os.getenv('DEFAULT_CLOUD_PROVIDER', 'google_drive')
    
    def get_connector(self, provider: str = None) -> CloudStorageConnector:
        """获取指定连接器"""
        provider = provider or self.default_provider
        connector = self.connectors.get(provider)
        
        if not connector:
            raise ValueError(f"Unsupported cloud provider: {provider}")
        
        return connector
    
    def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """获取可用的云盘提供商列表"""
        providers = {}
        
        for name, connector in self.connectors.items():
            providers[name] = {
                "name": connector.get_provider_name(),
                "display_name": self._get_display_name(name),
                "enabled": self._is_provider_enabled(name)
            }
        
        return providers
    
    def _get_display_name(self, provider: str) -> str:
        """获取云盘显示名称"""
        display_names = {
            "google_drive": "Google Drive",
            "nextcloud": "Nextcloud",
            "onedrive": "Microsoft OneDrive",
            "dropbox": "Dropbox"
        }
        return display_names.get(provider, provider.title())
    
    def _is_provider_enabled(self, provider: str) -> bool:
        """检查云盘提供商是否启用"""
        if provider == "google_drive":
            return os.getenv('ENABLE_GOOGLE_DRIVE', 'true').lower() == 'true'
        elif provider == "nextcloud":
            return os.getenv('ENABLE_NEXTCLOUD', 'true').lower() == 'true'
        else:
            return True
    
    async def upload_to_cloud(self, file_content: bytes, filename: str, 
                             user_id: str, provider: str = None) -> Dict[str, Any]:
        """统一云盘上传接口"""
        try:
            connector = self.get_connector(provider)
            result = await connector.upload_file(file_content, filename, user_id)
            
            if result["success"]:
                logger.info(f"File uploaded to {provider}: {filename}")
            else:
                logger.error(f"Failed to upload file to {provider}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Cloud upload error: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider
            }
    
    async def download_from_cloud(self, file_id: str, user_id: str, 
                                 provider: str) -> bytes:
        """统一云盘下载接口"""
        try:
            connector = self.get_connector(provider)
            return await connector.download_file(file_id, user_id)
            
        except Exception as e:
            logger.error(f"Cloud download error: {e}")
            raise
    
    async def get_cloud_thumbnail(self, file_id: str, user_id: str, 
                                 provider: str) -> bytes:
        """统一云盘缩略图接口"""
        try:
            connector = self.get_connector(provider)
            return await connector.get_thumbnail(file_id, user_id)
            
        except Exception as e:
            logger.error(f"Cloud thumbnail error: {e}")
            raise
