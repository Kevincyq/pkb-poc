# PKB 后端架构分析文档

> 📅 生成时间：2025-10-14  
> 🎯 目的：全面梳理PKB后端的模块结构、职责和调用关系

---

## 📊 总体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI 应用层                            │
│                         (app/main.py)                            │
│  - CORS中间件、日志配置、路由注册、系统初始化                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
    │ API 层  │        │Service层│        │Worker层 │
    │ (REST)  │◄──────►│ (业务)  │◄──────►│ (异步)  │
    └────┬────┘        └────┬────┘        └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
    │ Models  │        │Adapters │        │ Parsers │
    │(数据模型)│        │(外部集成)│        │(文档解析)│
    └────┬────┘        └────┬────┘        └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │   PostgreSQL    │
                    │  + pgvector     │
                    │  + Redis        │
                    └─────────────────┘
```

---

## 🏗️ 模块层次结构
核心架构分为5层：
┌─────────────────────────────────────┐
│  1. API层 (11个路由模块)             │  ← REST接口
│  - ingest, search, qa, category等   │
├─────────────────────────────────────┤
│  2. Service层 (9个业务服务)         │  ← 业务逻辑
│  - 搜索、问答、分类、合集匹配等       │
├─────────────────────────────────────┤
│  3. Worker层 (3个任务队列)          │  ← 异步处理
│  - quick, classify, heavy队列       │
├─────────────────────────────────────┤
│  4. Adapter层 + Parser层            │  ← 外部集成+解析
│  - WebDAV, MaxKB, 文档解析器         │
├─────────────────────────────────────┤
│  5. Data层 (8个核心模型)             │  ← 数据持久化
│  - Content, Chunk, Category等       │
└─────────────────────────────────────┘

### **1. 应用入口层 (Entry Point)**

#### `app/main.py` - FastAPI应用主入口
**职责：**
- 创建FastAPI应用实例
- 配置中间件（CORS、代理头处理）
- 注册所有API路由
- 初始化数据库表结构
- 启动时初始化系统分类

**关键代码：**
```python
app = FastAPI(title="PKB-backend", version="0.1.0")
app.include_router(ingest.router, prefix="/api/ingest")
app.include_router(search.router, prefix="/api/search")
# ... 其他路由
```

**依赖：**
- `app.db` - 数据库连接
- `app.models` - 数据模型
- `app.api.*` - 所有API模块
- `app.services.category_service` - 系统初始化

---

### **2. 数据层 (Data Layer)**

#### `app/db.py` - 数据库配置
**职责：**
- 创建SQLAlchemy引擎
- 配置数据库连接池
- 提供会话工厂
- 定义Base类（所有模型的基类）

**关键组件：**
```python
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
```

#### `app/models.py` - 数据模型定义
**核心模型：**

1. **Content (内容表)** - 核心实体
   - 存储所有类型的内容（文本、图片、PDF等）
   - 字段：title, text, summary, modality, source_uri, meta
   - 关系：chunks, content_categories, content_tags

2. **Chunk (文档块表)**
   - 文档分块存储，支持向量搜索
   - 字段：text, embedding (vector(1536)), seq, chunk_type

3. **Category (分类表)**
   - 系统分类和用户自定义分类
   - 字段：name, description, color, is_system

4. **Collection (合集表)**
   - 智能合集，基于规则自动匹配内容
   - 字段：name, query_rules, auto_generated

5. **QAHistory (问答历史)**
   - 记录用户问答对话
   - 字段：question, answer, sources, session_id

6. **AgentTask (Agent任务)**
   - 异步Agent任务记录
   - 字段：task_type, input_data, status, output_data

7. **辅助表：**
   - `ContentCategory` - 内容与分类多对多关联
   - `ContentTag` - 内容与标签关联
   - `Tag` - 标签定义
   - `Signals` - 审计日志（记录AI决策）
   - `MCPTool` - MCP工具注册
   - `OpsLog` - 操作日志

#### `app/constants.py` - 系统常量
**定义：**
- 分类角色类型（PRIMARY_SYSTEM, SECONDARY_TAG, USER_RULE）
- 分类来源类型（ML, RULE, HEURISTIC, MANUAL）
- 搜索模式（KEYWORD, SEMANTIC, HYBRID）
- 阈值配置（分类置信度、语义相似度等）

---

### **3. API 路由层 (API Routes)**

#### `app/api/ingest.py` - 内容摄取
**核心端点：**
- `POST /api/ingest/memo` - 添加文本备忘录
- `POST /api/ingest/scan` - 扫描Nextcloud文件
- `POST /api/ingest/upload` - 单文件上传
- `POST /api/ingest/upload-multiple` - 批量文件上传
- `GET /api/ingest/status/{content_id}` - 查询处理状态

**处理流程：**
```
上传文件 → 保存到/app/uploads/ → 创建Content记录 → 
触发异步任务（解析、分块、向量化、分类、合集匹配）
```

**调用：**
- `app.adapters.webdav` - Nextcloud扫描
- `app.parsers.document_processor` - 文件解析
- `app.workers.tasks` - 异步处理任务
- `app.workers.quick_tasks` - 快速分类任务

#### `app/api/search.py` - 搜索服务
**核心端点：**
- `GET /api/search/` - 多模态搜索（关键词/语义/混合）
- `GET /api/search/suggestions` - 搜索建议
- `GET /api/search/category/{category_id}` - 按分类搜索

**调用：**
- `app.services.search_service.SearchService`
- `app.services.embedding_service.EmbeddingService`

#### `app/api/qa.py` - AI问答
**核心端点：**
- `POST /api/qa/ask` - AI智能问答
- `GET /api/qa/history` - 问答历史
- `POST /api/qa/feedback` - 反馈

**调用：**
- `app.services.qa_service.QAService`
- `app.services.search_service.SearchService`

#### `app/api/category.py` - 分类管理
**核心端点：**
- `GET /api/category/` - 获取分类列表
- `POST /api/category/initialize` - 初始化系统分类
- `POST /api/category/classify` - 单个内容分类
- `POST /api/category/classify/batch` - 批量分类

**调用：**
- `app.services.category_service.CategoryService`

#### `app/api/collection.py` - 合集管理
**核心端点：**
- `GET /api/collection/` - 获取合集列表
- `POST /api/collection/` - 创建合集
- `GET /api/collection/{id}/contents` - 获取合集内容

**调用：**
- `app.services.collection_matching_service.CollectionMatchingService`

#### `app/api/document.py` - 文档管理
**核心端点：**
- `GET /api/document/list` - 文档列表
- `GET /api/document/{content_id}` - 文档详情
- `DELETE /api/document/{content_id}` - 删除文档
- `GET /api/document/chunks` - 获取文档块

**调用：**
- `app.services.document_service.DocumentService`

#### `app/api/files.py` - 文件服务
**核心端点：**
- `GET /api/files/{filename}` - 获取原始文件
- `GET /api/files/thumbnail/{filename}` - 获取缩略图
- `POST /api/files/pregenerate-thumbnail` - 预生成缩略图

**功能：**
- 文件路径解析（支持webui://和nextcloud://）
- 缩略图生成和缓存
- 文件存储管理

#### `app/api/embedding.py` - 向量化服务
**端点：**
- `POST /api/embedding/` - 文本向量化

#### `app/api/agent.py` - Agent服务
**端点：**
- `POST /api/agent/execute` - 执行Agent任务
- `GET /api/agent/tasks/{task_id}` - 获取任务状态

#### `app/api/operator.py` - 运维接口
**端点：**
- `GET /api/operator/` - 运维操作列表

---

### **4. 业务服务层 (Service Layer)**

#### `app/services/search_service.py` - 搜索服务
**职责：**
- 实现多模态搜索（关键词、语义、混合）
- BM25算法实现
- 向量相似度搜索
- 搜索结果融合和排序

**关键方法：**
```python
search(query, search_type, top_k, filters)
keyword_search()  # BM25全文搜索
semantic_search()  # 向量相似度搜索
hybrid_search()    # 融合搜索
```

**依赖：**
- `app.services.embedding_service` - 文本向量化
- PostgreSQL全文搜索、pgvector向量搜索

#### `app/services/qa_service.py` - 问答服务
**职责：**
- AI问答核心逻辑
- 上下文管理
- 来源引用生成
- 对话历史记录

**流程：**
```
用户问题 → 向量化 → 检索相关文档 → 构建Prompt → 
调用GPT → 生成回答 → 保存历史
```

**依赖：**
- `app.services.search_service` - 检索相关内容
- OpenAI API - GPT模型调用

#### `app/services/category_service.py` - 分类服务
**职责：**
- 系统分类初始化
- 内容自动分类
- 分类规则管理
- 多分类支持（主分类+次要标签）

**核心功能：**
```python
initialize_system_categories()  # 初始化预置分类
classify_content(content_id)     # AI分类
get_category_stats()             # 分类统计
```

#### `app/services/quick_classification_service.py` - 快速分类服务
**职责：**
- 基于规则的快速分类（不调用AI）
- 关键词匹配
- 正则表达式匹配
- 启发式分类

**特点：**
- 速度快（毫秒级）
- 准确率中等
- 作为AI分类的前置步骤

#### `app/services/collection_matching_service.py` - 合集匹配服务
**职责：**
- 智能合集规则匹配
- 文档自动归类到合集
- 语义相似度匹配

**匹配策略：**
1. 关键词匹配（精确/模糊）
2. 分类匹配
3. 语义相似度匹配（使用embedding）

#### `app/services/embedding_service.py` - 向量化服务
**职责：**
- 文本转向量（embedding）
- 支持多种embedding模型
- 批量向量化

**模型支持：**
- Turing平台（默认）
- text-embedding-3-small
- 本地embedding模型（可选）

#### `app/services/document_service.py` - 文档服务
**职责：**
- 文档CRUD操作
- 文档验证
- 支持格式检查

#### `app/services/agent_service.py` - Agent服务
**职责：**
- Agent任务编排
- 工具调用管理
- 任务状态追踪

#### `app/services/mcp_service.py` - MCP工具服务
**职责：**
- MCP（Model Context Protocol）工具注册
- 工具调用封装

---

### **5. 异步任务层 (Worker Layer)**

#### `app/workers/celery_app.py` - Celery配置
**队列定义：**
1. **quick队列** - 快速任务（优先级高）
   - 快速分类
   - 文档解析
   - 合集匹配

2. **classify队列** - AI分类任务
   - 精确分类
   - 批量分类

3. **heavy队列** - 重型任务
   - 向量化（generate_embeddings）
   - 图片处理（process_image_content）
   - 大文件处理

4. **ingest队列** - 摄取任务
   - 文件导入

#### `app/workers/quick_tasks.py` - 快速任务
**任务列表：**
```python
@celery_app.task
def quick_classify_content(content_id)
    """快速分类单个内容"""

