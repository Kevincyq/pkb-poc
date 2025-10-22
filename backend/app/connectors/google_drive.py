"""
Google Drive连接器实现
"""
import os
import uuid
import httpx
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base import CloudStorageConnector

logger = logging.getLogger(__name__)

class GoogleDriveConnector(CloudStorageConnector):
    """Google Drive连接器"""
    
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        self.app_folder_name = "PKB-Files"  # 专用文件夹名称
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning("Google Drive配置不完整，连接器可能无法正常工作")
    
    def get_provider_name(self) -> str:
        return "google_drive"
    
    async def authenticate(self, user_id: str) -> Dict[str, Any]:
        """生成Google OAuth授权URL"""
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.error("Google OAuth配置不完整")
            return {
                "success": False,
                "error": "Google OAuth配置不完整。请设置以下环境变量：GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI"
            }
        
        scope = 'https://www.googleapis.com/auth/drive.file'
        state = f"gdrive_{user_id}_{uuid.uuid4()}"
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={scope}&"
            f"response_type=code&"
            f"state={state}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        
        return {
            "success": True,
            "auth_url": auth_url,
            "state": state,
            "provider": "google_drive"
        }
    
    async def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        """处理Google OAuth回调 - 简化版本，只关注Drive访问权限"""
        try:
            # 用code换取token
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                # 步骤1：换取access_token
                response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data=token_data
                )
                
                if response.status_code != 200:
                    raise Exception(f"Token exchange failed: {response.text}")
                
                token_info = response.json()
                access_token = token_info['access_token']
                logger.info(f"Token exchange successful, access_token: {access_token[:20]}...")
                
                # 步骤2：测试Drive API访问权限
                headers = {'Authorization': f"Bearer {access_token}"}
                logger.info("Testing Drive API access...")
                
                drive_response = await client.get(
                    'https://www.googleapis.com/drive/v3/about?fields=user',
                    headers=headers
                )
                
                logger.info(f"Drive API response status: {drive_response.status_code}")
                
                if drive_response.status_code != 200:
                    raise Exception(f"Drive API access failed: {drive_response.text}")
                
                # 步骤3：获取Drive用户信息（用于确认访问权限）
                drive_user_info = drive_response.json()
                user_email = drive_user_info.get('user', {}).get('emailAddress', 'unknown')
                logger.info(f"Drive access confirmed for user: {user_email}")
                
                return {
                    "success": True,
                    "access_token": access_token,
                    "refresh_token": token_info.get('refresh_token'),
                    "expires_in": token_info.get('expires_in', 3600),
                    "drive_user_email": user_email,
                    "drive_access_confirmed": True
                }
                
        except Exception as e:
            logger.error(f"Google OAuth callback error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_folder(self, folder_name: str, user_id: str) -> str:
        """创建或获取PKB专用文件夹"""
        try:
            # 从数据库获取用户的access_token
            from sqlalchemy.orm import Session
            from app.db import SessionLocal
            from app.models import CloudAuth
            
            db = SessionLocal()
            try:
                cloud_auth = db.query(CloudAuth).filter(
                    CloudAuth.user_id == user_id,
                    CloudAuth.provider == "google_drive",
                    CloudAuth.is_active == True
                ).first()
                
                if not cloud_auth or not cloud_auth.access_token:
                    raise Exception("No valid Google Drive access token found")
                
                # 如果已经有folder_id，直接返回
                if cloud_auth.folder_id:
                    logger.info(f"Using existing Google Drive folder: {cloud_auth.folder_id}")
                    return cloud_auth.folder_id
                
                # 检查是否已存在同名文件夹
                async with httpx.AsyncClient() as client:
                    headers = {
                        'Authorization': f"Bearer {cloud_auth.access_token}",
                        'Content-Type': 'application/json'
                    }
                    
                    # 搜索已存在的文件夹
                    search_params = {
                        'q': f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                        'fields': 'files(id,name)'
                    }
                    
                    search_response = await client.get(
                        'https://www.googleapis.com/drive/v3/files',
                        headers=headers,
                        params=search_params
                    )
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        existing_folders = search_data.get('files', [])
                        
                        # 如果找到同名文件夹，使用第一个
                        if existing_folders:
                            folder_id = existing_folders[0]['id']
                            logger.info(f"Found existing Google Drive folder: {folder_id}")
                            
                            # 更新数据库中的folder_id
                            cloud_auth.folder_id = folder_id
                            db.commit()
                            
                            return folder_id
                    
                    # 如果没有找到现有文件夹，创建新文件夹
                    folder_metadata = {
                        "name": folder_name,
                        "mimeType": "application/vnd.google-apps.folder"
                    }
                    
                    response = await client.post(
                        'https://www.googleapis.com/drive/v3/files',
                        headers=headers,
                        json=folder_metadata
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Failed to create folder: {response.text}")
                    
                    folder_data = response.json()
                    folder_id = folder_data['id']
                    
                    logger.info(f"Created new Google Drive folder: {folder_id}")
                    
                    # 更新数据库中的folder_id
                    cloud_auth.folder_id = folder_id
                    db.commit()
                    
                    return folder_id
                    
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Failed to create Google Drive folder: {e}")
            raise
    
    async def upload_file(self, file_content: bytes, filename: str, user_id: str) -> Dict[str, Any]:
        """上传文件到Google Drive"""
        try:
            # 从数据库获取用户的access_token和folder_id
            from sqlalchemy.orm import Session
            from app.db import SessionLocal
            from app.models import CloudAuth
            from datetime import datetime
            
            db = SessionLocal()
            try:
                cloud_auth = db.query(CloudAuth).filter(
                    CloudAuth.user_id == user_id,
                    CloudAuth.provider == "google_drive",
                    CloudAuth.is_active == True
                ).first()
                
                if not cloud_auth or not cloud_auth.access_token:
                    raise Exception("No valid Google Drive access token found")
                
                if not cloud_auth.folder_id:
                    raise Exception("No Google Drive folder ID found")
                
                # 检查token是否过期，如果过期则刷新
                if cloud_auth.token_expires_at and cloud_auth.token_expires_at <= datetime.utcnow():
                    logger.info(f"Google Drive token expired, refreshing for user: {user_id}")
                    refresh_success = await self.refresh_token(user_id)
                    if not refresh_success:
                        raise Exception("Failed to refresh expired Google Drive token")
                    
                    # 重新获取更新后的token
                    db.refresh(cloud_auth)
                
                # 创建文件元数据
                file_metadata = {
                    "name": filename,
                    "parents": [cloud_auth.folder_id]
                }
                
                async with httpx.AsyncClient() as client:
                    # 上传文件
                    headers = {
                        'Authorization': f"Bearer {cloud_auth.access_token}"
                    }
                    
                    import json
                    files = {
                        'metadata': (None, json.dumps(file_metadata), 'application/json'),
                        'file': (filename, file_content)
                    }
                    
                    response = await client.post(
                        'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
                        headers=headers,
                        files=files
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Failed to upload file: {response.text}")
                    
                    file_data = response.json()
                    file_id = file_data['id']
                    
                    return {
                        "success": True,
                        "file_id": file_id,
                        "filename": filename,
                        "file_size": len(file_content),
                        "provider": "google_drive"
                    }
                    
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Failed to upload file to Google Drive: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_file(self, file_id: str, user_id: str) -> bytes:
        """从Google Drive下载文件"""
        try:
            # 从数据库获取用户的access_token
            from sqlalchemy.orm import Session
            from app.db import SessionLocal
            from app.models import CloudAuth
            from datetime import datetime
            
            db = SessionLocal()
            try:
                cloud_auth = db.query(CloudAuth).filter(
                    CloudAuth.user_id == user_id,
                    CloudAuth.provider == "google_drive",
                    CloudAuth.is_active == True
                ).first()
                
                if not cloud_auth or not cloud_auth.access_token:
                    raise Exception("No valid Google Drive access token found")
                
                # 检查token是否过期，如果过期则刷新
                if cloud_auth.token_expires_at and cloud_auth.token_expires_at <= datetime.utcnow():
                    logger.info(f"Google Drive token expired, refreshing for user: {user_id}")
                    refresh_success = await self.refresh_token(user_id)
                    if not refresh_success:
                        raise Exception("Failed to refresh expired Google Drive token")
                    
                    # 重新获取更新后的token
                    db.refresh(cloud_auth)
                
                async with httpx.AsyncClient() as client:
                    headers = {
                        'Authorization': f"Bearer {cloud_auth.access_token}"
                    }
                    
                    response = await client.get(
                        f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media',
                        headers=headers
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Failed to download file: {response.text}")
                    
                    return response.content
                    
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Failed to download file from Google Drive: {e}")
            raise
    
    async def get_thumbnail(self, file_id: str, user_id: str) -> bytes:
        """获取Google Drive文件缩略图"""
        try:
            # 从数据库获取用户的access_token
            from sqlalchemy.orm import Session
            from app.db import SessionLocal
            from app.models import CloudAuth
            
            db = SessionLocal()
            try:
                cloud_auth = db.query(CloudAuth).filter(
                    CloudAuth.user_id == user_id,
                    CloudAuth.provider == "google_drive",
                    CloudAuth.is_active == True
                ).first()
                
                if not cloud_auth or not cloud_auth.access_token:
                    raise Exception("No valid Google Drive access token found")
                
                async with httpx.AsyncClient() as client:
                    headers = {
                        'Authorization': f"Bearer {cloud_auth.access_token}"
                    }
                    
                    response = await client.get(
                        f'https://www.googleapis.com/drive/v3/files/{file_id}/thumbnail?sz=300',
                        headers=headers
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Failed to get thumbnail: {response.text}")
                    
                    return response.content
                    
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Failed to get thumbnail from Google Drive: {e}")
            raise
    
    async def list_files(self, user_id: str, folder_path: str = None) -> List[Dict]:
        """列出Google Drive文件"""
        try:
            # 这里需要实现实际的Google Drive API文件列表
            # 暂时返回模拟数据
            return []
            
        except Exception as e:
            logger.error(f"Failed to list files from Google Drive: {e}")
            return []
    
    async def refresh_token(self, user_id: str) -> bool:
        """刷新Google Drive访问令牌"""
        try:
            # 从数据库获取用户的refresh_token
            from sqlalchemy.orm import Session
            from app.db import SessionLocal
            from app.models import CloudAuth
            from datetime import datetime, timedelta
            
            db = SessionLocal()
            try:
                cloud_auth = db.query(CloudAuth).filter(
                    CloudAuth.user_id == user_id,
                    CloudAuth.provider == "google_drive",
                    CloudAuth.is_active == True
                ).first()
                
                if not cloud_auth or not cloud_auth.refresh_token:
                    logger.error(f"No refresh token found for user: {user_id}")
                    return False
                
                # 使用refresh_token获取新的access_token
                token_data = {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'refresh_token': cloud_auth.refresh_token,
                    'grant_type': 'refresh_token'
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        'https://oauth2.googleapis.com/token',
                        data=token_data
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Token refresh failed: {response.text}")
                        return False
                    
                    token_info = response.json()
                    new_access_token = token_info['access_token']
                    expires_in = token_info.get('expires_in', 3600)
                    
                    # 更新数据库中的token信息
                    cloud_auth.access_token = new_access_token
                    cloud_auth.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                    cloud_auth.updated_at = datetime.utcnow()
                    db.commit()
                    
                    logger.info(f"Successfully refreshed Google Drive token for user: {user_id}")
                    return True
                    
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Failed to refresh Google Drive token: {e}")
            return False
