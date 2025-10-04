# 🚀 完整部署步骤

## 第一步：推送代码修改
```bash
# 在本地
git add .
git commit -m "fix: 修复搜索API的HTTPS重定向问题

- 添加ProxyHeadersMiddleware处理代理头
- 前端添加HTTPS强制和重定向处理
- 修复Mixed Content错误"

git push origin feature/search-enhance
```

## 第二步：部署后端修改
```bash
# 在服务器上
cd /path/to/pkb-poc
git pull origin feature/search-enhance
cd deploy
docker-compose -f docker-compose.cloud.yml -p pkb-test restart pkb-backend
```

## 第三步：更新Nginx配置（可选但推荐）
```bash
# 在服务器上，编辑Nginx配置
sudo nano /etc/nginx/sites-available/pkb-test.kmchat.cloud

# 在 location /api/ 块中添加：
proxy_redirect http://pkb-test.kmchat.cloud/ https://pkb-test.kmchat.cloud/;
proxy_redirect http://$host/ https://$host/;
proxy_set_header X-Forwarded-Ssl on;

# 重载Nginx配置
sudo nginx -t  # 测试配置
sudo systemctl reload nginx
```

## 第四步：测试验证
```bash
# 测试API健康检查
curl -I "https://pkb-test.kmchat.cloud/api/health"

# 测试搜索API
curl -X GET "https://pkb-test.kmchat.cloud/api/search?q=test&top_k=5" \
  -H "Origin: https://test-pkb.kmchat.cloud" \
  -H "Accept: application/json"
```

## 预期结果
- ✅ 不再出现Mixed Content错误
- ✅ 搜索返回正确的JSON结果
- ✅ 所有重定向都使用HTTPS
- ✅ 前端搜索功能正常工作
