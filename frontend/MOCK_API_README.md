# Mock API 使用说明

## 📋 概述

当前项目已配置为使用 **Mock API 模式**，所有后端API调用都会返回模拟数据，方便本地开发和调试。

## 🎯 功能特性

### 已实现的Mock API端点

1. **分类相关**
   - `GET /search/categories/stats` - 获取分类统计
   - `GET /search/category/{categoryName}` - 按分类搜索文档

2. **搜索相关**
   - `GET /search` - 全文搜索（关键词/语义/混合）

3. **合集管理**
   - `GET /collection` - 获取合集列表
   - `POST /collection` - 创建合集
   - `PUT /collection/{id}` - 更新合集
   - `DELETE /collection/{id}` - 删除合集
   - `GET /collection/{id}/contents` - 获取合集内容

4. **文件上传**
   - `POST /ingest/upload-smart` - 单文件上传
   - `POST /ingest/upload-multiple` - 批量上传
   - `GET /ingest/status/{contentId}` - 获取处理状态
   - `GET /document/validate/{filename}` - 验证文件格式

5. **问答系统**
   - `POST /qa/ask` - 发送问题
   - `GET /qa/history` - 获取问答历史
   - `POST /qa/feedback` - 提交反馈
   - `GET /qa/test` - 测试服务状态

6. **文档管理**
   - `DELETE /document/{id}` - 删除文档

## 🔧 配置说明

### 使用Mock API（默认）

项目默认使用Mock API，无需任何配置。所有API调用都会：
- 返回模拟数据
- 模拟网络延迟（200-800ms）
- 在控制台显示 `[MOCK]` 标记

### 切换到真实API

当后端API开发完成后，可以通过以下方式切换到真实API：

**方法1：环境变量（推荐）**

在项目根目录创建或修改 `.env` 文件：

```env
VITE_USE_MOCK_API=false
```

然后重启开发服务器。

**方法2：修改代码**

编辑 `src/services/api.ts`，将：

```typescript
const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API !== 'false';
```

改为：

```typescript
const USE_MOCK_API = false;
```

## 📊 Mock数据说明

### 分类数据

默认包含5个分类：
- 工作文档 (15个文档)
- 学习笔记 (23个文档)
- 生活记录 (8个文档)
- 技术资料 (31个文档)
- 项目文档 (12个文档)

### 文档数据

包含4个示例文档：
- React最佳实践指南
- 项目管理会议纪要
- 机器学习入门笔记
- 旅行照片

### 合集数据

包含2个示例合集：
- 前端开发合集
- AI学习资料

### 问答数据

包含2条示例问答历史。

## 🎨 自定义Mock数据

如果需要修改Mock数据，可以编辑以下文件：

- `src/services/mockData.ts` - 所有Mock数据定义
- `src/services/mockApi.ts` - API响应逻辑

### 添加新的Mock数据

1. 在 `mockData.ts` 中添加数据
2. 在 `mockApi.ts` 中添加对应的处理逻辑

### 示例：添加新的分类

```typescript
// 在 mockData.ts 中
export const mockCategories = [
  // ... 现有分类
  { id: '6', name: '新分类', color: '#ff4d4f', content_count: 5 },
];
```

## 🐛 调试技巧

### 查看Mock API调用

所有Mock API调用都会在控制台显示，格式如下：

```
🎭 [MOCK] GET: /search/categories/stats
🎭 [MOCK] POST: /collection { name: "新合集" }
```

### 模拟网络延迟

Mock API会自动模拟200-800ms的网络延迟，模拟真实环境。

### 模拟错误

可以在 `mockApi.ts` 中修改逻辑来模拟错误响应：

```typescript
// 模拟404错误
if (url === '/collection/notfound') {
  return createMockResponse<T>({} as T, 404);
}
```

## ⚠️ 注意事项

1. **数据持久化**
   - Mock数据存储在内存中，刷新页面后会重置
   - 合集的新增/修改/删除在页面刷新前有效

2. **文件上传**
   - 文件上传会模拟进度，但不会真正保存文件
   - 上传的文件信息会保存在内存中，直到页面刷新

3. **问答历史**
   - 问答历史会保存在内存中
   - 新提问会自动添加到历史记录

4. **类型安全**
   - 所有Mock响应都遵循真实API的类型定义
   - 确保类型兼容性

## 🔄 切换到真实API后的检查清单

1. ✅ 确认环境变量 `VITE_USE_MOCK_API=false`
2. ✅ 确认后端API服务已启动
3. ✅ 确认API基础URL配置正确
4. ✅ 测试所有功能是否正常工作
5. ✅ 检查控制台是否有错误

## 📝 文件结构

```
frontend/src/services/
├── api.ts              # API服务入口（自动选择Mock或真实API）
├── mockApi.ts          # Mock API实现
├── mockData.ts         # Mock数据定义
├── categoryService.ts  # 分类服务（使用api.ts）
├── collectionService.ts # 合集服务（使用api.ts）
├── qaService.ts        # 问答服务（使用api.ts）
└── uploadService.ts    # 上传服务（使用api.ts）
```

## 🚀 快速开始

1. 启动开发服务器：
   ```bash
   npm run dev
   # 或
   pnpm dev
   ```

2. 打开浏览器，所有API调用都会使用Mock数据

3. 查看控制台，确认看到 `[MOCK]` 标记

4. 开始开发和调试！

## 💡 提示

- Mock数据可以根据实际需求随时修改
- 建议在开发过程中保持Mock数据与真实API响应格式一致
- 使用TypeScript类型定义确保Mock数据的正确性