@celery_app.task
def batch_quick_classify(content_ids)
    """批量快速分类"""

@celery_app.task
def match_document_to_collections(content_id)
    """匹配文档到合集"""
```

#### `app/workers/tasks.py` - 主要任务
**任务列表：**
```python
@celery_app.task
def generate_embeddings(chunk_ids)
    """生成向量embedding"""

@celery_app.task
def classify_content(content_id)
    """AI精确分类"""

@celery_app.task
def batch_classify_contents(content_ids)
    """批量AI分类"""

@celery_app.task
def parse_and_chunk_file(content_id, file_path)
    """解析文件并分块"""

@celery_app.task
def process_image_content(content_id)
    """处理图片内容（OCR识别）"""

@celery_app.task
def generate_image_thumbnail(content_id, file_path)
    """生成图片缩略图"""

@celery_app.task
def ingest_file(path)
    """导入文件"""
```

**任务执行流程（以上传为例）：**
```
1. 文件上传 → 创建Content记录
2. parse_and_chunk_file (quick队列, 优先级10)
   ↓
3. quick_classify_content (quick队列, 优先级9)
   ↓
4. classify_content (classify队列, 优先级8, 延迟4秒)
   ↓
5. match_document_to_collections (quick队列, 优先级7, 延迟10秒)
   ↓
