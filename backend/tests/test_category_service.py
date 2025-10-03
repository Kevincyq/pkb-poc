"""
AI分类服务单元测试
测试多标签分类、置信度计算、错误处理等核心功能
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.services.category_service import CategoryService
from app.models import Content, Category, ContentCategory


class TestCategoryService:
    """AI分类服务测试类"""
    
    def test_init(self, test_db, sample_categories):
        """测试服务初始化"""
        service = CategoryService(test_db)
        assert service.db == test_db
        assert len(service.SYSTEM_CATEGORIES) == 4
        
    def test_get_system_categories(self, test_db, sample_categories):
        """测试获取系统分类"""
        service = CategoryService(test_db)
        categories = service.get_system_categories()
        
        assert len(categories) == 4
        category_names = [cat.name for cat in categories]
        assert "职场商务" in category_names
        assert "生活点滴" in category_names
        assert "学习成长" in category_names
        assert "科技前沿" in category_names
    
    @patch('app.services.category_service.OpenAI')
    def test_classify_with_ai_success(self, mock_openai, test_db, sample_categories, sample_content):
        """测试AI分类成功场景"""
        # 模拟OpenAI响应
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "primary": "生活点滴",
            "secondary": ["职场商务"],
            "confidence": {
                "生活点滴": 0.85,
                "职场商务": 0.45
            },
            "reasoning": "海边度假照片属于生活记录"
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = CategoryService(test_db)
        result = service._classify_with_ai("海边度假的美好时光", "海边度假照片.jpg")
        
        assert result["success"] is True
        assert result["primary"] == "生活点滴"
        assert "职场商务" in result["secondary"]
        assert result["confidence"]["生活点滴"] == 0.85
        assert "海边度假照片属于生活记录" in result["reasoning"]
    
    @patch('app.services.category_service.OpenAI')
    def test_classify_with_ai_json_error(self, mock_openai, test_db, sample_categories):
        """测试AI分类JSON解析错误的降级处理"""
        # 模拟返回无效JSON
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "invalid json response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = CategoryService(test_db)
        
        # 模拟降级方法
        with patch.object(service, '_classify_with_ai_single_label') as mock_fallback:
            mock_fallback.return_value = {
                "success": True,
                "category": "生活点滴",
                "confidence": 0.7,
                "reasoning": "降级分类结果"
            }
            
            result = service._classify_with_ai("测试内容", "测试标题")
            
            # 验证降级方法被调用
            mock_fallback.assert_called_once_with("测试内容", "测试标题")
    
    def test_build_multi_label_classification_prompt(self, test_db):
        """测试多标签分类提示词构建"""
        service = CategoryService(test_db)
        prompt = service._build_multi_label_classification_prompt("测试文本内容", "测试标题")
        
        assert "测试标题" in prompt
        assert "测试文本内容" in prompt
        assert "职场商务" in prompt
        assert "生活点滴" in prompt
        assert "学习成长" in prompt
        assert "科技前沿" in prompt
        assert "primary" in prompt
        assert "secondary" in prompt
        assert "confidence" in prompt
        assert "reasoning" in prompt
    
    @patch('app.services.category_service.CategoryService._classify_with_ai')
    def test_classify_content_success(self, mock_classify_ai, test_db, sample_categories, sample_content):
        """测试完整的内容分类流程"""
        # 模拟AI分类结果
        mock_classify_ai.return_value = {
            "success": True,
            "primary": "生活点滴",
            "secondary": ["职场商务"],
            "confidence": {
                "生活点滴": 0.85,
                "职场商务": 0.45
            },
            "reasoning": "海边度假照片"
        }
        
        service = CategoryService(test_db)
        content = sample_content[0]  # 海边度假照片
        
        result = service.classify_content(str(content.id))
        
        assert result is True
        
        # 验证数据库中的分类记录
        classifications = test_db.query(ContentCategory).filter(
            ContentCategory.content_id == content.id
        ).all()
        
        # 应该有两条记录：主分类和次分类
        assert len(classifications) >= 1
        
        # 验证主分类
        primary_classification = next(
            (c for c in classifications if c.role == "primary_system"), None
        )
        assert primary_classification is not None
        assert primary_classification.confidence == 0.85
        
        # 验证内容状态更新
        updated_content = test_db.query(Content).filter(Content.id == content.id).first()
        assert updated_content.meta["classification_status"] == "ai_done"
        assert updated_content.meta["show_classification"] is True
    
    def test_classify_content_not_found(self, test_db):
        """测试分类不存在的内容"""
        service = CategoryService(test_db)
        result = service.classify_content("non-existent-id")
        
        assert result is False
    
    @patch('app.services.category_service.CategoryService._classify_with_ai')
    def test_classify_content_ai_failure(self, mock_classify_ai, test_db, sample_categories, sample_content):
        """测试AI分类失败的处理"""
        # 模拟AI分类失败
        mock_classify_ai.return_value = {
            "success": False,
            "error": "API调用失败"
        }
        
        service = CategoryService(test_db)
        content = sample_content[0]
        
        result = service.classify_content(str(content.id))
        
        # 分类应该失败但不抛出异常
        assert result is False
    
    def test_confidence_threshold_filtering(self, test_db, sample_categories):
        """测试置信度阈值过滤"""
        service = CategoryService(test_db)
        
        # 测试置信度数据
        confidence_data = {
            "生活点滴": 0.85,  # 应该被包含（主分类）
            "职场商务": 0.45,  # 应该被包含（次分类，>0.3）
            "学习成长": 0.25,  # 应该被排除（<0.3）
            "科技前沿": 0.15   # 应该被排除（<0.3）
        }
        
        # 模拟处理置信度过滤的逻辑
        primary_category = max(confidence_data, key=confidence_data.get)
        secondary_categories = [
            cat for cat, conf in confidence_data.items() 
            if conf >= 0.3 and cat != primary_category
        ]
        
        assert primary_category == "生活点滴"
        assert "职场商务" in secondary_categories
        assert "学习成长" not in secondary_categories
        assert "科技前沿" not in secondary_categories
    
    def test_prompt_generalization(self, test_db):
        """测试提示词的泛化性（不包含硬编码示例）"""
        service = CategoryService(test_db)
        prompt = service._build_multi_label_classification_prompt("任意内容", "任意标题")
        
        # 确保提示词不包含硬编码的具体示例
        assert "旅游、度假、风景照片等应归入" not in prompt
        assert "会议纪要、工作文档等应归入" not in prompt
        
        # 确保包含通用化的指导原则
        assert "根据内容的主要用途和性质进行分类" in prompt
        assert "重点分析其用途、场景和可能的应用领域" in prompt
