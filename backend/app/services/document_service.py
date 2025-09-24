"""
文档处理服务
提供统一的文档处理接口和高级功能
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.parsers.document_processor import DocumentProcessor
from app.models import Content, Chunk
from app.workers.tasks import simple_chunk, generate_embeddings, classify_content

logger = logging.getLogger(__name__)

class DocumentService:
    """文档处理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.processor = DocumentProcessor()
    
    def process_and_store_file(self, file_path: str, created_by: str = "document_service") -> Dict[str, Any]:
        """
        处理文件并存储到数据库
        
        Args:
            file_path: 文件路径
            created_by: 创建者标识
            
        Returns:
            处理结果字典
        """
        try:
            # 解析文件
            parse_result = self.processor.process_file(file_path)
            
            if not parse_result.get('success', True):
                return {
                    "success": False,
                    "error": parse_result.get('metadata', {}).get('error', 'Unknown parsing error')
                }
            
            # 存储到数据库
            return self._store_parsed_content(parse_result, file_path, created_by)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def process_and_store_content(self, content: str, title: str, source_uri: str, 
                                created_by: str = "document_service") -> Dict[str, Any]:
        """
        处理文本内容并存储到数据库
        
        Args:
            content: 文本内容
            title: 文档标题
            source_uri: 来源 URI
            created_by: 创建者标识
            
        Returns:
            处理结果字典
        """
        try:
            # 解析内容
            parse_result = self.processor.process_content(content, title)
            
            if not parse_result.get('success', True):
                return {
                    "success": False,
                    "error": parse_result.get('metadata', {}).get('error', 'Unknown parsing error')
                }
            
            # 存储到数据库
            return self._store_parsed_content(parse_result, source_uri, created_by, title)
            
        except Exception as e:
            logger.error(f"Error processing content for {title}: {e}")
            return {"success": False, "error": str(e)}
    
    def _store_parsed_content(self, parse_result: Dict[str, Any], source_uri: str, 
                            created_by: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        将解析结果存储到数据库
        
        Args:
            parse_result: 解析结果
            source_uri: 来源 URI
            created_by: 创建者标识
            title: 文档标题（可选）
            
        Returns:
            存储结果字典
        """
        try:
            text_content = parse_result.get('text', '')
            if not text_content.strip():
                return {"success": False, "error": "No text content to store"}
            
            # 确定标题
            if title is None:
                title = parse_result.get('metadata', {}).get('title') or \
                       parse_result.get('metadata', {}).get('filename', 'Untitled')
            
            # 确定文档类型
            detected_type = parse_result.get('metadata', {}).get('detected_type', 'text')
            modality = 'image' if detected_type == 'image' else 'text'
            
            # 创建 Content 记录
            content_obj = Content(
                title=title,
                text=text_content,
                modality=modality,
                meta=parse_result.get('metadata', {}),
                source_uri=source_uri,
                created_by=created_by
            )
            
            self.db.add(content_obj)
            self.db.commit()
            self.db.refresh(content_obj)
            
            # 文本分块
            chunks = simple_chunk(text_content)
            chunk_ids = []
            
            for seq, chunk_text in enumerate(chunks):
                chunk = Chunk(
                    content_id=content_obj.id,
                    seq=seq,
                    text=chunk_text,
                    meta={
                        "source_uri": source_uri,
                        "chunk_index": seq,
                        "total_chunks": len(chunks)
                    }
                )
                self.db.add(chunk)
                chunk_ids.append(chunk.id)
            
            self.db.commit()
            
            # 立即进行快速分类（高优先级）
            from app.workers.quick_tasks import quick_classify_content
            quick_classify_content.apply_async(
                args=[str(content_obj.id)], 
                queue="quick", 
                priority=9
            )
            
            # 异步生成 embeddings
            if chunk_ids:
                chunk_ids_str = [str(cid) for cid in chunk_ids]
                generate_embeddings.delay(chunk_ids_str)
            
            # 异步进行精确AI分类（较低优先级，会覆盖快速分类）
            classify_content.apply_async(
                args=[str(content_obj.id)], 
                queue="classify", 
                priority=5,
                countdown=30  # 延迟30秒执行，让用户先看到快速分类结果
            )
            
            result = {
                "success": True,
                "content_id": str(content_obj.id),
                "title": title,
                "chunks_created": len(chunks),
                "text_length": len(text_content),
                "file_type": parse_result.get('metadata', {}).get('detected_type', 'unknown'),
                "embedding_scheduled": len(chunk_ids) > 0
            }
            
            logger.info(f"Successfully stored document {title}: {len(chunks)} chunks created")
            return result
            
        except Exception as e:
            logger.error(f"Error storing parsed content: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """
        获取支持的文档格式信息
        
        Returns:
            支持格式的详细信息
        """
        return {
            "supported_extensions": self.processor.get_supported_extensions(),
            "parser_info": self.processor.get_parser_info(),
            "description": {
                "pdf": "支持纯文本 PDF 文档的文本提取",
                "markdown": "支持 Markdown 格式文档，包括 Front Matter 解析",
                "text": "支持各种编码的纯文本文件，包括代码文件"
            }
        }
    
    def validate_file(self, filename: str) -> Dict[str, Any]:
        """
        验证文件是否支持处理
        
        Args:
            filename: 文件名
            
        Returns:
            验证结果
        """
        is_supported = self.processor.is_supported(filename)
        file_type = self.processor.detect_file_type(filename)
        
        return {
            "supported": is_supported,
            "file_type": file_type,
            "parser": file_type if is_supported else None,
            "message": f"File type '{file_type}' is {'supported' if is_supported else 'not supported'}"
        }
