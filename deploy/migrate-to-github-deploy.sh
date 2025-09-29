#!/bin/bash

# PKB 现有环境到 GitHub 部署的安全迁移脚本
# 适用于已有运行环境的平滑迁移

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
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

# 配置变量
CURRENT_DIR=$(pwd)
BACKUP_DIR="/opt/pkb-migration-backup-$(date +%Y%m%d-%H%M%S)"
NEW_DEPLOY_DIR="/opt/pkb"
GITHUB_REPO="https://github.com/kevincyq/pkb-poc.git"  # 请修改为你的仓库地址
BRANCH="main"

echo "======================================"
echo "    PKB 环境安全迁移脚本"
echo "======================================"
echo ""
log_info "当前目录: $CURRENT_DIR"
log_info "备份目录: $BACKUP_DIR"
log_info "新部署目录: $NEW_DEPLOY_DIR"
echo ""

# 检查权限
check_permissions() {
    log_info "检查运行权限..."
    
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 root 权限运行此脚本"
        log_info "使用命令: sudo $0"
        exit 1
    fi
    
    log_success "权限检查通过"
}

# 评估当前环境
assess_current_environment() {
    log_info "评估当前部署环境..."
    
    # 检查 Docker 服务
    if ! docker ps &> /dev/null; then
        log_error "Docker 服务未运行或无权限访问"
        exit 1
    fi
    
    # 检查运行中的 PKB 容器
    PKB_CONTAINERS=$(docker ps --format "table {{.Names}}" | grep -E "(pkb|postgres|redis)" || true)
    
    if [ -n "$PKB_CONTAINERS" ]; then
        log_success "发现运行中的 PKB 相关容器:"
        echo "$PKB_CONTAINERS"
    else
        log_warning "未发现运行中的 PKB 容器"
    fi
    
    # 检查 docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        log_success "发现 docker-compose.yml 文件"
        COMPOSE_FILE_EXISTS=true
    else
        log_warning "未发现 docker-compose.yml 文件"
        COMPOSE_FILE_EXISTS=false
    fi
    
    # 检查 .env 文件
    if [ -f ".env" ]; then
        log_success "发现 .env 配置文件"
        ENV_FILE_EXISTS=true
    else
        log_warning "未发现 .env 配置文件"
        ENV_FILE_EXISTS=false
    fi
    
    echo ""
}

# 创建完整备份
create_full_backup() {
    log_info "创建完整环境备份..."
    
    mkdir -p "$BACKUP_DIR"
    
    # 1. 备份当前目录的所有文件
    log_info "备份当前部署文件..."
    cp -r "$CURRENT_DIR" "$BACKUP_DIR/current_deployment"
    
    # 2. 备份数据库
    log_info "备份数据库..."
    if docker ps | grep -q postgres; then
        POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep postgres | head -1)
        log_info "发现 PostgreSQL 容器: $POSTGRES_CONTAINER"
        
        # 创建数据库备份
        docker exec "$POSTGRES_CONTAINER" pg_dumpall -U postgres > "$BACKUP_DIR/database_full_backup.sql" 2>/dev/null || \
        docker exec "$POSTGRES_CONTAINER" pg_dump -U pkb pkb > "$BACKUP_DIR/database_pkb_backup.sql" 2>/dev/null || \
        log_warning "数据库备份失败，请手动备份"
        
        if [ -f "$BACKUP_DIR/database_full_backup.sql" ] || [ -f "$BACKUP_DIR/database_pkb_backup.sql" ]; then
            log_success "数据库备份完成"
        fi
    else
        log_warning "未发现 PostgreSQL 容器，跳过数据库备份"
    fi
    
    # 3. 备份 Docker 卷
    log_info "备份 Docker 卷..."
    docker volume ls --format "{{.Name}}" | grep -E "(pkb|postgres|redis)" > "$BACKUP_DIR/docker_volumes.txt" 2>/dev/null || true
    
    # 4. 备份容器配置
    log_info "备份容器配置..."
    docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep -E "(pkb|postgres|redis)" > "$BACKUP_DIR/containers_status.txt" 2>/dev/null || true
    
    # 5. 创建恢复说明
    cat > "$BACKUP_DIR/RESTORE_INSTRUCTIONS.md" << EOF
# PKB 环境备份恢复说明

## 备份信息
- 备份时间: $(date)
- 备份目录: $BACKUP_DIR
- 原部署目录: $CURRENT_DIR

## 备份内容
- current_deployment/: 完整的当前部署文件
- database_*_backup.sql: 数据库备份
- docker_volumes.txt: Docker 卷列表
- containers_status.txt: 容器状态

## 恢复步骤（如果需要回滚）