6. generate_embeddings (heavy队列, 后台执行)
```

---

### **6. 适配器层 (Adapters)**

#### `app/adapters/webdav.py` - Nextcloud集成
**职责：**
- WebDAV协议通信
- 文件列表获取
- 文件下载
- XML解析（PROPFIND响应）

**核心功能：**
```python
list_webdav(url)               # 列出目录文件
download_text(url)              # 下载文本文件
download_binary(url)            # 下载二进制文件
download_and_parse_file(url)    # 下载并解析
scan_inbox()                    # 扫描PKB-Inbox目录
```

**使用场景：**
- 定时扫描Nextcloud新文件
- 自动同步文件到PKB

#### `app/adapters/maxkb.py` - MaxKB集成
**职责：**
- MaxKB向量库集成
- 文档上传到MaxKB
- 语义搜索

**核心功能：**
```python
upsert_document(text, meta)     # 上传文档
semantic_search(query, top_k)   # 语义搜索
```

---

### **7. 解析器层 (Parsers)**

#### `app/parsers/document_processor.py` - 文档处理器（统一入口）
**职责：**
- 文件类型检测
- 路由到对应解析器
- 统一解析接口

**支持格式：**
- 文本：`.txt`, `.md`
- PDF：`.pdf`
- 图片：`.jpg`, `.png`, `.gif`, `.webp`, `.bmp`
- Office：`.docx`（部分支持）

**核心方法：**
```python
detect_file_type(filename)           # 检测文件类型
is_supported(filename)               # 检查是否支持
process_file(file_path)              # 处理文件（路径）
process_bytes(file_bytes, filename)  # 处理文件（二进制）
process_content(content, filename)   # 处理内容（文本）
```

#### `app/parsers/text_parser.py` - 文本解析器
**支持：** `.txt`, `.md`
**功能：** 直接读取文本内容

#### `app/parsers/pdf_parser.py` - PDF解析器
**支持：** `.pdf`
**功能：** 
- 提取文本内容
- 页数统计
- 元数据提取

#### `app/parsers/image_parser.py` - 图片解析器
**支持：** 图片格式
**功能：**
- GPT-4V视觉识别
- 图片内容描述生成
- OCR文字提取

**依赖：** OpenAI GPT-4o-mini (vision)

#### `app/parsers/markdown_parser.py` - Markdown解析器
**支持：** `.md`
**功能：**
- Markdown语法解析
- 结构化提取

---

### **8. 工具层 (Utils)**

#### `app/utils/datetime_utils.py` - 日期时间工具
**功能：**
- 时区处理
- 日期序列化
- 格式转换

---

## 🔄 数据流向分析

### **场景1：WebUI文件上传**

```
1. 用户上传文件
   ↓
