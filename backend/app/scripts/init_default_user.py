"""
创建默认用户和初始化数据
"""
import os
import logging
import hashlib
from sqlalchemy.orm import Session
from app.models import User, StorageConfig, CloudAuth
from app.db import SessionLocal

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_default_user():
    """创建默认用户（只创建test用户）"""
    db = SessionLocal()
    try:
        # 只创建test用户，Google用户通过注册API创建
        test_user = create_test_user(db)
        
        logger.info("✅ 默认用户创建完成")
        return test_user
        
    except Exception as e:
        logger.error(f"Failed to create default users: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_test_user(db: Session):
    """创建test用户"""
    # 检查是否已存在test用户
    existing_user = db.query(User).filter(User.email == "test").first()
    
    if existing_user:
        logger.info("Test user already exists")
        return existing_user
    
    # 创建test用户
    test_user = User(
        google_id=None,  # test用户没有Google ID
        email="test",  # 直接使用test作为用户名
        password_hash=hash_password("test"),  # 设置密码哈希
        display_name="Test User",
        avatar_url=None,
        is_active=True
    )
    
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
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
    
    # 创建默认存储配置（test用户使用Nextcloud）
    default_configs = [
        ("large_file_threshold", 5 * 1024 * 1024),  # 5MB
        ("default_cloud_provider", "nextcloud"),  # test用户使用Nextcloud
        ("enable_google_drive", False),  # test用户不能使用Google Drive
        ("enable_nextcloud", True),  # test用户可以使用Nextcloud
        ("thumbnail_size", {"width": 300, "height": 200}),
        ("thumbnail_quality", 85)
    ]
    
    for key, value in default_configs:
        config = StorageConfig(
            user_id=test_user.id,
            config_key=key,
            config_value=value
        )
        db.add(config)
    
    db.commit()
    
    logger.info(f"✅ Created test user: {test_user.email}")
    return test_user

def migrate_existing_content():
    """迁移现有Content记录到test用户"""
    db = SessionLocal()
    try:
        # 获取test用户
        test_user = db.query(User).filter(User.email == "test").first()
        if not test_user:
            logger.warning("Test user not found, skipping content migration")
            return
        
        # 更新现有Content记录
        from app.models import Content
        updated_count = db.query(Content).filter(Content.user_id == None).update({
            'user_id': test_user.id,
            'storage_provider': 'local'  # 现有文件都是本地存储
        })
        
        db.commit()
        logger.info(f"Migrated {updated_count} existing content records to test user")
        
    except Exception as e:
        logger.error(f"Failed to migrate existing content: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_default_user()
    migrate_existing_content()
