#!/bin/bash
# 修复测试依赖问题

echo "🔧 PKB 测试依赖修复工具"
echo "=================================="

# 检查当前目录
if [ ! -f "backend/requirements-test.txt" ]; then
    echo "❌ 错误: 请在项目根目录执行此脚本"
    exit 1
fi

cd backend

echo "📦 安装完整的测试依赖..."

# 方案1: 直接安装测试依赖文件
echo "尝试方案1: 安装 requirements-test.txt"
if pip3 install -r requirements-test.txt; then
    echo "✅ 测试依赖安装成功"
else
    echo "⚠️ 方案1失败，尝试方案2..."
    
    # 方案2: 分别安装基础依赖和测试依赖
    echo "安装基础应用依赖..."
    pip3 install fastapi sqlalchemy pydantic python-dateutil openai
    
    echo "安装测试框架依赖..."
    pip3 install pytest pytest-asyncio pytest-cov httpx pytest-mock
fi

echo ""
echo "🧪 验证依赖安装..."

# 验证关键依赖
python3 -c "import sqlalchemy; print('✅ sqlalchemy:', sqlalchemy.__version__)" 2>/dev/null || echo "❌ sqlalchemy 安装失败"
python3 -c "import fastapi; print('✅ fastapi:', fastapi.__version__)" 2>/dev/null || echo "❌ fastapi 安装失败"
python3 -c "import pytest; print('✅ pytest:', pytest.__version__)" 2>/dev/null || echo "❌ pytest 安装失败"
python3 -c "import pydantic; print('✅ pydantic:', pydantic.__version__)" 2>/dev/null || echo "❌ pydantic 安装失败"

echo ""
echo "🧪 测试 conftest.py 导入..."
export PYTHONPATH=$(pwd)
python3 -c "
try:
    import sys
    sys.path.insert(0, 'tests')
    from conftest import test_db
    print('✅ conftest.py 导入成功')
except Exception as e:
    print(f'❌ conftest.py 导入失败: {e}')
"

echo ""
echo "🚀 现在可以运行测试了:"
echo "   cd backend"
echo "   export PYTHONPATH=\$(pwd)"
echo "   python3 -m pytest tests/ -v"
