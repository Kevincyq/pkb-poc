# PKB智能知识库系统 - API接口文档

## 📋 概述

PKB（Personal Knowledge Base）智能知识库系统提供完整的RESTful API接口，支持文档管理、智能搜索、AI问答、分类管理等功能。

### 🌐 基础信息
- **服务地址**: `https://pkb.kmchat.cloud`
- **API前缀**: `/api`
- **文档地址**: `https://pkb.kmchat.cloud/api/docs`
- **认证方式**: 无需认证（当前版本）
- **数据格式**: JSON
- **字符编码**: UTF-8

### 🔧 CORS配置
系统已配置CORS，支持以下域名：
- `https://pkb.kmchat.cloud`
- `https://kb.kmchat.cloud`
- `https://nextcloud.kmchat.cloud`

---

## 🏥 系统健康检查

### GET /api/health
检查系统健康状态

**请求示例**:
```bash
curl "https://pkb.kmchat.cloud/api/health"
```

**响应示例**:
```json
{
  "status": "ok"
}
```

---

## 🔍 搜索接口 (/api/search)

### 1. GET /api/search/
智能搜索接口，支持多种搜索模式

**参数**:
- `q` (string, 必需): 搜索查询关键词
- `top_k` (int, 可选, 默认8): 返回结果数量
- `search_type` (string, 可选, 默认"hybrid"): 搜索类型
  - `keyword`: 关键词搜索
  - `semantic`: 语义搜索
  - `hybrid`: 混合搜索
- `modality` (string, 可选): 内容类型过滤 (`text`, `image`)
- `category` (string, 可选): 分类过滤

**请求示例**:
```bash
# 基础搜索
curl -G "https://pkb.kmchat.cloud/api/search/" \
  --data-urlencode "q=人工智能"

# 高级搜索
curl -G "https://pkb.kmchat.cloud/api/search/" \
  --data-urlencode "q=机器学习" \
  --data-urlencode "search_type=semantic" \
  --data-urlencode "top_k=10"
```

**响应示例**:
```json
{
  "query": "人工智能",
  "results": [
    {
      "id": "uuid-string",
      "title": "AI技术发展报告",
      "text": "人工智能技术正在快速发展...",
      "summary": "关于AI技术的详细报告",
      "modality": "text",
      "score": 0.95,
      "created_at": "2024-01-01T00:00:00",
      "categories": ["科技前沿"]
    }
  ],
  "total": 8,
  "response_time": 0.123,
  "search_type": "hybrid"
}
```

### 2. GET /api/search/suggestions
获取搜索建议

**参数**:
- `q` (string, 必需): 搜索查询前缀
- `limit` (int, 可选, 默认5): 建议数量

**请求示例**:
```bash
curl -G "https://pkb.kmchat.cloud/api/search/suggestions" \
  --data-urlencode "q=人工"
```

**响应示例**:
```json
{
  "suggestions": [
    "人工智能",
    "人工智能发展",
    "人工智能应用"
  ]
}
```

### 3. GET /api/search/category/{category_name}
在指定分类中搜索

**路径参数**:
- `category_name` (string): 分类名称

**查询参数**:
- `q` (string, 可选): 搜索关键词
- `top_k` (int, 可选, 默认10): 返回结果数量

**请求示例**:
```bash
curl -G "https://pkb.kmchat.cloud/api/search/category/科技前沿" \
  --data-urlencode "q=AI"
```

### 4. GET /api/search/categories/stats
获取分类搜索统计

**响应示例**:
```json
{
  "categories": [
    {
      "name": "科技前沿",
      "count": 15,
      "color": "#2196F3"
    }
  ]
}
```

---

## 🤖 问答接口 (/api/qa)

### 1. POST /api/qa/ask
智能问答接口，基于RAG技术

**请求体**:
```json
{
  "question": "人工智能有什么发展前景？",
  "session_id": "optional-session-id",
  "context_limit": 3000,
  "model": "gpt-4o-mini",
  "search_type": "hybrid",
  "category_filter": "科技前沿",
  "top_k": 5
}
```

