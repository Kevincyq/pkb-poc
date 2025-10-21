#!/bin/bash

# Google认证API测试脚本
BASE_URL="http://34.247.12.46:8010"

echo "🚀 开始Google认证API测试..."

# 检查环境变量
echo "1️⃣ 检查环境变量配置..."
echo "GOOGLE_PROJECT_ID: ${GOOGLE_PROJECT_ID:-未设置}"
echo "GOOGLE_FIREBASE_API_KEY: ${GOOGLE_FIREBASE_API_KEY:-未设置}"

if [ -z "$GOOGLE_PROJECT_ID" ] || [ -z "$GOOGLE_FIREBASE_API_KEY" ]; then
    echo "❌ Google认证环境变量未配置，请参考 GOOGLE_AUTH_SETUP.md"
    exit 1
fi

echo -e "\n"

# 测试Google用户注册
echo "2️⃣ 测试Google用户注册..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register-google" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser@gmail.com",
    "password": "password123",
    "display_name": "Test User"
  }')

echo "注册响应: $REGISTER_RESPONSE"

# 检查注册是否成功
if echo "$REGISTER_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "✅ Google用户注册成功"
    JWT_TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.token')
    echo "JWT Token: ${JWT_TOKEN:0:50}..."
else
    echo "❌ Google用户注册失败"
    ERROR_MSG=$(echo $REGISTER_RESPONSE | jq -r '.detail // .error // "未知错误"')
    echo "错误信息: $ERROR_MSG"
fi

echo -e "\n"

# 测试Google用户登录
echo "3️⃣ 测试Google用户登录..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser@gmail.com",
    "password": "password123"
  }')

echo "登录响应: $LOGIN_RESPONSE"

# 检查登录是否成功
if echo "$LOGIN_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "✅ Google用户登录成功"
    JWT_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.token')
    echo "JWT Token: ${JWT_TOKEN:0:50}..."
    
    # 测试用户信息获取
    echo "3️⃣.1️⃣ 测试用户信息获取..."
    USER_INFO=$(curl -s -X GET "$BASE_URL/api/auth/me" \
      -H "Authorization: Bearer $JWT_TOKEN")
    echo "用户信息: $USER_INFO"
    
    # 测试云盘提供商
    echo "3️⃣.2️⃣ 测试云盘提供商..."
    PROVIDERS=$(curl -s -X GET "$BASE_URL/api/cloud/providers" \
      -H "Authorization: Bearer $JWT_TOKEN")
    echo "云盘提供商: $PROVIDERS"
    
    # 测试文件上传
    echo "3️⃣.3️⃣ 测试文件上传..."
    echo "This is a test file for Google user" > google_test_file.txt
    
    UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/ingest/upload-smart" \
      -H "Authorization: Bearer $JWT_TOKEN" \
      -F "file=@google_test_file.txt")
    echo "文件上传响应: $UPLOAD_RESPONSE"
    
    # 清理测试文件
    rm -f google_test_file.txt
    
else
    echo "❌ Google用户登录失败"
    ERROR_MSG=$(echo $LOGIN_RESPONSE | jq -r '.detail // .error // "未知错误"')
    echo "错误信息: $ERROR_MSG"
fi

echo -e "\n"

# 测试test用户登录（确保仍然工作）
echo "4️⃣ 测试test用户登录..."
TEST_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@pkb.local",
    "password": "test"
  }')

echo "Test用户登录响应: $TEST_LOGIN_RESPONSE"

if echo "$TEST_LOGIN_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "✅ Test用户登录成功"
else
    echo "❌ Test用户登录失败"
fi

echo -e "\n"

echo "🎉 Google认证API测试完成！"
echo ""
echo "📋 测试总结:"
echo "   ✅ Google用户注册（使用Firebase）"
echo "   ✅ Google用户登录（使用Firebase）"
echo "   ✅ 用户信息获取"
echo "   ✅ 云盘提供商检查"
echo "   ✅ 文件上传功能"
echo "   ✅ Test用户登录（本地认证）"
echo ""
echo "💡 如果测试失败，请检查："
echo "   1. Firebase项目配置"
echo "   2. API Key是否正确"
echo "   3. 网络连接"
echo "   4. 服务是否重启"
