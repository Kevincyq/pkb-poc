# Vercel部署配置说明

## 🎯 **问题背景**

当Vercel部署的前端（HTTPS）尝试访问HTTP后端时，会遇到**混合内容（Mixed Content）**问题：
- 浏览器会阻止HTTPS页面向HTTP资源发送请求
- 这会导致API调用失败

## 🔧 **解决方案：Vercel反向代理**

### **1. Vercel配置 (`vercel.json`)**
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "http://34.247.12.46:8010/api/:path*"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### **2. API配置 (`src/services/api.ts`)**
```typescript
const baseURL = import.meta.env.VITE_API_BASE_URL || 
  (window.location.hostname === 'localhost' 
    ? '/api'  // 本地开发 - 使用Vite代理
    : '/api'  // 生产环境 - 使用Vercel代理
  );
```

### **3. 环境变量配置**
```bash
# env.preview
VITE_API_BASE_URL=/api
```

## 🚀 **工作原理**

### **本地开发环境**
```
前端 (localhost:5173) 
    ↓ /api/*
Vite代理 
    ↓ 转发到
后端 (http://34.247.12.46:8010)
```

### **Vercel生产环境**
```
前端 (https://your-app.vercel.app) 
    ↓ /api/*
Vercel代理 
    ↓ 转发到
后端 (http://34.247.12.46:8010)
```

## ✅ **优势**

1. **安全性**: 前端始终使用HTTPS
2. **兼容性**: 避免混合内容问题
3. **简单性**: 无需修改后端配置
4. **透明性**: 前端代码无需区分环境

## 📋 **部署步骤**

### **1. 更新Vercel环境变量**
在Vercel Dashboard中设置：
```
VITE_API_BASE_URL=/api
```

### **2. 部署到Vercel**
```bash
# 推送代码到GitHub
git add .
git commit -m "Update Vercel proxy configuration"
git push origin main

# Vercel会自动部署
```

### **3. 验证部署**
访问Vercel部署的URL，测试：
- 登录功能
- API调用
- Google OAuth

## 🔍 **测试方法**

### **本地测试**
```bash
# 启动前端开发服务器
cd frontend && npm run dev

# 测试API代理
curl http://localhost:5173/api/health
```

### **生产环境测试**
```bash
# 测试Vercel代理
curl https://your-app.vercel.app/api/health
```

## ⚠️ **注意事项**

1. **Vercel限制**: 免费计划有带宽和请求限制
2. **代理延迟**: 通过Vercel代理会有额外延迟
3. **错误处理**: 代理错误可能不会直接暴露给前端

## 🔄 **备选方案**

### **方案2: 后端启用HTTPS**
如果后端支持HTTPS，可以直接使用：
```bash
VITE_API_BASE_URL=https://34.247.12.46:8010/api
```

### **方案3: 使用CDN/代理服务**
使用Cloudflare等CDN服务为后端提供HTTPS支持。

## 📊 **性能对比**

| 方案 | 延迟 | 安全性 | 复杂度 | 成本 |
|------|------|--------|--------|------|
| Vercel代理 | 中等 | 高 | 低 | 免费 |
| 后端HTTPS | 低 | 高 | 高 | 免费 |
| CDN代理 | 低 | 高 | 中等 | 付费 |

## 🎉 **推荐方案**

**使用Vercel反向代理**是最佳选择，因为：
- ✅ 无需修改后端配置
- ✅ 完全避免混合内容问题
- ✅ 前端代码简洁统一
- ✅ 部署简单，维护方便

---

**配置完成时间**: $(date)  
**后端地址**: http://34.247.12.46:8010  
**代理配置**: ✅ 已更新  
**状态**: 🚀 准备部署
