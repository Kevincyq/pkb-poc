"""
文件服务 API
提供文件缩略图生成和访问功能
"""

from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import FileResponse
import os
import logging
from pathlib import Path
from PIL import Image
import io
import hashlib
import time
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Content, Chunk, ContentCategory

router = APIRouter()
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

# 缩略图配置
THUMBNAIL_SIZE = (300, 200)
THUMBNAIL_QUALITY = 85

# 缩略图存储目录
THUMBNAIL_DIR = Path("/tmp/pkb_thumbnails")
THUMBNAIL_DIR.mkdir(exist_ok=True)

def get_file_path(filename: str, db: Session) -> Path:
    """获取文件的实际路径 - 优化版本，支持原始文件名和存储文件名映射"""
    logger.info(f"🔍 Looking for file: {filename}")
    logger.info(f"🔍 Filename type: {type(filename)}, repr: {repr(filename)}")
    
    try:
        # URL解码文件名（处理前端传来的编码文件名）
        import urllib.parse
        decoded_filename = urllib.parse.unquote(filename)
        logger.info(f"🔓 Decoded filename: {decoded_filename}")
        logger.info(f"🔓 Decoded type: {type(decoded_filename)}, repr: {repr(decoded_filename)}")
        
        # 1. 优先通过数据库查找（支持原始文件名和存储文件名）
        logger.info(f"🔍 Step 1: 尝试通过source_uri查找: webui://{filename}")
        content = db.query(Content).filter(
            Content.source_uri == f"webui://{filename}"
        ).first()
        
        # 如果没找到，尝试解码后的文件名
        if not content:
            logger.info(f"🔍 Step 2: 尝试通过解码后的source_uri查找: webui://{decoded_filename}")
            content = db.query(Content).filter(
                Content.source_uri == f"webui://{decoded_filename}"
            ).first()
        
        # 如果没找到，尝试通过原始文件名查找
        if not content:
            logger.info(f"🔍 Step 3: 尝试通过title查找: {filename}")
            content = db.query(Content).filter(
                Content.title == filename
            ).first()
            
        # 如果没找到，尝试解码后的原始文件名
        if not content:
            logger.info(f"🔍 Step 4: 尝试通过解码后的title查找: {decoded_filename}")
            content = db.query(Content).filter(
                Content.title == decoded_filename
            ).first()
        
        if content:
            logger.info(f"✅ Found content in database: id={content.id}, title={content.title}, source_uri={content.source_uri}")
            logger.info(f"📋 Content meta: {content.meta}")
            
            if content.meta and isinstance(content.meta, dict):
                # 优先使用数据库中存储的文件路径
                actual_path = content.meta.get('file_path')
                if actual_path:
                    file_path = Path(actual_path)
                    logger.info(f"📂 Database file path: {actual_path}, exists: {file_path.exists()}")
                    if file_path.exists():
                        logger.info(f"✅ Found file via database file_path: {filename} -> {actual_path}")
                        return file_path
                    else:
                        logger.warning(f"⚠️ Database file path does not exist: {actual_path}")
            
                # 如果数据库路径不存在，尝试使用存储文件名
                stored_filename = content.meta.get('stored_filename')
                if stored_filename:
                    stored_path = Path("/app/uploads") / stored_filename
                    logger.info(f"📂 Trying stored_filename: {stored_filename}, path: {stored_path}, exists: {stored_path.exists()}")
                    if stored_path.exists():
                        logger.info(f"✅ Found file via stored filename: {filename} -> {stored_path}")
                        return stored_path
            
            # 如果前端传来的是原始文件名，但数据库中存储的是带时间戳的文件名
            # 尝试通过source_uri获取实际的存储文件名
            if content.source_uri and content.source_uri.startswith('webui://'):
                actual_stored_filename = content.source_uri.replace('webui://', '')
                stored_path = Path("/app/uploads") / actual_stored_filename
                logger.info(f"📂 Trying source_uri filename: {actual_stored_filename}, path: {stored_path}, exists: {stored_path.exists()}")
                if stored_path.exists():
                    logger.info(f"✅ Found file via source_uri: {filename} -> {stored_path}")
                    return stored_path
                else:
                    logger.warning(f"⚠️ Source URI file not found: {stored_path}")
        else:
            logger.warning(f"❌ No database record found for: {filename}")
        
        # 2. 尝试直接匹配文件名（备用方案）
        possible_locations = [
            Path("/app/uploads") / filename,
            Path("/data/uploads") / filename,
            Path("/var/uploads") / filename,
            Path("/uploads") / filename,
            Path("/tmp/pkb_uploads") / filename,  # 临时目录放最后
        ]
        
        for file_path in possible_locations:
            if file_path.exists():
                logger.info(f"Found file via direct match: {filename} -> {file_path}")
                return file_path
        
        # 3. 尝试在各个目录中按文件名模糊匹配（而非仅按扩展名）
        target_name = Path(filename).stem.lower()  # 获取不带扩展名的文件名
        target_extension = Path(filename).suffix.lower()
        search_dirs = [Path("/app/uploads"), Path("/data/uploads"), Path("/var/uploads"), Path("/uploads"), Path("/tmp/pkb_uploads")]
        
        for base_dir in search_dirs:
            logger.info(f"Checking directory: {base_dir}, exists: {base_dir.exists()}")
            if not base_dir.exists():
                continue
                
            # 列出目录中的所有文件用于调试
            try:
                all_files = list(base_dir.rglob("*"))
                logger.info(f"Files in {base_dir}: {[f.name for f in all_files if f.is_file()][:10]}")  # 只显示前10个
            except Exception as e:
                logger.warning(f"Could not list files in {base_dir}: {e}")
                
            # 首先尝试精确的文件名匹配（不区分大小写）
            exact_matches = []
            fuzzy_matches = []
            
            for file in base_dir.rglob(f"*{target_extension}"):
                if file.is_file():
                    file_stem = file.stem.lower()
                    # 精确匹配文件名（不含扩展名）
                    if file_stem == target_name:
                        exact_matches.append(file)
                    # 模糊匹配（包含目标文件名）
                    elif target_name in file_stem or file_stem in target_name:
                        fuzzy_matches.append(file)
            
            logger.info(f"Found {len(exact_matches)} exact matches and {len(fuzzy_matches)} fuzzy matches for {filename}")
            
            # 优先返回精确匹配
            if exact_matches:
                # 如果有多个精确匹配，选择最新的
                best_match = max(exact_matches, key=lambda f: f.stat().st_mtime)
                logger.info(f"Found file via exact match: {filename} -> {best_match}")
                return best_match
            
            # 其次返回模糊匹配中最相似的
            elif fuzzy_matches:
                # 按文件名相似度排序，选择最相似的
                def similarity_score(file_path):
                    file_stem = file_path.stem.lower()
                    # 计算简单的相似度分数
                    if target_name == file_stem:
                        return 100
                    elif target_name in file_stem:
                        return 80 - abs(len(file_stem) - len(target_name))
                    elif file_stem in target_name:
                        return 70 - abs(len(target_name) - len(file_stem))
                    else:
                        return 0
                
                best_match = max(fuzzy_matches, key=similarity_score)
                logger.warning(f"Found file via fuzzy match: {filename} -> {best_match} (this may cause thumbnail issues)")
                return best_match
        
        # 4. 最后的回退
        logger.error(f"File not found anywhere: {filename}")
        return Path("/tmp/pkb_uploads") / filename
        
    except Exception as e:
        logger.error(f"Error in get_file_path for {filename}: {e}")
        return Path("/tmp/pkb_uploads") / filename

