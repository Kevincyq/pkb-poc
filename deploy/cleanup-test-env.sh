#!/bin/bash

# PKB 测试环境清理脚本

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

DEPLOY_DIR="/home/ec2-user/pkb-test"
COMPOSE_PROJECT="pkb-test"

echo "🧹 PKB 测试环境清理脚本"
echo "========================="
echo ""

if [ ! -d "$DEPLOY_DIR" ]; then
    log_warning "测试环境目录不存在: $DEPLOY_DIR"
    exit 0
fi

cd "$DEPLOY_DIR"

# 获取当前部署信息
if [ -f "test_deployed_branch" ]; then
    CURRENT_BRANCH=$(cat test_deployed_branch)
    log_info "当前测试分支: $CURRENT_BRANCH"
fi

if [ -f "test_deployed_port" ]; then
    CURRENT_PORT=$(cat test_deployed_port)
    log_info "当前测试端口: $CURRENT_PORT"
fi

# 停止测试环境服务
log_info "停止测试环境服务..."
cd deploy
docker-compose -f docker-compose.test.yml -p $COMPOSE_PROJECT down

# 清理测试环境容器和镜像
log_info "清理测试环境容器..."
docker-compose -f docker-compose.test.yml -p $COMPOSE_PROJECT rm -f

# 可选：清理测试环境镜像
read -p "是否清理测试环境镜像? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "清理测试环境镜像..."
    docker images | grep pkb-test | awk '{print $3}' | xargs -r docker rmi
fi

# 可选：清理整个测试目录
read -p "是否删除整个测试环境目录? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_warning "删除测试环境目录: $DEPLOY_DIR"
    cd /
    rm -rf "$DEPLOY_DIR"
    log_success "测试环境目录已删除"
else
    # 只清理部署状态文件
    cd "$DEPLOY_DIR"
    rm -f test_deployed_branch test_deployed_port
    log_info "保留测试环境目录，清理部署状态"
fi

log_success "测试环境清理完成！"
