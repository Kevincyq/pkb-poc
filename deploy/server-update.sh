#!/bin/bash

# PKB 服务器端更新脚本
# 用于从 GitHub 拉取最新代码并更新部署

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置
DEPLOY_DIR="/home/ec2-user/pkb-new"
BRANCH="main"

echo "🔄 PKB 服务器端更新脚本"
echo "========================="
echo ""

# 检查部署目录
if [ ! -d "$DEPLOY_DIR" ]; then
    log_error "部署目录不存在: $DEPLOY_DIR"
    exit 1
fi

cd "$DEPLOY_DIR"

# 检查是否是 Git 仓库
if [ ! -d ".git" ]; then
    log_error "不是 Git 仓库: $DEPLOY_DIR"
    exit 1
fi

log_info "当前目录: $(pwd)"
log_info "当前分支: $(git branch --show-current)"

# 显示当前版本
CURRENT_COMMIT=$(git rev-parse --short HEAD)
log_info "当前版本: $CURRENT_COMMIT"

# 检查远程更新
log_info "检查远程更新..."
git fetch origin

REMOTE_COMMIT=$(git rev-parse --short "origin/$BRANCH")
log_info "远程版本: $REMOTE_COMMIT"

if [ "$CURRENT_COMMIT" = "$REMOTE_COMMIT" ]; then
    log_success "已是最新版本，无需更新"
    exit 0
fi

# 显示将要更新的内容
echo ""
log_info "将要更新的提交:"
git log --oneline "$CURRENT_COMMIT..$REMOTE_COMMIT"
echo ""

# 确认更新
read -p "确认更新到最新版本？(y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    log_info "更新已取消"
    exit 0
fi

# 备份当前版本信息
echo "$CURRENT_COMMIT" > ".last_version_backup"

# 拉取最新代码
log_info "拉取最新代码..."
git pull origin "$BRANCH"

NEW_COMMIT=$(git rev-parse --short HEAD)
log_success "代码更新完成: $CURRENT_COMMIT -> $NEW_COMMIT"

# 检查是否需要重新构建
NEED_REBUILD=false

# 检查后端代码变化
if git diff --name-only "$CURRENT_COMMIT" HEAD | grep -E "^backend/|requirements.txt|Dockerfile" > /dev/null; then
    log_info "检测到后端代码变化，需要重新构建"
    NEED_REBUILD=true
fi

# 检查前端代码变化
if git diff --name-only "$CURRENT_COMMIT" HEAD | grep -E "^frontend/|package.json" > /dev/null; then
    log_info "检测到前端代码变化，需要重新构建"
    NEED_REBUILD=true
fi

# 检查 Docker 配置变化
if git diff --name-only "$CURRENT_COMMIT" HEAD | grep -E "docker-compose|Dockerfile" > /dev/null; then
    log_info "检测到 Docker 配置变化，需要重新构建"
    NEED_REBUILD=true
fi

# 进入 deploy 目录
cd deploy

# 更新服务
if [ "$NEED_REBUILD" = true ]; then
    log_info "重新构建并启动服务..."
    docker-compose -f docker-compose.cloud.yml up -d --build
else
    log_info "重启服务..."
    docker-compose -f docker-compose.cloud.yml up -d
fi

# 等待服务启动
log_info "等待服务启动..."
sleep 30

# 健康检查
log_info "执行健康检查..."
max_attempts=10
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8002/api/health | grep -q '"status":"ok"'; then
        log_success "✅ 健康检查通过"
        break
    fi
    
    log_info "健康检查失败，重试 ($attempt/$max_attempts)..."
    sleep 10
    ((attempt++))
done

if [ $attempt -gt $max_attempts ]; then
    log_error "❌ 健康检查失败，可能需要回滚"
    echo ""
    echo "🔧 故障排除："
    echo "1. 查看日志: docker-compose logs pkb-backend"
    echo "2. 检查服务: docker-compose ps"
    echo "3. 回滚版本: git reset --hard $CURRENT_COMMIT && docker-compose up -d --build"
    exit 1
fi

# 显示更新结果
echo ""
log_success "🎉 更新完成！"
echo ""
echo "📋 更新信息："
echo "  • 版本: $CURRENT_COMMIT -> $NEW_COMMIT"
echo "  • 分支: $BRANCH"
echo "  • 时间: $(date)"
echo ""
echo "📊 服务状态："
docker-compose ps
echo ""
echo "🌐 访问地址："
echo "  • API 文档: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8002/api/docs"
echo "  • 健康检查: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8002/api/health"
echo ""

# 清理备份
rm -f .last_version_backup

log_success "更新流程完成！"
