#!/bin/bash

echo "🔧 Deploying Frontend & Backend Fixes"
echo "====================================="

cd /home/ec2-user/pkb-poc/deploy

echo "🛑 Stopping all services..."
docker-compose -f docker-compose.cloud.yml -p pkb-test down

echo "🔨 Rebuilding all services with latest fixes..."
docker-compose -f docker-compose.cloud.yml -p pkb-test build

echo "🚀 Starting services..."
docker-compose -f docker-compose.cloud.yml -p pkb-test up -d

echo "⏳ Waiting for services to be ready..."
sleep 20

echo "🔍 Checking service status..."
docker-compose -f docker-compose.cloud.yml -p pkb-test ps

echo "🧪 Testing fixes..."

echo "1. Testing file path lookup..."
docker-compose -f docker-compose.cloud.yml -p pkb-test exec pkb-backend python -c "
from app.api.files import get_file_path
from app.db import SessionLocal
import urllib.parse

db = SessionLocal()
try:
    # 测试中文文件名解码
    encoded_name = '%E8%BF%AA%E6%96%AF%E5%B0%BC%E6%99%AF%E9%85%92%E5%A5%97%E9%A4%90.jpg'
    decoded_name = urllib.parse.unquote(encoded_name)
    print(f'Encoded: {encoded_name}')
    print(f'Decoded: {decoded_name}')
    
    # 测试文件路径查找
    file_path = get_file_path(decoded_name, db)
    print(f'File path: {file_path}')
    print(f'File exists: {file_path.exists()}')
    
except Exception as e:
    print(f'Error: {e}')
finally:
    db.close()
"

echo "2. Testing thumbnail generation..."
docker-compose -f docker-compose.cloud.yml -p pkb-test exec pkb-backend ls -la /tmp/pkb_thumbnails/

echo "3. Testing API endpoint..."
curl -I "http://localhost:8003/api/health"

echo "✅ Frontend & Backend fix deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Open browser and test file upload"
echo "2. Check if thumbnails display correctly"
echo "3. Verify classification status updates properly"
echo "4. Monitor browser console for any remaining errors"
