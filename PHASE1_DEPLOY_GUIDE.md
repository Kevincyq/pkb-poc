# PKB Phase 1 部署指南（测试环境）

## 🎯 部署目标

第一阶段：扩展数据模型，为分层分类和标签系统做准备

## 📋 修改内容

### 1. 数据模型扩展
- **ContentCategory表**：新增 `role` 和 `source` 字段
- **新增Tag表**：标签管理，支持层级和语义向量
- **新增ContentTag表**：内容标签关联
- **新增Signals表**：决策审计记录

### 2. 服务更新
- 快速分类服务：设置 `role="primary_system"`, `source="heuristic"`
- AI分类服务：设置 `role="primary_system"`, `source="ml"`
- 合集匹配服务：设置 `role="user_rule"`, `source="rule"`

## 🚀 部署步骤（测试环境）

### 方案A：自动化脚本（推荐）

```bash
# 1. 拉取最新代码
git pull origin <branch-name>

# 2. 运行自动化部署脚本
./deploy_phase1.sh
```

### 方案B：手动执行

```bash
# 1. 进入deploy目录
cd deploy

# 2. 备份数据库（可选但推荐）
docker-compose -f docker-compose.cloud.yml -p pkb-test exec postgres pg_dump -U pkb pkb > backup_$(date +%Y%m%d).sql

# 3. 停止服务
docker-compose -f docker-compose.cloud.yml -p pkb-test down

# 4. 启动数据库
docker-compose -f docker-compose.cloud.yml -p pkb-test up -d postgres

# 5. 运行迁移
docker-compose -f docker-compose.cloud.yml -p pkb-test exec backend python -m app.migrate_phase1 --force

# 6. 启动所有服务
docker-compose -f docker-compose.cloud.yml -p pkb-test up -d

# 7. 验证部署
docker-compose -f docker-compose.cloud.yml -p pkb-test ps
curl http://localhost:8000/health
```

## 🔍 验证清单

### 数据库结构验证
```sql
-- 检查新字段
SELECT role, source FROM content_categories LIMIT 5;

-- 检查新表
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('tags', 'content_tags', 'signals');
```

### API验证
```bash
# 基础健康检查
curl http://localhost:8000/health

# 分类功能检查
curl http://localhost:8000/api/categories/

# 文件上传测试
curl -X POST -F "files=@test.txt" http://localhost:8000/api/ingest/upload-multiple
```

## ⚠️ 重要说明

### 测试环境配置
- **项目名称**：`pkb-test`
- **Compose文件**：`docker-compose.cloud.yml`
- **完整命令格式**：`docker-compose -f docker-compose.cloud.yml -p pkb-test <command>`

### 常用命令
```bash
# 查看服务状态
docker-compose -f docker-compose.cloud.yml -p pkb-test ps

# 查看日志
docker-compose -f docker-compose.cloud.yml -p pkb-test logs -f backend

# 进入容器
docker-compose -f docker-compose.cloud.yml -p pkb-test exec backend bash

# 重启服务
docker-compose -f docker-compose.cloud.yml -p pkb-test restart backend
```

## ⚠️ 注意事项

1. **数据安全**：迁移前建议手动备份数据库
2. **服务中断**：迁移过程中服务会短暂停止（约1-2分钟）
3. **兼容性**：所有现有功能保持不变，只是增加了新字段
4. **回滚**：如有问题，可以使用备份文件快速回滚

## 🎉 完成后续

Phase 1 完成后，可以继续进行：
- Phase 2: 关键词搜索引擎
- Phase 3: 标签系统
- Phase 4: 联合搜索
- Phase 5: 前端适配

## 🆘 故障排除

### 常见问题

1. **迁移脚本权限错误**
   ```bash
   chmod +x deploy_phase1.sh
   ```

2. **Docker容器未启动**
   ```bash
   docker-compose -f docker-compose.cloud.yml -p pkb-test up -d
   ```

3. **数据库连接失败**
   ```bash
   docker-compose -f docker-compose.cloud.yml -p pkb-test logs postgres
   ```

4. **Python模块导入错误**
   ```bash
   docker-compose -f docker-compose.cloud.yml -p pkb-test exec backend pip list
   ```

### 项目名称冲突
如果遇到端口冲突或容器名冲突，确保：
- 使用正确的项目名称：`-p pkb-test`
- 检查是否有其他PKB实例在运行
- 必要时清理旧容器：`docker-compose -f docker-compose.cloud.yml -p pkb-test down -v`

### 联系支持
如遇到问题，请提供：
- 错误日志
- 服务状态：`docker-compose -f docker-compose.cloud.yml -p pkb-test ps`
- 系统环境信息
