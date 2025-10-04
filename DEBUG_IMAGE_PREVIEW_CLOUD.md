# 🔧 **云服务器调试指南 - 图片预览问题**

## 📋 **问题描述**

**文件**: `迪斯尼景酒套餐.jpg`  
**现象**: 缩略图正常显示，但点击预览无法显示  
**数据库记录**:
```
ID: 375560bd-2ccb-4cd1-ac3c-3206c43a7218
Title: 迪斯尼景酒套餐.jpg
Source URI: webui://迪斯尼景酒套餐_20251004_061528.jpg
```

**核心问题**: title和source_uri文件名不一致（title没有时间戳）

---

## 🚀 **部署修复代码到云服务器**

### **步骤1：在本地提交代码**

```bash
cd /home/kevincyq/pkb-poc

# 查看修改
git diff backend/app/api/files.py

# 添加修改
git add backend/app/api/files.py

# 提交
git commit -m "fix: 增强文件路径查找日志，修复中文文件名预览问题"

# 推送
git push origin feature/search-enhance
```

### **步骤2：SSH到云服务器**

```bash
ssh user@your-cloud-server
cd /home/kevincyq/pkb-poc
```

### **步骤3：拉取并部署**

```bash
# 拉取最新代码
git pull origin feature/search-enhance

# 进入部署目录
cd deploy

# 重建后端容器
docker-compose -f docker-compose.cloud.yml -p pkb-test build pkb-backend

# 重启服务
docker-compose -f docker-compose.cloud.yml -p pkb-test restart pkb-backend

# 查看日志（等待服务启动）
docker-compose -f docker-compose.cloud.yml -p pkb-test logs -f pkb-backend
```

---

## 🔍 **步骤4：复现问题并查看日志**

### **1. 访问前端并点击预览**

打开浏览器，访问测试环境：
```
https://pkb-poc-git-feature-search-enhance-kevincyqs-projects.vercel.app
```

1. 进入"生活点滴"合集
2. 找到"迪斯尼景酒套餐.jpg"
3. 点击预览

### **2. 实时查看后端日志**

在云服务器上执行：
```bash
cd /home/kevincyq/pkb-poc/deploy
docker-compose -f docker-compose.cloud.yml -p pkb-test logs -f pkb-backend | grep -E "(🔍|📋|📂|✅|⚠️|❌)"
```

**关键日志信息**:
- `🔍 Looking for file:` - 前端请求的文件名
- `🔓 Decoded filename:` - URL解码后的文件名
- `✅ Found content in database:` - 是否找到数据库记录
- `📋 Content meta:` - meta字段内容（包含file_path, stored_filename）
- `📂 Database file path:` - 尝试的文件路径和是否存在
- `✅ Found file via...` - 成功找到文件
- `❌ No database record found` - 未找到数据库记录

---

## 🔍 **步骤5：检查文件系统**

### **1. 检查文件是否存在**

```bash
# 进入后端容器
docker exec -it pkb-test-pkb-backend-1 /bin/bash

# 查看uploads目录
ls -lah /app/uploads/ | grep -i "迪"

# 或者查看所有图片文件
ls -lah /app/uploads/*.jpg

# 退出容器
exit
```

### **2. 检查文件权限**

```bash
docker exec pkb-test-pkb-backend-1 ls -lah /app/uploads/ | grep "迪斯尼"
```

预期输出应该包含类似：
```
-rw-r--r-- 1 root root 123K Oct  4 06:15 迪斯尼景酒套餐_20251004_061528.jpg
```

---

## 📊 **步骤6：数据库验证**

### **1. 查询完整meta信息**

```bash
docker exec -it pkb-test-postgres-1 psql -U pkb -d pkb_test
```

然后在psql中执行：
```sql
\x
SELECT * FROM contents WHERE id='375560bd-2ccb-4cd1-ac3c-3206c43a7218';
```

**关键检查**:
- `meta->>'file_path'` - 应该是 `/app/uploads/迪斯尼景酒套餐_20251004_061528.jpg`
- `meta->>'stored_filename'` - 应该是 `迪斯尼景酒套餐_20251004_061528.jpg`
- `source_uri` - 应该是 `webui://迪斯尼景酒套餐_20251004_061528.jpg`

### **2. 退出psql**

```sql
\q
```

---

## 🐛 **常见问题排查**

### **问题A: 文件不存在**

