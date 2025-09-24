#!/usr/bin/env python3
"""
测试搜索去重和相关性改进
"""
import requests
import json
from urllib.parse import urlencode

def test_search_deduplication():
    """测试搜索去重功能"""
    base_url = "https://pkb.kmchat.cloud/api/search/"
    
    test_cases = [
        {
            "name": "语义搜索 - 机器学习",
            "params": {"q": "机器学习的发展前景", "search_type": "semantic"},
            "expected_improvement": "只显示相关文档，过滤掉ppp.txt等不相关内容"
        },
        {
            "name": "语义搜索 - 山顶照片", 
            "params": {"q": "山顶照片", "search_type": "semantic"},
            "expected_improvement": "只显示图片文件，过滤掉.md和.txt文档"
        },
        {
            "name": "关键词搜索 - 人工智能",
            "params": {"q": "人工智能", "search_type": "keyword"},
            "expected_improvement": "每个文档只出现一次"
        },
        {
            "name": "混合搜索 - 技术文档",
            "params": {"q": "技术文档", "search_type": "hybrid"},
            "expected_improvement": "结合关键词和语义搜索，去重后结果"
        }
    ]
    
    print("🔍 测试搜索去重和相关性改进")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        
        try:
            # 构建URL
            url = f"{base_url}?{urlencode(test_case['params'])}"
            print(f"请求URL: {url}")
            
            # 发送请求
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                print(f"✓ 状态码: {response.status_code}")
                print(f"✓ 结果数量: {len(results)}")
                
                # 检查去重效果
                titles = [r.get('title', '') for r in results]
                unique_titles = list(set(titles))
                duplicate_count = len(titles) - len(unique_titles)
                
                if duplicate_count == 0:
                    print("✅ 去重成功：没有重复文档")
                else:
                    print(f"❌ 仍有重复：{duplicate_count} 个重复文档")
                    # 显示重复的文档
                    from collections import Counter
                    title_counts = Counter(titles)
                    duplicates = {title: count for title, count in title_counts.items() if count > 1}
                    if duplicates:
                        print("重复文档:")
                        for title, count in duplicates.items():
                            print(f"  - {title}: {count} 次")
                
                # 显示前5个结果的标题和分数
                print("前5个结果:")
                for j, result in enumerate(results[:5], 1):
                    title = result.get('title', 'N/A')
                    score = result.get('score', 0)
                    modality = result.get('modality', 'N/A')
                    print(f"  {j}. {title} (分数: {score:.3f}, 类型: {modality})")
                
                # 智能分析结果质量
                _analyze_result_quality(test_case, results)
                
                print(f"预期改进: {test_case['expected_improvement']}")
                
            else:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 测试完成")
    print("\n💡 如果仍有重复结果，请检查:")
    print("1. 后端服务是否已重启并加载了新代码")
    print("2. 数据库中是否存在真正的重复内容")
    print("3. 相似度阈值是否需要进一步调整")

def _analyze_result_quality(test_case, results):
    """分析搜索结果质量"""
    query = test_case['params']['q']
    
    if "山顶照片" in query:
        # 分析图片搜索结果
        image_count = sum(1 for r in results if r.get('modality') == 'image')
        non_image_count = len(results) - image_count
        
        if non_image_count == 0:
            print("✅ 智能过滤成功：只返回图片文件")
        else:
            print(f"⚠️  仍有非图片文件：{non_image_count} 个")
            for r in results:
                if r.get('modality') != 'image':
                    print(f"   - {r.get('title')} (类型: {r.get('modality')}, 分数: {r.get('score', 0):.3f})")
    
    elif "机器学习" in query:
        # 分析机器学习相关搜索
        low_score_count = sum(1 for r in results if r.get('score', 0) < 0.25)
        irrelevant_files = [r for r in results if 'ppp.txt' in r.get('title', '') or r.get('score', 0) < 0.25]
        
        if not irrelevant_files:
            print("✅ 智能过滤成功：过滤掉不相关内容")
        else:
            print(f"⚠️  仍有不相关内容：{len(irrelevant_files)} 个")
            for r in irrelevant_files:
                print(f"   - {r.get('title')} (分数: {r.get('score', 0):.3f})")

if __name__ == "__main__":
    test_search_deduplication()
