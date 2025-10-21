# PKB (Personal Knowledge Base) 系统架构文档

## 🏗️ 系统总览

PKB 是一个基于 AI 的个人知识库系统，采用前后端分离架构，拥有独立的用户认证系统，支持多源数据集成、智能分类、语义搜索和 AI 问答功能。

## 📊 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户访问层                                │
├─────────────────────────────────────────────────────────────────┤
│  🌐 https://pkb-poc.kmchat.cloud (前端界面)                     │
│  🔗 https://pkb.kmchat.cloud (后端 API)                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (Vercel)                          │
├─────────────────────────────────────────────────────────────────┤
│  📱 React + TypeScript + Vite                                  │
│  🎨 Ant Design UI 组件库                                       │
│  🔄 Axios HTTP 客户端                                          │
│  📦 自动部署：GitHub → Vercel                                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ HTTPS API 调用
┌─────────────────────────────────────────────────────────────────┐
│                      后端层 (AWS EC2)                           │
├─────────────────────────────────────────────────────────────────┤
│  🐍 FastAPI (Python)                                           │
│  🔀 CORS 跨域支持                                              │
│  📝 RESTful API 设计                                           │
│  🐳 Docker 容器化部署                                          │
│  🔄 手动部署：GitHub → EC2 Docker                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        服务层                                   │
├─────────────────────────────────────────────────────────────────┤
│  🤖 AI 服务 (Turing API)                                       │
│  │  ├── GPT-4o-mini (文本分析、问答)                           │
│  │  ├── GPT-4V (图像内容提取)                                  │
│  │  └── text-embedding-3-small (向量化)                       │
│  │                                                             │
│  ⚡ 异步任务队列 (Celery + Redis)                               │
│  │  ├── 快速队列：图像解析、快速分类                            │
│  │  ├── 分类队列：AI 智能分类                                  │
│  │  └── 重型队列：向量化、复杂处理                              │
│  │                                                             │
│  🔐 用户认证服务 (PKB 原生)                                    │
│  │  ├── JWT Token 管理                                        │
│  │  ├── OAuth 第三方登录                                      │
│  │  └── 用户权限控制                                          │
│  │                                                             │
│  ☁️ 多源数据集成                                               │
│  │  ├── Nextcloud WebDAV (可选)                               │
│  │  ├── WebUI 文件上传                                        │
│  │  └── 其他云盘集成 (未来)                                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据层                                   │
├─────────────────────────────────────────────────────────────────┤
│  🗄️ PostgreSQL + pgvector                                      │
│  │  ├── 用户账号和认证信息                                     │
│  │  ├── 文档元数据存储                                         │
│  │  ├── 向量索引 (语义搜索)                                    │
│  │  ├── 数据源集成配置                                         │
│  │  └── 用户自定义分类                                         │
│  │                                                             │
│  🚀 Redis                                                      │
│  │  ├── 缓存层                                                │
│  │  ├── 任务队列                                              │
│  │  └── 会话存储                                              │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 部署架构

### 前端部署 (Vercel)
```
开发环境 → GitHub → Vercel → CDN → 用户
    ↓         ↓        ↓       ↓
  本地开发   代码仓库  自动构建  全球分发
```

### 后端部署 (AWS EC2)
```
开发环境 → GitHub → EC2 Server → Docker → 用户
    ↓         ↓         ↓         ↓
  本地开发   代码仓库   手动更新   容器运行
```

## 🔐 用户认证架构

### 认证系统设计

PKB 采用**独立的用户认证系统**，不依赖任何外部服务，同时支持多种登录方式和数据源集成。

```
┌─────────────────────────────────────────────────────────────────┐
│                    PKB 认证系统架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔐 认证层                                                      │
│  ├── 📧 邮箱密码认证 (主要方式)                                 │
│  ├── 🔗 OAuth 第三方登录                                       │
│  │   ├── Google OAuth 2.0                                     │
│  │   ├── GitHub OAuth                                         │
│  │   └── 微信扫码登录                                          │
│  └── 🎫 JWT Token 管理                                         │
│                                                                 │
│  👤 用户管理层                                                  │
│  ├── 🗄️ 用户信息存储 (PostgreSQL)                              │
│  ├── 🔒 权限控制系统                                           │
│  ├── 📊 用户偏好设置                                           │
│  └── 🔄 多设备会话管理                                         │
│                                                                 │
│  🔌 数据源集成层                                               │
│  ├── ☁️ Nextcloud 集成 (可选)                                  │
│  ├── 📁 Google Drive (规划中)                                  │
│  ├── 📦 Dropbox (规划中)                                       │
│  └── 🗂️ OneDrive (规划中)                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 用户数据隔离

```
用户 A 的数据空间
├── 📄 个人文档库
├── 🏷️ 自定义分类
├── 💬 问答历史
├── ⚙️ 集成配置
└── 🔒 完全隔离

用户 B 的数据空间  
├── 📄 个人文档库
├── 🏷️ 自定义分类
├── 💬 问答历史
├── ⚙️ 集成配置
└── 🔒 完全隔离
```

### 产品定位策略

**PKB 是主产品，外部服务是可选增强**

- **核心价值**：AI 智能知识库 + 现代化界面
- **差异化**：不是文件管理，而是知识管理
- **用户路径**：
  1. 用户首先体验 PKB 的 AI 问答和智能搜索
  2. 如果需要多设备文件同步，可选择集成 Nextcloud
  3. 如果不需要，直接使用 WebUI 上传即可

## 🔄 CI/CD 流程

### 前端自动化部署
1. **开发** → 本地修改代码
2. **提交** → `git push origin main`
3. **触发** → Vercel 自动检测 GitHub 变更
4. **构建** → 自动执行 `pnpm build`
5. **部署** → 自动发布到 `https://pkb-poc.kmchat.cloud`
6. **通知** → Vercel Dashboard 显示部署状态

