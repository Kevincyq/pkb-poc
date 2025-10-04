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
        
        # 预定义的关键词映射（作为种子词汇，可扩展）
        keyword_mapping = {
            "会议纪要": ["会议", "纪要", "meeting", "minutes", "议题", "决议", "参会", "讨论", "会谈"],
            "旅游": ["旅游", "旅行", "度假", "vacation", "travel", "景点", "风景", "海边", "山水", "迪斯尼", "景区", "酒店", "套餐"],
            "项目文档": ["项目", "project", "计划", "方案", "需求", "设计"],
            "技术文档": ["技术", "开发", "代码", "API", "架构", "设计"],
            "工作总结": ["总结", "汇报", "报告", "review", "summary"],
            "学习笔记": ["学习", "笔记", "note", "教程", "课程", "培训"],
            "重要文档": ["重要", "关键", "核心", "urgent", "important"],
            "生活记录": ["生活", "日常", "个人", "家庭", "朋友", "休闲", "娱乐"],
            "美食": ["美食", "餐厅", "菜谱", "cooking", "food", "吃饭", "料理"],
            "健康": ["健康", "医疗", "运动", "fitness", "health", "锻炼", "体检", "养生"],
            "财务": ["财务", "理财", "投资", "finance", "money", "预算", "账单", "收支"],
            "家庭": ["家庭", "family", "孩子", "父母", "亲子", "育儿", "家务"],
            "娱乐": ["娱乐", "游戏", "电影", "音乐", "entertainment", "movie", "game", "music"],
            "购物": ["购物", "shopping", "商品", "价格", "优惠", "折扣", "商城"],
            "教育": ["教育", "education", "培训", "课程", "学校", "老师", "学生"]
        }
        
        # 直接匹配
        if name in keyword_mapping:
            keywords.extend(keyword_mapping[name])
        
        # 模糊匹配
        for key, values in keyword_mapping.items():
            if key in name or name in key:
                keywords.extend(values)
        
        # 智能关键词扩展：基于合集名称的语义分析
        keywords.extend(self._generate_semantic_keywords(name))
        
        # 添加原始名称作为关键词
        keywords.append(name)
        
        return list(set(keywords))  # 去重
    
    def _generate_semantic_keywords(self, name: str) -> List[str]:
        """基于合集名称生成语义相关的关键词"""
        semantic_keywords = []
        
        # 分词处理（简单的中文分词逻辑）
        import re
        # 提取中文词汇
        chinese_words = re.findall(r'[\u4e00-\u9fff]+', name)
        for word in chinese_words:
            if len(word) >= 2:  # 只保留长度>=2的词
                semantic_keywords.append(word)
        
        # 提取英文词汇
        english_words = re.findall(r'[a-zA-Z]+', name)
        for word in english_words:
            if len(word) >= 3:  # 只保留长度>=3的英文词
                semantic_keywords.append(word.lower())
        
        # 基于常见词汇模式扩展
        name_lower = name.lower()
        
        # 如果包含时间相关词汇
        if any(time_word in name_lower for time_word in ['日记', '记录', '日志', 'diary', 'log']):
            semantic_keywords.extend(['记录', '日志', '笔记'])
        
        # 如果包含工作相关词汇
        if any(work_word in name_lower for work_word in ['工作', 'work', '职场', '公司']):
            semantic_keywords.extend(['工作', '职场', '办公'])
        
        # 如果包含学习相关词汇
        if any(study_word in name_lower for study_word in ['学习', 'study', '课程', '教程']):
            semantic_keywords.extend(['学习', '教育', '知识'])
        
        return semantic_keywords
    
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
            
            # 检查内容是否有足够的信息进行匹配
            if not content.title and not content.text:
                logger.info(f"Content {content_id} has no title or text, skipping collection matching")
                return []
            
            # 获取所有用户创建的合集（包括没有匹配规则的）
            collections = self.db.query(Collection).filter(
                Collection.auto_generated == False  # 用户创建的合集
            ).all()
            
            matched_collections = []
            
            logger.info(f"Found {len(collections)} user collections to check for content {content_id}")
            
            for collection in collections:
                logger.info(f"🔍 Checking collection '{collection.name}' (id: {collection.id}) for content '{content.title}'")
                
                # 检查合集是否有关联的Category
                if not collection.category_id:
                    logger.warning(f"⚠️ Collection '{collection.name}' has no associated category_id, skipping")
                    continue
                
                if self._is_document_match_collection(content, collection):
                    # 创建文档-合集关联
                    self._create_content_collection_association(content_id, str(collection.id))
                    matched_collections.append(str(collection.id))
                    logger.info(f"✅ Document '{content.title}' matched to collection '{collection.name}'")
                else:
                    logger.info(f"❌ Document '{content.title}' did not match collection '{collection.name}'")
            
            # 🔥 修复：不要覆盖AI分类的状态，只标记合集匹配完成
            if content.meta is None:
                content.meta = {}
            
            # 添加合集匹配完成标记，但不覆盖classification_status
            content.meta["collection_matching_status"] = "completed"
            content.meta["collection_matching_count"] = len(matched_collections)
            # 保持show_classification状态不变，由AI分类决定
            
            # 标记meta字段为已修改，确保SQLAlchemy保存更改
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(content, 'meta')
            
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
            match_score += title_score * 0.3  # 标题权重30%
            
            # 内容匹配
            content_score = self._calculate_content_match_score(content.text, rules)
            match_score += content_score * 0.4  # 内容权重40%
            
            # 图片活动推理匹配（新增）
            activity_score = self._calculate_activity_match_score(content, rules)
            match_score += activity_score * 0.3  # 活动推理权重30%
            
            logger.info(f"🎯 Match score for '{content.title}' -> '{collection.name}': "
                       f"title={title_score:.2f}, content={content_score:.2f}, activity={activity_score:.2f}, "
                       f"total={match_score:.2f}, threshold={threshold:.2f}, "
                       f"match={match_score >= threshold}")
            
            # 特殊处理：如果是明显的匹配（如"迪士尼"图片匹配"旅游"合集），降低阈值
            if self._is_obvious_match(content, collection):
                logger.info(f"🎯 Obvious match detected, using lower threshold")
                return match_score >= 0.3  # 降低阈值
            
            return match_score >= threshold
            
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return False
    
    def _is_obvious_match(self, content: Content, collection: Collection) -> bool:
        """检测明显的匹配情况"""
        try:
            title = content.title.lower() if content.title else ""
            collection_name = collection.name.lower()
            
            # 明显匹配的模式
            obvious_patterns = {
                "旅游": ["迪士尼", "景区", "景点", "风景", "旅行", "度假", "酒店", "套餐"],
                "会议纪要": ["会议", "纪要", "meeting", "minutes"],
                "工作": ["工作", "项目", "报告", "总结"],
                "学习": ["学习", "笔记", "教程", "课程"]
            }
            
            for pattern_key, keywords in obvious_patterns.items():
                if pattern_key in collection_name:
                    for keyword in keywords:
                        if keyword in title:
                            logger.info(f"🎯 Obvious match: '{title}' contains '{keyword}' for collection '{collection_name}'")
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in _is_obvious_match: {e}")
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
    
    def _calculate_activity_match_score(self, content: Content, rules: Dict) -> float:
        """基于图片活动推理计算匹配分数"""
        try:
            # 如果不是图片或没有文本内容，返回0
            if content.modality != 'image' or not content.text:
                return 0.0
            
            # 解析图片分析结果
            activity_info = self._parse_image_analysis(content.text)
            if not activity_info:
                return 0.0
            
            # 获取合集关键词
            keywords = rules.get("keywords", [])
            if not keywords:
                return 0.0
            
            score = 0.0
            total_checks = 0
            
            # 检查活动推理匹配
            activity_inference = activity_info.get("activity_inference", "").lower()
            if activity_inference:
                total_checks += 1
                for keyword in keywords:
                    if keyword.lower() in activity_inference:
                        score += 0.8  # 活动推理匹配权重高
                        logger.debug(f"Activity inference match: '{keyword}' in '{activity_inference}'")
                        break
            
            # 检查关键元素匹配
            key_elements = activity_info.get("key_elements", "").lower()
            if key_elements:
                total_checks += 1
                keyword_matches = 0
                for keyword in keywords:
                    if keyword.lower() in key_elements:
                        keyword_matches += 1
                        logger.debug(f"Key element match: '{keyword}' in '{key_elements}'")
                
                if keyword_matches > 0:
                    score += (keyword_matches / len(keywords)) * 0.6  # 关键元素匹配
            
            # 检查场景描述匹配
            scene_description = activity_info.get("scene_description", "").lower()
            if scene_description:
                total_checks += 1
                for keyword in keywords:
                    if keyword.lower() in scene_description:
                        score += 0.4  # 场景描述匹配权重较低
                        logger.debug(f"Scene description match: '{keyword}' in '{scene_description}'")
                        break
            
            # 归一化分数
            final_score = min(score, 1.0) if total_checks > 0 else 0.0
            
            logger.debug(f"Activity match score: {final_score:.2f} for content '{content.title}'")
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating activity match score: {e}")
            return 0.0
    
    def _parse_image_analysis(self, text: str) -> Dict[str, str]:
        """解析图片分析结果，提取结构化信息"""
        try:
            if not text:
                return {}
            
            result = {}
            
            # 使用正则表达式提取各个部分
            import re
            
            # 提取活动推理
            activity_match = re.search(r'【活动推理】\s*(.*?)(?=【|$)', text, re.DOTALL)
            if activity_match:
                result["activity_inference"] = activity_match.group(1).strip()
            
            # 提取关键元素
            elements_match = re.search(r'【关键元素】\s*(.*?)(?=【|$)', text, re.DOTALL)
            if elements_match:
                result["key_elements"] = elements_match.group(1).strip()
            
            # 提取场景描述
            scene_match = re.search(r'【场景描述】\s*(.*?)(?=【|$)', text, re.DOTALL)
            if scene_match:
                result["scene_description"] = scene_match.group(1).strip()
            
            # 提取分类建议
            classification_match = re.search(r'【分类建议】\s*(.*?)(?=【|$)', text, re.DOTALL)
            if classification_match:
                result["classification_suggestion"] = classification_match.group(1).strip()
            
            logger.debug(f"Parsed image analysis: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing image analysis: {e}")
            return {}
