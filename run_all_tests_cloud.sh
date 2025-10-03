#!/bin/bash
# 云端服务器完整测试执行脚本

set -e  # 遇到错误立即退出

echo "🚀 PKB 云端测试执行器"
echo "=================================="

# 检查当前目录
if [ ! -f "package.json" ] && [ ! -f "backend/requirements.txt" ]; then
    echo "❌ 错误: 请在项目根目录执行此脚本"
    exit 1
fi

# 1. 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin feature/search-enhance

# 2. 后端测试
echo ""
echo "🔧 执行后端测试..."
echo "--------------------------------"

cd backend

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 安装后端测试依赖
echo "📦 安装后端测试依赖..."
pip3 install pytest pytest-asyncio pytest-cov httpx pytest-mock

# 设置Python路径
export PYTHONPATH=$(pwd)

# 运行后端测试
echo "🧪 运行后端测试..."
python3 -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

BACKEND_EXIT_CODE=$?

# 3. 前端测试
echo ""
echo "🎨 执行前端测试..."
echo "--------------------------------"

cd ../frontend

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi

# 安装前端依赖
echo "📦 安装前端依赖..."
npm install

# 运行前端测试
echo "🧪 运行前端测试..."
npm test -- --run --reporter=verbose

FRONTEND_EXIT_CODE=$?

# 4. 测试结果汇总
echo ""
echo "📊 测试结果汇总"
echo "=================================="

if [ $BACKEND_EXIT_CODE -eq 0 ]; then
    echo "✅ 后端测试: 通过"
else
    echo "❌ 后端测试: 失败 (退出码: $BACKEND_EXIT_CODE)"
fi

if [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo "✅ 前端测试: 通过"
else
    echo "❌ 前端测试: 失败 (退出码: $FRONTEND_EXIT_CODE)"
fi

# 总体结果
if [ $BACKEND_EXIT_CODE -eq 0 ] && [ $FRONTEND_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "🎉 所有测试通过！系统可以安全部署"
    exit 0
else
    echo ""
    echo "⚠️ 部分测试失败，请检查并修复问题"
    exit 1
fi
