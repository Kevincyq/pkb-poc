#!/bin/bash

# PKB 快速回滚脚本

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

DEPLOY_DIR="/home/ec2-user/pkb-new"

echo "🔄 PKB 快速回滚脚本"
echo "==================="
echo ""

cd "$DEPLOY_DIR"

# 检查是否有备份信息
if [ ! -f ".last_deployed_branch" ]; then
    log_warning "没有找到上次部署的分支信息，回滚到 main 分支"
    TARGET_BRANCH="main"
else
    TARGET_BRANCH=$(cat .last_deployed_branch)
    log_info "回滚到上次部署的分支: $TARGET_BRANCH"
fi

# 当前分支信息
CURRENT_BRANCH=$(git branch --show-current)
log_info "当前分支: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" = "$TARGET_BRANCH" ]; then
    log_warning "当前已经在目标分支 $TARGET_BRANCH，检查是否需要重新部署"
    
    # 检查服务状态
    if curl -f -s http://localhost:8002/api/health > /dev/null; then
        log_success "服务运行正常，无需回滚"
        exit 0
    else
        log_warning "服务异常，重新部署当前分支"
    fi
else
    # 切换分支
    log_info "切换到分支: $TARGET_BRANCH"
    git fetch origin
    git checkout $TARGET_BRANCH
    git pull origin $TARGET_BRANCH
fi

# 重新部署
log_info "重新部署服务..."
cd deploy
docker-compose -f docker-compose.cloud.yml down
docker-compose -f docker-compose.cloud.yml up -d --build

# 等待服务启动
log_info "等待服务启动..."
sleep 30

# 健康检查
log_info "执行健康检查..."
cd ..

if curl -f -s http://localhost:8002/api/health > /dev/null; then
    log_success "回滚成功！服务运行正常"
else
    log_error "回滚后服务仍然异常，请检查日志"
    cd deploy
    docker-compose logs --tail=50 pkb-backend
    exit 1
fi

# 更新部署状态
echo "$TARGET_BRANCH" > .last_deployed_branch
git rev-parse HEAD > .last_deployed_commit

log_success "回滚到分支 $TARGET_BRANCH 完成！"
echo ""
echo "🌐 前端地址: https://pkb-poc.kmchat.cloud"
echo "🔗 后端地址: https://pkb.kmchat.cloud"
