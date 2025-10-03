# PKB 测试快速修复指南

## 🚨 问题总结
1. `DATABASE_URL` 环境变量为空导致 `app/db.py` 导入失败
2. 测试依赖安装路径问题

## 🛠️ 快速修复步骤

### 步骤1: 在云服务器上执行
```bash
cd /home/ec2-user/pkb-poc

# 拉取最新修复代码
git pull origin feature/search-enhance
```

### 步骤2: 安装依赖（选择其中一种方法）

#### 方法A: 使用系统Python
```bash
cd backend

# 安装基础依赖
sudo pip3 install sqlalchemy fastapi pydantic python-dateutil openai

# 安装测试依赖  
sudo pip3 install pytest pytest-asyncio pytest-cov httpx pytest-mock
```

#### 方法B: 使用用户安装
```bash
cd backend

# 安装到用户目录
pip3 install --user sqlalchemy fastapi pydantic python-dateutil openai pytest pytest-asyncio pytest-cov httpx pytest-mock
```

#### 方法C: 使用虚拟环境
```bash
cd backend

# 创建虚拟环境
python3 -m venv test_env
source test_env/bin/activate

# 安装依赖
pip install -r requirements-test.txt
```

### 步骤3: 运行测试
```bash
cd /home/ec2-user/pkb-poc/backend

# 设置环境变量
export PYTHONPATH=$(pwd)
export TESTING=true

# 运行测试
python3 -m pytest tests/ -v --tb=short
```

## 🎯 一键解决脚本

如果上述步骤太复杂，直接运行：
```bash
cd /home/ec2-user/pkb-poc
./run_backend_tests_fixed.sh
```

## 📋 验证修复

运行以下命令验证修复是否成功：
```bash
cd /home/ec2-user/pkb-poc/backend
export PYTHONPATH=$(pwd)

python3 -c "
try:
    from app.db import Base
    print('✅ app.db 导入成功')
except Exception as e:
    print('❌ app.db 导入失败:', e)

try:
    from tests.conftest import test_db
    print('✅ conftest 导入成功')
except Exception as e:
    print('❌ conftest 导入失败:', e)
"
```

## 🔧 如果还有问题

### 问题1: 权限问题
```bash
# 使用sudo安装
sudo pip3 install sqlalchemy fastapi pydantic pytest
```

### 问题2: Python版本问题
```bash
# 检查Python版本
python3 --version
# 需要Python 3.8+
```

### 问题3: 网络问题
```bash
# 使用国内镜像
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple/ sqlalchemy fastapi pydantic pytest
```

## 📊 预期结果

修复成功后，你应该看到：
```
================================== test session starts ==================================
collected 84 items

tests/test_category_service.py::TestCategoryService::test_init PASSED           [ 1%]
tests/test_category_service.py::TestCategoryService::test_get_system_categories PASSED [ 2%]
...
================================== 84 passed in 15.23s ==================================
```

## 💡 核心修复内容

1. **修复了 `app/db.py`**: 添加了 `DATABASE_URL` 检查，避免测试时连接真实数据库
2. **修复了 `conftest.py`**: 移除了不必要的 `get_db` 导入
3. **完善了依赖配置**: `requirements-test.txt` 包含了所有必要的依赖
