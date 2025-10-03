"""
图片解析服务单元测试
测试图片内容提取、GPT-4V分析、结构化输出解析等功能
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from app.parsers.image_parser import ImageParser


class TestImageParser:
    """图片解析服务测试类"""
    
    def test_init(self):
        """测试解析器初始化"""
        parser = ImageParser()
        assert parser is not None
    
    def test_can_parse_image_files(self):
        """测试图片文件类型识别"""
        parser = ImageParser()
        
        # 支持的图片格式
        supported_formats = [
            "test.jpg", "test.jpeg", "test.png", 
            "test.gif", "test.bmp", "test.webp"
        ]
        
        for filename in supported_formats:
            assert parser.can_parse(filename) is True
        
        # 不支持的格式
        unsupported_formats = [
            "test.txt", "test.pdf", "test.docx", 
            "test.mp4", "test.unknown"
        ]
        
        for filename in unsupported_formats:
            assert parser.can_parse(filename) is False
    
    def test_can_parse_case_insensitive(self):
        """测试文件扩展名大小写不敏感"""
        parser = ImageParser()
        
        test_cases = [
            "test.JPG", "test.JPEG", "test.PNG",
            "test.Jpg", "test.Png", "test.GIF"
        ]
        
        for filename in test_cases:
            assert parser.can_parse(filename) is True
    
    def test_build_extraction_prompt_generalization(self):
        """测试提示词的泛化性"""
        parser = ImageParser()
        prompt = parser._build_extraction_prompt("测试图片.jpg")
        
        # 验证提示词不包含硬编码的具体示例
        assert "旅游度假（风景、景点、旅行相关）" not in prompt
        assert "工作商务（办公环境、会议、商业活动）" not in prompt
        
        # 验证包含通用化的指导
        assert "包括但不限于" in prompt
        assert "请根据图片实际内容进行推理，不局限于上述类别" in prompt
        assert "根据图片的主要用途和内容性质确定" in prompt
    
    def test_build_extraction_prompt_structure(self):
        """测试提示词结构完整性"""
        parser = ImageParser()
        prompt = parser._build_extraction_prompt("示例图片.png")
        
        # 验证包含所有必要的分析维度
        required_sections = [
            "【文本内容】",
            "【场景描述】", 
            "【活动推理】",
            "【关键元素】",
            "【情感色彩】",
            "【分类建议】"
        ]
        
        for section in required_sections:
            assert section in prompt
        
        # 验证包含文件名
        assert "示例图片.png" in prompt
    
    def test_clean_text_basic(self):
        """测试文本清理功能"""
        parser = ImageParser()
        
        test_cases = [
            ("正常文本", "正常文本"),
            ("包含\x00空字符的文本", "包含空字符的文本"),
            ("包含\n换行符的文本", "包含\n换行符的文本"),
            ("", ""),
            (None, "")
        ]
        
        for input_text, expected_output in test_cases:
            result = parser._clean_text(input_text)
            assert result == expected_output
    
    def test_clean_text_control_characters(self):
        """测试控制字符清理"""
        parser = ImageParser()
        
        # 测试各种控制字符
        dirty_text = "文本" + chr(0) + "包含" + chr(1) + "各种" + chr(2) + "控制" + chr(3) + "字符" + chr(4)
        cleaned_text = parser._clean_text(dirty_text)
        
        # 验证控制字符被移除
        assert chr(0) not in cleaned_text
        assert chr(1) not in cleaned_text
        assert chr(2) not in cleaned_text
        assert chr(3) not in cleaned_text
        assert chr(4) not in cleaned_text
        
        # 验证正常文本保留
        assert "文本" in cleaned_text
        assert "包含" in cleaned_text
        assert "各种" in cleaned_text
    
    @patch('app.parsers.image_parser.OpenAI')
    def test_extract_with_gpt4v_success(self, mock_openai):
        """测试GPT-4V成功提取内容"""
        # 模拟OpenAI响应
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        【文本内容】
        巴厘岛度假村欢迎您
        
        【场景描述】
        美丽的海滩风景，蓝天白云，椰子树摇曳
        
        【活动推理】
        旅游度假
        
        【关键元素】
        海滩,度假村,椰子树,蓝天,白云
        
        【情感色彩】
        轻松愉快的度假氛围
        
        【分类建议】
        主要分类：生活点滴
        可能的次要分类：无
        推理依据：这是典型的旅游度假场景
        """
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        parser = ImageParser()
        
        # 创建临时图片文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'fake image data')
            temp_path = Path(temp_file.name)
        
        try:
            result = parser._extract_with_gpt4v(temp_path)
            
            assert "巴厘岛度假村欢迎您" in result
            assert "美丽的海滩风景" in result
            assert "旅游度假" in result
            assert "海滩,度假村,椰子树" in result
            assert "生活点滴" in result
            
        finally:
            # 清理临时文件
            os.unlink(temp_path)
    
    @patch('app.parsers.image_parser.OpenAI')
    def test_extract_with_gpt4v_api_error(self, mock_openai):
        """测试GPT-4V API错误处理"""
        # 模拟API错误
        mock_openai.side_effect = Exception("API调用失败")
        
        parser = ImageParser()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'fake image data')
            temp_path = Path(temp_file.name)
        
        try:
            result = parser._extract_with_gpt4v(temp_path)
            
            # API错误时应该返回空字符串
            assert result == ""
            
        finally:
            os.unlink(temp_path)
    
    @patch('app.parsers.image_parser.OpenAI')
    def test_extract_with_gpt4v_empty_response(self, mock_openai):
        """测试GPT-4V空响应处理"""
        # 模拟空响应
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = ""
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        parser = ImageParser()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'fake image data')
            temp_path = Path(temp_file.name)
        
        try:
            result = parser._extract_with_gpt4v(temp_path)
            
            # 空响应应该返回空字符串
            assert result == ""
            
        finally:
            os.unlink(temp_path)
    
    def test_parse_file_not_found(self):
        """测试解析不存在的文件"""
        parser = ImageParser()
        
        result = parser.parse(Path("/non/existent/file.jpg"))
        
        # 文件不存在时应该返回空结果
        assert result["text"] == ""
        assert result["title"] == ""
        assert result["modality"] == "image"
    
    @patch('app.parsers.image_parser.ImageParser._extract_with_gpt4v')
    def test_parse_success(self, mock_extract):
        """测试完整解析流程成功"""
        # 模拟GPT-4V提取结果
        mock_extract.return_value = """
        【文本内容】
        Python编程教程
        
        【场景描述】
        代码编辑器界面，显示Python代码
        
        【活动推理】
        编程学习
        
        【关键元素】
        代码,编程,Python,教程
        
        【情感色彩】
        专业的学习氛围
        
        【分类建议】
        主要分类：学习成长
        次要分类：科技前沿
        """
        
        parser = ImageParser()
        
        # 创建临时图片文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(b'fake image data')
            temp_path = Path(temp_file.name)
        
        try:
            result = parser.parse(temp_path)
            
            assert result["modality"] == "image"
            assert result["title"] == temp_path.name
            assert "Python编程教程" in result["text"]
            assert "代码编辑器界面" in result["text"]
            assert "编程学习" in result["text"]
            
        finally:
            os.unlink(temp_path)
    
    @patch('app.parsers.image_parser.ImageParser._extract_with_gpt4v')
    def test_parse_extraction_failure(self, mock_extract):
        """测试内容提取失败的处理"""
        # 模拟提取失败
        mock_extract.return_value = ""
        
        parser = ImageParser()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'fake image data')
            temp_path = Path(temp_file.name)
        
        try:
            result = parser.parse(temp_path)
            
            # 提取失败时应该返回基本信息
            assert result["modality"] == "image"
            assert result["title"] == temp_path.name
            assert result["text"] == ""
            
        finally:
            os.unlink(temp_path)
    
    def test_parse_unsupported_file_type(self):
        """测试解析不支持的文件类型"""
        parser = ImageParser()
        
        # 创建非图片文件
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b'text content')
            temp_path = Path(temp_file.name)
        
        try:
            # 即使文件存在，但类型不支持
            result = parser.parse(temp_path)
            
            # 应该返回空结果
            assert result["text"] == ""
            assert result["title"] == ""
            assert result["modality"] == "image"
            
        finally:
            os.unlink(temp_path)
    
    @patch('app.parsers.image_parser.OpenAI')
    def test_gpt4v_prompt_includes_filename(self, mock_openai):
        """测试GPT-4V提示词包含文件名"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "测试响应"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        parser = ImageParser()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'fake image data')
            temp_path = Path(temp_file.name)
        
        try:
            parser._extract_with_gpt4v(temp_path)
            
            # 验证调用参数包含文件名
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            
            # 找到包含提示词的消息
            prompt_message = next(msg for msg in messages if msg['role'] == 'user')
            prompt_content = prompt_message['content'][0]['text']
            
            # 验证文件名在提示词中
            assert temp_path.name in prompt_content
            
        finally:
            os.unlink(temp_path)
    
    def test_text_cleaning_preserves_structure(self):
        """测试文本清理保持结构完整性"""
        parser = ImageParser()
        
        # 测试包含结构化内容的文本
        structured_text = "【文本内容】" + chr(0) + "\n        这是提取的文本" + chr(1) + "\n        \n        【场景描述】" + chr(2) + "\n        这是场景描述" + chr(3) + "\n        \n        【活动推理】" + chr(4) + "\n        这是活动推理"
        
        cleaned = parser._clean_text(structured_text)
        
        # 验证结构标记保留
        assert "【文本内容】" in cleaned
        assert "【场景描述】" in cleaned
        assert "【活动推理】" in cleaned
        
        # 验证内容保留
        assert "这是提取的文本" in cleaned
        assert "这是场景描述" in cleaned
        assert "这是活动推理" in cleaned
        
        # 验证控制字符被移除
        for i in range(5):
            control_char = f"\\x0{i}"
            assert control_char not in repr(cleaned)
