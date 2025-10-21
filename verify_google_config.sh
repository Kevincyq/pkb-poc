#!/bin/bash

# 验证Google OAuth配置脚本

echo "🔍 验证Google OAuth配置..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_var() {
    local var_name=$1
    local var_value=$2
    local required=$3
    
    if [ -z "$var_value" ] || [ "$var_value" == "your_"* ] || [ "$var_value" == "None" ]; then
        if [ "$required" == "true" ]; then
            echo -e "${RED}❌ $var_name 未配置或配置错误${NC}"
            echo "   当前值: $var_value"
            return 1
        else
            echo -e "${YELLOW}⚠️  $var_name 未配置（可选）${NC}"
            return 0
        fi
    else
        echo -e "${GREEN}✅ $var_name 已配置${NC}"
        echo "   值: $var_value"
        return 0
    fi
}

# 读取.env文件
if [ -f "deploy/.env" ]; then
    ENV_FILE="deploy/.env"
elif [ -f ".env" ]; then
    ENV_FILE=".env"
else
    echo -e "${RED}❌ 未找到.env文件${NC}"
    exit 1
fi

echo "📄 读取环境变量文件: $ENV_FILE"
echo ""

# 读取环境变量
GOOGLE_PROJECT_ID=$(grep "^GOOGLE_PROJECT_ID=" "$ENV_FILE" | cut -d '=' -f2)
GOOGLE_CLIENT_ID=$(grep "^GOOGLE_CLIENT_ID=" "$ENV_FILE" | cut -d '=' -f2)
GOOGLE_CLIENT_SECRET=$(grep "^GOOGLE_CLIENT_SECRET=" "$ENV_FILE" | cut -d '=' -f2)
GOOGLE_REDIRECT_URI=$(grep "^GOOGLE_REDIRECT_URI=" "$ENV_FILE" | cut -d '=' -f2)
GOOGLE_FIREBASE_API_KEY=$(grep "^GOOGLE_FIREBASE_API_KEY=" "$ENV_FILE" | cut -d '=' -f2)

# 检查是否使用了错误的变量名
GDRIVE_CLIENT_ID=$(grep "^GDRIVE_CLIENT_ID=" "$ENV_FILE" | cut -d '=' -f2)
GDRIVE_CLIENT_SECRET=$(grep "^GDRIVE_CLIENT_SECRET=" "$ENV_FILE" | cut -d '=' -f2)
GDRIVE_REDIRECT_URI=$(grep "^GDRIVE_REDIRECT_URI=" "$ENV_FILE" | cut -d '=' -f2)

if [ ! -z "$GDRIVE_CLIENT_ID" ] || [ ! -z "$GDRIVE_CLIENT_SECRET" ] || [ ! -z "$GDRIVE_REDIRECT_URI" ]; then
    echo -e "${RED}❌ 检测到错误的变量名！${NC}"
    echo ""
    echo "   你使用了: GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REDIRECT_URI"
    echo "   应该使用: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI"
    echo ""
    echo "   代码中读取的是 GOOGLE_* 而不是 GDRIVE_*"
    echo ""
fi

# 检查必需的变量
echo "1️⃣ 检查必需的Google OAuth配置"
echo "----------------------------------------"
check_var "GOOGLE_PROJECT_ID" "$GOOGLE_PROJECT_ID" "true"
check_var "GOOGLE_CLIENT_ID" "$GOOGLE_CLIENT_ID" "true"
check_var "GOOGLE_CLIENT_SECRET" "$GOOGLE_CLIENT_SECRET" "true"
check_var "GOOGLE_REDIRECT_URI" "$GOOGLE_REDIRECT_URI" "true"
echo ""

# 检查可选的变量
echo "2️⃣ 检查可选的Firebase配置（仅OAuth访问Google Drive不需要）"
echo "----------------------------------------"
check_var "GOOGLE_FIREBASE_API_KEY" "$GOOGLE_FIREBASE_API_KEY" "false"
echo ""

# 验证CLIENT_ID格式
echo "3️⃣ 验证配置格式"
echo "----------------------------------------"
if [[ "$GOOGLE_CLIENT_ID" == *".apps.googleusercontent.com"* ]]; then
    echo -e "${GREEN}✅ CLIENT_ID 格式正确${NC}"
else
    echo -e "${YELLOW}⚠️  CLIENT_ID 格式可能不正确${NC}"
    echo "   正确格式应为: xxxxx.apps.googleusercontent.com"
fi

