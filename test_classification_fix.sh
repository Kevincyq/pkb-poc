#!/bin/bash

echo "🔧 Testing Classification Fix"
echo "============================"

cd /home/ec2-user/pkb-poc/deploy

echo "🛑 Stopping services..."
docker-compose -f docker-compose.cloud.yml -p pkb-test down

echo "🔨 Rebuilding backend image..."
docker-compose -f docker-compose.cloud.yml -p pkb-test build pkb-backend

echo "🚀 Starting services..."
docker-compose -f docker-compose.cloud.yml -p pkb-test up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "🔍 Checking service status..."
docker-compose -f docker-compose.cloud.yml -p pkb-test ps

echo "✅ Classification fix deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Upload a test file through the frontend"
echo "2. Check the classification status and meta fields"
echo "3. Verify thumbnails are generated correctly"
