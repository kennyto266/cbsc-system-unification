#!/usr / bin / env python3
"""
Simple Code Refactoring Analyzer
Analyzes Python code for refactoring needs (T162 - T166)
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Any
import json


class CodeAnalyzer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues = {
            "large_functions": [],
            "complex_functions": [],
            "large_classes": [],
            "unused_imports": [],
            "todos": [],
            "dead_code": []
        }

    def analyze(self) -> Dict[str, Any]:
        """Analyze a Python file"""
        try:
            with open(self.file_path, 'r', encoding='utf - 8', errors='ignore') as f:
                content = f.read()

            # Parse AST
            try:
                tree = ast.parse(content)
            except Exception:
                return {"error": "Parse error"}

            # Analyze functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self._analyze_function(node, content)
                elif isinstance(node, ast.ClassDef):
                    self._analyze_class(node, content)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    pass  # Will analyze imports separately

            # Check for TODOs
            self._find_todos(content)

            # Check for dead code
            self._find_dead_code(content)

            return self.issues

        except Exception as e:
            return {"error": str(e)}

    def _analyze_function(self, node: ast.FunctionDef, content: str):
        """Analyze a function"""
        lines = content.split('\n')
        start_line = node.lineno
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 20
        func_lines = end_line - start_line

        # Calculate complexity
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1

        if func_lines > 50:
            self.issues["large_functions"].append({
                "name": node.name,
                "line": start_line,
                "lines": func_lines,
                "complexity": complexity
            })

        if complexity > 10:
            self.issues["complex_functions"].append({
                "name": node.name,
                "line": start_line,
                "lines": func_lines,
                "complexity": complexity
            })

    def _analyze_class(self, node: ast.ClassDef, content: str):
        """Analyze a class"""
        lines = content.split('\n')
        start_line = node.lineno
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 50
        class_lines = end_line - start_line

        if class_lines > 200:
            self.issues["large_classes"].append({
                "name": node.name,
                "line": start_line,
                "lines": class_lines
            })

    def _find_todos(self, content: str):
        """Find TODO and FIXME comments"""
        for i, line in enumerate(content.split('\n'), 1):
            if re.search(r'#\s*(TODO|FIXME|XXX|HACK)', line, re.IGNORECASE):
                self.issues["todos"].append({
                    "line": i,
                    "content": line.strip()
                })

    def _find_dead_code(self, content: str):
        """Find dead code patterns"""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'^\s * if\s + False\s*:', line):
                self.issues["dead_code"].append({
                    "line": i + 1,
                    "type": "if_false",
                    "content": line.strip()
                })


def main():
    """Main function"""
    project_root = Path("/c / Users / Penguin8n / CODEX--")

    print("\n" + "="*60)
    print("Code Quality Analysis Report")
    print("="*60 + "\n")

    all_issues = {
        "large_functions": [],
        "complex_functions": [],
        "large_classes": [],
        "todos": []
    }

    # Find and analyze Python files
    python_files = list(project_root.rglob("*.py"))
    python_files = [f for f in python_files if ".venv" not in str(f)]

    print(f"Found {len(python_files)} Python files to analyze\n")

    for file_path in python_files:
        analyzer = CodeAnalyzer(str(file_path))
        issues = analyzer.analyze()

        if "error" not in issues:
            for key in all_issues:
                if key in issues:
                    for item in issues[key]:
                        item["file"] = str(file_path)
                        all_issues[key].append(item)

    # Print summary
    print("Analysis Summary:")
    print(f"  - Large functions (>50 lines): {len(all_issues['large_functions'])}")
    print(f"  - Complex functions (complexity>10): {len(all_issues['complex_functions'])}")
    print(f"  - Large classes (>200 lines): {len(all_issues['large_classes'])}")
    print(f"  - TODO / FIXME items: {len(all_issues['todos'])}")

    # Show top issues
    print("\nTop 10 Largest Functions:")
    sorted_funcs = sorted(all_issues['large_functions'], key=lambda x: x['lines'], reverse=True)[:10]
    for i, func in enumerate(sorted_funcs, 1):
        print(f"  {i}. {func['name']} in {Path(func['file']).name}")
        print(f"     Line {func['line']}, {func['lines']} lines, complexity {func['complexity']}")

    print("\nTop 5 Largest Classes:")
    sorted_classes = sorted(all_issues['large_classes'], key=lambda x: x['lines'], reverse=True)[:5]
    for i, cls in enumerate(sorted_classes, 1):
        print(f"  {i}. {cls['name']} in {Path(cls['file']).name}")
        print(f"     Line {cls['line']}, {cls['lines']} lines")

    # Save report
    report = {
        "summary": {
            "files_analyzed": len(python_files),
            "large_functions": len(all_issues['large_functions']),
            "complex_functions": len(all_issues['complex_functions']),
            "large_classes": len(all_issues['large_classes']),
            "todos": len(all_issues['todos'])
        },
        "details": all_issues
    }

    with open("/c / Users / Penguin8n / CODEX--/refactoring_report.json", 'w') as f:
        json.dump(report, f, indent=2)

    print("\nReport saved to: /c / Users / Penguin8n / CODEX--/refactoring_report.json")
    print("="*60 + "\n")

    return report


if __name__ == "__main__":
    main()
