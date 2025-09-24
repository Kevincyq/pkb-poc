#!/usr/bin/env python3
"""
清理重复文档脚本
保留每个 source_uri 的最早记录，删除重复的记录
"""

import os
import sys
sys.path.append('/app')

from app.db import SessionLocal
from app.models import Content, Chunk
from sqlalchemy import func
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_duplicate_documents():
    """清理重复文档，保留最早的记录"""
    db = SessionLocal()
    try:
        # 1. 找出所有重复的 source_uri
        duplicates = db.query(
            Content.source_uri,
            func.count(Content.id).label('count'),
            func.min(Content.created_at).label('earliest_date')
        ).group_by(Content.source_uri).having(func.count(Content.id) > 1).all()
        
        logger.info(f"发现 {len(duplicates)} 个重复的文件")
        
        total_deleted = 0
        
        for source_uri, count, earliest_date in duplicates:
            logger.info(f"处理重复文件: {source_uri} ({count} 个副本)")
            
            # 获取该 source_uri 的所有记录，按创建时间排序
            all_records = db.query(Content).filter(
                Content.source_uri == source_uri
            ).order_by(Content.created_at).all()
            
            # 保留第一个（最早的），删除其他的
            records_to_delete = all_records[1:]  # 跳过第一个
            
            for record in records_to_delete:
                logger.info(f"  删除重复记录: {record.id} (创建于 {record.created_at})")
                
                # 先删除相关的 chunks
                chunks_deleted = db.query(Chunk).filter(
                    Chunk.content_id == record.id
                ).delete()
                logger.info(f"    删除了 {chunks_deleted} 个相关文本块")
                
                # 删除 content 记录
                db.delete(record)
                total_deleted += 1
            
            db.commit()
        
        logger.info(f"清理完成！总共删除了 {total_deleted} 个重复文档")
        
        # 显示清理后的统计
        remaining_docs = db.query(func.count(Content.id)).scalar()
        remaining_chunks = db.query(func.count(Chunk.id)).scalar()
        
        logger.info(f"剩余文档: {remaining_docs} 个")
        logger.info(f"剩余文本块: {remaining_chunks} 个")
        
        return {
            "deleted_documents": total_deleted,
            "remaining_documents": remaining_docs,
            "remaining_chunks": remaining_chunks
        }
        
    except Exception as e:
        logger.error(f"清理过程中出错: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("开始清理重复文档...")
    result = clean_duplicate_documents()
    print(f"清理结果: {result}")