def get_thumbnail_path(original_file_path: Path, requested_filename: str = None) -> Path:
    """
    生成缩略图文件路径
    
    Args:
        original_file_path: 实际文件路径
        requested_filename: 用户请求的文件名（用于确保缓存键的一致性）
    """
    # 优先使用请求的文件名，确保缓存键一致性
    if requested_filename:
        base_name = Path(requested_filename).stem
    else:
        base_name = original_file_path.stem
    
    # 使用文件名、大小和修改时间生成唯一标识
    file_stat = original_file_path.stat()
    
    # 生成更稳定的缓存键：基于请求的文件名而非实际路径
    content = f"{base_name}_{file_stat.st_size}_{file_stat.st_mtime}"
    file_hash = hashlib.md5(content.encode()).hexdigest()
    
    thumbnail_filename = f"{base_name}_{file_hash[:8]}.jpg"  # 使用文件名前缀 + 短哈希
    return THUMBNAIL_DIR / thumbnail_filename

def generate_thumbnail(image_path: Path, max_size: tuple = THUMBNAIL_SIZE) -> bytes:
    """生成图片缩略图"""
    try:
        with Image.open(image_path) as img:
            # 转换为RGB模式（处理RGBA等格式）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 生成缩略图
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存到内存
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=THUMBNAIL_QUALITY, optimize=True)
            return output.getvalue()
            
    except Exception as e:
        logger.error(f"Failed to generate thumbnail for {image_path}: {e}")
        raise

