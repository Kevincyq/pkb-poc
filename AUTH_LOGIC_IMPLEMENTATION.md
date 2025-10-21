# 用户认证逻辑实现说明

## 🎯 **需求确认**

### **Test用户**
- **用户名**: `test`
- **密码**: `test`
- **认证方式**: 硬编码/写死在数据库中，直接密码验证
- **默认云盘**: Nextcloud
- **权限**: 只能使用Nextcloud

### **Google用户**
- **认证方式**: 真实用户认证 + Google Drive API OAuth授权
- **默认云盘**: Google Drive
- **权限**: 可以访问真实用户的Google Drive数据

## 🔄 **实现逻辑流程**

### **1. Test用户登录流程**

```
用户输入: test / test
    ↓
系统查找: User.email = "test"
    ↓
检查用户类型: user.google_id = None (非Google用户)
    ↓
密码验证: verify_password("test", user.password_hash)
    ↓
生成JWT Token
    ↓
返回用户信息 + Token
    ↓
默认云盘: Nextcloud
```

### **2. Google用户登录流程**

#### **方案A: OAuth直接登录（推荐）**
```
用户点击"Google登录"
    ↓
GET /api/auth/google
    ↓
重定向到Google OAuth页面
    ↓
用户同意授权（包括Google Drive权限）
    ↓
Google回调 /api/auth/callback/gdrive
    ↓
系统自动创建Google用户记录
    ↓
生成JWT Token
    ↓
返回用户信息 + Token
    ↓
默认云盘: Google Drive
```

#### **方案B: 用户名/密码登录**
```
用户输入: user@gmail.com / password
    ↓
系统查找: User.email = "user@gmail.com"
    ↓
检查用户类型: user.google_id != None (Google用户)
    ↓
Google认证: verify_google_user_credentials()
    ↓
调用Firebase Auth API验证
    ↓
生成JWT Token
    ↓
返回用户信息 + Token
    ↓
默认云盘: Google Drive
```

## 🗄️ **数据库设计**

### **User表结构**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    google_id VARCHAR UNIQUE,  -- Google用户ID，test用户为NULL
    email VARCHAR UNIQUE NOT NULL,  -- 用户名/邮箱
    password_hash VARCHAR,  -- 密码哈希，test用户有值
    display_name VARCHAR,
    avatar_url VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### **CloudAuth表结构**
```sql
CREATE TABLE cloud_auths (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR NOT NULL,  -- 'nextcloud' | 'google_drive'
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    folder_id VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## 🔧 **代码实现关键点**

### **1. 用户类型识别**
```python
if user.google_id:
    # Google用户：需要与Google IDP认证
    if not await verify_google_user_credentials(login_data.username, login_data.password):
        raise HTTPException(status_code=401, detail="Google用户认证失败")
else:
    # Test用户：直接验证密码
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
```

### **2. Test用户初始化**
```python
def create_test_user(db: Session):
    test_user = User(
        google_id=None,  # test用户没有Google ID
        email="test",  # 直接使用test作为用户名
        password_hash=hash_password("test"),  # 硬编码密码
        display_name="Test User",
        is_active=True
    )
    # 创建Nextcloud认证
    # 创建存储配置（默认使用Nextcloud）
```

### **3. Google用户OAuth回调**
```python
@router.get("/auth/callback/gdrive")
async def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    # 处理OAuth回调
    callback_result = await google_connector.handle_callback(code, state)
    
    # 查找或创建用户（基于Google ID）
    user = db.query(User).filter(User.google_id == user_info["id"]).first()
    
    if not user:
        # 自动创建Google用户
        user = User(
            google_id=user_info["id"],
            email=user_info["email"],
            display_name=user_info.get("name"),
            is_active=True
        )
        # 创建Google Drive认证
        # 创建存储配置（默认使用Google Drive）
```

## 📋 **API端点说明**

| 端点 | 方法 | 功能 | 用户类型 | 说明 |
|------|------|------|----------|------|
| `/api/auth/login` | POST | 统一用户登录 | 所有用户 | test用户直接验证，Google用户调用Firebase |
| `/api/auth/google` | GET | 启动Google OAuth | Google用户 | 重定向到Google授权页面 |
| `/api/auth/callback/gdrive` | GET | Google OAuth回调 | Google用户 | 自动创建Google用户 |
| `/api/auth/register-google` | POST | Google用户注册 | Google用户 | 使用Firebase创建用户 |
| `/api/cloud/providers` | GET | 获取云盘提供商 | 所有用户 | test用户返回Nextcloud，Google用户返回Google Drive |

## 🧪 **测试命令**

### **Test用户登录**
```bash
curl -X POST "http://34.247.12.46:8010/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test",
    "password": "test"
  }'
```

### **Google用户OAuth登录**
```bash
# 1. 启动OAuth
curl -X GET "http://34.247.12.46:8010/api/auth/google"

# 2. 访问返回的auth_url完成授权
# 3. 系统自动创建用户并返回JWT token
```

### **Google用户注册（备用）**
```bash
curl -X POST "http://34.247.12.46:8010/api/auth/register-google" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@gmail.com",
    "password": "password123",
    "display_name": "User Name"
  }'
```

## ✅ **实现确认**

### **Test用户**
- ✅ 用户名: `test`
- ✅ 密码: `test`
- ✅ 硬编码在数据库中
- ✅ 直接密码验证
- ✅ 默认使用Nextcloud

### **Google用户**
- ✅ 真实用户认证（Firebase）
- ✅ Google Drive API OAuth授权
- ✅ 访问真实用户的Google Drive数据
- ✅ 默认使用Google Drive

### **权限隔离**
- ✅ Test用户只能使用Nextcloud
- ✅ Google用户只能使用Google Drive
- ✅ 不同用户类型使用不同的云盘服务

## 🔍 **验证方法**

运行测试脚本验证实现：
```bash
chmod +x test_auth_logic_verification.sh
./test_auth_logic_verification.sh
```

这个脚本会验证：
1. Test用户登录（test/test）
2. Google用户OAuth流程
3. 用户类型识别
4. 云盘提供商分配
5. 权限隔离
