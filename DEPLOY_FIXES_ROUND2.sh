#!/bin/bash
# ========================================
# 第二轮修复部署 - 解决用户反馈的3个问题
# 执行时间：2025-10-04
# ========================================

set -e

echo "======================================================================="
echo "🔧 PKB知识库 - 第二轮问题修复部署"
echo "======================================================================="
echo ""
echo "本次修复包含以下问题："
echo ""
echo "  🖼️ 问题1：迪士尼图片预览失败 - 增强调试日志"
echo "  📁 问题2：合集关联逻辑问题 - 增强匹配算法和调试"
echo "  ❌ 问题3：搜索框X按钮功能错误 - 修改为清除功能"
echo ""
echo "======================================================================="

# 检查当前分支
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo ""
echo "📍 当前分支: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "feature/search-enhance" ]; then
    echo "⚠️  警告：当前不在 feature/search-enhance 分支"
    echo "是否继续？(y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

# 显示修改文件列表
echo ""
echo "======================================================================="
echo "📝 查看修改文件"
echo "======================================================================="
echo ""
echo "修改文件："
echo "  - frontend/src/components/SearchOverlay/index.tsx (搜索框X按钮修复)"
echo "  - backend/app/api/files.py (图片预览调试增强)"
echo "  - backend/app/services/collection_matching_service.py (合集匹配增强)"
echo ""

git status

echo ""
echo "是否继续提交并部署这些修改？(y/n)"
read -r response
if [ "$response" != "y" ]; then
    echo "❌ 取消部署"
    exit 1
fi

# 添加修改文件
echo ""
echo "======================================================================="
echo "➕ 添加修改文件到Git"
echo "======================================================================="

git add \
    frontend/src/components/SearchOverlay/index.tsx \
    backend/app/api/files.py \
    backend/app/services/collection_matching_service.py \
    DEPLOY_FIXES_ROUND2.sh

echo "✅ 文件已添加"

# 提交代码
echo ""
echo "======================================================================="
echo "💾 提交代码"
echo "======================================================================="

git commit -m "fix: 第二轮修复 - 解决用户反馈的3个问题

问题1 - 迪士尼图片预览失败 🖼️
- 增强files.py的文件查找调试日志
- 添加详细的步骤追踪（🔍 Step 1-4）
- 便于定位具体的查找失败环节

问题2 - 合集关联逻辑问题 📁
- 增强collection_matching_service.py的匹配算法
- 添加明显匹配检测（_is_obvious_match）
- 降低明显匹配的阈值（0.6 -> 0.3）
- 增强调试日志，显示匹配过程和分数
- 检查合集category_id关联状态

问题3 - 搜索框X按钮功能错误 ❌
- 修改SearchOverlay的X按钮功能
- 从关闭搜索框改为清除搜索内容
- 添加handleClearSearch函数
- 只在有搜索内容时显示X按钮
- 清除后自动聚焦输入框

修改文件：
- frontend/src/components/SearchOverlay/index.tsx (X按钮修复)
- backend/app/api/files.py (图片预览调试)
- backend/app/services/collection_matching_service.py (合集匹配增强)

预期效果：
1. 迪士尼图片预览：通过日志定位具体问题
2. 合集关联：提高匹配成功率，特别是明显匹配
3. 搜索体验：X按钮符合用户预期（清除而非关闭）"

echo "✅ 代码已提交"

# 推送到远程仓库
echo ""
echo "======================================================================="
echo "📤 推送到远程仓库"
echo "======================================================================="
echo "正在推送到 origin/$CURRENT_BRANCH..."

git push origin "$CURRENT_BRANCH"

echo "✅ 代码已推送到远程仓库"

# 部署说明
echo ""
echo "======================================================================="
echo "✅ Git部署完成！"
echo "======================================================================="
echo ""
echo "📌 后续步骤："
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  前端部署（Vercel - 自动）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Vercel会自动检测到Git推送并开始构建部署"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  后端部署（云服务器）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "请SSH到云服务器，执行以下命令："
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│  cd /home/kevincyq/pkb-poc &&                                │"
echo "│  git pull origin feature/search-enhance &&                   │"
echo "│  cd deploy &&                                                │"
echo "│  docker-compose -f docker-compose.cloud.yml -p pkb-test \\   │"
echo "│    build pkb-backend &&                                      │"
echo "│  docker-compose -f docker-compose.cloud.yml -p pkb-test \\   │"
echo "│    restart pkb-backend pkb-worker                            │"
echo "└─────────────────────────────────────────────────────────────┘"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  验证修复效果"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "【问题1 - 迪士尼图片预览】"
echo "  1. 进入\"生活点滴\"合集"
echo "  2. 点击\"迪士尼景酒套餐.jpg\""
echo "  3. 查看是否能正常预览"
echo "  📊 查看调试日志："
echo "     docker-compose -f docker-compose.cloud.yml -p pkb-test \\"
echo "       logs -f pkb-backend | grep -E \"(🔍|📋|📂|✅|⚠️|❌)\""
echo ""
echo "【问题2 - 合集关联】"
echo "  1. 创建\"旅游\"合集（如未创建）"
echo "  2. 上传包含\"迪士尼\"的图片"
echo "  3. 等待分类完成"
echo "  4. 检查\"生活点滴\"和\"旅游\"合集"
echo "  ✓ 验证：图片同时出现在两个合集中"
echo "  📊 查看匹配日志："
echo "     docker-compose -f docker-compose.cloud.yml -p pkb-test \\"
echo "       logs -f pkb-backend | grep -E \"(🔍|🎯|✅|❌)\""
echo ""
echo "【问题3 - 搜索框X按钮】"
echo "  1. 点击搜索图标打开搜索框"
echo "  2. 输入搜索内容"
echo "  3. 点击X按钮"
echo "  ✓ 验证：搜索内容被清除，搜索框保持打开"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  健康检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "后端API："
echo "  curl https://pkb-test.kmchat.cloud/api/health"
echo ""
echo "前端访问："
echo "  https://pkb-poc-git-feature-search-enhance-kevincyqs-projects.vercel.app"
echo ""
echo "======================================================================="
echo "🎉 本地部署脚本执行完成！"
echo "======================================================================="
echo ""
echo "请按照上述步骤完成云服务器部署和验证。"
echo "重点关注调试日志，帮助定位具体问题。"
echo ""
