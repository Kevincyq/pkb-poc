#!/bin/bash
# 部署图片预览修复 - 问题2
# 执行环境：本地开发机

set -e

echo "========================================="
echo "🔧 部署图片预览修复（问题2）"
echo "========================================="

# 显示修改
echo ""
echo "📝 修改文件："
echo "   backend/app/api/files.py (增强文件查找日志)"
echo ""

# 确认
echo "是否继续部署？(y/n)"
read -r response
if [ "$response" != "y" ]; then
    echo "❌ 取消部署"
    exit 1
fi

# 提交代码
echo ""
echo "========================================="
echo "💾 提交代码"
echo "========================================="

git add backend/app/api/files.py DEBUG_IMAGE_PREVIEW_CLOUD.md

git commit -m "fix: 增强文件路径查找日志，修复中文文件名预览问题

问题：迪斯尼景酒套餐.jpg预览失败
原因：中文文件名+时间戳后缀导致文件查找失败
修复：增强日志，添加详细的文件查找trace

修改：
- backend/app/api/files.py: 添加emoji日志标记
- DEBUG_IMAGE_PREVIEW_CLOUD.md: 添加云端调试指南"

echo "✅ 代码已提交"

# 推送
echo ""
echo "========================================="
echo "📤 推送到远程仓库"
echo "========================================="

git push origin feature/search-enhance

echo "✅ 代码已推送"

# 部署说明
echo ""
echo "========================================="
echo "🚀 后续步骤（在云服务器上执行）"
echo "========================================="
echo ""
echo "1. SSH到云服务器："
echo "   ssh user@your-server"
echo ""
echo "2. 执行以下命令："
echo ""
cat << 'EOF'
cd /home/kevincyq/pkb-poc && \
git pull origin feature/search-enhance && \
cd deploy && \
docker-compose -f docker-compose.cloud.yml -p pkb-test build pkb-backend && \
docker-compose -f docker-compose.cloud.yml -p pkb-test restart pkb-backend && \
echo "✅ 部署完成，开始查看日志..." && \
docker-compose -f docker-compose.cloud.yml -p pkb-test logs -f pkb-backend | grep -E "(🔍|📋|📂|✅|⚠️|❌)"
EOF
echo ""
echo "3. 然后访问前端，点击'迪斯尼景酒套餐.jpg'预览"
echo "   观察日志中的emoji标记，了解文件查找过程"
echo ""
echo "========================================="
echo "📚 详细调试指南"
echo "========================================="
echo ""
echo "请查看: DEBUG_IMAGE_PREVIEW_CLOUD.md"
echo ""
echo "========================================="
echo "✅ 本地部署完成！"
echo "========================================="

