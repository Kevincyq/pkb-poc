#!/usr/bin/env python3
"""
测试完整的用户认证流程
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8002"

def test_auth_flow():
    """测试完整的认证流程"""
    print("🧪 开始测试用户认证流程...")
    
    # 1. 测试用户注册
    print("\n1️⃣ 测试用户注册...")
    register_data = {
        "username": "user@example.com",
        "password": "password123",
        "display_name": "Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if response.status_code == 200:
            print("✅ 用户注册成功")
            user_data = response.json()
            print(f"   用户ID: {user_data['user']['id']}")
            print(f"   邮箱: {user_data['user']['email']}")
            print(f"   是否Google用户: {user_data['user']['is_google_user']}")
        else:
            print(f"❌ 用户注册失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 注册请求失败: {e}")
        return False
    
    # 2. 测试用户登录
    print("\n2️⃣ 测试用户登录...")
    login_data = {
        "username": "user@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ 用户登录成功")
            login_data = response.json()
            token = login_data['token']
            print(f"   JWT Token: {token[:50]}...")
        else:
            print(f"❌ 用户登录失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return False
    
    # 3. 测试获取用户信息
    print("\n3️⃣ 测试获取用户信息...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        if response.status_code == 200:
            print("✅ 获取用户信息成功")
            user_info = response.json()
            print(f"   用户ID: {user_info['id']}")
            print(f"   邮箱: {user_info['email']}")
            print(f"   显示名: {user_info['display_name']}")
        else:
            print(f"❌ 获取用户信息失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 获取用户信息请求失败: {e}")
        return False
    
    # 4. 测试获取可用云盘提供商
    print("\n4️⃣ 测试获取可用云盘提供商...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/cloud/providers", headers=headers)
        if response.status_code == 200:
            print("✅ 获取云盘提供商成功")
            providers = response.json()
            print(f"   可用提供商: {providers['providers']}")
        else:
            print(f"❌ 获取云盘提供商失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 获取云盘提供商请求失败: {e}")
        return False
    
    # 5. 测试获取云盘状态
    print("\n5️⃣ 测试获取云盘状态...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/cloud/status", headers=headers)
        if response.status_code == 200:
            print("✅ 获取云盘状态成功")
            status = response.json()
            print(f"   云盘状态: {status}")
        else:
            print(f"❌ 获取云盘状态失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 获取云盘状态请求失败: {e}")
        return False
    
    print("\n🎉 所有测试通过！")
    return True

def test_google_user_flow():
    """测试Google用户流程"""
    print("\n🔍 测试Google用户流程...")
    
    # 1. 注册Google用户
    print("\n1️⃣ 注册Google用户...")
    register_data = {
        "username": "google@example.com",
        "password": "google123",
        "google_id": "google_user_123",
        "display_name": "Google User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register-google", json=register_data)
        if response.status_code == 200:
            print("✅ Google用户注册成功")
            user_data = response.json()
            print(f"   用户ID: {user_data['user']['id']}")
            print(f"   是否Google用户: {user_data['user']['is_google_user']}")
            token = user_data['token']
        else:
            print(f"❌ Google用户注册失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Google用户注册请求失败: {e}")
        return False
    
    # 2. 测试Google用户登录
    print("\n2️⃣ 测试Google用户登录...")
    login_data = {
        "username": "google@example.com",
        "password": "google123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ Google用户登录成功")
            login_data = response.json()
            token = login_data['token']
            print(f"   JWT Token: {token[:50]}...")
        else:
            print(f"❌ Google用户登录失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Google用户登录请求失败: {e}")
        return False
    
    # 3. 测试Google OAuth启动（需要先登录）
    print("\n3️⃣ 测试Google OAuth启动...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/google", headers=headers)
        if response.status_code == 200:
            print("✅ Google OAuth启动成功")
            auth_data = response.json()
            print(f"   授权URL: {auth_data['auth_url'][:100]}...")
            print(f"   状态: {auth_data['state']}")
        else:
            print(f"❌ Google OAuth启动失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Google OAuth启动请求失败: {e}")
        return False
    
    print("\n🎉 Google用户流程测试通过！")
    return True

def test_test_user_flow():
    """测试Test用户流程"""
    print("\n🔍 测试Test用户流程...")
    
    # 1. Test用户登录
    print("\n1️⃣ 测试Test用户登录...")
    login_data = {
        "username": "test",
        "password": "test"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/test-login", json=login_data)
        if response.status_code == 200:
            print("✅ Test用户登录成功")
            login_data = response.json()
            token = login_data['token']
            print(f"   JWT Token: {token[:50]}...")
        else:
            print(f"❌ Test用户登录失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Test用户登录请求失败: {e}")
        return False
    
    # 2. 测试Test用户云盘提供商
    print("\n2️⃣ 测试Test用户云盘提供商...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/cloud/providers", headers=headers)
        if response.status_code == 200:
            print("✅ Test用户云盘提供商获取成功")
            providers = response.json()
            print(f"   可用提供商: {providers['providers']}")
        else:
            print(f"❌ Test用户云盘提供商获取失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Test用户云盘提供商请求失败: {e}")
        return False
    
    print("\n🎉 Test用户流程测试通过！")
    return True

if __name__ == "__main__":
    print("🚀 开始测试用户认证系统...")
    
    # 测试普通用户流程
    if not test_auth_flow():
        print("❌ 普通用户流程测试失败")
        sys.exit(1)
    
    # 测试Google用户流程
    if not test_google_user_flow():
        print("❌ Google用户流程测试失败")
        sys.exit(1)
    
    # 测试Test用户流程
    if not test_test_user_flow():
        print("❌ Test用户流程测试失败")
        sys.exit(1)
    
    print("\n🎉 所有认证流程测试通过！")
    print("\n📋 测试总结:")
    print("   ✅ 普通用户注册/登录")
    print("   ✅ Google用户注册/登录")
    print("   ✅ Test用户登录")
    print("   ✅ 用户信息获取")
    print("   ✅ 云盘提供商获取")
    print("   ✅ 云盘状态获取")
    print("   ✅ Google OAuth启动")
