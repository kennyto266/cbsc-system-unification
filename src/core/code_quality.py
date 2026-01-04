#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Quality Analysis Module
代碼質量分析模塊

Provides:
- Cyclomatic complexity analysis
- Maintainability index calculation
- Code duplication detection
- Quality gate enforcement
"""

import ast
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Complexity Analysis
# ============================================================================

@dataclass
class ComplexityMetrics:
    """Complexity metrics for a function"""
    name: str
    lineno: int
    complexity: int
    nested: bool = False


@dataclass
class FileMetrics:
    """Metrics for a source file"""
    path: str
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    functions: List[ComplexityMetrics] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)

    @property
    def average_complexity(self) -> float:
        """Calculate average cyclomatic complexity"""
        if not self.functions:
            return 0.0
        return sum(f.complexity for f in self.functions) / len(self.functions)

    @property
    def max_complexity(self) -> int:
        """Get maximum complexity"""
        if not self.functions:
            return 0
        return max(f.complexity for f in self.functions)

    @property
    def high_complexity_functions(self) -> List[ComplexityMetrics]:
        """Get functions with complexity > 10"""
        return [f for f in self.functions if f.complexity > 10]


class ComplexityAnalyzer(ast.NodeVisitor):
    """
    AST-based complexity analyzer
    基於 AST 的複雜度分析器

    Calculates cyclomatic complexity using the standard formula:
    CC = E - N + 2P
    Where E = edges, N = nodes, P = connected components

    Simplified: Count decision points + 1
    """

    def __init__(self, source: str):
        self.source = source
        self.complexities: List[ComplexityMetrics] = []
        self._class_stack: List[str] = []
        self._function_stack: List[str] = []

    def analyze(self) -> List[ComplexityMetrics]:
        """Analyze source code complexity"""
        try:
            tree = ast.parse(self.source)
            self.visit(tree)
        except SyntaxError as e:
            logger.error(f"Syntax error in source: {e}")

        return self.complexities

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate complexity for a node"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Decision points that increase complexity
            if isinstance(child, (
                ast.If, ast.While, ast.For, ast.AsyncFor,
                ast.ExceptHandler, ast.With, ast.AsyncWith
            )):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.ListComp):
                complexity += 1
            elif isinstance(child, (ast.DictComp, ast.SetComp)):
                complexity += 1
            elif isinstance(child, ast.GeneratorExp):
                complexity += 1
            elif isinstance(child, ast.Lambda):
                complexity += 1
            elif isinstance(child, ast.Try):
                # Each except handler adds complexity
                complexity += len(child.handlers) if hasattr(child, 'handlers') else 0

        return complexity

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition"""
        full_name = node.name
        if self._class_stack:
            full_name = f"{self._class_stack[-1]}.{node.name}"

        complexity = self._calculate_complexity(node)

        self.complexities.append(ComplexityMetrics(
            name=full_name,
            lineno=node.lineno,
            complexity=complexity,
            nested=bool(self._function_stack)
        ))

        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition"""
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition"""
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()


# ============================================================================
# Maintainability Analysis
# ============================================================================

@dataclass
class MaintainabilityMetrics:
    """Maintainability index metrics"""
    file: str
    mi_score: float = 0.0
    grade: str = "F"
    comments_ratio: float = 0.0
    avg_complexity: float = 0.0
    avg_function_length: float = 0.0


