"""
Code Deduplication Utility
代碼去重工具

自動識別和消除重複代碼，提高代碼質量和可維護性
"""

import ast
import os
import re
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import difflib
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeBlock:
    """代碼塊數據類"""
    file_path: str
    start_line: int
    end_line: int
    content: str
    hash: str
    complexity: int  # 圈複雜度
    lines_of_code: int


@dataclass
class DuplicationResult:
    """重複檢測結果"""
    blocks: List[CodeBlock]
    similarity: float  # 相似度 0-1
    type: str  # 'exact', 'similar', 'partial'
    suggestions: List[str]


class CodeDeduplicator:
    """
    代碼去重器
    掃描代碼庫，識別重複代碼並提供重構建議
    """

    def __init__(self, target_dir: str, min_similarity: float = 0.8):
        self.target_dir = target_dir
        self.min_similarity = min_similarity
        self.code_blocks: List[CodeBlock] = []
        self.duplications: List[DuplicationResult] = []

    def scan_directory(self) -> Dict[str, Any]:
        """
        掃描目錄中的所有Python文件
        """
        logger.info(f"開始掃描目錄: {self.target_dir}")

        python_files = []
        for root, dirs, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    python_files.append(os.path.join(root, file))

        logger.info(f"找到 {len(python_files)} 個Python文件")

        # 解析每個文件
        for file_path in python_files:
            self._parse_file(file_path)

        logger.info(f"解析完成，共 {len(self.code_blocks)} 個代碼塊")
        return {
            "files_scanned": len(python_files),
            "code_blocks": len(self.code_blocks),
            "total_lines": sum(block.lines_of_code for block in self.code_blocks)
        }

    def find_duplications(self) -> List[DuplicationResult]:
        """
        查找重複代碼
        """
        logger.info("開始查找重複代碼...")

        # 1. 查找完全相同的代碼
        exact_duplications = self._find_exact_duplications()

        # 2. 查找相似的代碼
        similar_duplications = self._find_similar_duplications()

        # 3. 查找結構相似的重複
        structural_duplications = self._find_structural_duplications()

        self.duplications = exact_duplications + similar_duplications + structural_duplications

        logger.info(f"找到 {len(self.duplications)} 處重複代碼")
        return self.duplications

    def generate_refactoring_plan(self) -> Dict[str, Any]:
        """
        生成重構計劃
        """
        total_duplications = len(self.duplications)
        total_lines = sum(
            sum(block.lines_of_code for block in dup.blocks)
            for dup in self.duplications
        )

        # 按重複類型分組
        duplications_by_type = defaultdict(list)
        for dup in self.duplications:
            duplications_by_type[dup.type].append(dup)

        # 計算優先級
        prioritized_duplications = sorted(
            self.duplications,
            key=lambda x: (len(x.blocks) * x.similarity, x.blocks[0].complexity),
            reverse=True
        )

        return {
            "summary": {
                "total_duplications": total_duplications,
                "total_duplicated_lines": total_lines,
                "estimated_reduction": total_lines * 0.8,  # 假設可以減少80%
                "files_affected": len(set(block.file_path for dup in self.duplications for block in dup.blocks))
            },
            "by_type": {
                "exact": len(duplications_by_type['exact']),
                "similar": len(duplications_by_type['similar']),
                "structural": len(duplications_by_type['structural'])
            },
            "refactoring_plan": self._create_refactoring_steps(prioritized_duplications),
            "quick_wins": self._identify_quick_wins(prioritized_duplications)
        }

    def _parse_file(self, file_path: str):
        """解析Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析AST
            tree = ast.parse(content)

            # 提取函數和類
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    code_block = self._extract_code_block(file_path, node, content)
                    if code_block:
                        self.code_blocks.append(code_block)

                # 提取代碼片段（不小於5行）
                elif isinstance(node, ast.If) or isinstance(node, ast.For) or isinstance(node, ast.While):
                    # 檢查是否有足夠的行數
                    start = node.lineno - 1
                    end = node.end_lineno if hasattr(node, 'end_lineno') else start + 10
                    if end - start >= 5:
                        lines = content.split('\n')[start:end]
                        if lines:
                            code_block = CodeBlock(
                                file_path=file_path,
                                start_line=start + 1,
                                end_line=end,
                                content='\n'.join(lines),
                                hash=self._hash_code('\n'.join(lines)),
                                complexity=self._calculate_complexity(node),
                                lines_of_code=len(lines)
                            )
                            self.code_blocks.append(code_block)

        except Exception as e:
            logger.error(f"解析文件失敗 {file_path}: {e}")

    def _extract_code_block(
        self,
        file_path: str,
        node: ast.AST,
        content: str
    ) -> Optional[CodeBlock]:
        """從AST節點提取代碼塊"""
        try:
            start = node.lineno - 1
            end = node.end_lineno if hasattr(node, 'end_lineno') else start + 10

            lines = content.split('\n')[start:end]
            if not lines:
                return None

            code_content = '\n'.join(lines)

            return CodeBlock(
                file_path=file_path,
                start_line=start + 1,
                end_line=end,
                content=code_content,
                hash=self._hash_code(code_content),
                complexity=self._calculate_complexity(node),
                lines_of_code=len(lines)
            )
        except Exception as e:
            logger.error(f"提取代碼塊失敗: {e}")
            return None

    def _hash_code(self, code: str) -> str:
        """計算代碼哈希值"""
        import hashlib
        # 移除空白字符和註釋
        cleaned_code = re.sub(r'#.*', '', code)
        cleaned_code = re.sub(r'\s+', ' ', cleaned_code).strip()
        return hashlib.md5(cleaned_code.encode()).hexdigest()

    def _calculate_complexity(self, node: ast.AST) -> int:
        """計算圈複雜度"""
        complexity = 1  # 基礎複雜度

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _find_exact_duplications(self) -> List[DuplicationResult]:
        """查找完全相同的代碼"""
        hash_groups = defaultdict(list)
        for block in self.code_blocks:
            hash_groups[block.hash].append(block)

        duplications = []
        for hash_value, blocks in hash_groups.items():
            if len(blocks) > 1:
                duplications.append(DuplicationResult(
                    blocks=blocks,
                    similarity=1.0,
                    type='exact',
                    suggestions=[
                        "創建共享函數或方法",
                        "提取到公共模塊",
                        "使用裝飾器模式"
                    ]
                ))

        return duplications

    def _find_similar_duplications(self) -> List[DuplicationResult]:
        """查找相似的代碼"""
        duplications = []
        processed = set()

        for i, block1 in enumerate(self.code_blocks):
            for j, block2 in enumerate(self.code_blocks[i+1:], i+1):
                if (i, j) in processed:
                    continue

                similarity = self._calculate_similarity(block1.content, block2.content)
                if similarity >= self.min_similarity:
                    duplications.append(DuplicationResult(
                        blocks=[block1, block2],
                        similarity=similarity,
                        type='similar',
                        suggestions=[
                            "參數化相似函數",
                            "使用模板方法模式",
                            "創建基類並繼承"
                        ]
                    ))
                    processed.add((i, j))

        return duplications

    def _find_structural_duplications(self) -> List[DuplicationResult]:
        """查找結構相似的重複"""
        # 基於AST結構的比較
        structural_groups = defaultdict(list)

        for block in self.code_blocks:
            try:
                tree = ast.parse(block.content)
                structure = self._get_ast_structure(tree)
                structural_groups[structure].append(block)
            except:
                continue

        duplications = []
        for structure, blocks in structural_groups.items():
            if len(blocks) > 1:
                # 計算平均相似度
                similarities = []
                for i, block1 in enumerate(blocks):
                    for block2 in blocks[i+1:]:
                        sim = self._calculate_similarity(block1.content, block2.content)
                        similarities.append(sim)

                avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                if avg_similarity >= self.min_similarity * 0.6:  # 結構相似度要求較低
                    duplications.append(DuplicationResult(
                        blocks=blocks,
                        similarity=avg_similarity,
                        type='structural',
                        suggestions=[
                            "抽象公共模式",
                            "使用策略模式",
                            "實現重構工具"
                        ]
                    ))

        return duplications

    def _get_ast_structure(self, tree: ast.AST) -> str:
        """獲取AST結構的字符串表示"""
        structure = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                structure.append(f"def:{node.name}")
            elif isinstance(node, ast.ClassDef):
                structure.append(f"class:{node.name}")
            elif isinstance(node, ast.If):
                structure.append("if")
            elif isinstance(node, ast.For):
                structure.append("for")
            elif isinstance(node, ast.While):
                structure.append("while")
            elif isinstance(node, ast.Try):
                structure.append("try")

        return '|'.join(structure)

    def _calculate_similarity(self, code1: str, code2: str) -> float:
        """計算兩段代碼的相似度"""
        # 清理代碼
        clean1 = self._clean_code(code1)
        clean2 = self._clean_code(code2)

        # 使用序列匹配算法
        matcher = difflib.SequenceMatcher(None, clean1, clean2)
        return matcher.ratio()

    def _clean_code(self, code: str) -> str:
        """清理代碼：移除註釋、空白等"""
        # 移除註釋
        code = re.sub(r'#.*', '', code)
        # 移除多餘的空白
        code = re.sub(r'\s+', ' ', code)
        # 移除字面量的差異（用標記替代）
        code = re.sub(r'"[^"]*"', '__STRING__', code)
        code = re.sub(r"'[^']*'", '__STRING__', code)
        code = re.sub(r'\b\d+\b', '__NUMBER__', code)
        code = re.sub(r'\b\d+\.\d+\b', '__NUMBER__', code)

        return code.strip()

    def _create_refactoring_steps(
        self,
        prioritized_duplications: List[DuplicationResult]
    ) -> List[Dict[str, Any]]:
        """創建重構步驟"""
        steps = []

        for i, dup in enumerate(prioritized_duplications[:10]):  # 只處理前10個
            files_involved = list(set(block.file_path for block in dup.blocks))
            total_lines = sum(block.lines_of_code for block in dup.blocks)

            step = {
                "step": i + 1,
                "priority": "高" if dup.similarity > 0.9 else "中" if dup.similarity > 0.7 else "低",
                "type": dup.type,
                "similarity": f"{dup.similarity:.2%}",
                "files_involved": files_involved,
                "total_lines": total_lines,
                "potential_savings": int(total_lines * dup.similarity * 0.8),
                "recommendation": self._get_best_refactoring_approach(dup)
            }
            steps.append(step)

        return steps

    def _identify_quick_wins(
        self,
        prioritized_duplications: List[DuplicationResult]
    ) -> List[Dict[str, Any]]:
        """識識快速修復的重複"""
        quick_wins = []

        for dup in prioritized_duplications:
            # 快速修復條件：
            # 1. 完全相同或高度相似
            # 2. 代碼行數小於20行
            # 3. 複雜度小於5
            # 4. 不在同一文件中

            if (dup.similarity > 0.9 and
                all(block.lines_of_code < 20 for block in dup.blocks) and
                all(block.complexity < 5 for block in dup.blocks) and
                len(set(block.file_path for block in dup.blocks)) > 1):

                quick_wins.append({
                    "description": f"合併 {len(dup.blocks)} 個相似的代碼塊",
                    "effort": "低",
                    "impact": "高",
                    "files": list(set(block.file_path for block in dup.blocks)),
                    "lines_affected": sum(block.lines_of_code for block in dup.blocks)
                })

        return quick_wins[:5]  # 返回前5個快速修復

    def _get_best_refactoring_approach(self, duplication: DuplicationResult) -> str:
        """獲取最佳重構方法"""
        if duplication.type == 'exact':
            if all(block.lines_of_code < 10 for block in duplication.blocks):
                return "創建共享函數"
            else:
                return "提取到公共模塊"

        elif duplication.type == 'similar':
            if any('def' in block.content for block in duplication.blocks):
                return "參數化函數並使用默認參數"
            else:
                return "創建模板方法"

        else:  # structural
            if any('class' in block.content for block in duplication.blocks):
                return "使用繼承或多態"
            else:
                return "抽象公共模式到輔助函數"

    def generate_deduplication_report(self) -> str:
        """生成去重報告"""
        if not self.duplications:
            return "未發現重複代碼"

        report = ["# 代碼去重分析報告\n"]
        report.append(f"掃描目錄: {self.target_dir}")
        report.append(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 總結
        total_duplications = len(self.duplications)
        total_lines = sum(
            sum(block.lines_of_code for block in dup.blocks)
            for dup in self.duplications
        )
        estimated_savings = int(total_lines * 0.7)

        report.append("## 總結")
        report.append(f"- 發現重複: {total_duplications} 處")
        report.append(f"- 重複行數: {total_lines} 行")
        report.append(f"- 預計可減少: {estimated_savings} 行 ({estimated_savings/total_lines:.1%})\n")

        # 按類型統計
        type_counts = {}
        for dup in self.duplications:
            type_counts[dup.type] = type_counts.get(dup.type, 0) + 1

        report.append("## 重複類型分布")
        for dup_type, count in type_counts.items():
            type_name = {
                'exact': '完全相同',
                'similar': '高度相似',
                'structural': '結構相似'
            }.get(dup_type, dup_type)
            report.append(f"- {type_name}: {count} 處\n")

        # 詳細結果
        report.append("## 詳細結果\n")

        for i, dup in enumerate(self.duplications[:10], 1):  # 只顯示前10個
            report.append(f"### {i}. {dup.type.upper()} 重複 (相似度: {dup.similarity:.2%})")

            for j, block in enumerate(dup.blocks, 1):
                rel_path = os.path.relpath(block.file_path, self.target_dir)
                report.append(f"   {j}. {rel_path}:{block.start_line}-{block.end_line}")

            report.append(f"   建議操作: {dup.suggestions[0]}\n")

        # 重構建議
        report.append("## 重構建議\n")
        report.append("1. **優先處理完全相同的代碼** - 這些最容易合併")
        report.append("2. **考慮創建公共工具模塊** - 將通用功能提取到 utils 包")
        report.append("3. **使用設計模式** - 策略模式、模板方法模式等可以減少重複")
        report.append("4. **定期運行代碼檢查** - 集成到CI/CD流程中\n")

        return '\n'.join(report)


# 使用示例和便捷函數
def analyze_codebase(directory: str) -> Dict[str, Any]:
    """
    分析代碼庫的重複情況
    """
    deduplicator = CodeDeduplicator(directory)

    # 掃描文件
    scan_result = deduplicator.scan_directory()

    # 查找重複
    duplications = deduplicator.find_duplications()

    # 生成重構計劃
    refactoring_plan = deduplicator.generate_refactoring_plan()

    return {
        "scan_result": scan_result,
        "duplications": len(duplications),
        "refactoring_plan": refactoring_plan,
        "report": deduplicator.generate_deduplication_report()
    }


def generate_deduplication_script(directory: str, output_file: str = "deduplication_script.py"):
    """
    生成自動去重腳本
    """
    deduplicator = CodeDeduplicator(directory)
    deduplicator.scan_directory()
    duplications = deduplicator.find_duplications()

    script = ["#!/usr/bin/env python3", '"""\n自動代碼去重腳本\n"""\n\n']
    script.append("import os\nimport re\n\n")
    script.append("def deduplicate_code():\n    # TODO: 實現自動去重邏輯\n    pass\n\n\n")
    script.append("if __name__ == '__main__':\n    deduplicate_code()\n")

    # 寫入文件
    with open(output_file, 'w') as f:
        f.write('\n'.join(script))

    return output_file