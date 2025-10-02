#!/bin/bash

# PKB 简化测试环境部署脚本
# 复用 /home/ec2-user/pkb-poc 目录作为测试环境

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

# 检查参数
if [ $# -eq 0 ]; then
    echo "使用方法: $0 <branch-name>"
    echo "示例: $0 feature/user-auth-system"
    echo "回滚到 main: $0 main"
    exit 1
fi

BRANCH_NAME=$1
TEST_DIR="/home/ec2-user/pkb-poc"
TEST_PORT="8003"

echo "🧪 PKB 测试环境部署脚本"
echo "========================="
echo "分支: $BRANCH_NAME"
echo "目录: $TEST_DIR"
echo "端口: $TEST_PORT"
echo ""

# 检查测试目录
if [ ! -d "$TEST_DIR" ]; then
    log_error "测试目录不存在: $TEST_DIR"
    exit 1
fi

cd "$TEST_DIR"

# 检查是否是 Git 仓库
if [ ! -d ".git" ]; then
    log_error "不是 Git 仓库: $TEST_DIR"
    exit 1
fi

# 保存当前状态
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
log_info "当前分支: $CURRENT_BRANCH"

# 获取最新代码
log_info "获取最新代码..."
git fetch origin

# 检查分支是否存在
if ! git show-ref --verify --quiet refs/remotes/origin/$BRANCH_NAME; then
    log_error "分支 $BRANCH_NAME 不存在于远程仓库"
    exit 1
fi

# 切换分支
log_info "切换到分支: $BRANCH_NAME"
git checkout $BRANCH_NAME
git pull origin $BRANCH_NAME

# 创建测试环境配置
log_info "准备测试环境配置..."

# 备份原始配置
if [ -f "deploy/docker-compose.cloud.yml" ]; then
    cp deploy/docker-compose.cloud.yml deploy/docker-compose.cloud.yml.backup
fi

# 修改端口配置 (8002 -> 8003)
sed -i 's/8002:8000/8003:8000/g' deploy/docker-compose.cloud.yml

# 修改数据库名称 (pkb -> pkb_test)
sed -i 's/POSTGRES_DB: pkb/POSTGRES_DB: pkb_test/g' deploy/docker-compose.cloud.yml

# 停止现有测试环境
log_info "停止现有测试环境..."
cd deploy
docker-compose -p pkb-test down 2>/dev/null || true

# 启动测试环境
log_info "启动测试环境..."
docker-compose -p pkb-test up -d --build

# 等待服务启动
log_info "等待服务启动..."
sleep 30

# 健康检查
log_info "执行健康检查..."
cd ..

MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s http://localhost:$TEST_PORT/api/health > /dev/null; then
        log_success "测试环境健康检查通过"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        log_warning "健康检查失败，重试 $RETRY_COUNT/$MAX_RETRIES..."
        sleep 10
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "测试环境启动失败"
    cd deploy
    docker-compose -p pkb-test logs --tail=50
    exit 1
fi

# 显示服务状态
log_info "检查服务状态..."
cd deploy
docker-compose -p pkb-test ps

# 保存部署信息
echo "$BRANCH_NAME" > ../test_branch
echo "$TEST_PORT" > ../test_port

log_success "测试环境部署完成！"
echo ""
echo "🧪 测试环境信息:"
echo "   分支: $BRANCH_NAME"
echo "   后端: http://localhost:$TEST_PORT"
echo "   API 文档: http://localhost:$TEST_PORT/api/docs"
echo "   健康检查: http://localhost:$TEST_PORT/api/health"
echo ""
echo "🌐 前端预览环境:"
echo "   Vercel 自动部署: https://pkb-poc-git-$(echo $BRANCH_NAME | sed 's/\//-/g').vercel.app"
echo ""
echo "💡 停止测试环境:"
echo "   cd $TEST_DIR/deploy && docker-compose -p pkb-test down"
echo ""
echo "🔄 恢复配置文件:"
echo "   cd $TEST_DIR/deploy && mv docker-compose.cloud.yml.backup docker-compose.cloud.yml"
