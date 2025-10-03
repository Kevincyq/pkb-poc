"""
快速分类服务 - 基于规则的快速预分类
用于提供即时的用户体验，后续由AI分类服务进行精确分类
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Category, Content, ContentCategory

logger = logging.getLogger(__name__)

class QuickClassificationService:
    """快速分类服务 - 基于规则和关键词的快速分类"""
    
    # 快速分类规则
    QUICK_RULES = {
        "职场商务": {
            "keywords": ["工作", "商务", "职场", "项目", "会议", "商业", "管理", "职业", "公司", "团队", "业务", "客户", "合同", "报告", "计划", "纪要", "议题", "决议", "讨论"],
            "file_patterns": ["report", "meeting", "business", "work", "project", "plan", "minutes", "agenda"],
            "extensions": [".docx", ".pptx", ".xlsx"]
        },
        "生活点滴": {
            "keywords": ["生活", "日常", "个人", "旅行", "美食", "感悟", "经验", "日记", "家庭", "朋友", "休闲", "娱乐", "购物", "健康", "风景", "自拍"],
            "file_patterns": ["diary", "life", "travel", "food", "personal", "daily", "selfie", "vacation"],
            "extensions": []  # 移除图片扩展名，让内容决定分类
        },
        "学习成长": {
            "keywords": ["学习", "笔记", "知识", "技能", "成长", "教育", "课程", "读书", "培训", "考试", "研究", "总结", "心得", "方法", "教程"],
            "file_patterns": ["study", "learn", "note", "course", "education", "training", "research", "tutorial"],
            "extensions": [".md", ".txt", ".pdf"]
        },
        "科技前沿": {
            "keywords": ["技术", "科技", "编程", "代码", "创新", "产品", "趋势", "开发", "算法", "数据", "AI", "人工智能", "机器学习", "区块链", "架构", "系统", "API"],
            "file_patterns": ["tech", "code", "dev", "api", "algorithm", "data", "ai", "ml", "architecture", "system"],
            "extensions": [".py", ".js", ".java", ".cpp", ".go", ".rs", ".json", ".yaml", ".yml"]
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def quick_classify(self, content_id: str, update_display: bool = True) -> Dict[str, Any]:
        """
        快速分类内容
        
        Args:
            content_id: 内容ID
            update_display: 是否更新前端显示状态
            
        Returns:
            快速分类结果
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
            
            # 检查是否已有系统分类（只检查系统分类，允许用户分类并存）
            existing_classification = self.db.query(ContentCategory).join(
                Category, ContentCategory.category_id == Category.id
            ).filter(
                ContentCategory.content_id == content_uuid,
                Category.is_system == True  # 只检查系统分类
            ).first()
            
            if existing_classification:
                return {
                    "success": True,
                    "message": "Content already has system classification",
                    "category_id": str(existing_classification.category_id),
                    "is_quick": False
                }
            
            # 执行快速分类
            classification_result = self._classify_by_rules(content)
            
            if not classification_result["success"]:
                return classification_result
            
            # 获取分类
            category = self.db.query(Category).filter(
                Category.name == classification_result["category"]
            ).first()
            
            if not category:
                return {"success": False, "error": f"Category not found: {classification_result['category']}"}
            
            # 创建快速分类记录
            content_category = ContentCategory(
                content_id=content_uuid,
                category_id=category.id,
                confidence=classification_result["confidence"],
                reasoning=f"快速分类: {classification_result.get('reasoning', '')}",
                role="primary_system",  # 系统主分类
                source="heuristic"      # 基于规则的快速分类
            )
            
            self.db.add(content_category)
            
            # 更新Content的分类状态
            if content.meta is None:
                content.meta = {}
            
            content.meta["classification_status"] = "quick_done"
            if update_display:
                content.meta["show_classification"] = True
            else:
                content.meta["show_classification"] = False
            
            # 标记meta字段为已修改，确保SQLAlchemy保存更改
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(content, 'meta')
            
            self.db.commit()
            
            logger.info(f"Quick classified content {content_id} as {category.name} (display: {update_display})")
            
            return {
                "success": True,
                "content_id": content_id,
                "category_id": str(category.id),
                "category_name": category.name,
                "confidence": classification_result["confidence"],
                "reasoning": classification_result.get("reasoning", ""),
                "is_quick": True,
                "display_updated": update_display
            }
            
        except Exception as e:
            logger.error(f"Error in quick classification for {content_id}: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def _classify_by_rules(self, content: Content) -> Dict[str, Any]:
        """基于规则进行快速分类"""
        try:
            # 合并标题和内容进行分析
            text_to_analyze = f"{content.title} {content.text[:500]}".lower()  # 只分析前500字符
            
            # 获取文件扩展名
            source_uri = content.source_uri or ""
            file_extension = ""
            if "." in source_uri:
                file_extension = "." + source_uri.split(".")[-1].lower()
            
            category_scores = {}
            
            # 对每个分类计算得分
            for category_name, rules in self.QUICK_RULES.items():
                score = 0
                reasons = []
                
                # 关键词匹配
                keyword_matches = 0
                for keyword in rules["keywords"]:
                    if keyword in text_to_analyze:
                        keyword_matches += 1
                        score += 2
                
                if keyword_matches > 0:
                    reasons.append(f"关键词匹配({keyword_matches}个)")
                
                # 文件名模式匹配
                pattern_matches = 0
                for pattern in rules["file_patterns"]:
                    if pattern in text_to_analyze:
                        pattern_matches += 1
                        score += 1
                
                if pattern_matches > 0:
                    reasons.append(f"文件名模式匹配({pattern_matches}个)")
                
                # 文件扩展名匹配（降低权重，避免过度依赖扩展名）
                if file_extension in rules["extensions"]:
                    score += 1  # 从3降低到1
                    reasons.append(f"文件类型匹配({file_extension})")
                
                category_scores[category_name] = {
                    "score": score,
                    "reasons": reasons
                }
            
            # 选择得分最高的分类
            if not category_scores or all(info["score"] == 0 for info in category_scores.values()):
                # 如果没有匹配，使用默认分类
                return {
                    "success": True,
                    "category": "学习成长",  # 默认分类
                    "confidence": 0.3,
                    "reasoning": "无明显特征，使用默认分类"
                }
            
            best_category = max(category_scores, key=lambda x: category_scores[x]["score"])
            best_info = category_scores[best_category]
            
            # 计算置信度
            max_score = best_info["score"]
            confidence = min(0.8, max(0.4, max_score / 10))  # 快速分类置信度较低
            
            reasoning = f"基于规则匹配: {', '.join(best_info['reasons'])}"
            
            return {
                "success": True,
                "category": best_category,
                "confidence": confidence,
                "reasoning": reasoning
            }
            
        except Exception as e:
            logger.error(f"Error in rule-based classification: {e}")
            return {
                "success": True,
                "category": "学习成长",  # 降级到默认分类
                "confidence": 0.2,
                "reasoning": f"分类出错，使用默认分类: {str(e)}"
            }
    
    def batch_quick_classify(self, content_ids: list) -> Dict[str, Any]:
        """批量快速分类"""
        results = {
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for content_id in content_ids:
            result = self.quick_classify(content_id)
            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "content_id": content_id,
                "result": result
            })
        
        return results
    
    def is_quick_classification(self, content_id: str) -> bool:
        """检查是否为快速分类"""
        try:
            # 转换content_id为UUID格式
            from uuid import UUID
            try:
                content_uuid = UUID(content_id) if isinstance(content_id, str) else content_id
            except ValueError:
                return False
            
            content_category = self.db.query(ContentCategory).filter(
                ContentCategory.content_id == content_uuid
            ).first()
            
            if content_category and content_category.reasoning:
                return content_category.reasoning.startswith("快速分类:")
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking quick classification status: {e}")
            return False
