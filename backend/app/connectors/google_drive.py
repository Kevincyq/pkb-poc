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
            "auth_url": auth_url,
            "state": state,
            "provider": "google_drive"
        }
    
    async def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        """处理Google OAuth回调"""
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
                response = await client.post(
                    'https://oauth2.googleapis.com/token',
                    data=token_data
                )
                
                if response.status_code != 200:
                    raise Exception(f"Token exchange failed: {response.text}")
                
                token_info = response.json()
                
                # 获取用户信息
                headers = {'Authorization': f"Bearer {token_info['access_token']}"}
                user_response = await client.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers=headers
                )
                
                if user_response.status_code != 200:
                    raise Exception(f"Failed to get user info: {user_response.text}")
                
                user_info = user_response.json()
                
                return {
                    "success": True,
                    "access_token": token_info['access_token'],
                    "refresh_token": token_info.get('refresh_token'),
                    "expires_in": token_info.get('expires_in', 3600),
                    "user_info": user_info
                }
                
        except Exception as e:
            logger.error(f"Google OAuth callback error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_folder(self, folder_name: str, user_id: str) -> str:
        """创建PKB专用文件夹"""
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
                
                # 创建文件夹的元数据
                folder_metadata = {
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder"
                }
                
                async with httpx.AsyncClient() as client:
                    headers = {
                        'Authorization': f"Bearer {cloud_auth.access_token}",
                        'Content-Type': 'application/json'
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
                    
                    logger.info(f"Created Google Drive folder: {folder_id}")
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
            # 这里需要实现实际的token刷新逻辑
            logger.info(f"Refreshing Google Drive token for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh Google Drive token: {e}")
            return False
