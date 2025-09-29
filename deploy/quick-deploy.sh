#!/bin/bash

# PKB 快速部署脚本
# 一键从 GitHub 拉取并部署 PKB 服务

set -e

# 配置变量（请根据实际情况修改）
GITHUB_REPO="https://github.com/kevincyq/pkb-poc.git"  # 替换为你的仓库地址
BRANCH="main"
DEPLOY_DIR="/opt/pkb"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    error "请使用 root 权限运行: sudo $0"
fi

echo "🚀 PKB 快速部署开始..."
echo "仓库: $GITHUB_REPO"
echo "分支: $BRANCH"
echo "目标: $DEPLOY_DIR"
echo ""

# 安装依赖
log "检查并安装依赖..."
if ! command -v git &> /dev/null; then
    apt-get update && apt-get install -y git curl
fi

if ! command -v docker &> /dev/null; then
    error "请先安装 Docker: curl -fsSL https://get.docker.com | sh"
fi

if ! command -v docker-compose &> /dev/null; then
    error "请先安装 Docker Compose"
fi

# 停止现有服务
if [ -d "$DEPLOY_DIR" ]; then
    log "停止现有服务..."
    cd "$DEPLOY_DIR" && docker-compose down 2>/dev/null || true
fi

# 获取代码
log "获取最新代码..."
if [ -d "$DEPLOY_DIR" ]; then
    cd "$DEPLOY_DIR"
    git fetch && git reset --hard "origin/$BRANCH"
else
    git clone -b "$BRANCH" "$GITHUB_REPO" "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

# 配置环境
log "配置环境变量..."
if [ ! -f ".env" ]; then
    if [ -f "deploy/env.cloud.template" ]; then
        cp deploy/env.cloud.template .env
    elif [ -f "env.template" ]; then
        cp env.template .env
    else
        error "未找到环境变量模板"
    fi
    
    echo ""
    echo "⚠️  重要：请编辑 .env 文件配置以下必要参数："
    echo "   - TURING_API_KEY"
    echo "   - NC_WEBDAV_URL"
    echo "   - NC_USER"
    echo "   - NC_PASS"
    echo "   - POSTGRES_PASSWORD"
    echo ""
    read -p "按 Enter 继续（确保已配置 .env）..."
fi

# 使用云端配置
if [ -f "deploy/docker-compose.cloud.yml" ]; then
    log "使用云端部署配置..."
    cd deploy
    COMPOSE_FILE="-f docker-compose.cloud.yml"
else
    log "使用默认配置..."
    COMPOSE_FILE=""
fi

# 构建和启动
log "构建服务..."
docker-compose $COMPOSE_FILE build

log "启动基础服务..."
docker-compose $COMPOSE_FILE up -d postgres redis

log "等待数据库启动..."
sleep 30

log "初始化数据库..."
docker-compose $COMPOSE_FILE exec -T postgres psql -U pkb -d pkb -c "CREATE EXTENSION IF NOT EXISTS vector;" || true

log "启动所有服务..."
docker-compose $COMPOSE_FILE up -d

log "等待服务启动..."
sleep 60

# 健康检查
log "检查服务状态..."
if curl -s http://localhost:8002/api/health | grep -q '"status":"ok"'; then
    success "🎉 部署成功！"
    echo ""
    echo "📋 访问信息："
    echo "  • API 文档: http://localhost:8002/api/docs"
    echo "  • 健康检查: http://localhost:8002/api/health"
    echo ""
    echo "🔧 管理命令："
    echo "  • 查看状态: cd $DEPLOY_DIR && docker-compose ps"
    echo "  • 查看日志: cd $DEPLOY_DIR && docker-compose logs -f"
    echo "  • 重启服务: cd $DEPLOY_DIR && docker-compose restart"
    echo ""
else
    error "服务启动失败，请检查日志: cd $DEPLOY_DIR && docker-compose logs"
fi
