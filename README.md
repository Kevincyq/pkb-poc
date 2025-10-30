# PKB - Personal Knowledge Base

> 🧠 智能个人知识库系统 - 集成 AI 问答、多模态搜索、自动分类的现代化知识管理平台

## 🌟 核心功能

### 用户功能
- **🔐 用户登录/登出** - 支持账号密码和Google OAuth登录
- **📤 文件上传** - 支持txt、md、pdf文档和jpg、png等图片，单文件最大20MB
- **🤖 AI智能解析** - 自动解析文件内容，生成文档摘要
- **🏷️ 智能双层分类** - 快速分类（2秒响应）+ AI精确分类（多标签分层级）
- **☁️ 云盘集成** - 支持NextCloud和Google Drive授权、文件上传
- **🔍 关键词搜索** - 全文搜索知识库内容
- **💬 知识问答** - 基于知识库内容的AI问答，支持多轮对话

### 技术特性
- **🎯 智能预览** - 图片缩略图生成、文档内容预览
- **⚡ 异步处理** - Celery任务队列处理大文件和批量操作
- **🌐 响应式界面** - React + TypeScript现代化Web界面
- **🐳 容器化部署** - Docker Compose一键部署

## 🏗️ 系统架构

```
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│   React Frontend     │    │   PKB Backend        │    │   PostgreSQL         │
│   (TypeScript)       │◄──►│   (FastAPI)          │◄──►│  (数据+向量存储)     │
│   - 用户认证         │    │   - API路由           │    │  - contents表        │
│   - 文件上传         │    │   - 业务逻辑         │    │  - chunks表          │
│   - 搜索/问答        │    │   - 用户隔离         │    │  - categories表      │
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘
                                       │                         │
         ┌─────────────────┐           │              ┌──────────────────────┐
         │  Google Drive   │           │              │    Celery Workers     │
         │  Nextcloud      │◄──────────┼─────────────►│  - 文件解析           │
         │  (云存储)        │           │              │  - AI分类            │
         └─────────────────┘           │              │  - 向量生成          │
                                       │              └──────────────────────┘
                             ┌──────────────────────┐     ┌──────────────────────┐
                             │   Turing API         │     │   Redis              │
                             │  (GPT-4o/Embedding)  │     │  (缓存+消息队列)      │
                             └──────────────────────┘     └──────────────────────┘
```

详细架构说明请查看 [项目架构说明.md](./项目架构说明.md)

## 🚀 快速开始

### 环境要求
- Docker & Docker Compose
- 4GB+ 内存 (推荐 8GB)
- 20GB+ 磁盘空间

### 部署步骤

```bash
# 1. 克隆项目
git clone https://github.com/Kevincyq/pkb-poc.git
cd pkb-poc

# 2. 配置环境变量
cd deploy
cp .env.template .env
# 编辑 .env 文件，配置必要的环境变量

# 3. 启动服务
docker compose -f docker-compose.cloud.yml up -d

# 4. 验证部署
# 访问 Web 界面: http://localhost:3000
# 访问 API 文档: http://localhost:8002/api/docs
```

### 核心环境变量配置

```env
# AI 服务配置 (必需)
TURING_API_KEY=your_turing_api_key
TURING_BASE_URL=https://api.turing.com/v1
QA_MODEL=turing/gpt-4o-mini

# 数据库配置
POSTGRES_HOST=postgres
POSTGRES_DB=pkb
POSTGRES_USER=pkb
POSTGRES_PASSWORD=your_password

# Redis 配置
REDIS_URL=redis://redis:6379/0

# Google OAuth (可选)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_FIREBASE_API_KEY=your_firebase_key

# NextCloud (可选)
NC_WEBDAV_URL=https://your-nextcloud.com/remote.php/dav/files/your_username/PKB-Inbox
NC_USER=your_username
NC_PASS=your_password
NC_SCAN_ENABLED=false  # 定期扫描开关
```

## 📁 项目结构

```
pkb-poc/
├── backend/                 # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/           # API路由模块
│   │   │   ├── auth.py    # 用户认证
│   │   │   ├── search.py  # 搜索接口
│   │   │   ├── qa.py      # AI问答接口
│   │   │   ├── category.py # 分类管理
│   │   │   ├── collection.py # 合集管理
│   │   │   ├── ingest.py  # 内容摄取
│   │   │   ├── files.py   # 文件服务
│   │   │   └── document.py # 文档处理
│   │   ├── services/      # 业务逻辑服务
│   │   ├── workers/       # Celery异步任务
│   │   ├── adapters/      # 外部服务适配器
│   │   ├── connectors/    # 云存储连接器
│   │   ├── parsers/       # 文档解析器
│   │   └── models.py      # 数据模型
│   ├── migrations/        # 数据库迁移脚本
│   └── requirements.txt   # Python依赖
├── frontend/               # 前端应用 (React + TypeScript)
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── pages/         # 页面组件
│   │   ├── services/     # API服务
│   │   ├── stores/        # 状态管理
│   │   └── utils/         # 工具函数
│   └── package.json       # 依赖配置
├── deploy/                 # 部署配置
│   ├── docker-compose.yml
│   └── .env.template
└── README.md              # 本文件
```

