# PKB 云端部署指南

## 🚀 一键部署

### 快速部署（推荐）

```bash
# 1. 下载快速部署脚本
curl -fsSL https://raw.githubusercontent.com/kevincyq/pkb-poc/main/deploy/quick-deploy.sh -o quick-deploy.sh

# 2. 给予执行权限
chmod +x quick-deploy.sh

# 3. 运行部署
sudo ./quick-deploy.sh
```

### 完整部署

```bash
# 1. 下载完整部署脚本
curl -fsSL https://raw.githubusercontent.com/kevincyq/pkb-poc/main/deploy/deploy-from-github.sh -o deploy-from-github.sh

# 2. 给予执行权限
chmod +x deploy-from-github.sh

# 3. 运行部署（支持更多选项）
sudo ./deploy-from-github.sh
```

## 📋 部署前准备

### 1. 服务器要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **内存**: 最少 4GB，推荐 8GB+
- **存储**: 最少 20GB 可用空间
- **网络**: 能够访问 GitHub 和外部 API

### 2. 必需软件

```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git
sudo apt-get update && sudo apt-get install -y git curl
```

### 3. 环境配置

部署脚本会自动创建 `.env` 文件，你需要配置以下关键参数：

```bash
# Turing API 配置（必须）
TURING_API_KEY=your_turing_api_key_here

# Nextcloud WebDAV 配置（必须）
NC_WEBDAV_URL=https://your-nextcloud.com/remote.php/dav/files/username/PKB-Inbox
NC_USER=your_username
NC_PASS=your_password

# 数据库密码（建议修改）
POSTGRES_PASSWORD=pkb_secure_2024_change_me
```

## 🔧 部署选项

### 快速部署脚本选项

```bash
# 基础部署
sudo ./quick-deploy.sh

# 自定义仓库和分支
GITHUB_REPO="https://github.com/yourusername/pkb-poc.git" BRANCH="develop" sudo ./quick-deploy.sh
```

### 完整部署脚本选项

```bash
# 查看帮助
./deploy-from-github.sh --help

# 自定义仓库
./deploy-from-github.sh --repo https://github.com/yourusername/pkb-poc.git

# 指定分支
./deploy-from-github.sh --branch develop

# 强制重建
./deploy-from-github.sh --force-rebuild

# 跳过备份
./deploy-from-github.sh --skip-backup
```

## 📁 部署结构

```
/opt/pkb/                    # 主部署目录
├── backend/                 # 后端代码
├── deploy/                  # 部署配置
│   ├── docker-compose.yml  # Docker 配置
│   ├── .env                # 环境变量
│   └── logs/               # 日志目录
└── .git/                   # Git 仓库

/opt/pkb-backup/            # 备份目录
├── pkb-backup-20241201-120000/
└── pkb-backup-20241201-130000/
```

## 🌐 服务访问

部署完成后，服务将在以下端口运行：

- **PKB API**: http://localhost:8002
- **API 文档**: http://localhost:8002/api/docs
- **健康检查**: http://localhost:8002/api/health
- **Celery 监控**: http://localhost:5555 (可选)

## 🔧 管理命令

### 基本操作

```bash
# 进入部署目录
cd /opt/pkb

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码并重启
git pull && docker-compose up -d --build
```

### 服务管理

```bash
# 重启特定服务
docker-compose restart pkb-backend

# 查看特定服务日志
docker-compose logs -f pkb-backend

# 进入容器
docker-compose exec pkb-backend bash

# 查看资源使用
docker stats
```

### 数据库操作

```bash
# 连接数据库
docker-compose exec postgres psql -U pkb -d pkb

# 备份数据库
docker-compose exec postgres pg_dump -U pkb pkb > backup.sql

# 恢复数据库
docker-compose exec -T postgres psql -U pkb -d pkb < backup.sql
```

## 🔄 更新部署

### 自动更新

```bash
# 重新运行部署脚本即可
sudo ./quick-deploy.sh
```

### 手动更新

```bash
cd /opt/pkb
git pull
docker-compose build
docker-compose up -d
```

## 🛠️ 故障排除

### 常见问题

1. **端口占用**
   ```bash
   # 检查端口占用
   sudo netstat -tlnp | grep :8002
   
   # 修改端口
   echo "PKB_PORT=8003" >> .env
   docker-compose up -d
   ```

2. **内存不足**
   ```bash
   # 检查内存使用
   free -h
   
   # 减少 worker 并发数
   # 编辑 docker-compose.yml 中的 --concurrency 参数
   ```

3. **API 密钥错误**
   ```bash
   # 检查环境变量
   docker-compose exec pkb-backend env | grep TURING
   
   # 更新 .env 文件后重启
   docker-compose restart pkb-backend
   ```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs

# 查看最近的错误
docker-compose logs --tail=100 | grep ERROR

# 实时监控日志
docker-compose logs -f pkb-backend
```

### 健康检查

```bash
# API 健康检查
curl http://localhost:8002/api/health

# 数据库连接检查
docker-compose exec postgres pg_isready -U pkb

# Redis 连接检查
docker-compose exec redis redis-cli ping
```

## 🔒 安全建议

### 生产环境配置

1. **修改默认密码**
   ```bash
   # 生成强密码
   openssl rand -base64 32
   
   # 更新 .env 文件
   POSTGRES_PASSWORD=your_strong_password_here
   ```

2. **限制网络访问**
   ```bash
   # 只允许本地访问
   # 在 docker-compose.yml 中使用 127.0.0.1:8002:8000
   ```

3. **启用 HTTPS**
   ```bash
   # 使用 Nginx 反向代理
   # 配置 SSL 证书
   ```

4. **定期备份**
   ```bash
   # 添加到 crontab
   0 2 * * * cd /opt/pkb && docker-compose exec postgres pg_dump -U pkb pkb > /backup/pkb-$(date +\%Y\%m\%d).sql
   ```

## 📊 监控和维护

### 系统监控

```bash
# 查看系统资源
htop

# 查看磁盘使用
df -h

# 查看 Docker 资源使用
docker system df
```

### 日志轮转

```bash
# 配置 Docker 日志轮转
# 在 docker-compose.yml 中添加：
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 定期维护

```bash
# 清理 Docker 资源
docker system prune -f

# 清理旧镜像
docker image prune -f

# 更新系统
sudo apt-get update && sudo apt-get upgrade -y
```

## 📞 支持

如果遇到问题，请：

1. 查看日志：`docker-compose logs`
2. 检查配置：确认 `.env` 文件配置正确
3. 重启服务：`docker-compose restart`
4. 重新部署：重新运行部署脚本

更多信息请参考项目文档或提交 Issue。
