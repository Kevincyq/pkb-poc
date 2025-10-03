#!/bin/bash
# 检查服务器测试环境要求

echo "🔍 PKB 服务器测试环境检查"
echo "=================================="

# 检查操作系统
echo "📋 系统信息:"
echo "OS: $(uname -s)"
echo "Architecture: $(uname -m)"
echo "Kernel: $(uname -r)"
echo ""

# 检查Python环境
echo "🐍 Python环境检查:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python3: $PYTHON_VERSION"
    
    # 检查pip
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version)
        echo "✅ pip3: $PIP_VERSION"
    else
        echo "❌ pip3: 未安装"
    fi
else
    echo "❌ Python3: 未安装"
fi
echo ""

# 检查Node.js环境
echo "🟢 Node.js环境检查:"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js: $NODE_VERSION"
    
    # 检查npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        echo "✅ npm: $NPM_VERSION"
    else
        echo "❌ npm: 未安装"
    fi
else
    echo "❌ Node.js: 未安装"
fi
echo ""

# 检查Git
echo "📚 Git环境检查:"
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo "✅ Git: $GIT_VERSION"
else
    echo "❌ Git: 未安装"
fi
echo ""

# 检查磁盘空间
echo "💾 磁盘空间检查:"
df -h . | head -2
echo ""

# 检查内存
echo "🧠 内存检查:"
free -h
echo ""

# 检查网络连接
echo "🌐 网络连接检查:"
if ping -c 1 pypi.org &> /dev/null; then
    echo "✅ PyPI连接: 正常"
else
    echo "❌ PyPI连接: 失败"
fi

if ping -c 1 registry.npmjs.org &> /dev/null; then
    echo "✅ NPM Registry连接: 正常"
else
    echo "❌ NPM Registry连接: 失败"
fi
echo ""

# 总结
echo "📊 环境要求总结:"
echo "--------------------------------"
echo "最低要求:"
echo "- Python 3.8+ ✓"
echo "- Node.js 16+ ✓" 
echo "- 磁盘空间 2GB+ (用于依赖包)"
echo "- 内存 1GB+ (用于测试执行)"
echo "- 网络连接 (下载依赖)"
echo ""

# 给出建议
echo "💡 安装建议:"
if ! command -v python3 &> /dev/null; then
    echo "安装Python3: sudo apt update && sudo apt install python3 python3-pip"
fi

if ! command -v node &> /dev/null; then
    echo "安装Node.js: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
fi

echo ""
echo "🚀 准备就绪后，运行: ./run_all_tests_cloud.sh"
