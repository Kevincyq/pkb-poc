# PKB 简化多环境工作流程

## 🏗️ 环境架构

```
生产环境:
├── 前端: https://pkb-poc.kmchat.cloud (main 分支，Vercel 自动)
├── 后端: /home/ec2-user/pkb-new:8002 (main 分支，手动)
└── 数据: pkb 数据库

测试环境:
├── 前端: https://pkb-poc-git-<branch>.vercel.app (功能分支，Vercel 自动)
├── 后端: /home/ec2-user/pkb-poc:8003 (功能分支，手动)
└── 数据: pkb_test 数据库
```

## 🚀 完整工作流程

### 1. 本地开发
```bash
# 创建功能分支
git checkout -b feature/user-auth

# 修改代码（前端 + 后端）
# ... 编辑代码 ...

# 提交推送
git add .
git commit -m "feat: add user authentication"
git push origin feature/user-auth
```

### 2. 前端自动部署
- Vercel 自动检测分支推送
- 自动部署到：`https://pkb-poc-git-feature-user-auth.vercel.app`
- **无需任何配置**

### 3. 后端手动部署
```bash
# SSH 到服务器
ssh ec2-user@your-server-ip

# 部署测试环境
cd /home/ec2-user/pkb-poc
./deploy/deploy-test-simple.sh feature/user-auth
```

### 4. 测试验证
```bash
# 前端测试
# 访问 https://pkb-poc-git-feature-user-auth.vercel.app

# 后端测试  
curl http://localhost:8003/api/health
curl http://localhost:8003/api/docs

# 查看服务状态
cd /home/ec2-user/pkb-poc/deploy
docker-compose -p pkb-test ps
```

### 5. 合并到生产
```bash
# 测试通过后，本地合并
git checkout main
git merge feature/user-auth
git push origin main

# 生产环境部署
# 前端：Vercel 自动部署 main 分支
# 后端：手动更新生产环境
ssh ec2-user@your-server-ip
cd /home/ec2-user/pkb-new
./update-pkb.sh
```

### 6. 清理测试环境
```bash
# 清理测试环境
cd /home/ec2-user/pkb-poc
./deploy/cleanup-test-simple.sh

# 删除功能分支
git branch -d feature/user-auth
git push origin --delete feature/user-auth
```

## 🛠️ 常用命令

### 服务器操作
```bash
# 部署测试环境
./deploy/deploy-test-simple.sh <branch-name>

# 清理测试环境
./deploy/cleanup-test-simple.sh

# 查看测试环境状态
cd /home/ec2-user/pkb-poc/deploy
docker-compose -p pkb-test ps

# 查看测试环境日志
docker-compose -p pkb-test logs -f

# 手动停止测试环境
docker-compose -p pkb-test down
```

### 本地操作
```bash
# 创建功能分支
git checkout -b feature/new-feature

# 推送分支（触发前端自动部署）
git push origin feature/new-feature

# 合并到主分支
git checkout main
git merge feature/new-feature
git push origin main
```

## 📋 快速检查清单

### 部署前
- [ ] 功能分支已推送到 GitHub
- [ ] 代码已测试，没有明显错误

### 部署后
- [ ] Vercel 前端预览环境正常
- [ ] 后端测试环境启动成功 (8003端口)
- [ ] API 健康检查通过
- [ ] 前后端集成测试正常

### 合并前
- [ ] 所有功能测试通过
- [ ] 没有破坏现有功能
- [ ] 准备好清理测试环境

## ⚠️ 注意事项

1. **端口区分**：生产环境 8002，测试环境 8003
2. **数据库隔离**：生产 pkb，测试 pkb_test
3. **容器命名**：使用 `-p pkb-test` 项目名称避免冲突
4. **配置恢复**：清理时会自动恢复原始配置文件
5. **分支管理**：测试完成后记得清理功能分支

## 🎯 优势

- ✅ 复用现有目录结构
- ✅ 简单的脚本操作
- ✅ 自动端口和数据库配置
- ✅ 完整的环境隔离
- ✅ 一键部署和清理
