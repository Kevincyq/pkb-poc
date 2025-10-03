"""
文件上传API单元测试
测试文件上传、重名处理、任务调度、边界情况等功能
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
from app.api.ingest import get_unique_filename, router
from app.models import Content
from datetime import datetime


class TestIngestAPI:
    """文件上传API测试类"""
    
    def test_get_unique_filename_no_conflict(self, tmp_path):
        """测试无重名文件的唯一文件名生成"""
        upload_dir = tmp_path
        original_filename = "test_document.pdf"
        
        result = get_unique_filename(upload_dir, original_filename)
        
        assert result == original_filename
    
    def test_get_unique_filename_with_conflict(self, tmp_path):
        """测试重名文件的唯一文件名生成"""
        upload_dir = tmp_path
        original_filename = "test_document.pdf"
        
        # 创建同名文件
        (upload_dir / original_filename).touch()
        
        result = get_unique_filename(upload_dir, original_filename)
        
        # 应该生成带时间戳的新文件名
        assert result != original_filename
        assert result.startswith("test_document_")
        assert result.endswith(".pdf")
        
        # 验证时间戳格式
        timestamp_part = result.replace("test_document_", "").replace(".pdf", "")
        assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS
    
    def test_get_unique_filename_multiple_conflicts(self, tmp_path):
        """测试多次重名的处理"""
        upload_dir = tmp_path
        original_filename = "document.txt"
        
        # 创建原文件
        (upload_dir / original_filename).touch()
        
        # 生成第一个唯一文件名
        first_unique = get_unique_filename(upload_dir, original_filename)
        
        # 创建第一个唯一文件
        (upload_dir / first_unique).touch()
        
        # 再次生成唯一文件名
        second_unique = get_unique_filename(upload_dir, original_filename)
        
        # 应该生成不同的文件名
        assert first_unique != second_unique
        assert original_filename != second_unique
    
    def test_get_unique_filename_no_extension(self, tmp_path):
        """测试无扩展名文件的处理"""
        upload_dir = tmp_path
        original_filename = "README"
        
        # 创建同名文件
        (upload_dir / original_filename).touch()
        
        result = get_unique_filename(upload_dir, original_filename)
        
        # 应该在文件名后添加时间戳
        assert result != original_filename
        assert result.startswith("README_")
    
    def test_get_unique_filename_chinese_characters(self, tmp_path):
        """测试中文文件名的处理"""
        upload_dir = tmp_path
        original_filename = "会议纪要.docx"
        
        # 创建同名文件
        (upload_dir / original_filename).touch()
        
        result = get_unique_filename(upload_dir, original_filename)
        
        # 应该正确处理中文文件名
        assert result != original_filename
        assert result.startswith("会议纪要_")
        assert result.endswith(".docx")
    
    @patch('app.api.ingest.quick_classify_content.apply_async')
    @patch('app.api.ingest.classify_content.apply_async')
    @patch('app.api.ingest.match_document_to_collections.apply_async')
    @patch('app.api.ingest.pregenerate_thumbnail_if_image')
    def test_upload_file_success(self, mock_thumbnail, mock_match, mock_classify, mock_quick, test_db):
        """测试文件上传成功流程"""
        from app.main import app
        client = TestClient(app)
        
        # 模拟任务调度
        mock_quick.return_value = Mock(id="quick_task_id")
        mock_classify.return_value = Mock(id="classify_task_id")
        mock_match.return_value = Mock(id="match_task_id")
        
        # 创建测试文件
        test_content = b"This is a test document content"
        
        with patch('app.api.ingest.get_db', return_value=test_db):
            response = client.post(
                "/api/ingest/upload",
                files={"file": ("test_document.txt", test_content, "text/plain")}
            )
        
        assert response.status_code == 200
        result = response.json()
        
        assert "content_id" in result
        assert result["message"] == "文件上传成功"
        assert result["filename"] == "test_document.txt"
        
        # 验证任务调度
        mock_quick.assert_called_once()
        mock_classify.assert_called_once()
        mock_match.assert_called_once()
        
        # 验证任务调度参数
        quick_args = mock_quick.call_args
        assert quick_args[1]["countdown"] == 1  # 1秒延迟
        assert quick_args[1]["priority"] == 10
        
        classify_args = mock_classify.call_args
        assert classify_args[1]["countdown"] == 1.5  # 1.5秒延迟
        assert classify_args[1]["priority"] == 9
        
        match_args = mock_match.call_args
        assert match_args[1]["countdown"] == 6  # 6秒延迟
        assert match_args[1]["priority"] == 8
    
    @patch('app.api.ingest.pregenerate_thumbnail_if_image')
    def test_upload_image_file(self, mock_thumbnail, test_db):
        """测试图片文件上传"""
        from app.main import app
        client = TestClient(app)
        
        # 创建测试图片文件
        test_image_content = b"fake image data"
        
        with patch('app.api.ingest.get_db', return_value=test_db), \
             patch('app.api.ingest.quick_classify_content.apply_async'), \
             patch('app.api.ingest.classify_content.apply_async'), \
             patch('app.api.ingest.match_document_to_collections.apply_async'):
            
            response = client.post(
                "/api/ingest/upload",
                files={"file": ("vacation_photo.jpg", test_image_content, "image/jpeg")}
            )
        
        assert response.status_code == 200
        
        # 验证缩略图生成被调用
        mock_thumbnail.assert_called_once()
        
        # 验证调用参数是Path对象
        call_args = mock_thumbnail.call_args[0]
        assert isinstance(call_args[0], Path)
    
    def test_upload_empty_file(self, test_db):
        """测试上传空文件"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.api.ingest.get_db', return_value=test_db):
            response = client.post(
                "/api/ingest/upload",
                files={"file": ("empty.txt", b"", "text/plain")}
            )
        
        # 空文件应该被拒绝
        assert response.status_code == 400
        result = response.json()
        assert "文件为空" in result["detail"]
    
    def test_upload_oversized_file(self, test_db):
        """测试上传超大文件"""
        from app.main import app
        client = TestClient(app)
        
        # 创建超大文件内容（模拟）
        large_content = b"x" * (100 * 1024 * 1024 + 1)  # 超过100MB
        
        with patch('app.api.ingest.get_db', return_value=test_db):
            response = client.post(
                "/api/ingest/upload",
                files={"file": ("large_file.txt", large_content, "text/plain")}
            )
        
        # 应该被拒绝（具体状态码取决于FastAPI配置）
        assert response.status_code in [413, 400]
    
    def test_upload_invalid_filename(self, test_db):
        """测试上传无效文件名"""
        from app.main import app
        client = TestClient(app)
        
        test_content = b"test content"
        
        # 测试各种无效文件名
        invalid_filenames = [
            "",  # 空文件名
            "   ",  # 只有空格
            "../../../etc/passwd",  # 路径遍历
            "file\x00name.txt",  # 包含空字符
            "con.txt",  # Windows保留名称
        ]
        
        for filename in invalid_filenames:
            with patch('app.api.ingest.get_db', return_value=test_db):
                response = client.post(
                    "/api/ingest/upload",
                    files={"file": (filename, test_content, "text/plain")}
                )
            
            # 无效文件名应该被处理或拒绝
            if response.status_code == 200:
                # 如果接受了，应该有安全的文件名处理
                result = response.json()
                assert result["filename"] != filename
            else:
                # 或者直接拒绝
                assert response.status_code in [400, 422]
    
    @patch('app.api.ingest.get_unique_filename')
    def test_upload_duplicate_filename_handling(self, mock_unique_filename, test_db):
        """测试重复文件名处理"""
        from app.main import app
        client = TestClient(app)
        
        # 模拟重名处理
        mock_unique_filename.return_value = "document_20241003_143022.txt"
        
        test_content = b"test document content"
        
        with patch('app.api.ingest.get_db', return_value=test_db), \
             patch('app.api.ingest.quick_classify_content.apply_async'), \
             patch('app.api.ingest.classify_content.apply_async'), \
             patch('app.api.ingest.match_document_to_collections.apply_async'):
            
            response = client.post(
                "/api/ingest/upload",
                files={"file": ("document.txt", test_content, "text/plain")}
            )
        
        assert response.status_code == 200
        result = response.json()
        
        # 验证返回的是唯一文件名
        assert result["filename"] == "document_20241003_143022.txt"
        
        # 验证get_unique_filename被调用
        mock_unique_filename.assert_called_once()
    
    def test_upload_no_file_provided(self, test_db):
        """测试未提供文件的情况"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.api.ingest.get_db', return_value=test_db):
            response = client.post("/api/ingest/upload")
        
        # 应该返回错误
        assert response.status_code == 422  # FastAPI validation error
    
    @patch('app.api.ingest.get_db')
    def test_upload_database_error(self, mock_get_db, test_db):
        """测试数据库错误处理"""
        from app.main import app
        client = TestClient(app)
        
        # 模拟数据库错误
        mock_get_db.side_effect = Exception("数据库连接失败")
        
        test_content = b"test content"
        
        response = client.post(
            "/api/ingest/upload",
            files={"file": ("test.txt", test_content, "text/plain")}
        )
        
        # 应该返回服务器错误
        assert response.status_code == 500
    
    def test_content_metadata_creation(self, test_db):
        """测试内容元数据创建"""
        from app.main import app
        client = TestClient(app)
        
        test_content = b"This is test document content for metadata testing"
        
        with patch('app.api.ingest.get_db', return_value=test_db), \
             patch('app.api.ingest.quick_classify_content.apply_async'), \
             patch('app.api.ingest.classify_content.apply_async'), \
             patch('app.api.ingest.match_document_to_collections.apply_async'):
            
            response = client.post(
                "/api/ingest/upload",
                files={"file": ("metadata_test.txt", test_content, "text/plain")}
            )
        
        assert response.status_code == 200
        result = response.json()
        
        # 验证数据库中的内容记录
        content = test_db.query(Content).filter(Content.id == result["content_id"]).first()
        
        assert content is not None
        assert content.title == "metadata_test.txt"
        assert content.modality == "text"
        assert content.source_uri.startswith("webui://")
        
        # 验证元数据
        assert content.meta is not None
        assert "original_filename" in content.meta
        assert "stored_filename" in content.meta
        assert "file_path" in content.meta
        assert content.meta["classification_status"] == "pending"
        assert content.meta["show_classification"] is False
    
    def test_task_scheduling_order(self, test_db):
        """测试任务调度顺序"""
        from app.main import app
        client = TestClient(app)
        
        with patch('app.api.ingest.get_db', return_value=test_db) as mock_db, \
             patch('app.api.ingest.quick_classify_content.apply_async') as mock_quick, \
             patch('app.api.ingest.classify_content.apply_async') as mock_classify, \
             patch('app.api.ingest.match_document_to_collections.apply_async') as mock_match:
            
            # 设置任务ID
            mock_quick.return_value = Mock(id="quick_id")
            mock_classify.return_value = Mock(id="classify_id")
            mock_match.return_value = Mock(id="match_id")
            
            test_content = b"test content for task scheduling"
            
            response = client.post(
                "/api/ingest/upload",
                files={"file": ("task_test.txt", test_content, "text/plain")}
            )
        
        assert response.status_code == 200
        
        # 验证任务调度顺序和延迟
        quick_call = mock_quick.call_args
        classify_call = mock_classify.call_args
        match_call = mock_match.call_args
        
        # 快速分类：1秒延迟，优先级10
        assert quick_call[1]["countdown"] == 1
        assert quick_call[1]["priority"] == 10
        
        # AI分类：1.5秒延迟，优先级9
        assert classify_call[1]["countdown"] == 1.5
        assert classify_call[1]["priority"] == 9
        
        # 合集匹配：6秒延迟，优先级8
        assert match_call[1]["countdown"] == 6
        assert match_call[1]["priority"] == 8
        
        # 验证调度顺序（通过延迟时间）
        assert quick_call[1]["countdown"] < classify_call[1]["countdown"]
        assert classify_call[1]["countdown"] < match_call[1]["countdown"]
