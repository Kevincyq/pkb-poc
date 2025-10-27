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
from pydantic import BaseModel

from app.db import get_db
from app.models import User, CloudAuth, StorageConfig
from ..services.cloud_connector_service import CloudConnectorService
from ..services.storage_strategy_service import StorageStrategyService
from ..services.google_auth_service import google_auth_service

router = APIRouter()
logger = logging.getLogger(__name__)

# 请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

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
async def user_login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """统一用户登录（支持test用户和Google用户）"""
    try:
        # 查找用户
        user = db.query(User).filter(User.email == login_data.username).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 检查用户类型并验证
        if user.google_id:
            # Google用户：需要与Google IDP认证
            if not await verify_google_user_credentials(login_data.username, login_data.password):
                raise HTTPException(status_code=401, detail="Google用户认证失败")
        else:
            # Test用户或其他本地用户：直接验证密码
            if not user.password_hash:
                raise HTTPException(status_code=401, detail="用户密码未设置")
            
            if not verify_password(login_data.password, user.password_hash):
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

async def verify_google_user_credentials(email: str, password: str) -> bool:
    """验证Google用户凭据（使用真实Google认证API）"""
    try:
        # 使用Google Identity Platform验证密码
        result = await google_auth_service.verify_password(email, password)
        
        if result["success"]:
            logger.info(f"Google user {email} authenticated successfully")
            return True
        else:
            logger.warning(f"Google user {email} authentication failed: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Google user verification error: {e}")
        return False

@router.get("/auth/google")
async def google_auth():
    """启动Google OAuth认证（直接OAuth登录）"""
    try:
        connector_service = CloudConnectorService()
        google_connector = connector_service.get_connector("google_drive")
        
        # 生成临时用户ID（实际应用中可能从session获取）
        temp_user_id = str(uuid.uuid4())
        auth_info = await google_connector.authenticate(temp_user_id)
        
        if not auth_info.get("success", True):
            raise HTTPException(status_code=400, detail=auth_info.get("error", "Google OAuth配置错误"))
        
        return {
            "auth_url": auth_info["auth_url"],
            "state": auth_info["state"],
            "provider": auth_info["provider"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(status_code=500, detail=f"认证启动失败: {str(e)}")

@router.get("/auth/callback/gdrive")
async def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Google OAuth回调处理 - 简化版本，只处理Drive访问权限"""
    try:
        connector_service = CloudConnectorService()
        google_connector = connector_service.get_connector("google_drive")
        
        # 处理OAuth回调
        callback_result = await google_connector.handle_callback(code, state)
        
        if not callback_result["success"]:
            raise HTTPException(status_code=400, detail=f"OAuth回调失败: {callback_result.get('error')}")
        
        # 获取Drive用户邮箱
        drive_user_email = callback_result.get("drive_user_email", "unknown")
        
        # 查找或创建用户（基于邮箱）
        user = db.query(User).filter(User.email == drive_user_email).first()
        
        if not user:
            # 创建Google Drive用户（简化版本）
            user = User(
                email=drive_user_email,
                display_name=drive_user_email.split("@")[0],  # 使用邮箱前缀作为显示名
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # 创建默认存储配置（Google Drive用户默认使用Google Drive）
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
        
        # 创建或获取Google Drive专用文件夹
        try:
            folder_id = await google_connector.create_folder("PKB-Files", str(user.id))
            # create_folder方法内部已经更新了cloud_auth.folder_id，这里不需要再次设置
            logger.info(f"Google Drive folder ready: {folder_id}")
        except Exception as e:
            logger.warning(f"Failed to create/get Google Drive folder: {e}")
        
        # 生成JWT token
        jwt_token = create_jwt_token(user)
        
        # 准备用户信息（直接返回，避免前端再调用API）
        import urllib.parse
        import json
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "is_google_user": user.google_id is not None
        }
        user_json = json.dumps(user_data)
        user_param = urllib.parse.quote(user_json)
        
        # 构建前端URL（使用前端域名而非后端域名）
        frontend_url = os.getenv('FRONTEND_BASE_URL', 'https://test-pkb.kmchat.cloud')
        frontend_url = f"{frontend_url}/auth/callback"
        
        # 将token、用户信息和云盘状态通过URL参数传递给前端
        redirect_url = f"{frontend_url}?token={jwt_token}&user={user_param}&success=true"
        
        # 返回重定向响应
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        # 构建错误重定向URL
        import urllib.parse
        frontend_url = os.getenv('FRONTEND_BASE_URL', 'https://test-pkb.kmchat.cloud')
        frontend_url = f"{frontend_url}/auth/callback"
        error_param = urllib.parse.quote(str(e))
        redirect_url = f"{frontend_url}?success=false&error={error_param}"
        return RedirectResponse(url=redirect_url)

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

@router.post("/auth/register-google")
async def register_google_user(login_data: LoginRequest, display_name: str = None, db: Session = Depends(get_db)):
    """注册Google用户（使用真实Google认证）"""
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.email == login_data.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="用户已存在")
        
        # 使用Google Identity Platform创建用户
        google_result = await google_auth_service.create_user(
            login_data.username, 
            login_data.password, 
            display_name
        )
        
        if not google_result["success"]:
            raise HTTPException(status_code=400, detail=f"Google用户创建失败: {google_result.get('error')}")
        
        user_info = google_result["user_info"]
        
        # 创建本地用户记录
        user = User(
            google_id=user_info["id"],
            email=user_info["email"],
            display_name=user_info["display_name"],
            avatar_url=None,
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

@router.post("/auth/logout")
async def logout():
    """用户登出"""
    return {"success": True, "message": "登出成功"}

@router.get("/cloud/providers")
async def get_cloud_providers(current_user: User = Depends(get_current_user), 
                            db: Session = Depends(get_db)):
    """获取可用的云盘提供商列表"""
    providers = []
    
    # 根据用户类型返回可用提供商
    # 检查是否有Google Drive认证记录
    google_auth = db.query(CloudAuth).filter(
        CloudAuth.user_id == current_user.id,
        CloudAuth.provider == "google_drive",
        CloudAuth.is_active == True
    ).first()
    
    if google_auth:
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
    
    # 检查用户的云盘认证状态
    cloud_auths = db.query(CloudAuth).filter(
        CloudAuth.user_id == current_user.id,
        CloudAuth.is_active == True
    ).all()
    
    for auth in cloud_auths:
        if auth.provider == "google_drive":
            status["google_drive"] = {
                "connected": True,
                "folder_id": auth.folder_id,
                "expires_at": auth.token_expires_at.isoformat() if auth.token_expires_at else None
            }
        elif auth.provider == "nextcloud":
            status["nextcloud"] = {
                "connected": True,
                "folder_id": auth.folder_id
            }
    
    # 如果没有找到认证记录，设置默认状态
    if "google_drive" not in status:
        status["google_drive"] = {"connected": False}
    if "nextcloud" not in status:
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
