#!/bin/bash

# URL编码函数
urlencode() {
    local string="${1}"
    local strlen=${#string}
    local encoded=""
    local pos c o

    for (( pos=0 ; pos<strlen ; pos++ )); do
        c=${string:$pos:1}
        case "$c" in
            [-_.~a-zA-Z0-9] ) o="${c}" ;;
            * )               printf -v o '%%%02x' "'$c"
        esac
        encoded+="${o}"
    done
    echo "${encoded}"
}

# 1. 测试关键词搜索
echo "=== [1] 关键词搜索测试 ==="
QUERY=$(urlencode "风力发电")
curl -s "https://pkb.kmchat.cloud/api/search/?q=${QUERY}&search_type=keyword" | jq '.'

# 2. 测试语义搜索
echo -e "\n=== [2] 语义搜索测试 ==="
QUERY=$(urlencode "海边的风景")
curl -s "https://pkb.kmchat.cloud/api/search/?q=${QUERY}&search_type=semantic" | jq '.'

# 3. 测试混合搜索
echo -e "\n=== [3] 混合搜索测试 ==="
QUERY=$(urlencode "日落时分的景色")
curl -s "https://pkb.kmchat.cloud/api/search/?q=${QUERY}&search_type=hybrid" | jq '.'

# 4. 测试分类搜索
echo -e "\n=== [4] 分类搜索测试 ==="
CATEGORY_ID=$(docker exec -i deploy-postgres-1 psql -U pkb -d pkb -t -A -c "select id from categories where name='生活点滴' limit 1;")
curl -s "https://pkb.kmchat.cloud/api/search/category/${CATEGORY_ID}" | jq '.'

# 5. 检查分类统计
echo -e "\n=== [5] 分类统计 ==="
curl -s "https://pkb.kmchat.cloud/api/category/stats/overview" | jq '.'

# 6. 检查向量索引
echo -e "\n=== [6] 向量索引状态 ==="
docker exec -i deploy-postgres-1 psql -U pkb -d pkb -f /check_vector_index.sql