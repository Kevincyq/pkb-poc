"""
Markdown 文档解析器
支持 Markdown 格式的解析和文本提取
"""

import re
import logging
from typing import Dict, Any, List
from pathlib import Path

# 可选导入 markdown
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    markdown = None
    MARKDOWN_AVAILABLE = False

logger = logging.getLogger(__name__)

class MarkdownParser:
    """Markdown 文档解析器"""
    
    def __init__(self):
        self.supported_extensions = ['.md', '.markdown', '.mdown', '.mkd']
        
        # Markdown 扩展配置
        self.md_extensions = [
            'tables',           # 表格支持
            'fenced_code',      # 代码块支持
            'toc',              # 目录支持
            'footnotes',        # 脚注支持
            'attr_list',        # 属性列表支持
        ]
    
    def parse_file(self, file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        解析本地 Markdown 文件
        
        Args:
            file_path: Markdown 文件路径
            encoding: 文件编码
            
        Returns:
            解析结果字典
        """
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
                return self.parse_content(content, Path(file_path).name)
        except UnicodeDecodeError:
            # 尝试其他编码
            for alt_encoding in ['gbk', 'gb2312', 'latin1']:
                try:
                    with open(file_path, 'r', encoding=alt_encoding) as file:
                        content = file.read()
                        logger.info(f"Successfully read {file_path} with encoding {alt_encoding}")
                        return self.parse_content(content, Path(file_path).name)
                except UnicodeDecodeError:
                    continue
            
            logger.error(f"Failed to read {file_path} with any encoding")
            return {
                "text": "",
                "metadata": {"error": "Encoding detection failed"},
                "success": False
            }
        except Exception as e:
            logger.error(f"Error parsing Markdown file {file_path}: {e}")
            return {
                "text": "",
                "metadata": {"error": str(e)},
                "success": False
            }
    
    def parse_content(self, content: str, filename: str = "unknown.md") -> Dict[str, Any]:
        """
        解析 Markdown 内容
        
        Args:
            content: Markdown 文本内容
            filename: 文件名（用于日志）
            
        Returns:
            解析结果字典
        """
        try:
            # 提取元数据（YAML Front Matter）
            metadata = self._extract_front_matter(content)
            
            # 移除 Front Matter
            content_without_frontmatter = self._remove_front_matter(content)
            
            # 解析 Markdown 结构
            structure = self._parse_structure(content_without_frontmatter)
            
            # 转换为纯文本（保留结构）
            plain_text = self._convert_to_plain_text(content_without_frontmatter)
            
            # 转换为 HTML（可选，用于富文本显示）
            html_content = self._convert_to_html(content_without_frontmatter)
            
            # 统计信息
            char_count = len(plain_text)
            word_count = len(plain_text.split()) if plain_text else 0
            
            # 合并元数据
            metadata.update({
                "filename": filename,
                "parser": "MarkdownParser",
                "format": "markdown",
                "structure": structure,
                "char_count": char_count,
                "word_count": word_count
            })
            
            result = {
                "text": plain_text,
                "html": html_content,
                "raw_markdown": content,
                "metadata": metadata,
                "success": True
            }
            
            logger.info(f"Successfully parsed Markdown {filename}: {char_count} characters, {len(structure.get('headings', []))} headings")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing Markdown content for {filename}: {e}")
            return {
                "text": content,  # 降级为原始文本
                "metadata": {"error": str(e), "filename": filename},
                "success": False
            }
    
    def _extract_front_matter(self, content: str) -> Dict[str, Any]:
        """
        提取 YAML Front Matter
        
        Args:
            content: Markdown 内容
            
        Returns:
            Front Matter 字典
        """
        metadata = {}
        
        # 匹配 YAML Front Matter
        front_matter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(front_matter_pattern, content, re.DOTALL)
        
        if match:
            try:
                import yaml
                yaml_content = match.group(1)
                metadata = yaml.safe_load(yaml_content) or {}
            except ImportError:
                logger.warning("PyYAML not installed, skipping YAML front matter parsing")
                # 简单解析键值对
                yaml_content = match.group(1)
                for line in yaml_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
            except Exception as e:
                logger.warning(f"Error parsing YAML front matter: {e}")
        
        return metadata
    
    def _remove_front_matter(self, content: str) -> str:
        """
        移除 YAML Front Matter
        
        Args:
            content: Markdown 内容
            
        Returns:
            移除 Front Matter 后的内容
        """
        front_matter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        return re.sub(front_matter_pattern, '', content, flags=re.DOTALL)
    
    def _parse_structure(self, content: str) -> Dict[str, Any]:
        """
        解析 Markdown 结构
        
        Args:
            content: Markdown 内容
            
        Returns:
            结构信息字典
        """
        structure = {
            "headings": [],
            "code_blocks": [],
            "links": [],
            "images": [],
            "tables": []
        }
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 提取标题
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2)
                structure["headings"].append({
                    "level": level,
                    "title": title,
                    "line": line_num
                })
            
            # 提取链接
            link_matches = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', line)
            for text, url in link_matches:
                structure["links"].append({
                    "text": text,
                    "url": url,
                    "line": line_num
                })
            
            # 提取图片
            image_matches = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', line)
            for alt_text, url in image_matches:
                structure["images"].append({
                    "alt_text": alt_text,
                    "url": url,
                    "line": line_num
                })
            
            # 检测代码块
            if line.strip().startswith('```'):
                structure["code_blocks"].append({"line": line_num})
            
            # 检测表格
            if '|' in line and line.strip():
                structure["tables"].append({"line": line_num})
        
        return structure
    
    def _convert_to_plain_text(self, content: str) -> str:
        """
        将 Markdown 转换为纯文本，保留结构
        
        Args:
            content: Markdown 内容
            
        Returns:
            纯文本内容
        """
        # 保留标题结构
        text = re.sub(r'^(#{1,6})\s+(.+)$', r'\2', content, flags=re.MULTILINE)
        
        # 移除链接语法，保留文本
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # 移除图片语法
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'[图片: \1]', text)
        
        # 移除代码块标记
        text = re.sub(r'```[^\n]*\n', '', text)
        text = re.sub(r'```', '', text)
        
        # 移除行内代码标记
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # 移除粗体和斜体标记
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # 处理列表
        text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '• ', text, flags=re.MULTILINE)
        
        # 清理多余的空行
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def _convert_to_html(self, content: str) -> str:
        """
        将 Markdown 转换为 HTML
        
        Args:
            content: Markdown 内容
            
        Returns:
            HTML 内容
        """
        if not MARKDOWN_AVAILABLE:
            logger.warning("Markdown library not available, returning original content")
            return content
            
        try:
            md = markdown.Markdown(extensions=self.md_extensions)
            return md.convert(content)
        except Exception as e:
            logger.warning(f"Error converting Markdown to HTML: {e}")
            return content
    
    def is_supported(self, filename: str) -> bool:
        """
        检查文件是否支持解析
        
        Args:
            filename: 文件名
            
        Returns:
            是否支持
        """
        return any(filename.lower().endswith(ext) for ext in self.supported_extensions)
