#!/usr/bin/env python3
"""
数据库重置脚本
删除所有表并重新创建
"""
import os
import sys
import logging
from sqlalchemy import text
from app.db import SessionLocal, engine, Base
from app.models import Content, Chunk, QAHistory, AgentTask, MCPTool, OpsLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """重置数据库：删除所有表并重新创建"""
    try:
        logger.info("🔄 Starting database reset...")
        
        # 创建数据库连接
        db = SessionLocal()
        
        try:
            # 1. 删除所有表（按依赖关系逆序）
            logger.info("📋 Dropping all tables...")
            
            # 删除表的顺序很重要，先删除有外键的表
            tables_to_drop = [
                'qa_history',
                'agent_tasks', 
                'mcp_tools',
                'chunks',      # 有外键到 contents
                'contents',
                'ops_log'
            ]
            
            for table_name in tables_to_drop:
                try:
                    db.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    logger.info(f"  ✅ Dropped table: {table_name}")
                except Exception as e:
                    logger.warning(f"  ⚠️ Failed to drop {table_name}: {e}")
            
            db.commit()
            logger.info("🗑️ All tables dropped successfully")
            
        finally:
            db.close()
        
        # 2. 重新创建所有表
        logger.info("🏗️ Creating all tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created successfully")
        
        # 3. 验证表创建
        db = SessionLocal()
        try:
            # 检查表是否存在
            result = db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)).fetchall()
            
            tables = [row[0] for row in result]
            logger.info(f"📋 Created tables: {', '.join(tables)}")
            
            # 检查 pgvector 扩展
            try:
                db.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
                logger.info("✅ pgvector extension is available")
            except Exception as e:
                logger.warning(f"⚠️ pgvector extension check failed: {e}")
            
        finally:
            db.close()
        
        logger.info("🎉 Database reset completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}")
        return False

def verify_database():
    """验证数据库状态"""
    try:
        db = SessionLocal()
        try:
            # 测试基本操作
            content_count = db.query(Content).count()
            chunk_count = db.query(Chunk).count()
            
            logger.info(f"📊 Database status:")
            logger.info(f"  - Contents: {content_count}")
            logger.info(f"  - Chunks: {chunk_count}")
            
            return True
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Database verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 PKB Database Reset Script")
    print("=" * 50)
    
    # 确认操作
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        confirmed = True
    else:
        response = input("⚠️ This will DELETE ALL DATA in the database. Continue? (yes/no): ")
        confirmed = response.lower() in ['yes', 'y']
    
    if not confirmed:
        print("❌ Operation cancelled")
        sys.exit(1)
    
    # 执行重置
    success = reset_database()
    
    if success:
        # 验证重置结果
        if verify_database():
            print("✅ Database reset and verification completed!")
            sys.exit(0)
        else:
            print("⚠️ Database reset completed but verification failed")
            sys.exit(1)
    else:
        print("❌ Database reset failed!")
        sys.exit(1)
