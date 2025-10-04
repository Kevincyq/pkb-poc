# 数据流完整性验证

## 1️⃣ **搜索功能数据流**

### 前端触发
1. 用户在 `SearchOverlay` 输入关键词 ✅
2. `performSearch` 函数构建URL: `/api/search?q={query}&top_k=10&search_type=hybrid` ✅
3. 使用 `api.get()` 发送请求（自动添加baseURL和headers） ✅

### 后端处理
4. FastAPI接收请求: `GET /api/search` ✅
5. URL解码: `unquote(query)` ✅
6. 创建 `SearchService(db)` ✅
7. 调用 `search_service.search(decoded_query, top_k, search_type, filters)` ✅
8. 根据search_type分发：
   - `keyword`: `_keyword_search()` ✅
   - `semantic`: `_semantic_search()` ✅
   - `hybrid`: 两者结合 ✅
9. 查询数据库（Chunk + Content + Category） ✅
10. 格式化结果: `_format_search_results()` ✅
11. 返回JSON: `{query, results, total, response_time, search_type}` ✅

### 前端展示
12. 接收response.data.results ✅
13. 使用 `HighlightText` 组件高亮关键词 ✅
14. 渲染 `List.Item` 展示搜索结果 ✅
15. `ErrorBoundary` 捕获任何渲染错误 ✅

**✅ 搜索功能数据流完整，无断点**

---

## 2️⃣ **缩略图显示数据流**

### 前端请求（DocumentCard）
1. 组件接收props: `{sourceUri, title, modality}` ✅
2. 检查 `modality === 'image'` ✅
3. 调用 `getThumbnailUrl(sourceUri)` ✅
4. 从 `sourceUri` 提取文件名: `sourceUri.replace('webui://', '')` ✅
5. 构建缩略图URL: `${apiBaseUrl}/files/thumbnail/${encodeURIComponent(fileName)}` ✅
6. 设置 `<img src={thumbnailUrl} />` ✅

### 后端处理（files.py）
7. FastAPI接收: `GET /api/files/thumbnail/{filename}` ✅
8. URL解码文件名（在get_file_path中） ✅
9. 调用 `get_file_path(filename, db)`:
   - 查询数据库: `Content.source_uri == f"webui://{filename}"` ✅
   - 或查询: `Content.title == filename` ✅
   - 返回 `content.meta['file_path']` 或 fallback路径 ✅
10. 检查文件是否存在 ✅
11. 检查文件格式是否支持（SUPPORTED_IMAGE_FORMATS） ✅
12. 调用 `get_or_create_thumbnail(file_path, filename)`:
    - 检查缩略图缓存 ✅
    - 如不存在，调用 `create_and_save_thumbnail()` ✅
    - 使用PIL生成缩略图（300x200, quality=85） ✅
    - 保存到 `/tmp/pkb_thumbnails/` ✅
13. 返回 `FileResponse(thumbnail_path, media_type="image/jpeg")` ✅

### 浏览器渲染
14. 接收JPEG图片数据 ✅
15. 浏览器缓存（Cache-Control: max-age=86400） ✅
16. 渲染到 `<img>` 标签 ✅
17. 如加载失败，`onError` 设置 `thumbnailError=true` 显示占位符 ✅

**✅ 缩略图显示数据流完整，无断点**

---

## 3️⃣ **文件预览数据流**

### 前端触发（Collection/Detail.tsx）
1. 用户点击文件卡片 ✅
2. `handleDocumentClick(document)` 设置 `previewDocument` ✅
3. `Modal` 打开，`open={!!previewDocument}` ✅
4. 检查 `modality === 'image'` ✅
5. 从 `source_uri` 提取文件名: `previewDocument.source_uri.replace(/^(webui|nextcloud):\/\//, '')` ✅
6. 构建原图URL: `${apiBaseUrl}/files/${encodeURIComponent(fileName)}` ✅
7. 设置 `<img src={...} />` 在Modal中 ✅

### 后端处理（files.py）
8. FastAPI接收: `GET /api/files/{filename}` ✅ **（刚刚添加的端点）**
9. URL解码文件名 ✅
10. 调用 `get_file_path(filename, db)` ✅
11. 检查文件是否存在 ✅
12. 根据文件扩展名确定 `media_type`:
    - `.jpg/.jpeg`: `image/jpeg` ✅
    - `.png`: `image/png` ✅
    - `.pdf`: `application/pdf` ✅
    - 其他: `application/octet-stream` ✅
