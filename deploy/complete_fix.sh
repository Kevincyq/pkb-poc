#!/bin/bash

echo "=== 完整修复方案 ==="

# 1. 诊断当前状态
echo "1. 诊断当前状态..."
echo "检查服务状态:"
docker-compose ps

echo -e "\n检查后端服务日志:"
docker-compose logs --tail=20 pkb-backend | head -20

# 2. 重新构建和启动
echo -e "\n2. 重新构建和启动..."
docker-compose down
docker-compose build pkb-backend
docker-compose up -d

# 3. 等待服务启动
echo "3. 等待服务启动..."
sleep 30

# 4. 检查服务是否正常
echo "4. 检查服务健康状态..."
for i in {1..10}; do
    echo "尝试 $i/10..."
    if curl -s https://pkb.kmchat.cloud/api/health > /dev/null; then
        echo "✓ 服务已启动"
        break
    else
        echo "× 服务未就绪，等待5秒..."
        sleep 5
    fi
done

# 5. 重置PDF数据
echo "5. 重置PDF数据..."
docker exec -i deploy-postgres-1 psql -U pkb_user -d pkb_db << 'EOF'
-- 查看领英报告当前状态
SELECT id, title, processing_status, char_length(text) as text_len FROM contents WHERE title LIKE '%领英%';

-- 重置状态
UPDATE contents 
SET 
    processing_status = null,
    text = '文档内容正在重新处理中...',
    updated_at = CURRENT_TIMESTAMP
WHERE title LIKE '%领英%';

-- 清理相关数据
DELETE FROM chunks WHERE content_id IN (SELECT id FROM contents WHERE title LIKE '%领英%');
DELETE FROM content_categories WHERE content_id IN (SELECT id FROM contents WHERE title LIKE '%领英%');

-- 添加搜索关键词
UPDATE contents 
SET meta = COALESCE(meta, '{}'::jsonb) || '{"keywords": ["领英", "LinkedIn", "AI人才", "人工智能", "全球AI", "人才报告"]}'::jsonb
WHERE title LIKE '%领英%';

-- 确认修改
SELECT id, title, processing_status, meta->'keywords' as keywords FROM contents WHERE title LIKE '%领英%';
EOF

# 6. 手动触发文件重新处理
echo "6. 手动触发文件重新处理..."
docker exec -i deploy-postgres-1 psql -U pkb_user -d pkb_db << 'EOF'
-- 获取领英报告的文件路径
SELECT id, title, source_uri FROM contents WHERE title LIKE '%领英%';
EOF

# 7. 重启相关服务来触发重新处理
echo "7. 重启处理服务..."
docker-compose restart pkb-auto-scan pkb-worker-heavy pkb-worker-classify

# 8. 等待处理完成
echo "8. 等待处理完成..."
sleep 60

# 9. 检查处理结果
echo "9. 检查处理结果..."
docker exec -i deploy-postgres-1 psql -U pkb_user -d pkb_db << 'EOF'
-- 检查文本是否已更新
SELECT 
    title, 
    processing_status, 
    CASE 
        WHEN char_length(text) > 100 THEN '已处理'
        ELSE '未处理'
    END as status,
    char_length(text) as text_len,
    (SELECT COUNT(*) FROM chunks WHERE content_id = contents.id) as chunk_count
FROM contents 
WHERE title LIKE '%领英%';
EOF

# 10. 测试搜索功能
echo "10. 测试搜索功能..."

echo "测试API健康状态:"
curl -s https://pkb.kmchat.cloud/api/health

echo -e "\n测试基础搜索 - 领英:"
curl -s "https://pkb.kmchat.cloud/api/search?q=领英" | python3 -m json.tool 2>/dev/null | head -10 || echo "搜索返回非JSON格式"

echo -e "\n测试基础搜索 - LinkedIn:"
curl -s "https://pkb.kmchat.cloud/api/search?q=LinkedIn" | python3 -m json.tool 2>/dev/null | head -10 || echo "搜索返回非JSON格式"

# 11. 如果搜索仍有问题，检查详细错误
echo -e "\n11. 详细错误检查..."
echo "搜索原始响应:"
response=$(curl -s "https://pkb.kmchat.cloud/api/search?q=领英")
echo "Response: $response"

if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
    echo "✓ JSON格式正确"
else
    echo "× JSON格式错误，检查后端日志:"
    docker-compose logs --tail=10 pkb-backend
fi

echo "=== 修复完成 ==="
