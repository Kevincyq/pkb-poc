# PKB智能知识库系统 - 完整测试指南

## 📋 测试概述

本文档提供PKB智能知识库系统的完整端到端测试流程，验证从文件上传到智能问答的全链路功能。

### 🎯 测试目标
1. **文件上传与处理** - 验证文件自动扫描和处理
2. **智能分类** - 验证AI自动分类功能
3. **搜索功能** - 验证多种搜索模式
4. **智能问答** - 验证基于RAG的AI问答

### 🏗️ 系统架构
- **前端接入**: REST API
- **后端服务**: FastAPI + Python
- **数据库**: PostgreSQL + pgvector
- **AI服务**: Turing平台 + GPT-4o-mini
- **文件存储**: Nextcloud WebDAV
- **任务处理**: Celery + Redis

---

## 🚀 测试环境准备

### 📡 API基础信息
- **服务地址**: `https://pkb.kmchat.cloud`
- **API前缀**: `/api`
- **认证方式**: 无需认证（测试环境）

### 🛠️ 测试工具
```bash
# 必需工具
curl          # HTTP请求测试
jq            # JSON格式化
base64        # 文件编码（如需要）

# 可选工具
httpie        # 更友好的HTTP客户端
postman       # 图形化API测试
```

---

## 📝 完整测试流程

### 第一步：系统健康检查

#### 1.1 检查系统状态
```bash
# 健康检查
curl -s "https://pkb.kmchat.cloud/api/health" | jq '.'

# 期望输出
{
  "status": "ok"
}
```

#### 1.2 检查分类系统状态
```bash
# 分类统计
curl -s "https://pkb.kmchat.cloud/api/category/stats/overview" | jq '.'

# 期望输出示例
{
  "total_contents": 9,
  "classified_contents": 6,
  "classification_rate": 0.67,
  "categories": [
    {
      "name": "科技前沿",
      "count": 1,
      "color": "#2196F3"
    },
    {
      "name": "职场商务", 
      "count": 2,
      "color": "#FF9800"
    },
    {
      "name": "生活点滴",
      "count": 3,
      "color": "#4CAF50"
    }
  ]
}
```

### 第二步：文件上传与处理测试

#### 2.1 准备测试文件

**选项A：使用现有Nextcloud**
```bash
# 如果您有Nextcloud访问权限，直接上传文件到指定目录
# 支持的文件类型：
# - PDF: .pdf
# - 文档: .md, .txt, .docx
# - 图片: .jpg, .jpeg, .png, .gif, .bmp, .webp
```

**选项B：使用备忘录API（推荐测试）**
```bash
# 创建测试备忘录
curl -X POST "https://pkb.kmchat.cloud/api/ingest/memo" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试文档 - AI技术发展趋势",
    "content": "人工智能技术正在快速发展，特别是在自然语言处理、计算机视觉和机器学习等领域。ChatGPT和GPT-4等大语言模型的出现，标志着AI技术进入了新的发展阶段。这些技术在教育、医疗、金融等行业都有广泛应用前景。",
    "tags": ["AI", "技术", "发展趋势"],
    "category": "科技前沿"
  }' | jq '.'

# 期望输出
{
  "message": "备忘录创建成功",
  "content_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

#### 2.2 触发系统扫描
```bash
# 手动触发扫描（模拟自动扫描过程）
curl -X POST "https://pkb.kmchat.cloud/api/ingest/scan" \
  -H "Content-Type: application/json" | jq '.'

# 期望输出
{
  "message": "扫描完成",
  "processed_files": 1,
  "new_files": 0,
  "updated_files": 0,
  "deleted_files": 0
}
```

#### 2.3 验证文件处理状态
```bash
# 等待处理完成（通常需要10-30秒）
sleep 30

# 检查处理状态
curl -s -G "https://pkb.kmchat.cloud/api/search/" --data-urlencode "q=AI技术" | jq '.results[] | {title, modality, summary}'

# 期望看到新上传的文档出现在搜索结果中
```

### 第三步：智能分类验证

#### 3.1 检查分类结果
```bash
# 查看科技前沿分类
curl -G "https://pkb.kmchat.cloud/api/search/category/%E7%A7%91%E6%8A%80%E5%89%8D%E6%B2%BF" | jq '.results[] | {title, categories}'

# 期望输出：包含我们刚上传的AI相关文档
```

#### 3.2 验证分类统计更新
```bash
# 重新检查分类统计
curl -s "https://pkb.kmchat.cloud/api/category/stats/overview" | jq '.'

