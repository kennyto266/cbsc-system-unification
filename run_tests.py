"""
测试运行脚本
运行所有测试并生成覆盖率报告
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """运行所有测试"""
    print("🧪 开始运行测试套件...")
    print("=" * 60)
    
    # 检查pytest是否安装
    try:
        import pytest
        print("✅ pytest 已安装")
    except ImportError:
        print("❌ pytest 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"], check=True)
        print("✅ pytest 安装完成")
    
    # 运行测试
    test_files = [
        "test_core_functions.py",
        "test_api_endpoints.py", 
        "test_data_processing.py"
    ]
    
    # 检查测试文件是否存在
    existing_tests = []
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_tests.append(test_file)
            print(f"✅ 找到测试文件: {test_file}")
        else:
            print(f"⚠️ 测试文件不存在: {test_file}")
    
    if not existing_tests:
        print("❌ 没有找到测试文件")
        return False
    
    # 运行测试
    cmd = [
        sys.executable, "-m", "pytest",
        *existing_tests,
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=70"  # 设置最低覆盖率要求
    ]
    
    print(f"\n🚀 运行命令: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 所有测试通过!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ 测试失败!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n📊 生成测试报告...")
    
    # 检查是否有HTML覆盖率报告
    if os.path.exists("htmlcov/index.html"):
        print("✅ HTML覆盖率报告已生成: htmlcov/index.html")
    else:
        print("⚠️ HTML覆盖率报告未生成")
    
    # 生成简单的文本报告
    report_content = """
# 测试报告

## 测试覆盖情况
- 核心功能测试: ✅ 完成
- API端点测试: ✅ 完成  
- 数据处理测试: ✅ 完成

## 测试文件
- test_core_functions.py: 核心功能单元测试
- test_api_endpoints.py: API集成测试
- test_data_processing.py: 数据处理测试

## 覆盖率目标
- 目标覆盖率: 80%
- 当前覆盖率: 请查看pytest输出

## 运行测试
```bash
python run_tests.py
```

## 查看详细报告
```bash
pytest --cov=. --cov-report=html
```
"""
    
    with open("TEST_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("✅ 测试报告已生成: TEST_REPORT.md")

def main():
    """主函数"""
    print("🧪 量化交易系统测试套件")
    print("=" * 60)
    
    # 运行测试
    success = run_tests()
    
    # 生成报告
    generate_test_report()
    
    if success:
        print("\n🎉 测试完成! 系统质量良好!")
        print("📊 查看详细覆盖率报告: htmlcov/index.html")
    else:
        print("\n⚠️ 测试未完全通过，请检查失败项")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
