#!/usr/bin/env python3
"""
诊断文件存储和缩略图问题的脚本
"""
import requests
import json
from pathlib import Path

def check_remote_api():
    """检查远程API的文件记录"""
    base_url = "https://pkb.kmchat.cloud"
    
    print("=== 远程API诊断 ===")
    
    # 1. 检查缩略图统计
    try:
        response = requests.get(f"{base_url}/api/files/thumbnails/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"缩略图统计: {stats}")
        else:
            print(f"缩略图统计请求失败: {response.status_code}")
    except Exception as e:
        print(f"缩略图统计请求异常: {e}")
    
    # 2. 测试几个具体文件的缩略图
    test_files = ["evening.png", "fuz2.jpg", "fuz1.jpg", "chicken.jpg"]
    
    print("\n=== 测试具体文件 ===")
    for filename in test_files:
        try:
            # 测试缩略图
            thumb_response = requests.get(f"{base_url}/api/files/thumbnail/{filename}")
            print(f"{filename} 缩略图: {thumb_response.status_code}")
            if thumb_response.status_code != 200:
                print(f"  错误: {thumb_response.text}")
            
            # 尝试预生成缩略图
            pregenerate_response = requests.post(f"{base_url}/api/files/pregenerate-thumbnail", 
                                               params={"filename": filename})
            print(f"{filename} 预生成: {pregenerate_response.status_code}")
            if pregenerate_response.status_code == 200:
                result = pregenerate_response.json()
                print(f"  结果: {result}")
            else:
                print(f"  错误: {pregenerate_response.text}")
                
        except Exception as e:
            print(f"{filename} 测试异常: {e}")
        print()

if __name__ == "__main__":
    check_remote_api()
