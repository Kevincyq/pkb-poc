#!/bin/bash

# PKB v2.0 全新部署脚本
# 适用于新环境的完整部署

set -e

echo "🚀 开始 PKB v2.0 全新部署..."

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

# 检查环境
check_environment() {
    log_info "检查部署环境..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查端口占用
    if netstat -tuln | grep -q ":8002 "; then
        log_warning "端口 8002 已被占用，可能需要修改配置"
    fi
    
    log_success "环境检查通过"
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."
    
    if [ ! -f ".env" ]; then
        cp env.template .env
        log_success "已创建 .env 文件"
        
        echo ""
        log_warning "请配置以下必要的环境变量："
        echo "  1. TURING_API_KEY - Turing API 密钥"
        echo "  2. NC_WEBDAV_URL - Nextcloud WebDAV 地址"
        echo "  3. NC_USER - Nextcloud 用户名"
        echo "  4. NC_PASS - Nextcloud 密码"
        echo ""
        
        read -p "是否现在编辑 .env 文件？(y/N): " edit_env
        if [[ $edit_env =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        else
            log_warning "请手动编辑 .env 文件后重新运行部署脚本"
            exit 1
        fi
    else
        log_info ".env 文件已存在"
    fi
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p backup
    mkdir -p logs
    
    log_success "目录创建完成"
}

# 启动服务
start_services() {
    log_info "启动 PKB v2.0 服务..."
    
    # 启动基础服务
    log_info "启动数据库和缓存..."
    docker-compose up -d postgres redis
    
    # 等待数据库启动
    log_info "等待数据库初始化..."
    sleep 30
    
    # 执行数据库初始化
    log_info "初始化数据库..."
    docker-compose exec -T postgres psql -U pkb -d pkb < migrate_v2.sql || true
    
    # 启动后端服务
    log_info "启动后端服务..."
    docker-compose up -d pkb-backend
    sleep 20
    
    # 启动 Worker 服务
    log_info "启动 Worker 服务..."
    docker-compose up -d pkb-worker-quick pkb-worker-classify pkb-worker-heavy
    sleep 15
    
    # 启动其他服务
    log_info "启动完整服务栈..."
    docker-compose up -d
    
    log_success "所有服务已启动"
}

# 初始化系统
initialize_system() {
    log_info "初始化系统..."
    
    # 等待服务完全启动
    log_info "等待服务完全启动..."
    sleep 60
    
    # 初始化系统分类
    log_info "初始化系统分类..."
    response=$(curl -s -X POST http://localhost:8002/api/category/initialize || echo '{"success":false}')
    
    if echo "$response" | grep -q '"success":true'; then
        log_success "系统分类初始化成功"
    else
        log_warning "系统分类初始化失败，可能需要手动初始化"
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查服务状态
    services=("postgres" "redis" "pkb-backend" "pkb-worker-quick" "pkb-worker-classify" "pkb-worker-heavy")
    
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            log_success "$service 服务运行正常"
        else
            log_error "$service 服务未正常运行"
            return 1
        fi
    done
    
    # 检查 API 健康
    if curl -s http://localhost:8002/api/health | grep -q '"status":"ok"'; then
        log_success "API 健康检查通过"
    else
        log_error "API 健康检查失败"
        return 1
    fi
    
    # 检查分类服务
    response=$(curl -s http://localhost:8002/api/category/service/status || echo '{"enabled":false}')
    if echo "$response" | grep -q '"enabled":true'; then
        log_success "分类服务配置正确"
    else
        log_warning "分类服务配置可能有问题，请检查 API 密钥"
    fi
}

# 显示部署信息
show_deployment_info() {
    log_success "🎉 PKB v2.0 部署完成！"
    echo ""
    echo "📋 功能特性："
    echo "  ✅ 智能文档分类（职场商务、生活点滴、学习成长、科技前沿）"
    echo "  ✅ GPT-4o-mini 图片内容识别"
    echo "  ✅ 快速预分类 + AI精确分类"
    echo "  ✅ 分类搜索和问答"
    echo "  ✅ 自动文件删除同步"
    echo "  ✅ 多队列异步处理"
    echo ""
    echo "🌐 访问地址："
    echo "  • API 文档: http://localhost:8002/api/docs"
    echo "  • 健康检查: http://localhost:8002/api/health"
    echo "  • 分类状态: http://localhost:8002/api/category/service/status"
    echo ""
    echo "🔧 管理命令："
    echo "  • 查看日志: docker-compose logs -f [service_name]"
    echo "  • 重启服务: docker-compose restart [service_name]"
    echo "  • 停止服务: docker-compose down"
    echo "  • 查看状态: docker-compose ps"
    echo ""
    echo "📁 重要目录："
    echo "  • 备份目录: ./backup/"
    echo "  • 日志目录: ./logs/"
    echo "  • 配置文件: ./.env"
    echo ""
    echo "⚡ 快速测试："
    echo "  # 上传文件测试"
    echo "  curl -X POST http://localhost:8002/api/ingest/scan"
    echo ""
    echo "  # 查看分类"
    echo "  curl http://localhost:8002/api/category/"
    echo ""
    log_info "部署完成！开始使用 PKB v2.0 吧！"
}

# 主函数
main() {
    echo "======================================"
    echo "    PKB v2.0 智能分类全新部署"
    echo "======================================"
    echo ""
    
    # 确认部署
    read -p "确认开始全新部署？(y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log_info "部署已取消"
        exit 0
    fi
    
    # 执行部署步骤
    check_environment
    setup_environment
    create_directories
    start_services
    initialize_system
    
    # 健康检查
    if health_check; then
        show_deployment_info
    else
        log_error "健康检查失败，请检查服务状态"
        log_info "查看日志: docker-compose logs"
        exit 1
    fi
}

# 错误处理
trap 'log_error "部署过程中发生错误，请查看日志"; exit 1' ERR

# 运行主函数
main "$@"
