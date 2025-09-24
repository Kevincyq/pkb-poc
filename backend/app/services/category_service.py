"""
分类服务 - 使用 GPT-4o-mini 进行智能文档分类
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Category, Content, ContentCategory
import uuid

# 导入 OpenAI 客户端
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class CategoryService:
    """文档分类服务"""
    
    # 预置分类配置
    SYSTEM_CATEGORIES = [
        {
            "name": "职场商务",
            "description": "工作相关文档、商业计划、职业发展、会议记录、项目管理等",
            "color": "#2196F3",
            "keywords": ["工作", "商务", "职场", "项目", "会议", "商业", "管理", "职业"]
        },
        {
            "name": "生活点滴", 
            "description": "日常生活记录、个人感悟、生活经验、旅行日记、美食分享等",
            "color": "#4CAF50",
            "keywords": ["生活", "日常", "个人", "旅行", "美食", "感悟", "经验", "日记"]
        },
        {
            "name": "学习成长",
            "description": "学习笔记、技能提升、知识总结、读书心得、课程资料等", 
            "color": "#FF9800",
            "keywords": ["学习", "笔记", "知识", "技能", "成长", "教育", "课程", "读书"]
        },
        {
            "name": "科技前沿",
            "description": "技术文档、科技资讯、创新产品、编程代码、技术趋势等",
            "color": "#9C27B0", 
            "keywords": ["技术", "科技", "编程", "代码", "创新", "产品", "趋势", "开发"]
        }
    ]
    
    def __init__(self, db: Session):
        self.db = db
        
        # 检查 OpenAI 库可用性
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI library not available. Install with: pip install openai>=1.0.0")
            self.openai_enabled = False
            self.openai_client = None
            return
        
        # 配置 Turing API
        self.turing_api_key = os.getenv("TURING_API_KEY")
        self.turing_api_base = os.getenv("TURING_API_BASE")
        self.classification_model = os.getenv("CLASSIFICATION_MODEL", "turing/gpt-4o-mini")
        
        # 检查必要的环境变量
        if not self.turing_api_key or not self.turing_api_base:
            logger.error("Turing API configuration missing. Please set TURING_API_KEY and TURING_API_BASE")
            self.openai_enabled = False
            self.openai_client = None
            return
        
        try:
            # 创建 Turing API 客户端
            self.openai_client = OpenAI(
                api_key=self.turing_api_key,
                base_url=self.turing_api_base
            )
            self.openai_enabled = True
            logger.info(f"Classification service initialized with model: {self.classification_model}")
        except Exception as e:
            logger.error(f"Failed to initialize classification client: {e}")
            self.openai_enabled = False
    
    def initialize_system_categories(self) -> bool:
        """初始化系统预置分类"""
        try:
            for category_config in self.SYSTEM_CATEGORIES:
                # 检查分类是否已存在
                existing = self.db.query(Category).filter(
                    Category.name == category_config["name"]
                ).first()
                
                if not existing:
                    category = Category(
                        name=category_config["name"],
                        description=category_config["description"],
                        color=category_config["color"],
                        is_system=True
                    )
                    self.db.add(category)
                    logger.info(f"Created system category: {category_config['name']}")
                elif existing.is_system != True:
                    # 修复现有系统分类的is_system字段（强制修复所有非True的值）
                    old_value = existing.is_system
                    existing.is_system = True
                    logger.info(f"Fixed is_system field for category: {existing.name} (was: {old_value}, now: True)")
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error initializing system categories: {e}")
            self.db.rollback()
            return False
    
    def classify_content(self, content_id: str, force_reclassify: bool = False) -> Dict[str, Any]:
        """
        对内容进行智能分类
        
        Args:
            content_id: 内容ID
            force_reclassify: 是否强制重新分类
            
        Returns:
            分类结果
        """
        try:
            # 转换content_id为UUID格式
            from uuid import UUID
            try:
                content_uuid = UUID(content_id) if isinstance(content_id, str) else content_id
            except ValueError:
                return {"success": False, "error": "Invalid content_id format"}
            
            # 获取内容
            content = self.db.query(Content).filter(Content.id == content_uuid).first()
            if not content:
                return {"success": False, "error": "Content not found"}
            
            # 检查是否已分类
            existing_classification = self.db.query(ContentCategory).filter(
                ContentCategory.content_id == content_uuid
            ).first()
            
            if existing_classification and not force_reclassify:
                # 如果已经是AI分类（非快速分类），则跳过
                if existing_classification.reasoning and not existing_classification.reasoning.startswith("快速分类:"):
                    return {
                        "success": True, 
                        "message": "Content already classified with AI",
                        "category_id": str(existing_classification.category_id)
                    }
            
            # 使用AI进行分类
            classification_result = self._classify_with_ai(content.text, content.title)
            
            if not classification_result["success"]:
                return classification_result
            
            # 获取分类
            category = self.db.query(Category).filter(
                Category.name == classification_result["category"]
            ).first()
            
            if not category:
                return {"success": False, "error": f"Category not found: {classification_result['category']}"}
            
            # 删除现有分类（如果是重新分类或覆盖快速分类）
            existing_to_delete = self.db.query(ContentCategory).filter(
                ContentCategory.content_id == content_uuid
            ).first()
            
            if existing_to_delete:
                self.db.delete(existing_to_delete)
            
            # 创建新的分类关联
            content_category = ContentCategory(
                content_id=content_uuid,
                category_id=category.id,
                confidence=classification_result["confidence"],
                reasoning=classification_result.get("reasoning", "")
            )
            
            self.db.add(content_category)
            self.db.commit()
            
            logger.info(f"Successfully classified content {content_id} as {category.name}")
            
            return {
                "success": True,
                "content_id": content_id,
                "category_id": str(category.id),
                "category_name": category.name,
                "confidence": classification_result["confidence"],
                "reasoning": classification_result.get("reasoning", "")
            }
            
        except Exception as e:
            logger.error(f"Error classifying content {content_id}: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def _classify_with_ai(self, text: str, title: str) -> Dict[str, Any]:
        """使用AI进行文档分类"""
        if not self.openai_enabled:
            return {"success": False, "error": "AI classification not available"}
        
        try:
            # 构建分类提示词
            prompt = self._build_classification_prompt(text, title)
            
            # 调用GPT-4o-mini
            response = self.openai_client.chat.completions.create(
                model=self.classification_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的文档分类助手。请根据文档内容进行准确分类，并返回JSON格式的结果。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 解析JSON结果
            try:
                result = json.loads(result_text)
                
                # 验证结果格式
                if not all(key in result for key in ["category", "confidence"]):
                    raise ValueError("Missing required fields in classification result")
                
                # 验证分类名称
                valid_categories = [cat["name"] for cat in self.SYSTEM_CATEGORIES]
                if result["category"] not in valid_categories:
                    # 降级到最相似的分类
                    result["category"] = self._find_closest_category(result["category"])
                
                # 确保置信度在合理范围内
                result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
                
                return {
                    "success": True,
                    "category": result["category"],
                    "confidence": result["confidence"],
                    "reasoning": result.get("reasoning", "")
                }
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.error(f"Error parsing classification result: {e}, raw result: {result_text}")
                # 降级到基于关键词的分类
                return self._classify_by_keywords(text, title)
            
        except Exception as e:
            logger.error(f"Error in AI classification: {e}")
            # 降级到基于关键词的分类
            return self._classify_by_keywords(text, title)
    
    def _build_classification_prompt(self, text: str, title: str) -> str:
        """构建分类提示词"""
        # 截取文本前1000字符以避免token限制
        text_sample = text[:1000] + "..." if len(text) > 1000 else text
        
        categories_desc = "\n".join([
            f"{i+1}. {cat['name']} - {cat['description']}"
            for i, cat in enumerate(self.SYSTEM_CATEGORIES)
        ])
        
        return f"""请分析以下文档内容，将其归类到最合适的分类中。

