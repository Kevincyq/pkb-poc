#!/bin/bash
# PKB Phase 1 部署脚本
# 用于在服务器端安全地部署第一阶段的数据模型更新

set -e  # 遇到错误立即退出

echo "🚀 PKB Phase 1 Deployment Script"
echo "=================================="

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

# 1. 备份数据库
echo "📦 Creating database backup..."
BACKUP_FILE="backup_before_phase1_$(date +%Y%m%d_%H%M%S).sql"

# 从docker-compose.yml中提取数据库配置
DB_USER=$(grep POSTGRES_USER docker-compose.yml | cut -d: -f2 | tr -d ' ' | head -1)
DB_NAME=$(grep POSTGRES_DB docker-compose.yml | cut -d: -f2 | tr -d ' ' | head -1)

if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ]; then
    echo "⚠️  Could not extract DB config from docker-compose.yml"
    echo "Please manually backup your database before proceeding."
    read -p "Continue anyway? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        exit 1
    fi
else
    echo "Backing up database: $DB_NAME (user: $DB_USER)"
    docker-compose exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"
    echo "✅ Backup created: $BACKUP_FILE"
fi

# 2. 停止服务
echo "🛑 Stopping services..."
docker-compose down

# 3. 启动数据库（只启动数据库用于迁移）
echo "🔧 Starting database for migration..."
docker-compose up -d postgres
sleep 10  # 等待数据库启动

# 4. 运行迁移
echo "🔄 Running Phase 1 migration..."
docker-compose exec -T backend python -m app.migrate_phase1 --force

if [ $? -eq 0 ]; then
    echo "✅ Migration completed successfully"
else
    echo "❌ Migration failed!"
    echo "Restoring from backup..."
    if [ -f "$BACKUP_FILE" ]; then
        docker-compose exec -T postgres psql -U "$DB_USER" "$DB_NAME" < "$BACKUP_FILE"
        echo "✅ Database restored from backup"
    fi
    exit 1
fi

# 5. 验证迁移结果
echo "🔍 Verifying migration..."
docker-compose exec -T backend python -c "
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
docker-compose up -d

# 7. 等待服务启动并检查状态
echo "⏳ Waiting for services to start..."
sleep 15

echo "🔍 Checking service status..."
docker-compose ps

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
