#!/bin/bash
# 修复后的后端测试执行脚本

echo "🧪 PKB 后端测试执行器 (修复版)"
echo "=================================="

# 检查当前目录
if [ ! -f "backend/requirements-test.txt" ]; then
    echo "❌ 错误: 请在项目根目录执行此脚本"
    exit 1
fi

cd backend

echo "📦 安装测试依赖..."
# 只安装测试必需的依赖，不包含生产环境的 PostgreSQL 扩展
pip3 install pytest pytest-asyncio pytest-cov httpx pytest-mock fastapi sqlalchemy pydantic python-dateutil openai

echo "🔧 设置测试环境..."
# 设置Python路径
export PYTHONPATH=$(pwd)

# 设置测试环境变量（使用内存数据库）
export TESTING=true
export DATABASE_URL="sqlite:///:memory:"  # 使用内存SQLite数据库

echo "🧪 运行后端测试..."
echo "Python路径: $PYTHONPATH"
echo "当前目录: $(pwd)"

# 首先验证导入是否正常
echo "验证模块导入..."
python3 -c "
import sys
print('Python version:', sys.version)

# 验证Mock模型导入
try:
    from tests.mock_models import Content, Category
    print('✅ Mock模型导入成功')
except Exception as e:
    print('❌ Mock模型导入失败:', e)
    exit(1)

# 验证conftest导入
try:
    from tests.conftest import test_db
    print('✅ conftest导入成功')
except Exception as e:
    print('❌ conftest导入失败:', e)
    exit(1)

# 验证基础依赖
try:
    import sqlalchemy, fastapi, pytest
    print('✅ 基础依赖导入成功')
except Exception as e:
    print('❌ 基础依赖导入失败:', e)
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 模块导入验证失败，停止测试"
    exit 1
fi

# 运行测试
echo ""
echo "开始执行测试..."
python3 -m pytest tests/ -v --tb=short --no-header

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "🎉 后端测试全部通过！"
else
    echo "⚠️ 部分测试失败，请检查输出"
fi

exit $TEST_EXIT_CODE
