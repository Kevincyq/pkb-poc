"""
纯文本文档解析器
支持各种编码的纯文本文件解析
"""

import chardet
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TextParser:
    """纯文本文档解析器"""
    
    def __init__(self):
        self.supported_extensions = ['.txt', '.text', '.log', '.csv', '.json', '.xml', '.html', '.css', '.js', '.py', '.java', '.cpp', '.c', '.h']
        
        # 常见编码列表（按优先级排序）
        self.common_encodings = [
            'utf-8',
            'utf-8-sig',  # UTF-8 with BOM
            'gbk',
            'gb2312',
            'gb18030',
            'big5',
            'latin1',
            'cp1252',
            'ascii'
        ]
    
    def parse_file(self, file_path: str, encoding: Optional[str] = None) -> Dict[str, Any]:
        """
        解析本地文本文件
        
        Args:
            file_path: 文本文件路径
            encoding: 指定编码（如果为 None 则自动检测）
            
        Returns:
            解析结果字典
        """
        try:
            # 如果没有指定编码，尝试自动检测
            if encoding is None:
                encoding = self._detect_encoding(file_path)
            
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
                return self.parse_content(content, Path(file_path).name, encoding)
                
        except Exception as e:
            logger.error(f"Error parsing text file {file_path}: {e}")
            return {
                "text": "",
                "metadata": {"error": str(e)},
                "success": False
            }
    
    def parse_content(self, content: str, filename: str = "unknown.txt", encoding: str = "utf-8") -> Dict[str, Any]:
        """
        解析文本内容
        
        Args:
            content: 文本内容
            filename: 文件名（用于日志）
            encoding: 文件编码
            
        Returns:
            解析结果字典
        """
        try:
            # 基本统计信息
            char_count = len(content)
            line_count = content.count('\n') + 1 if content else 0
            word_count = len(content.split()) if content else 0
            
            # 检测文本特征
            features = self._analyze_text_features(content)
            
            # 构建元数据
            metadata = {
                "filename": filename,
                "parser": "TextParser",
                "format": "text",
                "encoding": encoding,
                "char_count": char_count,
                "line_count": line_count,
                "word_count": word_count,
                "features": features
            }
            
            # 检测文件类型
            file_type = self._detect_file_type(filename, content)
            if file_type:
                metadata["detected_type"] = file_type
            
            result = {
                "text": content,
                "metadata": metadata,
                "success": True
            }
            
            logger.info(f"Successfully parsed text file {filename}: {char_count} characters, {line_count} lines")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing text content for {filename}: {e}")
            return {
                "text": content,
                "metadata": {"error": str(e), "filename": filename},
                "success": False
            }
    
    def parse_bytes(self, text_bytes: bytes, filename: str = "unknown.txt", encoding: Optional[str] = None) -> Dict[str, Any]:
        """
        解析文本字节流
        
        Args:
            text_bytes: 文本字节数据
            filename: 文件名（用于日志）
            encoding: 指定编码（如果为 None 则自动检测）
            
        Returns:
            解析结果字典
        """
        try:
            # 如果没有指定编码，尝试自动检测
            if encoding is None:
                encoding = self._detect_encoding_from_bytes(text_bytes)
            
            content = text_bytes.decode(encoding)
            return self.parse_content(content, filename, encoding)
            
        except Exception as e:
            logger.error(f"Error parsing text bytes for {filename}: {e}")
            return {
                "text": "",
                "metadata": {"error": str(e)},
                "success": False
            }
    
    def _detect_encoding(self, file_path: str) -> str:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测到的编码
        """
        try:
            # 读取文件的一部分进行编码检测
            with open(file_path, 'rb') as file:
                raw_data = file.read(10240)  # 读取前10KB
                return self._detect_encoding_from_bytes(raw_data)
        except Exception as e:
            logger.warning(f"Error detecting encoding for {file_path}: {e}")
            return 'utf-8'  # 默认使用 UTF-8
    
    def _detect_encoding_from_bytes(self, data: bytes) -> str:
        """
        从字节数据检测编码
        
        Args:
            data: 字节数据
            
        Returns:
            检测到的编码
        """
        try:
            # 使用 chardet 检测编码
            result = chardet.detect(data)
            if result and result['encoding'] and result['confidence'] > 0.7:
                detected_encoding = result['encoding'].lower()
                logger.info(f"Detected encoding: {detected_encoding} (confidence: {result['confidence']:.2f})")
                return detected_encoding
        except Exception as e:
            logger.warning(f"Error using chardet for encoding detection: {e}")
        
        # 如果 chardet 失败，尝试常见编码
        for encoding in self.common_encodings:
            try:
                data.decode(encoding)
                logger.info(f"Successfully decoded with encoding: {encoding}")
                return encoding
            except UnicodeDecodeError:
                continue
        
        logger.warning("Could not detect encoding, using utf-8 as fallback")
        return 'utf-8'
    
    def _analyze_text_features(self, content: str) -> Dict[str, Any]:
        """
        分析文本特征
        
        Args:
            content: 文本内容
            
        Returns:
            特征字典
        """
        features = {}
        
        if not content:
            return features
        
        # 语言特征检测
        chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
        english_chars = len([c for c in content if c.isalpha() and ord(c) < 128])
        
        features['chinese_char_count'] = chinese_chars
        features['english_char_count'] = english_chars
        
        if chinese_chars > english_chars:
            features['primary_language'] = 'chinese'
        elif english_chars > 0:
            features['primary_language'] = 'english'
        else:
            features['primary_language'] = 'unknown'
        
        # 结构特征
        features['has_urls'] = 'http' in content.lower()
        features['has_emails'] = '@' in content and '.' in content
        features['has_code'] = any(keyword in content for keyword in ['function', 'class', 'import', 'def', 'var', 'const'])
        features['has_json'] = content.strip().startswith(('{', '['))
        features['has_xml'] = content.strip().startswith('<')
        
        # 格式特征
        features['avg_line_length'] = len(content) / (content.count('\n') + 1)
        features['empty_line_ratio'] = content.count('\n\n') / max(content.count('\n'), 1)
        
        return features
    
    def _detect_file_type(self, filename: str, content: str) -> Optional[str]:
        """
        根据文件名和内容检测文件类型
        
        Args:
            filename: 文件名
            content: 文件内容
            
        Returns:
            检测到的文件类型
        """
        filename_lower = filename.lower()
        content_stripped = content.strip()
        
        # 根据扩展名检测
        if filename_lower.endswith('.json'):
            return 'json'
        elif filename_lower.endswith('.xml'):
            return 'xml'
        elif filename_lower.endswith('.html'):
            return 'html'
        elif filename_lower.endswith('.css'):
            return 'css'
        elif filename_lower.endswith('.js'):
            return 'javascript'
        elif filename_lower.endswith('.py'):
            return 'python'
        elif filename_lower.endswith('.java'):
            return 'java'
        elif filename_lower.endswith(('.cpp', '.cc', '.cxx')):
            return 'cpp'
        elif filename_lower.endswith('.c'):
            return 'c'
        elif filename_lower.endswith('.h'):
            return 'header'
        elif filename_lower.endswith('.log'):
            return 'log'
        elif filename_lower.endswith('.csv'):
            return 'csv'
        
        # 根据内容检测
        if content_stripped.startswith(('{', '[')):
            return 'json'
        elif content_stripped.startswith('<'):
            return 'xml_or_html'
        elif 'function' in content or 'class' in content:
            return 'code'
        
        return 'plain_text'
    
    def is_supported(self, filename: str) -> bool:
        """
        检查文件是否支持解析
        
        Args:
            filename: 文件名
            
        Returns:
            是否支持
        """
        return any(filename.lower().endswith(ext) for ext in self.supported_extensions)
