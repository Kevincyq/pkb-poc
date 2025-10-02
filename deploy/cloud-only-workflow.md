# PKB 云端开发工作流程

> 适用于没有本地后端开发环境的情况

## 🎯 工作流程概述

```
本地开发 → 推送分支 → 云端部署测试 → 合并或回滚
```

## 🚀 详细操作步骤

### 1. 本地创建功能分支

```bash
# 确保在最新的 main 分支
git checkout main
git pull origin main

# 创建新功能分支
git checkout -b feature/user-auth-system

# 修改代码（前端 + 后端）
# ... 编辑代码 ...

# 提交更改
git add .
git commit -m "feat: add user authentication system

- Add user registration API
- Create login/logout endpoints  
- Update frontend auth components
- Add JWT token management"

# 推送到 GitHub
git push origin feature/user-auth-system
```

### 2. 云端部署测试

```bash
# SSH 到服务器
ssh ec2-user@your-server-ip

# 使用分支部署脚本
cd /home/ec2-user/pkb-new
./deploy/deploy-branch.sh feature/user-auth-system
```

### 3. 测试验证

```bash
# 前端测试
# 访问 https://pkb-poc.kmchat.cloud
# 测试新功能界面和交互

# 后端 API 测试
curl https://pkb.kmchat.cloud/api/health
curl https://pkb.kmchat.cloud/api/docs

# 查看服务状态
cd /home/ec2-user/pkb-new/deploy
docker-compose ps
docker-compose logs -f pkb-backend
```

### 4. 处理结果

#### 4a. 测试通过 - 合并到 main

```bash
# 本地合并
git checkout main
git merge feature/user-auth-system
git push origin main

# 服务器部署 main 分支
cd /home/ec2-user/pkb-new
./deploy/deploy-branch.sh main

# 清理功能分支
git branch -d feature/user-auth-system
git push origin --delete feature/user-auth-system
```

#### 4b. 测试失败 - 快速回滚

```bash
# 服务器端快速回滚
cd /home/ec2-user/pkb-new
./deploy/rollback.sh

# 本地修复问题
git checkout feature/user-auth-system
# ... 修复代码 ...
git add .
git commit -m "fix: resolve authentication issues"
git push origin feature/user-auth-system

# 重新部署测试
# 重复步骤 2-4
```

## 🛠️ 常用命令速查

### 服务器端操作

```bash
# 部署指定分支
./deploy/deploy-branch.sh <branch-name>

# 快速回滚
./deploy/rollback.sh

# 查看当前部署状态
git branch --show-current
cat .last_deployed_branch

# 查看服务状态
cd deploy && docker-compose ps

# 查看服务日志
cd deploy && docker-compose logs -f pkb-backend

# 重启服务（不重新构建）
cd deploy && docker-compose restart pkb-backend
```

### 本地操作

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 推送分支
git push origin feature/new-feature

# 合并到 main
git checkout main
git merge feature/new-feature
git push origin main

# 删除分支
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```

## ⚠️ 注意事项

### 1. 前端部署
- 前端会自动部署到 Vercel（基于 main 分支）
- 功能分支测试时，前端仍然是 main 分支的版本
- 如果前端有重大变更，需要先合并到 main 才能看到效果

### 2. 数据安全
- 生产环境测试可能影响真实数据
- 重要功能测试前建议备份数据
- 使用测试数据进行验证

### 3. 服务稳定性
- 部署脚本包含自动回滚机制
- 如果健康检查失败会自动回滚
- 手动回滚命令：`./deploy/rollback.sh`

## 🔧 故障排除

### 部署失败

```bash
# 查看详细日志
cd /home/ec2-user/pkb-new/deploy
docker-compose logs --tail=100 pkb-backend

# 检查容器状态
docker-compose ps

# 手动重启
docker-compose down
docker-compose up -d --build
```

### 服务异常

```bash
# 快速回滚到稳定版本
./deploy/rollback.sh

# 或者回滚到 main 分支
./deploy/deploy-branch.sh main
```

### 数据库问题

```bash
# 检查数据库连接
cd /home/ec2-user/pkb-new/deploy
docker-compose exec postgres psql -U pkb -d pkb -c "SELECT 1;"

# 查看数据库日志
docker-compose logs postgres
```

## 📋 开发检查清单

### 推送前检查
- [ ] 代码已提交并推送到功能分支
- [ ] 提交信息清晰描述了变更内容
- [ ] 没有包含敏感信息（密码、密钥等）

### 部署前检查
- [ ] 确认要部署的分支名称
- [ ] 备份重要数据（如有需要）
- [ ] 通知团队成员（如有协作）

### 测试检查
- [ ] 前端界面正常加载
- [ ] 新功能按预期工作
- [ ] 现有功能没有被破坏
- [ ] API 健康检查通过
- [ ] 没有明显的错误日志

### 合并前检查
- [ ] 所有测试通过
- [ ] 代码审查完成（如有需要）
- [ ] 文档已更新（如有需要）
- [ ] 准备好处理可能的问题

## 🎯 最佳实践

1. **小步快跑**：每个功能分支保持较小的变更范围
2. **及时测试**：推送后立即部署测试，快速发现问题
3. **做好备份**：重要更新前备份数据和配置
4. **保持沟通**：团队协作时及时沟通部署状态
5. **文档更新**：重要变更及时更新相关文档
