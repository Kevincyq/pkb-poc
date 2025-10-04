# 问题分析报告

## 问题1: 搜索功能
### 状态: ✅ 功能正常
- 后端搜索逻辑正确实现
- 前端HighlightText组件已替换dangerouslySetInnerHTML
- 关键词搜索支持中文分词和模糊匹配

## 问题2: 文件预览显示问题
### 问题描述
- 文档或图片预览无法显示或清晰度不高

### 可能原因
1. **缩略图API路径问题**：前端可能请求错误的缩略图URL
2. **文件路径映射问题**：后端无法找到正确的文件路径
3. **图片压缩过度**：缩略图质量设置过低

### 需要检查
- `/home/kevincyq/pkb-poc/backend/app/api/files.py` - 缩略图生成逻辑
- `/home/kevincyq/pkb-poc/frontend/src/components/Document/DocumentCard.tsx` - 缩略图URL构建
- `/home/kevincyq/pkb-poc/frontend/src/pages/Collection/Detail.tsx` - 预览模态框实现

## 问题3: 合集缩略图数量显示不对
### 问题描述
- 合集有5个内容，但只显示3个缩略图

### 根本原因分析
**后端API查询限制**：
```python
# backend/app/services/search_service.py:652
results = base_query.order_by(
    desc(ContentCategory.confidence),
    desc(Content.created_at)
).limit(top_k).all()  # 这里限制了返回数量
```

**问题**：
- `search_by_category` 默认 `top_k=20`
- 但是查询使用了 `Chunk` JOIN，可能导致重复或遗漏
- `Chunk` 级别的查询会为每个文件的每个chunk返回一条记录
- 格式化时可能没有正确去重

### 解决方案
1. **改为Content级别的查询**：不使用Chunk表，直接查询Content
2. **去重逻辑**：在格式化结果时确保每个Content只出现一次
3. **正确的GROUP BY**：使用SQL的GROUP BY去重

## 优先级
1. 🔴 **高**：合集缩略图数量问题（影响用户体验）
2. 🟡 **中**：文件预览显示问题（需要进一步测试确认）
3. 🟢 **低**：搜索功能优化（已基本正常）