2. POST /api/ingest/upload
   ├─ 保存文件到 /app/uploads/
   ├─ 创建Content记录（status: uploaded）
   └─ 返回content_id给前端
   ↓
3. 触发异步任务链
   ├─ parse_and_chunk_file (解析并分块)
   │  ├─ DocumentProcessor.process_file()
   │  ├─ simple_chunk() 文本分块
   │  └─ 更新Content.text
   ├─ quick_classify_content (快速分类)
   │  └─ QuickClassificationService.classify()
   ├─ classify_content (AI精确分类)
   │  └─ CategoryService.classify_content()
   ├─ match_document_to_collections (匹配合集)
   │  └─ CollectionMatchingService.match()
   └─ generate_embeddings (向量化)
      └─ EmbeddingService.embed_chunks()
   ↓
4. 前端轮询 GET /api/ingest/status/{content_id}
   └─ 返回处理状态和分类结果
```

### **场景2：Nextcloud文件同步**

```
1. 定时任务触发（每5分钟）
   ↓
2. POST /api/ingest/scan
   ├─ webdav.scan_inbox()
   │  ├─ list_webdav() 列出文件
   │  ├─ download_and_parse_file() 下载解析
   │  └─ 返回 [{title, text, source_uri, metadata}]
   ├─ 检查去重（source_uri）
   ├─ 创建新的Content记录
   └─ 检测并删除Nextcloud中已删除的文件
   ↓
3. 触发异步任务（同WebUI上传）
   └─ 问题：图片文件没有下载到本地 ❌
```

### **场景3：AI问答**

```
1. 用户提问
   ↓
2. POST /api/qa/ask
   ├─ QAService.ask(question, session_id)
   │  ├─ 向量化问题
   │  │  └─ EmbeddingService.embed_text()
   │  ├─ 检索相关内容
   │  │  └─ SearchService.search(semantic)
   │  ├─ 构建Prompt（问题+上下文+历史）
   │  ├─ 调用GPT-4o-mini
   │  └─ 解析回答+来源引用
   ├─ 保存QAHistory记录
   └─ 返回{answer, sources, session_id}
```

### **场景4：搜索**

```
1. 用户搜索
   ↓
