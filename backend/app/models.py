from sqlalchemy import Column, String, Text, JSON, TIMESTAMP, Integer, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from app.db import Base

class Content(Base):
    __tablename__ = "contents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_uri = Column(Text, nullable=True)        # nextcloud:// 或 memo://
    modality   = Column(String, default="text")     # text|image|audio|pdf|voice
    title      = Column(String, nullable=False)
    text       = Column(Text, nullable=False)       # 纯文本（OCR/ASR 后）
    summary    = Column(Text, nullable=True)        # AI 生成的摘要
    tags       = Column(JSON, nullable=True)        # AI 生成的标签
    category   = Column(String, nullable=True)      # AI 生成的分类
    meta       = Column(JSON, nullable=True)        # {people, project, topics, ...}
    
    # 统计信息
    access_count = Column(Integer, default=0)
    search_count = Column(Integer, default=0)
    last_accessed = Column(TIMESTAMP, nullable=True)
    
    created_by = Column(String, default="api")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    chunks = relationship("Chunk", back_populates="content", cascade="all, delete-orphan")
    content_categories = relationship("ContentCategory", back_populates="content", cascade="all, delete-orphan")
    content_tags = relationship("ContentTag", cascade="all, delete-orphan")
    signals = relationship("Signals", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey("contents.id"), nullable=False)
    seq   = Column(Integer, default=0)
    text  = Column(Text, nullable=False)
    
    # 向量存储
    embedding = Column(Vector(1536), nullable=True)  # turing/text-embedding-3-small 维度
    
    # 元数据
    meta  = Column(JSON, nullable=True)            # {source_uri, page, ...}
    chunk_type = Column(String, default="paragraph") # paragraph|title|list|code|table
    token_count = Column(Integer, nullable=True)
    char_count = Column(Integer, nullable=True)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # 关系
    content = relationship("Content", back_populates="chunks")

class QAHistory(Base):
    """问答历史"""
    __tablename__ = "qa_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=True)      # 会话ID
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)           # 引用的文档ID列表
    model_used = Column(String, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)       # 置信度
    feedback = Column(String, nullable=True)        # 用户反馈 good|bad
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class AgentTask(Base):
    """Agent 任务"""
    __tablename__ = "agent_tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type = Column(String, nullable=False)      # memo|email|calendar|todo|search
    input_data = Column(JSON, nullable=False)       # 输入数据
    output_data = Column(JSON, nullable=True)       # 输出结果
    status = Column(String, default="pending")      # pending|running|completed|failed
    agent_used = Column(String, nullable=True)      # 使用的 Agent
    tools_used = Column(JSON, nullable=True)        # 使用的工具列表
    execution_log = Column(Text, nullable=True)     # 执行日志
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    completed_at = Column(TIMESTAMP, nullable=True)

class MCPTool(Base):
    """MCP 工具注册"""
    __tablename__ = "mcp_tools"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)       # connector|executor|reader|writer
    config = Column(JSON, nullable=False)           # 工具配置
    enabled = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Category(Base):
    """文档分类"""
    __tablename__ = "categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)        # 颜色代码，如 #FF5722
    is_system = Column(Boolean, default=False)      # 是否系统预置分类
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    content_categories = relationship("ContentCategory", back_populates="category", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="category", cascade="all, delete-orphan")

class ContentCategory(Base):
    """内容分类关联表（支持多分类和置信度）"""
    __tablename__ = "content_categories"
    content_id = Column(UUID(as_uuid=True), ForeignKey("contents.id"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), primary_key=True)
    confidence = Column(Float, default=1.0)         # 分类置信度 0.0-1.0
    reasoning = Column(Text, nullable=True)         # AI分类理由
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # 新增字段：支持分层分类和来源追踪
    role = Column(String, default="primary_system")  # primary_system|secondary_tag|user_rule
    source = Column(String, default="ml")            # ml|rule|heuristic|manual
    
    # 关系
    content = relationship("Content", back_populates="content_categories")
    category = relationship("Category", back_populates="content_categories")

class Collection(Base):
    """智能合集"""
    __tablename__ = "collections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    auto_generated = Column(Boolean, default=True)  # 是否自动生成
    query_rules = Column(JSON, nullable=True)       # 自动合集的查询规则
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    category = relationship("Category", back_populates="collections")

class Tag(Base):
    """标签表"""
    __tablename__ = "tags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)  # 标签名称
    description = Column(Text, nullable=True)           # 标签描述
    tag_type = Column(String, default="auto")           # auto|manual|system
    parent_id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), nullable=True)  # 支持标签层级
    usage_count = Column(Integer, default=0)            # 使用次数
    embedding = Column(Vector(1536), nullable=True)     # 标签语义向量
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    parent = relationship("Tag", remote_side=[id])
    children = relationship("Tag", overlaps="parent")
    content_tags = relationship("ContentTag", back_populates="tag", cascade="all, delete-orphan")

class ContentTag(Base):
    """内容标签关联表"""
    __tablename__ = "content_tags"
    content_id = Column(UUID(as_uuid=True), ForeignKey("contents.id"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True)
    confidence = Column(Float, default=1.0)             # 标签置信度
    source = Column(String, default="auto")             # auto|manual|rule
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # 关系
    content = relationship("Content", overlaps="content_tags")
    tag = relationship("Tag", back_populates="content_tags")

class Signals(Base):
    """信号审计表 - 记录所有自动决策的详细信息"""
    __tablename__ = "signals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey("contents.id"), nullable=False)
    signal_type = Column(String, nullable=False)        # classification|tag_extraction|search|recommendation
    payload = Column(JSON, nullable=False)              # 详细的决策数据
    confidence = Column(Float, nullable=True)           # 整体置信度
    model_version = Column(String, nullable=True)       # 模型版本
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # 关系
    content = relationship("Content", overlaps="signals")

class OpsLog(Base):
    __tablename__ = "ops_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    op_type = Column(String, nullable=False)       # todo|calendar|email|agent_task
    payload = Column(JSON, nullable=False)
    status  = Column(String, default="draft")
    log     = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

