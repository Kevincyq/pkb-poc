#!/bin/bash
# ========================================
# 云服务器端一键部署脚本
# 使用方法：将此脚本复制到云服务器，然后执行
# ========================================

set -e

echo "======================================================================="
echo "🚀 PKB知识库 - 云服务器端部署"
echo "======================================================================="
echo ""
echo "当前目录: $(pwd)"
echo "当前用户: $(whoami)"
echo ""

# 进入项目目录
if [ ! -d "/home/kevincyq/pkb-poc" ]; then
    echo "❌ 错误：项目目录不存在 /home/kevincyq/pkb-poc"
    exit 1
fi

cd /home/kevincyq/pkb-poc

echo "✅ 已进入项目目录"
echo ""

# 检查当前分支
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 当前分支: $CURRENT_BRANCH"

# 拉取最新代码
echo ""
echo "======================================================================="
echo "📥 拉取最新代码"
echo "======================================================================="

git fetch origin
git pull origin feature/search-enhance

echo "✅ 代码已更新"

# 显示最新commit
echo ""
echo "最新提交："
git log -1 --oneline

# 进入部署目录
echo ""
echo "======================================================================="
echo "🏗️  开始重建Docker容器"
echo "======================================================================="

cd deploy

# 检查Docker是否运行
if ! docker ps > /dev/null 2>&1; then
    echo "❌ 错误：Docker未运行或无权限"
    exit 1
fi

echo "✅ Docker运行正常"
echo ""

# 重建后端容器
echo "正在重建 pkb-backend 容器..."
docker-compose -f docker-compose.cloud.yml -p pkb-test build pkb-backend

echo "✅ 容器重建完成"
echo ""

# 重启服务
echo "======================================================================="
echo "🔄 重启服务"
echo "======================================================================="

docker-compose -f docker-compose.cloud.yml -p pkb-test restart pkb-backend pkb-worker

echo "✅ 服务已重启"
echo ""

# 等待服务启动
echo "⏳ 等待服务启动（5秒）..."
sleep 5

# 检查服务状态
echo ""
echo "======================================================================="
echo "📊 检查服务状态"
echo "======================================================================="

docker-compose -f docker-compose.cloud.yml -p pkb-test ps

echo ""
echo "======================================================================="
echo "✅ 部署完成！"
echo "======================================================================="
echo ""
echo "📋 后续验证步骤："
echo ""
echo "1. 查看后端日志（实时）："
echo "   docker-compose -f docker-compose.cloud.yml -p pkb-test logs -f pkb-backend"
echo ""
echo "2. 查看问题2的调试日志（emoji标记）："
echo "   docker-compose -f docker-compose.cloud.yml -p pkb-test logs -f pkb-backend | grep -E \"(🔍|📋|📂|✅|⚠️|❌)\""
echo ""
echo "3. 健康检查："
echo "   curl http://localhost:8003/api/health"
echo ""
echo "4. 访问前端测试："
echo "   https://pkb-poc-git-feature-search-enhance-kevincyqs-projects.vercel.app"
echo ""
echo "======================================================================="
echo ""
echo "是否查看实时日志？(y/n)"
read -r response

if [ "$response" = "y" ]; then
    echo ""
    echo "开始查看实时日志（按Ctrl+C退出）..."
    echo ""
    docker-compose -f docker-compose.cloud.yml -p pkb-test logs -f pkb-backend | grep -E "(🔍|📋|📂|✅|⚠️|❌|INFO|ERROR)"
fi