# 验证：科技前沿类别的文档数量应该增加
```

### 第四步：搜索功能全面测试

#### 4.1 关键词搜索测试
```bash
# 测试1：中文关键词搜索
curl -s -G "https://pkb.kmchat.cloud/api/search/" \
  --data-urlencode "q=人工智能" \
  --data-urlencode "search_type=keyword" | jq '.results[] | {title, score}'

# 测试2：英文关键词搜索  
curl -s -G "https://pkb.kmchat.cloud/api/search/" \
  --data-urlencode "q=AI" \
  --data-urlencode "search_type=keyword" | jq '.results[] | {title, score}'

# 测试3：混合关键词搜索
curl -s -G "https://pkb.kmchat.cloud/api/search/" \
  --data-urlencode "q=GPT ChatGPT" \
  --data-urlencode "search_type=keyword" | jq '.results[] | {title, score}'
```

#### 4.2 语义搜索测试
```bash
# 测试1：语义相似性搜索
curl -s -G "https://pkb.kmchat.cloud/api/search/" \
  --data-urlencode "q=机器学习的发展前景" \
  --data-urlencode "search_type=semantic" | jq '.results[] | {title, score}'

# 测试2：概念性搜索
curl -s -G "https://pkb.kmchat.cloud/api/search/" \
  --data-urlencode "q=科技创新趋势" \
  --data-urlencode "search_type=semantic" | jq '.results[] | {title, score}'
```

#### 4.3 混合搜索测试
```bash
# 混合搜索（推荐模式）
curl -s -G "https://pkb.kmchat.cloud/api/search/" \
  --data-urlencode "q=AI人工智能发展" \
  --data-urlencode "search_type=hybrid" | jq '.results[] | {title, score, search_type}'
```

#### 4.4 分类搜索测试
```bash
# 在特定分类中搜索
curl -s -G "https://pkb.kmchat.cloud/api/search/category/科技前沿" \
  --data-urlencode "q=技术" | jq '.results[] | {title, categories}'
```

### 第五步：智能问答系统测试

#### 5.1 基础问答测试
```bash
# 测试1：具体内容问答
curl -X POST "https://pkb.kmchat.cloud/api/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "AI技术有哪些主要发展趋势？",
    "top_k": 5
  }' | jq '.'

# 期望输出：基于文档内容的详细回答
```

#### 5.2 分类限定问答
```bash
# 测试2：在特定分类中问答
curl -X POST "https://pkb.kmchat.cloud/api/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "科技前沿领域有什么新发展？",
    "top_k": 3,
    "category_filter": "科技前沿"
  }' | jq '.'
```

#### 5.3 复杂问答测试
```bash
# 测试3：多文档综合问答
curl -X POST "https://pkb.kmchat.cloud/api/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "根据知识库中的内容，总结一下当前技术发展的主要特点",
    "top_k": 10
  }' | jq '.'
```

### 第六步：端到端完整流程测试

#### 6.1 创建测试场景
```bash
# 场景：上传一个关于职场技能的文档
curl -X POST "https://pkb.kmchat.cloud/api/ingest/memo" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "职场沟通技巧指南",
    "content": "有效的职场沟通是职业成功的关键。包括：1. 主动倾听技巧，理解他人观点；2. 清晰表达想法，使用简洁明了的语言；3. 非语言沟通，注意肢体语言和语调；4. 跨部门协作，建立良好的工作关系；5. 冲突解决，以建设性方式处理分歧。这些技能在现代职场环境中尤为重要。",
    "tags": ["职场", "沟通", "技能"],
    "category": "职场商务"
  }' | jq '.'
```

#### 6.2 等待处理并验证
```bash
# 等待处理
sleep 30

# 触发扫描
curl -X POST "https://pkb.kmchat.cloud/api/ingest/scan" \
  -H "Content-Type: application/json" | jq '.'

# 等待分类处理
sleep 20
```

#### 6.3 验证完整流程
```bash
# 1. 验证文档出现在搜索中
echo "=== 1. 搜索验证 ==="
curl -s -G "https://pkb.kmchat.cloud/api/search/" \
  --data-urlencode "q=沟通技巧" | jq '.results[] | {title, summary}'

# 2. 验证分类正确
echo "=== 2. 分类验证 ==="
curl -s "https://pkb.kmchat.cloud/api/search/category/职场商务" | jq '.results[] | select(.title | contains("沟通")) | {title, categories}'

