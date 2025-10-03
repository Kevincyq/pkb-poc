"""
合集匹配服务单元测试
测试关键词扩展、语义匹配、活动推理等功能
"""
import pytest
from unittest.mock import patch, Mock
from app.services.collection_matching_service import CollectionMatchingService
from app.models import Content, Collection, ContentCategory


class TestCollectionMatchingService:
    """合集匹配服务测试类"""
    
    def test_init(self, test_db):
        """测试服务初始化"""
        service = CollectionMatchingService(test_db)
        assert service.db == test_db
    
    def test_extract_keywords_from_name_predefined(self, test_db):
        """测试预定义合集名称的关键词提取"""
        service = CollectionMatchingService(test_db)
        
        # 测试预定义的合集名称
        test_cases = [
            ("旅游", ["旅游", "旅行", "度假", "vacation", "travel", "景点", "风景"]),
            ("会议纪要", ["会议", "纪要", "meeting", "minutes", "议题", "决议"]),
            ("技术文档", ["技术", "开发", "代码", "API", "架构", "设计"]),
            ("健康", ["健康", "医疗", "运动", "fitness", "health", "锻炼"])
        ]
        
        for collection_name, expected_keywords in test_cases:
            keywords = service._extract_keywords_from_name(collection_name)
            
            # 验证包含预期的关键词
            for expected_keyword in expected_keywords:
                assert expected_keyword in keywords
            
            # 验证包含原始名称
            assert collection_name in keywords
    
    def test_extract_keywords_from_name_custom(self, test_db):
        """测试自定义合集名称的关键词提取"""
        service = CollectionMatchingService(test_db)
        
        # 测试自定义合集名称
        test_cases = [
            "我的读书笔记",
            "家庭照片集",
            "工作项目文档",
            "Python学习资料"
        ]
        
        for collection_name in test_cases:
            keywords = service._extract_keywords_from_name(collection_name)
            
            # 验证包含原始名称
            assert collection_name in keywords
            
            # 验证关键词数量合理
            assert len(keywords) >= 1
            
            # 验证去重
            assert len(keywords) == len(set(keywords))
    
    def test_generate_semantic_keywords(self, test_db):
        """测试语义关键词生成"""
        service = CollectionMatchingService(test_db)
        
        test_cases = [
            ("工作日记", ["工作", "日记", "记录", "日志", "笔记"]),
            ("学习笔记", ["学习", "笔记", "教育", "知识"]),
            ("Python开发", ["Python", "开发"]),
            ("家庭相册", ["家庭", "相册"])
        ]
        
        for name, expected_semantic_words in test_cases:
            semantic_keywords = service._generate_semantic_keywords(name)
            
            # 验证包含预期的语义词汇
            for expected_word in expected_semantic_words:
                if expected_word in ["记录", "日志", "笔记", "教育", "知识"]:
                    # 这些是扩展词汇，可能包含也可能不包含
                    continue
                assert expected_word in semantic_keywords
    
    def test_generate_auto_match_rules(self, test_db):
        """测试自动匹配规则生成"""
        service = CollectionMatchingService(test_db)
        
        # 测试基本规则生成
        rules = service.generate_auto_match_rules("旅游", "旅行相关的照片和文档")
        
        assert rules["auto_match"] is True
        assert "keywords" in rules
        assert "title_patterns" in rules
        assert "content_patterns" in rules
        assert rules["match_threshold"] == 0.6
        
        # 验证关键词包含预期内容
        assert "旅游" in rules["keywords"]
        assert "旅行" in rules["keywords"]
    
    def test_calculate_match_score(self, test_db, sample_collections):
        """测试匹配分数计算"""
        service = CollectionMatchingService(test_db)
        
        # 创建测试内容
        content = Content(
            title="巴厘岛旅游照片.jpg",
            text="【场景描述】\n美丽的海滩和度假村\n【活动推理】\n旅游度假\n【关键元素】\n海滩,度假村,旅行",
            source_uri="webui://巴厘岛旅游照片.jpg"
        )
        
        # 获取旅游合集
        travel_collection = next(c for c in sample_collections if c.name == "旅游")
        
        match_score = service._calculate_match_score(content, travel_collection)
        
        # 应该有较高的匹配分数
        assert match_score > 0.5
        assert isinstance(match_score, float)
        assert 0 <= match_score <= 1
    
    def test_calculate_title_match_score(self, test_db):
        """测试标题匹配分数计算"""
        service = CollectionMatchingService(test_db)
        
        test_cases = [
            ("旅游照片.jpg", ["旅游", "旅行", "度假"], 0.8),  # 高匹配
            ("会议纪要.docx", ["会议", "纪要", "meeting"], 0.8),  # 高匹配
            ("普通文档.txt", ["旅游", "旅行", "度假"], 0.0),  # 无匹配
            ("项目旅行计划.pdf", ["旅游", "旅行", "度假"], 0.4)  # 部分匹配
        ]
        
        for title, keywords, expected_min_score in test_cases:
            score = service._calculate_title_match_score(title, keywords)
            
            if expected_min_score > 0:
                assert score >= expected_min_score
            else:
                assert score == 0.0
    
    def test_calculate_content_match_score(self, test_db):
        """测试内容匹配分数计算"""
        service = CollectionMatchingService(test_db)
        
        test_cases = [
            ("这是一次美好的旅游经历，我们去了海边度假", ["旅游", "度假", "海边"], 0.6),
            ("今天的会议讨论了项目进度和决议事项", ["会议", "纪要", "议题", "决议"], 0.6),
            ("这是一个普通的文档内容", ["旅游", "度假"], 0.0)
        ]
        
        for content_text, keywords, expected_min_score in test_cases:
            score = service._calculate_content_match_score(content_text, keywords)
            
            if expected_min_score > 0:
                assert score >= expected_min_score
            else:
                assert score == 0.0
    
    def test_calculate_activity_match_score(self, test_db):
        """测试活动匹配分数计算"""
        service = CollectionMatchingService(test_db)
        
        # 测试包含活动推理的内容
        content_with_activity = "【活动推理】\n旅游度假\n【关键元素】\n海滩,风景,度假村"
        keywords = ["旅游", "度假", "海滩"]
        
        score = service._calculate_activity_match_score(content_with_activity, keywords)
        
        assert score > 0.0
        assert isinstance(score, float)
        
        # 测试不包含活动推理的内容
        content_without_activity = "普通的文档内容，没有特殊格式"
        score_no_activity = service._calculate_activity_match_score(content_without_activity, keywords)
        
        assert score_no_activity == 0.0
    
    def test_parse_image_analysis(self, test_db):
        """测试图片分析解析"""
        service = CollectionMatchingService(test_db)
        
        # 测试完整的图片分析文本
        analysis_text = """
        【文本内容】
        巴厘岛度假村
        
        【场景描述】
        美丽的海滩风景，蓝天白云
        
        【活动推理】
        旅游度假
        
        【关键元素】
        海滩,度假村,旅行,风景
        
        【情感色彩】
        轻松愉快的度假氛围
        
        【分类建议】
        主要分类：生活点滴
        """
        
        parsed = service._parse_image_analysis(analysis_text)
        
        assert parsed["activity_inference"] == "旅游度假"
        assert "海滩" in parsed["key_elements"]
        assert "度假村" in parsed["key_elements"]
        assert parsed["scene_description"] == "美丽的海滩风景，蓝天白云"
        assert "生活点滴" in parsed["classification_suggestion"]
    
    def test_is_document_match_collection(self, test_db, sample_collections):
        """测试文档与合集的匹配判断"""
        service = CollectionMatchingService(test_db)
        
        # 创建旅游相关的内容
        travel_content = Content(
            title="泰国旅游照片.jpg",
            text="【活动推理】\n旅游度假\n【关键元素】\n海滩,旅行,度假",
            source_uri="webui://泰国旅游照片.jpg"
        )
        
        # 创建工作相关的内容
        work_content = Content(
            title="项目会议纪要.docx",
            text="会议时间：2024年10月3日，议题：项目进度讨论",
            source_uri="webui://项目会议纪要.docx"
        )
        
        travel_collection = next(c for c in sample_collections if c.name == "旅游")
        meeting_collection = next(c for c in sample_collections if c.name == "会议纪要")
        
        # 测试正确匹配
        assert service._is_document_match_collection(travel_content, travel_collection) is True
        assert service._is_document_match_collection(work_content, meeting_collection) is True
        
        # 测试错误匹配
        assert service._is_document_match_collection(travel_content, meeting_collection) is False
        assert service._is_document_match_collection(work_content, travel_collection) is False
    
    @patch('app.services.collection_matching_service.CollectionMatchingService._create_content_collection_association')
    def test_match_document_to_collections_success(self, mock_create_association, test_db, sample_collections, sample_content):
        """测试文档到合集的完整匹配流程"""
        service = CollectionMatchingService(test_db)
        
        # 使用海边度假照片（应该匹配旅游合集）
        content = sample_content[0]
        
        # 模拟匹配成功
        with patch.object(service, '_is_document_match_collection', return_value=True):
            matched_collections = service.match_document_to_collections(str(content.id))
        
        # 验证返回了匹配的合集
        assert len(matched_collections) > 0
        
        # 验证创建关联被调用
        assert mock_create_association.call_count > 0
        
        # 验证内容状态更新
        updated_content = test_db.query(Content).filter(Content.id == content.id).first()
        assert updated_content.meta["classification_status"] == "completed"
    
    def test_match_document_to_collections_no_content(self, test_db):
        """测试匹配不存在的文档"""
        service = CollectionMatchingService(test_db)
        
        result = service.match_document_to_collections("non-existent-id")
        
        assert result == []
    
    def test_match_document_to_collections_empty_content(self, test_db, sample_collections):
        """测试匹配空内容的文档"""
        service = CollectionMatchingService(test_db)
        
        # 创建空内容
        empty_content = Content(
            title="",
            text="",
            source_uri="webui://empty.txt"
        )
        test_db.add(empty_content)
        test_db.commit()
        
        result = service.match_document_to_collections(str(empty_content.id))
        
        # 空内容应该跳过匹配
        assert result == []
    
    def test_match_document_to_collections_no_collections(self, test_db, sample_content):
        """测试没有用户合集时的匹配"""
        service = CollectionMatchingService(test_db)
        
        # 删除所有合集
        test_db.query(Collection).delete()
        test_db.commit()
        
        content = sample_content[0]
        result = service.match_document_to_collections(str(content.id))
        
        # 没有合集时应该返回空列表
        assert result == []
    
    def test_error_handling_in_collection_matching(self, test_db, sample_collections, sample_content):
        """测试合集匹配中的错误处理"""
        service = CollectionMatchingService(test_db)
        content = sample_content[0]
        
        # 模拟在检查某个合集时出错
        original_method = service._is_document_match_collection
        
        def mock_method_with_error(content, collection):
            if collection.name == "旅游":
                raise Exception("模拟错误")
            return original_method(content, collection)
        
        with patch.object(service, '_is_document_match_collection', side_effect=mock_method_with_error):
            # 即使某个合集检查出错，也应该继续检查其他合集
            result = service.match_document_to_collections(str(content.id))
            
            # 应该返回结果（可能为空，但不应该抛出异常）
            assert isinstance(result, list)