### 后端半自动化部署
1. **开发** → 本地修改代码
2. **提交** → `git push origin main`
3. **更新** → 服务器执行 `./update-pkb.sh` 或手动更新
4. **重启** → Docker 容器重启
5. **验证** → 健康检查确认服务正常

## 🌐 域名架构

### 统一域名策略
- **主域名**: `kmchat.cloud`
- **前端**: `pkb-poc.kmchat.cloud` (Vercel)
- **后端**: `pkb.kmchat.cloud` (EC2)
- **文件存储**: `nextcloud.kmchat.cloud` (Nextcloud)
- **知识库**: `kb.kmchat.cloud` (MaxKB)

### DNS 配置
```
pkb-poc.kmchat.cloud → CNAME → e4b4e65b79bc2aef.vercel-dns-017.com
pkb.kmchat.cloud → A → [EC2 IP]
nextcloud.kmchat.cloud → A → [EC2 IP]
```

## 🔧 技术栈详情

### 前端技术栈
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 库**: Ant Design
- **HTTP 客户端**: Axios
- **状态管理**: React Hooks
- **部署平台**: Vercel

### 后端技术栈
- **框架**: FastAPI (Python)
- **数据库**: PostgreSQL + pgvector
- **缓存**: Redis
- **任务队列**: Celery
- **容器化**: Docker + Docker Compose
- **部署平台**: AWS EC2

### AI 服务
- **LLM**: GPT-4o-mini (Turing API)
- **视觉模型**: GPT-4V
- **嵌入模型**: text-embedding-3-small
- **向量搜索**: pgvector

## 📁 项目结构

```
pkb-poc/
├── frontend/                 # 前端代码
│   ├── src/
│   │   ├── components/       # React 组件
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API 服务
│   │   └── types/           # TypeScript 类型
│   ├── package.json
│   └── vercel.json          # Vercel 配置
│
├── backend/                  # 后端代码
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── services/        # 业务逻辑
│   │   ├── models/          # 数据模型
│   │   └── workers/         # Celery 任务
│   ├── Dockerfile
│   └── requirements.txt
│
├── deploy/                   # 部署配置
│   ├── docker-compose.cloud.yml
│   ├── update-pkb.sh        # 更新脚本
│   └── *.sh                 # 各种部署脚本
│
└── README.md
```

## 🔐 安全配置

### CORS 策略
```python
allow_origins=[
    "https://pkb.kmchat.cloud",
    "https://pkb-poc.kmchat.cloud",
    "https://nextcloud.kmchat.cloud",
]
```

### SSL/TLS
- **前端**: Vercel 自动 SSL
- **后端**: 需要配置 SSL 证书 (Let's Encrypt)

## 📊 性能优化

### 前端优化
- **CDN**: Vercel 全球 CDN
- **缓存**: 浏览器缓存 + CDN 缓存
- **压缩**: Gzip/Brotli 压缩
- **懒加载**: 组件按需加载

### 后端优化
- **数据库**: 索引优化 + 连接池
- **缓存**: Redis 缓存热点数据
- **异步**: Celery 异步任务处理
- **容器**: Docker 资源限制

## 🔄 开发工作流

### 日常开发流程
1. **本地开发**
   ```bash
   # 前端
   cd frontend && pnpm dev
   
   # 后端
   cd backend && python -m uvicorn app.main:app --reload
   ```

2. **代码提交**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin main
   ```

3. **部署更新**
   - **前端**: Vercel 自动部署 (2-3分钟)
   - **后端**: 服务器执行 `./update-pkb.sh`

### 分支策略
- **main**: 生产环境分支
- **develop**: 开发分支 (可选)
- **feature/***: 功能分支 (可选)

## 🚨 监控与维护

### 健康检查
- **前端**: Vercel 自动监控
- **后端**: Docker 健康检查 + 手动监控

### 日志管理
```bash
# 查看后端日志
docker-compose -f deploy/docker-compose.cloud.yml logs -f pkb-backend

# 查看任务队列日志
docker-compose -f deploy/docker-compose.cloud.yml logs -f pkb-worker-quick
```

### 备份策略
- **数据库**: 定期备份 PostgreSQL
- **文件**: Nextcloud 文件备份
- **配置**: Git 版本控制

## 🎯 扩展规划

### 水平扩展
- **前端**: Vercel 自动扩展
- **后端**: 多实例 + 负载均衡
- **数据库**: 读写分离 + 分片

### 功能扩展
- **多用户支持**: 用户认证 + 权限管理
- **API 限流**: 防止滥用
- **实时通知**: WebSocket 支持
- **移动端**: React Native 或 PWA

## 📞 联系信息

- **项目仓库**: https://github.com/Kevincyq/pkb-poc
- **前端地址**: https://pkb-poc.kmchat.cloud
- **后端 API**: https://pkb.kmchat.cloud/api
- **API 文档**: https://pkb.kmchat.cloud/api/docs

---

*最后更新: 2025年9月30日*