## 🔧 API 接口核心端点

### 认证 (`/api/auth`)
- `POST /api/auth/login` - 账号密码登录
- `GET /api/auth/google` - Google OAuth登录
- `GET /api/auth/callback/gdrive` - Google Drive回调
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/register-google` - 注册Google用户
- `POST /api/auth/logout` - 登出
- `GET /api/cloud/providers` - 获取云存储提供商列表
- `GET /api/cloud/status` - 获取云存储状态

### 搜索 (`/api/search`)
- `GET /api/search` - 多模态搜索（支持关键词、语义、混合搜索）
  - 查询参数：`q`, `top_k`, `search_type`, `modality`, `category`, `categories`, `collections`, `role`, `source`, `confidence_min`, `confidence_max`
- `GET /api/search/suggestions` - 搜索建议
- `GET /api/search/category/{category_id}` - 按分类搜索
- `GET /api/search/categories/stats` - 获取分类统计信息
- `GET /api/search/health` - 搜索服务健康检查

### 问答 (`/api/qa`)
- `POST /api/qa/ask` - AI问答（支持多轮对话、合集范围限制）
- `GET /api/qa/history` - 获取问答历史
- `POST /api/qa/generate-report` - 生成报告
- `POST /api/qa/feedback` - 提交问答反馈
- `GET /api/qa/sessions` - 获取会话列表
- `GET /api/qa/test` - 问答服务测试

### 文件上传 (`/api/ingest`)
- `POST /api/ingest/upload` - 单文件上传（WebUI）
- `POST /api/ingest/upload-multiple` - 批量上传
- `POST /api/ingest/upload-smart` - 智能上传（自动识别类型）
- `POST /api/ingest/scan` - 扫描NextCloud WebDAV
- `POST /api/ingest/memo` - 创建备忘录
- `POST /api/ingest/file` - 文件上传接口（兼容旧版）
- `GET /api/ingest/status/{content_id}` - 查询文件处理状态
- `GET /api/ingest/storage-config` - 获取存储配置
- `POST /api/ingest/storage-config` - 更新存储配置

### 分类管理 (`/api/category`)
- `GET /api/category/` - 获取分类列表（支持统计信息）
- `POST /api/category/classify` - AI分类单个内容
- `POST /api/category/classify/batch` - 批量分类内容
- `GET /api/category/{category_id}` - 获取分类详情
- `POST /api/category/custom` - 创建自定义分类
- `PUT /api/category/{category_id}` - 更新分类
- `DELETE /api/category/{category_id}` - 删除分类
- `POST /api/category/reclassify/all` - 重新分类所有内容
- `GET /api/category/content/{content_id}/status` - 获取内容分类状态
- `GET /api/category/stats/overview` - 获取分类统计概览
- `GET /api/category/service/status` - 获取分类服务状态
- `POST /api/category/initialize` - 初始化分类（已弃用，使用initialize-system-categories）
- `POST /api/category/initialize-system-categories` - 初始化系统分类

### 合集管理 (`/api/collection`)
- `GET /api/collection/` - 获取合集列表
- `POST /api/collection/` - 创建合集
- `GET /api/collection/{collection_id}` - 获取合集详情
- `PUT /api/collection/{collection_id}` - 更新合集
- `DELETE /api/collection/{collection_id}` - 删除合集
- `GET /api/collection/{collection_id}/contents` - 获取合集内容
- `POST /api/collection/match-all-documents` - 匹配所有文档到合集
- `POST /api/collection/fix-missing-rules` - 修复缺失的匹配规则
- `POST /api/collection/fix-collection-data` - 修复合集数据

### 文档管理 (`/api/document`)
- `GET /api/document/list` - 获取文档列表
- `GET /api/document/{content_id}` - 获取文档详情
- `DELETE /api/document/{content_id}` - 删除文档
- `GET /api/document/chunks` - 获取文档块列表
- `GET /api/document/stats` - 获取文档统计信息
- `GET /api/document/validate/{filename}` - 验证文件格式
- `GET /api/document/formats` - 获取支持的文件格式
- `POST /api/document/parse-text` - 解析文本内容
- `GET /api/document/deleted-records` - 获取已删除记录
- `DELETE /api/document/deleted-records/{record_id}` - 永久删除记录

### 文件服务 (`/api/files`, `/api/files_improved`)
- `GET /api/files/{filename}` - 获取文件（支持中文文件名）
- `GET /api/files/raw/{filename}` - 获取原始文件
- `GET /api/files/thumbnail/{filename}` - 获取缩略图
- `POST /api/files/pregenerate-thumbnail` - 预生成缩略图
- `POST /api/files/batch-pregenerate-thumbnails` - 批量预生成缩略图
- `GET /api/files/thumbnails/stats` - 获取缩略图统计
- `DELETE /api/files/thumbnails/cleanup` - 清理缩略图
- `GET /api/files/list-uploads` - 列出上传的文件
- `GET /api/files/list-database-files` - 列出数据库中的文件
- `GET /api/files/check-upload-config` - 检查上传配置
- `GET /api/files/debug/{filename}` - 调试文件路径

### 向量化 (`/api/embedding`)
- `GET /api/embedding/info` - 获取向量化服务信息
- `GET /api/embedding/health` - 向量化服务健康检查
- `POST /api/embedding/embed` - 生成向量嵌入
- `POST /api/embedding/embed/batch` - 批量生成向量嵌入
- `POST /api/embedding/similarity` - 计算向量相似度
- `GET /api/embedding/models` - 获取支持的模型列表
- `GET /api/embedding/test` - 测试向量化服务

### 智能代理 (`/api/agent`)
- `POST /api/agent/execute` - 执行智能代理任务
- `GET /api/agent/tasks/{task_id}` - 获取任务状态
- `POST /api/agent/plan` - 创建任务计划
- `GET /api/agent/tools` - 获取可用工具列表
- `POST /api/agent/mcp/register` - 注册MCP工具
- `POST /api/agent/mcp/call` - 调用MCP工具
- `GET /api/agent/mcp/tools` - 获取MCP工具列表
- `POST /api/agent/mcp/tools/{tool_name}/enable` - 启用MCP工具
- `POST /api/agent/mcp/tools/{tool_name}/disable` - 禁用MCP工具
- `POST /api/agent/mcp/initialize` - 初始化MCP

### 运维 (`/api/operator`)
- `POST /api/operator/commit` - 提交操作日志

### 健康检查
- `GET /api/health` - 服务健康检查

---

**📚 详细API文档（Swagger UI）**: `http://localhost:8002/api/docs`  
**📄 OpenAPI规范**: `http://localhost:8002/api/openapi.json`

