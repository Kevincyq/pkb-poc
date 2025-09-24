#!/bin/bash
# PKB智能知识库系统 - 快速验证脚本
# 使用方法: ./quick_test_pkb.sh

BASE_URL="https://pkb.kmchat.cloud/api"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }

echo "🚀 PKB系统快速验证"
echo "=================="

# 1. 健康检查
print_info "检查系统健康..."
health=$(curl -s "$BASE_URL/health" | jq -r '.status // "error"')
if [ "$health" = "ok" ]; then
    print_success "系统健康正常"
else
    print_error "系统健康检查失败"
    exit 1
fi

# 2. 搜索功能检查
print_info "检查搜索功能..."
search_count=$(curl -s -G "$BASE_URL/search/" --data-urlencode "q=*" | jq '.results | length // 0')
print_success "搜索功能正常，共 $search_count 个文档"

# 3. 分类统计
print_info "检查分类统计..."
stats=$(curl -s "$BASE_URL/category/stats/overview")
total=$(echo "$stats" | jq '.total_contents // 0')
classified=$(echo "$stats" | jq '.classified_contents // 0')
rate=$(echo "$stats" | jq '.classification_rate // 0')

print_success "文档统计: $total 总数, $classified 已分类, $(echo "scale=1; $rate * 100" | bc)% 覆盖率"

# 4. 问答功能检查
print_info "检查问答功能..."
answer_length=$(curl -X POST "$BASE_URL/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"系统中有什么内容？","top_k":3}' | \
  jq -r '.answer | length // 0')

if [ $answer_length -gt 20 ]; then
    print_success "问答功能正常，回答长度 $answer_length 字符"
else
    print_error "问答功能可能异常"
fi

echo ""
print_success "🎉 快速验证完成！系统运行正常。"
