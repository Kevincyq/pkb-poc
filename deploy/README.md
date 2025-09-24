# PKB 项目部署指南

## 🚀 快速开始

### 1. 环境准备
确保已安装：
- Docker
- Docker Compose

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp env.template .env

# 编辑配置文件，设置必要的 API Key
nano .env  # 或使用其他编辑器
```

**必须配置的变量**：
- `TURING_API_KEY`: 你的 Turing 平台 API Key
- `NC_PASS`: 你的 Nextcloud 密码

### 3. 部署服务

#### 首次部署或常规启动
```bash
./deploy.sh
```

#### 完全重置部署（清理所有数据）
```bash
./deploy.sh --reset
```

#### 强制执行（不询问确认）
```bash
./deploy.sh --force
./deploy.sh --reset --force
```

## 📋 部署脚本说明

### `deploy.sh` - 统一部署脚本

**功能**：
- ✅ 自动检查和创建 `.env` 文件
- ✅ 验证必要的环境变量
- ✅ 检查 Docker 环境
- ✅ 支持常规部署和重置部署两种模式
- ✅ 自动初始化数据库和扩展
- ✅ 提供详细的状态信息和测试命令

**使用方法**：
```bash
# 查看帮助
./deploy.sh --help

# 常规部署（推荐）
./deploy.sh

# 重置部署（清理所有数据，重新开始）
./deploy.sh --reset

# 强制执行（CI/CD 环境）
./deploy.sh --force
```

## 🌐 服务访问

部署完成后，可以访问：

- **PKB API 文档**: http://localhost:8002/api/docs
- **Embedding API**: http://localhost:8002/api/embedding/info
- **Nextcloud**: http://localhost:8080
- **MaxKB**: http://localhost:7861

## 🔧 常用操作

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f pkb-backend
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart pkb-backend
```

### 停止服务
```bash
docker-compose down
```

### 进入容器调试
```bash
# 进入后端容器
docker-compose exec pkb-backend bash

# 进入数据库容器
docker-compose exec postgres psql -U pkb -d pkb
```

## 🧪 测试验证

### API 健康检查
```bash
curl http://localhost:8002/api/health
curl http://localhost:8002/api/embedding/health
```

### 运行测试脚本
```bash
# 测试文档处理功能
docker-compose exec pkb-backend python test_document_processing.py

# 测试 Embedding 服务
docker-compose exec pkb-backend python test_embedding_service.py
```

### 测试文档摄取
```bash
# 测试手动添加备忘录
curl -X POST "http://localhost:8002/api/ingest/memo" \
  -H "Content-Type: application/json" \
  -d '{"title": "测试", "text": "这是一个测试文档"}'

# 测试 Nextcloud 扫描
curl -X POST "http://localhost:8002/api/ingest/scan"
```

## 🔒 安全注意事项

1. **`.env` 文件包含敏感信息**，不应提交到版本控制
2. **定期更新 API Key** 和密码
3. **生产环境**应使用更强的密码和 HTTPS
4. **防火墙配置**：只开放必要的端口

## 🆘 故障排除

### 常见问题

1. **端口冲突**：确保 8002、8080、7861 端口未被占用
2. **权限问题**：确保 Docker 有足够权限
3. **网络问题**：检查 Docker 网络配置
4. **内存不足**：确保系统有足够内存（建议 4GB+）

### 日志查看
```bash
# 查看启动错误
docker-compose logs pkb-backend

# 查看数据库日志
docker-compose logs postgres

# 查看 Celery 工作进程日志
docker-compose logs pkb-worker
```

### 完全重置
如果遇到无法解决的问题，可以完全重置：
```bash
./deploy.sh --reset --force
```

## 📞 支持

如有问题，请：
1. 查看日志文件
2. 检查环境变量配置
3. 确认 Docker 环境正常
4. 参考项目文档
