#!/bin/bash

# PKB 分支部署脚本
# 用于在生产环境测试功能分支

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
DEPLOY_DIR="/home/ec2-user/pkb-new"

echo "🔄 PKB 分支部署脚本"
echo "========================="
echo "目标分支: $BRANCH_NAME"
echo ""

cd "$DEPLOY_DIR"

# 备份当前分支信息
CURRENT_BRANCH=$(git branch --show-current)
log_info "当前分支: $CURRENT_BRANCH"

# 保存当前状态
log_info "保存当前部署状态..."
echo "$CURRENT_BRANCH" > .last_deployed_branch
git rev-parse HEAD > .last_deployed_commit

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

# 检查是否有变更
if [ -f ".last_deployed_commit" ]; then
    LAST_COMMIT=$(cat .last_deployed_commit)
    CURRENT_COMMIT=$(git rev-parse HEAD)
    
    if [ "$LAST_COMMIT" = "$CURRENT_COMMIT" ] && [ "$CURRENT_BRANCH" = "$BRANCH_NAME" ]; then
        log_warning "没有检测到变更，跳过重新部署"
        exit 0
    fi
fi

# 停止服务
log_info "停止当前服务..."
cd deploy
docker-compose -f docker-compose.cloud.yml down

# 重新构建和启动
log_info "重新构建和启动服务..."
docker-compose -f docker-compose.cloud.yml up -d --build

# 等待服务启动
log_info "等待服务启动..."
sleep 30

# 健康检查
log_info "执行健康检查..."
cd ..

# 检查后端健康状态
if curl -f -s http://localhost:8002/api/health > /dev/null; then
    log_success "后端服务健康检查通过"
else
    log_error "后端服务健康检查失败"
    
    # 自动回滚
    if [ -f ".last_deployed_branch" ] && [ -f ".last_deployed_commit" ]; then
        ROLLBACK_BRANCH=$(cat .last_deployed_branch)
        log_warning "自动回滚到分支: $ROLLBACK_BRANCH"
        
        git checkout $ROLLBACK_BRANCH
        cd deploy
        docker-compose -f docker-compose.cloud.yml up -d --build
        cd ..
        
        log_error "部署失败，已自动回滚"
        exit 1
    fi
fi

# 检查服务状态
log_info "检查服务状态..."
cd deploy
docker-compose ps

log_success "分支 $BRANCH_NAME 部署完成！"
echo ""
echo "🌐 前端地址: https://pkb-poc.kmchat.cloud"
echo "🔗 后端地址: https://pkb.kmchat.cloud"
echo "📊 API 文档: https://pkb.kmchat.cloud/api/docs"
echo ""
echo "💡 如需回滚到 main 分支："
echo "   $0 main"
