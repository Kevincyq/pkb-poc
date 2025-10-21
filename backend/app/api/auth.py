"""
用户认证API
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
import jwt

from app.db import get_db
from app.models import User, CloudAuth, StorageConfig
from app.services.cloud_connector_service import CloudConnectorService
from app.services.storage_strategy_service import StorageStrategyService

router = APIRouter()
logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRE_MINUTES', 1440))  # 24小时

def create_jwt_token(user: User) -> str:
    """创建JWT token"""
    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """验证JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """获取当前用户"""
    # 从Authorization header获取token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.split(" ")[1]
    payload = verify_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user

@router.get("/auth/google")
async def google_auth():
    """启动Google OAuth认证"""
    try:
        connector_service = CloudConnectorService()
        google_connector = connector_service.get_connector("google_drive")
        
        # 生成临时用户ID（实际应用中可能从session获取）
        temp_user_id = str(uuid.uuid4())
        auth_info = await google_connector.authenticate(temp_user_id)
        
        return {
            "auth_url": auth_info["auth_url"],
            "state": auth_info["state"],
            "provider": auth_info["provider"]
        }
        
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(status_code=500, detail=f"认证启动失败: {str(e)}")

@router.get("/auth/callback/gdrive")
async def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Google OAuth回调处理"""
    try:
        connector_service = CloudConnectorService()
        google_connector = connector_service.get_connector("google_drive")
        
        # 处理OAuth回调
        callback_result = await google_connector.handle_callback(code, state)
        
        if not callback_result["success"]:
            raise HTTPException(status_code=400, detail=f"OAuth回调失败: {callback_result.get('error')}")
        
        user_info = callback_result["user_info"]
        
        # 创建或更新用户
        user = db.query(User).filter(User.google_id == user_info["id"]).first()
        
        if not user:
            user = User(
                google_id=user_info["id"],
                email=user_info["email"],
                display_name=user_info.get("name", user_info["email"].split("@")[0]),
                avatar_url=user_info.get("picture"),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # 创建默认存储配置
            await create_default_storage_config(user.id, db)
        else:
            # 更新用户信息
            user.display_name = user_info.get("name", user.display_name)
            user.avatar_url = user_info.get("picture", user.avatar_url)
            user.updated_at = datetime.utcnow()
            db.commit()
        
        # 存储云盘认证信息
        cloud_auth = db.query(CloudAuth).filter(
            and_(CloudAuth.user_id == user.id, CloudAuth.provider == "google_drive")
        ).first()
        
        if not cloud_auth:
            cloud_auth = CloudAuth(
                user_id=user.id,
                provider="google_drive",
                access_token=callback_result["access_token"],
                refresh_token=callback_result.get("refresh_token"),
                token_expires_at=datetime.utcnow() + timedelta(seconds=callback_result["expires_in"]),
                is_active=True
            )
            db.add(cloud_auth)
            db.commit()
            db.refresh(cloud_auth)
        else:
            # 更新认证信息
            cloud_auth.access_token = callback_result["access_token"]
            cloud_auth.refresh_token = callback_result.get("refresh_token")
            cloud_auth.token_expires_at = datetime.utcnow() + timedelta(seconds=callback_result["expires_in"])
            cloud_auth.updated_at = datetime.utcnow()
            db.commit()
        
        # 创建Google Drive专用文件夹
        try:
            folder_id = await google_connector.create_folder("PKB-Files", str(user.id))
            cloud_auth.folder_id = folder_id
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to create Google Drive folder: {e}")
        
        # 生成JWT token
        jwt_token = create_jwt_token(user)
        
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url
            },
            "token": jwt_token,
            "redirect_url": "/dashboard"
        }
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        return {
            "success": False,
            "error": str(e),
            "redirect_url": "/login?error=oauth_failed"
        }

@router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user), 
                               db: Session = Depends(get_db)):
    """获取当前用户信息"""
    # 获取用户云盘认证状态
    cloud_auths = db.query(CloudAuth).filter(
        CloudAuth.user_id == current_user.id,
        CloudAuth.is_active == True
    ).all()
    
    auth_status = {
        auth.provider: {
            "is_authenticated": True,
            "folder_id": auth.folder_id,
            "expires_at": auth.token_expires_at.isoformat() if auth.token_expires_at else None
        }
        for auth in cloud_auths
    }
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url,
        "cloud_auth_status": auth_status
    }

@router.post("/auth/logout")
async def logout():
    """用户登出"""
    return {"success": True, "message": "登出成功"}

@router.get("/cloud/providers")
async def get_cloud_providers():
    """获取可用的云盘提供商列表"""
    connector_service = CloudConnectorService()
    providers = connector_service.get_available_providers()
    
    return {
        "providers": [
            {
                "provider": provider,
                "display_name": info["display_name"],
                "enabled": info["enabled"]
            }
            for provider, info in providers.items()
        ]
    }

@router.get("/cloud/status")
async def get_cloud_status(current_user: User = Depends(get_current_user), 
                          db: Session = Depends(get_db)):
    """获取用户云盘连接状态"""
    cloud_auths = db.query(CloudAuth).filter(
        CloudAuth.user_id == current_user.id,
        CloudAuth.is_active == True
    ).all()
    
    connector_service = CloudConnectorService()
    available_providers = connector_service.get_available_providers()
    
    status = {}
    for provider, info in available_providers.items():
        auth = next((auth for auth in cloud_auths if auth.provider == provider), None)
        
        status[provider] = {
            "display_name": info["display_name"],
            "enabled": info["enabled"],
            "authenticated": auth is not None,
            "folder_id": auth.folder_id if auth else None,
            "expires_at": auth.token_expires_at.isoformat() if auth and auth.token_expires_at else None
        }
    
    return {"cloud_status": status}

async def create_default_storage_config(user_id: str, db: Session):
    """创建用户默认存储配置"""
    try:
        default_configs = [
            ("large_file_threshold", 5 * 1024 * 1024),  # 5MB
            ("default_cloud_provider", "google_drive"),
            ("thumbnail_size", {"width": 300, "height": 200}),
            ("thumbnail_quality", 85)
        ]
        
        for key, value in default_configs:
            config = StorageConfig(
                user_id=user_id,
                config_key=key,
                config_value=value
            )
            db.add(config)
        
        db.commit()
        logger.info(f"Created default storage config for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to create default storage config: {e}")
        db.rollback()