# 3. 验证问答功能
echo "=== 3. 问答验证 ==="
curl -X POST "https://pkb.kmchat.cloud/api/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "如何提高职场沟通技巧？",
    "top_k": 5,
    "category_filter": "职场商务"
  }' | jq '.answer'

# 4. 验证分类统计更新
echo "=== 4. 统计验证 ==="
curl -s "https://pkb.kmchat.cloud/api/category/stats/overview" | jq '.categories[] | select(.name == "职场商务")'
```

---

## 🧪 自动化测试脚本

### 完整测试脚本
```bash
#!/bin/bash
# 保存为：pkb_full_test.sh

set -e  # 遇到错误立即退出

BASE_URL="https://pkb.kmchat.cloud/api"
CONTENT_TYPE="Content-Type: application/json"

echo "🚀 PKB智能知识库系统 - 完整测试开始"
echo "=================================="

# 函数：URL编码
urlencode() {
    python3 -c "import urllib.parse; print(urllib.parse.quote('$1'))"
}

# 函数：等待处理
wait_processing() {
    echo "⏳ 等待处理完成..."
    sleep $1
}

# 1. 系统健康检查
echo "📋 1. 系统健康检查"
echo "----------------"
health_status=$(curl -s "$BASE_URL/health" | jq -r '.status')
if [ "$health_status" = "ok" ]; then
    echo "✅ 系统健康状态正常"
else
    echo "❌ 系统健康检查失败"
    exit 1
fi

# 2. 上传测试文档
echo ""
echo "📄 2. 上传测试文档"
echo "----------------"
content_id=$(curl -X POST "$BASE_URL/ingest/memo" \
  -H "$CONTENT_TYPE" \
  -d '{
    "title": "测试文档-区块链技术应用",
    "content": "区块链技术作为一种分布式账本技术，正在金融、供应链、医疗等多个行业中找到应用场景。其去中心化、不可篡改的特性使其在数字货币、智能合约、数据验证等方面具有独特优势。随着技术成熟度提升，区块链有望在更多领域发挥重要作用。",
    "tags": ["区块链", "技术", "应用"],
    "category": "科技前沿"
  }' | jq -r '.content_id')

if [ "$content_id" != "null" ] && [ -n "$content_id" ]; then
    echo "✅ 文档上传成功，ID: $content_id"
else
    echo "❌ 文档上传失败"
    exit 1
fi

# 3. 触发扫描
echo ""
echo "🔄 3. 触发系统扫描"
echo "----------------"
curl -X POST "$BASE_URL/ingest/scan" -H "$CONTENT_TYPE" > /dev/null
echo "✅ 扫描触发成功"

# 等待处理
wait_processing 30

# 4. 验证搜索功能
echo ""
echo "🔍 4. 验证搜索功能"
echo "----------------"

# 关键词搜索
keyword_results=$(curl -s -G "$BASE_URL/search/" \
  --data-urlencode "q=区块链" \
  --data-urlencode "search_type=keyword" | jq '.results | length')
echo "✅ 关键词搜索结果: $keyword_results 个"

# 语义搜索
semantic_results=$(curl -s -G "$BASE_URL/search/" \
  --data-urlencode "q=分布式技术应用" \
  --data-urlencode "search_type=semantic" | jq '.results | length')
echo "✅ 语义搜索结果: $semantic_results 个"

# 5. 验证分类功能
echo ""
echo "🏷️  5. 验证智能分类"
echo "----------------"
wait_processing 20  # 等待分类处理

category_results=$(curl -s "$BASE_URL/search/category/科技前沿" | jq '.results | length')
echo "✅ 科技前沿分类文档数: $category_results 个"

# 6. 验证问答功能
echo ""
echo "🤖 6. 验证智能问答"
echo "----------------"
answer_length=$(curl -X POST "$BASE_URL/qa/ask" \
  -H "$CONTENT_TYPE" \
  -d '{
    "question": "区块链技术有哪些主要应用场景？",
    "top_k": 5
  }' | jq -r '.answer | length')

if [ "$answer_length" -gt 50 ]; then
    echo "✅ 智能问答功能正常，回答长度: $answer_length 字符"
else
    echo "❌ 智能问答功能异常"
fi

# 7. 最终统计
echo ""
echo "📊 7. 系统状态统计"
echo "----------------"
curl -s "$BASE_URL/category/stats/overview" | jq '.categories[] | "\(.name): \(.count) 个文档"'

