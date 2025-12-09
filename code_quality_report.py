"""
代码质量检查报告 - QA审查
"""

import ast
import re
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import os

class CodeQualityAnalyzer:
    """代码质量分析器"""
    
    def __init__(self):
        self.issues = defaultdict(list)
        self.metrics = {}
    
    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """分析单个文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析AST
            tree = ast.parse(content)
            
            # 分析代码质量
            self._analyze_imports(tree)
            self._analyze_functions(tree)
            self._analyze_classes(tree)
            self._analyze_complexity(tree)
            self._analyze_naming_conventions(tree)
            self._analyze_docstrings(tree)
            
            # 计算指标
            self._calculate_metrics(content, tree)
            
            return {
                'filepath': filepath,
                'issues': dict(self.issues),
                'metrics': self.metrics
            }
            
        except Exception as e:
            return {
                'filepath': filepath,
                'error': str(e),
                'issues': {},
                'metrics': {}
            }
    
    def _analyze_imports(self, tree: ast.AST):
        """分析导入语句"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        # 检查未使用的导入
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
        
        for imp in imports:
            if imp.split('.')[-1] not in used_names:
                self.issues['unused_imports'].append(imp)
    
    def _analyze_functions(self, tree: ast.AST):
        """分析函数"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 检查函数长度
                if node.end_lineno - node.lineno > 50:
                    self.issues['long_functions'].append({
                        'name': node.name,
                        'lines': node.end_lineno - node.lineno
                    })
                
                # 检查参数数量
                if len(node.args.args) > 5:
                    self.issues['too_many_parameters'].append({
                        'name': node.name,
                        'count': len(node.args.args)
                    })
                
                # 检查返回值类型注解
                if not node.returns:
                    self.issues['missing_return_type'].append(node.name)
    
    def _analyze_classes(self, tree: ast.AST):
        """分析类"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查类方法数量
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 10:
                    self.issues['large_classes'].append({
                        'name': node.name,
                        'methods': len(methods)
                    })
                
                # 检查是否有__init__方法
                has_init = any(m.name == '__init__' for m in methods)
                if not has_init and len(methods) > 0:
                    self.issues['missing_init'].append(node.name)
    
    def _analyze_complexity(self, tree: ast.AST):
        """分析代码复杂度"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    self.issues['high_complexity'].append({
                        'name': node.name,
                        'complexity': complexity
                    })
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _analyze_naming_conventions(self, tree: ast.AST):
        """分析命名规范"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    self.issues['naming_conventions'].append({
                        'type': 'function',
                        'name': node.name,
                        'issue': 'Should use snake_case'
                    })
            
            elif isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    self.issues['naming_conventions'].append({
                        'type': 'class',
                        'name': node.name,
                        'issue': 'Should use PascalCase'
                    })
            
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, str) and node.value.isupper():
                    if not re.match(r'^[A-Z_][A-Z0-9_]*$', node.value):
                        self.issues['naming_conventions'].append({
                            'type': 'constant',
                            'name': node.value,
                            'issue': 'Should use UPPER_CASE'
                        })
    
    def _analyze_docstrings(self, tree: ast.AST):
        """分析文档字符串"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    self.issues['missing_docstrings'].append({
                        'type': 'function' if isinstance(node, ast.FunctionDef) else 'class',
                        'name': node.name
                    })
    
    def _calculate_metrics(self, content: str, tree: ast.AST):
        """计算代码指标"""
        lines = content.split('\n')
        
        # 基本指标
        self.metrics['total_lines'] = len(lines)
        self.metrics['non_empty_lines'] = len([l for l in lines if l.strip()])
        self.metrics['comment_lines'] = len([l for l in lines if l.strip().startswith('#')])
        
        # 代码行数
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        self.metrics['code_lines'] = code_lines
        
        # 注释率
        if code_lines > 0:
            self.metrics['comment_ratio'] = self.metrics['comment_lines'] / code_lines
        else:
            self.metrics['comment_ratio'] = 0
        
        # 函数和类数量
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        
        self.metrics['function_count'] = len(functions)
        self.metrics['class_count'] = len(classes)
        
        # 平均函数长度
        if functions:
            total_function_lines = sum(f.end_lineno - f.lineno for f in functions)
            self.metrics['avg_function_length'] = total_function_lines / len(functions)
        else:
            self.metrics['avg_function_length'] = 0

def generate_quality_report(files: List[str]) -> Dict[str, Any]:
    """生成代码质量报告"""
    analyzer = CodeQualityAnalyzer()
    results = []
    
    for filepath in files:
        if filepath.endswith('.py'):
            result = analyzer.analyze_file(filepath)
            results.append(result)
    
    # 汇总报告
    total_issues = defaultdict(int)
    total_metrics = defaultdict(float)
    file_count = 0
    
    for result in results:
        if 'error' not in result:
            file_count += 1
            for issue_type, issues in result['issues'].items():
                total_issues[issue_type] += len(issues)
            
            for metric, value in result['metrics'].items():
                if isinstance(value, (int, float)):
                    total_metrics[metric] += value
    
    # 计算平均值
    for metric in total_metrics:
        if file_count > 0:
            total_metrics[metric] = total_metrics[metric] / file_count
    
    return {
        'summary': {
            'files_analyzed': file_count,
            'total_issues': sum(total_issues.values()),
            'issue_breakdown': dict(total_issues),
            'average_metrics': dict(total_metrics)
        },
        'file_details': results
    }

# 代码质量建议
QUALITY_RECOMMENDATIONS = {
    "高优先级": [
        "添加类型注解提升代码可读性",
        "为所有公共函数添加文档字符串",
        "减少函数复杂度，拆分大型函数",
        "移除未使用的导入语句"
    ],
    "中优先级": [
        "遵循PEP 8命名规范",
        "添加单元测试覆盖核心功能",
        "使用常量替代魔法数字",
        "改进错误处理和异常管理"
    ],
    "低优先级": [
        "添加代码注释解释复杂逻辑",
        "使用枚举替代字符串常量",
        "实现设计模式提升代码结构",
        "添加性能监控和日志记录"
    ]
}

def main():
    """主函数"""
    # 分析项目文件
    files_to_analyze = [
        'complete_project_system.py',
        'unified_quant_system.py',
        'security_fixes.py',
        'performance_analysis.py'
    ]
    
    # 过滤存在的文件
    existing_files = [f for f in files_to_analyze if os.path.exists(f)]
    
    if not existing_files:
        print("没有找到要分析的文件")
        return
    
    print("🔍 开始代码质量分析...")
    print("=" * 50)
    
    report = generate_quality_report(existing_files)
    
    # 输出摘要
    summary = report['summary']
    print(f"\n📊 分析摘要:")
    print(f"  分析文件数: {summary['files_analyzed']}")
    print(f"  总问题数: {summary['total_issues']}")
    
    print(f"\n📋 问题分类:")
    for issue_type, count in summary['issue_breakdown'].items():
        print(f"  {issue_type}: {count}")
    
    print(f"\n📈 代码指标:")
    for metric, value in summary['average_metrics'].items():
        if isinstance(value, float):
            print(f"  {metric}: {value:.2f}")
        else:
            print(f"  {metric}: {value}")
    
    # 输出详细问题
    print(f"\n🔍 详细问题:")
    for file_result in report['file_details']:
        if 'error' in file_result:
            print(f"\n❌ {file_result['filepath']}: {file_result['error']}")
            continue
        
        filepath = file_result['filepath']
        issues = file_result['issues']
        
        if not any(issues.values()):
            print(f"\n✅ {filepath}: 无问题")
            continue
        
        print(f"\n📄 {filepath}:")
        for issue_type, issue_list in issues.items():
            if issue_list:
                print(f"  {issue_type}:")
                for issue in issue_list[:5]:  # 只显示前5个
                    if isinstance(issue, dict):
                        print(f"    - {issue}")
                    else:
                        print(f"    - {issue}")
                if len(issue_list) > 5:
                    print(f"    ... 还有 {len(issue_list) - 5} 个问题")
    
    # 输出建议
    print(f"\n💡 代码质量改进建议:")
    print("=" * 50)
    for priority, recommendations in QUALITY_RECOMMENDATIONS.items():
        print(f"\n{priority}:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

if __name__ == "__main__":
    main()
