# PKB - Personal Knowledge Base

> 🧠 智能个人知识库系统 - 集成 AI 问答、多模态搜索、自动分类的现代化知识管理平台

## 🌟 核心功能

- **🤖 AI 智能问答** - 基于知识库内容的智能问答系统，支持上下文对话
- **🔍 多模态搜索** - 支持关键词、语义和混合搜索，智能匹配相关内容
- **📁 多源数据接入** - Nextcloud 文件同步 + WebUI 直接上传 + 批量文件处理
- **🏷️ 自动分类系统** - AI 驱动的内容自动分类和标签生成
- **📚 自建合集管理** - 用户自定义知识合集，灵活组织内容
- **🎯 智能预览系统** - 图片缩略图生成 + 渐进式加载优化
- **⚡ 异步处理** - Celery 任务队列，支持大文件和批量处理
- **🌐 现代化界面** - React + TypeScript + 原生组件构建的响应式 Web 界面
- **🐳 容器化部署** - Docker Compose 一键部署，支持云端和本地部署

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  React Frontend │    │   PKB Backend   │    │  PostgreSQL     │
│  (TypeScript)   │◄──►│   (FastAPI)     │◄──►│ (数据+向量存储)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
         ┌─────────────────┐    │              ┌─────────────────┐
         │   Nextcloud     │    │              │   Celery        │
         │  (文件同步)      │◄───┼──────────────►│  (异步任务)      │
         └─────────────────┘    │              └─────────────────┘
                                │                       │
                       ┌─────────────────┐     ┌─────────────────┐
                       │  AI Services    │     │     Redis       │
                       │ (GPT-4o/Turing) │     │   (缓存+队列)    │
                       └─────────────────┘     └─────────────────┘
```

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose
- 4GB+ 内存 (推荐 8GB)
- 20GB+ 磁盘空间
- 支持的操作系统：Linux、macOS、Windows

### 1. 克隆项目

```bash
git clone https://github.com/Kevincyq/pkb-poc.git
cd pkb-poc
```

### 2. 配置环境变量

创建 `deploy/.env` 文件：

```bash
# AI 服务配置 (必需)
TURING_API_KEY=your_turing_api_key
TURING_BASE_URL=https://api.turing.com/v1

# Nextcloud WebDAV 配置 (可选)
NC_WEBDAV_URL=https://your-nextcloud.com/remote.php/dav/files/username/PKB-Inbox/
NC_USER=your_nextcloud_username
NC_PASS=your_nextcloud_password
NC_EXTS=.txt,.md,.pdf,.docx,.jpg,.png

# 数据库配置
POSTGRES_HOST=postgres
POSTGRES_DB=pkb
POSTGRES_USER=pkb
POSTGRES_PASSWORD=your_secure_password

# Redis 配置
REDIS_URL=redis://redis:6379/0

# 应用配置
PKB_BASE_URL=http://localhost:8002
FRONTEND_URL=http://localhost:3000
```

### 3. 启动服务

```bash
cd deploy
# 使用云端配置启动
docker-compose -f docker-compose.cloud.yml up -d

# 或使用本地开发配置
docker-compose up -d
```

### 4. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 测试后端 API
curl "http://localhost:8002/api/health"

# 访问 Web 界面
open http://localhost:3000

# 访问 API 文档
open http://localhost:8002/api/docs
```

### 5. 初始化系统

```bash
# 初始化系统分类
curl -X POST "http://localhost:8002/api/category/initialize"

# 可选：扫描 Nextcloud 文件
curl -X POST "http://localhost:8002/api/ingest/scan"
```

## 📖 使用指南

### Web 界面操作

#### 1. 访问主界面
- 打开浏览器访问 `http://localhost:3000`
- 主页显示所有知识合集和最近上传的文档
- 支持 PC 端和移动端响应式布局

#### 2. 文件上传
- **支持格式**：
  - 📄 文本：.txt, .md, .pdf
  - 🖼️ 图片：.jpg, .jpeg, .png, .gif, .bmp, .webp
  - ❌ 暂不支持：Office 文档(.doc, .xls, .ppt等)