echo ""
echo "🎉 完整测试流程执行完成！"
echo "========================"
```

### 运行测试脚本
```bash
# 赋予执行权限
chmod +x pkb_full_test.sh

# 运行测试
./pkb_full_test.sh
```

---

## 📊 测试结果验证标准

### ✅ 成功标准

#### 文件处理成功
- 文档成功创建，返回有效content_id
- 扫描处理无错误
- 文档出现在搜索结果中

#### 分类功能成功
- 文档自动分类到正确类别
- 分类统计数据更新
- 分类搜索能找到对应文档

#### 搜索功能成功
- 关键词搜索：返回相关结果
- 语义搜索：理解查询意图
- 混合搜索：综合多种匹配方式
- 分类搜索：在指定类别中搜索

#### 问答功能成功
- 基于文档内容生成准确回答
- 回答长度合理（通常>100字符）
- 引用相关文档作为依据
- 支持分类限定问答

### ❌ 失败排查

#### 常见问题及解决方案

**1. 系统健康检查失败**
```bash
# 检查服务状态
curl -I "https://pkb.kmchat.cloud/api/health"

# 如果返回404或500，联系系统管理员
```

**2. 文档上传失败**
```bash
# 检查请求格式
curl -X POST "https://pkb.kmchat.cloud/api/ingest/memo" \
  -H "Content-Type: application/json" \
  -d '{"title":"test","content":"test content"}' -v
```

**3. 搜索结果为空**
```bash
# 检查文档是否已处理
curl -s "https://pkb.kmchat.cloud/api/search/?q=*" | jq '.results | length'

# 如果为0，说明没有文档或处理未完成
```

**4. 分类功能异常**
```bash
# 检查分类服务状态
curl -s "https://pkb.kmchat.cloud/api/category/stats/overview" | jq '.classification_rate'

# 如果为0，说明分类服务未正常工作
```

**5. 问答功能异常**
```bash
# 简单问答测试
curl -X POST "https://pkb.kmchat.cloud/api/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"测试","top_k":1}' | jq '.answer'
```

---

## 🎯 高级测试场景

### 场景1：多模态内容测试
```bash
# 如果支持图片上传，测试图片处理
# （需要Nextcloud文件上传或base64编码）
```

### 场景2：大批量文档测试
```bash
# 批量创建多个文档，测试系统处理能力
for i in {1..5}; do
  curl -X POST "$BASE_URL/ingest/memo" \
    -H "$CONTENT_TYPE" \
    -d "{\"title\":\"批量测试文档$i\",\"content\":\"这是第$i个测试文档的内容...\"}"
  sleep 2
done
```

### 场景3：性能压力测试
```bash
# 并发搜索测试
for i in {1..10}; do
  curl -s -G "$BASE_URL/search/" --data-urlencode "q=测试" &
done
wait
```

---

## 📖 API参考文档

### 搜索API
```bash
GET /api/search/?q={query}&search_type={type}&top_k={number}

参数：
- q: 搜索关键词（必需）
- search_type: keyword|semantic|hybrid（默认hybrid）
- top_k: 返回结果数量（默认10）
```

### 问答API
```bash
POST /api/qa/ask
{
  "question": "问题内容",
  "top_k": 5,
  "category_filter": "分类名称"
}
```

### 分类API
```bash
GET /api/category/stats/overview          # 分类统计
GET /api/search/category/{category_name}  # 分类搜索
```

### 文档API
```bash
POST /api/ingest/memo     # 创建备忘录
POST /api/ingest/scan     # 触发扫描
```

---

## 🎉 测试完成检查清单

- [ ] ✅ 系统健康检查通过
- [ ] ✅ 文档上传成功
- [ ] ✅ 自动扫描处理完成
- [ ] ✅ 智能分类正确
- [ ] ✅ 关键词搜索正常
- [ ] ✅ 语义搜索正常
- [ ] ✅ 混合搜索正常
- [ ] ✅ 分类搜索正常
- [ ] ✅ 基础问答功能正常
- [ ] ✅ 分类限定问答正常
- [ ] ✅ 统计数据更新正确

**🎊 恭喜！如果以上所有项目都通过，说明PKB智能知识库系统运行完全正常！**

---

*测试文档版本: v1.0*  
*最后更新: 2024年9月*  
*系统版本: PKB v2.0*
