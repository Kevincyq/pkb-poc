#!/usr/bin/env python3
"""
测试搜索API的简单脚本
"""
import requests
import json

# 测试URL
BASE_URL = "https://pkb-test.kmchat.cloud/api"

def test_health():
    """测试健康检查"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"🏥 Health check: {response.status_code}")
        print(f"📋 Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_search_health():
    """测试搜索服务健康检查"""
    try:
        response = requests.get(f"{BASE_URL}/search/health", timeout=10)
        print(f"🔍 Search health check: {response.status_code}")
        print(f"📋 Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Search health check failed: {e}")
        return False

def test_search():
    """测试搜索功能"""
    try:
        params = {
            'q': '迪斯尼',
            'top_k': 10,
            'search_type': 'hybrid'
        }
        
        print(f"🔍 Testing search with params: {params}")
        response = requests.get(f"{BASE_URL}/search", params=params, timeout=30)
        print(f"📊 Search response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search successful!")
            print(f"📋 Query: {data.get('query')}")
            print(f"📊 Total results: {data.get('total')}")
            print(f"⏱️ Response time: {data.get('response_time'):.3f}s")
            print(f"🔧 Search type: {data.get('search_type')}")
            print(f"🤖 Embedding enabled: {data.get('embedding_enabled')}")
            
            if data.get('error'):
                print(f"⚠️ Error: {data.get('error')}")
            
            results = data.get('results', [])
            if results:
                print(f"📄 First result: {results[0].get('title', 'No title')}")
            else:
                print("📄 No results found")
                
        else:
            print(f"❌ Search failed with status: {response.status_code}")
            print(f"📋 Response: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False

def main():
    print("🧪 Testing PKB Search API")
    print("=" * 50)
    
    # 测试基本健康检查
    print("\n1. Testing basic health check...")
    health_ok = test_health()
    
    # 测试搜索服务健康检查
    print("\n2. Testing search service health...")
    search_health_ok = test_search_health()
    
    # 测试搜索功能
    print("\n3. Testing search functionality...")
    search_ok = test_search()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"🏥 Basic health: {'✅' if health_ok else '❌'}")
    print(f"🔍 Search health: {'✅' if search_health_ok else '❌'}")
    print(f"🔍 Search function: {'✅' if search_ok else '❌'}")
    
    if all([health_ok, search_health_ok, search_ok]):
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()
