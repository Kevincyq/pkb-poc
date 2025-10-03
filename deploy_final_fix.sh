#!/bin/bash

echo "🔧 Deploying Final Classification Fix"
echo "===================================="

cd /home/ec2-user/pkb-poc/deploy

echo "🛑 Stopping services..."
docker-compose -f docker-compose.cloud.yml -p pkb-test down

echo "🔨 Rebuilding all services with latest fixes..."
docker-compose -f docker-compose.cloud.yml -p pkb-test build pkb-backend pkb-worker-quick pkb-worker-classify pkb-worker-heavy

echo "🚀 Starting services..."
docker-compose -f docker-compose.cloud.yml -p pkb-test up -d

echo "⏳ Waiting for services to be ready..."
sleep 15

echo "🔍 Checking service status..."
docker-compose -f docker-compose.cloud.yml -p pkb-test ps

echo "✅ Final fix deployment completed!"
echo ""
echo "🧪 Testing fixes:"
echo "1. Upload a new test file"
echo "2. Check classification status updates"
echo "3. Verify thumbnails display correctly"
