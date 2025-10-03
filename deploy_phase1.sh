#!/bin/bash
# PKB Phase 1 部署脚本
# 用于在服务器端安全地部署第一阶段的数据模型更新

set -e  # 遇到错误立即退出

echo "🚀 PKB Phase 1 Deployment Script"
echo "=================================="

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
    
    # 云端数据库配置（基于docker-compose.cloud.yml）
    DB_USER="pkb"
    DB_NAME="pkb"
    
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

# 3. 启动数据库和backend服务用于迁移
echo "🔧 Starting database and backend for migration..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d postgres redis
sleep 10  # 等待数据库启动

echo "🚀 Starting backend service..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d pkb-backend
sleep 5   # 等待backend服务启动

# 4. 运行迁移
echo "🔄 Running Phase 1 migration..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T pkb-backend python -m app.migrate_phase1 --force

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully"
else
    echo "❌ Migration failed!"
    if [ ! -z "$BACKUP_FILE" ] && [ -f "$BACKUP_FILE" ]; then
        echo "Restoring from backup..."
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d postgres
        sleep 5
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T postgres psql -U "pkb" "pkb" < "$BACKUP_FILE"
        echo "✅ Database restored from backup"
    else
        echo "⚠️  No backup file found, please restore manually if needed"
    fi
    exit 1
fi

# 5. 验证迁移结果
echo "🔍 Verifying migration..."
docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T pkb-backend python -c "
from app.db import SessionLocal
from sqlalchemy import text, inspect
import sys

try:
    db = SessionLocal()
    inspector = inspect(db.bind)
    
    # 检查新字段
    cc_columns = [col['name'] for col in inspector.get_columns('content_categories')]
    if 'role' in cc_columns and 'source' in cc_columns:
        print('✅ ContentCategory fields added successfully')
    else:
        print('❌ ContentCategory fields missing')
        sys.exit(1)
    
    # 检查新表
    tables = inspector.get_table_names()
    new_tables = ['tags', 'content_tags', 'signals']
    for table in new_tables:
        if table in tables:
            print(f'✅ {table} table created successfully')
        else:
            print(f'❌ {table} table missing')
            sys.exit(1)
    
    print('🎉 All verifications passed!')
    
finally:
    db.close()
"

if [ $? -eq 0 ]; then
    echo "✅ Migration verification passed"
else
    echo "❌ Migration verification failed"
    exit 1
fi

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
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is responding"
else
    echo "⚠️  API not responding yet, please check manually"
fi

echo ""
echo "🎉 Phase 1 deployment completed successfully!"
echo "📁 Database backup saved as: $BACKUP_FILE"
echo "🔗 API should be available at: http://localhost:8000"
echo ""
echo "Next steps:"
echo "1. Test the application functionality"
echo "2. Proceed with Phase 2: Keyword Search Engine"
echo ""
