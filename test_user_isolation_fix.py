#!/usr/bin/env python3
"""
用户隔离修复测试脚本
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加后端目录到 Python 路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db import SessionLocal
from app.models import User, Content, Collection
from app.services.user_context_service import UserContextFactory
from app.services.file_upload_service import FileUploadServiceFactory
from app.api.auth import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserIsolationTester:
    """用户隔离功能测试器"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def create_test_users(self) -> tuple:
        """创建测试用户"""
        try:
            # 创建或获取test用户
            test_user = self.db.query(User).filter(User.email == "test").first()
            if not test_user:
                test_user = User(
                    email="test",
                    display_name="Test User",
                    password_hash=hash_password("test"),
                    is_active=True
                )
                self.db.add(test_user)
            
            # 创建或获取Google测试用户
            google_user = self.db.query(User).filter(User.email == "test@gmail.com").first()
            if not google_user:
                google_user = User(
                    email="test@gmail.com",
                    display_name="Google Test User",
                    google_id="google_test_123",
                    is_active=True
                )
                self.db.add(google_user)
            
            self.db.commit()
            self.db.refresh(test_user)
            self.db.refresh(google_user)
            
            logger.info(f"✅ Test users created: {test_user.email}, {google_user.email}")
            return test_user, google_user
            
        except Exception as e:
            logger.error(f"❌ Failed to create test users: {e}")
            self.db.rollback()
            raise
    
    def test_user_context_service(self, user: User) -> bool:
        """测试用户上下文服务"""
        try:
            logger.info(f"🧪 Testing UserContextService for {user.email}")
            
            # 创建用户上下文
            context = UserContextFactory.create_from_user(self.db, user)
            
            # 测试用户验证
            validated_user = context.ensure_user_access()
            assert validated_user.id == user.id, "User validation failed"
            
            # 测试统计信息
            stats = context.get_user_stats()
            assert "total_contents" in stats, "Stats missing total_contents"
            assert "user_id" in stats, "Stats missing user_id"
            
            logger.info(f"✅ UserContextService test passed for {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ UserContextService test failed for {user.email}: {e}")
            return False
    
    def test_content_isolation(self, user1: User, user2: User) -> bool:
        """测试内容隔离"""
        try:
            logger.info(f"🧪 Testing content isolation between {user1.email} and {user2.email}")
            
            # 创建用户上下文
            context1 = UserContextFactory.create_from_user(self.db, user1)
            context2 = UserContextFactory.create_from_user(self.db, user2)
            
            # 用户1创建内容
            content1 = context1.create_user_content(
                title="User1 Test Content",
                text="This is user1's content",
                modality="text",
                source_uri="test://user1"
            )
            self.db.commit()
            self.db.refresh(content1)
            
            # 用户2创建内容
            content2 = context2.create_user_content(
                title="User2 Test Content", 
                text="This is user2's content",
                modality="text",
                source_uri="test://user2"
            )
            self.db.commit()
            self.db.refresh(content2)
            
            # 测试隔离：用户1不能访问用户2的内容
            user1_cannot_access_user2_content = context1.get_user_content(str(content2.id)) is None
            user2_cannot_access_user1_content = context2.get_user_content(str(content1.id)) is None
            
            # 测试访问：用户可以访问自己的内容
            user1_can_access_own_content = context1.get_user_content(str(content1.id)) is not None
            user2_can_access_own_content = context2.get_user_content(str(content2.id)) is not None
            
            # 验证结果
            assert user1_cannot_access_user2_content, "User1 should not access User2's content"
            assert user2_cannot_access_user1_content, "User2 should not access User1's content"
            assert user1_can_access_own_content, "User1 should access own content"
            assert user2_can_access_own_content, "User2 should access own content"
            
            logger.info("✅ Content isolation test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Content isolation test failed: {e}")
            return False
    
    def test_collection_isolation(self, user1: User, user2: User) -> bool:
        """测试合集隔离"""
        try:
            logger.info(f"🧪 Testing collection isolation between {user1.email} and {user2.email}")
            
            # 创建用户上下文
            context1 = UserContextFactory.create_from_user(self.db, user1)
            context2 = UserContextFactory.create_from_user(self.db, user2)
            
            # 用户1创建合集
            collection1 = context1.create_user_collection(
                name="User1 Test Collection",
                description="This is user1's collection",
                auto_generated=False
            )
            self.db.commit()
            self.db.refresh(collection1)
            
            # 用户2创建合集
            collection2 = context2.create_user_collection(
                name="User2 Test Collection",
                description="This is user2's collection", 
                auto_generated=False
            )
            self.db.commit()
            self.db.refresh(collection2)
            
            # 测试隔离：用户1不能访问用户2的合集
            user1_cannot_access_user2_collection = context1.get_user_collection(str(collection2.id)) is None
            user2_cannot_access_user1_collection = context2.get_user_collection(str(collection1.id)) is None
            
            # 测试访问：用户可以访问自己的合集
            user1_can_access_own_collection = context1.get_user_collection(str(collection1.id)) is not None
            user2_can_access_own_collection = context2.get_user_collection(str(collection2.id)) is not None
            
            # 验证结果
            assert user1_cannot_access_user2_collection, "User1 should not access User2's collection"
            assert user2_cannot_access_user1_collection, "User2 should not access User1's collection"
            assert user1_can_access_own_collection, "User1 should access own collection"
            assert user2_can_access_own_collection, "User2 should access own collection"
            
            logger.info("✅ Collection isolation test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Collection isolation test failed: {e}")
            return False
    
    def test_service_integration(self, user: User) -> bool:
        """测试服务集成"""
        try:
            logger.info(f"🧪 Testing service integration for {user.email}")
            
            # 创建用户上下文
            context = UserContextFactory.create_from_user(self.db, user)
            
            # 测试分类服务
            from app.services.category_service import CategoryService
            category_service = CategoryService(self.db, str(user.id))
            assert category_service.user_id == str(user.id), "CategoryService user_id mismatch"
            
            # 测试搜索服务
            from app.services.search_service import SearchService
            search_service = SearchService(self.db, str(user.id))
            assert search_service.user_id == str(user.id), "SearchService user_id mismatch"
            
            # 测试合集匹配服务
            from app.services.collection_matching_service import CollectionMatchingService
            matching_service = CollectionMatchingService(self.db, str(user.id))
            assert matching_service.user_id == str(user.id), "CollectionMatchingService user_id mismatch"
            
            logger.info("✅ Service integration test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Service integration test failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        try:
            logger.info("🚀 Starting user isolation tests...")
            
            # 创建测试用户
            test_user, google_user = self.create_test_users()
            
            # 运行测试
            tests = [
                ("UserContextService Test (Test User)", lambda: self.test_user_context_service(test_user)),
                ("UserContextService Test (Google User)", lambda: self.test_user_context_service(google_user)),
                ("Content Isolation Test", lambda: self.test_content_isolation(test_user, google_user)),
                ("Collection Isolation Test", lambda: self.test_collection_isolation(test_user, google_user)),
                ("Service Integration Test (Test User)", lambda: self.test_service_integration(test_user)),
                ("Service Integration Test (Google User)", lambda: self.test_service_integration(google_user)),
            ]
            
            passed = 0
            failed = 0
            
            for test_name, test_func in tests:
                logger.info(f"\n{'='*50}")
                logger.info(f"Running: {test_name}")
                logger.info(f"{'='*50}")
                
                try:
                    if test_func():
                        passed += 1
                        logger.info(f"✅ {test_name} PASSED")
                    else:
                        failed += 1
                        logger.error(f"❌ {test_name} FAILED")
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ {test_name} ERROR: {e}")
            
            # 打印结果
            logger.info(f"\n{'='*50}")
            logger.info(f"TEST RESULTS")
            logger.info(f"{'='*50}")
            logger.info(f"✅ Passed: {passed}")
            logger.info(f"❌ Failed: {failed}")
            logger.info(f"📊 Total: {passed + failed}")
            
            if failed == 0:
                logger.info("🎉 All tests passed!")
                return True
            else:
                logger.error(f"💥 {failed} tests failed!")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            return False

def main():
    """主函数"""
    try:
        with UserIsolationTester() as tester:
            success = tester.run_all_tests()
            
            if success:
                print("\n🎉 All user isolation tests passed!")
                return 0
            else:
                print("\n💥 Some tests failed!")
                return 1
                
    except Exception as e:
        logger.error(f"❌ Test script execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