13. 返回 `FileResponse(path, media_type, Content-Disposition: inline)` ✅

### 浏览器渲染
14. 接收原始文件数据（无压缩） ✅
15. 根据 `Content-Disposition: inline` 在浏览器内预览 ✅
16. 渲染高清原图到 `<img>` ✅
17. 如加载失败，`onError` 显示占位符 ✅

**✅ 文件预览数据流完整，刚刚修复的端点缺失问题**

---

## 4️⃣ **合集内容查询数据流**

### 前端请求（Collection/Detail.tsx）
1. 页面加载，从URL参数获取 `categoryName` ✅
2. 使用 `useQuery` 调用 `getCategoryDocuments(categoryName, searchQuery)` ✅
3. 构建URL: `/api/search/category/${encodeURIComponent(categoryName)}?q={searchQuery}&top_k=20` ✅
4. 发送 `api.get()` 请求 ✅

### 后端处理（search.py → search_service.py）
5. FastAPI接收: `GET /api/search/category/{category_id}` ✅
6. URL解码查询参数 ✅
7. 调用 `search_service.search_by_category(category_id, decoded_q, top_k)` ✅
8. 查找分类:
   - 尝试UUID格式查找 `Category.id == uuid_obj` ✅
   - 尝试名称查找 `Category.name == category_identifier` ✅
9. 构建查询（**已修复为Content级别**）:
   ```python
   base_query = self.db.query(
       Content, Category.name, ...
   ).select_from(Content).join(
       ContentCategory, Content.id == ContentCategory.content_id
   ).join(
       Category, ContentCategory.category_id == Category.id
   ).filter(Category.id == category.id)
   ```
   ✅ **直接查询Content，避免Chunk重复**
   
10. 如有搜索查询，过滤:
    ```python
    Content.text.ilike(f"%{query}%")
    Content.title.ilike(f"%{query}%")
    ```
    ✅ **使用Content.text而非Chunk.text**
    
11. 排序: `desc(ContentCategory.confidence), desc(Content.created_at)` ✅
12. 限制数量: `limit(top_k)` ✅ **现在返回top_k个Content，而非Chunk**
13. 直接格式化结果（无需去重）:
    ```python
    for content, category_name, ... in results:
        formatted_results.append({
            "content_id": str(content.id),
            "chunk_id": str(content.id),  # 使用content_id
            "title": content.title,
            "source_uri": content.source_uri,
            ...
        })
    ```
    ✅ **一对一映射，无重复**
    
14. 返回JSON: `{category, query, results, total}` ✅

### 前端展示
15. 接收 `data.results` ✅
16. 使用 `map()` 渲染 `DocumentCard` ✅
17. 每个文件一个卡片，显示缩略图和标题 ✅
18. 点击卡片触发预览 ✅

**✅ 合集内容查询数据流完整，Chunk重复问题已修复**

---

## 🔍 **关键修复点总结**

### ✅ 已修复问题
1. **文件预览端点缺失**: 添加了 `GET /api/files/{filename}` ✅
2. **合集查询重复**: 改为Content级别查询，避免Chunk导致的重复/遗漏 ✅
3. **React渲染错误**: 移除所有 `dangerouslySetInnerHTML`，使用安全的React组件 ✅
4. **预览图片质量**: 使用原图API而非缩略图API ✅

### ⚠️ 潜在边界情况
1. **文件名特殊字符**: 已使用 `encodeURIComponent` 处理 ✅
2. **文件不存在**: 有完整的404错误处理 ✅
3. **数据库记录缺失**: 有fallback到文件系统直接查找 ✅
4. **缩略图生成失败**: 有错误处理和占位符显示 ✅
5. **搜索查询为空**: 后端返回空结果，前端显示"未找到相关内容" ✅

---

## 📊 **数据流图总结**

```
搜索流: 
用户输入 → SearchOverlay → /api/search → SearchService 
→ 数据库查询 → 格式化结果 → HighlightText渲染

缩略图流:
DocumentCard → getThumbnailUrl → /api/files/thumbnail/{filename} 
→ get_file_path → 数据库查找 → 生成/缓存缩略图 → FileResponse

预览流:
点击卡片 → Modal打开 → /api/files/{filename} 
→ get_file_path → 数据库查找 → FileResponse(原图) → 浏览器预览

合集流:
页面加载 → useQuery → /api/search/category/{name} 
→ search_by_category → Content级别查询 → 格式化结果 → DocumentCard列表
```

**所有数据流已验证完整！** 🎉