1. 停止新部署的服务
   \`\`\`bash
   cd $NEW_DEPLOY_DIR
   docker-compose down
   \`\`\`

2. 恢复原部署文件
   \`\`\`bash
   cp -r $BACKUP_DIR/current_deployment/* $CURRENT_DIR/
   cd $CURRENT_DIR
   \`\`\`

3. 恢复数据库
   \`\`\`bash
   # 如果有完整备份
   docker exec -i postgres_container psql -U postgres < $BACKUP_DIR/database_full_backup.sql
   
   # 或者恢复 PKB 数据库
   docker exec -i postgres_container psql -U pkb -d pkb < $BACKUP_DIR/database_pkb_backup.sql
   \`\`\`

4. 启动原服务
   \`\`\`bash
   docker-compose up -d
   \`\`\`

## 联系信息
如需帮助，请查看备份文件或联系管理员。
EOF
    
    log_success "完整备份创建完成: $BACKUP_DIR"
}

# 停止当前服务
stop_current_services() {
    log_info "停止当前运行的服务..."
    
    if [ "$COMPOSE_FILE_EXISTS" = true ]; then
        log_info "使用 docker-compose 停止服务..."
        docker-compose down || log_warning "docker-compose down 执行失败"
    else
        log_info "手动停止 PKB 相关容器..."
        # 停止所有 PKB 相关容器
        docker ps --format "{{.Names}}" | grep -E "(pkb|postgres|redis)" | xargs -r docker stop || true
    fi
    
    log_success "服务停止完成"
}

# 迁移配置文件
migrate_configuration() {
    log_info "迁移配置文件到新部署目录..."
    
    # 确保新部署目录存在
    mkdir -p "$NEW_DEPLOY_DIR"
    
    # 如果新目录已存在且有内容，先备份
    if [ "$(ls -A $NEW_DEPLOY_DIR 2>/dev/null)" ]; then
        log_warning "新部署目录不为空，创建备份..."
        mv "$NEW_DEPLOY_DIR" "${NEW_DEPLOY_DIR}_old_$(date +%H%M%S)"
        mkdir -p "$NEW_DEPLOY_DIR"
    fi
    
    # 克隆新代码
    log_info "克隆最新代码..."
    git clone -b "$BRANCH" "$GITHUB_REPO" "$NEW_DEPLOY_DIR"
    
    # 迁移 .env 文件
    if [ "$ENV_FILE_EXISTS" = true ]; then
        log_info "迁移现有 .env 配置..."
        # 检查是否使用云端配置，决定 .env 文件位置
        if [ -f "$NEW_DEPLOY_DIR/deploy/docker-compose.cloud.yml" ]; then
            cp "$CURRENT_DIR/.env" "$NEW_DEPLOY_DIR/deploy/.env"
            log_success ".env 文件迁移完成: $NEW_DEPLOY_DIR/deploy/.env"
        else
            cp "$CURRENT_DIR/.env" "$NEW_DEPLOY_DIR/.env"
            log_success ".env 文件迁移完成: $NEW_DEPLOY_DIR/.env"
        fi
    else
        log_info "创建新的 .env 文件..."
        if [ -f "$NEW_DEPLOY_DIR/deploy/env.cloud.template" ]; then
            cp "$NEW_DEPLOY_DIR/deploy/env.cloud.template" "$NEW_DEPLOY_DIR/deploy/.env"
            log_warning "请编辑 $NEW_DEPLOY_DIR/deploy/.env 文件配置必要参数"
        elif [ -f "$NEW_DEPLOY_DIR/env.template" ]; then
            cp "$NEW_DEPLOY_DIR/env.template" "$NEW_DEPLOY_DIR/.env"
            log_warning "请编辑 $NEW_DEPLOY_DIR/.env 文件配置必要参数"
        fi
    fi
    
    log_success "配置迁移完成"
}

# 启动新部署
start_new_deployment() {
    log_info "启动新的 GitHub 部署..."
    
    cd "$NEW_DEPLOY_DIR"
    
    # 检查使用哪个 compose 文件
    if [ -f "deploy/docker-compose.cloud.yml" ]; then
        log_info "使用云端优化配置..."
        cd deploy
        COMPOSE_CMD="docker-compose -f docker-compose.cloud.yml"
    elif [ -f "docker-compose.yml" ]; then
        log_info "使用默认配置..."
        COMPOSE_CMD="docker-compose"
    else
        log_error "未找到 docker-compose 配置文件"
        exit 1
    fi
    
    # 构建服务
    log_info "构建服务..."
    $COMPOSE_CMD build
    
    # 启动基础服务
    log_info "启动数据库和缓存..."
    $COMPOSE_CMD up -d postgres redis
    
    # 等待数据库启动
    log_info "等待数据库启动..."
    sleep 30
    
    # 初始化数据库扩展
    log_info "初始化数据库扩展..."
    $COMPOSE_CMD exec -T postgres psql -U pkb -d pkb -c "CREATE EXTENSION IF NOT EXISTS vector;" || true
    
    # 恢复数据库（如果有备份）
    if [ -f "$BACKUP_DIR/database_pkb_backup.sql" ]; then
        log_info "恢复数据库数据..."
        $COMPOSE_CMD exec -T postgres psql -U pkb -d pkb < "$BACKUP_DIR/database_pkb_backup.sql" || \
        log_warning "数据库恢复失败，可能需要手动恢复"
    elif [ -f "$BACKUP_DIR/database_full_backup.sql" ]; then
        log_info "恢复完整数据库..."
        $COMPOSE_CMD exec -T postgres psql -U postgres < "$BACKUP_DIR/database_full_backup.sql" || \
        log_warning "数据库恢复失败，可能需要手动恢复"
    fi
    
    # 启动所有服务
    log_info "启动所有服务..."
    $COMPOSE_CMD up -d
    
    log_success "新部署启动完成"
}

# 验证新部署
verify_new_deployment() {
    log_info "验证新部署..."
    
    # 等待服务启动
    log_info "等待服务完全启动..."
    sleep 60
    
    # 检查容器状态
    cd "$NEW_DEPLOY_DIR"
    if [ -d "deploy" ]; then
        cd deploy
        COMPOSE_CMD="docker-compose -f docker-compose.cloud.yml"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    log_info "检查服务状态..."
    $COMPOSE_CMD ps
    
    # 健康检查
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "API 健康检查 (尝试 $attempt/$max_attempts)..."
        
        if curl -s http://localhost:8002/api/health | grep -q '"status":"ok"'; then
            log_success "✅ API 健康检查通过"
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    log_error "❌ API 健康检查失败"
    return 1
}

# 显示迁移结果
show_migration_result() {
    log_success "🎉 PKB 环境迁移完成！"
    echo ""
    echo "📋 迁移信息："
    echo "  • 原部署目录: $CURRENT_DIR"
    echo "  • 新部署目录: $NEW_DEPLOY_DIR"
    echo "  • 备份目录: $BACKUP_DIR"
    echo ""
    echo "🌐 访问地址："
    echo "  • API 文档: http://localhost:8002/api/docs"
    echo "  • 健康检查: http://localhost:8002/api/health"
    echo ""
    echo "🔧 新的管理命令："
    echo "  • 查看状态: cd $NEW_DEPLOY_DIR && docker-compose ps"
    echo "  • 查看日志: cd $NEW_DEPLOY_DIR && docker-compose logs -f"
    echo "  • 重启服务: cd $NEW_DEPLOY_DIR && docker-compose restart"
    echo ""
    echo "📁 重要文件："
    echo "  • 新配置文件: $NEW_DEPLOY_DIR/.env"
    echo "  • 完整备份: $BACKUP_DIR"
    echo "  • 恢复说明: $BACKUP_DIR/RESTORE_INSTRUCTIONS.md"
    echo ""
    echo "🔄 后续更新："
    echo "  • 自动更新: cd $NEW_DEPLOY_DIR && git pull && docker-compose up -d --build"
    echo "  • 使用新脚本: 下载并使用 quick-deploy.sh 或 deploy-from-github.sh"
    echo ""
    log_info "迁移完成！现在你可以使用 GitHub 自动部署方案了！"
}

# 错误处理
cleanup_on_error() {
    log_error "迁移过程中发生错误"
    log_info "备份文件位于: $BACKUP_DIR"
    log_info "可以参考 $BACKUP_DIR/RESTORE_INSTRUCTIONS.md 进行恢复"
    exit 1
}

# 主函数
main() {
    # 设置错误处理
    trap cleanup_on_error ERR
    
    # 确认迁移
    echo "⚠️  重要提醒："
    echo "   此脚本将安全地迁移你的现有 PKB 环境到新的 GitHub 自动部署方案"
    echo "   迁移过程包括："
    echo "   1. 完整备份现有环境（包括数据库）"
    echo "   2. 停止当前服务"
    echo "   3. 部署新的 GitHub 版本"
    echo "   4. 迁移配置和数据"
    echo "   5. 启动新服务"
    echo ""
    echo "📁 当前目录: $CURRENT_DIR"
    echo "📁 新部署目录: $NEW_DEPLOY_DIR"
    echo "📁 备份目录: $BACKUP_DIR"
    echo ""
    read -p "确认开始迁移？(y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log_info "迁移已取消"
        exit 0
    fi
    
    # 执行迁移步骤
    check_permissions
    assess_current_environment
    create_full_backup
    stop_current_services
    migrate_configuration
    start_new_deployment
    
    # 验证新部署
    if verify_new_deployment; then
        show_migration_result
    else
        log_error "新部署验证失败"
        log_info "请检查服务状态: cd $NEW_DEPLOY_DIR && docker-compose logs"
        log_info "如需回滚，请参考: $BACKUP_DIR/RESTORE_INSTRUCTIONS.md"
        exit 1
    fi
}

# 运行主函数
main "$@"
