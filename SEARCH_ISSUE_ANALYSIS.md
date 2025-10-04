# 🔍 搜索API问题分析与解决方案

## 问题现象
前端搜索时出现 **Mixed Content** 错误：
```
Mixed Content: The page at 'https://test-pkb.kmchat.cloud/' was loaded over HTTPS, 
but requested an insecure XMLHttpRequest endpoint 'http://pkb-test.kmchat.cloud/api/search/...'
```

## 🔍 问题根源分析

### Nginx配置与问题关系

你的Nginx配置：
```nginx
location /api/ {
    proxy_pass http://pkb_test_backend;  # ⚠️ 关键：转发到HTTP
    proxy_set_header X-Forwarded-Proto $scheme;  # ✅ 正确设置协议头
}
```

### 问题流程

1. **前端请求** (HTTPS):
   ```
   https://pkb-test.kmchat.cloud/api/search?q=迪斯尼
   ```

2. **Nginx接收并代理** (HTTPS → HTTP):
   ```
   Nginx收到: https://pkb-test.kmchat.cloud/api/search
   转发给后端: http://127.0.0.1:8003/api/search
   设置头: X-Forwarded-Proto: https
   ```

3. **FastAPI处理请求**:
   - 收到HTTP请求（来自Nginx内部代理）
   - 但可能没有正确识别原始HTTPS协议
   - 如果需要重定向（如添加尾部斜杠），会基于收到的HTTP协议生成重定向URL

4. **问题重定向**:
   ```
   FastAPI返回: 307 Temporary Redirect
   Location: http://pkb-test.kmchat.cloud/api/search/  # ❌ HTTP URL
   ```

5. **浏览器Mixed Content错误**:
   - HTTPS页面尝试访问HTTP URL
   - 浏览器安全策略阻止

## 🛠️ 解决方案

### 方案1: Nginx配置修复（推荐）

在Nginx配置中添加重定向修复：
```nginx
location /api/ {
    proxy_pass http://pkb_test_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # 🔧 修复重定向URL - 将HTTP重定向转换为HTTPS
    proxy_redirect http://pkb-test.kmchat.cloud/ https://pkb-test.kmchat.cloud/;
    proxy_redirect http://$host/ https://$host/;
    
    # 🔧 确保FastAPI知道原始协议
    proxy_set_header X-Forwarded-Ssl on;
}
```

### 方案2: FastAPI中间件修复（已实现）

添加了 `ProxyHeadersMiddleware` 来正确处理代理头：
```python
class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 检查X-Forwarded-Proto头
        if "x-forwarded-proto" in request.headers:
            if request.headers["x-forwarded-proto"] == "https":
                request.scope["scheme"] = "https"  # 告诉FastAPI这是HTTPS请求
        
        # 检查X-Forwarded-Ssl头
        if "x-forwarded-ssl" in request.headers:
            if request.headers["x-forwarded-ssl"] == "on":
                request.scope["scheme"] = "https"
                
        response = await call_next(request)
        return response
```

### 方案3: 前端防护修复（已实现）

前端添加了多层保护：
```javascript
// 1. 禁用自动重定向
const api = axios.create({
    maxRedirects: 0,  // 防止自动跟随HTTP重定向
});

// 2. 请求拦截器 - 强制HTTPS
api.interceptors.request.use((config) => {
    if (config.baseURL && config.baseURL.startsWith('http://')) {
        config.baseURL = config.baseURL.replace('http://', 'https://');
    }
    return config;
});

// 3. 响应拦截器 - 处理307重定向
api.interceptors.response.use(null, async (error) => {
    if (error.response?.status === 307) {
        const redirectUrl = error.response.headers.location;
        if (redirectUrl.startsWith('http://')) {
            // 自动重试HTTPS版本
            const httpsUrl = redirectUrl.replace('http://', 'https://');
            return await api.get(httpsUrl.replace(error.config.baseURL, ''));
        }
    }
    return Promise.reject(error);
});
```

## 🎯 推荐解决顺序

1. **立即生效**: 前端修复已部署 ✅
2. **根本解决**: 部署后端中间件修复 🔄
3. **最佳实践**: 更新Nginx配置（可选）

## 🚀 部署步骤

1. **推送代码到GitHub**
2. **在服务器上拉取并重启后端**:
   ```bash
   cd /path/to/pkb-poc
   git pull origin feature/search-enhance
   cd deploy
   docker-compose -f docker-compose.cloud.yml -p pkb-test restart pkb-backend
   ```
3. **测试搜索功能**

## 📊 验证方法

部署后，搜索应该：
- ✅ 不再出现Mixed Content错误
- ✅ 正确返回搜索结果
- ✅ 控制台显示HTTPS请求日志

---

**总结**: 这是一个典型的反向代理HTTPS/HTTP协议转换问题，通过多层修复确保了兼容性和稳定性。
