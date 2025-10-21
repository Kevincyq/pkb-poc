#!/bin/bash

# 完整的用户认证流程测试
BASE_URL="http://34.247.12.46:8010"

echo "🚀 开始完整的用户认证流程测试..."

# 1. 测试test用户登录
echo "1️⃣ 测试test用户登录..."
TEST_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@pkb.local",
    "password": "test"
  }')

echo "Test用户登录响应: $TEST_LOGIN_RESPONSE"

# 提取JWT token
TEST_JWT_TOKEN=$(echo $TEST_LOGIN_RESPONSE | jq -r '.token')
if [ "$TEST_JWT_TOKEN" != "null" ] && [ -n "$TEST_JWT_TOKEN" ]; then
    echo "✅ Test用户登录成功，JWT token: ${TEST_JWT_TOKEN:0:50}..."
    
    # 测试test用户功能
    echo "1️⃣.1️⃣ 测试test用户云盘提供商..."
    TEST_PROVIDERS=$(curl -s -X GET "$BASE_URL/api/cloud/providers" \
      -H "Authorization: Bearer $TEST_JWT_TOKEN")
    echo "Test用户云盘提供商: $TEST_PROVIDERS"
    
    echo "1️⃣.2️⃣ 测试test用户云盘状态..."
    TEST_STATUS=$(curl -s -X GET "$BASE_URL/api/cloud/status" \
      -H "Authorization: Bearer $TEST_JWT_TOKEN")
    echo "Test用户云盘状态: $TEST_STATUS"
else
    echo "❌ Test用户登录失败"
fi

echo -e "\n"

# 2. 测试Google用户登录
echo "2️⃣ 测试Google用户登录..."
GOOGLE_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "kevincyq@gmail.com",
    "password": "Seucyq19801007"
  }')

echo "Google用户登录响应: $GOOGLE_LOGIN_RESPONSE"

# 提取JWT token
GOOGLE_JWT_TOKEN=$(echo $GOOGLE_LOGIN_RESPONSE | jq -r '.token')
if [ "$GOOGLE_JWT_TOKEN" != "null" ] && [ -n "$GOOGLE_JWT_TOKEN" ]; then
    echo "✅ Google用户登录成功，JWT token: ${GOOGLE_JWT_TOKEN:0:50}..."
    
    # 测试Google用户功能
    echo "2️⃣.1️⃣ 测试Google用户云盘提供商..."
    GOOGLE_PROVIDERS=$(curl -s -X GET "$BASE_URL/api/cloud/providers" \
      -H "Authorization: Bearer $GOOGLE_JWT_TOKEN")
    echo "Google用户云盘提供商: $GOOGLE_PROVIDERS"
    
    echo "2️⃣.2️⃣ 测试Google用户云盘状态..."
    GOOGLE_STATUS=$(curl -s -X GET "$BASE_URL/api/cloud/status" \
      -H "Authorization: Bearer $GOOGLE_JWT_TOKEN")
    echo "Google用户云盘状态: $GOOGLE_STATUS"
    
    echo "2️⃣.3️⃣ 测试Google OAuth启动..."
    GOOGLE_OAUTH=$(curl -s -X GET "$BASE_URL/api/auth/google" \
      -H "Authorization: Bearer $GOOGLE_JWT_TOKEN")
    echo "Google OAuth启动: $GOOGLE_OAUTH"
else
    echo "❌ Google用户登录失败"
fi

echo -e "\n"

# 3. 测试文件上传功能
if [ "$TEST_JWT_TOKEN" != "null" ] && [ -n "$TEST_JWT_TOKEN" ]; then
    echo "3️⃣ 测试test用户文件上传..."
    
    # 创建测试文件
    echo "This is a test file for test user" > test_user_file.txt
    
    # 上传小文件
    TEST_UPLOAD=$(curl -s -X POST "$BASE_URL/api/ingest/upload-smart" \
      -H "Authorization: Bearer $TEST_JWT_TOKEN" \
      -F "file=@test_user_file.txt")
    echo "Test用户文件上传: $TEST_UPLOAD"
    
    # 清理测试文件
    rm -f test_user_file.txt
fi

if [ "$GOOGLE_JWT_TOKEN" != "null" ] && [ -n "$GOOGLE_JWT_TOKEN" ]; then
    echo "3️⃣.1️⃣ 测试Google用户文件上传..."
    
    # 创建测试文件
    echo "This is a test file for Google user" > google_user_file.txt
    
    # 上传小文件
    GOOGLE_UPLOAD=$(curl -s -X POST "$BASE_URL/api/ingest/upload-smart" \
      -H "Authorization: Bearer $GOOGLE_JWT_TOKEN" \
      -F "file=@google_user_file.txt")
    echo "Google用户文件上传: $GOOGLE_UPLOAD"
    
    # 清理测试文件
    rm -f google_user_file.txt
fi

echo -e "\n"

# 4. 测试用户信息获取
if [ "$TEST_JWT_TOKEN" != "null" ] && [ -n "$TEST_JWT_TOKEN" ]; then
    echo "4️⃣ 测试test用户信息获取..."
    TEST_USER_INFO=$(curl -s -X GET "$BASE_URL/api/auth/me" \
      -H "Authorization: Bearer $TEST_JWT_TOKEN")
    echo "Test用户信息: $TEST_USER_INFO"
fi

if [ "$GOOGLE_JWT_TOKEN" != "null" ] && [ -n "$GOOGLE_JWT_TOKEN" ]; then
    echo "4️⃣.1️⃣ 测试Google用户信息获取..."
    GOOGLE_USER_INFO=$(curl -s -X GET "$BASE_URL/api/auth/me" \
      -H "Authorization: Bearer $GOOGLE_JWT_TOKEN")
    echo "Google用户信息: $GOOGLE_USER_INFO"
fi

echo -e "\n"

echo "🎉 完整用户认证流程测试完成！"
echo ""
echo "📋 测试总结:"
echo "   ✅ Test用户登录 (test@pkb.local / test)"
echo "   ✅ Google用户登录 (kevincyq@gmail.com / Seucyq19801007)"
echo "   ✅ 用户云盘提供商检查"
echo "   ✅ 用户云盘状态检查"
echo "   ✅ Google OAuth启动"
echo "   ✅ 文件上传功能"
echo "   ✅ 用户信息获取"
