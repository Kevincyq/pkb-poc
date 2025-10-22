"""
存储策略服务
"""
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import User, CloudAuth, StorageConfig
from .cloud_connector_service import CloudConnectorService

logger = logging.getLogger(__name__)

class StorageStrategyService:
    """存储策略服务"""
    
    def __init__(self):
        self.connector_service = CloudConnectorService()
        
        # 默认配置
        self.default_config = {
            "large_file_threshold": int(os.getenv('LARGE_FILE_THRESHOLD', 5 * 1024 * 1024)),  # 5MB
            "default_cloud_provider": os.getenv('DEFAULT_CLOUD_PROVIDER', 'google_drive'),
            "enable_nextcloud": os.getenv('ENABLE_NEXTCLOUD', 'true').lower() == 'true',
            "enable_google_drive": os.getenv('ENABLE_GOOGLE_DRIVE', 'true').lower() == 'true',
            "thumbnail_size": {"width": 300, "height": 200},
            "thumbnail_quality": 85
        }
    
    async def get_storage_config(self, user_id: str = None, db: Session = None) -> Dict[str, Any]:
        """获取存储配置"""
        config = self.default_config.copy()
        
        if user_id and db:
            # 获取用户特定配置
            user_configs = db.query(StorageConfig).filter(
                StorageConfig.user_id == user_id,
                StorageConfig.is_active == True
            ).all()
            
            for user_config in user_configs:
                config[user_config.config_key] = user_config.config_value
            
            # 如果没有用户配置，根据用户类型创建默认配置
            if not user_configs:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    if user.google_id:
                        # Google用户默认使用Google Drive
                        default_config = {
                            "default_cloud_provider": "google_drive",
                            "large_file_threshold": int(os.getenv("LARGE_FILE_THRESHOLD", "5242880")),
                            "enable_google_drive": True,
                            "enable_nextcloud": False
                        }
                    else:
                        # Test用户默认使用Nextcloud
                        default_config = {
                            "default_cloud_provider": "nextcloud",
                            "large_file_threshold": int(os.getenv("LARGE_FILE_THRESHOLD", "5242880")),
                            "enable_google_drive": False,
                            "enable_nextcloud": True
                        }
                    
                    # 保存默认配置
                    storage_config = StorageConfig(
                        user_id=user_id,
                        config_key="storage_preferences",
                        config_value=default_config
                    )
                    db.add(storage_config)
                    db.commit()
                    
                    # 更新config
                    config.update(default_config)
        
        return config
    
    async def determine_storage_strategy(self, file_size: int, user_id: str, 
                                       db: Session, preferred_provider: str = None) -> Dict[str, Any]:
        """决定文件存储策略"""
        config = await self.get_storage_config(user_id, db)
        threshold = config["large_file_threshold"]
        
        logger.info(f"Storage strategy decision: file_size={file_size}, threshold={threshold}, user_id={user_id}")
        
        if file_size >= threshold:
            # 大文件存云盘
            provider = preferred_provider or config["default_cloud_provider"]
            logger.info(f"File size >= threshold, using provider: {provider}")
            
            # 检查用户是否已认证该云盘
            import uuid
            user_uuid = uuid.UUID(user_id)
            cloud_auth = db.query(CloudAuth).filter(
                CloudAuth.user_id == user_uuid,
                CloudAuth.provider == provider,
                CloudAuth.is_active == True
            ).first()
            
            logger.info(f"Cloud auth found: {cloud_auth is not None}")
            
            if not cloud_auth:
                logger.warning(f"No cloud auth found for user {user_id} and provider {provider}")
                return {
                    "strategy": "require_auth",
                    "provider": provider,
                    "message": f"请先连接{provider}云盘",
                    "available_providers": self._get_available_providers(user_id, db)
                }
            
            logger.info(f"Returning cloud strategy with folder_id: {cloud_auth.folder_id}")
            return {
                "strategy": "cloud",
                "provider": provider,
                "folder_id": cloud_auth.folder_id,
                "cloud_auth_id": str(cloud_auth.id)
            }
        else:
            # 小文件存本地
            logger.info(f"File size < threshold, using local storage")
            return {
                "strategy": "local",
                "path": "/app/uploads"
            }
    
    def _get_available_providers(self, user_id: str, db: Session) -> list:
        """获取用户可用的云盘提供商"""
        # 获取用户已认证的云盘
        user_auths = db.query(CloudAuth).filter(
            CloudAuth.user_id == user_id,
            CloudAuth.is_active == True
        ).all()
        
        authenticated_providers = [auth.provider for auth in user_auths]
        
        # 获取所有可用的云盘提供商
        all_providers = self.connector_service.get_available_providers()
        
        available = []
        for provider, info in all_providers.items():
            if info["enabled"]:
                available.append({
                    "provider": provider,
                    "display_name": info["display_name"],
                    "authenticated": provider in authenticated_providers
                })
        
        return available
    
    async def upload_file(self, file_content: bytes, filename: str, user_id: str, 
                         db: Session, preferred_provider: str = None) -> Dict[str, Any]:
        """智能文件上传"""
        try:
            file_size = len(file_content)
            
            # 决定存储策略
            strategy = await self.determine_storage_strategy(
                file_size, user_id, db, preferred_provider
            )
            
            if strategy["strategy"] == "require_auth":
                return {
                    "success": False,
                    "error": strategy["message"],
                    "auth_required": True,
                    "provider": strategy["provider"],
                    "available_providers": strategy["available_providers"]
                }
            
            # 根据策略上传文件
            if strategy["strategy"] == "local":
                return await self._upload_to_local(file_content, filename)
            
            elif strategy["strategy"] == "cloud":
                # 上传到云盘
                cloud_result = await self.connector_service.upload_to_cloud(
                    file_content, filename, user_id, strategy["provider"]
                )
                
                if cloud_result["success"]:
                    return {
                        "success": True,
                        "strategy": "cloud",
                        "provider": strategy["provider"],
                        "file_id": cloud_result["file_id"],
                        "file_size": file_size,
                        "source_uri": f"{strategy['provider']}://{cloud_result['file_id']}"
                    }
                else:
                    # 云盘上传失败，降级到本地存储
                    logger.warning(f"Cloud upload failed, falling back to local: {cloud_result.get('error')}")
                    return await self._upload_to_local(file_content, filename)
            
        except Exception as e:
            logger.error(f"File upload error: {e}")
            # 发生异常时，尝试本地存储作为降级方案
            try:
                return await self._upload_to_local(file_content, filename)
            except Exception as fallback_error:
                logger.error(f"Fallback to local storage also failed: {fallback_error}")
                return {
                    "success": False,
                    "error": f"Upload failed: {str(e)}"
                }
    
    async def _upload_to_local(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """上传文件到本地存储"""
        try:
            upload_dir = Path("/app/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成唯一文件名
            actual_filename = self._get_unique_filename(upload_dir, filename)
            file_path = upload_dir / actual_filename
            
            # 保存文件
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            return {
                "success": True,
                "strategy": "local",
                "file_path": str(file_path),
                "filename": actual_filename,
                "file_size": len(file_content),
                "source_uri": f"webui://{actual_filename}"
            }
            
        except Exception as e:
            logger.error(f"Local upload error: {e}")
            raise
    
    def _get_unique_filename(self, upload_dir: Path, original_filename: str) -> str:
        """生成唯一文件名，重名时添加时间戳"""
        base_path = upload_dir / original_filename
        
        if not base_path.exists():
            return original_filename
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_part = Path(original_filename).stem
        extension = Path(original_filename).suffix
        
        return f"{name_part}_{timestamp}{extension}"
    
    async def update_storage_config(self, user_id: str, config_data: Dict[str, Any], 
                                  db: Session) -> Dict[str, Any]:
        """更新用户存储配置"""
        try:
            for key, value in config_data.items():
                # 查找现有配置
                existing = db.query(StorageConfig).filter(
                    StorageConfig.user_id == user_id,
                    StorageConfig.config_key == key
                ).first()
                
                if existing:
                    existing.config_value = value
                    existing.updated_at = datetime.utcnow()
                else:
                    new_config = StorageConfig(
                        user_id=user_id,
                        config_key=key,
                        config_value=value
                    )
                    db.add(new_config)
            
            db.commit()
            return {"success": True, "message": "配置已更新"}
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update storage config: {e}")
            return {"success": False, "error": str(e)}