- **上传限制**：
  - 📏 单文件大小：≤ 20MB
  - 📦 批量上传：≤ 5个文件
- **上传方式**：
  - 点击上传区域选择文件
  - 拖拽文件到上传区域
  - 支持多文件批量上传

#### 3. AI 问答
- 在主页的问答区域输入问题
- 系统会基于知识库内容智能回答
- 支持上下文对话和引用来源
- 实时显示处理状态

#### 4. 搜索功能
- 使用顶部搜索框进行全文搜索
- 支持关键词、语义和混合搜索模式
- 可按分类和内容类型过滤
- 智能搜索建议和自动完成

#### 5. 浏览合集
- 点击合集卡片查看分类内容
- 支持系统自动分类和用户自建合集
- **文档预览**：
  - 🖼️ 图片：智能缩略图 + 渐进式加载
  - 📄 文档：文件信息和内容预览
  - ⚡ 快速加载：缩略图优先，原图后台加载

#### 6. 交互操作
- **原生下拉菜单**：替代 Ant Design Dropdown，解决事件冲突
- **智能提示**：原生 Tooltip 组件，支持点击和悬停
- **响应式设计**：完美适配 PC 端和移动端

### API 接口使用

#### 1. 手动添加内容

```bash
curl -X POST "http://localhost:8002/api/ingest/memo" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "学习笔记",
    "text": "今天学习了 Docker 容器化技术...",
    "meta": {"tags": ["学习", "技术"]},
    "source_uri": "memo://manual-input"
  }'
```

#### 2. 批量文件上传

```bash
curl -X POST "http://localhost:8002/api/ingest/upload-multiple" \
  -F "files=@document1.pdf" \
  -F "files=@image1.jpg" \
  -F "files=@notes.txt"
```

#### 3. AI 问答

```bash
curl -X POST "http://localhost:8002/api/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是 Docker？",
    "session_id": "user_session_123",
    "search_type": "hybrid"
  }'
```

#### 4. 高级搜索

```bash
# 混合搜索（推荐）
curl -G "http://localhost:8002/api/search/" \
  --data-urlencode "q=Docker 容器" \
  --data-urlencode "search_type=hybrid" \
  --data-urlencode "top_k=10"

# 语义搜索
curl -G "http://localhost:8002/api/search/" \
  --data-urlencode "q=容器化技术" \
  --data-urlencode "search_type=semantic"

# 按分类过滤
curl -G "http://localhost:8002/api/search/" \
  --data-urlencode "q=学习" \
  --data-urlencode "category=科技前沿"
```

#### 5. 分类管理

```bash
# 获取所有分类
curl "http://localhost:8002/api/category/"

# 手动分类内容
curl -X POST "http://localhost:8002/api/category/classify" \
  -H "Content-Type: application/json" \
  -d '{"content_id": "content_uuid", "force_reclassify": true}'

# 批量分类
curl -X POST "http://localhost:8002/api/category/classify/batch" \
  -H "Content-Type: application/json" \
  -d '{"content_ids": ["uuid1", "uuid2"], "force_reclassify": false}'
```

## 🔧 API 接口总览

### 内容摄取接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/ingest/memo` | POST | 添加文本备忘录 |
| `/api/ingest/scan` | POST | 扫描 Nextcloud 文件 |
| `/api/ingest/upload` | POST | 单文件上传 |
| `/api/ingest/upload-multiple` | POST | 批量文件上传 |
| `/api/ingest/status/{content_id}` | GET | 获取处理状态 |
| `/api/ingest/file` | POST | 文件摄取处理 |

