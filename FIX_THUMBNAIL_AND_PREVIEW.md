# 修复缩略图和预览功能

## 问题诊断

用户反映四个问题：
1. ❌ 缩略图不显示
2. ❌ 预览图也不显示
3. ❌ 标签缺少
4. ❌ 基于图片内容的问答失效

**根本原因**：文件存储于 Google Drive（`source_uri = "google_drive://{file_id}"`），但前端和后端都缺少对 `google_drive://` 协议的处理。

## 修复内容

### 1. 后端修复 (`backend/app/api/files.py`)

**问题**：缩略图API无法找到 Google Drive 文件
**修复**：添加通过 `source_uri` 模糊查找的支持

```python
# 3. 通过google_drive://source_uri查找
if not content:
    content = db.query(Content).filter(
        Content.source_uri.like(f"%{filename}%")
    ).first()
```

### 2. 前端修复（3个文件）

#### a) `frontend/src/components/Document/DocumentCard.tsx`
添加 `google_drive://` 协议支持：
```typescript
if (sourceUri.includes('google_drive://')) {
  const fileId = sourceUri.replace('google_drive://', '');
  const thumbnailUrl = `${apiBaseUrl}/files/thumbnail/${fileId}`;
  return thumbnailUrl;
}
```

#### b) `frontend/src/components/PreviewContent/PreviewContent.tsx`
修改 `getImageUrls` 函数，支持提取 Google Drive 文件ID

#### c) `frontend/src/components/Document/DocumentItem.tsx`
添加 `google_drive://` 协议处理

## 部署步骤

### 1. 提交代码

```bash
git add backend/app/api/files.py frontend/src/components/Document/DocumentCard.tsx frontend/src/components/PreviewContent/PreviewContent.tsx frontend/src/components/Document/DocumentItem.tsx
git commit -m "fix: 支持Google Drive文件的缩略图和预览功能"
git push
```

### 2. 云端部署

#### 后端部署

```bash
# SSH 到服务器
ssh your_server

# 进入项目目录
cd /path/to/pkb-poc

# 拉取最新代码
git pull

# 重启后端服务
docker compose -f docker-compose.cloud.yml restart pkb-backend

# 查看日志
docker compose -f docker-compose.cloud.yml logs -f pkb-backend
```

#### 前端部署

```bash
# 本地构建
cd frontend
npm run build

# 部署到 Vercel（或其他前端托管平台）
vercel --prod

# 或者推送到GitHub，自动触发部署
git push origin main
```

### 3. 验证修复

1. **缩略图**：
   - 上传一张新图片
   - 应能显示缩略图（非占位符）

2. **预览**：
   - 点击图片卡片
   - 应能正常加载预览图

3. **标签**：
   - 图片上传后等待AI分类完成
   - 应能看到提取的标签

4. **QA**：
   - 在问答界面输入图片内容相关的问题
   - 应能正常回答

## 技术细节

### 文件查找逻辑

当请求缩略图时，后端按以下顺序查找：
1. 通过 `Content.title` 查找（精确匹配）
2. 通过 `Content.source_uri == "webui://{filename}"` 查找
3. 通过 `Content.source_uri LIKE "%{filename}%"` 查找（✅ **新增**：支持 Google Drive）
4. 通过 `Content.cloud_file_id` 查找

### 缩略图生成流程

Google Drive 文件缩略图生成流程：
1. 前端请求：`/api/files/thumbnail/{file_id}`
2. 后端通过 `source_uri LIKE "%{file_id}%"` 找到 `Content` 记录
3. 检查 `storage_provider == "google_drive"`
4. 从 Google Drive 下载原图
5. 生成缩略图并返回
6. 清理临时文件

### 为什么标签和QA也失效？

标签和QA都依赖于图片内容的AI分析：
- **标签提取**：使用 `ImageParser._extract_text_with_gpt4v()` 分析图片内容
- **QA分析**：使用图片的文本内容（OCR结果）进行语义搜索

如果图片无法访问，则无法提取内容，导致标签缺失和QA失效。

修复后，后端将正确访问 Google Drive 文件，从而恢复这些功能。

## 注意事项

1. **性能优化**：缩略图会被缓存24小时，减少对 Google Drive 的频繁请求
2. **错误处理**：如果 Google Drive 认证过期，会返回404错误
3. **文件大小限制**：大文件可能会超时，建议增加 `TIMEOUT` 设置

## 相关文件

- `backend/app/api/files.py` - 缩略图API
- `frontend/src/components/Document/DocumentCard.tsx` - 卡片缩略图
- `frontend/src/components/PreviewContent/PreviewContent.tsx` - 预览组件
- `frontend/src/components/Document/DocumentItem.tsx` - 文档列表项
- `backend/app/connectors/google_drive.py` - Google Drive 连接器
- `backend/app/services/storage_strategy_service.py` - 存储策略服务

