# PKB 多环境开发部署工作流程

## 🏗️ 环境架构

### 生产环境 (Production)
```
前端: https://pkb-poc.kmchat.cloud (main 分支)
后端: https://pkb.kmchat.cloud:8002 (main 分支)
数据库: pkb (生产数据)
```

### 测试环境 (Preview/Staging)
```
前端: https://pkb-poc-git-<branch>.vercel.app (功能分支)
后端: http://your-server:8003 (功能分支)
数据库: pkb_test (测试数据)
```

## 🚀 完整开发流程

### 1. 本地开发

```bash
# 创建功能分支
git checkout main
git pull origin main
git checkout -b feature/user-auth-system

# 开发代码（前端 + 后端）
# 修改 frontend/ 和 backend/ 目录下的文件

# 提交代码
git add .
git commit -m "feat: implement user authentication system

- Add user registration and login APIs
- Create JWT token management
- Update frontend auth components
- Add user profile management"

# 推送分支
git push origin feature/user-auth-system
```

### 2. 自动前端部署

推送分支后，Vercel 会自动：
- 检测到新分支推送
- 自动构建前端代码
- 部署到预览环境：`https://pkb-poc-git-feature-user-auth-system.vercel.app`
- 发送部署通知

### 3. 手动后端部署

```bash
# SSH 到服务器
ssh ec2-user@your-server-ip

# 部署测试环境
cd /home/ec2-user
./pkb-poc/deploy/deploy-test-env.sh feature/user-auth-system

# 输出示例:
# 🧪 测试环境信息:
#    分支: feature/user-auth-system
#    后端: http://localhost:8003
#    API 文档: http://localhost:8003/api/docs
```

### 4. 环境配置同步

为了让前端预览环境能正确连接到测试后端，需要配置环境变量：

#### 方案 A: 使用 Vercel 环境变量
在 Vercel Dashboard 中为预览环境设置：
```
VITE_API_BASE_URL = http://your-server-ip:8003/api
```

#### 方案 B: 动态环境检测
修改前端 API 配置：

```typescript
// frontend/src/services/api.ts
const getApiBaseUrl = () => {
  // 生产环境
  if (window.location.hostname === 'pkb-poc.kmchat.cloud') {
    return 'https://pkb.kmchat.cloud/api';
  }
  
  // 预览环境 (Vercel)
  if (window.location.hostname.includes('vercel.app')) {
    return import.meta.env.VITE_API_BASE_URL || 'http://your-server-ip:8003/api';
  }
  
  // 本地开发
  return 'http://localhost:8000/api';
};

const baseURL = getApiBaseUrl();
```

### 5. 完整测试

```bash
# 前端测试
# 访问 Vercel 预览环境 URL
# 测试所有新功能和现有功能

# 后端测试
curl http://your-server-ip:8003/api/health
curl http://your-server-ip:8003/api/docs

# 集成测试
# 在前端预览环境中测试完整的用户流程
```

### 6. 合并到生产环境

测试通过后：

```bash
# 本地合并
git checkout main
git merge feature/user-auth-system
git push origin main

# 生产环境部署
# 前端：Vercel 自动部署 main 分支
# 后端：服务器手动部署
ssh ec2-user@your-server-ip
cd /home/ec2-user/pkb-new
./deploy/deploy-branch.sh main
```

### 7. 清理测试环境

```bash
# 清理服务器测试环境
ssh ec2-user@your-server-ip
cd /home/ec2-user
./pkb-poc/deploy/cleanup-test-env.sh

# 删除功能分支
git branch -d feature/user-auth-system
git push origin --delete feature/user-auth-system

# Vercel 预览环境会自动清理
```

## 🛠️ 常用命令

### 服务器端操作

```bash
# 部署测试环境
./deploy/deploy-test-env.sh <branch-name> [port]

# 查看测试环境状态
cd /home/ec2-user/pkb-test/deploy
docker-compose -f docker-compose.test.yml -p pkb-test ps

# 查看测试环境日志
docker-compose -f docker-compose.test.yml -p pkb-test logs -f pkb-test-backend

# 停止测试环境
docker-compose -f docker-compose.test.yml -p pkb-test down

# 清理测试环境
./deploy/cleanup-test-env.sh
```

### 本地操作

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 推送分支（触发前端自动部署）
git push origin feature/new-feature

# 查看 Vercel 部署状态
# 访问 Vercel Dashboard 或检查 GitHub PR 中的部署状态

# 合并到主分支
git checkout main
git merge feature/new-feature
git push origin main
```

## 🔧 环境配置

### Vercel 环境变量配置

在 Vercel Dashboard 中设置：

**Production (main 分支)**:
```
VITE_API_BASE_URL = https://pkb.kmchat.cloud/api
VITE_ENV = production
```

**Preview (其他分支)**:
```
VITE_API_BASE_URL = http://your-server-ip:8003/api
VITE_ENV = preview
```

### 服务器环境隔离

测试环境使用独立的：
- 端口：8003 (vs 生产环境 8002)
- 数据库：pkb_test (vs 生产环境 pkb)
- 容器名：pkb-test-* (vs 生产环境 pkb-*)
- 项目名：pkb-test (vs 生产环境 deploy)

## ⚠️ 注意事项

### 1. 数据隔离
- 测试环境使用独立数据库 `pkb_test`
- 避免测试数据污染生产环境
- 定期清理测试数据

### 2. 资源管理
- 测试环境会占用额外的服务器资源
- 及时清理不需要的测试环境
- 监控服务器资源使用情况

### 3. 网络配置
- 确保测试环境端口 (8003) 可访问
- 配置防火墙规则（如需要）
- 注意 CORS 配置

### 4. 版本同步
- 确保前后端分支版本一致
- 测试时使用相同的分支代码
- 合并前确保所有测试通过

## 📋 测试检查清单

### 部署前检查
- [ ] 功能分支已推送到 GitHub
- [ ] Vercel 预览环境部署成功
- [ ] 测试环境后端部署成功
- [ ] 前后端版本同步

### 功能测试
- [ ] 新功能按预期工作
- [ ] 现有功能没有被破坏
- [ ] 前后端集成正常
- [ ] API 接口响应正确
- [ ] 用户界面显示正常

### 性能测试
- [ ] 页面加载速度正常
- [ ] API 响应时间合理
- [ ] 数据库查询效率
- [ ] 内存和 CPU 使用正常

### 安全测试
- [ ] 认证授权功能正常
- [ ] 数据验证和过滤
- [ ] 敏感信息保护
- [ ] CORS 配置正确

## 🎯 最佳实践

1. **小步快跑**：每个功能分支保持较小的变更范围
2. **及时测试**：推送后立即部署测试环境
3. **完整测试**：测试新功能和现有功能
4. **及时清理**：测试完成后清理测试环境
5. **文档更新**：重要变更及时更新文档
6. **团队协作**：多人开发时协调测试环境使用