def create_and_save_thumbnail(image_path: Path, requested_filename: str = None) -> Path:
    """创建并保存缩略图到磁盘"""
    thumbnail_path = get_thumbnail_path(image_path, requested_filename)
    
    # 如果缩略图已存在且是最新的，直接返回
    if thumbnail_path.exists():
        return thumbnail_path
    
    try:
        # 生成缩略图数据
        thumbnail_data = generate_thumbnail(image_path)
        
        # 保存到磁盘
        with open(thumbnail_path, 'wb') as f:
            f.write(thumbnail_data)
        
        logger.info(f"Created thumbnail: {thumbnail_path}")
        return thumbnail_path
        
    except Exception as e:
        logger.error(f"Failed to create thumbnail for {image_path}: {e}")
        raise

def get_or_create_thumbnail(image_path: Path, requested_filename: str = None) -> Path:
    """获取或创建缩略图"""
    thumbnail_path = get_thumbnail_path(image_path, requested_filename)
    
    # 检查缩略图是否存在且是最新的
    if thumbnail_path.exists():
        return thumbnail_path
    
    # 创建新的缩略图
    return create_and_save_thumbnail(image_path, requested_filename)

@router.get("/thumbnail/{filename}")
async def get_file_thumbnail(filename: str, db: Session = Depends(get_db)):
    """
    获取文件缩略图（持久化策略）
    """
    try:
        logger.info(f"Requesting thumbnail for: {filename}")
        
        file_path = get_file_path(filename, db)
        logger.info(f"Found file path: {file_path}")
        
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
        
        # 检查是否是支持的图片格式
        file_extension = file_path.suffix.lower()
        if file_extension not in SUPPORTED_IMAGE_FORMATS:
            logger.error(f"Unsupported image format: {file_extension}")
            raise HTTPException(status_code=400, detail=f"不支持的图片格式: {file_extension}")
        
        # 获取或创建缩略图，传入请求的文件名以确保缓存一致性
        thumbnail_path = get_or_create_thumbnail(file_path, filename)
        logger.info(f"Generated thumbnail path: {thumbnail_path}")
        
        if not thumbnail_path or not thumbnail_path.exists():
            logger.error(f"Failed to create thumbnail: {thumbnail_path}")
            raise HTTPException(status_code=500, detail="缩略图生成失败")
        
        # 返回缩略图文件
        return FileResponse(
            path=str(thumbnail_path),
            media_type="image/jpeg",
            filename=f"thumbnail_{filename}",
            headers={
                "Cache-Control": "public, max-age=86400",  # 缓存24小时
                "ETag": f'"{thumbnail_path.stat().st_mtime}"'  # 使用修改时间作为ETag
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thumbnail for {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"获取缩略图失败: {str(e)}")

@router.get("/{filename}")
async def get_file(filename: str, db: Session = Depends(get_db)):
    """
    获取原始文件（用于预览和下载）
    """
    try:
        logger.info(f"Requesting file: {filename}")
        file_path = get_file_path(filename, db)
        logger.info(f"Found file path: {file_path}")
        
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
        
        # 判断文件类型
        file_extension = file_path.suffix.lower()
        
        # 根据文件类型设置media_type
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.json': 'application/json',
        }
        
        media_type = media_type_map.get(file_extension, 'application/octet-stream')
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename,
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Disposition": f'inline; filename="{filename}"'  # inline表示浏览器内预览
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")

@router.get("/raw/{filename}")
async def get_raw_file(filename: str, db: Session = Depends(get_db)):
    """
    获取原始文件（兼容旧接口）
    """
    return await get_file(filename, db)

# 公共函数，供其他模块调用
def pregenerate_thumbnail_if_image(file_path: Path) -> bool:
    """
    如果是图片文件，预生成缩略图
    返回是否成功生成缩略图
    """
    try:
        if not file_path.exists():
            return False
            
        file_extension = file_path.suffix.lower()
        if file_extension not in SUPPORTED_IMAGE_FORMATS:
            return False
        
        # 预生成缩略图
        thumbnail_path = create_and_save_thumbnail(file_path, file_path.name)
        logger.info(f"Pre-generated thumbnail for {file_path.name}: {thumbnail_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to pre-generate thumbnail for {file_path}: {e}")
        return False

@router.post("/pregenerate-thumbnail")
async def pregenerate_thumbnail(filename: str, db: Session = Depends(get_db)):
    """
    手动预生成缩略图（用于批量处理）
    """
    try:
        file_path = get_file_path(filename, db)
        logger.info(f"Attempting to pregenerate thumbnail for {filename}, found path: {file_path}")
        
        if not file_path.exists():
            return {"status": "error", "message": f"文件不存在: {filename} (searched path: {file_path})"}
        
        success = pregenerate_thumbnail_if_image(file_path)
        
        if success:
            return {"status": "success", "message": f"缩略图已生成: {filename}"}
        else:
            return {"status": "skipped", "message": f"跳过非图片文件: {filename} (extension: {file_path.suffix})"}
            
    except Exception as e:
        logger.error(f"Error pre-generating thumbnail for {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"预生成缩略图失败: {str(e)}")

@router.post("/batch-pregenerate-thumbnails")
async def batch_pregenerate_thumbnails(db: Session = Depends(get_db)):
    """
    批量预生成所有图片的缩略图
    """
    try:
        # 查询所有图片类型的内容
        image_contents = db.query(Content).filter(Content.modality == 'image').all()
        
        results = []
        success_count = 0
        error_count = 0
        
        for content in image_contents:
            filename = content.title
            try:
                file_path = get_file_path(filename, db)
                
                if file_path.exists():
                    success = pregenerate_thumbnail_if_image(file_path)
                    if success:
                        results.append({"filename": filename, "status": "success"})
                        success_count += 1
                    else:
                        results.append({"filename": filename, "status": "skipped", "reason": "not_image"})
                else:
                    results.append({"filename": filename, "status": "error", "reason": "file_not_found"})
                    error_count += 1
                    
            except Exception as e:
                results.append({"filename": filename, "status": "error", "reason": str(e)})
                error_count += 1
        
        return {
            "total_processed": len(image_contents),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch pregenerate thumbnails: {e}")
        raise HTTPException(status_code=500, detail=f"批量生成缩略图失败: {str(e)}")

@router.delete("/thumbnails/cleanup")
async def cleanup_old_thumbnails(max_age_days: int = 7):
    """
    清理旧的缩略图文件
    """
    try:
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        cleaned_count = 0
        
        for thumbnail_file in THUMBNAIL_DIR.glob("*.jpg"):
            try:
                file_age = current_time - thumbnail_file.stat().st_mtime
                if file_age > max_age_seconds:
                    thumbnail_file.unlink()
                    cleaned_count += 1
                    logger.info(f"Cleaned old thumbnail: {thumbnail_file}")
            except Exception as e:
                logger.warning(f"Failed to clean thumbnail {thumbnail_file}: {e}")
        
        return {
            "status": "success", 
            "cleaned_count": cleaned_count,
            "message": f"清理了 {cleaned_count} 个超过 {max_age_days} 天的缩略图"
        }
        
    except Exception as e:
        logger.error(f"Error during thumbnail cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"清理缩略图失败: {str(e)}")

@router.get("/thumbnails/stats")
async def get_thumbnail_stats():
    """
    获取缩略图统计信息
    """
    try:
        thumbnail_files = list(THUMBNAIL_DIR.glob("*.jpg"))
        total_count = len(thumbnail_files)
        
        total_size = sum(f.stat().st_size for f in thumbnail_files if f.exists())
        total_size_mb = total_size / (1024 * 1024)
        
        return {
            "thumbnail_count": total_count,
            "total_size_mb": round(total_size_mb, 2),
            "storage_path": str(THUMBNAIL_DIR),
            "average_size_kb": round(total_size / total_count / 1024, 2) if total_count > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting thumbnail stats: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/debug/{filename}")
async def debug_file_path(filename: str, db: Session = Depends(get_db)):
    """
    调试文件路径查找过程
    """
    try:
        logger.info(f"Debug: Looking for file: {filename}")
        
        # 检查可能的存储位置
        possible_locations = [
            Path("/tmp/pkb_uploads") / filename,
            Path("/app/uploads") / filename,
            Path("/uploads") / filename,
            Path("/data/uploads") / filename,
            Path("/var/uploads") / filename,
        ]
        
        location_status = {}
        for location in possible_locations:
            location_status[str(location)] = {
                "exists": location.exists(),
                "is_file": location.is_file() if location.exists() else False,
                "size": location.stat().st_size if location.exists() and location.is_file() else None
            }
        
        # 检查数据库记录
        content = db.query(Content).filter(
            Content.source_uri == f"webui://{filename}"
        ).first()
        
        db_info = None
        if content:
            db_info = {
                "id": str(content.id),
                "title": content.title,
                "source_uri": content.source_uri,
                "modality": content.modality,
                "meta_file_path": content.meta.get('file_path') if content.meta else None,
                "created_at": content.created_at.isoformat() if content.created_at else None
            }
            
            # 检查meta中的文件路径
            if content.meta and content.meta.get('file_path'):
                meta_path = Path(content.meta['file_path'])
                db_info["meta_path_exists"] = meta_path.exists()
                db_info["meta_path_is_file"] = meta_path.is_file() if meta_path.exists() else False
        
        return {
            "filename": filename,
            "possible_locations": location_status,
            "database_record": db_info,
            "thumbnail_dir_exists": THUMBNAIL_DIR.exists(),
            "thumbnail_dir_path": str(THUMBNAIL_DIR)
        }
        
    except Exception as e:
        logger.error(f"Debug error for {filename}: {e}")
        return {"error": str(e)}

@router.get("/list-uploads")
async def list_uploaded_files():
    """
    列出所有上传目录中的文件
    """
    try:
        result = {}
        search_dirs = [
            Path("/tmp/pkb_uploads"), 
            Path("/app/uploads"), 
            Path("/uploads"), 
            Path("/data/uploads"), 
            Path("/var/uploads")
        ]
        
        for base_dir in search_dirs:
            dir_info = {
                "exists": base_dir.exists(),
                "files": []
            }
            
            if base_dir.exists():
                try:
                    all_files = list(base_dir.rglob("*"))
                    for file_path in all_files:
                        if file_path.is_file():
                            dir_info["files"].append({
                                "name": file_path.name,
                                "path": str(file_path),
                                "size": file_path.stat().st_size,
                                "modified": file_path.stat().st_mtime
                            })
                except Exception as e:
                    dir_info["error"] = str(e)
            
            result[str(base_dir)] = dir_info
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/list-database-files")
async def list_database_files(db: Session = Depends(get_db)):
    """
    列出数据库中的所有文件记录
    """
    try:
        contents = db.query(Content).filter(
            Content.source_uri.like("webui://%")
        ).limit(20).all()
        
        result = []
        for content in contents:
            file_info = {
                "id": str(content.id),
                "title": content.title,
                "source_uri": content.source_uri,
                "modality": content.modality,
                "created_at": content.created_at.isoformat() if content.created_at else None,
                "meta_file_path": content.meta.get('file_path') if content.meta else None,
                "meta_keys": list(content.meta.keys()) if content.meta else []
            }
            
            # 检查文件是否存在
            if content.meta and content.meta.get('file_path'):
                file_path = Path(content.meta['file_path'])
                file_info["file_exists"] = file_path.exists()
                file_info["file_size"] = file_path.stat().st_size if file_path.exists() else None
            
            result.append(file_info)
        
        return {
            "total_webui_files": len(result),
            "files": result
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.post("/migrate-storage")
async def migrate_file_storage(db: Session = Depends(get_db)):
    """
    迁移文件存储：将临时目录的文件路径更新为持久化目录
    注意：这不会移动实际文件，只更新数据库记录
    """
    try:
        # 查找所有WebUI上传的文件
        contents = db.query(Content).filter(
            Content.source_uri.like("webui://%")
        ).all()
        
        updated_count = 0
        for content in contents:
            if content.meta and content.meta.get('file_path'):
                old_path = content.meta['file_path']
                
                # 如果是临时目录路径，更新为持久化目录
                if '/tmp/pkb_uploads/' in old_path:
                    # 提取文件名
                    file_name = Path(old_path).name
                    new_path = f"/app/uploads/{file_name}"
                    
                    # 更新meta中的file_path
                    content.meta['file_path'] = new_path
                    updated_count += 1
        
        # 提交更改
        db.commit()
        
        return {
            "success": True,
            "message": f"Updated {updated_count} file records",
            "updated_count": updated_count
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@router.post("/reset-database")
async def reset_database(confirm: bool = False, db: Session = Depends(get_db)):
    """
    重置数据库：删除所有WebUI上传的文件记录
    警告：这会删除所有数据！
    """
    if not confirm:
        return {
            "error": "请添加 confirm=true 参数来确认删除操作",
            "warning": "这将删除所有WebUI上传的文件记录！"
        }
    
    try:
        # 统计要删除的记录
        webui_contents = db.query(Content).filter(
            Content.source_uri.like("webui://%")
        ).all()
        
        content_count = len(webui_contents)
        chunk_count = 0
        category_count = 0
        
        # 删除相关的chunks和分类关联
        for content in webui_contents:
            # 删除chunks
            chunks = db.query(Chunk).filter(Chunk.content_id == content.id).all()
            chunk_count += len(chunks)
            for chunk in chunks:
                db.delete(chunk)
            
            # 删除分类关联
            categories = db.query(ContentCategory).filter(ContentCategory.content_id == content.id).all()
            category_count += len(categories)
            for category in categories:
                db.delete(category)
            
            # 删除content
            db.delete(content)
        
        # 提交删除
        db.commit()
        
        return {
            "success": True,
            "message": "数据库重置完成",
            "deleted": {
                "contents": content_count,
                "chunks": chunk_count,
                "category_associations": category_count
            }
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

@router.post("/cleanup-storage")
async def cleanup_storage_directories():
    """
    清理存储目录：删除上传目录中的所有文件
    """
    try:
        cleanup_results = {}
        
        # 要清理的目录
        directories_to_clean = [
            Path("/tmp/pkb_uploads"),
            Path("/app/uploads"),
            Path("/tmp/pkb_thumbnails")  # 也清理缩略图
        ]
        
        for directory in directories_to_clean:
            result = {
                "exists": directory.exists(),
                "files_deleted": 0,
                "errors": []
            }
            
            if directory.exists():
                try:
                    # 删除目录中的所有文件
                    for file_path in directory.rglob("*"):
                        if file_path.is_file():
                            try:
                                file_path.unlink()
                                result["files_deleted"] += 1
                            except Exception as e:
                                result["errors"].append(f"Failed to delete {file_path}: {e}")
                    
                    # 可选：删除空目录
                    if result["files_deleted"] > 0 and not result["errors"]:
                        try:
                            directory.rmdir()
                        except:
                            pass  # 目录可能不为空或有权限问题，忽略
                            
                except Exception as e:
                    result["errors"].append(f"Failed to access directory: {e}")
            
            cleanup_results[str(directory)] = result
        
        return {
            "success": True,
            "message": "存储目录清理完成",
            "results": cleanup_results
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/check-upload-config")
async def check_upload_config():
    """
    检查当前的上传配置
    """
    try:
        # 检查各个可能的上传目录
        test_dirs = [
            Path("/app/uploads"),
            Path("/tmp/pkb_uploads"),
            Path("/data/uploads"),
            Path("/uploads")
        ]
        
        dir_status = {}
        for test_dir in test_dirs:
            dir_status[str(test_dir)] = {
                "exists": test_dir.exists(),
                "writable": test_dir.exists() and os.access(test_dir, os.W_OK),
                "files_count": len(list(test_dir.rglob("*"))) if test_dir.exists() else 0
            }
        
        return {
            "upload_directories": dir_status,
            "recommended_dir": "/app/uploads",
            "current_time": time.time(),
            "message": "Check if ingest.py changes were deployed"
        }
        
    except Exception as e:
        return {"error": str(e)}
