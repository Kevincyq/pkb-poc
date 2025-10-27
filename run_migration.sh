#!/bin/bash
# 数据库迁移脚本：为collections表添加user_id字段

echo "======================================"
echo "  PKB 数据库迁移 - 添加user_id列"
echo "======================================"
echo ""

# 步骤1: 确认容器名称
echo "📍 步骤1: 查找PostgreSQL容器..."
POSTGRES_CONTAINER=$(docker ps --format "{{.Names}}" | grep -E "(postgres|pkb)" | head -1)

if [ -z "$POSTGRES_CONTAINER" ]; then
    echo "❌ 找不到PostgreSQL容器，请检查服务是否运行"
    echo "当前运行的容器："
    docker ps
    exit 1
fi

echo "✅ 找到容器: $POSTGRES_CONTAINER"
echo ""

# 步骤2: 检查列是否已存在
echo "📍 步骤2: 检查user_id列是否存在..."
EXISTS=$(docker exec -i $POSTGRES_CONTAINER psql -U pkb -d pkb -t -c "
SELECT EXISTS (
    SELECT 1 
    FROM information_schema.columns 
    WHERE table_name = 'collections' AND column_name = 'user_id'
);
" | tr -d ' ')

if [ "$EXISTS" = "t" ]; then
    echo "✅ user_id列已存在，无需迁移"
    exit 0
fi

echo "⏳ user_id列不存在，开始迁移..."
echo ""

# 步骤3: 执行迁移
echo "📍 步骤3: 添加user_id列..."
docker exec -i $POSTGRES_CONTAINER psql -U pkb -d pkb << 'SQL'
BEGIN;

-- 添加user_id列
ALTER TABLE collections 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);

-- 验证
SELECT 'Migration completed!' as status;

COMMIT;
SQL

if [ $? -eq 0 ]; then
    echo "✅ 迁移成功！"
else
    echo "❌ 迁移失败，请检查错误信息"
    exit 1
fi

echo ""

# 步骤4: 验证迁移
echo "📍 步骤4: 验证迁移结果..."
docker exec -i $POSTGRES_CONTAINER psql -U pkb -d pkb -c "
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'collections' 
AND column_name = 'user_id';
"

echo ""

# 步骤5: 重启后端服务
echo "📍 步骤5: 重启后端服务..."
cd /home/kevincyq/pkb-poc  # 修改为你的实际项目路径
docker-compose -f deploy/docker-compose.cloud.yml restart pkb-backend

if [ $? -eq 0 ]; then
    echo "✅ 后端重启成功"
else
    echo "⚠️  后端重启失败，请手动重启"
fi

echo ""
echo "======================================"
echo "  ✅ 迁移完成！"
echo "======================================"
echo ""
echo "📋 接下来请："
echo "  1. 等待30秒让后端完全启动"
echo "  2. 刷新浏览器页面"
echo "  3. 应该不再有500错误"
echo ""

