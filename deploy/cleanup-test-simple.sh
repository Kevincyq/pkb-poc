#!/bin/bash

# PKB 简化测试环境清理脚本

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

TEST_DIR="/home/ec2-user/pkb-poc"

echo "🧹 PKB 测试环境清理脚本"
echo "========================="
echo ""

if [ ! -d "$TEST_DIR" ]; then
    log_warning "测试目录不存在: $TEST_DIR"
    exit 0
fi

cd "$TEST_DIR"

# 获取当前部署信息
if [ -f "test_branch" ]; then
    CURRENT_BRANCH=$(cat test_branch)
    log_info "当前测试分支: $CURRENT_BRANCH"
fi

if [ -f "test_port" ]; then
    CURRENT_PORT=$(cat test_port)
    log_info "当前测试端口: $CURRENT_PORT"
fi

# 停止测试环境服务
log_info "停止测试环境服务..."
cd deploy
docker-compose -p pkb-test down

# 恢复配置文件
if [ -f "docker-compose.cloud.yml.backup" ]; then
    log_info "恢复原始配置文件..."
    mv docker-compose.cloud.yml.backup docker-compose.cloud.yml
fi

# 清理部署状态文件
cd ..
rm -f test_branch test_port

# 切换回 main 分支
log_info "切换回 main 分支..."
git checkout main
git pull origin main

log_success "测试环境清理完成！"
echo ""
echo "📋 清理内容:"
echo "   ✅ 停止测试环境容器"
echo "   ✅ 恢复配置文件"
echo "   ✅ 清理部署状态"
echo "   ✅ 切换回 main 分支"
