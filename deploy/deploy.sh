#!/bin/bash
# PKB 项目统一部署脚本
# 支持首次部署和重置部署

set -e  # 遇到错误就退出

echo "🚀 PKB 项目部署脚本"
echo "==================="

# 解析命令行参数
RESET_MODE=false
FORCE_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --reset)
            RESET_MODE=true
            shift
            ;;
        --force)
            FORCE_MODE=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --reset    完全重置并重新部署（清理容器、镜像、重建）"
            echo "  --force    强制执行，不询问确认"
            echo "  -h, --help 显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                # 首次部署或常规启动"
            echo "  $0 --reset        # 完全重置部署"
            echo "  $0 --reset --force # 强制重置部署"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 $0 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 请在 deploy 目录中运行此脚本"
    exit 1
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "📋 创建 .env 文件..."
    
    if [ -f "env.template" ]; then
        cp env.template .env
        echo "✅ 已从模板创建 .env 文件"
        echo ""
        echo "⚠️  重要提醒："
        echo "   请编辑 .env 文件，设置以下必要的配置："
        echo "   - TURING_API_KEY: 你的 Turing 平台 API Key"
        echo "   - NC_PASS: 你的 Nextcloud 密码"
        echo ""
        echo "   编辑命令: nano .env 或 vim .env"
        echo ""
        
        if [ "$FORCE_MODE" = false ]; then
            read -p "按 Enter 键继续，或 Ctrl+C 退出去编辑 .env 文件..."
        fi
    else
        echo "❌ 错误: env.template 文件不存在"
        exit 1
    fi
fi

# 验证关键环境变量
echo "🔍 验证环境变量配置..."
export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)

missing_vars=()
if [ -z "$TURING_API_KEY" ] || [ "$TURING_API_KEY" = "your_turing_api_key_here" ]; then
    missing_vars+=("TURING_API_KEY")
fi

if [ -z "$NC_PASS" ] || [ "$NC_PASS" = "your_nextcloud_password" ]; then
    missing_vars+=("NC_PASS")
fi

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ 以下环境变量需要配置:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "请编辑 .env 文件设置这些变量，然后重新运行此脚本"
    exit 1
fi

echo "✅ 环境变量验证通过"

# 检查 Docker 环境
echo "🐳 检查 Docker 环境..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 根据模式执行不同的部署流程
if [ "$RESET_MODE" = true ]; then
    echo ""
    echo "🔄 重置部署模式"
    echo "==============="
    
    if [ "$FORCE_MODE" = false ]; then
        echo "⚠️  警告: 重置模式将会："
        echo "   - 停止并删除所有容器"
        echo "   - 清理 Docker 镜像和缓存"
        echo "   - 重新构建所有服务"
        echo "   - 重置数据库表结构（数据将丢失）"
        echo ""
        read -p "确定要继续吗？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ 取消重置部署"
            exit 1
        fi
    fi
    
    echo "📋 步骤 1: 停止所有服务"
    docker-compose down
    
    echo "📋 步骤 2: 清理旧镜像和容器"
    docker-compose rm -f
    docker system prune -f
    
    echo "📋 步骤 3: 重新构建服务"
    docker-compose build --no-cache
    
    echo "📋 步骤 4: 启动基础服务（数据库、Redis）"
    docker-compose up -d postgres redis
    
    echo "⏳ 等待数据库启动..."
    sleep 10
    
    echo "📋 步骤 5: 初始化 pgvector 扩展"
    docker-compose exec postgres psql -U pkb -d pkb -c "CREATE EXTENSION IF NOT EXISTS vector;"
    
    echo "📋 步骤 6: 启动 PKB 服务"
    docker-compose up -d pkb-backend pkb-worker
    
    echo "⏳ 等待 PKB 服务启动..."
    sleep 10
    
    echo "📋 步骤 7: 重置数据库表结构"
    docker-compose exec pkb-backend python -m app.reset_database --force
    
    echo "📋 步骤 8: 启动所有服务"
    docker-compose up -d
    
else
    echo ""
    echo "🚀 常规部署模式"
    echo "==============="
    
    # 检查是否已有运行的服务
    if docker-compose ps | grep -q "Up"; then
        echo "📊 检测到运行中的服务:"
        docker-compose ps
        echo ""
        
        if [ "$FORCE_MODE" = false ]; then
            read -p "是否重启服务？(y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "🔄 重启服务..."
                docker-compose restart
            else
                echo "👍 保持现有服务运行"
            fi
        fi
    else
        echo "🚀 启动所有服务..."
        docker-compose up -d
    fi
fi

echo ""
echo "⏳ 等待所有服务启动..."
sleep 5

echo ""
echo "📊 服务状态:"
docker-compose ps

echo ""
echo "🌐 访问地址:"
echo "   - PKB API 文档: http://localhost:8002/api/docs"
echo "   - PKB Embedding API: http://localhost:8002/api/embedding/info"
echo "   - Nextcloud: http://localhost:8080"
echo "   - MaxKB: http://localhost:7861"

echo ""
echo "🔧 常用命令:"
echo "   - 查看日志: docker-compose logs -f [服务名]"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart [服务名]"
echo "   - 进入容器: docker-compose exec [服务名] bash"

echo ""
echo "🧪 测试命令:"
echo "   - 测试 API: curl http://localhost:8002/api/health"
echo "   - 测试 Embedding: curl http://localhost:8002/api/embedding/health"
echo "   - 测试文档处理: docker-compose exec pkb-backend python test_document_processing.py"
echo "   - 测试 Embedding 服务: docker-compose exec pkb-backend python test_embedding_service.py"

echo ""
echo "🎉 部署完成！"
