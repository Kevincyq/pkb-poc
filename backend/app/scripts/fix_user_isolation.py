#!/usr/bin/env python3
"""
用户隔离修复脚本 - 修复数据一致性问题
"""
import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal, engine
from app.models import User, Content, Collection, ContentCategory
from app.services.user_context_service import UserContextService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserIsolationFixer:
    """用户隔离修复工具"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.stats = {
            "orphan_contents": 0,
            "orphan_collections": 0,
            "fixed_contents": 0,
            "fixed_collections": 0,
            "errors": 0
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def create_default_user_if_needed(self) -> User:
        """创建默认用户（如果不存在）"""
        try:
            # 检查是否存在test用户
            test_user = self.db.query(User).filter(User.email == "test").first()
            if test_user:
                logger.info(f"✅ Test user exists: {test_user.id}")
                return test_user
            
            # 创建test用户
            from app.api.auth import hash_password
            test_user = User(
                email="test",
                display_name="Test User",
                password_hash=hash_password("test"),
                is_active=True
            )
            self.db.add(test_user)
            self.db.commit()
            self.db.refresh(test_user)
            
            logger.info(f"✅ Created test user: {test_user.id}")
            return test_user
            
        except Exception as e:
            logger.error(f"❌ Failed to create default user: {e}")
            self.db.rollback()
            raise
    
    def find_orphan_contents(self) -> list:
        """查找没有用户关联的内容"""
        try:
            orphan_contents = self.db.query(Content).filter(
                Content.user_id.is_(None)
            ).all()
            
            self.stats["orphan_contents"] = len(orphan_contents)
            logger.info(f"🔍 Found {len(orphan_contents)} orphan contents")
            
            return orphan_contents
            
        except Exception as e:
            logger.error(f"❌ Failed to find orphan contents: {e}")
            return []
    
    def find_orphan_collections(self) -> list:
        """查找没有用户关联的合集"""
        try:
            orphan_collections = self.db.query(Collection).filter(
                Collection.user_id.is_(None),
                Collection.auto_generated == False  # 只处理自建合集
            ).all()
            
            self.stats["orphan_collections"] = len(orphan_collections)
            logger.info(f"🔍 Found {len(orphan_collections)} orphan collections")
            
            return orphan_collections
            
        except Exception as e:
            logger.error(f"❌ Failed to find orphan collections: {e}")
            return []
    
    def fix_orphan_contents(self, default_user: User) -> bool:
        """修复孤儿内容"""
        try:
            orphan_contents = self.find_orphan_contents()
            
            if not orphan_contents:
                logger.info("✅ No orphan contents to fix")
                return True
            
            # 批量更新
            updated_count = self.db.query(Content).filter(
                Content.user_id.is_(None)
            ).update({
                Content.user_id: default_user.id
            }, synchronize_session=False)
            
            self.db.commit()
            self.stats["fixed_contents"] = updated_count
            
            logger.info(f"✅ Fixed {updated_count} orphan contents")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fix orphan contents: {e}")
            self.db.rollback()
            self.stats["errors"] += 1
            return False
    
    def fix_orphan_collections(self, default_user: User) -> bool:
        """修复孤儿合集"""
        try:
            orphan_collections = self.find_orphan_collections()
            
            if not orphan_collections:
                logger.info("✅ No orphan collections to fix")
                return True
            
            # 批量更新
            updated_count = self.db.query(Collection).filter(
                Collection.user_id.is_(None),
                Collection.auto_generated == False
            ).update({
                Collection.user_id: default_user.id
            }, synchronize_session=False)
            
            self.db.commit()
            self.stats["fixed_collections"] = updated_count
            
            logger.info(f"✅ Fixed {updated_count} orphan collections")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fix orphan collections: {e}")
            self.db.rollback()
            self.stats["errors"] += 1
            return False
    
    def validate_data_consistency(self) -> bool:
        """验证数据一致性"""
        try:
            # 检查是否还有孤儿数据
            orphan_contents = self.db.query(Content).filter(
                Content.user_id.is_(None)
            ).count()
            
            orphan_collections = self.db.query(Collection).filter(
                Collection.user_id.is_(None),
                Collection.auto_generated == False
            ).count()
            
            if orphan_contents > 0 or orphan_collections > 0:
                logger.warning(f"⚠️ Still have orphan data: {orphan_contents} contents, {orphan_collections} collections")
                return False
            
            logger.info("✅ Data consistency validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data consistency validation failed: {e}")
            return False
    
    def create_database_constraints(self) -> bool:
        """创建数据库约束（可选）"""
        try:
            # 注意：这会影响现有数据，谨慎使用
            logger.info("⚠️ Database constraint creation is optional and may affect existing data")
            
            # 可以在这里添加约束创建逻辑
            # 例如：ALTER TABLE contents ALTER COLUMN user_id SET NOT NULL;
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create database constraints: {e}")
            return False
    
    def run_fix(self) -> bool:
        """运行完整的修复流程"""
        try:
            logger.info("🚀 Starting user isolation fix...")
            
            # 1. 创建默认用户
            default_user = self.create_default_user_if_needed()
            
            # 2. 修复孤儿内容
            if not self.fix_orphan_contents(default_user):
                return False
            
            # 3. 修复孤儿合集
            if not self.fix_orphan_collections(default_user):
                return False
            
            # 4. 验证数据一致性
            if not self.validate_data_consistency():
                return False
            
            # 5. 打印统计信息
            self.print_stats()
            
            logger.info("🎉 User isolation fix completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ User isolation fix failed: {e}")
            return False
    
    def print_stats(self):
        """打印统计信息"""
        logger.info("📊 Fix Statistics:")
        logger.info(f"  - Orphan contents found: {self.stats['orphan_contents']}")
        logger.info(f"  - Orphan collections found: {self.stats['orphan_collections']}")
        logger.info(f"  - Contents fixed: {self.stats['fixed_contents']}")
        logger.info(f"  - Collections fixed: {self.stats['fixed_collections']}")
        logger.info(f"  - Errors: {self.stats['errors']}")

def main():
    """主函数"""
    try:
        with UserIsolationFixer() as fixer:
            success = fixer.run_fix()
            
            if success:
                print("✅ User isolation fix completed successfully!")
                return 0
            else:
                print("❌ User isolation fix failed!")
                return 1
                
    except Exception as e:
        logger.error(f"❌ Script execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
