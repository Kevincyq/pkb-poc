# PKB 部署检查清单

## 修复总结

### ✅ 已完成的修复

1. **分类功能错误修复**
   - 修复 `category_service.py` 中 `content_uuid` 未定义错误
   - 文件: `backend/app/services/category_service.py`

2. **Google Drive 文件支持修复**
   - 修复缩略图生成逻辑（后端）
   - 修复前端缩略图显示（3个组件文件）
   - 文件: `backend/app/api/files.py`, `frontend/src/components/*`

3. **数据库约束强化**
   - 将 `Contents.user_id` 和 `Collections.user_id` 改为 NOT NULL
   - 文件: `backend/app/models.py`

---

## 部署步骤

### 1. 数据库迁移（必须先执行）

⚠️ **重要**: 在生产环境部署前，必须先修复现有的 NULL 值

```bash
# 在云服务器上执行
docker compose -f docker-compose.cloud.yml exec postgres psql -U pkb -d pkb -f /path/to/fix_user_id_constraints.sql

# 或者直接执行 SQL
docker compose -f docker-compose.cloud.yml exec postgres psql -U pkb -d pkb -c "
UPDATE contents SET user_id = (SELECT id FROM users WHERE email = 'test@pkb.local' LIMIT 1) WHERE user_id IS NULL;
UPDATE collections SET user_id = (SELECT id FROM users WHERE email = 'test@pkb.local' LIMIT 1) WHERE user_id IS NULL;
ALTER TABLE contents ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE collections ALTER COLUMN user_id SET NOT NULL;
"
```

### 2. 代码部署

```bash
# 拉取最新代码
git pull

# 重启后端服务
docker compose -f docker-compose.cloud.yml restart pkb-backend

# 重启 Celery workers
docker compose -f docker-compose.cloud.yml restart pkb-celery pkb-worker-classify pkb-worker-quick pkb-worker-heavy

# 检查服务状态
docker compose -f docker-compose.cloud.yml ps
```

### 3. 前端部署

```bash
cd frontend
npm run build
vercel --prod
# 或者推送到 GitHub 自动部署
git push origin main
```

### 4. 验证功能

#### A. 用户认证 ✅
- [ ] 登录功能正常
- [ ] Google 用户登录正常
- [ ] 登出功能正常

#### B. 文件上传和分类 ✅
- [ ] 上传 .txt/.md 文档
- [ ] 上传 PDF 文档
- [ ] 上传图片 (.jpg, .png)
- [ ] 文件自动解析
- [ ] 快速分类完成
- [ ] AI 分类完成
- [ ] 标签自动提取

#### C. 云盘集成 ✅
- [ ] Google Drive 授权
- [ ] 大文件自动上传到 Google Drive
- [ ] 缩略图正常显示
- [ ] 预览功能正常

#### D. 搜索功能 ✅
- [ ] 关键词搜索
- [ ] 语义搜索
- [ ] 混合搜索
- [ ] 按分类搜索

#### E. 知识问答 ✅
- [ ] 提问功能
- [ ] 答案生成
- [ ] 历史记录
- [ ] 基于图片内容的问答

---

## 环境变量检查

```bash
# 必需的环境变量
echo $JWT_SECRET_KEY
echo $DATABASE_URL
echo $TURING_API_KEY
echo $TURING_API_BASE
echo $CELERY_BROKER_URL
echo $CELERY_RESULT_BACKEND

# Google Drive（如果启用）
echo $GOOGLE_CLIENT_ID
echo $GOOGLE_CLIENT_SECRET
```

---

## 常见问题排查

### 问题1: 缩略图不显示
**原因**: Google Drive 文件 `source_uri` 格式为 `google_drive://{file_id}`  
**解决**: ✅ 已修复，前端和后端都支持此格式

### 问题2: 分类状态显示 error
**原因**: `content_uuid` 变量未定义  
**解决**: ✅ 已修复

### 问题3: 数据库约束错误
**原因**: `user_id` 允许 NULL  
**解决**: 运行迁移脚本，然后重启服务

### 问题4: 用户无法查看自己的数据
**原因**: 数据没有正确的 `user_id`  
**解决**: 运行迁移脚本，为 NULL 值设置默认用户

---

## 性能监控

```bash
# 查看后端日志
docker compose -f docker-compose.cloud.yml logs -f pkb-backend

# 查看 Celery worker 日志
docker compose -f docker-compose.cloud.yml logs -f pkb-worker-classify

# 查看错误日志
docker compose -f docker-compose.cloud.yml logs | grep -i error
```

---

## 数据一致性验证

```bash
# 检查是否有 NULL user_id
docker compose -f docker-compose.cloud.yml exec postgres psql -U pkb -d pkb -c "
SELECT COUNT(*) as null_contents FROM contents WHERE user_id IS NULL;
SELECT COUNT(*) as null_collections FROM collections WHERE user_id IS NULL;
"
```

如果返回 0，说明数据一致 ✅

---

## 备份建议

部署前务必备份：

```bash
# 备份数据库
docker compose -f docker-compose.cloud.yml exec postgres pg_dump -U pkb pkb > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份文件存储
tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz /app/uploads
```

---

## 回滚方案

如果部署出现问题：

```bash
# 回滚代码
git checkout previous-commit-hash

# 恢复数据库
docker compose -f docker-compose.cloud.yml exec postgres psql -U pkb -d pkb < backup.sql

# 重启服务
docker compose -f docker-compose.cloud.yml restart
```

---

## 成功标志 ✅

部署成功后，您应该看到：

1. ✅ 所有 API 返回 200 或 201 状态码
2. ✅ 文件上传后能正常解析和分类
3. ✅ 缩略图和预览正常显示
4. ✅ 搜索返回相关结果
5. ✅ 问答功能正常工作
6. ✅ 用户只能看到自己的数据

---

## 联系支持

如果遇到问题，请检查：
1. 日志文件 (`docker compose logs`)
2. 数据库连接 (`docker compose ps postgres`)
3. Celery worker 状态 (`docker compose ps pkb-celery`)
4. API 健康检查 (`curl https://your-domain.com/api/health`)

