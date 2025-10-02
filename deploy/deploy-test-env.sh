#!/bin/bash

# PKB 测试环境部署脚本
# 用于部署功能分支到独立的测试环境

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
    echo "使用方法: $0 <branch-name> [port]"
    echo "示例: $0 feature/user-auth-system 8003"
    echo "默认端口: 8003 (测试环境)"
    exit 1
fi

BRANCH_NAME=$1
TEST_PORT=${2:-8003}  # 默认测试环境端口 8003
DEPLOY_DIR="/home/ec2-user/pkb-test"  # 测试环境目录
COMPOSE_PROJECT="pkb-test"  # 独立的 compose 项目名

echo "🧪 PKB 测试环境部署脚本"
echo "========================="
echo "分支: $BRANCH_NAME"
echo "端口: $TEST_PORT"
echo "目录: $DEPLOY_DIR"
echo ""

# 创建测试环境目录
if [ ! -d "$DEPLOY_DIR" ]; then
    log_info "创建测试环境目录..."
    mkdir -p "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
    
    # 克隆仓库
    log_info "克隆代码仓库..."
    git clone https://github.com/Kevincyq/pkb-poc.git .
else
    cd "$DEPLOY_DIR"
fi

# 获取最新代码
log_info "获取最新代码..."
git fetch origin

# 检查分支是否存在
if ! git show-ref --verify --quiet refs/remotes/origin/$BRANCH_NAME; then
    log_error "分支 $BRANCH_NAME 不存在于远程仓库"
    exit 1
fi

# 切换到目标分支
log_info "切换到分支: $BRANCH_NAME"
git checkout $BRANCH_NAME
git pull origin $BRANCH_NAME

# 创建测试环境配置
log_info "创建测试环境配置..."

# 复制并修改 docker-compose 配置
cp deploy/docker-compose.cloud.yml deploy/docker-compose.test.yml

# 修改端口配置（使用 sed 替换）
sed -i "s/8002:8000/$TEST_PORT:8000/g" deploy/docker-compose.test.yml

# 修改项目名称和容器名称
sed -i "s/pkb-backend/pkb-test-backend/g" deploy/docker-compose.test.yml
sed -i "s/pkb-worker/pkb-test-worker/g" deploy/docker-compose.test.yml

# 创建测试环境变量文件
if [ -f "deploy/.env" ]; then
    cp deploy/.env deploy/.env.test
    
    # 修改数据库名称（避免与生产环境冲突）
    sed -i "s/POSTGRES_DB=pkb/POSTGRES_DB=pkb_test/g" deploy/.env.test
    sed -i "s/postgres:5432/postgres-test:5432/g" deploy/.env.test
    
    log_info "测试环境将使用独立的数据库: pkb_test"
else
    log_warning "未找到 .env 文件，请确保环境配置正确"
fi

# 停止现有的测试环境服务
log_info "停止现有测试环境服务..."
cd deploy
docker-compose -f docker-compose.test.yml -p $COMPOSE_PROJECT down 2>/dev/null || true

# 启动测试环境
log_info "启动测试环境..."
docker-compose -f docker-compose.test.yml -p $COMPOSE_PROJECT up -d --build

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
    docker-compose -f docker-compose.test.yml -p $COMPOSE_PROJECT logs --tail=50
    exit 1
fi

# 显示服务状态
log_info "检查服务状态..."
cd deploy
docker-compose -f docker-compose.test.yml -p $COMPOSE_PROJECT ps

# 保存部署信息
echo "$BRANCH_NAME" > ../test_deployed_branch
echo "$TEST_PORT" > ../test_deployed_port

log_success "测试环境部署完成！"
echo ""
echo "🧪 测试环境信息:"
echo "   分支: $BRANCH_NAME"
echo "   后端: http://localhost:$TEST_PORT"
echo "   API 文档: http://localhost:$TEST_PORT/api/docs"
echo "   健康检查: http://localhost:$TEST_PORT/api/health"
echo ""
echo "🌐 前端测试环境:"
echo "   Vercel 会自动为分支 '$BRANCH_NAME' 创建预览环境"
echo "   URL 格式: https://pkb-poc-git-$(echo $BRANCH_NAME | sed 's/\//-/g').vercel.app"
echo ""
echo "💡 停止测试环境:"
echo "   cd $DEPLOY_DIR/deploy"
echo "   docker-compose -f docker-compose.test.yml -p $COMPOSE_PROJECT down"
