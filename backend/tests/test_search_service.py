"""
搜索服务单元测试
测试关键词搜索、语义搜索、混合搜索和多维度过滤功能
"""
import pytest
from unittest.mock import Mock, patch
from app.services.search_service import SearchService
from app.models import Content, Category, Collection, ContentCategory, Chunk


class TestSearchService:
    """搜索服务测试类"""
    
    def test_init(self, test_db):
        """测试服务初始化"""
        with patch('app.services.search_service.EmbeddingService') as mock_embedding:
            mock_embedding.return_value.is_enabled.return_value = True
            service = SearchService(test_db)
            assert service.db == test_db
    
    def test_extract_search_terms(self, test_db):
        """测试搜索词提取"""
        with patch('app.services.search_service.EmbeddingService'):
            service = SearchService(test_db)
            
            test_cases = [
                ("旅游 度假", ["旅游", "度假"]),
                ("Python编程学习", ["Python", "编程", "学习"]),
                ("会议纪要文档", ["会议", "纪要", "文档"]),
                ("single", ["single"]),
                ("", [])
            ]
            
            for query, expected_terms in test_cases:
                terms = service._extract_search_terms(query)
                
                # 验证包含预期的词汇
                for expected_term in expected_terms:
                    assert expected_term in terms or any(expected_term in term for term in terms)
    
    @patch('app.services.search_service.EmbeddingService')
    def test_keyword_search_basic(self, mock_embedding_service, test_db, sample_content):
        """测试基本关键词搜索"""
        # 创建chunks数据
        for content in sample_content:
            chunk = Chunk(
                id=f"chunk_{content.id}",
                content_id=content.id,
                text=content.text,
                chunk_index=0
            )
            test_db.add(chunk)
        test_db.commit()
        
        mock_embedding_service.return_value.is_enabled.return_value = False
        service = SearchService(test_db)
        
        # 测试搜索"海边"
        results = service._keyword_search("海边", 10)
        
        # 应该找到海边度假照片
        assert len(results) > 0
        
        # 验证结果结构
        for result in results:
            assert "content_id" in result
            assert "title" in result
            assert "text" in result
            assert "score" in result
    
    @patch('app.services.search_service.EmbeddingService')
    def test_keyword_search_with_filters(self, mock_embedding_service, test_db, sample_content, sample_categories):
        """测试带过滤条件的关键词搜索"""
        # 添加分类关联
        content = sample_content[0]  # 海边度假照片
        category = sample_categories[1]  # 生活点滴
        
        content_category = ContentCategory(
            content_id=content.id,
            category_id=category.id,
            confidence=0.8,
            role="primary_system",
            source="ml"
        )
        test_db.add(content_category)
        
        # 创建chunks
        chunk = Chunk(
            id=f"chunk_{content.id}",
            content_id=content.id,
            text=content.text,
            chunk_index=0
        )
        test_db.add(chunk)
        test_db.commit()
        
        mock_embedding_service.return_value.is_enabled.return_value = False
        service = SearchService(test_db)
        
        # 测试按分类过滤
        filters = {"categories": ["生活点滴"]}
        results = service._keyword_search("海边", 10, filters)
        
        assert len(results) > 0
        
        # 测试不匹配的分类过滤
        filters = {"categories": ["科技前沿"]}
        results = service._keyword_search("海边", 10, filters)
        
        assert len(results) == 0
    
    @patch('app.services.search_service.EmbeddingService')
    def test_semantic_search_disabled(self, mock_embedding_service, test_db, sample_content):
        """测试语义搜索功能禁用时的处理"""
        mock_embedding_service.return_value.is_enabled.return_value = False
        service = SearchService(test_db)
        
        results = service._semantic_search("美好的旅行回忆", 10)
        
        # 语义搜索禁用时应该返回空列表
        assert results == []
    
    @patch('app.services.search_service.EmbeddingService')
    def test_semantic_search_enabled(self, mock_embedding_service, test_db, sample_content):
        """测试语义搜索功能启用时的处理"""
        # 模拟embedding服务
        mock_service = Mock()
        mock_service.is_enabled.return_value = True
        mock_service.get_embedding.return_value = [0.1] * 384  # 模拟向量
        mock_service.search_similar.return_value = [
            {
                "content_id": str(sample_content[0].id),
                "title": sample_content[0].title,
                "text": sample_content[0].text,
                "score": 0.85,
                "source_uri": sample_content[0].source_uri
            }
        ]
        mock_embedding_service.return_value = mock_service
        
        service = SearchService(test_db)
        results = service._semantic_search("美好的旅行回忆", 10)
        
        assert len(results) > 0
        assert results[0]["score"] == 0.85
    
    @patch('app.services.search_service.EmbeddingService')
    def test_hybrid_search(self, mock_embedding_service, test_db, sample_content):
        """测试混合搜索"""
        # 创建chunks数据
        for content in sample_content:
            chunk = Chunk(
                id=f"chunk_{content.id}",
                content_id=content.id,
                text=content.text,
                chunk_index=0
            )
            test_db.add(chunk)
        test_db.commit()
        
        # 模拟embedding服务
        mock_service = Mock()
        mock_service.is_enabled.return_value = True
        mock_service.get_embedding.return_value = [0.1] * 384
        mock_service.search_similar.return_value = [
            {
                "content_id": str(sample_content[0].id),
                "title": sample_content[0].title,
                "text": sample_content[0].text,
                "score": 0.8,
                "source_uri": sample_content[0].source_uri
            }
        ]
        mock_embedding_service.return_value = mock_service
        
        service = SearchService(test_db)
        results = service._hybrid_search("海边度假", 10)
        
        # 混合搜索应该返回结果
        assert len(results) > 0
        
        # 验证结果包含混合分数
        for result in results:
            assert "score" in result
            assert isinstance(result["score"], (int, float))
    
    @patch('app.services.search_service.EmbeddingService')
    def test_apply_filters_modality(self, mock_embedding_service, test_db, sample_content):
        """测试按文件类型过滤"""
        mock_embedding_service.return_value.is_enabled.return_value = False
        service = SearchService(test_db)
        
        # 创建基础查询
        base_query = test_db.query(Content)
        
        # 测试图片类型过滤
        filters = {"modality": "image"}
        filtered_query = service._apply_filters(base_query, filters)
        results = filtered_query.all()
        
        # 验证只返回图片类型的内容
        for result in results:
            assert result.modality == "image"
    
    @patch('app.services.search_service.EmbeddingService')
    def test_apply_filters_confidence_range(self, mock_embedding_service, test_db, sample_content, sample_categories):
        """测试按置信度范围过滤"""
        # 添加不同置信度的分类
        content = sample_content[0]
        category = sample_categories[0]
        
        high_confidence_classification = ContentCategory(
            content_id=content.id,
            category_id=category.id,
            confidence=0.9,
            role="primary_system",
            source="ml"
        )
        test_db.add(high_confidence_classification)
        test_db.commit()
        
        mock_embedding_service.return_value.is_enabled.return_value = False
        service = SearchService(test_db)
        
        # 创建基础查询
        base_query = test_db.query(Content).outerjoin(
            ContentCategory, Content.id == ContentCategory.content_id
        )
        
        # 测试高置信度过滤
        filters = {"confidence_min": 0.8}
        filtered_query = service._apply_filters(base_query, filters)
        results = filtered_query.all()
        
        # 应该找到高置信度的内容
        assert len(results) > 0
        
        # 测试低置信度过滤（应该没有结果）
        filters = {"confidence_max": 0.5}
        filtered_query = service._apply_filters(base_query, filters)
        results = filtered_query.all()
        
        # 应该没有低置信度的结果
        assert len(results) == 0
    
    @patch('app.services.search_service.EmbeddingService')
    def test_apply_filters_role_and_source(self, mock_embedding_service, test_db, sample_content, sample_categories):
        """测试按角色和来源过滤"""
        content = sample_content[0]
        category = sample_categories[0]
        
        # 创建不同角色和来源的分类
        classifications = [
            ContentCategory(
                content_id=content.id,
                category_id=category.id,
                confidence=0.8,
                role="primary_system",
                source="ml"
            ),
            ContentCategory(
                content_id=sample_content[1].id,
                category_id=category.id,
                confidence=0.6,
                role="secondary_system",
                source="heuristic"
            )
        ]
        
        for classification in classifications:
            test_db.add(classification)
        test_db.commit()
        
        mock_embedding_service.return_value.is_enabled.return_value = False
        service = SearchService(test_db)
        
        base_query = test_db.query(Content).outerjoin(
            ContentCategory, Content.id == ContentCategory.content_id
        )
        
        # 测试按角色过滤
        filters = {"role": "primary_system"}
        filtered_query = service._apply_filters(base_query, filters)
        results = filtered_query.all()
        
        assert len(results) > 0
        
        # 测试按来源过滤
        filters = {"source": "ml"}
        filtered_query = service._apply_filters(base_query, filters)
        results = filtered_query.all()
        
        assert len(results) > 0
    
    @patch('app.services.search_service.EmbeddingService')
    def test_search_api_success(self, mock_embedding_service, test_db, sample_content):
        """测试搜索API成功场景"""
        # 创建chunks数据
        for content in sample_content:
            chunk = Chunk(
                id=f"chunk_{content.id}",
                content_id=content.id,
                text=content.text,
                chunk_index=0
            )
            test_db.add(chunk)
        test_db.commit()
        
        mock_embedding_service.return_value.is_enabled.return_value = False
        service = SearchService(test_db)
        
        result = service.search("海边", top_k=10, search_type="keyword")
        
        assert "query" in result
        assert "results" in result
        assert "total" in result
        assert "response_time" in result
        assert "search_type" in result
        assert "embedding_enabled" in result
        
        assert result["query"] == "海边"
        assert result["search_type"] == "keyword"
        assert isinstance(result["response_time"], (int, float))
    
    @patch('app.services.search_service.EmbeddingService')
    def test_search_api_error_handling(self, mock_embedding_service, test_db):
        """测试搜索API错误处理"""
        # 模拟数据库错误
        mock_embedding_service.return_value.is_enabled.return_value = False
        service = SearchService(test_db)
        
        # 关闭数据库连接以模拟错误
        test_db.close()
        
        result = service.search("测试查询", top_k=10, search_type="keyword")
        
        # 错误情况下应该返回错误响应
        assert result["results"] == []
        assert result["total"] == 0
        assert "error" in result
        assert result["query"] == "测试查询"
    
    @patch('app.services.search_service.EmbeddingService')
    def test_search_empty_query(self, mock_embedding_service, test_db):
        """测试空查询的处理"""
        mock_embedding_service.return_value.is_enabled.return_value = False
        service = SearchService(test_db)
        
        # 测试空字符串
        result = service.search("", top_k=10)
        assert result["results"] == []
        
        # 测试只有空格的字符串
        result = service.search("   ", top_k=10)
        assert result["results"] == []
    
    @patch('app.services.search_service.EmbeddingService')
    def test_search_with_complex_filters(self, mock_embedding_service, test_db, sample_content, sample_categories, sample_collections):
        """测试复杂过滤条件的搜索"""
        # 设置测试数据
        content = sample_content[0]
        category = sample_categories[1]  # 生活点滴
        collection = sample_collections[0]  # 旅游
        
        # 添加分类关联
        content_category = ContentCategory(
            content_id=content.id,
            category_id=category.id,
            confidence=0.85,
            role="primary_system",
            source="ml"
        )
        test_db.add(content_category)
        
        # 创建chunks
        chunk = Chunk(
            id=f"chunk_{content.id}",
            content_id=content.id,
            text=content.text,
            chunk_index=0
        )
        test_db.add(chunk)
        test_db.commit()
        
        mock_embedding_service.return_value.is_enabled.return_value = False
        service = SearchService(test_db)
        
        # 测试复合过滤条件
        filters = {
            "categories": ["生活点滴"],
            "modality": "image",
            "role": "primary_system",
            "source": "ml",
            "confidence_min": 0.8
        }
        
        result = service.search("海边", top_k=10, search_type="keyword", filters=filters)
        
        # 应该找到匹配的结果
        assert len(result["results"]) > 0
        
        # 测试不匹配的过滤条件
        filters["categories"] = ["科技前沿"]  # 不匹配的分类
        
        result = service.search("海边", top_k=10, search_type="keyword", filters=filters)
        
        # 应该没有结果
        assert len(result["results"]) == 0
