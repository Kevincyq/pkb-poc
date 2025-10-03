"""
智能合集匹配服务
用于自动将文档匹配到用户创建的合集中
"""

import logging
import re
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Collection, Content, ContentCategory, Category

logger = logging.getLogger(__name__)

class CollectionMatchingService:
    """智能合集匹配服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_auto_match_rules(self, collection_name: str, description: str = None) -> Dict[str, Any]:
        """
        根据合集名称和描述生成自动匹配规则
        
        Args:
            collection_name: 合集名称
            description: 合集描述
            
        Returns:
            匹配规则字典
        """
        try:
            # 基于合集名称生成关键词
            keywords = self._extract_keywords_from_name(collection_name)
            
            # 如果有描述，从描述中提取更多关键词
            if description:
                desc_keywords = self._extract_keywords_from_description(description)
                keywords.extend(desc_keywords)
            
            # 生成标题匹配模式
            title_patterns = self._generate_title_patterns(collection_name, keywords)
            
            # 生成内容匹配模式
            content_patterns = self._generate_content_patterns(keywords)
            
            rules = {
                "keywords": list(set(keywords)),  # 去重
                "title_patterns": title_patterns,
                "content_patterns": content_patterns,
                "auto_match": True,
                "match_threshold": 0.6  # 匹配阈值
            }
            
            logger.info(f"Generated auto-match rules for collection '{collection_name}': {rules}")
            return rules
            
        except Exception as e:
            logger.error(f"Error generating auto-match rules: {e}")
            return {"auto_match": False}
    
    def _extract_keywords_from_name(self, name: str) -> List[str]:
        """从合集名称中提取关键词"""
        keywords = []
        
        # 预定义的关键词映射
        keyword_mapping = {
            "会议纪要": ["会议", "纪要", "meeting", "minutes", "议题", "决议", "参会"],
            "项目文档": ["项目", "project", "计划", "方案", "需求", "设计"],
            "技术文档": ["技术", "开发", "代码", "API", "架构", "设计"],
            "工作总结": ["总结", "汇报", "报告", "review", "summary"],
            "学习笔记": ["学习", "笔记", "note", "教程", "课程", "培训"],
            "重要文档": ["重要", "关键", "核心", "urgent", "important"]
        }
        
        # 直接匹配
        if name in keyword_mapping:
            keywords.extend(keyword_mapping[name])
        
        # 模糊匹配
        for key, values in keyword_mapping.items():
            if key in name or name in key:
                keywords.extend(values)
        
        # 添加原始名称作为关键词
        keywords.append(name)
        
        return keywords
    
    def _extract_keywords_from_description(self, description: str) -> List[str]:
        """从描述中提取关键词"""
        keywords = []
        
        # 简单的关键词提取（可以后续用NLP优化）
        common_keywords = [
            "会议", "项目", "工作", "技术", "学习", "重要", "文档", "资料",
            "meeting", "project", "work", "tech", "study", "important", "document"
        ]
        
        desc_lower = description.lower()
        for keyword in common_keywords:
            if keyword in desc_lower:
                keywords.append(keyword)
        
        return keywords
    
    def _generate_title_patterns(self, collection_name: str, keywords: List[str]) -> List[str]:
        """生成标题匹配模式"""
        patterns = []
        
        # 基于合集名称的模式
        patterns.append(f".*{re.escape(collection_name)}.*")
        
        # 基于关键词的模式
        for keyword in keywords[:5]:  # 只取前5个关键词避免过多模式
            patterns.append(f".*{re.escape(keyword)}.*")
        
        return patterns
    
    def _generate_content_patterns(self, keywords: List[str]) -> List[str]:
        """生成内容匹配模式"""
        patterns = []
        
        # 会议纪要特定模式
        if any(k in keywords for k in ["会议", "meeting", "纪要", "minutes"]):
            patterns.extend([
                "会议时间", "参会人员", "会议议题", "会议内容", "决议事项",
                "meeting time", "attendees", "agenda", "action items"
            ])
        
        # 项目文档特定模式
        if any(k in keywords for k in ["项目", "project"]):
            patterns.extend([
                "项目背景", "项目目标", "里程碑", "deliverable", "timeline"
            ])
        
        return patterns
    
    def match_document_to_collections(self, content_id: str) -> List[str]:
        """
        将文档匹配到合适的用户合集
        
        Args:
            content_id: 文档ID
            
        Returns:
            匹配的合集ID列表
        """
        try:
            from uuid import UUID
            content_uuid = UUID(content_id) if isinstance(content_id, str) else content_id
            
            # 获取文档内容
            content = self.db.query(Content).filter(Content.id == content_uuid).first()
            if not content:
                logger.warning(f"Content not found: {content_id}")
                return []
            
            # 获取所有用户创建的合集（包括没有匹配规则的）
            collections = self.db.query(Collection).filter(
                Collection.auto_generated == False  # 用户创建的合集
            ).all()
            
            matched_collections = []
            
            logger.info(f"Found {len(collections)} user collections to check for content {content_id}")
            
            for collection in collections:
                logger.debug(f"Checking collection {collection.name} (id: {collection.id})")
                if self._is_document_match_collection(content, collection):
                    # 创建文档-合集关联
                    self._create_content_collection_association(content_id, str(collection.id))
                    matched_collections.append(str(collection.id))
                    logger.info(f"✅ Document {content_id} matched to collection {collection.name}")
                else:
                    logger.debug(f"❌ Document {content_id} did not match collection {collection.name}")
            
            # 更新Content的分类状态（合集匹配完成）
            if content.meta is None:
                content.meta = {}
            
            content.meta["classification_status"] = "completed"
            # 保持show_classification状态不变，由AI分类决定
            
            # 提交所有关联创建和状态更新
            self.db.commit()
            
            if matched_collections:
                logger.info(f"Committed {len(matched_collections)} collection associations and updated status")
            else:
                logger.info(f"No collections matched, but updated status to completed")
            
            return matched_collections
            
        except Exception as e:
            logger.error(f"Error matching document to collections: {e}")
            self.db.rollback()
            return []
    
    def _is_document_match_collection(self, content: Content, collection: Collection) -> bool:
        """判断文档是否匹配合集"""
        try:
            rules = collection.query_rules
            
            # 如果没有匹配规则，动态生成（但不立即保存，避免在匹配过程中提交事务）
            if not rules:
                rules = self.generate_auto_match_rules(collection.name, collection.description)
                if rules and rules.get("auto_match", False):
                    # 临时设置规则，但不提交到数据库（避免事务冲突）
                    collection.query_rules = rules
                    logger.info(f"Generated temporary rules for collection {collection.name}")
            
            if not rules or not rules.get("auto_match", False):
                return False
            
            match_score = 0
            threshold = rules.get("match_threshold", 0.3)  # 降低阈值以便调试
            
            # 标题匹配
            title_score = self._calculate_title_match_score(content.title, rules)
            match_score += title_score * 0.4  # 标题权重40%
            
            # 内容匹配
            content_score = self._calculate_content_match_score(content.text, rules)
            match_score += content_score * 0.6  # 内容权重60%
            
            logger.info(f"Match score for '{content.title}' -> '{collection.name}': "
                       f"title={title_score:.2f}, content={content_score:.2f}, "
                       f"total={match_score:.2f}, threshold={threshold:.2f}, "
                       f"match={match_score >= threshold}")
            
            return match_score >= threshold
            
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return False
    
    def _calculate_title_match_score(self, title: str, rules: Dict) -> float:
        """计算标题匹配分数"""
        if not title:
            return 0.0
        
        title_lower = title.lower()
        score = 0.0
        
        # 关键词匹配（优化：使用匹配数量而不是比例，避免关键词过多稀释分数）
        keywords = rules.get("keywords", [])
        if keywords:
            matched_keywords = sum(1 for keyword in keywords if keyword.lower() in title_lower)
            # 使用匹配关键词数量，每个匹配的关键词贡献0.2分，最大0.7分
            score += min(0.7, matched_keywords * 0.2)
        
        # 模式匹配
        patterns = rules.get("title_patterns", [])
        if patterns:
            matched_patterns = sum(1 for pattern in patterns if re.search(pattern, title, re.IGNORECASE))
            score += (matched_patterns / len(patterns)) * 0.3
        
        return min(1.0, score)
    
    def _calculate_content_match_score(self, text: str, rules: Dict) -> float:
        """计算内容匹配分数"""
        if not text:
            return 0.0
        
        # 只分析前1000字符以提高性能
        text_sample = text[:1000].lower()
        score = 0.0
        
        # 关键词匹配（优化：使用匹配数量）
        keywords = rules.get("keywords", [])
        if keywords:
            matched_keywords = sum(1 for keyword in keywords if keyword.lower() in text_sample)
            # 每个匹配的关键词贡献0.15分，最大0.6分
            score += min(0.6, matched_keywords * 0.15)
        
        # 内容模式匹配
        content_patterns = rules.get("content_patterns", [])
        if content_patterns:
            matched_patterns = sum(1 for pattern in content_patterns if pattern.lower() in text_sample)
            score += (matched_patterns / len(content_patterns)) * 0.4
        
        return min(1.0, score)
    
    def match_existing_documents_to_collection(self, collection_id: str) -> int:
        """
        将现有文档匹配到新创建的合集
        
        Args:
            collection_id: 合集ID
            
        Returns:
            匹配的文档数量
        """
        try:
            from uuid import UUID
            collection_uuid = UUID(collection_id) if isinstance(collection_id, str) else collection_id
            
            collection = self.db.query(Collection).filter(Collection.id == collection_uuid).first()
            if not collection or not collection.query_rules:
                return 0
            
            # 获取所有文档
            contents = self.db.query(Content).all()
            matched_count = 0
            
            for content in contents:
                if self._is_document_match_collection(content, collection):
                    # 创建文档-合集关联
                    self._create_content_collection_association(str(content.id), collection_id)
                    matched_count += 1
            
            logger.info(f"Matched {matched_count} existing documents to collection {collection.name}")
            return matched_count
            
        except Exception as e:
            logger.error(f"Error matching existing documents to collection: {e}")
            return 0
    
    def _create_content_collection_association(self, content_id: str, collection_id: str):
        """创建文档-合集关联"""
        try:
            from uuid import UUID
            
            content_uuid = UUID(content_id)
            collection_uuid = UUID(collection_id)
            
            # 获取合集对应的分类ID
            collection = self.db.query(Collection).filter(Collection.id == collection_uuid).first()
            if not collection or not collection.category_id:
                logger.warning(f"Collection {collection_id} has no associated category")
                return
            
            # 检查是否已存在相同reasoning的关联（避免重复，但允许不同来源的分类）
            existing = self.db.query(ContentCategory).filter(
                ContentCategory.content_id == content_uuid,
                ContentCategory.category_id == collection.category_id,
                ContentCategory.reasoning.like(f"%自动匹配到合集: {collection.name}%")
            ).first()
            
            if existing:
                logger.debug(f"Collection association already exists: content {content_id} -> collection {collection.name}")
                return
            
            # 创建新的关联
            content_category = ContentCategory(
                content_id=content_uuid,
                category_id=collection.category_id,
                confidence=0.8,  # 自动匹配的置信度
                reasoning=f"自动匹配到合集: {collection.name}",
                role="user_rule",  # 用户规则分类
                source="rule"      # 基于规则的分类
            )
            
            self.db.add(content_category)
            # 不在这里提交，让调用者决定何时提交事务
            self.db.flush()  # 确保对象被持久化到会话中
            
            logger.info(f"Created association: content {content_id} -> collection {collection_id}")
            
        except Exception as e:
            logger.error(f"Error creating content-collection association: {e}")
            self.db.rollback()
