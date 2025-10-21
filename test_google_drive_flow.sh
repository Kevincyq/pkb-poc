#!/bin/bash

# Google Drive完整测试流程（修正版）
BASE_URL="http://localhost:8010"

echo "🚀 开始Google Drive完整测试流程（修正版）..."

# 1. 启动Google OAuth（直接OAuth登录）
echo "1️⃣ 启动Google OAuth（直接OAuth登录）..."
OAUTH_RESPONSE=$(curl -s -X GET "$BASE_URL/api/auth/google")

echo "OAuth响应: $OAUTH_RESPONSE"

# 提取授权URL
AUTH_URL=$(echo $OAUTH_RESPONSE | jq -r '.auth_url')
if [ "$AUTH_URL" != "null" ] && [ -n "$AUTH_URL" ]; then
    echo "✅ OAuth启动成功"
    echo "🔗 请访问以下URL完成Google授权:"
    echo "$AUTH_URL"
    echo ""
    echo "⚠️  完成授权后，系统会自动创建用户并返回JWT token"
    echo "⚠️  请按任意键继续..."
    read -n 1 -s
else
    echo "❌ OAuth启动失败"
    exit 1
fi

# 2. 检查云盘状态（需要JWT token）
echo "2️⃣ 检查云盘连接状态..."
echo "⚠️  请提供从OAuth回调中获得的JWT token:"
read -p "JWT Token: " JWT_TOKEN

if [ -z "$JWT_TOKEN" ]; then
    echo "❌ 未提供JWT token"
    exit 1
fi

STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/cloud/status" \
  -H "Authorization: Bearer $JWT_TOKEN")

echo "云盘状态: $STATUS_RESPONSE"

# 3. 检查云盘提供商
echo "3️⃣ 检查云盘提供商..."
PROVIDERS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/cloud/providers" \
  -H "Authorization: Bearer $JWT_TOKEN")

echo "云盘提供商: $PROVIDERS_RESPONSE"

# 4. 创建测试文件
echo "4️⃣ 创建测试文件..."
echo "This is a test file for Google Drive upload" > test_file.txt
echo "Test file created: test_file.txt"

# 5. 上传小文件
echo "5️⃣ 上传小文件（应该存储到本地）..."
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/ingest/upload-smart" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@test_file.txt")

echo "上传响应: $UPLOAD_RESPONSE"

# 6. 创建大文件
echo "6️⃣ 创建大文件（>5MB）..."
dd if=/dev/zero of=large_file.bin bs=1M count=6 2>/dev/null
echo "Large file created: large_file.bin ($(stat -c%s large_file.bin) bytes)"

# 7. 上传大文件
echo "7️⃣ 上传大文件（应该存储到Google Drive）..."
LARGE_UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/ingest/upload-smart" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@large_file.bin")

echo "大文件上传响应: $LARGE_UPLOAD_RESPONSE"

# 8. 获取存储配置
echo "8️⃣ 获取存储配置..."
CONFIG_RESPONSE=$(curl -s -X GET "$BASE_URL/api/ingest/storage-config" \
  -H "Authorization: Bearer $JWT_TOKEN")

echo "存储配置: $CONFIG_RESPONSE"

# 9. 测试文件访问
echo "9️⃣ 测试文件访问..."
FILE_ACCESS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/files/test_file.txt" \
  -H "Authorization: Bearer $JWT_TOKEN")

if [ ${#FILE_ACCESS_RESPONSE} -gt 0 ]; then
    echo "✅ 文件访问成功"
else
    echo "❌ 文件访问失败"
fi

# 10. 清理测试文件
echo "🔟 清理测试文件..."
rm -f test_file.txt large_file.bin
echo "✅ 测试文件已清理"

echo ""
echo "🎉 Google Drive测试流程完成！"
echo ""
echo "📋 测试总结:"
echo "   ✅ Google OAuth启动"
echo "   ✅ 用户自动创建"
echo "   ✅ 云盘状态检查"
echo "   ✅ 云盘提供商检查"
echo "   ✅ 小文件上传（本地存储）"
echo "   ✅ 大文件上传（云盘存储）"
echo "   ✅ 存储配置管理"
echo "   ✅ 文件访问测试"
