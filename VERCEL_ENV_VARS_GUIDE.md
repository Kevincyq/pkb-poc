# Vercel环境变量配置指南

## 🎯 **环境变量设置**

在Vercel Dashboard中设置以下环境变量：

### **Production环境**
```
VITE_API_BASE_URL=/api
VITE_ENV=production
VITE_APP_NAME=PKB 个人知识库
```

### **Preview环境**
```
VITE_API_BASE_URL=/api
VITE_ENV=preview
VITE_APP_NAME=PKB (测试环境)
```

### **Development环境**
```
VITE_API_BASE_URL=/api
VITE_ENV=development
VITE_APP_NAME=PKB (开发环境)
```

## 🔧 **设置步骤**

1. **登录Vercel Dashboard**
   - 访问 https://vercel.com/dashboard
   - 选择你的项目

2. **进入Settings**
   - 点击项目设置
   - 选择 "Environment Variables"

3. **添加环境变量**
   - 点击 "Add New"
   - 输入变量名和值
   - 选择适用的环境（Production/Preview/Development）

4. **重新部署**
   - 环境变量更新后需要重新部署
   - 可以在Deployments页面触发重新部署

## 📋 **验证方法**

### **检查环境变量**
在浏览器控制台查看：
```javascript
console.log('API Base URL:', import.meta.env.VITE_API_BASE_URL);
console.log('Environment:', import.meta.env.VITE_ENV);
```

### **测试API调用**
```javascript
// 测试API是否正常工作
fetch('/api/health')
  .then(response => response.json())
  .then(data => console.log('API Health:', data));
```

## ⚠️ **重要提醒**

1. **变量名必须以VITE_开头**：只有以VITE_开头的变量才会暴露给前端
2. **重新部署**：环境变量更新后必须重新部署才能生效
3. **敏感信息**：不要在环境变量中存储敏感信息（如API密钥）
4. **代理配置**：确保vercel.json中的代理配置正确

## 🔍 **故障排除**

### **问题1: API调用失败**
- 检查vercel.json配置
- 确认后端服务正常运行
- 查看Vercel函数日志

### **问题2: 环境变量未生效**
- 确认变量名以VITE_开头
- 检查是否重新部署
- 验证变量值是否正确

### **问题3: 代理不工作**
- 检查vercel.json语法
- 确认rewrites配置正确
- 查看Vercel部署日志

## 📊 **配置检查清单**

- [ ] vercel.json配置正确
- [ ] 环境变量已设置
- [ ] 后端服务正常运行
- [ ] 本地开发环境正常
- [ ] Vercel部署成功
- [ ] API调用测试通过

---

**配置指南版本**: 1.0  
**更新时间**: $(date)  
**适用版本**: Vercel 2024
