# PKB - Personal Knowledge Base

> 🧠 个人知识库系统 - 基于 Nextcloud + PostgreSQL 的轻量级知识管理解决方案

## 🌟 项目特色

- **📁 无缝文件同步** - 基于 Nextcloud WebDAV，支持多设备文件同步
- **🔍 智能搜索** - 多级搜索策略，支持精确匹配和模糊搜索
- **📝 灵活摄取** - 支持手动输入、文件扫描、批量导入
- **⚡ 异步处理** - Celery 任务队列，支持大文件和批量处理
- **🐳 容器化部署** - Docker Compose 一键部署，开箱即用
- **🔧 API 优先** - RESTful API 设计，易于集成和扩展

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nextcloud     │    │   PKB Backend   │    │   PostgreSQL    │
│  (文件同步)      │◄──►│   (API服务)      │◄──►│   (数据存储)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   Celery        │              │
         └──────────────►│  (异步任务)      │◄─────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │     Redis       │
                        │   (任务队列)     │
                        └─────────────────┘
```

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose
- 2GB+ 内存
- 10GB+ 磁盘空间

### 1. 克隆项目

```bash
git clone <repository-url>
cd pkb-poc
```

### 2. 配置环境变量

创建 `deploy/.env` 文件：

```bash
# Nextcloud WebDAV 配置
NC_WEBDAV_URL=https://nextcloud.kmchat.cloud/remote.php/dav/files/username/PKB-Inbox/
NC_USER=your_nextcloud_username
NC_PASS=your_nextcloud_password
NC_EXTS=.txt,.md,.pdf

# 数据库配置
POSTGRES_HOST=postgres
POSTGRES_DB=pkb
POSTGRES_USER=pkb
POSTGRES_PASSWORD=pkb

# Redis 配置
REDIS_URL=redis://redis:6379/0

# 可选：OpenAI API (用于未来的语义搜索)
# OPENAI_API_KEY=your_openai_api_key
```

### 3. 启动服务

```bash
cd deploy
docker-compose up -d
```

### 4. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 测试 API
curl "http://localhost:8002/api/health"

# 访问 API 文档
open http://localhost:8002/api/docs
```

## 📖 使用指南

### 文档摄取

#### 1. 手动添加备忘录

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

#### 2. 扫描 Nextcloud 文件

```bash
# 将文件上传到 Nextcloud 的 PKB-Inbox 文件夹
# 然后执行扫描
curl -X POST "http://localhost:8002/api/ingest/scan"
```

#### 3. 指定文件摄取

```bash
curl -X POST "http://localhost:8002/api/ingest/file" \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/document.txt"}'
```

### 搜索查询

#### 基础搜索

```bash
# 英文搜索
curl "http://localhost:8002/api/search/?q=docker&top_k=5"

# 中文搜索（需要 URL 编码）
curl -G "http://localhost:8002/api/search/" \
  --data-urlencode "q=学习笔记" \
  --data-urlencode "top_k=5"
```

#### 搜索结果格式

```json
{
  "query": "docker",
  "items": [
    {
      "score": 0.95,
      "text": "Docker 是一个开源的容器化平台...",
      "metadata": {"source_uri": "nextcloud://docker-notes.md"},
      "title": "Docker 学习笔记",
      "source_uri": "nextcloud://docker-notes.md"
    }
  ],
  "source": "database"
}
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

## 🔧 API 接口

### 摄取接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/ingest/memo` | POST | 添加备忘录 |
| `/api/ingest/scan` | POST | 扫描 Nextcloud 文件 |
| `/api/ingest/file` | POST | 摄取指定文件 |

### 搜索接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/search/` | GET | 文本搜索 |

### 系统接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/docs` | GET | API 文档 |

## 📊 数据模型

### Content (文档表)

```sql
CREATE TABLE contents (
    id UUID PRIMARY KEY,
    source_uri TEXT,           -- 来源URI
    modality VARCHAR,          -- 模态类型 (text/image/audio/pdf)
    title VARCHAR NOT NULL,    -- 文档标题
    text TEXT NOT NULL,        -- 文档内容
    meta JSON,                 -- 元数据
    created_by VARCHAR,        -- 创建者
    created_at TIMESTAMP       -- 创建时间
);
```

### Chunk (文本块表)

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    content_id UUID REFERENCES contents(id),
    seq INTEGER,               -- 序号
    text TEXT NOT NULL,        -- 文本块内容
    meta JSON,                 -- 元数据
    created_at TIMESTAMP       -- 创建时间
);
```

## 🔍 搜索策略

PKB 采用多级搜索策略，确保搜索结果的准确性和相关性：

1. **精确匹配** - 使用正则表达式进行精确匹配
2. **词边界匹配** - PostgreSQL 词边界匹配
3. **模糊匹配** - ILIKE 模式匹配
4. **相关性评分** - 基于匹配类型计算相关性分数

## 🛠️ 开发指南

### 项目结构

```
pkb-poc/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── adapters/       # 外部服务适配器
│   │   ├── workers/        # Celery 任务
│   │   ├── models.py       # 数据模型
│   │   └── main.py         # 应用入口
│   ├── Dockerfile
│   └── requirements.txt
├── deploy/                  # 部署配置
│   └── docker-compose.yml
└── README.md
```

### 添加新功能

1. **新增 API 端点**：在 `backend/app/api/` 下创建新的路由文件
2. **数据库迁移**：修改 `models.py` 并重启服务
3. **异步任务**：在 `workers/tasks.py` 中添加新任务
4. **外部集成**：在 `adapters/` 下创建适配器

### 本地开发

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 运行开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行 Celery Worker
celery -A app.workers.celery_app worker -l info
```

## 🚀 未来规划

### 短期目标 (1-2个月)

- [ ] **语义搜索** - 集成 OpenAI Embeddings 或本地向量模型
- [ ] **智能问答** - 基于检索的问答系统
- [ ] **Web 界面** - 简洁的管理界面
- [ ] **移动端 API** - 针对移动端优化的接口

### 中期目标 (3-6个月)

- [ ] **多模态支持** - 图片、音频、视频处理
- [ ] **自动标签** - AI 自动生成标签和分类
- [ ] **智能提醒** - 基于内容的智能提醒系统
- [ ] **知识图谱** - 文档间关系挖掘

### 长期目标 (6个月+)

- [ ] **Agent 系统** - 智能助手和任务自动化
- [ ] **协作功能** - 多用户知识共享
- [ ] **插件系统** - 第三方扩展支持
- [ ] **移动应用** - 原生移动端应用

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Nextcloud](https://nextcloud.com/) - 开源文件同步和共享平台
- [PostgreSQL](https://www.postgresql.org/) - 强大的开源关系数据库
- [Celery](https://docs.celeryproject.org/) - 分布式任务队列

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 创建 [Issue](../../issues)
- 发送邮件至：[your-email@example.com]

---

**PKB** - 让知识管理变得简单高效 🚀
