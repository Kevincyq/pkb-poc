# 🔐 Google Drive OAuth 配置完整指南

## 📋 目标
配置PKB后端通过OAuth 2.0授权访问用户的Google Drive，实现文件存储和管理功能。

---

## ✅ 第一步：创建Google Cloud项目

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 点击顶部导航栏的项目选择器
3. 点击 **"新建项目"**
4. 输入项目名称：`pkb-drive-app` 或 `honghu-voe2`（你已创建）
5. 记录项目ID（用于环境变量 `GOOGLE_PROJECT_ID`）

---

## ✅ 第二步：启用Google Drive API

1. 在左侧菜单中选择 **"API和服务" > "库"**
2. 搜索 **"Google Drive API"**
3. 点击进入后，点击 **"启用"** 按钮
4. 等待API启用完成（通常几秒钟）

---

## ✅ 第三步：创建OAuth 2.0客户端ID

### 1. 配置OAuth同意屏幕

在创建客户端ID之前，必须先配置同意屏幕：

1. 转到 **"API和服务" > "OAuth同意屏幕"**
2. 选择用户类型：
   - **内部**：仅限组织内用户（如果你有Google Workspace）
   - **外部**：任何Google用户都可以使用（推荐）
3. 点击 **"创建"**
4. 填写应用信息：
   ```
   应用名称：PKB Drive Access
   用户支持电子邮件：<你的Gmail地址>
   应用徽标：（可选）
   应用网域：
     - 应用首页：https://pkb.kmchat.cloud
     - 应用隐私权政策链接：https://pkb.kmchat.cloud/privacy
     - 应用服务条款链接：https://pkb.kmchat.cloud/terms
   已获授权的网域：
     - kmchat.cloud
   开发者联系信息：<你的Gmail地址>
   ```
5. 点击 **"保存并继续"**

### 2. 添加作用域（Scopes）

1. 点击 **"添加或移除作用域"**
2. 搜索并勾选以下作用域：
   ```
   https://www.googleapis.com/auth/drive.file
   https://www.googleapis.com/auth/userinfo.email
   https://www.googleapis.com/auth/userinfo.profile
   openid
   ```
3. 解释：
   - `drive.file`：只能访问通过此应用创建或打开的文件（最小权限）
   - `userinfo.email`：获取用户邮箱
   - `userinfo.profile`：获取用户基本信息
   - `openid`：用于身份验证
4. 点击 **"更新"** 然后 **"保存并继续"**

### 3. 添加测试用户（外部应用需要）

如果你选择了"外部"用户类型，在发布前需要添加测试用户：

1. 点击 **"添加用户"**
2. 输入你的Gmail地址（例如：`kevincyq@gmail.com`）
3. 点击 **"保存并继续"**
4. 检查摘要，点击 **"返回信息中心"**

### 4. 创建OAuth 2.0客户端ID

1. 转到 **"API和服务" > "凭据"**
2. 点击 **"创建凭据" > "OAuth 2.0客户端ID"**
3. 选择应用类型：**Web 应用**
4. 输入名称：`PKB Backend`
5. **已获授权的JavaScript来源（可选）**：
   ```
   https://pkb.kmchat.cloud
   http://34.247.12.46:8010
   ```
6. **已获授权的重定向URI（重要！）**：
   ```
   https://pkb-bak.kmchat.cloud/api/auth/callback/gdrive
   http://34.247.12.46:8010/api/auth/callback/gdrive
   ```
7. 点击 **"创建"**
8. 记录生成的凭据：
   ```
   客户端ID：xxxxx.apps.googleusercontent.com
   客户端密钥：GOCSPX-xxxxx
   ```

---

## ✅ 第四步：配置PKB环境变量

### 1. 编辑 `.env` 文件

在你的服务器上编辑 `/home/kevincyq/pkb-poc/deploy/.env`：

```bash
# ===========================================
# Google OAuth 配置（必须）
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
# JWT 认证配置
# ===========================================
JWT_SECRET_KEY=your_jwt_secret_key_change_this_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

### 2. **重要提醒**

- ❌ **变量名错误**：`GDRIVE_CLIENT_ID` → ✅ **正确**：`GOOGLE_CLIENT_ID`
- ❌ **变量名错误**：`GDRIVE_CLIENT_SECRET` → ✅ **正确**：`GOOGLE_CLIENT_SECRET`
- ❌ **变量名错误**：`GDRIVE_REDIRECT_URI` → ✅ **正确**：`GOOGLE_REDIRECT_URI`

代码中读取的是 `GOOGLE_*` 而不是 `GDRIVE_*`！

---

## ✅ 第五步：部署和测试

### 1. 重新部署服务

```bash
cd /home/kevincyq/pkb-poc

