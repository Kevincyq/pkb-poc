"""
图片解析器 - 使用 GPT-4V 进行图片内容提取
"""

import os
import base64
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# 导入 OpenAI 客户端
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class ImageParser:
    """图片解析器 - 使用 GPT-4V 提取图片内容"""
    
    def __init__(self):
        self.supported_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        
        # 检查 OpenAI 库可用性
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI library not available. Install with: pip install openai>=1.0.0")
            self.openai_enabled = False
            self.openai_client = None
            return
        
        # 配置 Turing API
        self.turing_api_key = os.getenv("TURING_API_KEY")
        self.turing_api_base = os.getenv("TURING_API_BASE")
        self.vision_model = os.getenv("VISION_MODEL", "turing/gpt-4o-mini")
        
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
            logger.info(f"Vision client initialized successfully with model: {self.vision_model}")
        except Exception as e:
            logger.error(f"Failed to initialize GPT-4V client: {e}")
            self.openai_enabled = False
    
    def is_supported(self, filename: str) -> bool:
        """检查文件是否支持解析"""
        if not self.openai_enabled:
            return False
        
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.supported_extensions
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析图片文件
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            解析结果字典
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "text": "",
                    "metadata": {"error": f"File not found: {file_path}"},
                    "success": False
                }
            
            # 读取图片文件
            with open(file_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            filename = Path(file_path).name
            return self.parse_bytes(image_bytes, filename)
            
        except Exception as e:
            logger.error(f"Error parsing image file {file_path}: {e}")
            return {
                "text": "",
                "metadata": {"error": str(e), "file_path": file_path},
                "success": False
            }
    
    def parse_bytes(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        解析图片字节数据
        
        Args:
            image_bytes: 图片字节数据
            filename: 文件名
            
        Returns:
            解析结果字典
        """
        try:
            if not self.openai_enabled:
                return {
                    "text": "",
                    "metadata": {"error": "Vision client not available"},
                    "success": False
                }
            
            # 将图片转换为 base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # 检测图片格式
            image_format = self._detect_image_format(image_bytes)
            
            # 使用 GPT-4V 分析图片
            extracted_text = self._extract_text_with_gpt4v(base64_image, image_format, filename)
            
            if not extracted_text:
                return {
                    "text": "",
                    "metadata": {
                        "error": "No text extracted from image",
                        "filename": filename,
                        "image_format": image_format
                    },
                    "success": False
                }
            
            # 清理可能的NUL字符和其他控制字符
            cleaned_text = self._clean_text(extracted_text)
            
            return {
                "text": cleaned_text,
                "metadata": {
                    "filename": filename,
                    "parser": "ImageParser",
                    "image_format": image_format,
                    "extraction_method": "GPT-4o-mini",
                    "file_size": len(image_bytes)
                },
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error parsing image bytes for {filename}: {e}")
            return {
                "text": "",
                "metadata": {"error": str(e), "filename": filename},
                "success": False
            }
    
    def _detect_image_format(self, image_bytes: bytes) -> str:
        """检测图片格式"""
        if image_bytes.startswith(b'\xff\xd8\xff'):
            return 'jpeg'
        elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        elif image_bytes.startswith(b'GIF87a') or image_bytes.startswith(b'GIF89a'):
            return 'gif'
        elif image_bytes.startswith(b'BM'):
            return 'bmp'
        elif image_bytes.startswith(b'RIFF') and b'WEBP' in image_bytes[:12]:
            return 'webp'
        else:
            return 'unknown'
    
    def _extract_text_with_gpt4v(self, base64_image: str, image_format: str, filename: str) -> str:
        """使用 GPT-4o-mini 提取图片中的文本内容"""
        try:
            # 构建提示词
            prompt = self._build_extraction_prompt(filename)
            
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format};base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            # 调用 GPT-4o-mini（添加超时控制）
            response = self.openai_client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                max_tokens=2000,
                temperature=0.1,
                timeout=30  # 30秒超时
            )
            
            extracted_text = response.choices[0].message.content
            
            logger.info(f"Successfully extracted text from image {filename} using GPT-4o-mini")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text with GPT-4o-mini for {filename}: {e}")
            return ""
    
    def _build_extraction_prompt(self, filename: str) -> str:
        """构建图片内容提取的提示词"""
        return f"""请仔细分析这张图片并提取其中的所有文本内容和重要信息。

文件名：{filename}

请按以下要求处理：
1. 如果图片包含文字（如文档、截图、海报等），请准确提取所有可见的文字内容
2. 如果图片是图表、图形或数据可视化，请描述其内容和数据信息
3. 如果图片是照片或场景，请描述主要内容、物体、人物、场景等
4. 保持提取内容的结构和格式，如标题、段落、列表等
5. 如果有表格，请尽量保持表格结构

请直接返回提取的内容，不需要额外的说明或格式标记。"""

    def _clean_text(self, text: str) -> str:
        """清理文本中的控制字符和NUL字符"""
        if not text:
            return ""
        
        # 移除NUL字符和其他控制字符
        cleaned = text.replace('\x00', '')  # 移除NUL字符
        
        # 移除其他可能有问题的控制字符，但保留常见的换行符和制表符
        import re
        cleaned = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)
        
        return cleaned.strip()

    def get_parser_info(self) -> Dict[str, Any]:
        """获取解析器信息"""
        return {
            "name": "ImageParser",
            "description": "使用 GPT-4o-mini 提取图片中的文本和内容信息",
            "supported_extensions": self.supported_extensions,
            "enabled": self.openai_enabled,
            "model": self.vision_model if self.openai_enabled else None,
            "capabilities": [
                "文字识别 (OCR)",
                "图表分析",
                "场景描述",
                "文档截图处理"
            ]
        }
