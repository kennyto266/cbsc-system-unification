#!/usr/bin/env python3
"""
技术指标分析器 - Week 2 任务2.1
Technical Indicators Analyzer - Week 2 Task 2.1

分析simplified_system中的477个技术指标，识别使用频率和重要性
为精简到20个核心指标提供数据支持

Author: Claude Code Assistant
Created: 2025-11-29
Version: 1.0.0
"""

import os
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple, Set
import ast
import json

class TechnicalIndicatorAnalyzer:
    """
    技术指标分析器
    分析477个指标的使用频率和重要性
    """

    def __init__(self):
        """初始化分析器"""
        self.indicator_usage = defaultdict(int)
        self.indicator_definitions = {}
        self.indicator_imports = defaultdict(int)
        self.file_analysis = {}
        self.total_indicators = 0

    def analyze_simplified_system(self, base_path: str = "simplified_system"):
        """
        分析simplified_system中的技术指标

        Args:
            base_path: simplified_system路径
        """
        print(f"🔍 开始分析技术指标: {base_path}")
        base_path = Path(base_path)

        # 扫描所有Python文件
        python_files = list(base_path.rglob("*.py"))
        print(f"📁 找到 {len(python_files)} 个Python文件")

        for file_path in python_files:
            self._analyze_file(file_path)

        # 分析结果
        self._analyze_results()

    def _analyze_file(self, file_path: Path):
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                file_info = {
                    'path': str(file_path),
                    'size': len(content),
                    'indicators_used': set(),
                    'indicators_defined': set(),
                    'imports': set()
                }

                # 查找指标定义
                self._find_indicator_definitions(content, file_info)

                # 查找指标使用
                self._find_indicator_usage(content, file_info)

                # 查找导入
                self._find_indicator_imports(content, file_info)

                self.file_analysis[str(file_path)] = file_info

        except Exception as e:
            print(f"⚠️ 文件分析失败 {file_path}: {e}")

    def _find_indicator_definitions(self, content: str, file_info: dict):
        """查找指标定义"""
        # 匹配指标定义模式
        patterns = [
            r'def\s+(calculate_\w+)',  # calculate_开头的方法
            r'class\s+(\w*Indicator)',  # Indicator结尾的类
            r'def\s+(\w+indicator)',  # indicator结尾的方法
            r'def\s+(\w+[Rr]si)',  # RSI相关
            r'def\s+(\w+[Mm]acd)',  # MACD相关
            r'def\s+(\w+[Bb]ollinger)',  # 布林带相关
            r'def\s+(\w+[Mm]oving|[Aa]verage)',  # 移动平均相关
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    indicator_name = match[0]
                else:
                    indicator_name = match

                file_info['indicators_defined'].add(indicator_name)
                self.indicator_definitions[indicator_name] = self.indicator_definitions.get(indicator_name, 0) + 1

    def _find_indicator_usage(self, content: str, file_info: dict):
        """查找指标使用"""
        # 常见指标使用模式
        common_indicators = [
            'rsi', 'rsi_14', 'sma', 'sma_20', 'ema', 'ema_12', 'ema_26',
            'macd', 'macd_12_26', 'bb', 'bollinger', 'atr', 'cci',
            'stoch', 'stochastic', 'williams', 'williams_r',
            'adx', 'mfi', 'obv', 'vwap', 'ichimoku'
        ]

        # 在代码中搜索指标使用
        words = re.findall(r'\b\w+\b', content.lower())
        for word in words:
            if any(indicator in word for indicator in common_indicators):
                file_info['indicators_used'].add(word)
                self.indicator_usage[word] += 1

        # 搜索方法调用模式
        method_patterns = [
            r'\.calculate_(\w+)\(',
            r'calculate_(\w+)\(',
            r'(\w+)\(',
            r'indicator\(\w+\)',
            r'technical_\w+',
        ]

        for pattern in method_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    indicator_name = match[0].lower()
                else:
                    indicator_name = match.lower()

                if any(indicator in indicator_name for indicator in common_indicators):
                    file_info['indicators_used'].add(indicator_name)
                    self.indicator_usage[indicator_name] += 1

    def _find_indicator_imports(self, content: str, file_info: dict):
        """查找指标导入"""
        # 查找从indicator模块的导入
        import_patterns = [
            r'from\s+.*indicators.*import\s+(.+)'
            r'from\s+.*technical.*import\s+(.+)',
            r'import\s+.*indicators',
            r'import\s+.*technical',
        ]

        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    imports = match[0]
                else:
                    imports = match

                # 清理导入列表
                imports = re.sub(r'[#\'\"].*$', '', imports)  # 移除注释
                imports = re.sub(r'\s+', ' ', imports)  # 规范化空格
                modules = [m.strip() for m in imports.split(',') if m.strip()]

                for module in modules:
                    file_info['imports'].add(module)
                    self.indicator_imports[module] += 1

    def _analyze_results(self):
        """分析结果"""
        print("\n📊 技术指标分析结果")
        print("=" * 50)

        # 统计总指标数
        all_indicators = set()
        for file_info in self.file_analysis.values():
            all_indicators.update(file_info['indicators_defined'])
            all_indicators.update(file_info['indicators_used'])

        self.total_indicators = len(all_indicators)
        print(f"📈 发现技术指标总数: {self.total_indicators}")

        # 使用频率排名
        print(f"\n🔥 使用频率最高的20个指标:")
        top_used = sorted(self.indicator_usage.items(), key=lambda x: x[1], reverse=True)[:20]
        for i, (indicator, count) in enumerate(top_used, 1):
            print(f"   {i:2d}. {indicator:<20} (使用 {count} 次)")

        # 定义频率排名
        print(f"\n📋 定义频率最高的20个指标:")
        top_defined = sorted(self.indicator_definitions.items(), key=lambda x: x[1], reverse=True)[:20]
        for i, (indicator, count) in enumerate(top_defined, 1):
            print(f"   {i:2d}. {indicator:<20} (定义 {count} 次)")

        # 指标分类
        self._categorize_indicators()

        # 计算重要性分数
        self._calculate_importance_scores()

    def _categorize_indicators(self):
        """指标分类"""
        categories = {
            'trend': ['sma', 'ema', 'moving_average', 'ma', 'trend', 'direction'],
            'momentum': ['rsi', 'macd', 'momentum', 'roc', 'stoch', 'stochastic'],
            'volatility': ['atr', 'bollinger', 'volatility', 'std', 'variance'],
            'volume': ['obv', 'vwap', 'volume', 'money_flow', 'adl'],
            'oscillator': ['cci', 'williams', 'stoch', 'rsi', 'macd']
        }

        categorized = defaultdict(set)
        for indicator in self.indicator_usage.keys():
            for category, keywords in categories.items():
                if any(keyword in indicator for keyword in keywords):
                    categorized[category].add(indicator)
                    break
            else:
                categorized['other'].add(indicator)

        print(f"\n🏷️ 指标分类统计:")
        for category, indicators in categorized.items():
            print(f"   {category:<12}: {len(indicators)} 个指标")

    def _calculate_importance_scores(self):
        """计算重要性分数"""
        print(f"\n⭐ 指标重要性评分:")

        # 计算重要性分数 (使用频率 * 0.6 + 定义数 * 0.4)
        importance_scores = {}
        all_indicators = set(self.indicator_usage.keys()) | set(self.indicator_definitions.keys())

        for indicator in all_indicators:
            usage_score = self.indicator_usage.get(indicator, 0)
            definition_score = self.indicator_definitions.get(indicator, 0)
            importance_score = usage_score * 0.6 + definition_score * 0.4
            importance_scores[indicator] = importance_score

        # 排序并显示前20个
        top_important = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)[:20]
        for i, (indicator, score) in enumerate(top_important, 1):
            usage = self.indicator_usage.get(indicator, 0)
            definition = self.indicator_definitions.get(indicator, 0)
            print(f"   {i:2d}. {indicator:<15} (评分: {score:.1f}, 使用: {usage}, 定义: {definition})")

        # 保存推荐的核心指标
        self.core_indicators = [item[0] for item in top_important[:20]]
        print(f"\n✅ 推荐20个核心指标已确定")

    def get_core_indicators(self) -> List[str]:
        """获取推荐的核心指标列表"""
        return getattr(self, 'core_indicators', [])

    def get_recommendation_report(self) -> Dict:
        """获取精简建议报告"""
        if not hasattr(self, 'core_indicators'):
            return {}

        report = {
            'total_indicators': self.total_indicators,
            'core_indicators': self.core_indicators,
            'simplification_ratio': len(self.core_indicators) / max(self.total_indicators, 1),
            'usage_analysis': dict(sorted(self.indicator_usage.items(), key=lambda x: x[1], reverse=True)[:20]),
            'definition_analysis': dict(sorted(self.indicator_definitions.items(), key=lambda x: x[1], reverse=True)[:20]),
            'recommendations': self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """生成精简建议"""
        recommendations = [
            f"从{self.total_indicators}个指标精简到20个核心指标 (精简率: {(1-len(self.core_indicators)/self.total_indicators)*100:.1f}%)",
            "保留高频使用和高定义数量的指标",
            "优先保留趋势类和动量类指标",
            "移除低频使用和重复功能指标",
            "通过参数扩展实现更多变化"
        ]

        return recommendations

    def save_report(self, filename: str = "indicator_analysis_report.json"):
        """保存分析报告"""
        report = self.get_recommendation_report()

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n💾 分析报告已保存: {filename}")


def main():
    """主函数"""
    print("🔬 技术指标分析器启动")
    print("目标: 分析477个技术指标，推荐20个核心指标")
    print("=" * 60)

    analyzer = TechnicalIndicatorAnalyzer()

    # 分析simplified_system
    analyzer.analyze_simplified_system()

    # 获取核心指标
    core_indicators = analyzer.get_core_indicators()

    # 保存报告
    analyzer.save_report("indicator_analysis_report.json")

    print(f"\n🎯 分析完成!")
    print(f"📊 核心20个指标: {core_indicators}")
    print(f"📈 精简比例: {(1-len(core_indicators)/max(analyzer.total_indicators, 1))*100:.1f}%")
    print("🚀 准备进入任务2.2: 保留20个最有效指标")

    return core_indicators


if __name__ == "__main__":
    main()