#!/bin/bash

# Google认证配置检查脚本
BASE_URL="http://34.247.12.46:8010"

echo "🔍 检查Google认证配置..."

# 1. 检查Google OAuth配置
echo "1️⃣ 检查Google OAuth配置..."
OAUTH_RESPONSE=$(curl -s -X GET "$BASE_URL/api/auth/google")

echo "OAuth响应: $OAUTH_RESPONSE"

if echo "$OAUTH_RESPONSE" | jq -e '.auth_url' > /dev/null 2>&1; then
    echo "✅ Google OAuth配置正确"
    AUTH_URL=$(echo $OAUTH_RESPONSE | jq -r '.auth_url')
    echo "授权URL: ${AUTH_URL:0:100}..."
else
    echo "❌ Google OAuth配置有问题"
    ERROR_MSG=$(echo $OAUTH_RESPONSE | jq -r '.detail // .error // "未知错误"')
    echo "错误信息: $ERROR_MSG"
fi

echo -e "\n"

# 2. 检查Google用户注册（测试Firebase配置）
echo "2️⃣ 检查Google用户注册（测试Firebase配置）..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register-google" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser@gmail.com",
    "password": "password123",
    "display_name": "Test User"
  }')

echo "注册响应: $REGISTER_RESPONSE"

if echo "$REGISTER_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "✅ Google Firebase配置正确"
else
    echo "❌ Google Firebase配置有问题"
    ERROR_MSG=$(echo $REGISTER_RESPONSE | jq -r '.detail // .error // "未知错误"')
    echo "错误信息: $ERROR_MSG"
fi

echo -e "\n"

# 3. 检查test用户（确保基本功能正常）
echo "3️⃣ 检查test用户（确保基本功能正常）..."
TEST_LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test",
    "password": "test"
  }')

echo "Test用户登录响应: $TEST_LOGIN_RESPONSE"

if echo "$TEST_LOGIN_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "✅ Test用户功能正常"
else
    echo "❌ Test用户功能有问题"
fi

echo -e "\n"

echo "🎉 配置检查完成！"
echo ""
echo "📋 配置状态总结:"
echo "   ✅ Test用户（test/test）- 硬编码用户，直接登录"
echo "   ❓ Google OAuth - 需要配置环境变量"
echo "   ❓ Google Firebase - 需要配置环境变量"
echo ""
echo "💡 需要配置的环境变量:"
echo "   # Google OAuth配置"
echo "   GOOGLE_CLIENT_ID=your_google_client_id"
echo "   GOOGLE_CLIENT_SECRET=your_google_client_secret"
echo "   GOOGLE_REDIRECT_URI=http://34.247.12.46:8010/api/auth/callback/gdrive"
echo ""
echo "   # Google Firebase配置"
echo "   GOOGLE_PROJECT_ID=your_google_project_id"
echo "   GOOGLE_FIREBASE_API_KEY=your_firebase_api_key"
echo ""
echo "🔗 配置指南: 请参考 GOOGLE_AUTH_SETUP.md"
