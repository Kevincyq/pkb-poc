# Google认证API集成指南

## 🔐 **Google认证API配置步骤**

### **1. 创建Google Cloud项目**

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 记录项目ID（用于 `GOOGLE_PROJECT_ID`）

### **2. 启用Firebase Authentication**

1. 在Google Cloud Console中，转到 **Firebase** 页面
2. 创建Firebase项目（如果还没有）
3. 启用 **Authentication** 服务
4. 在 **Authentication > Sign-in method** 中启用 **Email/Password** 提供商

### **3. 获取Firebase API Key**

1. 在Firebase控制台中，转到 **Project Settings**
2. 在 **General** 标签页中找到 **Web API Key**
3. 复制API Key（用于 `GOOGLE_FIREBASE_API_KEY`）

### **4. 配置环境变量**

在 `.env` 文件中添加以下配置：

```bash
# Google认证配置
GOOGLE_PROJECT_ID=your_google_project_id
GOOGLE_FIREBASE_API_KEY=your_firebase_api_key
GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json

# Google OAuth配置（用于Google Drive）
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8002/api/auth/callback/gdrive
```

### **5. 创建服务账号（可选）**

如果需要使用Google Cloud API（如Google Drive API），需要创建服务账号：

1. 在Google Cloud Console中，转到 **IAM & Admin > Service Accounts**
2. 创建新的服务账号
3. 下载JSON密钥文件
4. 将文件路径设置为 `GOOGLE_SERVICE_ACCOUNT_FILE`

### **6. 测试Google认证**

#### **测试用户注册**
```bash
curl -X POST "http://34.247.12.46:8010/api/auth/register-google" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@gmail.com",
    "password": "password123",
    "display_name": "Test User"
  }'
```

#### **测试用户登录**
```bash
curl -X POST "http://34.247.12.46:8010/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@gmail.com",
    "password": "password123"
  }'
```

## 🔧 **API端点说明**

### **用户认证API**

| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/api/auth/login` | POST | 用户登录 | 支持test用户和Google用户 |
| `/api/auth/register-google` | POST | Google用户注册 | 使用Google Identity Platform |
| `/api/auth/google` | GET | 启动Google OAuth | 用于Google Drive授权 |
| `/api/auth/callback/gdrive` | GET | Google OAuth回调 | 处理Google Drive授权 |

### **请求格式**

#### **登录请求**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

#### **注册请求**
```json
{
  "username": "user@example.com",
  "password": "password123",
  "display_name": "User Name"
}
```

## 🛡️ **安全注意事项**

1. **API Key保护**: 确保Firebase API Key不被泄露
2. **HTTPS**: 生产环境必须使用HTTPS
3. **密码策略**: 建议实施强密码策略
4. **令牌管理**: 定期刷新访问令牌
5. **错误处理**: 不要暴露敏感的错误信息

## 🐛 **常见问题**

### **1. 认证失败**
- 检查Firebase API Key是否正确
- 确认用户已在Firebase中注册
- 检查网络连接

### **2. 用户创建失败**
- 检查Firebase项目配置
- 确认Email/Password提供商已启用
- 检查用户是否已存在

### **3. 令牌验证失败**
- 检查令牌是否过期
- 确认令牌格式正确
- 检查Firebase配置

## 📚 **相关文档**

- [Firebase Authentication](https://firebase.google.com/docs/auth)
- [Google Identity Platform](https://cloud.google.com/identity-platform)
- [Firebase REST API](https://firebase.google.com/docs/reference/rest/auth)
