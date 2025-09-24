"""
统一文档处理器
整合所有文档解析器，提供统一的文档处理接口
"""

import os
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

from .pdf_parser import PDFParser
from .markdown_parser import MarkdownParser
from .text_parser import TextParser
from .image_parser import ImageParser

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """统一文档处理器"""
    
    def __init__(self):
        # 初始化各种解析器
        self.pdf_parser = PDFParser()
        self.markdown_parser = MarkdownParser()
        self.text_parser = TextParser()
        self.image_parser = ImageParser()
        
        # 文件类型映射
        self.parser_mapping = {
            'pdf': self.pdf_parser,
            'markdown': self.markdown_parser,
            'text': self.text_parser,
            'image': self.image_parser
        }
    
    def process_file(self, file_path: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        处理本地文件
        
        Args:
            file_path: 文件路径
            file_type: 指定文件类型（如果为 None 则自动检测）
            
        Returns:
            处理结果字典
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "text": "",
                    "metadata": {"error": f"File not found: {file_path}"},
                    "success": False
                }
            
            # 检测文件类型
            if file_type is None:
                file_type = self.detect_file_type(file_path)
            
            # 选择合适的解析器
            parser = self._get_parser(file_type)
            if parser is None:
                return {
                    "text": "",
                    "metadata": {"error": f"Unsupported file type: {file_type}"},
                    "success": False
                }
            
            # 解析文件
            result = parser.parse_file(file_path)
            
            # 添加处理器信息
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['processor'] = 'DocumentProcessor'
            result['metadata']['file_path'] = file_path
            result['metadata']['detected_type'] = file_type
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {
                "text": "",
                "metadata": {"error": str(e), "file_path": file_path},
                "success": False
            }
    
    def process_bytes(self, file_bytes: bytes, filename: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        处理字节流数据
        
        Args:
            file_bytes: 文件字节数据
            filename: 文件名
            file_type: 指定文件类型（如果为 None 则自动检测）
            
        Returns:
            处理结果字典
        """
        try:
            # 检测文件类型
            if file_type is None:
                file_type = self.detect_file_type(filename)
            
            # 选择合适的解析器
            parser = self._get_parser(file_type)
            if parser is None:
                return {
                    "text": "",
                    "metadata": {"error": f"Unsupported file type: {file_type}"},
                    "success": False
                }
            
            # 解析字节流
            if file_type in ['pdf', 'image']:
                result = parser.parse_bytes(file_bytes, filename)
            else:
                # 文本类型文件
                result = parser.parse_bytes(file_bytes, filename)
            
            # 添加处理器信息
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['processor'] = 'DocumentProcessor'
            result['metadata']['filename'] = filename
            result['metadata']['detected_type'] = file_type
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing bytes for {filename}: {e}")
            return {
                "text": "",
                "metadata": {"error": str(e), "filename": filename},
                "success": False
            }
    
    def process_content(self, content: str, filename: str = "unknown", file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        处理文本内容
        
        Args:
            content: 文本内容
            filename: 文件名
            file_type: 指定文件类型（如果为 None 则自动检测）
            
        Returns:
            处理结果字典
        """
        try:
            # 检测文件类型
            if file_type is None:
                file_type = self.detect_file_type(filename)
                # 如果无法从文件名检测，尝试从内容检测
                if file_type == 'text':
                    file_type = self._detect_type_from_content(content)
            
            # 选择合适的解析器
            parser = self._get_parser(file_type)
            if parser is None:
                # 降级为文本处理
                parser = self.text_parser
                file_type = 'text'
            
            # 解析内容
            if hasattr(parser, 'parse_content'):
                result = parser.parse_content(content, filename)
            else:
                # 降级处理
                result = self.text_parser.parse_content(content, filename)
            
            # 添加处理器信息
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['processor'] = 'DocumentProcessor'
            result['metadata']['filename'] = filename
            result['metadata']['detected_type'] = file_type
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing content for {filename}: {e}")
            return {
                "text": content,  # 降级返回原始内容
                "metadata": {"error": str(e), "filename": filename},
                "success": False
            }
    
    def detect_file_type(self, filename: str) -> str:
        """
        根据文件名检测文件类型
        
        Args:
            filename: 文件名
            
        Returns:
            检测到的文件类型
        """
        filename_lower = filename.lower()
        
        # PDF 文件
        if filename_lower.endswith('.pdf'):
            return 'pdf'
        
        # Markdown 文件
        elif any(filename_lower.endswith(ext) for ext in ['.md', '.markdown', '.mdown', '.mkd']):
            return 'markdown'
        
        # 图片文件
        elif any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
            return 'image'
        
        # 其他文本文件
        else:
            return 'text'
    
    def _detect_type_from_content(self, content: str) -> str:
        """
        根据内容检测文件类型
        
        Args:
            content: 文件内容
            
        Returns:
            检测到的文件类型
        """
        content_stripped = content.strip()
        
        # 检测 Markdown 特征
        markdown_indicators = [
            content_stripped.startswith('#'),  # 标题
            '```' in content,  # 代码块
            content.count('](') > 0,  # 链接
            content.count('![') > 0,  # 图片
            '|' in content and content.count('|') > 2  # 表格
        ]
        
        if sum(markdown_indicators) >= 2:
            return 'markdown'
        
        return 'text'
    
    def _get_parser(self, file_type: str):
        """
        根据文件类型获取对应的解析器
        
        Args:
            file_type: 文件类型
            
        Returns:
            对应的解析器实例
        """
        return self.parser_mapping.get(file_type)
    
    def is_supported(self, filename: str) -> bool:
        """
        检查文件是否支持处理
        
        Args:
            filename: 文件名
            
        Returns:
            是否支持
        """
        file_type = self.detect_file_type(filename)
        parser = self._get_parser(file_type)
        return parser is not None and parser.is_supported(filename)
    
    def get_supported_extensions(self) -> Dict[str, list]:
        """
        获取所有支持的文件扩展名
        
        Returns:
            按解析器分类的扩展名字典
        """
        return {
            'pdf': self.pdf_parser.supported_extensions,
            'markdown': self.markdown_parser.supported_extensions,
            'text': self.text_parser.supported_extensions,
            'image': self.image_parser.supported_extensions
        }
    
    def get_parser_info(self) -> Dict[str, Any]:
        """
        获取解析器信息
        
        Returns:
            解析器信息字典
        """
        return {
            'available_parsers': list(self.parser_mapping.keys()),
            'supported_extensions': self.get_supported_extensions(),
            'total_supported_types': len(self.parser_mapping)
        }
