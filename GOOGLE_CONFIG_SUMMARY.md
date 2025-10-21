# 🎯 Google OAuth 配置摘要

## ❌ **你当前配置的问题**

### 问题1：环境变量名称错误

```bash
# ❌ 错误的配置（你当前使用的）
GDRIVE_CLIENT_ID=196978552337-hi5i0398m6u9a37mk41cn78fso7v0rnl.apps.googleusercontent.com
GDRIVE_CLIENT_SECRET=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
GDRIVE_REDIRECT_URI=https://pkb-bak.kmchat.cloud/api/auth/callback/gdrive

# ✅ 正确的配置（应该使用）
GOOGLE_CLIENT_ID=196978552337-hi5i0398m6u9a37mk41cn78fso7v0rnl.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://pkb-bak.kmchat.cloud/api/auth/callback/gdrive
```

**原因**：代码中读取的是 `GOOGLE_*` 而不是 `GDRIVE_*`

```python
# backend/app/connectors/google_drive.py 第18-20行
self.client_id = os.getenv('GOOGLE_CLIENT_ID')       # 注意：GOOGLE_
self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
```

---

## ✅ **正确的完整配置**

### 方案A：仅OAuth访问Google Drive（推荐，无需Firebase）

```bash
# ===========================================
# Google OAuth 配置
# ===========================================
GOOGLE_PROJECT_ID=honghu-voe2
GOOGLE_CLIENT_ID=196978552337-hi5i0398m6u9a37mk41cn78fso7v0rnl.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://pkb-bak.kmchat.cloud/api/auth/callback/gdrive

# ===========================================
# 存储策略配置
# ===========================================
DEFAULT_CLOUD_PROVIDER=google_drive
LARGE_FILE_THRESHOLD=5242880
ENABLE_GOOGLE_DRIVE=true
ENABLE_NEXTCLOUD=true

# ===========================================
# JWT 配置
# ===========================================
JWT_SECRET_KEY=your_jwt_secret_key_change_this_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

### 方案B：OAuth + Firebase用户认证（高级）

如果你还需要Firebase用户认证系统，添加：

```bash
# Firebase配置（可选）
GOOGLE_FIREBASE_API_KEY=your_firebase_api_key
```

但根据你的需求，**方案A就足够了**。

---

## 🔧 **Google Cloud Console配置要求**

### 1. OAuth 2.0客户端ID配置

在 [Google Cloud Console](https://console.cloud.google.com/) > API和服务 > 凭据 中：

- **应用类型**：Web应用
- **名称**：PKB Backend
- **已获授权的重定向URI**：
  ```
  https://pkb-bak.kmchat.cloud/api/auth/callback/gdrive
  http://34.247.12.46:8010/api/auth/callback/gdrive
  ```

### 2. OAuth同意屏幕配置

在 Google Cloud Console > API和服务 > OAuth同意屏幕 中：

- **用户类型**：外部
- **应用名称**：PKB Drive Access
- **授权域名**：`kmchat.cloud`
- **作用域**：
  ```
  https://www.googleapis.com/auth/drive.file
  https://www.googleapis.com/auth/userinfo.email
  https://www.googleapis.com/auth/userinfo.profile
  openid
  ```

### 3. 启用的API

- ✅ Google Drive API

### 4. 测试用户（外部应用发布前需要）

添加你的Gmail地址作为测试用户：`kevincyq@gmail.com`

---

## 🚀 **部署步骤**

### 1. 更新 `.env` 文件

编辑 `deploy/.env`，修改变量名：

```bash
# 将 GDRIVE_* 改为 GOOGLE_*
sed -i 's/GDRIVE_CLIENT_ID/GOOGLE_CLIENT_ID/g' deploy/.env
sed -i 's/GDRIVE_CLIENT_SECRET/GOOGLE_CLIENT_SECRET/g' deploy/.env
sed -i 's/GDRIVE_REDIRECT_URI/GOOGLE_REDIRECT_URI/g' deploy/.env
```

或手动编辑：

```bash
vim deploy/.env
# 或
nano deploy/.env
```

### 2. 验证配置

```bash
./verify_google_config.sh
```

### 3. 重启服务

```bash
docker-compose -f docker-compose.cloud.yml restart pkb-backend
```

### 4. 测试授权

```bash
./test_auth_logic_verification.sh
```

**预期结果**：OAuth URL应该显示正确的 `client_id` 而不是 `None`

```
https://accounts.google.com/o/oauth2/v2/auth?client_id=196978552337-hi5i0398m6u9a37mk41cn78fso7v0rnl.apps.googleusercontent.com&redirect_uri=https://pkb-bak.kmchat.cloud/api/auth/callback/gdrive&...
```

---

## 🔍 **为什么不需要Firebase？**

### Firebase是什么？

Firebase Authentication是Google提供的用户认证服务，用于：
- 用户注册/登录（邮箱+密码、手机号、社交登录等）
- 管理用户账户
- 多因素认证

### OAuth 2.0是什么？

OAuth 2.0是授权协议，用于：
- 授权第三方应用访问用户的Google服务（如Drive）
- 不需要用户提供密码给第三方应用
- 用户可以随时撤销授权

### 你的需求：

根据你的描述，你需要的是：
1. **Test用户**：本地账户，用户名/密码存在PKB数据库（不需要Firebase）
2. **Google用户**：通过OAuth授权访问Google Drive（不需要Firebase用户认证）

所以，**你只需要OAuth 2.0配置，不需要Firebase配置**。

### 如果你未来需要Firebase：

如果你希望用户可以用Google账号注册PKB账户（而不仅是授权Drive访问），那时再配置Firebase：

1. 在Firebase Console创建项目
2. 启用Authentication服务
3. 获取Web API Key
4. 添加到 `.env`：
   ```bash
   GOOGLE_FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```

但目前**不需要**。

---

## 📋 **配置检查清单**

- [ ] 环境变量名使用 `GOOGLE_*` 而不是 `GDRIVE_*`
- [ ] `GOOGLE_CLIENT_ID` 格式：`xxxxx.apps.googleusercontent.com`
- [ ] `GOOGLE_CLIENT_SECRET` 格式：`GOCSPX-xxxxx`
- [ ] `GOOGLE_REDIRECT_URI` 与Google Cloud Console中的配置一致
- [ ] Google Drive API已启用
- [ ] OAuth同意屏幕已配置
- [ ] 测试用户已添加（外部应用）
- [ ] 服务已重启
- [ ] 运行 `verify_google_config.sh` 验证通过
- [ ] 运行 `test_auth_logic_verification.sh` 测试通过

---

## 🆘 **快速修复命令**

### 一键修复变量名（备份后使用）

```bash
# 备份原文件
cp deploy/.env deploy/.env.backup

