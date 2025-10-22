#!/bin/bash

# 简化的Google OAuth测试脚本

if [ $# -ne 2 ]; then
    echo "使用方法: $0 <code> <state>"
    echo "示例: $0 '4/0AVGzR1B0YSaraSMgf1g8gANF0foZhw4A3qFAzIc38xIh2vkGKyzGjQjfrWVkAkszc5ochw' 'gdrive_xxx'"
    exit 1
fi

CODE=$1
STATE=$2
BASE_URL="http://34.247.12.46:8010"

echo "🔍 测试简化的Google OAuth授权..."
echo "Code: $CODE"
echo "State: $STATE"
echo ""

# 步骤1：测试OAuth回调
echo "1️⃣ 测试OAuth回调处理..."
CALLBACK_RESPONSE=$(curl -s "$BASE_URL/api/auth/callback/gdrive?code=$CODE&state=$STATE&scope=https://www.googleapis.com/auth/drive.file")
echo "回调响应:"
echo "$CALLBACK_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CALLBACK_RESPONSE"
echo ""

# 检查是否成功
if echo "$CALLBACK_RESPONSE" | grep -q '"success":true'; then
    echo "✅ OAuth回调处理成功！"
    
    # 提取JWT token
    JWT_TOKEN=$(echo "$CALLBACK_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$JWT_TOKEN" ]; then
        echo "🔑 JWT Token: $JWT_TOKEN"
        echo ""
        
        # 步骤2：获取用户信息
        echo "2️⃣ 获取Google用户信息..."
        USER_INFO=$(curl -s "$BASE_URL/api/auth/me" -H "Authorization: Bearer $JWT_TOKEN")
        echo "$USER_INFO" | python3 -m json.tool 2>/dev/null || echo "$USER_INFO"
        echo ""
        
        # 步骤3：检查云盘状态
        echo "3️⃣ 检查云盘连接状态..."
        CLOUD_STATUS=$(curl -s "$BASE_URL/api/cloud/status" -H "Authorization: Bearer $JWT_TOKEN")
        echo "$CLOUD_STATUS" | python3 -m json.tool 2>/dev/null || echo "$CLOUD_STATUS"
        echo ""
        
        # 步骤4：检查云盘提供商
        echo "4️⃣ 检查可用云盘提供商..."
        PROVIDERS=$(curl -s "$BASE_URL/api/cloud/providers" -H "Authorization: Bearer $JWT_TOKEN")
        echo "$PROVIDERS" | python3 -m json.tool 2>/dev/null || echo "$PROVIDERS"
        echo ""
        
        echo "🎉 测试完成！简化的Google OAuth授权成功！"
        echo ""
        echo "📋 关键改进："
        echo "   ✅ 移除了Google User Info API调用"
        echo "   ✅ 直接测试Drive API访问权限"
        echo "   ✅ 简化了用户创建流程"
        echo "   ✅ 只关注Drive访问权限"
    else
        echo "❌ 未获取到JWT Token"
    fi
else
    echo "❌ OAuth回调处理失败"
    echo "错误: $CALLBACK_RESPONSE"
fi