**症状**: 日志显示 `⚠️ Database file path does not exist` 或 `⚠️ Source URI file not found`

**排查**:
```bash
# 1. 检查文件是否在其他位置
docker exec pkb-test-pkb-backend-1 find /app -name "*迪斯尼*" -o -name "*景酒*"

# 2. 检查/data目录
docker exec pkb-test-pkb-backend-1 ls -lah /data/uploads/ 2>/dev/null || echo "No /data/uploads"

# 3. 检查容器挂载
docker inspect pkb-test-pkb-backend-1 | grep -A 10 "Mounts"
```

**解决方案**: 需要确认docker-compose.cloud.yml中的volume挂载配置正确。

---

### **问题B: 数据库查不到记录**

**症状**: 日志显示 `❌ No database record found for: 迪斯尼景酒套餐_20251004_061528.jpg`

**原因**: 前端传的文件名与数据库不匹配

**排查**:
1. 前端Network面板，查看实际请求的URL
2. 对比数据库中的`source_uri`值

**解决方案**: 检查前端是否正确使用`source_uri`构建URL。

---

### **问题C: 字符编码问题**

**症状**: 日志中的中文显示为乱码或`?`

**排查**:
```bash
# 检查容器locale
docker exec pkb-test-pkb-backend-1 locale

# 检查Python编码
docker exec pkb-test-pkb-backend-1 python -c "import sys; print(sys.getdefaultencoding())"
```

**解决方案**: 确保容器locale为`UTF-8`。

---

## ✅ **预期正常日志**

部署修复后，点击预览应该看到类似日志：

```
🔍 Looking for file: 迪斯尼景酒套餐_20251004_061528.jpg
🔍 Filename type: <class 'str'>, repr: '迪斯尼景酒套餐_20251004_061528.jpg'
🔓 Decoded filename: 迪斯尼景酒套餐_20251004_061528.jpg
🔓 Decoded type: <class 'str'>, repr: '迪斯尼景酒套餐_20251004_061528.jpg'
✅ Found content in database: id=375560bd-2ccb-4cd1-ac3c-3206c43a7218, title=迪斯尼景酒套餐.jpg, source_uri=webui://迪斯尼景酒套餐_20251004_061528.jpg
📋 Content meta: {'file_path': '/app/uploads/迪斯尼景酒套餐_20251004_061528.jpg', 'stored_filename': '迪斯尼景酒套餐_20251004_061528.jpg', ...}
📂 Database file path: /app/uploads/迪斯尼景酒套餐_20251004_061528.jpg, exists: True
✅ Found file via database file_path: 迪斯尼景酒套餐_20251004_061528.jpg -> /app/uploads/迪斯尼景酒套餐_20251004_061528.jpg
```

---

## 📝 **调试完成后**

### **1. 收集信息反馈**

如果问题仍未解决，请提供以下信息：

1. **后端日志**（包含emoji标记的那些）
2. **前端Network请求URL**
3. **文件系统检查结果**
4. **数据库meta字段完整内容**

### **2. 移除调试日志（可选）**

如果修复成功，可以移除emoji日志，恢复为普通日志：

```bash
# 创建一个清理日志的commit
git add backend/app/api/files.py
git commit -m "chore: 清理调试日志"
git push origin feature/search-enhance
```

---

## 🎯 **快速命令速查**

```bash
# 云服务器上一键部署
cd /home/kevincyq/pkb-poc && \
git pull origin feature/search-enhance && \
cd deploy && \
docker-compose -f docker-compose.cloud.yml -p pkb-test build pkb-backend && \
docker-compose -f docker-compose.cloud.yml -p pkb-test restart pkb-backend

# 查看实时日志
cd /home/kevincyq/pkb-poc/deploy && \
docker-compose -f docker-compose.cloud.yml -p pkb-test logs -f pkb-backend | grep -E "(🔍|📋|📂|✅|⚠️|❌)"

# 检查文件
docker exec pkb-test-pkb-backend-1 ls -lah /app/uploads/ | grep -i "迪"

# 查询数据库
docker exec -it pkb-test-postgres-1 psql -U pkb -d pkb_test -c "SELECT id, title, source_uri, meta FROM contents WHERE id='375560bd-2ccb-4cd1-ac3c-3206c43a7218';"
```

---

**创建时间**: 2025-10-04  
**问题ID**: 问题2 - 特定图片预览失败
