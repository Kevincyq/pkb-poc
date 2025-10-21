"""
用户认证API
"""
import os
import uuid
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
import jwt

from app.db import get_db
from app.models import User, CloudAuth, StorageConfig
from ..services.cloud_connector_service import CloudConnectorService
from ..services.storage_strategy_service import StorageStrategyService

router = APIRouter()
logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRE_MINUTES', 1440))  # 24小时

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash

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

@router.post("/auth/login")
async def user_login(username: str, password: str, db: Session = Depends(get_db)):
    """用户登录（用户名/密码）"""
    try:
        # 查找用户
        user = db.query(User).filter(User.email == username).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 验证密码
        if not user.password_hash:
            raise HTTPException(status_code=401, detail="用户密码未设置")
        
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 生成JWT token
        jwt_token = create_jwt_token(user)
        
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "is_google_user": user.google_id is not None
            },
            "token": jwt_token,
            "message": "登录成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")

@router.get("/auth/google")
async def google_auth(current_user: User = Depends(get_current_user)):
    """启动Google OAuth认证（需要先登录）"""
    try:
        # 检查用户是否是Google用户
        if not current_user.google_id:
            raise HTTPException(status_code=400, detail="当前用户不是Google用户")
        
        connector_service = CloudConnectorService()
        google_connector = connector_service.get_connector("google_drive")
        
        # 使用当前用户ID进行OAuth认证
        auth_info = await google_connector.authenticate(str(current_user.id))
        
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
        
        # 查找对应的用户（基于Google ID）
        user = db.query(User).filter(User.google_id == user_info["id"]).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在，请先完成用户注册")
        
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

@router.post("/auth/register")
async def user_register(username: str, password: str, display_name: str = None, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.email == username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="用户已存在")
        
        # 创建新用户
        user = User(
            google_id=None,  # 注册时没有Google ID
            email=username,
            password_hash=hash_password(password),  # 哈希密码
            display_name=display_name or username.split("@")[0],
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建默认存储配置（新用户默认使用Nextcloud）
        default_configs = [
            ("large_file_threshold", 5 * 1024 * 1024),  # 5MB
            ("default_cloud_provider", "nextcloud"),
            ("enable_google_drive", False),
            ("enable_nextcloud", True),
            ("thumbnail_size", {"width": 300, "height": 200}),
            ("thumbnail_quality", 85)
        ]
        
        for key, value in default_configs:
            config = StorageConfig(
                user_id=user.id,
                config_key=key,
                config_value=value
            )
            db.add(config)
        
        # 为新用户创建Nextcloud认证
        nextcloud_auth = CloudAuth(
            user_id=user.id,
            provider="nextcloud",
            access_token=os.getenv("NC_PASS"),  # 使用系统密码
            refresh_token=None,
            token_expires_at=None,
            folder_id=os.getenv("NC_INBOX_FOLDER", "PKB-Inbox"),
            is_active=True
        )
        db.add(nextcloud_auth)
        
        db.commit()
        
        # 生成JWT token
        jwt_token = create_jwt_token(user)
        
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "is_google_user": False
            },
            "token": jwt_token,
            "message": "注册成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Register error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

@router.post("/auth/register-google")
async def register_google_user(username: str, password: str, google_id: str, display_name: str = None, db: Session = Depends(get_db)):
    """注册Google用户"""
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.email == username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="用户已存在")
        
        # 检查Google ID是否已被使用
        existing_google_user = db.query(User).filter(User.google_id == google_id).first()
        if existing_google_user:
            raise HTTPException(status_code=400, detail="Google账号已被使用")
        
        # 创建Google用户
        user = User(
            google_id=google_id,
            email=username,
            password_hash=hash_password(password),  # 哈希密码
            display_name=display_name or username.split("@")[0],
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 创建默认存储配置（Google用户默认使用Google Drive）
        default_configs = [
            ("large_file_threshold", 5 * 1024 * 1024),  # 5MB
            ("default_cloud_provider", "google_drive"),
            ("enable_google_drive", True),
            ("enable_nextcloud", False),
            ("thumbnail_size", {"width": 300, "height": 200}),
            ("thumbnail_quality", 85)
        ]
        
        for key, value in default_configs:
            config = StorageConfig(
                user_id=user.id,
                config_key=key,
                config_value=value
            )
            db.add(config)
        
        db.commit()
        
        # 生成JWT token
        jwt_token = create_jwt_token(user)
        
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "is_google_user": True
            },
            "token": jwt_token,
            "message": "Google用户注册成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google register error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")