# 修复变量名
sed -i 's/^GDRIVE_CLIENT_ID=/GOOGLE_CLIENT_ID=/' deploy/.env
sed -i 's/^GDRIVE_CLIENT_SECRET=/GOOGLE_CLIENT_SECRET=/' deploy/.env
sed -i 's/^GDRIVE_REDIRECT_URI=/GOOGLE_REDIRECT_URI=/' deploy/.env

# 验证
grep "GOOGLE_CLIENT_ID\|GOOGLE_CLIENT_SECRET\|GOOGLE_REDIRECT_URI" deploy/.env

# 重启服务
docker-compose -f docker-compose.cloud.yml restart pkb-backend

# 测试
./verify_google_config.sh
```

---

## 📚 **相关文档**

- `GOOGLE_SETUP_GUIDE.md`：详细的Google Cloud Console配置步骤
- `verify_google_config.sh`：配置验证脚本
- `test_auth_logic_verification.sh`：功能测试脚本
- `deploy/env.template`：环境变量模板

---

## ✅ **总结**

### 主要问题：

1. ❌ 使用了 `GDRIVE_*` 变量名
2. ✅ 应该使用 `GOOGLE_*` 变量名

### 解决方案：

1. 修改 `deploy/.env` 文件中的变量名
2. 重启服务
3. 运行验证脚本

### 为什么没有Firebase配置？

- 你只需要OAuth访问Google Drive
- 不需要Firebase用户认证系统
- Test用户使用本地认证
- Google用户通过OAuth授权访问Drive

配置正确后，用户可以通过浏览器访问授权URL，登录Google账号，授权PKB访问其Google Drive！

