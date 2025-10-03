"""
快速分类服务单元测试
测试规则匹配、关键词分析、文件类型识别等功能
"""
import pytest
from unittest.mock import patch
from app.services.quick_classification_service import QuickClassificationService
from app.models import Content, Category, ContentCategory


class TestQuickClassificationService:
    """快速分类服务测试类"""
    
    def test_init(self, test_db):
        """测试服务初始化"""
        service = QuickClassificationService(test_db)
        assert service.db == test_db
        assert len(service.QUICK_RULES) == 4
        
        # 验证规则结构
        for category_name, rules in service.QUICK_RULES.items():
            assert "keywords" in rules
            assert "file_patterns" in rules
            assert "extensions" in rules
            assert isinstance(rules["keywords"], list)
            assert isinstance(rules["file_patterns"], list)
            assert isinstance(rules["extensions"], list)
    
    def test_classify_by_rules_work_document(self, test_db, sample_categories):
        """测试工作文档的规则分类"""
        service = QuickClassificationService(test_db)
        
        # 创建工作相关的内容
        content = Content(
            title="项目会议纪要.docx",
            text="会议时间：2024年10月3日，参会人员：张三、李四，议题：项目进度讨论，决议：下周完成开发任务",
            source_uri="webui://项目会议纪要.docx"
        )
        
        result = service._classify_by_rules(content)
        
        assert result["category"] == "职场商务"
        assert result["confidence"] > 0.5
        assert "关键词匹配" in result["reasoning"]
        assert "文件类型匹配" in result["reasoning"]
    
    def test_classify_by_rules_travel_photo(self, test_db, sample_categories):
        """测试旅游照片的规则分类"""
        service = QuickClassificationService(test_db)
        
        content = Content(
            title="海边度假照片.jpg",
            text="美丽的海滩风景，蓝天白云，椰子树，度假村",
            source_uri="webui://海边度假照片.jpg"
        )
        
        result = service._classify_by_rules(content)
        
        assert result["category"] == "生活点滴"
        assert result["confidence"] > 0.5
        assert "关键词匹配" in result["reasoning"]
    
    def test_classify_by_rules_tech_document(self, test_db, sample_categories):
        """测试技术文档的规则分类"""
        service = QuickClassificationService(test_db)
        
        content = Content(
            title="API接口文档.py",
            text="# API接口设计\n\ndef get_user_info(user_id):\n    # 获取用户信息的API\n    pass",
            source_uri="webui://API接口文档.py"
        )
        
        result = service._classify_by_rules(content)
        
        assert result["category"] == "科技前沿"
        assert result["confidence"] > 0.5
        assert "关键词匹配" in result["reasoning"]
        assert "文件类型匹配" in result["reasoning"]
    
    def test_classify_by_rules_study_notes(self, test_db, sample_categories):
        """测试学习笔记的规则分类"""
        service = QuickClassificationService(test_db)
        
        content = Content(
            title="Python学习笔记.md",
            text="# Python基础语法学习\n\n## 变量和数据类型\n这是我的学习心得和总结",
            source_uri="webui://Python学习笔记.md"
        )
        
        result = service._classify_by_rules(content)
        
        assert result["category"] == "学习成长"
        assert result["confidence"] > 0.5
        assert "关键词匹配" in result["reasoning"]
        assert "文件类型匹配" in result["reasoning"]
    
    def test_classify_by_rules_no_match(self, test_db, sample_categories):
        """测试无匹配规则的内容"""
        service = QuickClassificationService(test_db)
        
        content = Content(
            title="未知文件.unknown",
            text="这是一些没有明确分类特征的内容",
            source_uri="webui://未知文件.unknown"
        )
        
        result = service._classify_by_rules(content)
        
        # 应该返回得分最高的分类，即使得分很低
        assert result["category"] in ["职场商务", "生活点滴", "学习成长", "科技前沿"]
        assert result["confidence"] >= 0.1  # 最低置信度
    
    def test_classify_by_rules_empty_content(self, test_db, sample_categories):
        """测试空内容的处理"""
        service = QuickClassificationService(test_db)
        
        content = Content(
            title="",
            text="",
            source_uri="webui://empty_file.txt"
        )
        
        result = service._classify_by_rules(content)
        
        # 即使是空内容，也应该返回一个分类
        assert result["category"] in ["职场商务", "生活点滴", "学习成长", "科技前沿"]
        assert result["confidence"] >= 0.1
    
    def test_keyword_matching_logic(self, test_db):
        """测试关键词匹配逻辑"""
        service = QuickClassificationService(test_db)
        
        # 测试多个关键词匹配
        text = "这是一个关于工作项目的会议纪要，讨论了商务合作和团队管理"
        
        work_rules = service.QUICK_RULES["职场商务"]
        matches = 0
        for keyword in work_rules["keywords"]:
            if keyword in text:
                matches += 1
        
        # 应该匹配多个关键词
        assert matches >= 3  # 工作、项目、会议、商务、团队
    
    def test_file_extension_matching(self, test_db):
        """测试文件扩展名匹配逻辑"""
        service = QuickClassificationService(test_db)
        
        # 测试不同文件类型的匹配
        test_cases = [
            ("document.docx", "职场商务"),
            ("script.py", "科技前沿"),
            ("notes.md", "学习成长"),
            ("photo.jpg", None)  # 图片不应该仅基于扩展名分类
        ]
        
        for filename, expected_category in test_cases:
            file_extension = "." + filename.split(".")[-1].lower()
            
            matched_categories = []
            for category_name, rules in service.QUICK_RULES.items():
                if file_extension in rules["extensions"]:
                    matched_categories.append(category_name)
            
            if expected_category:
                assert expected_category in matched_categories
            else:
                # 图片扩展名不应该在任何规则中（已移除）
                assert len(matched_categories) == 0
    
    @patch('app.services.quick_classification_service.QuickClassificationService._classify_by_rules')
    def test_quick_classify_success(self, mock_classify_rules, test_db, sample_categories, sample_content):
        """测试完整的快速分类流程"""
        # 模拟规则分类结果
        mock_classify_rules.return_value = {
            "category": "生活点滴",
            "confidence": 0.75,
            "reasoning": "关键词匹配(3个), 文件名模式匹配(1个)"
        }
        
        service = QuickClassificationService(test_db)
        content = sample_content[0]  # 海边度假照片
        
        result = service.quick_classify(str(content.id), update_display=False)
        
        assert result is True
        
        # 验证数据库中的分类记录
        classification = test_db.query(ContentCategory).filter(
            ContentCategory.content_id == content.id
        ).first()
        
        assert classification is not None
        assert classification.role == "primary_system"
        assert classification.source == "heuristic"
        assert classification.confidence == 0.75
        
        # 验证内容状态更新
        updated_content = test_db.query(Content).filter(Content.id == content.id).first()
        assert updated_content.meta["classification_status"] == "quick_done"
        assert updated_content.meta["show_classification"] is False  # update_display=False
    
    def test_quick_classify_with_display_update(self, test_db, sample_categories, sample_content):
        """测试带显示更新的快速分类"""
        service = QuickClassificationService(test_db)
        content = sample_content[1]  # 项目会议纪要
        
        result = service.quick_classify(str(content.id), update_display=True)
        
        assert result is True
        
        # 验证显示状态
        updated_content = test_db.query(Content).filter(Content.id == content.id).first()
        assert updated_content.meta["show_classification"] is True
    
    def test_quick_classify_content_not_found(self, test_db):
        """测试分类不存在的内容"""
        service = QuickClassificationService(test_db)
        result = service.quick_classify("non-existent-id")
        
        assert result is False
    
    def test_upsert_logic_existing_classification(self, test_db, sample_categories, sample_content):
        """测试已存在分类记录的UPSERT逻辑"""
        service = QuickClassificationService(test_db)
        content = sample_content[0]
        
        # 先创建一个分类记录
        category = sample_categories[1]  # 生活点滴
        existing_classification = ContentCategory(
            content_id=content.id,
            category_id=category.id,
            confidence=0.6,
            reasoning="初始分类",
            role="primary_system",
            source="heuristic"
        )
        test_db.add(existing_classification)
        test_db.commit()
        
        # 再次执行快速分类
        result = service.quick_classify(str(content.id))
        
        assert result is True
        
        # 验证记录被更新而不是重复创建
        classifications = test_db.query(ContentCategory).filter(
            ContentCategory.content_id == content.id,
            ContentCategory.category_id == category.id
        ).all()
        
        assert len(classifications) == 1  # 应该只有一条记录
        
        # 验证记录被更新
        updated_classification = classifications[0]
        assert updated_classification.confidence != 0.6  # 置信度应该被更新
        assert "快速分类" in updated_classification.reasoning
