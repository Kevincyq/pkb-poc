#!/usr/bin/env python3
"""
调试Content记录创建问题
"""

import sys
import os
sys.path.append('/app')

from app.db import SessionLocal
from app.models import Content
from sqlalchemy import text
import uuid

def test_content_creation():
    """测试Content记录的创建和查询"""
    
    db = SessionLocal()
    
    try:
        print("🔍 Testing Content creation and retrieval...")
        
        # 1. 创建测试记录
        test_id = str(uuid.uuid4())
        print(f"Creating test content with ID: {test_id}")
        
        content = Content(
            id=test_id,
            title="测试文件.jpg",
            text="测试内容",
            meta={
                "classification_status": "pending",
                "show_classification": False,
                "original_filename": "测试文件.jpg",
                "stored_filename": "测试文件.jpg"
            }
        )
        
        db.add(content)
        db.commit()
        db.refresh(content)
        
        print(f"✅ Content created successfully: {content.id}")
        print(f"   Title: {content.title}")
        print(f"   Meta: {content.meta}")
        print(f"   Created at: {content.created_at}")
        
        # 2. 立即查询记录
        found_content = db.query(Content).filter(Content.id == test_id).first()
        if found_content:
            print(f"✅ Content found immediately: {found_content.id}")
        else:
            print("❌ Content NOT found immediately after creation!")
        
        # 3. 在新会话中查询记录
        db.close()
        db2 = SessionLocal()
        
        found_content2 = db2.query(Content).filter(Content.id == test_id).first()
        if found_content2:
            print(f"✅ Content found in new session: {found_content2.id}")
        else:
            print("❌ Content NOT found in new session!")
        
        # 4. 检查最新的几条记录
        print("\n📋 Latest 3 content records:")
        latest_contents = db2.query(Content).order_by(Content.created_at.desc()).limit(3).all()
        for i, c in enumerate(latest_contents, 1):
            print(f"  {i}. {c.id} - {c.title} - {c.created_at}")
        
        # 5. 清理测试记录
        if found_content2:
            db2.delete(found_content2)
            db2.commit()
            print(f"🗑️ Test content deleted: {test_id}")
        
        db2.close()
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        db.close()

if __name__ == "__main__":
    test_content_creation()
