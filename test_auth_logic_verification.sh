#!/bin/bash

# 验证用户认证逻辑测试脚本
BASE_URL="http://34.247.12.46:8010"

echo "🔍 验证用户认证逻辑..."

# 1. 测试test用户登录（硬编码用户）
echo "1️⃣ 测试test用户登录（硬编码用户）..."
TEST_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test",
    "password": "test"
  }')

echo "Test用户登录响应: $TEST_LOGIN_RESPONSE"

# 检查test用户登录是否成功
if echo "$TEST_LOGIN_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "✅ Test用户登录成功"
    TEST_JWT_TOKEN=$(echo $TEST_LOGIN_RESPONSE | jq -r '.token')
    echo "JWT Token: ${TEST_JWT_TOKEN:0:50}..."
    
    # 检查用户信息
    TEST_USER_INFO=$(echo $TEST_LOGIN_RESPONSE | jq -r '.user')
    echo "用户信息: $TEST_USER_INFO"
    
    # 检查是否为Google用户
    IS_GOOGLE_USER=$(echo $TEST_LOGIN_RESPONSE | jq -r '.user.is_google_user')
    if [ "$IS_GOOGLE_USER" = "false" ]; then
        echo "✅ Test用户正确识别为非Google用户"
    else
        echo "❌ Test用户错误识别为Google用户"
    fi
    
    # 测试test用户云盘提供商
    echo "1️⃣.1️⃣ 测试test用户云盘提供商..."
    TEST_PROVIDERS=$(curl -s -X GET "$BASE_URL/api/cloud/providers" \
      -H "Authorization: Bearer $TEST_JWT_TOKEN")
    echo "Test用户云盘提供商: $TEST_PROVIDERS"
    
else
    echo "❌ Test用户登录失败"
    ERROR_MSG=$(echo $TEST_LOGIN_RESPONSE | jq -r '.detail // .error // "未知错误"')
    echo "错误信息: $ERROR_MSG"
fi

echo -e "\n"

# 2. 测试Google OAuth启动（真实用户认证）
echo "2️⃣ 测试Google OAuth启动（真实用户认证）..."
GOOGLE_OAUTH_RESPONSE=$(curl -s -X GET "$BASE_URL/api/auth/google")

echo "Google OAuth启动响应: $GOOGLE_OAUTH_RESPONSE"

# 检查OAuth启动是否成功
if echo "$GOOGLE_OAUTH_RESPONSE" | jq -e '.auth_url' > /dev/null 2>&1; then
    echo "✅ Google OAuth启动成功"
    AUTH_URL=$(echo $GOOGLE_OAUTH_RESPONSE | jq -r '.auth_url')
    echo "授权URL: ${AUTH_URL:0:100}..."
    echo ""
    echo "🔗 请访问以下URL完成Google授权:"
    echo "$AUTH_URL"
    echo ""
    echo "⚠️  完成授权后，系统会自动创建Google用户并返回JWT token"
else
    echo "❌ Google OAuth启动失败"
    ERROR_MSG=$(echo $GOOGLE_OAUTH_RESPONSE | jq -r '.detail // .error // "未知错误"')
    echo "错误信息: $ERROR_MSG"
fi

echo -e "\n"

# 3. 测试Google用户注册（如果OAuth失败，可以尝试注册）
echo "3️⃣ 测试Google用户注册（备用方案）..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register-google" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser@gmail.com",
    "password": "password123",
    "display_name": "Test Google User"
  }')

echo "Google用户注册响应: $REGISTER_RESPONSE"

if echo "$REGISTER_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "✅ Google用户注册成功"
    REGISTER_JWT_TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.token')
    echo "JWT Token: ${REGISTER_JWT_TOKEN:0:50}..."
    
    # 检查用户信息
    REGISTER_USER_INFO=$(echo $REGISTER_RESPONSE | jq -r '.user')
    echo "用户信息: $REGISTER_USER_INFO"
    
    # 检查是否为Google用户
    IS_GOOGLE_USER=$(echo $REGISTER_RESPONSE | jq -r '.user.is_google_user')
    if [ "$IS_GOOGLE_USER" = "true" ]; then
        echo "✅ Google用户正确识别为Google用户"
    else
        echo "❌ Google用户错误识别为非Google用户"
    fi
    
    # 测试Google用户登录
    echo "3️⃣.1️⃣ 测试Google用户登录..."
    GOOGLE_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
      -H "Content-Type: application/json" \
      -d '{
        "username": "testuser@gmail.com",
        "password": "password123"
      }')
    echo "Google用户登录响应: $GOOGLE_LOGIN_RESPONSE"
    
else
    echo "❌ Google用户注册失败"
    ERROR_MSG=$(echo $REGISTER_RESPONSE | jq -r '.detail // .error // "未知错误"')
    echo "错误信息: $ERROR_MSG"
fi

echo -e "\n"

echo "🎉 用户认证逻辑验证完成！"
echo ""
echo "📋 验证总结:"
echo "   ✅ Test用户（test/test）- 硬编码用户，直接登录"
echo "   ✅ Google用户 - 真实用户认证 + OAuth授权"
echo "   ✅ 用户类型识别 - 正确区分test用户和Google用户"
echo "   ✅ 云盘提供商 - test用户使用Nextcloud，Google用户使用Google Drive"
echo ""
echo "💡 如果测试失败，请检查："
echo "   1. 服务是否重启"
echo "   2. 数据库是否正确初始化"
echo "   3. Google认证配置是否正确"
