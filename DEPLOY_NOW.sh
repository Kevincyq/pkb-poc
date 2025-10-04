#!/bin/bash
# 快速部署脚本 - 问题1、3、5修复
# 执行时间：2025-10-04

set -e

echo "========================================="
echo "🚀 开始部署修复代码"
echo "========================================="

# 检查当前分支
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 当前分支: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "feature/search-enhance" ]; then
    echo "⚠️  警告：当前不在 feature/search-enhance 分支"
    echo "是否继续？(y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

# 显示修改文件
echo ""
echo "========================================="
echo "📝 查看修改文件"
echo "========================================="
git status

echo ""
echo "是否继续提交这些修改？(y/n)"
read -r response
if [ "$response" != "y" ]; then
    echo "❌ 取消部署"
    exit 1
fi

# 添加文件
echo ""
echo "========================================="
echo "➕ 添加修改文件到Git"
echo "========================================="
git add backend/app/services/category_service.py \
        backend/app/models.py \
        frontend/src/components/SearchOverlay/index.tsx \
        frontend/src/pages/Collection/Detail.tsx \
        frontend/src/types/qa.ts \
        frontend/src/components/QA/QAAssistant.tsx \
        frontend/src/components/QA/QAAssistant.module.css \
        FIXES_IMPLEMENTATION_COMPLETE.md

echo "✅ 文件已添加"

# 提交
echo ""
echo "========================================="
echo "💾 提交代码"
echo "========================================="
git commit -m "feat: 实施问题1、3、5修复

- 问题1：搜索结果跳转到合集并高亮文件，优化搜索触发方式
- 问题3：AI自动提取标签并在预览中显示
- 问题5：QA结果显示相关文档链接
- 问题4：验证合集关联逻辑正确（无需修改）

修改文件：
- backend/app/services/category_service.py (新增标签提取)
- backend/app/models.py (新增tags属性)
- frontend/src/components/SearchOverlay/index.tsx (跳转逻辑)
- frontend/src/pages/Collection/Detail.tsx (标签显示)
- frontend/src/types/qa.ts (扩展QAMessage)
- frontend/src/components/QA/QAAssistant.tsx (sources显示)
- frontend/src/components/QA/QAAssistant.module.css (样式)"

echo "✅ 代码已提交"

# 推送
echo ""
echo "========================================="
echo "📤 推送到远程仓库"
echo "========================================="
echo "正在推送到 origin/$CURRENT_BRANCH..."
git push origin "$CURRENT_BRANCH"

echo "✅ 代码已推送"

# 部署说明
echo ""
echo "========================================="
echo "✅ Git部署完成！"
echo "========================================="
echo ""
echo "📌 后续步骤："
echo ""
echo "1️⃣ 前端（Vercel）："
echo "   - Vercel会自动检测到推送并开始构建"
echo "   - 预览链接稍后会更新"
echo "   - 访问: https://pkb-poc-git-feature-search-enhance-kevincyqs-projects.vercel.app"
echo ""
echo "2️⃣ 后端（云服务器）："
echo "   SSH到云服务器，执行以下命令："
echo ""
echo "   cd /home/kevincyq/pkb-poc"
echo "   git pull origin feature/search-enhance"
echo "   cd deploy"
echo "   docker-compose -f docker-compose.cloud.yml -p pkb-test build pkb-backend"
echo "   docker-compose -f docker-compose.cloud.yml -p pkb-test restart pkb-backend pkb-worker"
echo ""
echo "3️⃣ 验证部署："
echo "   - 后端: curl https://pkb-test.kmchat.cloud/api/health"
echo "   - 前端: 访问Vercel预览链接"
echo ""
echo "========================================="
echo "🎉 部署脚本执行完成！"
echo "========================================="

