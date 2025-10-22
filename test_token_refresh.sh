#!/bin/bash

# Google Drive Token刷新测试脚本

if [ $# -lt 1 ]; then
    echo "使用方法: $0 <JWT_TOKEN>"
    echo "示例: $0 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'"
    exit 1
fi

JWT_TOKEN=$1
BASE_URL="http://34.247.12.46:8010"

echo "🔍 测试Google Drive Token刷新功能..."
echo "JWT Token: ${JWT_TOKEN:0:50}..."
echo ""

# 1. 检查当前云盘状态
echo "1️⃣ 检查当前云盘状态..."
CLOUD_STATUS=$(curl -s "$BASE_URL/api/cloud/status" -H "Authorization: Bearer $JWT_TOKEN")
echo "云盘状态:"
echo "$CLOUD_STATUS" | python3 -m json.tool
echo ""

# 2. 检查存储配置
echo "2️⃣ 检查存储配置..."
STORAGE_CONFIG=$(curl -s "$BASE_URL/api/ingest/storage-config" -H "Authorization: Bearer $JWT_TOKEN")
echo "存储配置:"
echo "$STORAGE_CONFIG" | python3 -m json.tool
echo ""

# 3. 创建小测试文件
echo "3️⃣ 创建测试文件..."
echo "Token刷新测试文件 - $(date)" > token_test.txt
echo "✅ 测试文件创建完成"
echo ""

# 4. 上传测试文件（应该触发Token刷新）
echo "4️⃣ 上传测试文件（可能触发Token刷新）..."
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/ingest/upload-smart" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@token_test.txt")

echo "上传响应:"
echo "$UPLOAD_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPLOAD_RESPONSE"
echo ""

# 5. 再次检查云盘状态（查看Token是否更新）
echo "5️⃣ 再次检查云盘状态..."
CLOUD_STATUS_AFTER=$(curl -s "$BASE_URL/api/cloud/status" -H "Authorization: Bearer $JWT_TOKEN")
echo "更新后的云盘状态:"
echo "$CLOUD_STATUS_AFTER" | python3 -m json.tool
echo ""

# 6. 清理测试文件
echo "6️⃣ 清理测试文件..."
rm -f token_test.txt
echo "✅ 测试文件已清理"
echo ""

echo "🎉 Token刷新测试完成！"
echo ""
echo "💡 检查要点："
echo "   - 上传是否成功（storage_strategy应该是cloud）"
echo "   - Token过期时间是否更新"
echo "   - 后端日志是否显示Token刷新信息"
echo "   - Google Drive中是否出现测试文件"