if [[ "$GOOGLE_CLIENT_SECRET" == GOCSPX-* ]]; then
    echo -e "${GREEN}✅ CLIENT_SECRET 格式正确${NC}"
else
    echo -e "${YELLOW}⚠️  CLIENT_SECRET 格式可能不正确${NC}"
    echo "   正确格式应以 GOCSPX- 开头"
fi

if [[ "$GOOGLE_REDIRECT_URI" == http* ]]; then
    echo -e "${GREEN}✅ REDIRECT_URI 格式正确${NC}"
else
    echo -e "${RED}❌ REDIRECT_URI 格式错误${NC}"
    echo "   必须以 http:// 或 https:// 开头"
fi
echo ""

# 检查服务状态
echo "4️⃣ 检查Docker服务状态"
echo "----------------------------------------"
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    BACKEND_STATUS=$(docker ps --filter "name=pkb-backend" --format "{{.Status}}" 2>/dev/null | head -1)
    if [ ! -z "$BACKEND_STATUS" ]; then
        echo -e "${GREEN}✅ pkb-backend 容器运行中${NC}"
        echo "   状态: $BACKEND_STATUS"
    else
        echo -e "${RED}❌ pkb-backend 容器未运行${NC}"
        echo "   请运行: docker-compose -f docker-compose.cloud.yml up -d"
    fi
else
    echo -e "${YELLOW}⚠️  未检测到Docker环境${NC}"
fi
echo ""

# 测试API端点
echo "5️⃣ 测试Google OAuth端点"
echo "----------------------------------------"
BASE_URL="http://34.247.12.46:8010"
if [ ! -z "$GOOGLE_REDIRECT_URI" ]; then
    if [[ "$GOOGLE_REDIRECT_URI" == https://* ]]; then
        BASE_URL=$(echo "$GOOGLE_REDIRECT_URI" | sed 's|/api/auth/callback/gdrive||')
    fi
fi

echo "测试URL: $BASE_URL/api/auth/google"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/auth/google" 2>/dev/null)

if [ "$RESPONSE" == "307" ] || [ "$RESPONSE" == "302" ] || [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}✅ API端点可访问 (HTTP $RESPONSE)${NC}"
    
    # 获取授权URL
    AUTH_URL=$(curl -s -L "$BASE_URL/api/auth/google" 2>/dev/null | grep -o 'https://accounts.google.com[^"]*' | head -1)
    if [ ! -z "$AUTH_URL" ]; then
        echo ""
        echo "🔗 Google授权URL:"
        echo "$AUTH_URL"
        echo ""
        
        # 检查URL中的参数
        if [[ "$AUTH_URL" == *"client_id=None"* ]] || [[ "$AUTH_URL" == *"redirect_uri=None"* ]]; then
            echo -e "${RED}❌ 授权URL中包含 None 值！${NC}"
            echo "   这说明环境变量未正确加载到容器中"
            echo "   请运行: docker-compose -f docker-compose.cloud.yml restart pkb-backend"
        else
            echo -e "${GREEN}✅ 授权URL参数正确${NC}"
        fi
    fi
else
    echo -e "${RED}❌ API端点不可访问 (HTTP $RESPONSE)${NC}"
fi
echo ""

# 总结
echo "📋 配置总结"
echo "========================================"
echo ""
echo "✅ 正确的配置示例："
echo "   GOOGLE_PROJECT_ID=honghu-voe2"
echo "   GOOGLE_CLIENT_ID=196978552337-hi5i0398m6u9a37mk41cn78fso7v0rnl.apps.googleusercontent.com"
echo "   GOOGLE_CLIENT_SECRET=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"
echo "   GOOGLE_REDIRECT_URI=https://pkb-bak.kmchat.cloud/api/auth/callback/gdrive"
echo ""
echo "❌ 常见错误："
echo "   1. 使用 GDRIVE_* 而不是 GOOGLE_*"
echo "   2. 配置值为 None 或 your_*"
echo "   3. REDIRECT_URI 与 Google Cloud Console 不一致"
echo "   4. 环境变量修改后未重启服务"
echo ""
echo "🔧 如果配置有误，请："
echo "   1. 编辑 $ENV_FILE"
echo "   2. 确保变量名正确（GOOGLE_* 而不是 GDRIVE_*）"
echo "   3. 重启服务: docker-compose -f docker-compose.cloud.yml restart pkb-backend"
echo "   4. 再次运行此脚本验证"
echo ""
echo "📚 详细配置指南请参阅: GOOGLE_SETUP_GUIDE.md"
echo ""

