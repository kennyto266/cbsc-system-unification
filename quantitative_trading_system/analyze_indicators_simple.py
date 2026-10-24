#!/usr/bin/env python3
"""
Simple Technical Indicators Analyzer
Analyzes simplified_system indicators for Week 2 Task 2.1
"""

import os
import re
from collections import defaultdict
from pathlib import Path

def analyze_indicators():
    """Analyze technical indicators in simplified_system"""
    print("Technical Indicator Analysis Started")
    print("=" * 50)

    base_path = Path("simplified_system")
    if not base_path.exists():
        print("ERROR: simplified_system directory not found")
        return []

    # Scan for indicators
    indicator_usage = defaultdict(int)
    indicator_definitions = defaultdict(int)

    python_files = list(base_path.rglob("*.py"))
    print(f"Scanning {len(python_files)} Python files...")

    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()

            # Find indicator definitions
            definitions = re.findall(r'def\s+(calculate_\w+)', content)
            for def_match in definitions:
                indicator_name = def_match.split('_')[1] if '_' in def_match else def_match
                indicator_definitions[indicator_name] += 1

            # Find indicator usage
            usage_patterns = [
                r'\.calculate_(\w+)\(',
                r'calculate_(\w+)\(',
                r'\b(rsi|sma|ema|macd|bb|atr|cci|stoch|williams|vwap|obv|adx|mfi)\b',
            ]

            for pattern in usage_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        indicator_name = match[0].lower()
                    else:
                        indicator_name = match.lower()

                    if len(indicator_name) > 1:  # Filter out single chars
                        indicator_usage[indicator_name] += 1

        except Exception as e:
            continue

    # Calculate total indicators
    all_indicators = set(indicator_usage.keys()) | set(indicator_definitions.keys())
    total_count = len(all_indicators)
    print(f"Total technical indicators found: {total_count}")

    # Sort by usage frequency
    print("\nTop 20 most used indicators:")
    top_used = sorted(indicator_usage.items(), key=lambda x: x[1], reverse=True)[:20]
    for i, (indicator, count) in enumerate(top_used, 1):
        print(f"  {i:2d}. {indicator:<15} (used {count} times)")

    # Sort by definition frequency
    print("\nTop 20 most defined indicators:")
    top_defined = sorted(indicator_definitions.items(), key=lambda x: x[1], reverse=True)[:20]
    for i, (indicator, count) in enumerate(top_defined, 1):
        print(f"  {i:2d}. {indicator:<15} (defined {count} times)")

    # Calculate importance scores
    print("\nImportance scores (usage*0.6 + definition*0.4):")
    importance_scores = {}

    for indicator in all_indicators:
        usage = indicator_usage.get(indicator, 0)
        definition = indicator_definitions.get(indicator, 0)
        score = usage * 0.6 + definition * 0.4
        importance_scores[indicator] = score

    top_important = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)[:20]
    core_indicators = []

    for i, (indicator, score) in enumerate(top_important, 1):
        usage = indicator_usage.get(indicator, 0)
        definition = indicator_definitions.get(indicator, 0)
        print(f"  {i:2d}. {indicator:<15} (score: {score:.1f}, usage: {usage}, defined: {definition})")
        core_indicators.append(indicator)

    print(f"\nAnalysis completed!")
    print(f"Recommended core indicators: {len(core_indicators)}")
    print(f"Simplification ratio: {(1-len(core_indicators)/total_count)*100:.1f}%")

    # Map to standard indicator names
    standard_indicators = []
    indicator_mapping = {
        'sma': 'SMA',
        'ema': 'EMA',
        'rsi': 'RSI',
        'macd': 'MACD',
        'bb': 'Bollinger Bands',
        'atr': 'ATR',
        'cci': 'CCI',
        'stoch': 'Stochastic',
        'williams': 'Williams %R',
        'vwap': 'VWAP',
        'obv': 'OBV',
        'adx': 'ADX',
        'mfi': 'MFI'
    }

    for indicator in core_indicators:
        mapped = indicator_mapping.get(indicator, indicator.upper())
        if mapped not in standard_indicators:
            standard_indicators.append(mapped)

    return standard_indicators[:20]  # Ensure exactly 20

if __name__ == "__main__":
    core_indicators = analyze_indicators()
    print(f"\nFinal core indicators list: {core_indicators}")