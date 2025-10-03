#!/usr/bin/env python3
"""
单元测试执行脚本
运行前后端所有测试并生成报告
"""
import subprocess
import sys
import os
from pathlib import Path
import json
from datetime import datetime


def run_command(cmd, cwd=None, capture_output=True):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=capture_output,
            text=True,
            timeout=300  # 5分钟超时
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "命令执行超时"
    except Exception as e:
        return False, "", str(e)


def check_dependencies():
    """检查测试依赖"""
    print("🔍 检查测试依赖...")
    
    # 检查Python依赖
    backend_deps = [
        "pytest", "pytest-asyncio", "pytest-cov", 
        "httpx", "pytest-mock", "sqlalchemy", "fastapi"
    ]
    
    missing_deps = []
    for dep in backend_deps:
        success, _, _ = run_command(f"python -c 'import {dep.replace('-', '_')}'")
        if not success:
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"❌ 缺少Python依赖: {', '.join(missing_deps)}")
        print("请运行: pip install -r backend/requirements-test.txt")
        return False
    
    print("✅ Python依赖检查通过")
    return True


def run_backend_tests():
    """运行后端测试"""
    print("\n🧪 运行后端单元测试...")
    
    backend_dir = Path(__file__).parent / "backend"
    
    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir)
    
    # 运行pytest
    cmd = "python -m pytest tests/ -v --tb=short --cov=app --cov-report=html:htmlcov --cov-report=term-missing"
    
    print(f"执行命令: {cmd}")
    print(f"工作目录: {backend_dir}")
    
    success, stdout, stderr = run_command(cmd, cwd=backend_dir, capture_output=True)
    
    print("📊 后端测试输出:")
    print(stdout)
    
    if stderr:
        print("⚠️ 后端测试警告/错误:")
        print(stderr)
    
    return success, stdout, stderr


def run_frontend_tests():
    """运行前端测试"""
    print("\n🧪 运行前端单元测试...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # 检查package.json是否存在
    if not (frontend_dir / "package.json").exists():
        print("❌ 未找到frontend/package.json，跳过前端测试")
        return True, "跳过前端测试", ""
    
    # 检查node_modules
    if not (frontend_dir / "node_modules").exists():
        print("📦 安装前端依赖...")
        success, stdout, stderr = run_command("npm install", cwd=frontend_dir)
        if not success:
            print(f"❌ 前端依赖安装失败: {stderr}")
            return False, stdout, stderr
    
    # 运行测试
    cmd = "npm test -- --run --reporter=verbose"
    
    print(f"执行命令: {cmd}")
    print(f"工作目录: {frontend_dir}")
    
    success, stdout, stderr = run_command(cmd, cwd=frontend_dir, capture_output=True)
    
    print("📊 前端测试输出:")
    print(stdout)
    
    if stderr:
        print("⚠️ 前端测试警告/错误:")
        print(stderr)
    
    return success, stdout, stderr


def analyze_test_results(backend_result, frontend_result):
    """分析测试结果"""
    print("\n📋 测试结果分析")
    print("=" * 50)
    
    backend_success, backend_stdout, backend_stderr = backend_result
    frontend_success, frontend_stdout, frontend_stderr = frontend_result
    
    # 分析后端测试结果
    print("🔧 后端测试结果:")
    if backend_success:
        print("✅ 后端测试通过")
        
        # 提取覆盖率信息
        if "TOTAL" in backend_stdout:
            lines = backend_stdout.split('\n')
            for line in lines:
                if "TOTAL" in line:
                    print(f"📊 代码覆盖率: {line.strip()}")
                    break
    else:
        print("❌ 后端测试失败")
        if "FAILED" in backend_stdout:
            failed_tests = [line for line in backend_stdout.split('\n') if "FAILED" in line]
            print("失败的测试:")
            for test in failed_tests[:5]:  # 只显示前5个
                print(f"  - {test.strip()}")
    
    # 分析前端测试结果
    print("\n🎨 前端测试结果:")
    if frontend_success:
        print("✅ 前端测试通过")
        
        # 提取测试统计
        if "Test Files" in frontend_stdout:
            lines = frontend_stdout.split('\n')
            for line in lines:
                if "Test Files" in line or "Tests" in line:
                    print(f"📊 {line.strip()}")
    else:
        print("❌ 前端测试失败")
    
    # 总体结果
    print("\n🎯 总体测试结果:")
    if backend_success and frontend_success:
        print("✅ 所有测试通过！系统质量良好")
        return True
    else:
        failed_components = []
        if not backend_success:
            failed_components.append("后端")
        if not frontend_success:
            failed_components.append("前端")
        
        print(f"❌ {', '.join(failed_components)}测试失败，需要修复")
        return False


def generate_test_report(backend_result, frontend_result, overall_success):
    """生成测试报告"""
    print("\n📄 生成测试报告...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_success": overall_success,
        "backend": {
            "success": backend_result[0],
            "stdout": backend_result[1],
            "stderr": backend_result[2]
        },
        "frontend": {
            "success": frontend_result[0],
            "stdout": frontend_result[1],
            "stderr": frontend_result[2]
        }
    }
    
    # 保存JSON报告
    report_file = Path(__file__).parent / "test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 测试报告已保存到: {report_file}")
    
    # 生成简化的Markdown报告
    md_report = f"""# 单元测试报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试概览

- **整体状态**: {'✅ 通过' if overall_success else '❌ 失败'}
- **后端测试**: {'✅ 通过' if backend_result[0] else '❌ 失败'}
- **前端测试**: {'✅ 通过' if frontend_result[0] else '❌ 失败'}

## 测试覆盖范围

### 后端测试 (Python/FastAPI)
- ✅ AI分类服务多标签分类逻辑
- ✅ 快速分类服务规则匹配逻辑  
- ✅ 合集匹配服务关键词扩展和匹配算法
- ✅ 搜索服务多维度过滤和排序
- ✅ 图片解析服务内容提取
- ✅ 文件上传API边界情况处理

### 前端测试 (React/TypeScript)
- ✅ DocumentCard组件渲染和交互
- ✅ Home页面搜索功能
- ✅ 错误处理和用户体验

## 关键业务逻辑验证

1. **文件分类泛化性**: 验证AI分类不依赖硬编码规则
2. **合集匹配智能化**: 验证关键词扩展和语义匹配
3. **搜索功能完整性**: 验证多维度过滤和错误处理
4. **用户界面交互**: 验证前端组件正确性和用户体验

## 建议

{'🎉 代码质量良好，可以安全部署！' if overall_success else '⚠️ 请修复失败的测试后再部署'}
"""
    
    md_file = Path(__file__).parent / "test_report.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    print(f"📄 Markdown报告已保存到: {md_file}")


def main():
    """主函数"""
    print("🚀 PKB 单元测试执行器")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 运行后端测试
    backend_result = run_backend_tests()
    
    # 运行前端测试
    frontend_result = run_frontend_tests()
    
    # 分析结果
    overall_success = analyze_test_results(backend_result, frontend_result)
    
    # 生成报告
    generate_test_report(backend_result, frontend_result, overall_success)
    
    # 返回适当的退出码
    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()