**参数说明**:
- `question` (string, 必需): 用户问题
- `session_id` (string, 可选): 会话ID，用于上下文关联
- `context_limit` (int, 可选, 默认3000): 上下文长度限制
- `model` (string, 可选, 默认"gpt-4o-mini"): 使用的AI模型
- `search_type` (string, 可选, 默认"hybrid"): 搜索类型
- `category_filter` (string, 可选): 限定搜索的分类
- `top_k` (int, 可选, 默认5): 检索文档数量

**请求示例**:
```bash
curl -X POST "https://pkb.kmchat.cloud/api/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "人工智能技术有哪些应用场景？",
    "top_k": 5
  }'
```

**响应示例**:
```json
{
  "question": "人工智能技术有哪些应用场景？",
  "answer": "根据知识库中的内容，人工智能技术主要有以下应用场景：\n\n1. **自然语言处理**：包括机器翻译、语音识别、文本生成等...",
  "sources": [
    {
      "id": "uuid-string",
      "title": "AI技术应用报告",
      "text": "相关文档片段...",
      "score": 0.92
    }
  ],
  "session_id": "generated-session-id",
  "model": "gpt-4o-mini",
  "response_time": 1.234
}
```

### 2. GET /api/qa/history
获取问答历史

**参数**:
- `session_id` (string, 可选): 会话ID
- `limit` (int, 可选, 默认20): 返回数量

### 3. POST /api/qa/feedback
提供问答反馈

**请求体**:
```json
{
  "qa_id": "uuid-string",
  "feedback": "good"
}
```

### 4. GET /api/qa/sessions
获取会话列表

### 5. GET /api/qa/test
问答系统测试接口

---

## 🏷️ 分类管理接口 (/api/category)

### 1. GET /api/category/
获取所有分类列表

**参数**:
- `include_stats` (bool, 可选, 默认false): 是否包含统计信息

**请求示例**:
```bash
curl "https://pkb.kmchat.cloud/api/category/?include_stats=true"
```

**响应示例**:
```json
{
  "categories": [
    {
      "id": "uuid-string",
      "name": "科技前沿",
      "description": "科技创新和前沿技术",
      "color": "#2196F3",
      "is_system": true,
      "content_count": 15,
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

### 2. GET /api/category/{category_id}
获取指定分类详情

**路径参数**:
- `category_id` (string): 分类ID

### 3. POST /api/category/initialize
初始化系统预设分类

**请求示例**:
```bash
curl -X POST "https://pkb.kmchat.cloud/api/category/initialize"
```

**响应示例**:
```json
{
  "message": "系统分类初始化完成",
  "initialized_categories": [
    "科技前沿",
    "职场商务",
    "学习成长",
    "生活点滴"
  ]
}
```

### 4. POST /api/category/classify
对单个内容进行分类

**请求体**:
```json
{
  "content_id": "uuid-string",
  "force_reclassify": false
}
```

### 5. POST /api/category/classify/batch
批量分类

**请求体**:
```json
{
  "content_ids": ["uuid1", "uuid2", "uuid3"],
  "force_reclassify": false
}
```

### 6. GET /api/category/stats/overview
获取分类统计概览

**响应示例**:
```json
{
  "total_contents": 50,
  "classified_contents": 35,
  "classification_rate": 0.7,
  "categories": [
    {
      "name": "科技前沿",
      "count": 15,
      "color": "#2196F3"
    },
    {
      "name": "职场商务",
      "count": 10,
      "color": "#FF9800"
    },
    {
      "name": "学习成长",
      "count": 5,
      "color": "#9C27B0"
    },
    {
      "name": "生活点滴",
      "count": 5,
      "color": "#4CAF50"
    }
  ]
}
```

### 7. GET /api/category/service/status
获取分类服务状态

### 8. GET /api/category/content/{content_id}/status
获取指定内容的分类状态

### 9. POST /api/category/reclassify/all
重新分类所有内容

### 10. POST /api/category/custom
创建自定义分类

**请求体**:
```json
{
  "name": "自定义分类",
  "description": "用户自定义的分类",
  "color": "#FF5722"
}
```

### 11. PUT /api/category/{category_id}
更新分类信息

### 12. DELETE /api/category/{category_id}
删除分类

---

## 📄 文档管理接口 (/api/ingest)

### 1. POST /api/ingest/memo
创建备忘录/文档

**请求体**:
```json
{
  "title": "文档标题",
  "content": "文档内容",
  "tags": ["标签1", "标签2"],
  "category": "科技前沿",
  "meta": {
    "source": "manual",
    "keywords": ["关键词1", "关键词2"]
  }
}
```

**请求示例**:
```bash
curl -X POST "https://pkb.kmchat.cloud/api/ingest/memo" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI技术发展趋势",
    "content": "人工智能技术正在快速发展，包括机器学习、深度学习等领域...",
    "tags": ["AI", "技术", "趋势"],
    "category": "科技前沿"
  }'
