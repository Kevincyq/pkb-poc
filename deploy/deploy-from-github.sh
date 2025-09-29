#!/bin/bash

# PKB 项目 GitHub 自动部署脚本
# 适用于云端服务器从 GitHub 拉取代码并自动部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
GITHUB_REPO_URL="https://github.com/kevincyq/pkb-poc.git"  # 替换为你的 GitHub 仓库地址
PROJECT_NAME="pkb-poc"
DEPLOY_DIR="/opt/pkb"
BACKUP_DIR="/opt/pkb-backup"
BRANCH="main"  # 或者你想部署的分支

# 解析命令行参数
FORCE_REBUILD=false
SKIP_BACKUP=false
CUSTOM_REPO=""
CUSTOM_BRANCH=""

show_help() {
    echo "PKB GitHub 自动部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --repo URL          指定 GitHub 仓库地址"
    echo "  --branch BRANCH     指定部署分支 (默认: main)"
    echo "  --force-rebuild     强制重新构建所有镜像"
    echo "  --skip-backup       跳过备份步骤"
    echo "  --help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                                    # 使用默认配置部署"
    echo "  $0 --repo https://github.com/user/repo.git --branch dev"
    echo "  $0 --force-rebuild --skip-backup"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            CUSTOM_REPO="$2"
            shift 2
            ;;
        --branch)
            CUSTOM_BRANCH="$2"
            shift 2
            ;;
        --force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            log_error "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 使用自定义参数或默认值
if [ -n "$CUSTOM_REPO" ]; then
    GITHUB_REPO_URL="$CUSTOM_REPO"
fi

if [ -n "$CUSTOM_BRANCH" ]; then
    BRANCH="$CUSTOM_BRANCH"
fi

echo "======================================"
echo "    PKB GitHub 自动部署脚本"
echo "======================================"
echo ""
log_info "仓库地址: $GITHUB_REPO_URL"
log_info "部署分支: $BRANCH"
log_info "部署目录: $DEPLOY_DIR"
echo ""

# 检查运行权限
check_permissions() {
    log_info "检查运行权限..."
    
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 root 权限运行此脚本"
        log_info "使用命令: sudo $0"
        exit 1
    fi
    
    log_success "权限检查通过"
}

# 检查系统环境
check_environment() {
    log_info "检查系统环境..."
    
    # 检查 Git
    if ! command -v git &> /dev/null; then
        log_error "Git 未安装，正在安装..."
        apt-get update && apt-get install -y git
    fi
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        log_info "安装命令: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查网络连接
    if ! ping -c 1 github.com &> /dev/null; then
        log_error "无法连接到 GitHub，请检查网络连接"
        exit 1
    fi
    
    log_success "环境检查通过"
}

# 备份现有部署
backup_existing() {
    if [ "$SKIP_BACKUP" = true ]; then
        log_info "跳过备份步骤"
        return
    fi
    
    log_info "备份现有部署..."
    
    if [ -d "$DEPLOY_DIR" ]; then
        BACKUP_NAME="pkb-backup-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        log_info "创建备份: $BACKUP_DIR/$BACKUP_NAME"
        cp -r "$DEPLOY_DIR" "$BACKUP_DIR/$BACKUP_NAME"
        
        # 保留最近5个备份
        cd "$BACKUP_DIR"
        ls -t | tail -n +6 | xargs -r rm -rf
        
        log_success "备份完成"
    else
        log_info "未发现现有部署，跳过备份"
    fi
}

# 停止现有服务
stop_existing_services() {
    log_info "停止现有服务..."
    
    if [ -d "$DEPLOY_DIR" ] && [ -f "$DEPLOY_DIR/docker-compose.yml" ]; then
        cd "$DEPLOY_DIR"
        docker-compose down || true
        log_success "现有服务已停止"
    else
        log_info "未发现现有服务"
    fi
}

# 克隆或更新代码
clone_or_update_code() {
    log_info "获取最新代码..."
    
    if [ -d "$DEPLOY_DIR" ]; then
        log_info "更新现有代码仓库..."
        cd "$DEPLOY_DIR"
        
        # 检查是否是 git 仓库
        if [ -d ".git" ]; then
            git fetch origin
            git reset --hard "origin/$BRANCH"
            git clean -fd
        else
            log_warning "目录存在但不是 git 仓库，重新克隆..."
            cd /
            rm -rf "$DEPLOY_DIR"
            git clone -b "$BRANCH" "$GITHUB_REPO_URL" "$DEPLOY_DIR"
        fi
    else
        log_info "克隆代码仓库..."
        git clone -b "$BRANCH" "$GITHUB_REPO_URL" "$DEPLOY_DIR"
    fi
    
    cd "$DEPLOY_DIR"
    COMMIT_HASH=$(git rev-parse --short HEAD)
    COMMIT_MESSAGE=$(git log -1 --pretty=format:"%s")
    
    log_success "代码获取完成"
    log_info "当前版本: $COMMIT_HASH - $COMMIT_MESSAGE"
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."
    
    cd "$DEPLOY_DIR"
    
    # 检查是否存在 .env 文件
    if [ ! -f ".env" ]; then
        if [ -f "env.template" ]; then
            cp env.template .env
            log_success "已从模板创建 .env 文件"
        elif [ -f "deploy/env.template" ]; then
            cp deploy/env.template .env
            log_success "已从 deploy/env.template 创建 .env 文件"
        else
            log_error "未找到环境变量模板文件"
            exit 1
        fi
        
        log_warning "请编辑 .env 文件配置必要的环境变量："
        log_warning "- TURING_API_KEY: Turing API 密钥"
        log_warning "- NC_WEBDAV_URL: Nextcloud WebDAV 地址"
        log_warning "- NC_USER: Nextcloud 用户名"
        log_warning "- NC_PASS: Nextcloud 密码"
        
        read -p "按 Enter 继续，或 Ctrl+C 退出编辑 .env 文件..."
    else
        log_info ".env 文件已存在，使用现有配置"
    fi
}

