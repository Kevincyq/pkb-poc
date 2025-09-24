#!/usr/bin/env python3
"""
测试分类搜索修复
"""

import requests
import json
from urllib.parse import quote

def test_category_search():
    """测试分类搜索功能"""
    
    base_url = "https://pkb.kmchat.cloud/api"
    
    print("🔍 测试分类搜索修复")
    print("=" * 50)
    
    # 测试1: 获取所有分类
    print("\n1. 获取所有分类...")
    try:
        response = requests.get(f"{base_url}/category/")
        if response.status_code == 200:
            categories = response.json()
            print(f"✓ 找到 {len(categories.get('categories', []))} 个分类")
            
            # 显示分类信息
            for cat in categories.get('categories', []):
                print(f"  - {cat['name']} (ID: {cat['id']})")
        else:
            print(f"❌ 获取分类失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 获取分类出错: {e}")
        return
    
    # 测试2: 按分类名称搜索（原问题）
    print("\n2. 测试按分类名称搜索...")
    category_name = "科技前沿"
    encoded_name = quote(category_name)
    
    try:
        url = f"{base_url}/search/category/{encoded_name}"
        print(f"请求URL: {url}")
        
        response = requests.get(url)
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("✓ 成功返回JSON格式")
                print(f"结果数量: {len(data.get('results', []))}")
                
                if 'error' in data:
                    print(f"⚠️ API返回错误: {data['error']}")
                else:
                    print("✅ 分类搜索成功！")
                    
                    # 显示前几个结果
                    for i, result in enumerate(data.get('results', [])[:3]):
                        print(f"  结果 {i+1}: {result.get('title', 'No title')}")
                        
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print(f"原始响应: {response.text[:200]}...")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ 请求出错: {e}")
    
    # 测试3: 使用curl命令格式测试
    print("\n3. 测试curl命令兼容性...")
    try:
        # 模拟原始的curl命令
        url = f"{base_url}/search/category/科技前沿"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查是否有results字段，以及是否可以提取title和categories
            results = data.get('results', [])
            print(f"✓ 找到 {len(results)} 个结果")
            
            # 模拟jq处理
            extracted_data = []
            for result in results:
                extracted_data.append({
                    'title': result.get('title'),
                    'categories': result.get('categories', [])
                })
            
            print("✅ jq格式提取成功:")
            for item in extracted_data[:3]:
                print(f"  {json.dumps(item, ensure_ascii=False)}")
                
        else:
            print(f"❌ curl测试失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ curl测试出错: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 测试完成")

if __name__ == "__main__":
    test_category_search()
