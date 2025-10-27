"""
文件上传服务 - 高聚合的文件处理逻辑
"""
import os
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from fastapi import UploadFile, HTTPException

from app.services.user_context_service import UserContextService
from app.parsers.document_processor import DocumentProcessor
from app.models import Content

logger = logging.getLogger(__name__)

class FileUploadService:
    """文件上传服务 - 统一的文件处理逻辑"""
    
    def __init__(self, context: UserContextService):
        self.context = context
        self.processor = DocumentProcessor()
        self.upload_dir = Path("/app/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """验证文件是否符合上传要求"""
        # 检查文件类型
        if not self.processor.is_supported(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.filename}"
            )
        
        # 检查文件大小 (MVP: 20MB限制)
        max_size = 20 * 1024 * 1024  # 20MB
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大: {file.filename} ({file.size / 1024 / 1024:.1f}MB)，最大支持20MB"
            )
        
        # 获取文件信息
        file_extension = Path(file.filename).suffix.lower()
        is_image = file_extension in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        return {
            "filename": file.filename,
            "size": file.size or 0,
            "extension": file_extension,
            "is_image": is_image,
            "is_large": (file.size or 0) > 10 * 1024 * 1024  # 10MB
        }
    
    def validate_batch_upload(self, files: List[UploadFile]) -> Dict[str, Any]:
        """验证批量上传请求"""
        # MVP限制：最多5个文件
        if len(files) > 5:
            raise HTTPException(
                status_code=400,
                detail=f"MVP阶段一次最多只能上传5个文件，当前选择了{len(files)}个文件"
            )
        
        # 验证每个文件
        file_infos = []
        total_size = 0
        
        for file in files:
            file_info = self.validate_file(file)
            file_infos.append(file_info)
            total_size += file_info["size"]
        
        # 验证总大小 (MVP: 100MB限制)
        max_total_size = 100 * 1024 * 1024  # 100MB
        if total_size > max_total_size:
            raise HTTPException(
                status_code=400,
                detail=f"批量上传总大小不能超过100MB，当前：{total_size / 1024 / 1024:.1f}MB"
            )
        
        return {
            "files": file_infos,
            "total_size": total_size,
            "total_count": len(files)
        }
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """生成唯一文件名，避免冲突"""
        base_path = self.upload_dir / original_filename
        
        if not base_path.exists():
            return original_filename
        
        # 生成时间戳后缀
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_part = Path(original_filename).stem
        extension = Path(original_filename).suffix
        
        return f"{name_part}_{timestamp}{extension}"
    
    async def save_file(self, file: UploadFile) -> Tuple[Path, bytes]:
        """保存上传的文件到本地"""
        # 生成唯一文件名
        actual_filename = self.generate_unique_filename(file.filename)
        file_path = self.upload_dir / actual_filename
        
        # 读取文件内容
        file_content = await file.read()
        
        # 保存到本地
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        logger.info(f"📁 File saved: {actual_filename} ({len(file_content) / 1024 / 1024:.1f}MB)")
        
        return file_path, file_content
    
    def create_content_record(self, file_info: Dict[str, Any], file_path: Path) -> Content:
        """创建内容记录"""
        # 基本元数据
        metadata = {
            "source_type": "webui",
            "file_size": file_info["size"],
            "file_extension": file_info["extension"],
            "is_image": file_info["is_image"],
            "is_large_file": file_info["is_large"],
            "upload_timestamp": datetime.utcnow().isoformat(),
            "classification_status": "pending",
            "show_classification": True,  # 立即允许显示状态
            "processing_status": "uploaded",
            "parsing_status": "pending",
            "file_path": str(file_path),
            "original_filename": file_info["filename"],
            "stored_filename": file_path.name,
        }
        
        # 创建内容记录（自动设置用户ID）
        content = self.context.create_user_content(
            title=file_info["filename"],
            text="",  # 异步解析后填充
            modality='image' if file_info["is_image"] else 'text',
            storage_provider="local",
            file_size=file_info["size"],
            source_uri=f"webui://{file_path.name}",
            meta=metadata
        )
        
        return content
    
    async def process_single_file(self, file: UploadFile) -> Dict[str, Any]:
        """处理单个文件上传"""
        try:
            # 验证文件
            file_info = self.validate_file(file)
            
            # 保存文件
            file_path, file_content = await self.save_file(file)
            
            # 创建内容记录
            content = self.create_content_record(file_info, file_path)
            self.context.db.commit()
            self.context.db.refresh(content)
            
            logger.info(f"✅ Single file processed: {file.filename} -> content_id: {content.id}")
            
            return {
                "status": "success",
                "content_id": str(content.id),
                "filename": file.filename,
                "size": file_info["size"],
                "message": "文件上传成功"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Single file processing failed: {file.filename}, error: {e}")
            raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
    
    async def process_batch_files(self, files: List[UploadFile]) -> Dict[str, Any]:
        """处理批量文件上传"""
        try:
            # 验证批量上传
            batch_info = self.validate_batch_upload(files)
            
            results = []
            success_count = 0
            failed_count = 0
            
            # 处理每个文件
            for i, file in enumerate(files):
                try:
                    logger.info(f"📦 Processing batch file {i+1}/{len(files)}: {file.filename}")
                    
                    # 验证单个文件（已在batch验证中完成，这里是双重保险）
                    file_info = batch_info["files"][i]
                    
                    # 保存文件
                    file_path, file_content = await self.save_file(file)
                    
                    # 创建内容记录
                    content = self.create_content_record(file_info, file_path)
                    self.context.db.commit()
                    self.context.db.refresh(content)
                    
                    # 构建与前端期望格式匹配的结果
                    upload_response = {
                        "status": "success",
                        "content_id": str(content.id),
                        "title": file.filename,
                        "processing_status": "uploaded",
                        "chunks_created": 0,
                        "file_size": file_info["size"],
                        "message": "文件上传成功"
                    }
                    
                    results.append({
                        "index": i,
                        "filename": file.filename,
                        "status": "success",
                        "result": upload_response
                    })
                    
                    success_count += 1
                    logger.info(f"✅ Batch file {i+1} processed: {file.filename}")
                    
                except Exception as file_error:
                    logger.error(f"❌ Batch file {i+1} failed: {file.filename}, error: {file_error}")
                    
                    results.append({
                        "index": i,
                        "filename": file.filename,
                        "status": "error",
                        "error": str(file_error)
                    })
                    
                    failed_count += 1
            
            # 返回批量处理结果（与前端期望格式匹配）
            batch_result = {
                "status": "completed",
                "total_files": len(files),
                "success_count": success_count,
                "error_count": failed_count,  # ✅ 修复：使用前端期望的字段名
                "results": results,
                "message": f"批量上传完成：成功 {success_count} 个，失败 {failed_count} 个"
            }
            
            logger.info(f"🎉 Batch upload completed: {success_count}/{len(files)} successful")
            
            return batch_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Batch processing failed: {e}")
            raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")
    
    def schedule_background_tasks(self, content_id: str, file_path: str):
        """调度后台任务处理"""
        try:
            # 导入任务函数
            from app.workers.tasks import parse_and_chunk_file
            from app.workers.quick_tasks import quick_classify_content
            from app.workers.tasks import classify_content, generate_image_thumbnail
            
            # 1. 立即调度文件解析任务（最高优先级）
            parse_and_chunk_file.apply_async(
                args=[content_id, file_path, self.context.user_id],  # 传递用户ID
                queue="quick",
                priority=10,
                countdown=0.1
            )
            
            # 2. 如果是图片，生成缩略图
            file_extension = Path(file_path).suffix.lower()
            if file_extension in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
                generate_image_thumbnail.apply_async(
                    args=[content_id, file_path],
                    queue="heavy",
                    priority=7,
                    countdown=0.5
                )
            
            # 3. 快速分类（2秒后执行）
            quick_classify_content.apply_async(
                args=[content_id, self.context.user_id],  # 传递用户ID
                queue="quick",
                priority=9,
                countdown=2
            )
            
            # 4. AI精确分类（4秒后执行）
            classify_content.apply_async(
                args=[content_id, self.context.user_id],  # 传递用户ID
                queue="classify",
                priority=8,
                countdown=4
            )
            
            # 5. 智能合集匹配（10秒后执行，确保分类完成）
            from app.workers.quick_tasks import match_document_to_collections
            match_document_to_collections.apply_async(
                args=[content_id, self.context.user_id],  # 传递用户ID
                queue="quick",
                priority=7,
                countdown=10
            )
            
            logger.info(f"🚀 Background tasks scheduled for content {content_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule background tasks for {content_id}: {e}")
            # 不抛出异常，因为文件已经上传成功

class FileUploadServiceFactory:
    """文件上传服务工厂"""
    
    @staticmethod
    def create_for_user(context: UserContextService) -> FileUploadService:
        """为指定用户创建文件上传服务"""
        return FileUploadService(context)
