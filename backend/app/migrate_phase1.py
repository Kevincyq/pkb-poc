#!/usr/bin/env python3
"""
数据库迁移脚本 - 第一阶段
为现有数据库添加新的字段和表，不删除现有数据
"""
import os
import sys
import logging
from sqlalchemy import text, inspect
from app.db import SessionLocal, engine, Base
from app.models import Content, Chunk, QAHistory, AgentTask, MCPTool, OpsLog
from app.models import Category, ContentCategory, Collection, Tag, ContentTag, Signals

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_column_exists(db, table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return any(col['name'] == column_name for col in columns)
    except:
        return False

def check_table_exists(db, table_name: str) -> bool:
    """检查表是否存在"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return table_name in tables
    except:
        return False

def migrate_content_categories_table(db):
    """迁移 content_categories 表，添加新字段"""
    logger.info("🔄 Migrating content_categories table...")
    
    # 检查并添加 role 字段
    if not check_column_exists(db, 'content_categories', 'role'):
        try:
            db.execute(text("""
                ALTER TABLE content_categories 
                ADD COLUMN role VARCHAR DEFAULT 'primary_system'
            """))
            logger.info("  ✅ Added 'role' column to content_categories")
        except Exception as e:
            logger.error(f"  ❌ Failed to add 'role' column: {e}")
            raise
    else:
        logger.info("  ✅ 'role' column already exists")
    
    # 检查并添加 source 字段
    if not check_column_exists(db, 'content_categories', 'source'):
        try:
            db.execute(text("""
                ALTER TABLE content_categories 
                ADD COLUMN source VARCHAR DEFAULT 'ml'
            """))
            logger.info("  ✅ Added 'source' column to content_categories")
        except Exception as e:
            logger.error(f"  ❌ Failed to add 'source' column: {e}")
            raise
    else:
        logger.info("  ✅ 'source' column already exists")

def create_new_tables(db):
    """创建新表：tags, content_tags, signals"""
    logger.info("🔄 Creating new tables...")
    
    # 检查并创建 tags 表
    if not check_table_exists(db, 'tags'):
        try:
            db.execute(text("""
                CREATE TABLE tags (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR NOT NULL UNIQUE,
                    description TEXT,
                    tag_type VARCHAR DEFAULT 'auto',
                    parent_id UUID REFERENCES tags(id),
                    usage_count INTEGER DEFAULT 0,
                    embedding vector(1536),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            logger.info("  ✅ Created 'tags' table")
        except Exception as e:
            logger.error(f"  ❌ Failed to create 'tags' table: {e}")
            raise
    else:
        logger.info("  ✅ 'tags' table already exists")
    
    # 检查并创建 content_tags 表
    if not check_table_exists(db, 'content_tags'):
        try:
            db.execute(text("""
                CREATE TABLE content_tags (
                    content_id UUID REFERENCES contents(id),
                    tag_id UUID REFERENCES tags(id),
                    confidence FLOAT DEFAULT 1.0,
                    source VARCHAR DEFAULT 'auto',
                    created_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (content_id, tag_id)
                )
            """))
            logger.info("  ✅ Created 'content_tags' table")
        except Exception as e:
            logger.error(f"  ❌ Failed to create 'content_tags' table: {e}")
            raise
    else:
        logger.info("  ✅ 'content_tags' table already exists")
    
    # 检查并创建 signals 表
    if not check_table_exists(db, 'signals'):
        try:
            db.execute(text("""
                CREATE TABLE signals (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    content_id UUID REFERENCES contents(id) NOT NULL,
                    signal_type VARCHAR NOT NULL,
                    payload JSON NOT NULL,
                    confidence FLOAT,
                    model_version VARCHAR,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            logger.info("  ✅ Created 'signals' table")
        except Exception as e:
            logger.error(f"  ❌ Failed to create 'signals' table: {e}")
            raise
    else:
        logger.info("  ✅ 'signals' table already exists")

def update_existing_data(db):
    """更新现有数据，设置默认的 role 和 source 值"""
    logger.info("🔄 Updating existing data...")
    
    try:
        # 为现有的 content_categories 记录设置默认值
        result = db.execute(text("""
            UPDATE content_categories 
            SET role = CASE 
                WHEN reasoning LIKE '快速分类:%' THEN 'primary_system'
                WHEN reasoning LIKE '%自动匹配到合集:%' THEN 'user_rule'
                ELSE 'primary_system'
            END,
            source = CASE 
                WHEN reasoning LIKE '快速分类:%' THEN 'heuristic'
                WHEN reasoning LIKE '%自动匹配到合集:%' THEN 'rule'
                ELSE 'ml'
            END
            WHERE role IS NULL OR source IS NULL
        """))
        
        updated_count = result.rowcount
        logger.info(f"  ✅ Updated {updated_count} existing classification records")
        
    except Exception as e:
        logger.error(f"  ❌ Failed to update existing data: {e}")
        raise

def verify_migration(db):
    """验证迁移结果"""
    logger.info("🔄 Verifying migration...")
    
    try:
        # 检查表和字段
        inspector = inspect(engine)
        
        # 检查 content_categories 表的新字段
        cc_columns = inspector.get_columns('content_categories')
        cc_column_names = [col['name'] for col in cc_columns]
        
        required_cc_columns = ['role', 'source']
        for col in required_cc_columns:
            if col in cc_column_names:
                logger.info(f"  ✅ content_categories.{col} exists")
            else:
                logger.error(f"  ❌ content_categories.{col} missing")
                return False
        
        # 检查新表
        tables = inspector.get_table_names()
        required_tables = ['tags', 'content_tags', 'signals']
        for table in required_tables:
            if table in tables:
                logger.info(f"  ✅ {table} table exists")
            else:
                logger.error(f"  ❌ {table} table missing")
                return False
        
        # 检查数据
        cc_count = db.execute(text("SELECT COUNT(*) FROM content_categories")).scalar()
        logger.info(f"  ✅ content_categories records: {cc_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Verification failed: {e}")
        return False

def run_migration():
    """执行完整迁移"""
    try:
        logger.info("🚀 Starting Phase 1 database migration...")
        
        db = SessionLocal()
        try:
            # 确保 pgvector 扩展存在
            try:
                db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("✅ pgvector extension ensured")
            except Exception as e:
                logger.warning(f"⚠️ pgvector extension issue: {e}")
            
            # 步骤1：迁移现有表
            migrate_content_categories_table(db)
            
            # 步骤2：创建新表
            create_new_tables(db)
            
            # 步骤3：更新现有数据
            update_existing_data(db)
            
            # 提交所有更改
            db.commit()
            logger.info("✅ All changes committed")
            
            # 步骤4：验证迁移
            if verify_migration(db):
                logger.info("🎉 Phase 1 migration completed successfully!")
                return True
            else:
                logger.error("❌ Migration verification failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            db.rollback()
            return False
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Critical migration error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PKB Phase 1 Database Migration")
    print("=" * 50)
    print("This will add new fields and tables without deleting existing data.")
    print()
    
    # 确认操作
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        confirmed = True
    else:
        response = input("Continue with migration? (yes/no): ")
        confirmed = response.lower() in ['yes', 'y']
    
    if not confirmed:
        print("❌ Migration cancelled")
        sys.exit(1)
    
    # 执行迁移
    success = run_migration()
    
    if success:
        print("✅ Phase 1 migration completed successfully!")
        print("You can now proceed with implementing the search and tag features.")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)
