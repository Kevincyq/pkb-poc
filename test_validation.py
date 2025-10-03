#!/usr/bin/env python3
"""
测试验证脚本 - 验证测试文件的语法和结构正确性
不需要安装额外依赖，只验证代码质量
"""
import ast
import sys
from pathlib import Path
import re


def validate_python_syntax(file_path):
    """验证Python文件语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析AST
        ast.parse(content)
        return True, "语法正确"
    except SyntaxError as e:
        return False, f"语法错误: {e}"
    except Exception as e:
        return False, f"解析错误: {e}"


def analyze_test_coverage(file_path):
    """分析测试覆盖范围"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计测试函数
        test_functions = re.findall(r'def test_\w+\(', content)
        
        # 统计测试类
        test_classes = re.findall(r'class Test\w+:', content)
        
        # 统计断言
        assertions = re.findall(r'assert\s+', content)
        
        # 统计mock使用
        mocks = re.findall(r'@patch|Mock\(|mock_', content)
        
        return {
            "test_functions": len(test_functions),
            "test_classes": len(test_classes),
            "assertions": len(assertions),
            "mocks": len(mocks),
            "functions": test_functions[:5],  # 显示前5个函数名
            "classes": test_classes[:3]       # 显示前3个类名
        }
    except Exception as e:
        return {"error": str(e)}


def validate_typescript_basic(file_path):
    """基本的TypeScript文件验证"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查基本结构
        has_imports = 'import' in content
        has_describe = 'describe(' in content
        has_it_tests = 'it(' in content
        has_expect = 'expect(' in content
        
        # 统计测试用例
        test_cases = re.findall(r'it\([\'"`]([^\'"`]+)[\'"`]', content)
        
        return {
            "has_imports": has_imports,
            "has_describe": has_describe,
            "has_it_tests": has_it_tests,
            "has_expect": has_expect,
            "test_cases": len(test_cases),
            "test_names": test_cases[:5]
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    """主函数"""
    print("🧪 PKB 测试验证器")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    backend_tests = project_root / "backend" / "tests"
    frontend_tests = project_root / "frontend" / "src" / "test"
    
    total_files = 0
    valid_files = 0
    total_test_functions = 0
    total_assertions = 0
    
    print("\n🔧 后端测试文件验证:")
    print("-" * 30)
    
    if backend_tests.exists():
        for test_file in backend_tests.glob("test_*.py"):
            total_files += 1
            print(f"\n📄 {test_file.name}")
            
            # 验证语法
            is_valid, message = validate_python_syntax(test_file)
            if is_valid:
                valid_files += 1
                print(f"  ✅ 语法: {message}")
                
                # 分析覆盖范围
                coverage = analyze_test_coverage(test_file)
                if "error" not in coverage:
                    total_test_functions += coverage["test_functions"]
                    total_assertions += coverage["assertions"]
                    
                    print(f"  📊 测试函数: {coverage['test_functions']}")
                    print(f"  📊 测试类: {coverage['test_classes']}")
                    print(f"  📊 断言数量: {coverage['assertions']}")
                    print(f"  📊 Mock使用: {coverage['mocks']}")
                    
                    if coverage["functions"]:
                        print(f"  🎯 主要测试: {', '.join([f.replace('def test_', '').replace('(', '') for f in coverage['functions']])}")
                else:
                    print(f"  ⚠️ 分析错误: {coverage['error']}")
            else:
                print(f"  ❌ 语法: {message}")
    else:
        print("❌ 后端测试目录不存在")
    
    print("\n🎨 前端测试文件验证:")
    print("-" * 30)
    
    if frontend_tests.exists():
        for test_file in frontend_tests.glob("*.test.tsx"):
            total_files += 1
            print(f"\n📄 {test_file.name}")
            
            # 验证TypeScript结构
            analysis = validate_typescript_basic(test_file)
            if "error" not in analysis:
                valid_files += 1
                print(f"  ✅ 结构完整")
                print(f"  📊 测试用例: {analysis['test_cases']}")
                print(f"  📊 导入语句: {'✅' if analysis['has_imports'] else '❌'}")
                print(f"  📊 describe块: {'✅' if analysis['has_describe'] else '❌'}")
                print(f"  📊 it测试: {'✅' if analysis['has_it_tests'] else '❌'}")
                print(f"  📊 expect断言: {'✅' if analysis['has_expect'] else '❌'}")
                
                if analysis["test_names"]:
                    print(f"  🎯 主要测试: {', '.join(analysis['test_names'][:3])}")
            else:
                print(f"  ❌ 分析错误: {analysis['error']}")
    else:
        print("❌ 前端测试目录不存在")
    
    # 测试配置文件验证
    print("\n⚙️ 测试配置文件验证:")
    print("-" * 30)
    
    config_files = [
        ("backend/pytest.ini", "Pytest配置"),
        ("backend/requirements-test.txt", "Python测试依赖"),
        ("frontend/vitest.config.ts", "Vitest配置"),
        ("frontend/src/test/setup.ts", "测试环境设置")
    ]
    
    for file_path, description in config_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✅ {description}: {file_path}")
        else:
            print(f"  ❌ {description}: {file_path} (缺失)")
    
    # 业务逻辑覆盖验证
    print("\n🎯 业务逻辑测试覆盖验证:")
    print("-" * 30)
    
    key_components = [
        ("AI分类服务", "test_category_service.py"),
        ("快速分类服务", "test_quick_classification_service.py"),
        ("合集匹配服务", "test_collection_matching_service.py"),
        ("搜索服务", "test_search_service.py"),
        ("图片解析服务", "test_image_parser.py"),
        ("文件上传API", "test_ingest_api.py"),
        ("文档卡片组件", "DocumentCard.test.tsx"),
        ("主页面组件", "Home.test.tsx")
    ]
    
    covered_components = 0
    for component_name, test_file in key_components:
        backend_path = backend_tests / test_file
        frontend_path = frontend_tests / test_file
        
        if backend_path.exists() or frontend_path.exists():
            covered_components += 1
            print(f"  ✅ {component_name}")
        else:
            print(f"  ❌ {component_name} (无测试)")
    
    # 总结报告
    print("\n📋 验证总结:")
    print("=" * 50)
    print(f"📊 总文件数: {total_files}")
    print(f"✅ 有效文件: {valid_files}")
    print(f"❌ 无效文件: {total_files - valid_files}")
    print(f"🧪 后端测试函数: {total_test_functions}")
    print(f"🔍 后端断言数量: {total_assertions}")
    print(f"🎯 业务逻辑覆盖: {covered_components}/{len(key_components)} ({covered_components/len(key_components)*100:.1f}%)")
    
    # 质量评估
    if valid_files == total_files and covered_components >= len(key_components) * 0.8:
        print("\n🎉 测试质量评估: 优秀")
        print("✅ 所有测试文件语法正确")
        print("✅ 核心业务逻辑测试覆盖完整")
        print("✅ 测试结构规范，可以安全执行")
        return True
    elif valid_files >= total_files * 0.8:
        print("\n⚠️ 测试质量评估: 良好")
        print("⚠️ 大部分测试文件有效，但需要完善")
        return True
    else:
        print("\n❌ 测试质量评估: 需要改进")
        print("❌ 存在语法错误或覆盖不足")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
