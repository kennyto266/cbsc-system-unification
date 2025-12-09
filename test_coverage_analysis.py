"""
测试覆盖率分析 - QA审查 (修复版)
"""

import os
import ast
from typing import Dict, List, Any, Set
from collections import defaultdict

class TestCoverageAnalyzer:
    """测试覆盖率分析器"""
    
    def __init__(self):
        self.source_files = []
        self.test_files = []
        self.coverage_data = {}
    
    def find_source_files(self, directory: str = ".") -> List[str]:
        """查找源代码文件"""
        source_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    filepath = os.path.join(root, file)
                    source_files.append(filepath)
        return source_files
    
    def find_test_files(self, directory: str = ".") -> List[str]:
        """查找测试文件"""
        test_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    test_files.append(filepath)
        return test_files
    
    def analyze_function_coverage(self, source_file: str) -> Dict[str, Any]:
        """分析函数覆盖率"""
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 提取所有函数
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'is_public': not node.name.startswith('_'),
                        'has_docstring': ast.get_docstring(node) is not None
                    })
            
            # 检查是否有对应的测试
            test_coverage = {}
            for func in functions:
                func_name = func['name']
                has_test = self._check_function_has_test(func_name, source_file)
                test_coverage[func_name] = {
                    'has_test': has_test,
                    'is_public': func['is_public'],
                    'line': func['line'],
                    'has_docstring': func['has_docstring']
                }
            
            return {
                'file': source_file,
                'total_functions': len(functions),
                'public_functions': len([f for f in functions if f['is_public']]),
                'tested_functions': len([f for f in test_coverage.values() if f['has_test']]),
                'coverage_details': test_coverage
            }
            
        except Exception as e:
            return {
                'file': source_file,
                'error': str(e),
                'total_functions': 0,
                'public_functions': 0,
                'tested_functions': 0,
                'coverage_details': {}
            }
    
    def _check_function_has_test(self, func_name: str, source_file: str) -> bool:
        """检查函数是否有对应的测试"""
        # 查找可能的测试文件
        test_files = self.find_test_files()
        
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否包含函数名的测试
                if func_name in content:
                    return True
                    
            except Exception:
                continue
        
        return False
    
    def analyze_api_coverage(self, source_file: str) -> Dict[str, Any]:
        """分析API端点覆盖率"""
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 查找FastAPI路由
            api_endpoints = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 检查是否有路由装饰器
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Attribute):
                                if decorator.func.attr in ['get', 'post', 'put', 'delete']:
                                    # 提取路径
                                    if decorator.args:
                                        path = decorator.args[0].s if isinstance(decorator.args[0], ast.Constant) else str(decorator.args[0])
                                        api_endpoints.append({
                                            'method': decorator.func.attr.upper(),
                                            'path': path,
                                            'function': node.name,
                                            'line': node.lineno
                                        })
            
            # 检查API测试覆盖率
            test_coverage = {}
            for endpoint in api_endpoints:
                has_test = self._check_api_has_test(endpoint['path'], endpoint['method'])
                test_coverage[f"{endpoint['method']} {endpoint['path']}"] = {
                    'has_test': has_test,
                    'function': endpoint['function'],
                    'line': endpoint['line']
                }
            
            return {
                'file': source_file,
                'total_endpoints': len(api_endpoints),
                'tested_endpoints': len([e for e in test_coverage.values() if e['has_test']]),
                'coverage_details': test_coverage
            }
            
        except Exception as e:
            return {
                'file': source_file,
                'error': str(e),
                'total_endpoints': 0,
                'tested_endpoints': 0,
                'coverage_details': {}
            }
    
    def _check_api_has_test(self, path: str, method: str) -> bool:
        """检查API端点是否有测试"""
        test_files = self.find_test_files()
        
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否包含路径和方法的测试
                if path in content and method.lower() in content.lower():
                    return True
                    
            except Exception:
                continue
        
        return False
    
    def generate_coverage_report(self) -> Dict[str, Any]:
        """生成覆盖率报告"""
        source_files = self.find_source_files()
        test_files = self.find_test_files()
        
        print(f"📊 发现 {len(source_files)} 个源代码文件")
        print(f"🧪 发现 {len(test_files)} 个测试文件")
        
        # 分析函数覆盖率
        function_coverage = []
        for source_file in source_files:
            if 'complete_project_system.py' in source_file or 'unified_quant_system.py' in source_file:
                coverage = self.analyze_function_coverage(source_file)
                function_coverage.append(coverage)
        
        # 分析API覆盖率
        api_coverage = []
        for source_file in source_files:
            if 'complete_project_system.py' in source_file or 'unified_quant_system.py' in source_file:
                coverage = self.analyze_api_coverage(source_file)
                api_coverage.append(coverage)
        
        # 计算总体覆盖率
        total_functions = sum(c['total_functions'] for c in function_coverage)
        tested_functions = sum(c['tested_functions'] for c in function_coverage)
        function_coverage_rate = (tested_functions / total_functions * 100) if total_functions > 0 else 0
        
        total_endpoints = sum(c['total_endpoints'] for c in api_coverage)
        tested_endpoints = sum(c['tested_endpoints'] for c in api_coverage)
        api_coverage_rate = (tested_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
        
        return {
            'summary': {
                'source_files': len(source_files),
                'test_files': len(test_files),
                'total_functions': total_functions,
                'tested_functions': tested_functions,
                'function_coverage_rate': function_coverage_rate,
                'total_endpoints': total_endpoints,
                'tested_endpoints': tested_endpoints,
                'api_coverage_rate': api_coverage_rate
            },
            'function_coverage': function_coverage,
            'api_coverage': api_coverage
        }

def main():
    """主函数"""
    analyzer = TestCoverageAnalyzer()
    
    print("🔍 开始测试覆盖率分析...")
    print("=" * 50)
    
    report = analyzer.generate_coverage_report()
    
    # 输出报告
    summary = report['summary']
    print(f"\n📊 测试覆盖率摘要:")
    print(f"  源代码文件: {summary['source_files']}")
    print(f"  测试文件: {summary['test_files']}")
    print(f"  函数总数: {summary['total_functions']}")
    print(f"  已测试函数: {summary['tested_functions']}")
    print(f"  函数覆盖率: {summary['function_coverage_rate']:.1f}%")
    print(f"  API端点总数: {summary['total_endpoints']}")
    print(f"  已测试API: {summary['tested_endpoints']}")
    print(f"  API覆盖率: {summary['api_coverage_rate']:.1f}%")
    
    # 输出详细覆盖率
    print(f"\n📋 详细覆盖率:")
    for coverage in report['function_coverage']:
        if 'error' not in coverage:
            print(f"\n📄 {coverage['file']}:")
            print(f"  总函数数: {coverage['total_functions']}")
            print(f"  公共函数: {coverage['public_functions']}")
            print(f"  已测试函数: {coverage['tested_functions']}")
            
            # 显示未测试的函数
            untested = [name for name, details in coverage['coverage_details'].items() 
                       if not details['has_test'] and details['is_public']]
            if untested:
                print(f"  未测试的公共函数: {', '.join(untested[:5])}")
                if len(untested) > 5:
                    print(f"    ... 还有 {len(untested) - 5} 个")
    
    for coverage in report['api_coverage']:
        if 'error' not in coverage:
            print(f"\n🌐 {coverage['file']} API:")
            print(f"  总端点数: {coverage['total_endpoints']}")
            print(f"  已测试端点: {coverage['tested_endpoints']}")
            
            # 显示未测试的API
            untested = [endpoint for endpoint, details in coverage['coverage_details'].items() 
                       if not details['has_test']]
            if untested:
                print(f"  未测试的API: {', '.join(untested[:3])}")
                if len(untested) > 3:
                    print(f"    ... 还有 {len(untested) - 3} 个")
    
    # 测试建议
    print(f"\n💡 测试改进建议:")
    print("=" * 50)
    
    if summary['function_coverage_rate'] < 50:
        print("🔴 函数覆盖率过低，建议:")
        print("  1. 为核心业务逻辑函数添加单元测试")
        print("  2. 为技术分析函数添加测试用例")
        print("  3. 为数据处理函数添加边界测试")
    
    if summary['api_coverage_rate'] < 50:
        print("🔴 API覆盖率过低，建议:")
        print("  1. 为所有API端点添加集成测试")
        print("  2. 测试各种输入参数组合")
        print("  3. 测试错误处理和异常情况")
    
    if summary['test_files'] == 0:
        print("🔴 缺少测试文件，建议:")
        print("  1. 创建 test_main.py 测试主要功能")
        print("  2. 创建 test_api.py 测试API端点")
        print("  3. 创建 test_analysis.py 测试分析功能")
    
    print(f"\n📈 总体测试质量评分: {int((summary['function_coverage_rate'] + summary['api_coverage_rate']) / 2)}/100")

if __name__ == "__main__":
    main()