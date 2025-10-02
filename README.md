# PKB - Personal Knowledge Base

> 🧠 智能个人知识库系统 - 集成 AI 问答、多模态搜索、自动分类的现代化知识管理平台

## 🌟 核心功能

- **🤖 AI 智能问答** - 基于知识库内容的智能问答系统，支持上下文对话
- **🔍 多模态搜索** - 支持关键词、语义和混合搜索，智能匹配相关内容
- **📁 多源数据接入** - Nextcloud 文件同步 + WebUI 直接上传 + 批量文件处理
- **🏷️ 自动分类系统** - AI 驱动的内容自动分类和标签生成
- **📚 自建合集管理** - 用户自定义知识合集，灵活组织内容
- **🎯 缩略图生成** - 图片文件自动生成缩略图，优化浏览体验
- **⚡ 异步处理** - Celery 任务队列，支持大文件和批量处理
- **🌐 现代化界面** - React + Ant Design 构建的响应式 Web 界面
- **🐳 容器化部署** - Docker Compose 一键部署，支持云端和本地部署

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  React Frontend │    │   PKB Backend   │    │  PostgreSQL     │
│  (Web界面)       │◄──►│   (FastAPI)     │◄──►│ (数据+向量存储)  │
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

#### 2. 上传文件
- 在主页点击上传区域或拖拽文件
- 支持多文件批量上传
- 支持格式：文本、图片、PDF、Word 文档等

#### 3. AI 问答
- 在主页的问答区域输入问题
- 系统会基于知识库内容智能回答
- 支持上下文对话和引用来源

#### 4. 搜索功能
- 使用顶部搜索框进行全文搜索
- 支持关键词、语义和混合搜索模式
- 可按分类和内容类型过滤

#### 5. 浏览合集
- 点击合集卡片查看分类内容
- 支持系统自动分类和用户自建合集
- 可查看文档详情和缩略图

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
curl -X POST "http://localhost:8002/api/ingest/upload_multiple_files" \
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

### 数据库查询

#### 进入数据库

```bash
docker-compose exec postgres psql -U pkb -d pkb
```

#### 常用查询

```sql
-- 查看所有文档
SELECT id, title, created_at FROM contents ORDER BY created_at DESC;

-- 搜索包含关键词的内容
SELECT c.title, LEFT(ch.text, 100) as preview 
FROM chunks ch 
JOIN contents c ON ch.content_id = c.id 
WHERE ch.text ILIKE '%docker%' 
LIMIT 5;

-- 统计信息
SELECT 
    COUNT(*) as total_documents,
    COUNT(DISTINCT created_by) as sources
FROM contents;
```

## 🔧 API 接口总览

### 内容摄取接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/ingest/memo` | POST | 添加文本备忘录 |
| `/api/ingest/scan` | POST | 扫描 Nextcloud 文件 |
| `/api/ingest/upload_multiple_files` | POST | 批量文件上传 |
| `/api/document/parse-text` | POST | 解析文本内容 |

### AI 智能服务

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/qa/ask` | POST | AI 智能问答 |
| `/api/qa/generate-report` | POST | 生成智能报告 |
| `/api/search/` | GET | 多模态搜索 |
| `/api/embedding/` | POST | 文本向量化 |

### 分类管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/category/` | GET | 获取分类列表 |
| `/api/category/initialize` | POST | 初始化系统分类 |
| `/api/category/classify` | POST | 内容分类 |
| `/api/category/classify/batch` | POST | 批量分类 |
| `/api/category/{id}` | GET | 获取分类详情 |

### 合集管理

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/collection/` | GET/POST | 合集列表/创建 |
| `/api/collection/{id}` | GET/PUT/DELETE | 合集详情/更新/删除 |
| `/api/collection/{id}/contents` | GET | 获取合集内容 |

### 文件服务

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/files/thumbnail/{filename}` | GET | 获取缩略图 |
| `/api/files/supported-formats` | GET | 支持的文件格式 |

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
    meta JSONB,                -- 元数据 (JSON格式)
    created_by VARCHAR,        -- 创建者
    created_at TIMESTAMP,      -- 创建时间
    updated_at TIMESTAMP       -- 更新时间
);
```

### Category (分类表)

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

### Collection (合集表)

```sql
CREATE TABLE collections (
    id UUID PRIMARY KEY,
    user_id UUID,              -- 用户ID
    name VARCHAR NOT NULL,     -- 合集名称
    description TEXT,          -- 描述
    keywords TEXT[],           -- 关键词数组
    created_at TIMESTAMP
);
```

### QA History (问答历史)

```sql
CREATE TABLE qa_history (
    id UUID PRIMARY KEY,
    session_id VARCHAR,        -- 会话ID
    question TEXT NOT NULL,    -- 用户问题
    answer TEXT,               -- AI回答
    sources JSONB,             -- 引用来源
    model VARCHAR,             -- 使用的模型
    created_at TIMESTAMP
);
```

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
│   │   │   └── files.py    # 文件服务
│   │   ├── services/       # 业务逻辑服务
│   │   ├── workers/        # Celery 异步任务
│   │   ├── models.py       # 数据模型
│   │   └── main.py         # 应用入口
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # 前端界面 (React)
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API 服务
│   │   └── types/          # TypeScript 类型
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
```

### 技术栈

#### 后端技术
- **FastAPI** - 现代化 Python Web 框架
- **PostgreSQL + pgvector** - 数据库和向量存储
- **Celery + Redis** - 异步任务处理
- **SQLAlchemy** - ORM 数据库操作
- **Pydantic** - 数据验证和序列化

#### 前端技术
- **React 19** - 用户界面框架
- **TypeScript** - 类型安全的 JavaScript
- **Ant Design** - UI 组件库
- **Vite** - 现代化构建工具
- **React Query** - 数据获取和缓存

## 🎯 当前功能状态

### ✅ 已实现功能

- **🤖 AI 智能问答** - 基于 GPT-4o 的智能问答系统
- **🔍 多模态搜索** - 关键词、语义、混合搜索
- **📁 文件上传处理** - 支持多种格式的文件上传
- **🏷️ 自动分类** - AI 驱动的内容自动分类
- **📚 合集管理** - 用户自定义知识合集
- **🎯 缩略图生成** - 图片文件缩略图自动生成
- **🌐 现代化界面** - React + Ant Design Web 界面
- **🐳 容器化部署** - Docker 一键部署
- **📊 向量存储** - PostgreSQL + pgvector 向量数据库

### 🔄 部署方式

- **本地部署** - 支持 Docker Compose 本地部署
- **云端部署** - 支持 Vercel + 云服务器部署
- **自动更新** - GitHub 集成的自动部署脚本

### 📈 性能特点

- **异步处理** - Celery 任务队列处理大文件
- **智能缓存** - Redis 缓存提升响应速度
- **批量操作** - 支持多文件批量上传和处理
- **实时反馈** - WebSocket 实时任务状态更新

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。


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