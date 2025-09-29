# PKB 开发部署工作流程

## 🔄 完整的开发部署流程

### 本地开发环境操作

```bash
# 1. 创建新功能分支
git checkout -b feature/new-awesome-feature

# 2. 进行开发
# 修改代码、添加功能...

# 3. 测试本地更改
cd frontend && npm run dev  # 测试前端
cd backend && python -m uvicorn app.main:app --reload  # 测试后端

# 4. 提交更改
git add .
git commit -m "feat: add awesome new feature

- Add new API endpoint
- Update frontend UI
- Add tests"

# 5. 推送分支
git push origin feature/new-awesome-feature

# 6. 合并到主分支（通过 PR 或直接合并）
git checkout main
git merge feature/new-awesome-feature
git push origin main

# 7. 清理分支
git branch -d feature/new-awesome-feature
git push origin --delete feature/new-awesome-feature
```

### 服务器端更新操作

#### 方案一：使用自动更新脚本（推荐）
```bash
cd /home/ec2-user/pkb-new
./update-pkb.sh
```

#### 方案二：手动更新
```bash
cd /home/ec2-user/pkb-new
git pull origin main
docker-compose -f deploy/docker-compose.cloud.yml up -d --build
```

#### 方案三：验证更新
```bash
cd /home/ec2-user/pkb-new
./verify-pkb-deployment.sh
```

## 🛠️ 常用维护命令

### 查看服务状态
```bash
cd /home/ec2-user/pkb-new/deploy
docker-compose ps
```

### 查看日志
```bash
cd /home/ec2-user/pkb-new/deploy
docker-compose logs -f pkb-backend
```

### 重启特定服务
```bash
cd /home/ec2-user/pkb-new/deploy
docker-compose restart pkb-backend
```

### 备份数据
```bash
cd /home/ec2-user/pkb-new
./backup-pkb.sh
```

## 🚨 紧急回滚

如果更新后出现问题：

```bash
# 1. 查看最近的提交
git log --oneline -5

# 2. 回滚到上一个版本
git reset --hard HEAD~1

# 3. 重新部署
docker-compose -f deploy/docker-compose.cloud.yml up -d --build

# 4. 或者使用备份恢复
cd /opt/pkb-migration-backup-*
sudo ./restore.sh
```

## 📋 部署检查清单

每次部署后检查：
- [ ] API 健康检查通过
- [ ] 数据库连接正常
- [ ] 文件上传功能正常
- [ ] 问答功能正常
- [ ] 所有 Worker 服务运行
- [ ] 日志无严重错误

## 🔧 开发环境 vs 生产环境

### 本地开发
- 使用 `npm run dev` 和 `uvicorn --reload`
- 直接修改代码即时生效
- 使用开发数据库

### 生产环境
- 使用 Docker 容器部署
- 需要重新构建镜像
- 使用生产数据库和配置
