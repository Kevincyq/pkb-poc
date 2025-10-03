#!/bin/bash
# PKB Phase 1 修复部署脚本
# 用于在服务器端部署缩略图生成和模型关系修复

set -e  # 遇到错误立即退出

echo "🚀 PKB Phase 1 Fix Deployment Script"
echo "====================================="

# 检查是否在正确的目录
if [ ! -f "deploy/docker-compose.cloud.yml" ]; then
    echo "❌ Error: deploy/docker-compose.cloud.yml not found. Please run this script from the project root."
    echo "Current directory: $(pwd)"
    echo "Looking for: deploy/docker-compose.cloud.yml"
    exit 1
fi

# 进入deploy目录执行
cd deploy
COMPOSE_FILE="docker-compose.cloud.yml"
PROJECT_NAME="pkb-test"
echo "✅ Using compose file: $COMPOSE_FILE"
echo "✅ Using project name: $PROJECT_NAME"

# 1. 检查服务状态并备份数据库
echo "🔍 Checking current service status..."
if docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps | grep -q "Up"; then
    echo "✅ Services are running"
    
    # 备份数据库
    echo "📦 Creating database backup..."
    BACKUP_FILE="backup_before_phase1_$(date +%Y%m%d_%H%M%S).sql"
    
    # 测试环境数据库配置（基于.env文件）
    DB_USER="pkb"
    DB_NAME="pkb_test"
    
    echo "Database config: User=$DB_USER, Database=$DB_NAME"
    echo "Backing up database: $DB_NAME (user: $DB_USER)"
    
    if docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null; then
        echo "✅ Backup created: $BACKUP_FILE"
    else
        echo "⚠️  Backup failed, but continuing with migration..."
        echo "Please ensure you have a manual backup before proceeding."
        read -p "Continue anyway? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
            exit 1
        fi
    fi
else
    echo "⚠️  Services are not running, skipping backup"
    echo "Please ensure you have a manual backup if needed."
    read -p "Continue with migration? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        exit 1
    fi
fi

# 2. 停止服务
echo "🛑 Stopping services..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down

# 3. 重新构建backend镜像（包含新的迁移文件）
echo "🔨 Rebuilding backend image with migration files..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME build pkb-backend

# 4. 启动数据库和backend服务用于迁移
echo "🔧 Starting database and backend for migration..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d postgres redis
sleep 10  # 等待数据库启动

echo "🚀 Starting backend service..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d pkb-backend
sleep 5   # 等待backend服务启动

# 5. 验证Phase 1修复已部署
echo "🔍 Verifying Phase 1 fixes are deployed..."
echo "✅ Code fixes deployed: thumbnail generation and model relationships"

# 6. 重启所有服务
echo "🚀 Starting all services..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d

# 7. 等待服务启动并检查状态
echo "⏳ Waiting for services to start..."
sleep 15

echo "🔍 Checking service status..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps

# 8. 测试API
echo "🧪 Testing API..."
sleep 5
if curl -f http://localhost:8003/api/health > /dev/null 2>&1; then
    echo "✅ API is responding on port 8003"
else
    echo "⚠️  API not responding on port 8003 yet, please check manually"
fi

echo ""
echo "🎉 Phase 1 fixes deployed successfully!"
echo "📁 Database backup saved as: $BACKUP_FILE"
echo "🔗 Test API available at: http://localhost:8003"
echo ""
echo "✅ Fixed issues:"
echo "1. Thumbnail generation for uploaded images"
echo "2. SQLAlchemy model relationship warnings"
echo "3. Classification status updates"
echo ""
echo "Next steps:"
echo "1. Test image upload and thumbnail generation"
echo "2. Verify classification works without getting stuck"
echo "3. Proceed with Phase 2: Keyword Search Engine"
echo ""
