"""
测试专用的简化模型
避免 pgvector 依赖
"""
from sqlalchemy import Column, String, Text, JSON, Integer, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.orm import relationship
import uuid
from app.db import Base

# 测试专用的简化模型，不包含 pgvector 依赖
class TestContent(Base):
    __tablename__ = "test_contents"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_uri = Column(Text, nullable=True)
    modality = Column(String, default="text")
    title = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    category = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))
    updated_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))
    # 注意：跳过 embedding 字段，因为测试不需要向量功能

class TestCategory(Base):
    __tablename__ = "test_categories"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))

class TestCollection(Base):
    __tablename__ = "test_collections"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    auto_generated = Column(Boolean, default=False)
    created_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))

class TestContentCategory(Base):
    __tablename__ = "test_content_categories"
    content_id = Column(String(36), ForeignKey("test_contents.id"), primary_key=True)
    category_id = Column(String(36), ForeignKey("test_categories.id"), primary_key=True)
    confidence = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    role = Column(String, default="primary_system")  # primary_system, secondary_system, user_rule
    source = Column(String, default="ml")  # ml, heuristic, rule
    created_at = Column(Integer, default=lambda: int(datetime.utcnow().timestamp()))