# 构建和启动服务
build_and_start_services() {
    log_info "构建和启动服务..."
    
    cd "$DEPLOY_DIR"
    
    # 检查 docker-compose.yml 位置
    if [ -f "docker-compose.yml" ]; then
        COMPOSE_FILE="docker-compose.yml"
    elif [ -f "deploy/docker-compose.yml" ]; then
        cd deploy
        COMPOSE_FILE="docker-compose.yml"
    else
        log_error "未找到 docker-compose.yml 文件"
        exit 1
    fi
    
    log_info "使用配置文件: $(pwd)/$COMPOSE_FILE"
    
    # 构建镜像
    if [ "$FORCE_REBUILD" = true ]; then
        log_info "强制重新构建所有镜像..."
        docker-compose build --no-cache
    else
        log_info "构建镜像..."
        docker-compose build
    fi
    
    # 启动基础服务
    log_info "启动数据库和缓存服务..."
    docker-compose up -d postgres redis
    
    # 等待数据库启动
    log_info "等待数据库启动..."
    sleep 30
    
    # 初始化数据库扩展
    log_info "初始化数据库扩展..."
    docker-compose exec -T postgres psql -U pkb -d pkb -c "CREATE EXTENSION IF NOT EXISTS vector;" || true
    
    # 启动后端服务
    log_info "启动后端服务..."
    docker-compose up -d pkb-backend
    sleep 20
    
    # 启动 Worker 服务
    log_info "启动 Worker 服务..."
    docker-compose up -d pkb-worker-quick pkb-worker-classify pkb-worker-heavy
    sleep 15
    
    # 启动所有服务
    log_info "启动完整服务栈..."
    docker-compose up -d
    
    log_success "所有服务已启动"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 等待服务完全启动
    log_info "等待服务完全启动..."
    sleep 60
    
    # 检查服务状态
    services=("postgres" "redis" "pkb-backend")
    
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            log_success "$service 服务运行正常"
        else
            log_error "$service 服务未正常运行"
            return 1
        fi
    done
    
    # 检查 API 健康
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "检查 API 健康状态 (尝试 $attempt/$max_attempts)..."
        
        if curl -s http://localhost:8002/api/health | grep -q '"status":"ok"'; then
            log_success "API 健康检查通过"
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    log_error "API 健康检查失败"
    return 1
}

# 显示部署信息
show_deployment_info() {
    log_success "🎉 PKB 部署完成！"
    echo ""
    echo "📋 部署信息："
    echo "  • 仓库地址: $GITHUB_REPO_URL"
    echo "  • 部署分支: $BRANCH"
    echo "  • 部署目录: $DEPLOY_DIR"
    echo "  • 当前版本: $COMMIT_HASH"
    echo ""
    echo "🌐 访问地址："
    echo "  • API 文档: http://localhost:8002/api/docs"
    echo "  • 健康检查: http://localhost:8002/api/health"
    echo "  • Nextcloud: http://localhost:8080"
    echo ""
    echo "🔧 管理命令："
    echo "  • 查看日志: cd $DEPLOY_DIR && docker-compose logs -f [service_name]"
    echo "  • 重启服务: cd $DEPLOY_DIR && docker-compose restart [service_name]"
    echo "  • 停止服务: cd $DEPLOY_DIR && docker-compose down"
    echo "  • 查看状态: cd $DEPLOY_DIR && docker-compose ps"
    echo ""
    echo "📁 重要目录："
    echo "  • 部署目录: $DEPLOY_DIR"
    echo "  • 备份目录: $BACKUP_DIR"
    echo ""
    echo "🔄 重新部署："
    echo "  • 更新代码: $0"
    echo "  • 强制重建: $0 --force-rebuild"
    echo ""
    log_info "部署完成！PKB 服务已就绪！"
}

# 错误处理
cleanup_on_error() {
    log_error "部署过程中发生错误"
    
    if [ "$SKIP_BACKUP" = false ] && [ -d "$BACKUP_DIR" ]; then
        log_info "可以从备份恢复: $BACKUP_DIR"
    fi
    
    log_info "查看日志: cd $DEPLOY_DIR && docker-compose logs"
    exit 1
}

# 主函数
main() {
    # 设置错误处理
    trap cleanup_on_error ERR
    
    # 确认部署
    echo "即将从 GitHub 部署 PKB 项目："
    echo "  仓库: $GITHUB_REPO_URL"
    echo "  分支: $BRANCH"
    echo "  目标: $DEPLOY_DIR"
    echo ""
    read -p "确认开始部署？(y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log_info "部署已取消"
        exit 0
    fi
    
    # 执行部署步骤
    check_permissions
    check_environment
    backup_existing
    stop_existing_services
    clone_or_update_code
    setup_environment
    build_and_start_services
    
    # 健康检查
    if health_check; then
        show_deployment_info
    else
        log_error "健康检查失败，请检查服务状态"
        log_info "查看日志: cd $DEPLOY_DIR && docker-compose logs"
        exit 1
    fi
}

# 运行主函数
main "$@"