### 文档管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/document/validate/{filename}` | GET | 验证文件类型 |
| `/api/document/formats` | GET | 获取支持格式 |
| `/api/document/parse-text` | POST | 解析文本内容 |
| `/api/document/list` | GET | 获取文档列表 |
| `/api/document/chunks` | GET | 获取文档块列表 |
| `/api/document/stats` | GET | 获取文档统计 |
| `/api/document/{content_id}` | GET/DELETE | 获取/删除文档 |
| `/api/document/deleted-records` | GET | 获取删除记录 |
| `/api/document/deleted-records/{record_id}` | DELETE | 移除删除记录 |

### AI 智能服务

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/qa/ask` | POST | AI 智能问答 |
| `/api/qa/generate-report` | POST | 生成智能报告 |
| `/api/qa/history` | GET | 获取问答历史 |
| `/api/qa/feedback` | POST | 更新反馈 |
| `/api/qa/sessions` | GET | 获取活跃会话 |
| `/api/qa/test` | GET | 测试 QA 服务 |

### 搜索服务

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/search/` | GET | 多模态搜索 |
| `/api/search/health` | GET | 搜索服务健康检查 |
| `/api/search/suggestions` | GET | 获取搜索建议 |
| `/api/search/category/{category_id}` | GET | 按分类搜索 |
| `/api/search/categories/stats` | GET | 获取分类搜索统计 |

### 分类管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/category/` | GET | 获取分类列表 |
| `/api/category/initialize` | POST | 初始化系统分类 |
| `/api/category/{category_id}` | GET/PUT/DELETE | 分类详情/更新/删除 |
| `/api/category/classify` | POST | 内容分类 |
| `/api/category/classify/batch` | POST | 批量分类 |
| `/api/category/stats/overview` | GET | 获取分类统计概览 |
| `/api/category/service/status` | GET | 获取服务状态 |
| `/api/category/content/{content_id}/status` | GET | 获取内容分类状态 |
| `/api/category/reclassify/all` | POST | 重新分类所有内容 |
| `/api/category/custom` | POST | 创建自定义分类 |
| `/api/category/initialize-system-categories` | POST | 初始化系统分类 |

### 合集管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/collection/` | GET/POST | 合集列表/创建 |
| `/api/collection/{collection_id}` | PUT/DELETE | 更新/删除合集 |
| `/api/collection/{collection_id}/contents` | GET | 获取合集内容 |
| `/api/collection/fix-missing-rules` | POST | 修复缺失规则 |
| `/api/collection/fix-orphaned-collections` | POST | 修复孤立合集 |
| `/api/collection/match-all-documents` | POST | 匹配所有文档到合集 |
| `/api/collection/debug/duplicates` | GET | 调试重复合集 |
| `/api/collection/cleanup/duplicates` | POST | 清理重复合集 |
| `/api/collection/cleanup/invalid-categories` | POST | 清理无效分类 |
| `/api/collection/debug/category-content-mismatch` | GET | 调试分类内容不匹配 |
| `/api/collection/cleanup/orphan-content` | POST | 清理孤儿内容 |
| `/api/collection/fix-collection-data` | POST | 修复合集数据 |

### 文件服务

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/files/{filename}` | GET | 获取原始文件 |
| `/api/files/raw/{filename}` | GET | 获取原始文件（直接） |
| `/api/files/thumbnail/{filename}` | GET | 获取缩略图 |
| `/api/files/pregenerate-thumbnail` | POST | 预生成缩略图 |
| `/api/files/batch-pregenerate-thumbnails` | POST | 批量预生成缩略图 |
| `/api/files/thumbnails/cleanup` | DELETE | 清理旧缩略图 |
| `/api/files/thumbnails/stats` | GET | 获取缩略图统计 |
| `/api/files/debug/{filename}` | GET | 调试文件路径 |
| `/api/files/list-uploads` | GET | 列出上传文件 |
| `/api/files/list-database-files` | GET | 列出数据库文件 |
| `/api/files/migrate-storage` | POST | 迁移文件存储 |
| `/api/files/reset-database` | POST | 重置数据库 |
| `/api/files/cleanup-storage` | POST | 清理存储目录 |
| `/api/files/check-upload-config` | GET | 检查上传配置 |

### 文件服务（改进版）

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/files_improved/thumbnail/{filename}` | GET | 获取文件缩略图（改进版） |
| `/api/files_improved/debug/paths/{filename}` | GET | 调试文件路径 |