## 📚 关键业务逻辑

### 用户隔离机制
- 所有数据通过 `user_id` 隔离
- JWT token验证用户身份
- 搜索、问答、分类都基于用户数据

### 文件处理流程（双层分类架构）
1. 用户上传文件 → 保存到本地/云盘
2. 创建Content记录 → 设置初始状态
3. **文件解析阶段**（0.1秒）
   - DocumentProcessor统一处理（自动检测文件类型）
   - 智能分块（基于行边界，700字符/块）
   - 生成Chunk记录
4. **向量化阶段**（0.5秒，异步）
   - 生成向量嵌入（1536维）
   - 存储到数据库
5. **快速分类阶段**（2秒）⭐
   - 基于规则的启发式分类（关键词+文件名+扩展名）
   - 立即显示给用户
   - 置信度：0.4-0.8
6. **AI精确分类阶段**（4秒）⭐⭐
   - 使用GPT-4o-mini进行多标签分类
   - 支持主分类和次要分类
   - 覆盖快速分类结果
   - 置信度：0.3-1.0
7. 匹配到合集 → 自动关联（10秒）

### 搜索机制
- **关键词搜索**: PostgreSQL全文搜索
- **语义搜索**: 向量相似度匹配（pgvector）
- **混合搜索**: 合并两种结果，智能去重（文档级别）
- **动态相似度阈值**: 根据查询内容自动调整
- **文件类型智能过滤**: 基于查询意图过滤结果

### 问答机制
- **RAG检索**: 先搜索相关内容
- **上下文构建**: 文档级去重，保留最高分chunk
- **AI生成**: 基于上下文生成答案
- **来源引用**: 标注答案来源和置信度

## 🛠️ 技术栈

### 后端
- FastAPI - Web框架
- PostgreSQL + pgvector - 数据库和向量存储
- Celery + Redis - 异步任务
- SQLAlchemy - ORM
- OpenAI API - AI服务

### 前端
- React 18 - UI框架
- TypeScript - 类型安全
- Vite - 构建工具
- Axios - HTTP客户端
- Ant Design - UI组件库(部分)

## 🎯 核心算法创新点

### 双层分类架构
- **快速分类**：2秒响应，基于规则匹配，提供即时用户体验
- **AI精确分类**：4秒后完成，多标签分类，提升准确性
- **时序协同**：快速分类→AI分类的顺序执行和结果覆盖机制

### 多标签分层级分类系统
- **层级区分**：role字段（primary_system/secondary_system/user_rule）明确区分主次分类
- **来源追踪**：source字段（ml/heuristic/rule/manual）记录分类来源
- **置信度驱动**：基于置信度决定分类的创建、显示和更新


## 📞 技术支持

- GitHub Issues: https://github.com/Kevincyq/pkb-poc/issues
- 在线演示: https://pkb-poc.kmchat.cloud
- 技术支持: kevincyq@gmail.com

