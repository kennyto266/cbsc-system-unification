#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Circular Dependency Detection Script
循環依賴檢測腳本

檢測 Python 項目中的循環導入依賴
"""

import ast
import os
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Set, Tuple


class ImportAnalyzer(ast.NodeVisitor):
    """
    AST visitor to detect imports
    AST 訪問者檢測導入
    """

    def __init__(self, filepath: str, root_dir: str):
        self.filepath = filepath
        self.root_dir = root_dir
        self.imports: Set[str] = set()
        self.from_imports: Set[Tuple[str, str]] = set()
        self.module_path = self._get_module_path(filepath)

    def _get_module_path(self, filepath: str) -> str:
        """
        Convert filepath to module path
        將文件路徑轉換為模塊路徑
        """
        try:
            rel_path = os.path.relpath(filepath, self.root_dir)
            return rel_path.replace(os.sep, '.')[:-3]  # Remove .py
        except ValueError:
            # File is not under root_dir
            return filepath

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement"""
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statement"""
        if node.module:
            module = node.module.split('.')[0]
            self.imports.add(module)
            self.from_imports.add((module, node.module))
        self.generic_visit(node)


class CircularDependencyDetector:
    """
    Detect circular dependencies in Python project
    檢測 Python 項目中的循環依賴
    """

    def __init__(self, root_dirs: List[str], exclude_dirs: List[str] = None):
        """
        Initialize detector

        Args:
            root_dirs: Root directories to scan
            exclude_dirs: Directories to exclude from scanning
        """
        self.root_dirs = root_dirs
        self.exclude_dirs = exclude_dirs or [
            '__pycache__',
            '.git',
            'node_modules',
            'venv',
            'env',
            '.venv',
            'dist',
            'build'
        ]
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.modules: Set[str] = set()

    def _should_exclude(self, filepath: str) -> bool:
        """Check if file should be excluded"""
        for exclude_dir in self.exclude_dirs:
            if exclude_dir in filepath:
                return True
        return False

    def _is_python_file(self, filepath: str) -> bool:
        """Check if file is a Python file"""
        return filepath.endswith('.py')

    def _analyze_file(self, filepath: str, root_dir: str) -> None:
        """Analyze a single Python file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                analyzer = ImportAnalyzer(filepath, root_dir)
                try:
                    analyzer.visit(ast.parse(f.read()))
                    self.modules.add(analyzer.module_path)
                    self.graph[analyzer.module_path].update(analyzer.imports)
                except SyntaxError as e:
                    print(f"⚠️  Syntax error in {filepath}: {e}")
        except Exception as e:
            print(f"⚠️  Error reading {filepath}: {e}")

    def build_graph(self) -> None:
        """Build dependency graph"""
        print("🔍 Building dependency graph...")

        for root_dir in self.root_dirs:
            if not os.path.exists(root_dir):
                print(f"⚠️  Directory not found: {root_dir}")
                continue

            for dirpath, _, filenames in os.walk(root_dir):
                if self._should_exclude(dirpath):
                    continue

                for filename in filenames:
                    if self._is_python_file(filename):
                        filepath = os.path.join(dirpath, filename)
                        self._analyze_file(filepath, root_dir)

        print(f"✅ Analyzed {len(self.modules)} modules")

    def _has_cycle(
        self,
        node: str,
        visited: Set[str] = None,
        rec_stack: Set[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Check if node has cycle using DFS

        Returns:
            (has_cycle, cycle_path)
        """
        if visited is None:
            visited = set()
        if rec_stack is None:
            rec_stack = set()

        visited.add(node)
        rec_stack.add(node)

        for neighbor in self.graph.get(node, []):
            # Skip external modules
            if neighbor not in self.modules:
                continue

            if neighbor not in visited:
                has_cycle, cycle_path = self._has_cycle(neighbor, visited, rec_stack)
                if has_cycle:
                    cycle_path.insert(0, node)
                    return True, cycle_path
            elif neighbor in rec_stack:
                # Found a cycle
                cycle = [node, neighbor]
                return True, cycle

        rec_stack.remove(node)
        return False, []

    def detect_cycles(self) -> List[Tuple[str, List[str]]]:
        """
        Detect all circular dependencies

        Returns:
            List of (module, cycle_path) tuples
        """
        cycles = []
        checked = set()

        for module in self.modules:
            if module not in checked:
                has_cycle, cycle_path = self._has_cycle(module)
                if has_cycle and cycle_path:
                    # Find the full cycle
                    full_cycle = self._find_full_cycle(cycle_path[0])
                    if full_cycle and full_cycle not in [c[1] for c in cycles]:
                        cycles.append((cycle_path[0], full_cycle))
                checked.add(module)

        return cycles

    def _find_full_cycle(self, start_node: str) -> List[str]:
        """Find the full cycle starting from node"""
        cycle = [start_node]
        visited = {start_node}
        current = start_node

        while True:
            neighbors = self.graph.get(current, set())
            found_next = False

            for neighbor in neighbors:
                if neighbor in self.modules and neighbor in cycle:
                    # Found the cycle completion
                    cycle.append(neighbor)
                    return cycle

                if neighbor in self.modules and neighbor not in visited:
                    visited.add(neighbor)
                    cycle.append(neighbor)
                    current = neighbor
                    found_next = True
                    break

            if not found_next:
                break

        return cycle

    def get_module_info(self, module: str) -> Dict:
        """Get information about a module"""
        return {
            'module': module,
            'dependencies': list(self.graph.get(module, set())),
            'dependents': [
                m for m, deps in self.graph.items()
                if module in deps and m in self.modules
            ]
        }

    def generate_report(self) -> Dict:
        """Generate comprehensive report"""
        self.build_graph()
        cycles = self.detect_cycles()

        # Calculate statistics
        total_modules = len(self.modules)
        total_dependencies = sum(len(deps) for deps in self.graph.values())
        avg_dependencies = total_dependencies / total_modules if total_modules > 0 else 0

        # Find modules with most dependencies
        sorted_by_deps = sorted(
            self.graph.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        return {
            'summary': {
                'total_modules': total_modules,
                'total_dependencies': total_dependencies,
                'average_dependencies': round(avg_dependencies, 2),
                'circular_dependencies': len(cycles)
            },
            'cycles': [
                {
                    'entry_point': entry,
                    'cycle': ' -> '.join(cycle)
                }
                for entry, cycle in cycles
            ],
            'top_dependencies': [
                {
                    'module': module,
                    'dependency_count': len(deps),
                    'dependencies': list(deps)
                }
                for module, deps in sorted_by_deps[:10]
            ]
        }


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Detect circular dependencies in Python project'
    )
    parser.add_argument(
        'directories',
        nargs='+',
        help='Directories to scan'
    )
    parser.add_argument(
        '--exclude',
        '-e',
        action='append',
        help='Directories to exclude'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output file for report (JSON)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Initialize detector
    detector = CircularDependencyDetector(
        root_dirs=args.directories,
        exclude_dirs=args.exclude
    )

    # Generate report
    print("=" * 60)
    print("🔍 Circular Dependency Detection Report")
    print("=" * 60)
    print()

    report = detector.generate_report()

    # Print summary
    print("📊 Summary:")
    print(f"  Total modules: {report['summary']['total_modules']}")
    print(f"  Total dependencies: {report['summary']['total_dependencies']}")
    print(f"  Average dependencies per module: {report['summary']['average_dependencies']}")
    print(f"  Circular dependencies found: {report['summary']['circular_dependencies']}")
    print()

    # Print cycles
    if report['cycles']:
        print("⚠️  Circular Dependencies:")
        print("-" * 60)
        for i, cycle_info in enumerate(report['cycles'], 1):
            print(f"{i}. Entry point: {cycle_info['entry_point']}")
            print(f"   Cycle: {cycle_info['cycle']}")
            print()
    else:
        print("✅ No circular dependencies found!")
        print()

    # Print top dependencies
    if args.verbose:
        print("📈 Top Modules by Dependency Count:")
        print("-" * 60)
        for item in report['top_dependencies']:
            print(f"  {item['module']}: {item['dependency_count']} dependencies")
        print()

    # Save report if requested
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Report saved to: {args.output}")

    # Exit with error if cycles found
    if report['summary']['circular_dependencies'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
