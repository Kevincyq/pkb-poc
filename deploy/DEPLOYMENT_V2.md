# PKB v2.0 部署指南

## 🚀 版本特性

PKB v2.0 引入了智能分类和合集功能，主要新特性包括：

- ✅ **智能文档分类**：4个预置分类（职场商务、生活点滴、学习成长、科技前沿）
- ✅ **GPT-4o-mini 图片识别**：支持图片内容提取和分类
- ✅ **快速预分类**：文件上传后几秒内显示初步分类
- ✅ **AI精确分类**：30秒后自动升级为AI精确分类
- ✅ **分类搜索问答**：支持按分类筛选的搜索和问答
- ✅ **文件删除同步**：自动清理已删除文件的数据库记录
- ✅ **多队列处理**：快速、分类、重型任务分离处理

## 📋 部署方案

### 方案1：现有服务升级（推荐）

如果您已经有 PKB 服务在运行，使用升级脚本：

```bash
# 1. 进入部署目录
cd /path/to/pkb-poc/deploy

# 2. 赋予执行权限
chmod +x upgrade_v2.sh

# 3. 执行升级
./upgrade_v2.sh
```

**升级流程：**
1. 自动备份现有数据和配置
2. 更新环境变量配置
3. 执行数据库迁移
4. 构建新版本镜像
5. 启动新的服务架构
6. 初始化系统分类
7. 执行健康检查

### 方案2：全新部署

如果是全新环境部署：

```bash
# 1. 克隆代码
git clone <your-repo> pkb-poc
cd pkb-poc/deploy

# 2. 赋予执行权限
chmod +x deploy_v2.sh

# 3. 执行部署
./deploy_v2.sh
```

## ⚙️ 服务架构

### 新的服务组件

| 服务名 | 功能 | 队列 | 并发数 |
|--------|------|------|--------|
| pkb-backend | API 服务 | - | - |
| pkb-worker-quick | 快速分类 | quick | 4 |
| pkb-worker-classify | AI分类 | classify | 2 |
| pkb-worker-heavy | 向量化等重型任务 | heavy, ingest | 2 |

### 队列优先级

- **quick队列**：优先级9，立即执行快速分类
- **classify队列**：优先级5，延迟30秒执行AI分类
- **heavy队列**：正常优先级，处理向量化等重型任务

## 🔧 环境配置

### 新增环境变量

在 `.env` 文件中添加以下配置：

```bash
# 智能分类模型配置
CLASSIFICATION_MODEL=turing/gpt-4o-mini
VISION_MODEL=turing/gpt-4o-mini
```

### 必要的环境变量

确保以下环境变量已正确配置：

```bash
# Turing API 配置（必须）
TURING_API_KEY=your_api_key
TURING_API_BASE=https://your-api-base/v1

# Nextcloud 配置（必须）
NC_WEBDAV_URL=https://your-nextcloud/remote.php/dav/files/user/PKB-Inbox
NC_USER=your_username
NC_PASS=your_password

# 数据库配置
DATABASE_URL=postgresql://pkb:pkb@postgres/pkb
REDIS_URL=redis://redis:6379/0
```

## 📊 数据库迁移

### 新增数据表

v2.0 版本新增以下数据表：

- `categories` - 分类表
- `content_categories` - 内容分类关联表
- `collections` - 智能合集表

### 迁移脚本

数据库迁移会自动执行，包括：

1. 创建新表结构
2. 添加索引优化
3. 初始化系统分类
4. 更新现有内容的 modality 字段

## 🔍 健康检查

### API 检查

```bash
# 基础健康检查
curl http://localhost:8002/api/health

# 分类服务状态
curl http://localhost:8002/api/category/service/status

# 获取分类列表
curl http://localhost:8002/api/category/
```

### 服务状态检查

```bash
# 查看所有服务状态
docker-compose ps

# 查看特定服务日志
docker-compose logs -f pkb-worker-quick
docker-compose logs -f pkb-worker-classify
docker-compose logs -f pkb-worker-heavy
```

## 🚨 故障排除

### 常见问题

1. **分类服务不可用**
   ```bash
   # 检查 API 密钥配置
   docker-compose logs pkb-backend | grep -i "turing"
   
   # 重启分类服务
   docker-compose restart pkb-worker-classify
   ```

2. **队列任务堆积**
   ```bash
   # 查看队列状态
   docker-compose exec redis redis-cli
   > KEYS celery*
   
   # 清空队列（谨慎使用）
   > FLUSHDB
   ```

3. **数据库连接问题**
   ```bash
   # 检查数据库状态
   docker-compose logs postgres
   
   # 手动连接测试
   docker-compose exec postgres psql -U pkb -d pkb
   ```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定时间段日志
docker-compose logs --since="1h" pkb-backend

# 查看错误日志
docker-compose logs | grep -i error
```

## 🔄 回滚方案

如果升级出现问题，可以回滚到之前版本：

```bash
# 1. 停止新服务
docker-compose down

# 2. 恢复备份的配置
cp backup/YYYYMMDD_HHMMSS/env_backup .env

# 3. 恢复数据库（如果需要）
docker-compose up -d postgres
docker-compose exec -T postgres psql -U pkb -d pkb < backup/YYYYMMDD_HHMMSS/database_backup.sql

# 4. 启动旧版本服务
# 使用旧版本的 docker-compose.yml
```

## 📈 性能优化

### 队列优化

根据实际负载调整并发数：

```yaml
# 高负载环境
pkb-worker-quick:
  command: ["bash","-lc","celery -A app.workers.celery_app worker -Q quick -l info --concurrency=8"]

pkb-worker-classify:
  command: ["bash","-lc","celery -A app.workers.celery_app worker -Q classify -l info --concurrency=4"]
```

### 资源限制

```yaml
# 添加资源限制
pkb-worker-classify:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '1.0'
```

## 🔐 安全建议

1. **API 密钥管理**
   - 使用环境变量存储敏感信息
   - 定期轮换 API 密钥
   - 限制 API 密钥权限

2. **网络安全**
   - 使用内部网络通信
   - 配置防火墙规则
   - 启用 HTTPS

3. **数据备份**
   - 定期备份数据库
   - 备份配置文件
   - 测试恢复流程

## 📞 技术支持

如遇到部署问题，请提供以下信息：

1. 部署环境信息（OS、Docker版本等）
2. 错误日志（`docker-compose logs`）
3. 服务状态（`docker-compose ps`）
4. 环境配置（隐藏敏感信息）

---

**部署完成后，您的 PKB 系统将具备强大的智能分类能力，为用户提供更好的知识管理体验！** 🎉
