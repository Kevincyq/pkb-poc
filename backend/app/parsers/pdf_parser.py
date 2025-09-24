"""
PDF 文档解析器
支持纯文本 PDF 的文本提取
"""

import PyPDF2
import io
import logging
from typing import Dict, Any, Optional, BinaryIO
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFParser:
    """PDF 文档解析器"""
    
    def __init__(self):
        self.supported_extensions = ['.pdf']
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析本地 PDF 文件
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            解析结果字典，包含 text, metadata, page_count 等信息
        """
        try:
            with open(file_path, 'rb') as file:
                return self._parse_pdf_stream(file, Path(file_path).name)
        except Exception as e:
            logger.error(f"Error parsing PDF file {file_path}: {e}")
            return {
                "text": "",
                "metadata": {"error": str(e)},
                "page_count": 0,
                "success": False
            }
    
    def parse_bytes(self, pdf_bytes: bytes, filename: str = "unknown.pdf") -> Dict[str, Any]:
        """
        解析 PDF 字节流
        
        Args:
            pdf_bytes: PDF 文件的字节数据
            filename: 文件名（用于日志）
            
        Returns:
            解析结果字典
        """
        try:
            pdf_stream = io.BytesIO(pdf_bytes)
            return self._parse_pdf_stream(pdf_stream, filename)
        except Exception as e:
            logger.error(f"Error parsing PDF bytes for {filename}: {e}")
            return {
                "text": "",
                "metadata": {"error": str(e)},
                "page_count": 0,
                "success": False
            }
    
    def _parse_pdf_stream(self, pdf_stream: BinaryIO, filename: str) -> Dict[str, Any]:
        """
        解析 PDF 流的核心逻辑
        
        Args:
            pdf_stream: PDF 文件流
            filename: 文件名
            
        Returns:
            解析结果字典
        """
        try:
            reader = PyPDF2.PdfReader(pdf_stream)
            
            # 检查是否加密
            if reader.is_encrypted:
                logger.warning(f"PDF {filename} is encrypted, attempting to decrypt with empty password")
                try:
                    reader.decrypt("")
                except Exception as decrypt_error:
                    logger.error(f"Failed to decrypt PDF {filename}: {decrypt_error}")
                    return {
                        "text": "",
                        "metadata": {"error": "PDF is encrypted and cannot be decrypted"},
                        "page_count": 0,
                        "success": False
                    }
            
            # 提取文本
            text_content = []
            page_count = len(reader.pages)
            
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        # 清理和规范化文本
                        cleaned_text = self._clean_text(page_text.strip())
                        text_content.append(f"=== 第 {page_num + 1} 页 ===\n{cleaned_text}")
                except Exception as page_error:
                    logger.warning(f"Error extracting text from page {page_num + 1} of {filename}: {page_error}")
                    continue
            
            # 合并所有页面文本
            full_text = "\n\n".join(text_content)
            
            # 提取元数据
            metadata = self._extract_metadata(reader, filename)
            
            # 统计信息
            char_count = len(full_text)
            word_count = len(full_text.split()) if full_text else 0
            
            result = {
                "text": full_text,
                "metadata": metadata,
                "page_count": page_count,
                "char_count": char_count,
                "word_count": word_count,
                "success": True
            }
            
            logger.info(f"Successfully parsed PDF {filename}: {page_count} pages, {char_count} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing PDF stream for {filename}: {e}")
            return {
                "text": "",
                "metadata": {"error": str(e)},
                "page_count": 0,
                "success": False
            }
    
    def _extract_metadata(self, reader: PyPDF2.PdfReader, filename: str) -> Dict[str, Any]:
        """
        提取 PDF 元数据
        
        Args:
            reader: PyPDF2 阅读器对象
            filename: 文件名
            
        Returns:
            元数据字典
        """
        metadata = {
            "filename": filename,
            "parser": "PDFParser",
            "format": "pdf"
        }
        
        try:
            if reader.metadata:
                pdf_metadata = reader.metadata
                
                # 提取常见元数据字段
                if '/Title' in pdf_metadata:
                    metadata['title'] = str(pdf_metadata['/Title'])
                if '/Author' in pdf_metadata:
                    metadata['author'] = str(pdf_metadata['/Author'])
                if '/Subject' in pdf_metadata:
                    metadata['subject'] = str(pdf_metadata['/Subject'])
                if '/Creator' in pdf_metadata:
                    metadata['creator'] = str(pdf_metadata['/Creator'])
                if '/Producer' in pdf_metadata:
                    metadata['producer'] = str(pdf_metadata['/Producer'])
                if '/CreationDate' in pdf_metadata:
                    metadata['creation_date'] = str(pdf_metadata['/CreationDate'])
                if '/ModDate' in pdf_metadata:
                    metadata['modification_date'] = str(pdf_metadata['/ModDate'])
                    
        except Exception as e:
            logger.warning(f"Error extracting metadata from {filename}: {e}")
            metadata['metadata_error'] = str(e)
        
        return metadata
    
    def _clean_text(self, text: str) -> str:
        """
        清理和规范化PDF提取的文本
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除NUL字符和其他控制字符
        text = text.replace('\x00', '')
        
        # 移除其他可能的问题字符
        import re
        # 保留中文、英文、数字、标点和常见符号
        text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\x20-\x7E\n\r\t]', '', text)
        
        # 规范化空白字符
        text = re.sub(r'\s+', ' ', text)  # 多个空格合并为一个
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 多个换行合并为两个
        
        # 移除行首行尾空格
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def is_supported(self, filename: str) -> bool:
        """
        检查文件是否支持解析
        
        Args:
            filename: 文件名
            
        Returns:
            是否支持
        """
        return any(filename.lower().endswith(ext) for ext in self.supported_extensions)