# 推送代码到GitHub
git add .
git commit -m "更新Google OAuth配置"
git push

# 重新部署（在云端服务器）
docker-compose -f docker-compose.cloud.yml down
docker-compose -f docker-compose.cloud.yml build pkb-backend
docker-compose -f docker-compose.cloud.yml up -d
```

### 2. 运行测试脚本

```bash
cd /home/kevincyq/pkb-poc
./test_auth_logic_verification.sh
```

### 3. 检查配置

```bash
./check_google_config.sh
```

### 4. 预期结果

OAuth授权URL应该显示：
```
https://accounts.google.com/o/oauth2/v2/auth?client_id=196978552337-hi5i0398m6u9a37mk41cn78fso7v0rnl.apps.googleusercontent.com&redirect_uri=https://pkb-bak.kmchat.cloud/api/auth/callback/gdrive&scope=...
```

**不应该出现**：`client_id=None` 或 `redirect_uri=None`

---

## ✅ 第六步：测试授权流程

### 1. 浏览器访问

```
https://pkb-bak.kmchat.cloud/api/auth/google
```

或

```
http://34.247.12.46:8010/api/auth/google
```

### 2. 预期流程

1. 浏览器跳转到Google登录页面
2. 输入你的Gmail账号密码
3. Google显示授权请求：
   ```
   PKB Drive Access 想要访问您的 Google 帐号
   
   这将允许 PKB Drive Access 执行以下操作：
   ✓ 查看和管理此应用创建或打开的 Google 云端硬盘文件
   ✓ 查看您的电子邮件地址
   ✓ 查看您的个人信息
   ```
4. 点击 **"允许"**
5. 跳转回：`https://pkb-bak.kmchat.cloud/api/auth/callback/gdrive?code=xxxxx`
6. 后端自动处理，返回JWT token和用户信息

---

## 🔧 常见问题

### Q1: OAuth URL显示 `client_id=None`

**原因**：环境变量名称错误或未加载

**解决**：
1. 检查 `.env` 文件中变量名是 `GOOGLE_CLIENT_ID` 而不是 `GDRIVE_CLIENT_ID`
2. 重启服务：`docker-compose -f docker-compose.cloud.yml restart pkb-backend`
3. 检查环境变量：`docker-compose -f docker-compose.cloud.yml exec pkb-backend env | grep GOOGLE`

### Q2: 授权后显示 "redirect_uri_mismatch"

**原因**：重定向URI不匹配

**解决**：
1. 检查 `.env` 中的 `GOOGLE_REDIRECT_URI` 是否与Google Cloud Console中配置的完全一致
2. 注意 `http` vs `https`
3. 注意域名和端口是否一致

### Q3: 授权后显示 "access_denied"

**原因**：应用未发布或测试用户未添加

**解决**：
1. 如果是"外部"应用，确保在OAuth同意屏幕中添加了测试用户
2. 或者发布应用（转到OAuth同意屏幕 → 发布应用）

### Q4: "Firebase authentication not configured"

**原因**：未配置Firebase API Key

**解决**：
- 如果只使用OAuth访问Google Drive，**不需要Firebase配置**
- 这个警告可以忽略
- Google用户应该通过OAuth授权登录，而不是用户名/密码登录

---

## 📚 参考链接

- [Google OAuth 2.0 文档](https://developers.google.com/identity/protocols/oauth2)
- [Google Drive API 文档](https://developers.google.com/drive/api/v3/about-sdk)
- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)（测试工具）

---

## ✅ 配置检查清单

- [ ] Google Cloud项目已创建，记录了项目ID
- [ ] Google Drive API已启用
- [ ] OAuth同意屏幕已配置
- [ ] OAuth 2.0客户端ID已创建
- [ ] 重定向URI已正确配置（包括 `https://pkb-bak.kmchat.cloud/api/auth/callback/gdrive`）
- [ ] `.env` 文件中变量名正确（`GOOGLE_CLIENT_ID` 而不是 `GDRIVE_CLIENT_ID`）
- [ ] `.env` 文件中的值与Google Cloud Console中的一致
- [ ] 服务已重启
- [ ] 测试脚本运行成功，OAuth URL显示正确的 client_id

完成以上步骤后，Google Drive OAuth授权应该可以正常工作！