2. GET /api/search/?q=关键词&search_type=hybrid
   ├─ SearchService.search()
   │  ├─ 关键词搜索（BM25）
   │  │  └─ PostgreSQL全文搜索
   │  ├─ 语义搜索
   │  │  ├─ 向量化查询
   │  │  └─ pgvector相似度搜索
   │  └─ 融合排序（0.3*BM25 + 0.5*Semantic + 0.2*Tag)
   └─ 返回搜索结果
```

---

## 🎯 关键设计模式

### **1. 分层架构**
- API层（接口） → Service层（业务） → Model层（数据）
- 清晰的职责分离

### **2. 异步任务模式**
- Celery实现异步处理
- 队列优先级管理
- 任务链编排

### **3. 适配器模式**
- 外部服务封装（WebDAV, MaxKB）
- 统一接口，易于替换

### **4. 工厂模式**
- DocumentProcessor路由不同解析器
- 根据文件类型选择处理器

### **5. 依赖注入**
- Service接收db session
- 便于测试和管理

---

## ⚠️ 架构问题和改进建议

### **当前问题：**

1. **Nextcloud图片未下载** ❌（待调整NextCloud架构）
   - 位置：`app/adapters/webdav.py` 和 `app/api/ingest.py`
   - 影响：Nextcloud上传的图片无法显示缩略图
   - 原因：扫描时只保存了元数据，未下载文件

2. **文件路径管理混乱**（待调整NextCloud架构）
   - webui:// 和 nextcloud:// 处理不一致
   - 需要统一文件访问接口

3. **缺少缓存层**
   - 搜索结果、embedding可以缓存
   - 减少重复计算

### **改进建议：**

1. **统一文件管理**
   ```python
   # 新建 app/services/file_storage_service.py
   class FileStorageService:
       def save_file(source_uri, file_bytes)
       def get_file(source_uri)
       def generate_thumbnail(source_uri)
   ```

2. **添加缓存层**
   ```python
   # 使用Redis缓存
   - 搜索结果缓存（5分钟）
   - Embedding缓存（永久）
   - 分类结果缓存（1小时）
   ```

3. **改进错误处理**
   - 统一异常类
   - 重试机制
   - 错误上报

4. **性能优化**
   - 批量操作优化
   - 数据库索引优化
   - 异步IO优化

---

## 📚 模块依赖关系总结

```
main.py
 ├─ api/* (所有路由)
 │  ├─ services/* (业务逻辑)
 │  ├─ workers/* (异步任务)
 │  ├─ adapters/* (外部集成)
 │  └─ parsers/* (文档解析)
 ├─ db.py (数据库)
 ├─ models.py (数据模型)
 └─ constants.py (常量配置)

services/*
 ├─ embedding_service → OpenAI/Turing API
 ├─ search_service → PostgreSQL + pgvector
 ├─ qa_service → search_service + GPT
 ├─ category_service → GPT分类
 └─ collection_matching_service → embedding匹配

workers/*
 ├─ celery_app (Celery配置)
 ├─ quick_tasks (快速任务)
 └─ tasks (重型任务)
    ├─ 调用services/*
    ├─ 调用parsers/*
    └─ 更新models

adapters/*
 ├─ webdav → Nextcloud
 └─ maxkb → MaxKB

parsers/*
 └─ document_processor
    ├─ text_parser
    ├─ pdf_parser
    ├─ image_parser
    └─ markdown_parser
```

---

## 🎓 总结

PKB后端采用**经典的分层架构**：

1. **API层**：提供RESTful接口，参数验证
2. **Service层**：封装业务逻辑，可复用
3. **Worker层**：异步任务处理，提升性能
4. **Adapter层**：外部服务集成，解耦依赖
5. **Parser层**：文档解析，支持多格式
6. **Model层**：数据持久化，ORM映射

**核心特点：**
- ✅ 职责清晰，易于维护
- ✅ 异步处理，性能优秀
- ✅ 模块化设计，易于扩展
- ⚠️ 部分模块耦合较紧（需要优化）
- ⚠️ 缺少完善的错误处理和监控

**技术栈：**
- FastAPI - Web框架
- SQLAlchemy - ORM
- Celery - 异步任务
- PostgreSQL + pgvector - 数据库+向量搜索
- Redis - 消息队列+缓存
- OpenAI API - AI能力

---

*📝 此文档随代码演进持续更新*