### 智能代理服务

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/agent/execute` | POST | 执行代理任务 |
| `/api/agent/tasks/{task_id}` | GET | 获取任务状态 |
| `/api/agent/plan` | POST | 规划复杂任务 |
| `/api/agent/tools` | GET | 获取可用工具列表 |
| `/api/agent/mcp/register` | POST | 注册 MCP 工具 |
| `/api/agent/mcp/call` | POST | 调用 MCP 工具 |
| `/api/agent/mcp/tools` | GET | 获取 MCP 工具 |
| `/api/agent/mcp/tools/{tool_name}/enable` | POST | 启用 MCP 工具 |
| `/api/agent/mcp/tools/{tool_name}/disable` | POST | 禁用 MCP 工具 |
| `/api/agent/mcp/initialize` | POST | 初始化默认工具 |

### 向量化服务

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/embedding/` | POST | 文本向量化 |

### 运维管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/operator/` | GET | 运维操作列表 |

### 系统接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/docs` | GET | API 文档 |

## 📊 核心数据模型

### Content (内容表)

```sql
CREATE TABLE contents (
    id UUID PRIMARY KEY,
    user_id UUID,              -- 用户ID (多用户支持)
    source_uri TEXT,           -- 来源URI
    modality VARCHAR,          -- 模态类型 (text/image/pdf/audio)
    title VARCHAR NOT NULL,    -- 文档标题
    text TEXT,                 -- 文档内容
    summary TEXT,              -- 文档摘要
    category VARCHAR,          -- 分类
    meta JSONB,                -- 元数据 (JSON格式)
    access_count INTEGER,      -- 访问次数
    search_count INTEGER,      -- 搜索次数
    last_accessed TIMESTAMP,   -- 最后访问时间
    created_by VARCHAR,        -- 创建者
    created_at TIMESTAMP,      -- 创建时间
    updated_at TIMESTAMP       -- 更新时间
);
```

