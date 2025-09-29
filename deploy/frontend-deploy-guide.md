# PKB 前端云端部署指南

## 🎯 部署方案对比

| 平台 | 免费额度 | 优势 | 推荐度 |
|------|----------|------|--------|
| **Vercel** | 100GB/月 | React 优化，GitHub 集成 | ⭐⭐⭐⭐⭐ |
| **Netlify** | 100GB/月 | 功能丰富，易用 | ⭐⭐⭐⭐ |
| **GitHub Pages** | 无限制 | 完全免费 | ⭐⭐⭐ |
| **Firebase** | 10GB/月 | Google 生态 | ⭐⭐⭐ |

## 🚀 推荐方案：Vercel 部署

### 方法一：通过 Vercel CLI 部署

```bash
# 1. 安装 Vercel CLI
npm i -g vercel

# 2. 进入前端目录
cd frontend

# 3. 登录 Vercel
vercel login

# 4. 初始化项目
vercel

# 5. 部署到生产环境
vercel --prod
```

### 方法二：通过 GitHub 集成（推荐）

1. **连接 GitHub**
   - 访问 [vercel.com](https://vercel.com)
   - 使用 GitHub 账号登录
   - 导入 `pkb-poc` 仓库

2. **配置构建设置**
   ```
   Framework Preset: Vite
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: dist
   Install Command: npm install
   ```

3. **设置环境变量**
   ```
   VITE_API_BASE_URL = http://52.90.58.102:8002
   ```

4. **自动部署**
   - 每次推送到 main 分支自动部署
   - PR 预览功能

## 🔧 前端代码适配

### 1. 修改 API 基础 URL

创建 `frontend/src/config/api.ts`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

export const apiConfig = {
  baseURL: API_BASE_URL,
  timeout: 30000,
};
```

### 2. 更新 API 服务

修改 `frontend/src/services/api.ts`:
```typescript
import axios from 'axios';
import { apiConfig } from '../config/api';

const api = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: apiConfig.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
```

### 3. 处理 CORS 问题

后端需要添加前端域名到 CORS 允许列表：

在 `backend/.env` 中添加：
```
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

## 🌐 其他平台部署指南

### Netlify 部署

1. **通过 Netlify CLI**
   ```bash
   npm i -g netlify-cli
   cd frontend
   npm run build
   netlify deploy --prod --dir=dist
   ```

2. **通过 GitHub 集成**
   - 连接 GitHub 仓库
   - 设置构建命令：`npm run build`
   - 发布目录：`dist`

### GitHub Pages 部署

1. **创建 GitHub Actions**
   
   创建 `.github/workflows/deploy-frontend.yml`:
   ```yaml
   name: Deploy Frontend to GitHub Pages
   
   on:
     push:
       branches: [ main ]
       paths: [ 'frontend/**' ]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Setup Node.js
           uses: actions/setup-node@v3
           with:
             node-version: '18'
             cache: 'npm'
             cache-dependency-path: frontend/package-lock.json
         
         - name: Install dependencies
           run: cd frontend && npm ci
         
         - name: Build
           run: cd frontend && npm run build
           env:
             VITE_API_BASE_URL: http://52.90.58.102:8002
         
         - name: Deploy to GitHub Pages
           uses: peaceiris/actions-gh-pages@v3
           with:
             github_token: ${{ secrets.GITHUB_TOKEN }}
             publish_dir: frontend/dist
   ```

2. **启用 GitHub Pages**
   - 仓库设置 → Pages
   - Source: Deploy from a branch
   - Branch: gh-pages

## 🔒 安全考虑

### 1. API 域名配置

生产环境建议使用域名而非 IP：
```
VITE_API_BASE_URL=https://api.your-domain.com
```

### 2. HTTPS 配置

所有推荐平台都自动提供 HTTPS，但需要确保：
- API 服务器支持 HTTPS
- 或配置反向代理

### 3. 环境变量管理

不同环境使用不同配置：
```
.env.development  # 开发环境
.env.production   # 生产环境
.env.local        # 本地覆盖（不提交到 Git）
```

## 📋 部署检查清单

- [ ] 前端构建成功
- [ ] API 连接正常
- [ ] CORS 配置正确
- [ ] 路由正常工作
- [ ] 静态资源加载正常
- [ ] 移动端适配良好
- [ ] 性能指标良好

## 🚀 推荐的完整部署流程

1. **选择 Vercel 作为主要平台**
2. **配置 GitHub 集成自动部署**
3. **设置自定义域名（可选）**
4. **配置 CDN 加速**
5. **监控和分析设置**

## 💡 高级功能

### 分支预览
- 每个 PR 自动生成预览链接
- 便于测试和审查

### 性能监控
- Vercel Analytics
- Web Vitals 监控

### A/B 测试
- Vercel Edge Functions
- 流量分割测试
