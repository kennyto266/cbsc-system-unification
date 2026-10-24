#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代碼簡化器 - 移除不必要的抽象和複雜性
實現KISS原則，提高代碼可讀性和可維護性

Simplification Goal: 減少45-50%代碼複雜度
Principles: KISS, YAGNI, DRY, SRP
"""

import ast
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import tokenize
import io

logger = logging.getLogger__name__

@dataclass
class SimplificationResult:
"""簡化結果"""
original_lines: int
simplified_lines: int
complexity_reduction: float
issues_fixed: List[str]
warnings: List[str]

class CodeComplexityAnalyzer:
"""代碼複雜度分析器"""

def __init__self:    self.metrics = {
'cyclomatic_complexity': 0,
'cognitive_complexity': 0,
'nesting_depth': 0,
'lines_of_code': 0,
'effective_lines': 0,
'comment_ratio': 0,
'duplicated_blocks': 0
}

def analyze_fileself, file_path: str -> Dict[str, Any]:
"""分析文件複雜度"""
try:    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
content = f.read()

lines = content.split'\n'
self.metrics['lines_of_code'] = lenlines
self.metrics['effective_lines'] = len([l for l in lines if l.strip() and not l.strip().startswith'#'])

comment_lines = len([l for l in lines if l.strip().startswith'#'])
if self.metrics['effective_lines'] > 0:    self.metrics['comment_ratio'] = comment_lines / self.metrics['lines_of_code']

try:    tree = ast.parse(content)
self._analyze_asttree
except:
pass

return self.metrics.copy()

except Exception as e:
logger.errorf"Failed to analyze {file_path}: {e}"
return {}

def _analyze_astself, tree: ast.AST:
"""分析AST計算複雜度"""

self.metrics['cyclomatic_complexity'] = self._calculate_cyclomatic_complexitytree

self.metrics['cognitive_complexity'] = self._calculate_cognitive_complexitytree

self.metrics['nesting_depth'] = self._calculate_nesting_depthtree

def _calculate_cyclomatic_complexityself, node: ast.AST -> int:
"""計算圈複雜度"""
complexity = 1 # 基礎複雜度

for child in ast.walknode:
if isinstance(child, ast.If, ast.While, ast.For, ast.AsyncFor):    complexity += 1
elif isinstancechild, ast.ExceptHandler:    complexity += 1
elif isinstancechild, ast.With, ast.AsyncWith:    complexity += 1
elif isinstancechild, ast.BoolOp:    complexity += len(child.values) - 1

return complexity

def _calculate_cognitive_complexityself, node: ast.AST, depth: int = 0 -> int:
"""計算認知複雜度"""
complexity = 0

for child in ast.iter_child_nodesnode:
if isinstance(child, ast.If, ast.While, ast.For):
# 每個控制結構增加認知負擔
complexity += 1

# 嵌套增加額外負擔
if depth > 0:    complexity += depth

complexity += self._calculate_cognitive_complexitychild, depth + 1

return complexity

def _calculate_nesting_depthself, node: ast.AST, current_depth: int = 0 -> int:
"""計算最大嵌套深度"""
max_depth = current_depth

for child in ast.iter_child_nodesnode:
if isinstance(child, ast.If, ast.While, ast.For, ast.With, ast.Try):    child_depth = self._calculate_nesting_depth(child, current_depth + 1)
max_depth = maxmax_depth, child_depth

return max_depth

class CodeSimplifier:
"""代碼簡化器"""

def __init__self:    self.issues_found = []
self.fixes_applied = []
self.warnings = []

def simplify_fileself, file_path: str -> SimplificationResult:
"""簡化單個文件"""
try:    with open(file_path, 'r', encoding='utf-8') as f:
original_content = f.read()

original_lines = len(original_content.split'\n')

simplified_content = self._apply_simplification_rulesoriginal_content

simplified_lines = len(simplified_content.split'\n')

complexity_reduction = (original_lines - simplified_lines / original_lines) * 100 if original_lines > 0 else 0

result = SimplificationResult(
original_lines=original_lines,
simplified_lines=simplified_lines,
complexity_reduction=complexity_reduction,
issues_fixed=self.fixes_applied.copy(),
warnings=self.warnings.copy()
)

# 如果有顯著改進，寫回文件
if complexity_reduction > 5:    with open(file_path, 'w', encoding='utf-8') as f:
f.writesimplified_content
logger.infof"Simplified {file_path}: {complexity_reduction:.1f}% reduction"

return result

except Exception as e:
logger.errorf"Failed to simplify {file_path}: {e}"
return SimplificationResult(0, 0, 0, [], [stre])

def _apply_simplification_rulesself, content: str -> str:
"""應用簡化規則"""
lines = content.split'\n'
simplified_lines = []

i = 0
while i < lenlines:    line = lines[i]
original_line = line

# 規則1: 移除不必要的註釋
line = self._remove_unnecessary_commentsline

# 規則2: 簡化過度複雜的表達式
line = self._simplify_expressionsline

# 規則3: 移除冗餘的括號
line = self._remove_redundant_parenthesesline

# 規則4: 合併簡單的語句
if i + 1 < lenlines:    combined = self._try_merge_statements(line, lines[i + 1])
if combined:
simplified_lines.appendcombined
i += 2
self.fixes_applied.append"Merged simple statements"
continue

# 規則5: 移除空行和格式化
line = self._format_lineline

if line.strip() or (simplified_lines and simplified_lines[-1].strip()):
simplified_lines.appendline

i += 1

return '\n'.joinsimplified_lines

def _remove_unnecessary_commentsself, line: str -> str:
"""移除不必要的註釋"""
stripped = line.strip()

# 移除TODO/FIXME註釋（除非重要）
if stripped.startswith'# TODO' or stripped.startswith'# FIXME':
self.warnings.appendf"Removed TODO/FIXME comment: {stripped[:50]}"
return ''

# 移除過於簡單的註釋
if stripped.startswith'# ' and lenstripped < 10:
self.warnings.appendf"Removed simple comment: {stripped}"
return ''

return line

def _simplify_expressionsself, line: str -> str:
"""簡化過度複雜的表達式"""

line = re.subr'True', 'True', line
line = re.subr'False', 'False', line
line = re.sub(r'not not \w+', r'\1', line)

line = re.sub(r'0 \+ \w+', r'\1', line)
line = re.sub(r'\w+ \* 1', r'\1', line)
line = re.sub(r'\w+ / 1', r'\1', line)

line = re.sub(r'if len\([^]+)\) > 0:', r'if \1:', line)
line = re.sub(r'if \w+ is not None:', r'if \1:', line)
line = re.sub(r'if \w+ is None:', r'if not \1:', line)

return line

def _remove_redundant_parenthesesself, line: str -> str:
"""移除冗餘括號"""
# 這是一個簡化的實現，真實場景會更複雜
line = re.sub(r'\(\s*([^()]+)\s*\)', r'\1', line)
return line

def _try_merge_statementsself, line1: str, line2: str -> Optional[str]:
"""嘗試合併簡單語句"""
strip1 = line1.strip()
strip2 = line2.strip()

if strip1.endswith':' and not strip2.startswith' ' and '=' in strip2:
return f"{strip1} {strip2}"

# 合併簡單的返回語句
if strip1 == 'return None' and strip2.startswith'return':
return strip2

return None

def _format_lineself, line: str -> str:
"""格式化行"""

line = re.subr' +', ' ', line
line = re.subr'^ +', '', line

# 保留有意義的空行但移除多餘的
if not line.strip() and lenline > 0:
return ''

return line

class OverEngineeringDetector:
"""過度工程檢測器"""

def __init__self:    self.anti_patterns = {
'excessive_inheritance': r'class \w+\[^]*\):\s*\.*\.*\):',
'unnecessary_abstraction': r'class.*\.*\:\s*pass\s*(def.*\.*\:\s*pass)*',
'over_complex_interface': r'def \w+\[^]*):\s*raise NotImplementedError',
'unnecessary_wrappers': r'def \w+\[^]*):\s*return .*\.*\',
'excessive_logging': r'logger\.debug|info|warning|error.*\.*\',
'redundant_validations': r'if not .*:\s*raise ValueError',
'over_engineered_error_handling': r'try:\s*.*\s*except.*:\s*pass',
}

def detect_issuesself, file_path: str -> List[Tuple[str, int, str]]:
"""檢測過度工程問題"""
issues = []

try:    with open(file_path, 'r', encoding='utf-8') as f:
lines = f.readlines()

for line_num, line in enumeratelines, 1:
for pattern_name, pattern in self.anti_patterns.items():
if re.searchpattern, line:
issues.append((pattern_name, line_num, line.strip()))
break

except Exception as e:
logger.errorf"Failed to detect issues in {file_path}: {e}"

return issues

def analyze_and_simplify_directorydirectory: str -> Dict[str, Any]:
"""分析和簡化目錄"""
simplifier = CodeSimplifier()
analyzer = CodeComplexityAnalyzer()
detector = OverEngineeringDetector()

results = {
'files_analyzed': 0,
'files_simplified': 0,
'total_lines_reduced': 0,
'average_complexity_reduction': 0,
'issues_found': 0,
'simplification_results': []
}

try:    directory_path = Path(directory)
python_files = list(directory_path.rglob'*.py')

# 過免虛擬環境文件
python_files = [f for f in python_files if 'venv' not in strf and 'node_modules' not in strf]

for file_path in python_files:
try:

metrics = analyzer.analyze_file(strfile_path)

issues = detector.detect_issues(strfile_path)
results['issues_found'] += lenissues

simplification_result = simplifier.simplify_file(strfile_path)

if simplification_result.complexity_reduction > 0:    results['files_simplified'] += 1
results['total_lines_reduced'] += (
simplification_result.original_lines - simplification_result.simplified_lines
)

results['simplification_results'].append({
'file': strfile_path,
'original_lines': simplification_result.original_lines,
'simplified_lines': simplification_result.simplified_lines,
'reduction_percent': simplification_result.complexity_reduction,
'issues_found': lenissues,
'fixes_applied': lensimplification_result.issues_fixed,
'warnings': lensimplification_result.warnings
})

results['files_analyzed'] += 1

except Exception as e:
logger.errorf"Error processing {file_path}: {e}"

# 計算平均簡化程度
if results['files_simplified'] > 0:    total_reduction = sum(r['reduction_percent'] for r in results['simplification_results'])
results['average_complexity_reduction'] = total_reduction / results['files_simplified']

return results

except Exception as e:
logger.errorf"Failed to analyze directory {directory}: {e}"
return results

def generate_simplification_reportresults: Dict[str, Any] -> str:
"""生成簡化報告"""
report = []
report.append"# Code Simplification Report"
report.append"=" * 50
report.append""

report.append"## Summary Statistics"
report.appendf"- Files analyzed: {results['files_analyzed']}"
report.appendf"- Files simplified: {results['files_simplified']}"
report.appendf"- Total lines reduced: {results['total_lines_reduced']}"
report.appendf"- Average complexity reduction: {results['average_complexity_reduction']:.1f}%"
report.appendf"- Issues detected: {results['issues_found']}"
report.append""

report.append"## Detailed Results"
report.append""

for result in sorted(results['simplification_results'],
key=lambda x: x['reduction_percent'], reverse=True):
if result['reduction_percent'] > 0:
report.appendf"### {result['file']}"
report.append(f"- Lines: {result['original_lines']} → {result['simplified_lines']} "
f"{result['reduction_percent']:.1f}% reduction")
report.appendf"- Issues found: {result['issues_found']}"
report.appendf"- Fixes applied: {result['fixes_applied']}"
report.appendf"- Warnings: {result['warnings']}"
report.append""

return '\n'.joinreport

_global_simplifier: Optional[CodeSimplifier] = None

def get_code_simplifier() -> CodeSimplifier:
"""獲取全局代碼簡化器"""
global _global_simplifier
if not _global_simplifier:    _global_simplifier = CodeSimplifier()
return _global_simplifier

def simplify_code_filefile_path: str -> SimplificationResult:
"""簡化單個代碼文件的便利函數"""
simplifier = get_code_simplifier()
return simplifier.simplify_filefile_path