```

**响应示例**:
```json
{
  "message": "备忘录创建成功",
  "content_id": "uuid-string",
  "title": "AI技术发展趋势"
}
```

### 2. POST /api/ingest/scan
触发系统扫描

扫描Nextcloud中的新文件并处理

**请求示例**:
```bash
curl -X POST "https://pkb.kmchat.cloud/api/ingest/scan" \
  -H "Content-Type: application/json"
```

**响应示例**:
```json
{
  "message": "扫描完成",
  "processed_files": 5,
  "new_files": 2,
  "updated_files": 1,
  "deleted_files": 0
}
```

### 3. POST /api/ingest/file
直接上传文件

**请求体**: multipart/form-data
- `file`: 文件数据
- `title` (可选): 文件标题
- `category` (可选): 分类

---

## 📊 文档处理接口 (/api/document)

### 1. GET /api/document/validate/{filename}
验证文件格式

**路径参数**:
- `filename` (string): 文件名

**响应示例**:
```json
{
  "filename": "document.pdf",
  "is_valid": true,
  "file_type": "pdf",
  "supported_parsers": ["pdf_parser"],
  "estimated_size": "2.5MB"
}
```

### 2. GET /api/document/formats
获取支持的文件格式

**响应示例**:
```json
{
  "supported_formats": {
    "text": [".txt", ".md", ".rtf"],
    "pdf": [".pdf"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "office": [".docx", ".xlsx", ".pptx"]
  }
}
```

### 3. POST /api/document/parse-text
解析文本内容

**请求体**:
```json
{
  "text": "要解析的文本内容",
  "parser_type": "auto"
}
```

### 4. GET /api/document/list
获取文档列表

**参数**:
- `page` (int, 可选, 默认1): 页码
- `size` (int, 可选, 默认20): 每页数量
- `modality` (string, 可选): 内容类型过滤

### 5. GET /api/document/chunks
获取文档块信息

**参数**:
- `content_id` (string, 可选): 内容ID
- `limit` (int, 可选, 默认100): 返回数量

### 6. GET /api/document/stats
获取文档统计信息

**响应示例**:
```json
{
  "total_documents": 100,
  "total_chunks": 500,
  "by_modality": {
    "text": 80,
    "image": 20
  },
  "avg_chunk_size": 512
}
```

---

## 🧮 向量嵌入接口 (/api/embedding)

### 1. GET /api/embedding/info
获取嵌入服务信息

**响应示例**:
```json
{
  "model": "text-embedding-ada-002",
  "dimensions": 1536,
  "max_tokens": 8192,
  "status": "active"
}
```

### 2. GET /api/embedding/test
测试嵌入服务

### 3. POST /api/embedding/embed
生成文本嵌入

**请求体**:
```json
{
  "text": "要生成嵌入的文本",
  "model": "text-embedding-ada-002"
}
```

**响应示例**:
```json
{
  "text": "要生成嵌入的文本",
  "embedding": [0.1, -0.2, 0.3, ...],
  "dimensions": 1536,
  "model": "text-embedding-ada-002"
}
```

### 4. POST /api/embedding/embed/batch
批量生成嵌入

### 5. POST /api/embedding/similarity
计算文本相似度

**请求体**:
```json
{
  "text1": "第一段文本",
  "text2": "第二段文本"
}
```

### 6. GET /api/embedding/models
获取可用的嵌入模型

### 7. GET /api/embedding/health
嵌入服务健康检查

---

## 🤖 智能代理接口 (/api/agent)

### 1. POST /api/agent/execute
执行智能代理任务

### 2. GET /api/agent/tasks/{task_id}
获取任务状态

### 3. POST /api/agent/plan
创建执行计划

### 4. GET /api/agent/tools
获取可用工具列表

### 5. POST /api/agent/mcp/register
注册MCP工具

### 6. POST /api/agent/mcp/call
调用MCP工具

### 7. GET /api/agent/mcp/tools
获取MCP工具列表

### 8. POST /api/agent/mcp/tools/{tool_name}/enable
启用MCP工具

### 9. POST /api/agent/mcp/tools/{tool_name}/disable
禁用MCP工具

### 10. POST /api/agent/mcp/initialize
初始化MCP系统

---

## ⚙️ 运维接口 (/api/operator)

### 1. POST /api/operator/commit
提交运维操作

---

## 🎯 前端对接指导

### 📱 前端架构建议

#### 1. 技术栈推荐
- **框架**: React/Vue.js/Angular
- **状态管理**: Redux/Vuex/NgRx
- **HTTP客户端**: Axios/Fetch API
- **UI组件库**: Ant Design/Element UI/Material-UI
- **路由**: React Router/Vue Router/Angular Router

#### 2. API客户端封装

**JavaScript/TypeScript 示例**:
```typescript
// api/client.ts
import axios from 'axios';

const API_BASE_URL = 'https://pkb.kmchat.cloud/api';

class PKBApiClient {
  private client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // 搜索接口
  async search(params: {
    q: string;
    top_k?: number;
    search_type?: 'keyword' | 'semantic' | 'hybrid';
    category?: string;
  }) {
    const response = await this.client.get('/search/', { params });
    return response.data;
  }

  // 问答接口
  async ask(data: {
    question: string;
    session_id?: string;
    category_filter?: string;
    top_k?: number;
  }) {
    const response = await this.client.post('/qa/ask', data);
    return response.data;
  }

  // 创建文档
  async createMemo(data: {
    title: string;
    content: string;
    tags?: string[];
    category?: string;
  }) {
    const response = await this.client.post('/ingest/memo', data);
    return response.data;
  }

  // 获取分类统计
  async getCategoryStats() {
    const response = await this.client.get('/category/stats/overview');
    return response.data;
  }

  // 系统健康检查
  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const pkbApi = new PKBApiClient();
```

#### 3. React Hook 示例

```typescript
// hooks/usePKB.ts
import { useState, useEffect } from 'react';
import { pkbApi } from '../api/client';

// 搜索Hook
export function useSearch() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = async (query: string, options = {}) => {
    setLoading(true);
    setError(null);
    try {
      const data = await pkbApi.search({ q: query, ...options });
      setResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { results, loading, error, search };
}

// 问答Hook
export function useQA() {
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

  const ask = async (question: string, options = {}) => {
    setLoading(true);
    try {
      const data = await pkbApi.ask({ question, ...options });
      setAnswer(data.answer);
      setSources(data.sources);
    } catch (err) {
      console.error('QA error:', err);
    } finally {
      setLoading(false);
    }
  };

  return { answer, sources, loading, ask };
}

// 分类统计Hook
export function useCategoryStats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    pkbApi.getCategoryStats()
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return { stats, loading };
}
```

#### 4. Vue Composition API 示例

```typescript
// composables/usePKB.ts
import { ref, reactive } from 'vue';
import { pkbApi } from '../api/client';

export function useSearch() {
  const results = ref([]);
  const loading = ref(false);
  const error = ref(null);

  const search = async (query: string, options = {}) => {
    loading.value = true;
    error.value = null;
    try {
      const data = await pkbApi.search({ q: query, ...options });
      results.value = data.results;
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  };

  return { results, loading, error, search };
}
```

### 🎨 UI组件设计建议

#### 1. 搜索组件
```jsx
// components/SearchBox.jsx
import React, { useState } from 'react';
import { useSearch } from '../hooks/usePKB';

export function SearchBox() {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('hybrid');
  const { results, loading, search } = useSearch();

  const handleSearch = () => {
    if (query.trim()) {
      search(query, { search_type: searchType });
    }
  };

  return (
    <div className="search-box">
      <div className="search-input">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索知识库..."
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />
        <select value={searchType} onChange={(e) => setSearchType(e.target.value)}>
          <option value="hybrid">混合搜索</option>
          <option value="keyword">关键词</option>
          <option value="semantic">语义搜索</option>
        </select>
        <button onClick={handleSearch} disabled={loading}>
          {loading ? '搜索中...' : '搜索'}
        </button>
      </div>
      
      <div className="search-results">
        {results.map(result => (
          <div key={result.id} className="result-item">
            <h3>{result.title}</h3>
            <p>{result.summary}</p>
            <div className="result-meta">
              <span>相关度: {(result.score * 100).toFixed(1)}%</span>
              <span>类别: {result.categories?.join(', ')}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### 2. 问答组件
```jsx
// components/QAChat.jsx
import React, { useState } from 'react';
import { useQA } from '../hooks/usePKB';

export function QAChat() {
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState([]);
  const { answer, sources, loading, ask } = useQA();

  const handleAsk = async () => {
    if (!question.trim()) return;
    
    const newQuestion = question;
    setQuestion('');
    
    // 添加问题到历史
    setHistory(prev => [...prev, { type: 'question', content: newQuestion }]);
    
    await ask(newQuestion);
    
    // 添加答案到历史
    setHistory(prev => [...prev, { 
      type: 'answer', 
      content: answer,
      sources: sources
    }]);
  };

  return (
    <div className="qa-chat">
      <div className="chat-history">
        {history.map((item, index) => (
          <div key={index} className={`message ${item.type}`}>
            <div className="content">{item.content}</div>
            {item.sources && (
              <div className="sources">
                <h4>参考文档:</h4>
                {item.sources.map(source => (
                  <div key={source.id} className="source-item">
                    <span>{source.title}</span>
                    <span>相关度: {(source.score * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      
      <div className="input-area">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="请输入您的问题..."
          onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
        />
        <button onClick={handleAsk} disabled={loading}>
          {loading ? '思考中...' : '提问'}
        </button>
      </div>
    </div>
  );
}
```

#### 3. 分类统计组件
```jsx
// components/CategoryStats.jsx
import React from 'react';
import { useCategoryStats } from '../hooks/usePKB';

export function CategoryStats() {
  const { stats, loading } = useCategoryStats();

  if (loading) return <div>加载中...</div>;
  if (!stats) return <div>暂无数据</div>;

  return (
    <div className="category-stats">
      <div className="overview">
        <h3>知识库概览</h3>
        <div className="stats-grid">
          <div className="stat-item">
            <span className="label">总文档</span>
            <span className="value">{stats.total_contents}</span>
          </div>
          <div className="stat-item">
            <span className="label">已分类</span>
            <span className="value">{stats.classified_contents}</span>
          </div>
          <div className="stat-item">
            <span className="label">分类率</span>
            <span className="value">{(stats.classification_rate * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>
      
      <div className="categories">
        <h3>分类分布</h3>
        {stats.categories.map(category => (
          <div key={category.name} className="category-item">
            <div 
              className="color-indicator" 
              style={{ backgroundColor: category.color }}
            ></div>
            <span className="name">{category.name}</span>
            <span className="count">{category.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 🔄 状态管理

#### Redux示例
```typescript
// store/pkbSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { pkbApi } from '../api/client';

// 异步Action
export const searchContent = createAsyncThunk(
  'pkb/search',
  async (params: { q: string; search_type?: string }) => {
    const response = await pkbApi.search(params);
    return response;
  }
);

export const askQuestion = createAsyncThunk(
  'pkb/ask',
  async (params: { question: string; category_filter?: string }) => {
    const response = await pkbApi.ask(params);
    return response;
  }
);

const pkbSlice = createSlice({
  name: 'pkb',
  initialState: {
    searchResults: [],
    searchLoading: false,
    qaAnswer: '',
    qaSources: [],
    qaLoading: false,
    categoryStats: null,
  },
  reducers: {
    clearSearch: (state) => {
      state.searchResults = [];
    },
    clearQA: (state) => {
      state.qaAnswer = '';
      state.qaSources = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(searchContent.pending, (state) => {
        state.searchLoading = true;
      })
      .addCase(searchContent.fulfilled, (state, action) => {
        state.searchLoading = false;
        state.searchResults = action.payload.results;
      })
      .addCase(askQuestion.pending, (state) => {
        state.qaLoading = true;
      })
      .addCase(askQuestion.fulfilled, (state, action) => {
        state.qaLoading = false;
        state.qaAnswer = action.payload.answer;
        state.qaSources = action.payload.sources;
      });
  },
});

export const { clearSearch, clearQA } = pkbSlice.actions;
export default pkbSlice.reducer;
```

### 🎯 最佳实践

#### 1. 错误处理
```typescript
// utils/errorHandler.ts
export class PKBError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'PKBError';
  }
}

export function handleApiError(error: any) {
  if (error.response) {
    // 服务器返回错误状态码
    const { status, data } = error.response;
    throw new PKBError(
      data.message || '服务器错误',
      status,
      data
    );
  } else if (error.request) {
    // 网络错误
    throw new PKBError('网络连接失败，请检查网络设置');
  } else {
    // 其他错误
    throw new PKBError(error.message || '未知错误');
  }
}
```

#### 2. 缓存策略
```typescript
// utils/cache.ts
class APICache {
  private cache = new Map();
  private ttl = 5 * 60 * 1000; // 5分钟

  set(key: string, data: any) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  get(key: string) {
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }

  clear() {
    this.cache.clear();
  }
}

export const apiCache = new APICache();
```

#### 3. 请求防抖
```typescript
// utils/debounce.ts
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

// 使用示例
const debouncedSearch = debounce(search, 300);
```

#### 4. 分页处理
```typescript
// hooks/usePagination.ts
export function usePagination(fetchFunction: Function, pageSize = 20) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);

  const loadMore = async () => {
    if (loading || !hasMore) return;
    
    setLoading(true);
    try {
      const newData = await fetchFunction({ page, size: pageSize });
      
      if (newData.length < pageSize) {
        setHasMore(false);
      }
      
      setData(prev => [...prev, ...newData]);
      setPage(prev => prev + 1);
    } catch (error) {
      console.error('Load more error:', error);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setData([]);
    setPage(1);
    setHasMore(true);
  };

  return { data, loading, hasMore, loadMore, reset };
}
```

### 📱 响应式设计

#### CSS示例
```css
/* styles/components.css */
.search-box {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.search-input {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-input input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
}

.search-input select {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.search-input button {
  padding: 12px 24px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.search-input button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.result-item {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.result-item h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.result-item p {
  margin: 0 0 12px 0;
  color: #666;
  line-height: 1.5;
}

.result-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #888;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-input {
    flex-direction: column;
  }
  
  .result-meta {
    flex-direction: column;
    gap: 4px;
  }
}
```

### 🎉 完整示例应用

```jsx
// App.jsx
import React from 'react';
import { SearchBox } from './components/SearchBox';
import { QAChat } from './components/QAChat';
import { CategoryStats } from './components/CategoryStats';
import './styles/app.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>PKB 智能知识库</h1>
      </header>
      
      <main className="app-main">
        <div className="sidebar">
          <CategoryStats />
        </div>
        
        <div className="content">
          <div className="search-section">
            <SearchBox />
          </div>
          
          <div className="qa-section">
            <QAChat />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
```

这份API文档为前端开发提供了完整的接口信息和对接指导。建议根据具体的前端技术栈选择相应的实现方式，并根据业务需求调整UI设计和交互逻辑。
