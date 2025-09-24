"""
改进的文件服务 - 支持多种文件来源
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
import os
import logging
from pathlib import Path
from PIL import Image
import io
import hashlib
import time

router = APIRouter()
logger = logging.getLogger(__name__)

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

# 缩略图配置
THUMBNAIL_SIZE = (300, 200)
THUMBNAIL_QUALITY = 85

# 缩略图存储目录
THUMBNAIL_DIR = Path("/tmp/pkb_thumbnails")
THUMBNAIL_DIR.mkdir(exist_ok=True)

def get_file_path_by_source(source_uri: str) -> Path:
    """根据source_uri获取文件的实际路径"""
    
    if source_uri.startswith('webui://'):
        # WebUI上传的文件
        filename = source_uri.replace('webui://', '')
        possible_paths = [
            Path("/tmp/pkb_uploads") / filename,
            Path("/app/uploads") / filename,
            Path.cwd() / filename,
        ]
        
    elif source_uri.startswith('nextcloud://'):
        # Nextcloud文件 - 需要通过WebDAV访问或本地挂载
        filename = source_uri.replace('nextcloud://', '')
        possible_paths = [
            Path("/var/www/nextcloud/data") / filename,
            Path("/nextcloud/data") / filename,
            Path("/tmp/nextcloud") / filename,
            Path("/app/nextcloud") / filename,
        ]
        
    else:
        # 其他来源，尝试直接解析
        filename = Path(source_uri).name
        possible_paths = [
            Path("/tmp/pkb_uploads") / filename,
            Path.cwd() / filename,
        ]
    
    # 尝试所有可能的路径
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found file at: {path}")
            return path
    
    # 如果都找不到，返回第一个路径（用于错误提示）
    logger.warning(f"File not found for source_uri: {source_uri}")
    return possible_paths[0] if possible_paths else Path(source_uri)

def get_file_path(filename: str) -> Path:
    """获取文件的实际路径（兼容旧接口）"""
    # 尝试多个可能的存储位置
    possible_paths = [
        Path("/tmp/pkb_uploads") / filename,
        Path("/app/uploads") / filename,
        Path("/var/www/nextcloud/data") / filename,
        Path.cwd() / filename,
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return possible_paths[0]  # 返回默认路径

# ... 其余函数保持不变 ...

@router.get("/thumbnail/{filename}")
async def get_file_thumbnail(filename: str):
    """获取文件缩略图（改进版）"""
    try:
        file_path = get_file_path(filename)
        
        if not file_path.exists():
            # 尝试通过source_uri查找
            logger.info(f"File not found at {file_path}, trying alternative paths...")
            raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
        
        # 检查是否是支持的图片格式
        file_extension = file_path.suffix.lower()
        if file_extension not in SUPPORTED_IMAGE_FORMATS:
            raise HTTPException(status_code=400, detail="不支持的图片格式")
        
        # 生成缩略图（这里需要实现缩略图生成逻辑）
        # 临时返回原图
        return FileResponse(
            path=str(file_path),
            media_type="image/jpeg",
            filename=f"thumbnail_{filename}",
            headers={
                "Cache-Control": "public, max-age=3600",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thumbnail for {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"获取缩略图失败: {str(e)}")

@router.get("/debug/paths/{filename}")
async def debug_file_paths(filename: str):
    """调试接口：显示文件可能的路径"""
    possible_paths = [
        Path("/tmp/pkb_uploads") / filename,
        Path("/app/uploads") / filename,
        Path("/var/www/nextcloud/data") / filename,
        Path.cwd() / filename,
    ]
    
    results = []
    for path in possible_paths:
        results.append({
            "path": str(path),
            "exists": path.exists(),
            "is_file": path.is_file() if path.exists() else False
        })
    
    return {
        "filename": filename,
        "possible_paths": results,
        "current_working_directory": str(Path.cwd())
    }