### Chunks (文档块表)

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    content_id UUID REFERENCES contents(id),
    text TEXT NOT NULL,        -- 文档块内容
    chunk_type VARCHAR,        -- 块类型
    embedding vector(1536),    -- 向量嵌入
    created_at TIMESTAMP
);
```

### Categories (分类表)

```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    name VARCHAR UNIQUE,       -- 分类名称
    description TEXT,          -- 分类描述
    icon VARCHAR,              -- 图标
    color VARCHAR,             -- 颜色
    is_system BOOLEAN,         -- 是否系统分类
    created_at TIMESTAMP
);
```

### Collections (合集表)

```sql
CREATE TABLE collections (
    id UUID PRIMARY KEY,
    user_id UUID,              -- 用户ID
    name VARCHAR NOT NULL,     -- 合集名称
    description TEXT,          -- 描述
    keywords TEXT[],           -- 关键词数组
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Content Tags (内容标签表)

```sql
CREATE TABLE content_tags (
    id UUID PRIMARY KEY,
    content_id UUID REFERENCES contents(id),
    name VARCHAR NOT NULL,     -- 标签名称
    confidence FLOAT,          -- 置信度
    created_at TIMESTAMP
);
```

## 🛠️ 开发指南

### 项目结构

```
pkb-poc/
├── backend/                 # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/            # API 路由模块
│   │   │   ├── qa.py       # AI 问答接口
│   │   │   ├── search.py   # 搜索接口
│   │   │   ├── category.py # 分类管理
│   │   │   ├── collection.py # 合集管理
│   │   │   ├── ingest.py   # 内容摄取
│   │   │   ├── files.py    # 文件服务
│   │   │   ├── document.py # 文档处理
│   │   │   └── embedding.py # 向量化服务
│   │   ├── services/       # 业务逻辑服务
│   │   │   ├── search_service.py
│   │   │   ├── qa_service.py
│   │   │   └── classification_service.py
│   │   ├── workers/        # Celery 异步任务
│   │   ├── adapters/       # 外部服务适配器
│   │   │   └── webdav.py   # WebDAV 适配器
│   │   ├── parsers/        # 文档解析器
│   │   ├── utils/          # 工具函数
│   │   │   └── datetime_utils.py
│   │   ├── models.py       # 数据模型
│   │   ├── db.py          # 数据库配置
│   │   └── main.py        # 应用入口
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # 前端界面 (React + TypeScript)
│   ├── src/
│   │   ├── components/     # React 组件
│   │   │   ├── AIChat/     # AI 聊天组件
│   │   │   ├── AIInput/    # AI 输入组件
│   │   │   ├── Collection/ # 合集组件
│   │   │   ├── Document/   # 文档组件
│   │   │   ├── Layout/     # 布局组件
│   │   │   ├── NativeDropdown/ # 原生下拉菜单
│   │   │   ├── NativeTooltip/  # 原生提示组件
│   │   │   ├── PreviewContent/ # 预览内容组件
│   │   │   ├── Search/     # 搜索组件
│   │   │   └── Upload/     # 上传组件
│   │   ├── pages/          # 页面组件
│   │   │   ├── Home/       # 首页
│   │   │   └── Collection/ # 合集详情页
│   │   ├── services/       # API 服务
│   │   ├── utils/          # 工具函数
│   │   │   └── dateUtils.ts # 日期工具
│   │   ├── types/          # TypeScript 类型
│   │   └── styles/         # 样式文件
│   │       └── mobile.css  # 移动端样式
│   ├── package.json
│   └── vite.config.ts
├── deploy/                  # 部署配置
│   ├── docker-compose.yml
│   ├── docker-compose.cloud.yml
│   └── .env.template
└── README.md
```

### 本地开发环境

#### 后端开发

```bash
# 安装 Python 依赖
cd backend
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动 Celery Worker (另一个终端)
celery -A app.workers.celery_app worker -l info
```

#### 前端开发

```bash
# 安装 Node.js 依赖
cd frontend
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 预览构建结果
pnpm preview
```

### 技术栈

#### 后端技术
- **FastAPI** - 现代化 Python Web 框架
- **PostgreSQL + pgvector** - 数据库和向量存储
- **Celery + Redis** - 异步任务处理
- **SQLAlchemy** - ORM 数据库操作
- **Pydantic** - 数据验证和序列化
- **OpenAI API** - AI 服务集成
- **Pillow** - 图片处理
- **PyPDF2** - PDF 解析
- **lxml** - XML/HTML 解析

#### 前端技术
- **React 18** - 用户界面框架
- **TypeScript** - 类型安全的 JavaScript
- **Ant Design 5.12.8** - UI 组件库 (部分组件)
- **原生组件** - NativeDropdown, NativeTooltip (解决事件冲突)
- **Vite** - 现代化构建工具
- **React Query** - 数据获取和缓存
- **React Router** - 路由管理
- **CSS Modules** - 样式模块化

## 🎯 最新功能特性

### ✅ 已实现功能

#### 核心功能
- **🤖 AI 智能问答** - 基于 GPT-4o 的智能问答系统
- **🔍 多模态搜索** - 关键词、语义、混合搜索
- **📁 文件上传处理** - 支持多种格式的文件上传和解析
- **🏷️ 自动分类** - AI 驱动的内容自动分类和标签生成
- **📚 合集管理** - 用户自定义知识合集，支持增删改查

#### 用户界面
- **🌐 现代化界面** - React + TypeScript 构建的响应式 Web 界面
- **📱 移动端适配** - 完美支持手机和平板设备
- **🎨 原生组件** - 自研 NativeDropdown 和 NativeTooltip 组件
- **⚡ 智能预览** - 图片渐进式加载，缩略图优先显示
- **🎯 交互优化** - 解决了 Ant Design 组件的事件冲突问题

#### 性能优化
- **🚀 异步处理** - Celery 任务队列处理大文件
- **💾 智能缓存** - Redis 缓存提升响应速度
- **📦 批量操作** - 支持多文件批量上传和处理
- **🔄 实时反馈** - 任务状态实时更新

#### 数据管理
- **🗄️ 向量存储** - PostgreSQL + pgvector 向量数据库
- **🏷️ 标签系统** - 内容标签和分类管理
- **📊 统计分析** - 访问统计和搜索分析
- **🔗 关联管理** - 内容关联和引用追踪

### 🔄 部署方式

- **本地部署** - 支持 Docker Compose 本地部署
- **云端部署** - 支持 Vercel + 云服务器部署
- **自动更新** - GitHub 集成的自动部署脚本
- **环境隔离** - 开发、测试、生产环境分离

### 📈 性能特点

- **异步处理** - Celery 任务队列处理大文件
- **智能缓存** - Redis 缓存提升响应速度
- **批量操作** - 支持多文件批量上传和处理
- **实时反馈** - WebSocket 实时任务状态更新
- **渐进式加载** - 图片预览优化，先显示缩略图再加载原图

## 🔍 智能搜索系统

PKB 采用先进的多模态搜索技术，提供精准的知识检索：

### 搜索模式

1. **关键词搜索** - 基于 PostgreSQL 全文搜索，支持中英文分词
2. **语义搜索** - 使用向量嵌入进行语义相似度匹配
3. **混合搜索** - 结合关键词和语义搜索，智能权重分配
4. **图像搜索** - 支持图片内容识别和相似图片查找

### AI 问答系统

- **上下文理解** - 基于对话历史维护上下文
- **来源引用** - 自动标注答案来源和相关文档
- **多轮对话** - 支持连续问答和澄清问题
- **智能摘要** - 自动生成文档摘要和关键信息

## 🐛 已解决的技术问题

### 数据库问题
- ✅ **列冲突问题** - 解决了 `contents.tags` 列与 `@property tags` 的冲突
- ✅ **时区问题** - 统一了前后端的时间处理，解决了8小时时差问题
- ✅ **WebDAV XML解析** - 处理了 Nextcloud 返回的格式问题

### 前端交互问题
- ✅ **Dropdown 事件冲突** - 用原生组件替代 Ant Design Dropdown
- ✅ **Tooltip 显示问题** - 用原生组件替代 Ant Design Tooltip
- ✅ **移动端适配** - 完善了响应式设计和触摸优化
- ✅ **图片预览优化** - 实现了渐进式加载和错误处理

### 性能优化
- ✅ **预览加载慢** - 优化了图片预览的加载策略
- ✅ **组件重渲染** - 使用 React.memo 优化了组件性能
- ✅ **事件处理冲突** - 解决了全局事件监听器的冲突问题


## 📞 支持与反馈

如有问题或建议，请通过以下方式联系：

- 创建 [GitHub Issue](https://github.com/Kevincyq/pkb-poc/issues)
- 查看 [项目文档](https://github.com/Kevincyq/pkb-poc)
- 在线演示：[PKB Demo](https://pkb-poc.kmchat.cloud)
- 技术支持：kevincyq@gmail.com

## 🏆 项目亮点

PKB 是一个**生产就绪**的智能知识库系统，具备以下特色：

- 🧠 **AI 原生** - 深度集成 GPT-4o，提供智能问答和内容分析
- 🔍 **搜索优先** - 多模态搜索引擎，精准匹配用户需求
- 🎯 **用户友好** - 现代化 Web 界面，直观的操作体验
- ⚡ **高性能** - 异步处理架构，支持大规模数据处理
- 🐳 **易部署** - 容器化设计，一键部署到任何环境
- 🔧 **可扩展** - 模块化架构，易于定制和扩展
- 🛠️ **技术先进** - 采用最新的前后端技术栈，代码质量高
- 🎨 **原生组件** - 自研组件解决第三方库的兼容性问题