#!/usr/bin/env python3
"""
修复缩略图问题的脚本
"""
import sys
import os
sys.path.append('/path/to/your/backend')  # 根据实际路径调整

from pathlib import Path
from PIL import Image
import hashlib
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 缩略图配置
THUMBNAIL_DIR = Path("/tmp/pkb_thumbnails")
THUMBNAIL_SIZE = (300, 200)
THUMBNAIL_QUALITY = 85
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

def get_thumbnail_path(original_file_path: Path) -> Path:
    """生成缩略图路径"""
    THUMBNAIL_DIR.mkdir(exist_ok=True)
    
    # 使用文件内容的哈希值作为缩略图文件名，避免重复
    file_hash = hashlib.md5(str(original_file_path).encode()).hexdigest()
    thumbnail_filename = f"{file_hash}.jpg"
    return THUMBNAIL_DIR / thumbnail_filename

def generate_thumbnail(image_path: Path, max_size: tuple = THUMBNAIL_SIZE) -> bytes:
    """生成缩略图数据"""
    try:
        with Image.open(image_path) as img:
            # 转换为RGB模式（处理RGBA等格式）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 生成缩略图
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存为JPEG格式
            from io import BytesIO
            output = BytesIO()
            img.save(output, format='JPEG', quality=THUMBNAIL_QUALITY, optimize=True)
            return output.getvalue()
            
    except Exception as e:
        logger.error(f"Failed to generate thumbnail for {image_path}: {e}")
        raise

def create_and_save_thumbnail(image_path: Path) -> Path:
    """创建并保存缩略图"""
    thumbnail_path = get_thumbnail_path(image_path)
    
    # 如果缩略图已存在，直接返回
    if thumbnail_path.exists():
        return thumbnail_path
    
    try:
        # 生成缩略图数据
        thumbnail_data = generate_thumbnail(image_path)
        
        # 保存缩略图文件
        with open(thumbnail_path, 'wb') as f:
            f.write(thumbnail_data)
        
        logger.info(f"Created thumbnail: {thumbnail_path}")
        return thumbnail_path
        
    except Exception as e:
        logger.error(f"Failed to create thumbnail for {image_path}: {e}")
        raise

def find_image_files():
    """查找可能的图片文件位置"""
    possible_dirs = [
        Path("/tmp/pkb_uploads"),
        Path("/app/uploads"),
        Path("/uploads"),
        Path("/data/uploads"),
        Path("/var/uploads"),
    ]
    
    found_files = []
    
    for upload_dir in possible_dirs:
        if upload_dir.exists():
            logger.info(f"Checking directory: {upload_dir}")
            for file_path in upload_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                    found_files.append(file_path)
                    logger.info(f"Found image: {file_path}")
    
    return found_files

def batch_generate_thumbnails():
    """批量生成缩略图"""
    logger.info("开始批量生成缩略图...")
    
    # 查找所有图片文件
    image_files = find_image_files()
    
    if not image_files:
        logger.warning("没有找到任何图片文件")
        return
    
    success_count = 0
    error_count = 0
    
    for image_path in image_files:
        try:
            thumbnail_path = create_and_save_thumbnail(image_path)
            logger.info(f"✅ 成功生成缩略图: {image_path.name} -> {thumbnail_path}")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ 生成缩略图失败: {image_path.name} - {e}")
            error_count += 1
    
    logger.info(f"批量生成完成: 成功 {success_count}, 失败 {error_count}")

if __name__ == "__main__":
    batch_generate_thumbnails()