@router.post("/auth/test-login")
async def test_login(username: str, password: str, db: Session = Depends(get_db)):
    """Test用户登录"""
    try:
        # 验证用户名和密码
        if username != "test" or password != "test":
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 查找test用户
        test_user = db.query(User).filter(User.email == "test@pkb.local").first()
        
        if not test_user:
            raise HTTPException(status_code=404, detail="Test用户不存在")
        
        # 检查test用户是否有Nextcloud认证
        nextcloud_auth = db.query(CloudAuth).filter(
            CloudAuth.user_id == test_user.id,
            CloudAuth.provider == "nextcloud"
        ).first()
        
        if not nextcloud_auth:
            # 为test用户创建Nextcloud认证（使用系统凭据）
            nextcloud_auth = CloudAuth(
                user_id=test_user.id,
                provider="nextcloud",
                access_token=os.getenv("NC_PASS"),  # 使用系统密码作为token
                refresh_token=None,
                token_expires_at=None,
                folder_id=os.getenv("NC_INBOX_FOLDER", "PKB-Inbox"),
                is_active=True
            )
            db.add(nextcloud_auth)
            db.commit()
        
        # 生成JWT token
        jwt_token = create_jwt_token(test_user)
        
        return {
            "success": True,
            "user": {
                "id": str(test_user.id),
                "email": test_user.email,
                "display_name": test_user.display_name,
                "avatar_url": test_user.avatar_url,
                "is_google_user": False
            },
            "token": jwt_token,
            "message": "Test用户登录成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test login error: {e}")
        raise HTTPException(status_code=500, detail=f"Test登录失败: {str(e)}")

@router.post("/auth/logout")
async def logout():
    """用户登出"""
    return {"success": True, "message": "登出成功"}

@router.get("/cloud/providers")
async def get_cloud_providers(current_user: User = Depends(get_current_user)):
    """获取可用的云盘提供商列表"""
    providers = []
    
    # 根据用户类型返回可用提供商
    if current_user.google_id:
        # Google用户只能使用Google Drive
        providers.append({
            "provider": "google_drive",
            "display_name": "Google Drive",
            "enabled": True,
            "is_default": True
        })
    else:
        # Test用户只能使用Nextcloud
        providers.append({
            "provider": "nextcloud",
            "display_name": "Nextcloud",
            "enabled": True,
            "is_default": True
        })
    
    return {"providers": providers}

@router.get("/cloud/status")
async def get_cloud_status(current_user: User = Depends(get_current_user), 
                          db: Session = Depends(get_db)):
    """获取云盘连接状态"""
    status = {}
    
    # 根据用户类型检查对应云盘状态
    if current_user.google_id:
        # Google用户检查Google Drive状态
        cloud_auth = db.query(CloudAuth).filter(
            CloudAuth.user_id == current_user.id,
            CloudAuth.provider == "google_drive",
            CloudAuth.is_active == True
        ).first()
        
        if cloud_auth:
            status["google_drive"] = {
                "connected": True,
                "folder_id": cloud_auth.folder_id,
                "expires_at": cloud_auth.token_expires_at.isoformat() if cloud_auth.token_expires_at else None
            }
        else:
            status["google_drive"] = {"connected": False}
    else:
        # Test用户检查Nextcloud状态
        cloud_auth = db.query(CloudAuth).filter(
            CloudAuth.user_id == current_user.id,
            CloudAuth.provider == "nextcloud",
            CloudAuth.is_active == True
        ).first()
        
        if cloud_auth:
            status["nextcloud"] = {
                "connected": True,
                "folder_id": cloud_auth.folder_id
            }
        else:
            status["nextcloud"] = {"connected": False}
    
    return status

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
