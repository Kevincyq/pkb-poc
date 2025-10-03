"""
测试配置文件
提供测试数据库和通用测试工具
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base, get_db
from app.models import Content, Category, Collection, ContentCategory
from datetime import datetime
import uuid


@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库会话"""
    # 使用内存SQLite数据库进行测试
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def sample_categories(test_db):
    """创建测试分类数据"""
    categories = [
        Category(
            id=str(uuid.uuid4()),
            name="职场商务",
            description="工作相关文档、商业计划、职业发展、会议记录、项目管理等",
            color="#2196F3",
            is_system=True
        ),
        Category(
            id=str(uuid.uuid4()),
            name="生活点滴",
            description="日常生活记录、个人感悟、生活经验、旅行日记、美食分享等",
            color="#4CAF50",
            is_system=True
        ),
        Category(
            id=str(uuid.uuid4()),
            name="学习成长",
            description="学习笔记、技能提升、知识总结、读书心得、课程资料等",
            color="#FF9800",
            is_system=True
        ),
        Category(
            id=str(uuid.uuid4()),
            name="科技前沿",
            description="技术文档、科技资讯、创新产品、编程代码、技术趋势等",
            color="#9C27B0",
            is_system=True
        )
    ]
    
    for category in categories:
        test_db.add(category)
    test_db.commit()
    
    return categories


@pytest.fixture(scope="function")
def sample_collections(test_db):
    """创建测试合集数据"""
    collections = [
        Collection(
            id=str(uuid.uuid4()),
            name="旅游",
            description="旅行相关的照片和文档",
            auto_generated=False
        ),
        Collection(
            id=str(uuid.uuid4()),
            name="会议纪要",
            description="各种会议记录和纪要",
            auto_generated=False
        ),
        Collection(
            id=str(uuid.uuid4()),
            name="技术文档",
            description="技术相关的文档和资料",
            auto_generated=False
        )
    ]
    
    for collection in collections:
        test_db.add(collection)
    test_db.commit()
    
    return collections


@pytest.fixture(scope="function")
def sample_content(test_db):
    """创建测试内容数据"""
    content_items = [
        Content(
            id=str(uuid.uuid4()),
            title="海边度假照片.jpg",
            text="【场景描述】\n美丽的海滩风景，蓝天白云，椰子树\n【活动推理】\n旅游度假\n【关键元素】\n海滩,度假,风景,旅行",
            source_uri="webui://海边度假照片.jpg",
            modality="image",
            meta={"file_path": "/app/uploads/海边度假照片.jpg", "classification_status": "pending", "show_classification": False}
        ),
        Content(
            id=str(uuid.uuid4()),
            title="项目会议纪要.docx",
            text="会议时间：2024年10月3日\n参会人员：张三、李四、王五\n议题：项目进度讨论\n决议：下周完成开发任务",
            source_uri="webui://项目会议纪要.docx",
            modality="text",
            meta={"file_path": "/app/uploads/项目会议纪要.docx", "classification_status": "pending", "show_classification": False}
        ),
        Content(
            id=str(uuid.uuid4()),
            title="Python学习笔记.md",
            text="# Python基础语法\n\n## 变量和数据类型\n- 字符串\n- 整数\n- 列表\n\n## 函数定义\ndef hello():\n    print('Hello World')",
            source_uri="webui://Python学习笔记.md",
            modality="text",
            meta={"file_path": "/app/uploads/Python学习笔记.md", "classification_status": "pending", "show_classification": False}
        )
    ]
    
    for content in content_items:
        test_db.add(content)
    test_db.commit()
    
    return content_items


@pytest.fixture
def mock_openai_response():
    """模拟OpenAI API响应"""
    return {
        "primary": "生活点滴",
        "secondary": ["职场商务"],
        "confidence": {
            "生活点滴": 0.85,
            "职场商务": 0.45
        },
        "reasoning": "图片显示海边度假场景，主要属于生活记录类别"
    }
