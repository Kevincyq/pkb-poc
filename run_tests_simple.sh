#!/bin/bash
# 简化的测试执行脚本，直接跳过复杂的验证

echo "🧪 PKB 简化测试执行器"
echo "=================================="

# 检查当前目录
if [ ! -f "backend/requirements-test.txt" ]; then
    echo "❌ 错误: 请在项目根目录执行此脚本"
    exit 1
fi

cd backend

echo "📦 安装测试依赖..."
pip3 install --user pytest pytest-asyncio pytest-cov httpx pytest-mock fastapi sqlalchemy pydantic python-dateutil openai

echo "🔧 设置测试环境..."
export PYTHONPATH=$(pwd)
export DATABASE_URL="sqlite:///:memory:"
export TESTING=true

echo "🧪 直接运行测试（跳过验证）..."
echo "Python路径: $PYTHONPATH"
echo "数据库URL: $DATABASE_URL"

# 创建临时的pgvector mock
echo "创建临时pgvector mock..."
cat > /tmp/mock_pgvector.py << 'EOF'
import sys
from unittest.mock import MagicMock

# Mock pgvector模块
pgvector_mock = MagicMock()
pgvector_sqlalchemy_mock = MagicMock()
pgvector_sqlalchemy_mock.Vector = lambda x: str  # Vector类型用str替代

sys.modules['pgvector'] = pgvector_mock
sys.modules['pgvector.sqlalchemy'] = pgvector_sqlalchemy_mock
EOF

# 运行测试，预先加载mock
python3 -c "
import sys
sys.path.insert(0, '/tmp')
import mock_pgvector
print('✅ pgvector mock加载成功')
"

# 运行pytest，在Python中预先加载mock
python3 -c "
exec(open('/tmp/mock_pgvector.py').read())
import subprocess
import sys
result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'], 
                       capture_output=False)
sys.exit(result.returncode)
"

TEST_EXIT_CODE=$?

# 清理临时文件
rm -f /tmp/mock_pgvector.py

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "🎉 测试执行完成！"
else
    echo "⚠️ 测试执行遇到问题，退出码: $TEST_EXIT_CODE"
fi

exit $TEST_EXIT_CODE
