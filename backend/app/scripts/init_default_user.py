"""
创建默认用户和初始化数据
"""
import os
import logging
from sqlalchemy.orm import Session
from app.models import User, StorageConfig
from app.db import SessionLocal

logger = logging.getLogger(__name__)

def create_default_user():
    """创建默认test用户"""
    db = SessionLocal()
    try:
        # 检查是否已存在test用户
        existing_user = db.query(User).filter(User.email == "test@pkb.local").first()
        
        if existing_user:
            logger.info("Default test user already exists")
            return existing_user
        
        # 创建test用户
        test_user = User(
            google_id=None,  # test用户没有Google ID
            email="test@pkb.local",
            display_name="Test User",
            avatar_url=None,
            is_active=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # 创建默认存储配置
        default_configs = [
            ("large_file_threshold", 5 * 1024 * 1024),  # 5MB
            ("default_cloud_provider", "google_drive"),
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
        
        logger.info(f"Created default test user: {test_user.email}")
        return test_user
        
    except Exception as e:
        logger.error(f"Failed to create default user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def migrate_existing_content():
    """迁移现有Content记录到test用户"""
    db = SessionLocal()
    try:
        # 获取test用户
        test_user = db.query(User).filter(User.email == "test@pkb.local").first()
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