可选分类：
{categories_desc}

文档标题：{title}

文档内容：
{text_sample}

请返回JSON格式的结果：
{{
    "category": "分类名称",
    "confidence": 0.85,
    "reasoning": "分类理由（简短说明为什么选择这个分类）"
}}

注意：
1. category必须是上述4个分类之一的准确名称
2. confidence是0.0到1.0之间的数值
3. reasoning简要说明分类依据"""
    
    def _classify_by_keywords(self, text: str, title: str) -> Dict[str, Any]:
        """基于关键词的降级分类方法"""
        try:
            content = (title + " " + text).lower()
            
            category_scores = {}
            
            for category_config in self.SYSTEM_CATEGORIES:
                score = 0
                for keyword in category_config["keywords"]:
                    score += content.count(keyword.lower())
                category_scores[category_config["name"]] = score
            
            # 选择得分最高的分类
            best_category = max(category_scores, key=category_scores.get)
            max_score = category_scores[best_category]
            
            # 计算置信度（基于关键词匹配数量）
            confidence = min(0.8, max(0.3, max_score / 10))
            
            return {
                "success": True,
                "category": best_category,
                "confidence": confidence,
                "reasoning": f"基于关键词匹配，匹配到{max_score}个相关词汇"
            }
            
        except Exception as e:
            logger.error(f"Error in keyword classification: {e}")
            # 最后的降级：返回默认分类
            return {
                "success": True,
                "category": "学习成长",  # 默认分类
                "confidence": 0.2,
                "reasoning": "无法确定分类，使用默认分类"
            }
    
    def _find_closest_category(self, category_name: str) -> str:
        """找到最相似的系统分类"""
        category_name_lower = category_name.lower()
        
        # 简单的相似度匹配
        for cat_config in self.SYSTEM_CATEGORIES:
            if category_name_lower in cat_config["name"].lower():
                return cat_config["name"]
            
            for keyword in cat_config["keywords"]:
                if keyword.lower() in category_name_lower:
                    return cat_config["name"]
        
        # 默认返回第一个分类
        return self.SYSTEM_CATEGORIES[0]["name"]
    
    def batch_classify(self, content_ids: List[str], force_reclassify: bool = False) -> Dict[str, Any]:
        """批量分类内容"""
        results = {
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for content_id in content_ids:
            result = self.classify_content(content_id, force_reclassify)
            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "content_id": content_id,
                "result": result
            })
        
        return results
    
    def get_categories(self, include_stats: bool = False) -> List[Dict[str, Any]]:
        """获取所有分类"""
        try:
            categories = self.db.query(Category).all()
            
            result = []
            for category in categories:
                category_dict = {
                    "id": str(category.id),
                    "name": category.name,
                    "description": category.description,
                    "color": category.color,
                    "is_system": category.is_system,
                    "created_at": category.created_at.isoformat() if category.created_at else None
                }
                
                if include_stats:
                    # 统计该分类下的文档数量
                    content_count = self.db.query(func.count(ContentCategory.content_id)).filter(
                        ContentCategory.category_id == category.id
                    ).scalar()
                    category_dict["content_count"] = content_count
                
                result.append(category_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_content_by_category(self, category_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """获取分类下的内容"""
        try:
            # 转换category_id为UUID格式
            from uuid import UUID
            try:
                category_uuid = UUID(category_id) if isinstance(category_id, str) else category_id
            except ValueError:
                return {"success": False, "error": "Invalid category_id format"}
            
            # 获取分类信息
            category = self.db.query(Category).filter(Category.id == category_uuid).first()
            if not category:
                return {"success": False, "error": "Category not found"}
            
            # 获取该分类下的内容
            query = self.db.query(Content).join(ContentCategory).filter(
                ContentCategory.category_id == category_uuid
            )
            
            total = query.count()
            contents = query.offset(offset).limit(limit).all()
            
            content_list = []
            for content in contents:
                # 获取分类信息
                content_category = self.db.query(ContentCategory).filter(
                    ContentCategory.content_id == content.id,
                    ContentCategory.category_id == category_uuid
                ).first()
                
                content_list.append({
                    "id": str(content.id),
                    "title": content.title,
                    "modality": content.modality,
                    "source_uri": content.source_uri,
                    "created_at": content.created_at.isoformat() if content.created_at else None,
                    "confidence": content_category.confidence if content_category else None,
                    "reasoning": content_category.reasoning if content_category else None
                })
            
            return {
                "success": True,
                "category": {
                    "id": str(category.id),
                    "name": category.name,
                    "description": category.description
                },
                "contents": content_list,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error(f"Error getting content by category {category_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def is_enabled(self) -> bool:
        """检查分类服务是否可用"""
        return self.openai_enabled
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """获取分类统计信息"""
        try:
            # 总内容数
            total_contents = self.db.query(func.count(Content.id)).scalar()
            
            # 已分类内容数
            classified_contents = self.db.query(func.count(ContentCategory.content_id.distinct())).scalar()
            
            # 各分类统计
            category_stats = self.db.query(
                Category.name,
                func.count(ContentCategory.content_id).label('count')
            ).join(ContentCategory).group_by(Category.name).all()
            
            return {
                "total_contents": total_contents,
                "classified_contents": classified_contents,
                "unclassified_contents": total_contents - classified_contents,
                "classification_rate": classified_contents / total_contents if total_contents > 0 else 0,
                "category_distribution": {
                    name: count for name, count in category_stats
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting classification stats: {e}")
            return {}
