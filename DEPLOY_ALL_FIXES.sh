#!/bin/bash
# ========================================
# 一次性部署所有5个问题的修复
# 执行时间：2025-10-04
# ========================================

set -e

echo "======================================================================="
echo "🚀 PKB知识库 - 问题1-5全面修复部署"
echo "======================================================================="
echo ""
echo "本次部署包含以下修复："
echo ""
echo "  ✅ 问题1：搜索结果跳转功能 - 点击跳转到合集并高亮文件"
echo "  🔍 问题2：特定图片预览失败 - 增强文件查找日志"
echo "  ✅ 问题3：标签体系建立 - AI自动提取关键词标签"
echo "  ✅ 问题4：合集关联逻辑 - 验证通过（无需修改）"
echo "  ✅ 问题5：QA结果文件链接 - 显示相关文档列表"
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
echo "后端修改："
echo "  - backend/app/services/category_service.py (标签提取)"
echo "  - backend/app/models.py (tags属性)"
echo "  - backend/app/api/files.py (文件查找增强)"
echo ""
echo "前端修改："
echo "  - frontend/src/components/SearchOverlay/index.tsx (搜索跳转)"
echo "  - frontend/src/pages/Collection/Detail.tsx (标签显示)"
echo "  - frontend/src/types/qa.ts (QA类型扩展)"
echo "  - frontend/src/components/QA/QAAssistant.tsx (sources显示)"
echo "  - frontend/src/components/QA/QAAssistant.module.css (样式)"
echo ""

git status

echo ""
echo "是否继续提交并部署这些修改？(y/n)"
read -r response
if [ "$response" != "y" ]; then
    echo "❌ 取消部署"
    exit 1
fi

# 添加所有修改文件
echo ""
echo "======================================================================="
echo "➕ 添加修改文件到Git"
echo "======================================================================="

git add \
    backend/app/services/category_service.py \
    backend/app/models.py \
    backend/app/api/files.py \
    frontend/src/components/SearchOverlay/index.tsx \
    frontend/src/pages/Collection/Detail.tsx \
    frontend/src/types/qa.ts \
    frontend/src/components/QA/QAAssistant.tsx \
    frontend/src/components/QA/QAAssistant.module.css \
    FIXES_IMPLEMENTATION_COMPLETE.md \
    DEBUG_IMAGE_PREVIEW_CLOUD.md \
    DEPLOY_ALL_FIXES.sh

echo "✅ 文件已添加"

# 提交代码
echo ""
echo "======================================================================="
echo "💾 提交代码"
echo "======================================================================="

git commit -m "feat: 一次性修复问题1-5

问题1 - 搜索结果跳转 ✅
- 添加handleResultClick函数实现跳转到合集并高亮文件
- 优化搜索触发方式为回车触发（避免频繁请求）

问题2 - 图片预览失败 🔍
- 增强files.py的文件查找日志（emoji标记）
- 支持中文文件名+时间戳后缀的正确处理

问题3 - 标签体系 ✅
- 后端：AI分类时自动提取5-8个关键词标签
- 后端：存储到Tag表和ContentTag表
- 后端：Content模型添加tags属性自动序列化
- 前端：文件预览中显示标签（蓝色Tag组件）

问题4 - 合集关联逻辑 ✅
- 验证现有实现正确，无需修改
- 创建用户合集时自动创建对应Category
- 自动匹配文档并创建ContentCategory（role=user_rule）

问题5 - QA文档链接 ✅
- 扩展QAMessage类型，添加sources字段
- QA助理显示相关文档列表
- 文档链接可点击跳转到合集
- 显示置信度百分比

修改文件：
后端：
- backend/app/services/category_service.py (新增标签提取，67行)
- backend/app/models.py (新增tags属性，14行)
- backend/app/api/files.py (增强日志，30行)

前端：
- frontend/src/components/SearchOverlay/index.tsx (跳转逻辑，20行)
- frontend/src/pages/Collection/Detail.tsx (标签显示，30行)
- frontend/src/types/qa.ts (类型扩展，8行)
- frontend/src/components/QA/QAAssistant.tsx (sources显示，40行)
- frontend/src/components/QA/QAAssistant.module.css (样式，44行)

总计：8个文件，约253行代码"

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
echo "预览链接："
echo "https://pkb-poc-git-feature-search-enhance-kevincyqs-projects.vercel.app"
echo ""
echo "构建状态："
echo "访问 https://vercel.com/dashboard 查看实时构建进度"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  后端部署（云服务器 - 手动）"
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
echo "3️⃣  验证部署（重要！）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "【问题1 - 搜索跳转】"
echo "  1. 访问前端，点击搜索图标"
echo "  2. 输入关键词，按回车搜索"
echo "  3. 点击搜索结果"
echo "  ✓ 验证：跳转到对应合集并高亮文件"
echo ""
echo "【问题2 - 图片预览】"
echo "  1. 进入"生活点滴"合集"
echo "  2. 找到"迪斯尼景酒套餐.jpg""
echo "  3. 点击预览"
echo "  ✓ 验证：图片正常显示"
echo "  📊 查看日志："
echo "     cd /home/kevincyq/pkb-poc/deploy"
echo "     docker-compose -f docker-compose.cloud.yml -p pkb-test \\"
echo "       logs -f pkb-backend | grep -E \"(🔍|📋|📂|✅|⚠️|❌)\""
echo ""
echo "【问题3 - 标签显示】"
echo "  1. 上传新文件（或查看已有文件）"
echo "  2. 等待AI分类完成"
echo "  3. 点击文件预览"
echo "  ✓ 验证：显示5-8个蓝色标签"
echo ""
echo "【问题4 - 合集关联】"
echo "  1. 创建用户合集"会议纪要""
echo "  2. 上传会议纪要文档"
echo "  3. 检查"职场商务"和"会议纪要"合集"
echo "  ✓ 验证：文档同时出现在两个合集中"
echo ""
echo "【问题5 - QA文档链接】"
echo "  1. 打开问答助理"
echo "  2. 提问：\"有哪些会议纪要？\""
echo "  3. 查看回答下方"相关文档"列表"
echo "  4. 点击文档链接"
echo "  ✓ 验证：跳转到对应合集并高亮文件"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  健康检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "后端API："
echo "  curl https://pkb-test.kmchat.cloud/api/health"
echo ""
echo "搜索API："
echo "  curl https://pkb-test.kmchat.cloud/api/search/health"
echo ""
echo "前端访问："
echo "  https://pkb-poc-git-feature-search-enhance-kevincyqs-projects.vercel.app"
echo ""
echo "======================================================================="
echo "📚 详细文档"
echo "======================================================================="
echo ""
echo "  📄 FIXES_IMPLEMENTATION_COMPLETE.md - 详细修复实施报告"
echo "  📄 DEBUG_IMAGE_PREVIEW_CLOUD.md - 图片预览调试指南"
echo ""
echo "======================================================================="
echo "🎉 本地部署脚本执行完成！"
echo "======================================================================="
echo ""
echo "请按照上述步骤完成云服务器部署和验证。"
echo "如有问题，请参考详细文档或查看日志。"
echo ""