class MaintainabilityAnalyzer:
    """
    Maintainability index calculator
    可維護性指數計算器

    Based on the Microsoft Maintainability Index:
    MI = MAX(0, (171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)) * 100 / 171)

    Where:
    - HV = Halstead Volume
    - CC = Cyclomatic Complexity
    - LOC = Lines of Code
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'max_complexity': 10,
            'max_function_length': 50,
            'min_comments_ratio': 0.15,
        }

    def analyze(self, file_metrics: FileMetrics) -> MaintainabilityMetrics:
        """Calculate maintainability index"""
        # Calculate components
        loc = file_metrics.code_lines
        cc = file_metrics.average_complexity

        # Calculate comments ratio
        total = file_metrics.total_lines
        comments_ratio = file_metrics.comment_lines / total if total > 0 else 0

        # Calculate average function length
        if file_metrics.functions:
            avg_func_len = loc / len(file_metrics.functions)
        else:
            avg_func_len = 0

        # Simplified MI calculation (without Halstead Volume)
        # MI = 171 - 5.2 * ln(CC) - 0.23 * CC - 16.2 * ln(LOC)
        import math

        if loc > 0 and cc > 0:
            mi = 171 - 5.2 * math.log(max(cc, 1)) - 0.23 * cc - 16.2 * math.log(loc)
            mi = max(0, min(100, mi))
        else:
            mi = 100

        # Normalize to 0-100 scale
        mi_score = (mi / 171) * 100

        return MaintainabilityMetrics(
            file=file_metrics.path,
            mi_score=mi_score,
            grade=self._get_grade(mi_score),
            comments_ratio=comments_ratio,
            avg_complexity=cc,
            avg_function_length=avg_func_len
        )

    def _get_grade(self, mi_score: float) -> str:
        """Get maintainability grade from score"""
        if mi_score >= 85:
            return 'A'
        elif mi_score >= 70:
            return 'B'
        elif mi_score >= 50:
            return 'C'
        else:
            return 'D'


# ============================================================================
# Code Duplication Detection
# ============================================================================

@dataclass
class DuplicateBlock:
    """Duplicate code block"""
    file1: str
    start1: int
    end1: int
    file2: str
    start2: int
    end2: int
    lines: int
    content: str


class DuplicationDetector:
    """
    Code duplication detector
    代碼重複檢測器

    Uses token-based similarity to find duplicate blocks
    """

    def __init__(self, min_lines: int = 5, min_similarity: float = 0.8):
        self.min_lines = min_lines
        self.min_similarity = min_similarity

    def _normalize_line(self, line: str) -> str:
        """Normalize line for comparison"""
        # Remove comments
        line = re.sub(r'#.*$', '', line)
        # Remove string literals
        line = re.sub(r'["\'].*?["\']', '""', line)
        # Remove numbers
        line = re.sub(r'\b\d+\b', '0', line)
        # Normalize whitespace
        line = ' '.join(line.split())
        return line.strip()

    def _get_tokens(self, lines: List[str]) -> List[str]:
        """Get normalized tokens from lines"""
        return [self._normalize_line(line) for line in lines if line.strip()]

    def find_duplicates(self, files: List[str]) -> List[DuplicateBlock]:
        """Find duplicate code blocks across files"""
        duplicates = []
        file_contents: Dict[str, List[str]] = {}

        # Read all files
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_contents[file_path] = f.readlines()
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")

        # Compare each pair of files
        file_list = list(file_contents.keys())
        for i, file1 in enumerate(file_list):
            for file2 in file_list[i + 1:]:
                duplicates.extend(
                    self._compare_files(
                        file1, file_contents[file1],
                        file2, file_contents[file2]
                    )
                )

        return duplicates

    def _compare_files(
        self,
        file1: str,
        lines1: List[str],
        file2: str,
        lines2: List[str]
    ) -> List[DuplicateBlock]:
        """Compare two files for duplicates"""
        duplicates = []
        tokens1 = self._get_tokens(lines1)
        tokens2 = self._get_tokens(lines2)

        # Find matching blocks
        for i in range(len(tokens1) - self.min_lines):
            for j in range(len(tokens2) - self.min_lines):
                # Compare blocks
                match_length = self._find_match_length(
                    tokens1, i, tokens2, j
                )

                if match_length >= self.min_lines:
                    similarity = self._calculate_similarity(
                        tokens1, i, i + match_length,
                        tokens2, j, j + match_length
                    )

                    if similarity >= self.min_similarity:
                        duplicates.append(DuplicateBlock(
                            file1=file1,
                            start1=i + 1,
                            end1=i + match_length,
                            file2=file2,
                            start2=j + 1,
                            end2=j + match_length,
                            lines=match_length,
                            content=''.join(lines1[i:i + match_length])
                        ))

        return duplicates

    def _find_match_length(
        self,
        tokens1: List[str], start1: int,
        tokens2: List[str], start2: int
    ) -> int:
        """Find length of matching block"""
        length = 0
        max_len = min(len(tokens1) - start1, len(tokens2) - start2)

        while length < max_len and tokens1[start1 + length] == tokens2[start2 + length]:
            length += 1

        return length

    def _calculate_similarity(
        self,
        tokens1: List[str], start1: int, end1: int,
        tokens2: List[str], start2: int, end2: int
    ) -> float:
        """Calculate similarity between two blocks"""
        block1 = tokens1[start1:end1]
        block2 = tokens2[start2:end2]

        if not block1 or not block2:
            return 0.0

        # Simple token matching
        matches = sum(1 for a, b in zip(block1, block2) if a == b)
        return matches / max(len(block1), len(block2))


# ============================================================================
# Code Quality Checker
# ============================================================================

@dataclass
class QualityIssue:
    """Code quality issue"""
    file: str
    line: int
    type: str  # 'complexity', 'duplication', 'style', 'maintainability'
    severity: str  # 'error', 'warning', 'info'
    message: str


@dataclass
class QualityReport:
    """Code quality report"""
    total_files: int = 0
    passed_files: int = 0
    failed_files: int = 0
    total_issues: int = 0
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    average_complexity: float = 0.0
    average_maintainability: float = 0.0
    issues: List[QualityIssue] = field(default_factory=list)

    def add_issue(self, issue: QualityIssue) -> None:
        """Add an issue to the report"""
        self.issues.append(issue)
        self.total_issues += 1

        # Update counters
        self.issues_by_type[issue.type] = self.issues_by_type.get(issue.type, 0) + 1
        self.issues_by_severity[issue.severity] = self.issues_by_severity.get(issue.severity, 0) + 1


class CodeQualityChecker:
    """
    Comprehensive code quality checker
    綜合代碼質量檢查器

    Checks:
    - Cyclomatic complexity
    - Code duplication
    - Maintainability index
    - Code style violations
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.complexity_analyzer = ComplexityAnalyzer
        self.maintainability_analyzer = MaintainabilityAnalyzer(config)
        self.duplication_detector = DuplicationDetector()

    async def check_directory(
        self,
        directory: str,
        pattern: str = "*.py",
        exclude: Optional[List[str]] = None
    ) -> QualityReport:
        """Check all Python files in directory"""
        exclude = exclude or ['__pycache__', 'venv', '.venv', 'node_modules']

        report = QualityReport()
        python_files = self._find_python_files(directory, pattern, exclude)
        file_metrics_list = []

        for file_path in python_files:
            report.total_files += 1

            # Analyze file
            file_metrics = self._analyze_file(file_path)
            file_metrics_list.append(file_metrics)

            # Check complexity
            complexity_issues = self._check_complexity(file_metrics)
            for issue in complexity_issues:
                report.add_issue(issue)

            # Check maintainability
            maintainability_issues = self._check_maintainability(file_metrics)
            for issue in maintainability_issues:
                report.add_issue(issue)

            # Determine pass/fail
            file_issues = [i for i in report.issues if i.file == file_path]
            if file_issues and any(i.severity == 'error' for i in file_issues):
                report.failed_files += 1
            else:
                report.passed_files += 1

        # Check for duplications across all files
        duplicates = self.duplication_detector.find_duplicates(python_files)
        for dup in duplicates:
            report.add_issue(QualityIssue(
                file=dup.file1,
                line=dup.start1,
                type='duplication',
                severity='warning',
                message=f"Duplicate code block ({dup.lines} lines) with {dup.file2}:{dup.start2}"
            ))

        # Calculate averages
        if file_metrics_list:
            report.average_complexity = sum(
                fm.average_complexity for fm in file_metrics_list
            ) / len(file_metrics_list)

        return report

    def _find_python_files(
        self,
        directory: str,
        pattern: str,
        exclude: List[str]
    ) -> List[str]:
        """Find all Python files in directory"""
        files = []
        base_path = Path(directory)

        for file_path in base_path.rglob(pattern):
            # Check if should exclude
            if any(excluded in file_path.parts for excluded in exclude):
                continue

            files.append(str(file_path))

        return files

    def _analyze_file(self, file_path: str) -> FileMetrics:
        """Analyze a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except Exception as e:
            logger.error(f"Could not read {file_path}: {e}")
            return FileMetrics(path=file_path)

        lines = source.splitlines()

        metrics = FileMetrics(path=file_path)
        metrics.total_lines = len(lines)

        # Count lines
        for line in lines:
            stripped = line.strip()
            if not stripped:
                metrics.blank_lines += 1
            elif stripped.startswith('#'):
                metrics.comment_lines += 1
            else:
                metrics.code_lines += 1

        # Analyze complexity
        analyzer = self.complexity_analyzer(source)
        metrics.functions = analyzer.analyze()

        # Extract imports and classes
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        metrics.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        metrics.imports.append(node.module)
                elif isinstance(node, ast.ClassDef):
                    metrics.classes.append(node.name)
        except SyntaxError:
            pass

        return metrics

    def _check_complexity(self, metrics: FileMetrics) -> List[QualityIssue]:
        """Check complexity issues"""
        issues = []
        max_cc = self.config.get('max_complexity', 10)

        for func in metrics.high_complexity_functions:
            issues.append(QualityIssue(
                file=metrics.path,
                line=func.lineno,
                type='complexity',
                severity='warning' if func.complexity <= 15 else 'error',
                message=f"Function '{func.name}' has cyclomatic complexity {func.complexity} (max: {max_cc})"
            ))

        return issues

    def _check_maintainability(self, metrics: FileMetrics) -> List[QualityIssue]:
        """Check maintainability issues"""
        issues = []
        mi_metrics = self.maintainability_analyzer.analyze(metrics)

        if mi_metrics.grade in ['C', 'D']:
            issues.append(QualityIssue(
                file=metrics.path,
                line=1,
                type='maintainability',
                severity='warning' if mi_metrics.grade == 'C' else 'error',
                message=f"Maintainability grade {mi_metrics.grade} (score: {mi_metrics.mi_score:.1f})"
            ))

        return issues

    def get_report_text(self, report: QualityReport) -> str:
        """Get formatted text report"""
        lines = [
            "=" * 70,
            "Code Quality Report",
            "=" * 70,
            f"Total Files: {report.total_files}",
            f"Passed: {report.passed_files}",
            f"Failed: {report.failed_files}",
            f"Total Issues: {report.total_issues}",
            "",
            "Issues by Type:",
        ]

        for issue_type, count in report.issues_by_type.items():
            lines.append(f"  {issue_type}: {count}")

        lines.extend([
            "",
            "Issues by Severity:",
        ])

        for severity, count in report.issues_by_severity.items():
            lines.append(f"  {severity}: {count}")

        lines.extend([
            "",
            f"Average Complexity: {report.average_complexity:.2f}",
            "=" * 70,
        ])

        return "\n".join(lines)


# ============================================================================
# Quality Gate
# ============================================================================

class QualityGate:
    """
    Quality gate enforcement
    質量門禁強制執行

    Fails build if quality thresholds are not met
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.checker = CodeQualityChecker(config)

    async def check(self, directory: str) -> Tuple[bool, QualityReport]:
        """Run quality gate check"""
        report = await self.checker.check_directory(directory)

        # Check if passed
        passed = self._evaluate_gate(report)

        return passed, report

    def _evaluate_gate(self, report: QualityReport) -> bool:
        """Evaluate if quality gate passes"""
        # Check failed files
        max_failed = self.config.get('max_failed_files', 0)
        if report.failed_files > max_failed:
            return False

        # Check error severity issues
        max_errors = self.config.get('max_errors', 0)
        if report.issues_by_severity.get('error', 0) > max_errors:
            return False

        # Check average complexity
        max_avg_complexity = self.config.get('max_average_complexity', 15)
        if report.average_complexity > max_avg_complexity:
            return False

        return True


__all__ = [
    # Complexity
    "ComplexityMetrics",
    "FileMetrics",
    "ComplexityAnalyzer",

    # Maintainability
    "MaintainabilityMetrics",
    "MaintainabilityAnalyzer",

    # Duplication
    "DuplicateBlock",
    "DuplicationDetector",

    # Quality Checking
    "QualityIssue",
    "QualityReport",
    "CodeQualityChecker",

    # Quality Gate
    "QualityGate",
]
