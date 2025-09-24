"""
自建合集管理 API
提供合集的创建、查询、更新、删除功能
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.db import SessionLocal
from app.models import Collection, Category, Content, ContentCategory, Chunk
from app.services.collection_matching_service import CollectionMatchingService

router = APIRouter()
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    auto_match: Optional[bool] = True  # 是否启用智能匹配，默认开启

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CollectionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    content_count: int
    created_at: str
    updated_at: str

@router.get("/", response_model=List[CollectionResponse])
def get_collections(db: Session = Depends(get_db)):
    """
    获取所有自建合集
    """
    try:
        # 查询所有非自动生成的合集（自建合集）
        collections = db.query(Collection).filter(
            Collection.auto_generated == False
        ).all()
        
        result = []
        invalid_collections = []  # 记录无效的合集
        
        for collection in collections:
            # 检查合集是否有有效的分类关联
            if not collection.category_id or not collection.category:
                logger.warning(f"Found collection without category: {collection.name} (ID: {collection.id})")
                invalid_collections.append(collection)
                # 不跳过，而是返回content_count=0的合集
                result.append(CollectionResponse(
                    id=str(collection.id),
                    name=collection.name,
                    description=collection.description,
                    content_count=0,  # 没有category_id的合集内容为0
                    created_at=collection.created_at.isoformat() if collection.created_at else "",
                    updated_at=collection.updated_at.isoformat() if collection.updated_at else ""
                ))
                continue
            
            # 计算合集中的文档数量，只统计有chunks的内容
            content_count = db.query(func.count(func.distinct(Content.id))).select_from(
                ContentCategory
            ).join(
                Content, ContentCategory.content_id == Content.id
            ).join(
                Chunk, Content.id == Chunk.content_id
            ).filter(
                ContentCategory.category_id == collection.category_id
            ).scalar() or 0
            
            result.append(CollectionResponse(
                id=str(collection.id),
                name=collection.name,
                description=collection.description,
                content_count=content_count,
                created_at=collection.created_at.isoformat() if collection.created_at else "",
                updated_at=collection.updated_at.isoformat() if collection.updated_at else ""
            ))
        
        # 清理无效的合集
        if invalid_collections:
            logger.info(f"Cleaning up {len(invalid_collections)} invalid collections")
            for invalid_collection in invalid_collections:
                db.delete(invalid_collection)
            db.commit()
        
        # 按创建时间倒序排序
        result.sort(key=lambda x: x.created_at, reverse=True)
        
        return result
        
    except Exception as e:
        logger.error(f"获取合集列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取合集列表失败: {str(e)}")

@router.post("/", response_model=CollectionResponse)
def create_collection(collection_data: CollectionCreate, db: Session = Depends(get_db)):
    """
    创建新的自建合集，支持智能匹配
    """
    try:
        # 检查名称是否已存在
        existing = db.query(Collection).filter(
            Collection.name == collection_data.name,
            Collection.auto_generated == False
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="合集名称已存在")
        
        # 创建对应的分类（处理名称冲突）
        existing_category = db.query(Category).filter(Category.name == collection_data.name).first()
        
        if existing_category:
            # 如果已存在同名分类，检查是否为系统分类
            if existing_category.is_system:
                # 如果是系统分类，为用户合集创建一个带后缀的分类
                category_name = f"{collection_data.name}_用户合集"
                category = Category(
                    name=category_name,
                    description=collection_data.description or f"自建合集: {collection_data.name}",
                    is_system=False,
                    color="#1890ff"
                )
                db.add(category)
                db.flush()
                db.refresh(category)
            else:
                # 如果是用户分类，直接使用现有分类
                category = existing_category
        else:
            # 创建新分类
            category = Category(
                name=collection_data.name,
                description=collection_data.description or f"自建合集: {collection_data.name}",
                is_system=False,
                color="#1890ff"
            )
            db.add(category)
            db.flush()
            db.refresh(category)
        
        # 生成智能匹配规则
        query_rules = None
        if collection_data.auto_match:
            matching_service = CollectionMatchingService(db)
            query_rules = matching_service.generate_auto_match_rules(
                collection_data.name, 
                collection_data.description
            )
        
        # 创建合集
        collection = Collection(
            name=collection_data.name,
            description=collection_data.description,
            category_id=category.id,
            auto_generated=False,  # 标记为自建合集
            query_rules=query_rules  # 保存匹配规则
        )
        
        db.add(collection)
        db.commit()
        db.refresh(collection)
        
        # 如果启用智能匹配，扫描现有文档
        matched_count = 0
        if collection_data.auto_match and query_rules and query_rules.get("auto_match"):
            matching_service = CollectionMatchingService(db)
            matched_count = matching_service.match_existing_documents_to_collection(str(collection.id))
        
        logger.info(f"Created collection '{collection.name}' with {matched_count} matched documents")
        
        return CollectionResponse(
            id=str(collection.id),
            name=collection.name,
            description=collection.description,
            content_count=matched_count,  # 显示匹配的文档数
            created_at=collection.created_at.isoformat() if collection.created_at else "",
            updated_at=collection.updated_at.isoformat() if collection.updated_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建合集失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建合集失败: {str(e)}")

@router.post("/fix-missing-rules")
def fix_missing_rules(db: Session = Depends(get_db)):
    """
    修复缺失匹配规则的合集
    """
    try:
        from app.services.collection_matching_service import CollectionMatchingService
        
        # 查找没有匹配规则的用户合集
        collections_without_rules = db.query(Collection).filter(
            Collection.auto_generated == False,
            Collection.query_rules.is_(None)
        ).all()
        
        fixed_count = 0
        matching_service = CollectionMatchingService(db)
        
        for collection in collections_without_rules:
            # 生成匹配规则
            query_rules = matching_service.generate_auto_match_rules(
                collection.name,
                collection.description
            )
            
            if query_rules and query_rules.get("auto_match"):
                # 更新合集的匹配规则
                collection.query_rules = query_rules
                db.commit()
                
                # 匹配现有文档
                matched_count = matching_service.match_existing_documents_to_collection(str(collection.id))
                
                logger.info(f"Fixed collection '{collection.name}' with {matched_count} matched documents")
                fixed_count += 1
        
        return {
            "success": True,
            "message": f"Fixed {fixed_count} collections with missing rules",
            "fixed_collections": fixed_count
        }
        
    except Exception as e:
        logger.error(f"Error fixing missing rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fix missing rules: {str(e)}")

@router.put("/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: str, 
    collection_data: CollectionUpdate, 
    db: Session = Depends(get_db)
):
    """
    更新合集信息（重命名等）
    """
    try:
        # 转换UUID
        try:
            from uuid import UUID
            uuid_id = UUID(collection_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的合集ID格式")
        
        # 查找合集
        collection = db.query(Collection).filter(
            Collection.id == uuid_id,
            Collection.auto_generated == False  # 只能更新自建合集
        ).first()
        
        if not collection:
            raise HTTPException(status_code=404, detail="合集不存在或不是自建合集")
        
        # 如果要更新名称，检查是否重名
        if collection_data.name and collection_data.name != collection.name:
            existing = db.query(Collection).filter(
                Collection.name == collection_data.name,
                Collection.auto_generated == False,
                Collection.id != uuid_id
            ).first()
            
            if existing:
                raise HTTPException(status_code=400, detail="合集名称已存在")
            
            # 同时更新关联的分类名称
            if collection.category:
                collection.category.name = collection_data.name
        
        # 更新合集信息
        if collection_data.name:
            collection.name = collection_data.name
        if collection_data.description is not None:
            collection.description = collection_data.description
            if collection.category:
                collection.category.description = collection_data.description or f"自建合集: {collection.name}"
        
        db.commit()
        db.refresh(collection)
        
        # 计算文档数量
        content_count = 0
        if collection.category_id:
            content_count = db.query(func.count(ContentCategory.content_id)).filter(
                ContentCategory.category_id == collection.category_id
            ).scalar() or 0
        
        return CollectionResponse(
            id=str(collection.id),
            name=collection.name,
            description=collection.description,
            content_count=content_count,
            created_at=collection.created_at.isoformat() if collection.created_at else "",
            updated_at=collection.updated_at.isoformat() if collection.updated_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新合集失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新合集失败: {str(e)}")

@router.delete("/{collection_id}")
def delete_collection(collection_id: str, db: Session = Depends(get_db)):
    """
    删除自建合集
    """
    try:
        logger.info(f"Attempting to delete collection: {collection_id}")
        
        # 转换UUID
        try:
            from uuid import UUID
            uuid_id = UUID(collection_id)
            logger.info(f"UUID conversion successful: {uuid_id}")
        except ValueError:
            logger.error(f"Invalid UUID format: {collection_id}")
            raise HTTPException(status_code=400, detail="无效的合集ID格式")
        
        # 查找合集
        collection = db.query(Collection).filter(
            Collection.id == uuid_id,
            Collection.auto_generated == False  # 只能删除自建合集
        ).first()
        
        if not collection:
            logger.error(f"Collection not found or not custom: {uuid_id}")
            raise HTTPException(status_code=404, detail="合集不存在或不是自建合集")
        
        logger.info(f"Found collection to delete: {collection.name} (ID: {collection.id})")
        
        # 检查是否有文档关联
        if collection.category_id:
            content_count = db.query(func.count(ContentCategory.content_id)).filter(
                ContentCategory.category_id == collection.category_id
            ).scalar() or 0
            
            if content_count > 0:
                # 删除文档分类关联（文档本身保留，只是移除分类）
                db.query(ContentCategory).filter(
                    ContentCategory.category_id == collection.category_id
                ).delete()
            
            # 删除关联的分类
            if collection.category:
                db.delete(collection.category)
        
        # 删除合集
        db.delete(collection)
        db.commit()
        
        return {"status": "success", "message": "合集删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除合集失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除合集失败: {str(e)}")

@router.get("/{collection_id}/contents")
def get_collection_contents(collection_id: str, db: Session = Depends(get_db)):
    """
    获取合集中的文档列表
    """
    try:
        # 转换UUID
        try:
            from uuid import UUID
            uuid_id = UUID(collection_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的合集ID格式")
        
        # 查找合集
        collection = db.query(Collection).filter(Collection.id == uuid_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="合集不存在")
        
        if not collection.category_id:
            return {"collection": collection.name, "contents": []}
        
        # 查询合集中的文档
        contents = db.query(Content).join(ContentCategory).filter(
            ContentCategory.category_id == collection.category_id
        ).all()
        
        result = []
        for content in contents:
            result.append({
                "id": str(content.id),
                "title": content.title,
                "modality": content.modality,
                "source_uri": content.source_uri,
                "created_at": content.created_at.isoformat() if content.created_at else None
            })
        
        return {
            "collection": collection.name,
            "contents": result,
            "total": len(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取合集内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取合集内容失败: {str(e)}")

@router.post("/fix-orphaned-collections")
def fix_orphaned_collections(db: Session = Depends(get_db)):
    """修复没有category_id的孤立合集"""
    try:
        from app.services.collection_matching_service import CollectionMatchingService
        
        # 查找没有category_id的合集
        orphaned_collections = db.query(Collection).filter(
            Collection.auto_generated == False,
            Collection.category_id.is_(None)
        ).all()
        
        if not orphaned_collections:
            return {
                "success": True,
                "message": "No orphaned collections found",
                "fixed_collections": []
            }
        
        fixed_collections = []
        matching_service = CollectionMatchingService(db)
        
        for collection in orphaned_collections:
            try:
                logger.info(f"Fixing orphaned collection: {collection.name}")
                
                # 检查是否已存在同名分类
                existing_category = db.query(Category).filter(Category.name == collection.name).first()
                
                if existing_category:
                    if existing_category.is_system:
                        # 如果是系统分类，创建带后缀的新分类
                        category_name = f"{collection.name}_用户合集"
                        # 检查带后缀的名称是否也冲突
                        suffix_category = db.query(Category).filter(Category.name == category_name).first()
                        if suffix_category:
                            collection.category_id = suffix_category.id
                        else:
                            new_category = Category(
                                name=category_name,
                                description=collection.description or f"自建合集: {collection.name}",
                                is_system=False,
                                color="#1890ff"
                            )
                            db.add(new_category)
                            db.flush()
                            collection.category_id = new_category.id
                    else:
                        # 如果是用户分类，直接关联
                        collection.category_id = existing_category.id
                else:
                    # 创建新分类
                    new_category = Category(
                        name=collection.name,
                        description=collection.description or f"自建合集: {collection.name}",
                        is_system=False,
                        color="#1890ff"
                    )
                    db.add(new_category)
                    db.flush()
                    collection.category_id = new_category.id
                
                # 生成匹配规则（如果还没有）
                if not collection.query_rules:
                    query_rules = matching_service.generate_auto_match_rules(
                        collection.name,
                        collection.description
                    )
                    collection.query_rules = query_rules
                
                fixed_collections.append({
                    "collection_id": str(collection.id),
                    "collection_name": collection.name,
                    "category_id": str(collection.category_id),
                    "has_rules": bool(collection.query_rules)
                })
                
            except Exception as e:
                logger.error(f"Failed to fix collection {collection.name}: {e}")
                continue
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Fixed {len(fixed_collections)} orphaned collections",
            "fixed_collections": fixed_collections
        }
        
    except Exception as e:
        logger.error(f"修复孤立合集失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"修复孤立合集失败: {str(e)}")

@router.post("/match-all-documents")
def match_all_documents_to_collections(db: Session = Depends(get_db)):
    """手动触发所有文档匹配到用户合集"""
    try:
        from app.services.collection_matching_service import CollectionMatchingService
        from sqlalchemy import text
        
        # 获取所有包含会议相关词汇的文档
        meeting_contents = db.execute(text("""
            SELECT DISTINCT c.id, c.title 
            FROM contents c 
            WHERE c.title ILIKE '%会议纪要%' 
               OR c.title ILIKE '%会议%'
               OR c.title ILIKE '%例会%'
               OR c.text ILIKE '%会议%'
            LIMIT 50
        """)).fetchall()
        
        if not meeting_contents:
            return {
                "success": True,
                "message": "No meeting-related documents found",
                "matched_documents": []
            }
        
        matching_service = CollectionMatchingService(db)
        matched_documents = []
        total_matches = 0
        
        for content_row in meeting_contents:
            content_id = str(content_row[0])
            content_title = content_row[1]
            
            try:
                matched_collections = matching_service.match_document_to_collections(content_id)
                if matched_collections:
                    total_matches += 1
                    matched_documents.append({
                        "content_id": content_id,
                        "content_title": content_title,
                        "matched_collections": matched_collections,
                        "collection_count": len(matched_collections)
                    })
                    logger.info(f"✅ Document '{content_title}' matched to {len(matched_collections)} collections")
                else:
                    matched_documents.append({
                        "content_id": content_id,
                        "content_title": content_title,
                        "matched_collections": [],
                        "collection_count": 0
                    })
                    logger.info(f"❌ Document '{content_title}' matched to no collections")
            except Exception as e:
                logger.error(f"Error matching document {content_title}: {e}")
                matched_documents.append({
                    "content_id": content_id,
                    "content_title": content_title,
                    "error": str(e),
                    "matched_collections": [],
                    "collection_count": 0
                })
        
        return {
            "success": True,
            "message": f"Processed {len(meeting_contents)} documents, {total_matches} matched successfully",
            "total_processed": len(meeting_contents),
            "total_matched": total_matches,
            "matched_documents": matched_documents[:10]  # 只返回前10个结果
        }
        
    except Exception as e:
        logger.error(f"批量匹配文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量匹配文档失败: {str(e)}")

@router.get("/debug/duplicates")
def debug_duplicate_collections(db: Session = Depends(get_db)):
    """调试重复合集问题"""
    try:
        from sqlalchemy import func
        
        # 查找重复名称的合集
        duplicates = db.query(
            Collection.name,
            func.count(Collection.id).label('count')
        ).filter(
            Collection.auto_generated == False
        ).group_by(Collection.name).having(
            func.count(Collection.id) > 1
        ).all()
        
        duplicate_details = []
        for name, count in duplicates:
            collections = db.query(Collection).filter(
                Collection.name == name,
                Collection.auto_generated == False
            ).all()
            
            duplicate_details.append({
                "name": name,
                "count": count,
                "collections": [
                    {
                        "id": str(c.id),
                        "category_id": str(c.category_id) if c.category_id else None,
                        "category_name": c.category.name if c.category else None,
                        "created_at": c.created_at.isoformat() if c.created_at else None
                    }
                    for c in collections
                ]
            })
        
        return {
            "duplicate_collections": duplicate_details,
            "total_duplicates": len(duplicate_details)
        }
        
    except Exception as e:
        logger.error(f"调试重复合集失败: {e}")
        raise HTTPException(status_code=500, detail=f"调试失败: {str(e)}")

@router.post("/cleanup/duplicates")
def cleanup_duplicate_collections(db: Session = Depends(get_db)):
    """清理重复的合集，保留最新创建的"""
    try:
        from sqlalchemy import func
        
        # 查找重复名称的合集
        duplicates = db.query(
            Collection.name,
            func.count(Collection.id).label('count')
        ).filter(
            Collection.auto_generated == False
        ).group_by(Collection.name).having(
            func.count(Collection.id) > 1
        ).all()
        
        cleaned_up = []
        
        for name, count in duplicates:
            # 获取所有同名合集，按创建时间排序
            collections = db.query(Collection).filter(
                Collection.name == name,
                Collection.auto_generated == False
            ).order_by(Collection.created_at.desc()).all()
            
            # 保留最新的，删除其他的
            keep_collection = collections[0]  # 最新的
            delete_collections = collections[1:]  # 其他的
            
            for collection in delete_collections:
                logger.info(f"Deleting duplicate collection: {collection.name} (ID: {collection.id})")
                
                # 先删除相关的ContentCategory记录
                if collection.category_id:
                    db.query(ContentCategory).filter(
                        ContentCategory.category_id == collection.category_id
                    ).delete()
                    
                    # 删除对应的Category
                    db.query(Category).filter(Category.id == collection.category_id).delete()
                
                # 删除Collection
                db.delete(collection)
            
            cleaned_up.append({
                "name": name,
                "kept_id": str(keep_collection.id),
                "deleted_count": len(delete_collections)
            })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Cleaned up {len(cleaned_up)} duplicate collection groups",
            "cleaned_up": cleaned_up
        }
        
    except Exception as e:
        logger.error(f"清理重复合集失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@router.post("/cleanup/invalid-categories")
def cleanup_invalid_categories(db: Session = Depends(get_db)):
    """清理不应该存在的用户分类，这些分类不应该出现在系统分类中"""
    try:
        # 查找所有非系统分类，但名称与系统分类重复的分类
        system_category_names = ["职场商务", "生活点滴", "学习成长", "科技前沿"]
        
        invalid_categories = db.query(Category).filter(
            Category.name.in_(system_category_names),
            Category.is_system != True  # 包括NULL和False
        ).all()
        
        cleaned_categories = []
        
        for category in invalid_categories:
            logger.info(f"Found invalid category: {category.name} (is_system: {category.is_system})")
            
            # 检查是否有合集使用这个分类
            collections_using = db.query(Collection).filter(
                Collection.category_id == category.id
            ).all()
            
            if collections_using:
                # 如果有合集使用，需要重新关联到正确的系统分类
                correct_category = db.query(Category).filter(
                    Category.name == category.name,
                    Category.is_system == True
                ).first()
                
                if correct_category:
                    for collection in collections_using:
                        logger.info(f"Reassigning collection {collection.name} to correct category")
                        collection.category_id = correct_category.id
                    
                    # 更新ContentCategory记录
                    db.query(ContentCategory).filter(
                        ContentCategory.category_id == category.id
                    ).update({ContentCategory.category_id: correct_category.id})
            
            # 删除无效的分类
            db.delete(category)
            cleaned_categories.append({
                "name": category.name,
                "id": str(category.id),
                "is_system": category.is_system,
                "collections_reassigned": len(collections_using)
            })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Cleaned up {len(cleaned_categories)} invalid categories",
            "cleaned_categories": cleaned_categories
        }
        
    except Exception as e:
        logger.error(f"清理无效分类失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@router.get("/debug/category-content-mismatch")
def debug_category_content_mismatch(db: Session = Depends(get_db)):
    """调试分类内容统计不匹配的问题"""
    try:
        from sqlalchemy import func, text
        
        # 获取所有系统分类
        system_categories = db.query(Category).filter(Category.is_system == True).all()
        
        debug_info = []
        
        for category in system_categories:
            # 统计方法1：所有有ContentCategory关联的Content
            total_content = db.query(func.count(Content.id)).select_from(
                ContentCategory
            ).join(
                Content, ContentCategory.content_id == Content.id
            ).filter(
                ContentCategory.category_id == category.id
            ).scalar() or 0
            
            # 统计方法2：有ContentCategory关联且有Chunk的Content
            content_with_chunks = db.query(func.count(func.distinct(Content.id))).select_from(
                ContentCategory
            ).join(
                Content, ContentCategory.content_id == Content.id
            ).join(
                Chunk, Content.id == Chunk.content_id
            ).filter(
                ContentCategory.category_id == category.id
            ).scalar() or 0
            
            # 查找没有Chunk的Content
            orphan_content = db.query(Content).join(
                ContentCategory, Content.id == ContentCategory.content_id
            ).outerjoin(
                Chunk, Content.id == Chunk.content_id
            ).filter(
                ContentCategory.category_id == category.id,
                Chunk.id.is_(None)
            ).all()
            
            debug_info.append({
                "category_name": category.name,
                "category_id": str(category.id),
                "total_content": total_content,
                "content_with_chunks": content_with_chunks,
                "orphan_content_count": len(orphan_content),
                "orphan_content": [
                    {
                        "id": str(content.id),
                        "title": content.title,
                        "source_uri": content.source_uri,
                        "created_at": content.created_at.isoformat() if content.created_at else None
                    }
                    for content in orphan_content
                ]
            })
        
        return {
            "debug_info": debug_info
        }
        
    except Exception as e:
        logger.error(f"调试分类内容不匹配失败: {e}")
        raise HTTPException(status_code=500, detail=f"调试失败: {str(e)}")

@router.post("/cleanup/orphan-content")
def cleanup_orphan_content(db: Session = Depends(get_db)):
    """清理没有Chunk的孤儿Content记录"""
    try:
        # 查找所有没有Chunk的Content记录
        orphan_content = db.query(Content).outerjoin(
            Chunk, Content.id == Chunk.content_id
        ).filter(
            Chunk.id.is_(None)
        ).all()
        
        cleaned_content = []
        
        for content in orphan_content:
            logger.info(f"Cleaning orphan content: {content.title} (ID: {content.id})")
            
            # 删除相关的ContentCategory记录
            db.query(ContentCategory).filter(
                ContentCategory.content_id == content.id
            ).delete()
            
            # 删除Content记录
            db.delete(content)
            
            cleaned_content.append({
                "id": str(content.id),
                "title": content.title,
                "source_uri": content.source_uri,
                "created_at": content.created_at.isoformat() if content.created_at else None
            })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Cleaned up {len(cleaned_content)} orphan content records",
            "cleaned_content": cleaned_content
        }
        
    except Exception as e:
        logger.error(f"清理孤儿内容失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@router.post("/fix-collection-data")
def fix_collection_data(db: Session = Depends(get_db)):
    """修复合集数据不一致问题"""
    try:
        from app.services.collection_matching_service import CollectionMatchingService
        
        # 查找所有用户合集
        all_collections = db.query(Collection).all()
        
        fixed_collections = []
        matching_service = CollectionMatchingService(db)
        
        for collection in all_collections:
            fixed = False
            
            # 修复auto_generated字段
            if collection.auto_generated is None:
                # 根据名称判断是否为系统合集
                system_names = ["职场商务", "生活点滴", "学习成长", "科技前沿"]
                collection.auto_generated = collection.name in system_names
                fixed = True
                logger.info(f"Fixed auto_generated for {collection.name}: {collection.auto_generated}")
            
            # 为用户合集生成匹配规则
            if not collection.auto_generated and collection.query_rules is None:
                query_rules = matching_service.generate_auto_match_rules(
                    collection.name,
                    collection.description
                )
                if query_rules:
                    collection.query_rules = query_rules
                    fixed = True
                    logger.info(f"Generated rules for collection: {collection.name}")
            
            if fixed:
                fixed_collections.append({
                    "id": str(collection.id),
                    "name": collection.name,
                    "auto_generated": collection.auto_generated,
                    "has_rules": bool(collection.query_rules)
                })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Fixed {len(fixed_collections)} collections",
            "fixed_collections": fixed_collections
        }
        
    except Exception as e:
        logger.error(f"修复合集数据失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"修复合集数据失败: {str(e)}")
