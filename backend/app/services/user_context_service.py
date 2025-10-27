"""
用户上下文服务 - 统一管理用户隔离逻辑
"""
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID

from app.models import User, Content, Collection, Category, ContentCategory
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

class UserContextService:
    """用户上下文服务 - 高聚合的用户隔离管理"""
    
    def __init__(self, db: Session, user_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self._user_cache: Optional[User] = None
    
    @property
    def user(self) -> Optional[User]:
        """获取当前用户对象（带缓存）"""
        if not self.user_id:
            return None
        
        if not self._user_cache:
            try:
                self._user_cache = self.db.query(User).filter(User.id == self.user_id).first()
            except Exception as e:
                logger.error(f"Failed to load user {self.user_id}: {e}")
                return None
        
        return self._user_cache
    
    def ensure_user_access(self) -> User:
        """确保用户已认证，否则抛出异常"""
        if not self.user_id:
            raise ValueError("用户未认证，无法访问此功能")
        
        user = self.user
        if not user or not user.is_active:
            raise ValueError("用户不存在或已被禁用")
        
        return user
    
    def filter_user_content(self, query):
        """为查询添加用户过滤条件"""
        if self.user_id:
            return query.filter(Content.user_id == self.user_id)
        return query
    
    def filter_user_collections(self, query):
        """为合集查询添加用户过滤条件"""
        if self.user_id:
            return query.filter(Collection.user_id == self.user_id)
        return query
    
    def create_user_content(self, **kwargs) -> Content:
        """创建用户内容，自动设置用户ID"""
        user = self.ensure_user_access()
        
        # 确保设置用户ID
        kwargs['user_id'] = user.id
        kwargs.setdefault('created_by', f"user.{user.email}")
        
        content = Content(**kwargs)
        self.db.add(content)
        return content
    
    def create_user_collection(self, **kwargs) -> Collection:
        """创建用户合集，自动设置用户ID"""
        user = self.ensure_user_access()
        
        # 确保设置用户ID
        kwargs['user_id'] = user.id
        
        collection = Collection(**kwargs)
        self.db.add(collection)
        return collection
    
    def get_user_content(self, content_id: str) -> Optional[Content]:
        """获取用户的内容，确保用户隔离"""
        try:
            content_uuid = UUID(content_id)
        except ValueError:
            logger.error(f"Invalid content ID format: {content_id}")
            return None
        
        query = self.db.query(Content).filter(Content.id == content_uuid)
        query = self.filter_user_content(query)
        return query.first()
    
    def get_user_collection(self, collection_id: str) -> Optional[Collection]:
        """获取用户的合集，确保用户隔离"""
        try:
            collection_uuid = UUID(collection_id)
        except ValueError:
            logger.error(f"Invalid collection ID format: {collection_id}")
            return None
        
        query = self.db.query(Collection).filter(Collection.id == collection_uuid)
        query = self.filter_user_collections(query)
        return query.first()
    
    def get_user_stats(self) -> Dict[str, Any]:
        """获取用户统计信息"""
        if not self.user_id:
            return {"total_contents": 0, "total_collections": 0}
        
        try:
            total_contents = self.filter_user_content(
                self.db.query(Content)
            ).count()
            
            total_collections = self.filter_user_collections(
                self.db.query(Collection).filter(Collection.auto_generated == False)
            ).count()
            
            return {
                "total_contents": total_contents,
                "total_collections": total_collections,
                "user_id": self.user_id
            }
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {"total_contents": 0, "total_collections": 0}
    
    def validate_content_access(self, content_id: str) -> bool:
        """验证用户是否有权限访问指定内容"""
        content = self.get_user_content(content_id)
        return content is not None
    
    def validate_collection_access(self, collection_id: str) -> bool:
        """验证用户是否有权限访问指定合集"""
        collection = self.get_user_collection(collection_id)
        return collection is not None

class UserContextFactory:
    """用户上下文工厂 - 低耦合的服务创建"""
    
    @staticmethod
    def create_from_user(db: Session, user: User) -> UserContextService:
        """从用户对象创建上下文服务"""
        return UserContextService(db, str(user.id))
    
    @staticmethod
    def create_from_user_id(db: Session, user_id: str) -> UserContextService:
        """从用户ID创建上下文服务"""
        return UserContextService(db, user_id)
    
    @staticmethod
    def create_anonymous(db: Session) -> UserContextService:
        """创建匿名上下文服务（用于系统任务）"""
        return UserContextService(db, None)

# 便捷的装饰器和工具函数
def with_user_context(func):
    """装饰器：自动注入用户上下文"""
    def wrapper(*args, **kwargs):
        # 如果第一个参数是UserContextService，直接使用
        if args and isinstance(args[0], UserContextService):
            return func(*args, **kwargs)
        
        # 否则尝试从kwargs中获取db和user_id
        db = kwargs.get('db')
        user_id = kwargs.get('user_id')
        
        if db and user_id:
            context = UserContextService(db, user_id)
            kwargs['context'] = context
        
        return func(*args, **kwargs)
    
    return wrapper
