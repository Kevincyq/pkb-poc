"""
Google认证服务
"""
import os
import logging
import httpx
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class GoogleAuthService:
    """Google认证服务"""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_PROJECT_ID")
        self.service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        self.firebase_api_key = os.getenv("GOOGLE_FIREBASE_API_KEY")
        
        if not self.project_id:
            logger.warning("GOOGLE_PROJECT_ID not set, Google authentication will be disabled")
        
        if not self.firebase_api_key:
            logger.warning("GOOGLE_FIREBASE_API_KEY not set, Google authentication will be disabled")
    
    async def verify_password(self, email: str, password: str) -> Dict[str, Any]:
        """
        使用Google Identity Platform验证用户密码
        
        Args:
            email: 用户邮箱
            password: 用户密码
            
        Returns:
            Dict包含验证结果和用户信息
        """
        try:
            if not self.firebase_api_key:
                logger.warning("Google Firebase API key not configured, skipping Firebase authentication")
                return {"success": False, "error": "Firebase authentication not configured"}
            
            # 使用Firebase Auth REST API验证密码
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.firebase_api_key}"
            
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "user_info": {
                            "id": data.get("localId"),
                            "email": data.get("email"),
                            "display_name": data.get("displayName", email.split("@")[0]),
                            "email_verified": data.get("emailVerified", False),
                            "provider": "password"
                        },
                        "access_token": data.get("idToken"),
                        "refresh_token": data.get("refreshToken"),
                        "expires_in": data.get("expiresIn", 3600)
                    }
                else:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", "Authentication failed")
                    logger.error(f"Google authentication failed: {error_message}")
                    return {
                        "success": False,
                        "error": error_message
                    }
                    
        except Exception as e:
            logger.error(f"Google authentication error: {e}")
            return {
                "success": False,
                "error": f"Authentication service error: {str(e)}"
            }
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        验证Google ID Token
        
        Args:
            id_token: Google ID Token
            
        Returns:
            Dict包含验证结果和用户信息
        """
        try:
            if not self.firebase_api_key:
                logger.error("Google Firebase API key not configured")
                return {"success": False, "error": "Google authentication not configured"}
            
            # 使用Firebase Auth REST API验证ID Token
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={self.firebase_api_key}"
            
            payload = {
                "idToken": id_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    users = data.get("users", [])
                    if users:
                        user = users[0]
                        return {
                            "success": True,
                            "user_info": {
                                "id": user.get("localId"),
                                "email": user.get("email"),
                                "display_name": user.get("displayName", user.get("email", "").split("@")[0]),
                                "email_verified": user.get("emailVerified", False),
                                "provider": "google.com"
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "error": "User not found"
                        }
                else:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", "Token verification failed")
                    logger.error(f"Google token verification failed: {error_message}")
                    return {
                        "success": False,
                        "error": error_message
                    }
                    
        except Exception as e:
            logger.error(f"Google token verification error: {e}")
            return {
                "success": False,
                "error": f"Token verification service error: {str(e)}"
            }
    
    async def create_user(self, email: str, password: str, display_name: str = None) -> Dict[str, Any]:
        """
        创建Google用户
        
        Args:
            email: 用户邮箱
            password: 用户密码
            display_name: 显示名称
            
        Returns:
            Dict包含创建结果和用户信息
        """
        try:
            if not self.firebase_api_key:
                logger.error("Google Firebase API key not configured")
                return {"success": False, "error": "Google authentication not configured"}
            
            # 使用Firebase Auth REST API创建用户
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.firebase_api_key}"
            
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            if display_name:
                payload["displayName"] = display_name
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "user_info": {
                            "id": data.get("localId"),
                            "email": data.get("email"),
                            "display_name": data.get("displayName", email.split("@")[0]),
                            "email_verified": data.get("emailVerified", False),
                            "provider": "password"
                        },
                        "access_token": data.get("idToken"),
                        "refresh_token": data.get("refreshToken"),
                        "expires_in": data.get("expiresIn", 3600)
                    }
                else:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", "User creation failed")
                    logger.error(f"Google user creation failed: {error_message}")
                    return {
                        "success": False,
                        "error": error_message
                    }
                    
        except Exception as e:
            logger.error(f"Google user creation error: {e}")
            return {
                "success": False,
                "error": f"User creation service error: {str(e)}"
            }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新Google访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            Dict包含新的访问令牌
        """
        try:
            if not self.firebase_api_key:
                logger.error("Google Firebase API key not configured")
                return {"success": False, "error": "Google authentication not configured"}
            
            # 使用Firebase Auth REST API刷新令牌
            url = f"https://securetoken.googleapis.com/v1/token?key={self.firebase_api_key}"
            
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "access_token": data.get("access_token"),
                        "refresh_token": data.get("refresh_token"),
                        "expires_in": data.get("expires_in", 3600)
                    }
                else:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", "Token refresh failed")
                    logger.error(f"Google token refresh failed: {error_message}")
                    return {
                        "success": False,
                        "error": error_message
                    }
                    
        except Exception as e:
            logger.error(f"Google token refresh error: {e}")
            return {
                "success": False,
                "error": f"Token refresh service error: {str(e)}"
            }

# 全局实例
google_auth_service = GoogleAuthService()
