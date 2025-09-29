#!/bin/bash

# PKB 前端快速部署脚本
# 支持多个云平台部署

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置
FRONTEND_DIR="frontend"
API_BASE_URL="http://52.90.58.102:8002"

echo "🚀 PKB 前端部署脚本"
echo "==================="
echo ""

# 检查前端目录
if [ ! -d "$FRONTEND_DIR" ]; then
    log_error "前端目录不存在: $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR"

# 检查 package.json
if [ ! -f "package.json" ]; then
    log_error "未找到 package.json 文件"
    exit 1
fi

# 显示部署选项
echo "选择部署平台："
echo "1. Vercel (推荐)"
echo "2. Netlify"
echo "3. 构建静态文件"
echo "4. 本地预览"
echo ""
read -p "请选择 (1-4): " choice

case $choice in
    1)
        log_info "部署到 Vercel..."
        
        # 检查 Vercel CLI
        if ! command -v vercel &> /dev/null; then
            log_info "安装 Vercel CLI..."
            npm install -g vercel
        fi
        
        # 设置环境变量
        export VITE_API_BASE_URL="$API_BASE_URL"
        
        # 部署
        log_info "开始部署到 Vercel..."
        vercel --prod --env VITE_API_BASE_URL="$API_BASE_URL"
        
        log_success "Vercel 部署完成！"
        ;;
        
    2)
        log_info "部署到 Netlify..."
        
        # 检查 Netlify CLI
        if ! command -v netlify &> /dev/null; then
            log_info "安装 Netlify CLI..."
            npm install -g netlify-cli
        fi
        
        # 构建
        log_info "构建前端..."
        VITE_API_BASE_URL="$API_BASE_URL" npm run build
        
        # 部署
        log_info "开始部署到 Netlify..."
        netlify deploy --prod --dir=dist
        
        log_success "Netlify 部署完成！"
        ;;
        
    3)
        log_info "构建静态文件..."
        
        # 设置环境变量并构建
        VITE_API_BASE_URL="$API_BASE_URL" npm run build
        
        log_success "构建完成！文件位于 dist/ 目录"
        log_info "你可以将 dist/ 目录上传到任何静态文件托管服务"
        ;;
        
    4)
        log_info "本地预览..."
        
        # 构建
        VITE_API_BASE_URL="$API_BASE_URL" npm run build
        
        # 预览
        log_info "启动本地预览服务器..."
        npm run preview
        ;;
        
    *)
        log_error "无效选择"
        exit 1
        ;;
esac

echo ""
log_success "🎉 部署流程完成！"
echo ""
echo "📋 部署信息："
echo "  • API 地址: $API_BASE_URL"
echo "  • 前端构建: 完成"
echo ""
echo "🔧 后续步骤："
echo "1. 确保后端 CORS 配置包含前端域名"
echo "2. 测试前端功能是否正常"
echo "3. 配置自定义域名（可选）"
echo ""

# 显示 CORS 配置提醒
log_warning "重要提醒："
echo "请确保后端 .env 文件中的 CORS_ORIGINS 包含前端域名："
echo "CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000"
