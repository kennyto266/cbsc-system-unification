#!/usr/bin/env python3
"""
夏普比率驗證和修正工具
基於行業標準重新計算並比較結果
"""

import numpy as np
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple

class SharpeRatioValidator:
    """夏普比率驗證器 - 專業級金融計算"""

    def __init__(self):
        self.risk_free_rate = 0.03  # 3%年無風險利率
        self.trading_days = 252     # 年交易日數

    def calculate_sharpe_correct(self, returns: np.ndarray) -> float:
        """
        計算正確的夏普比率 (年化)

        Args:
            returns: 日回報率數組

        Returns:
            float: 年化夏普比率
        """
        if len(returns) < 2:
            return 0.0

        # 將年無風險利率轉換為日利率 (複利計算)
        daily_rf = (1 + self.risk_free_rate) ** (1/self.trading_days) - 1

        # 計算超額回報
        excess_returns = returns - daily_rf

        # 使用樣本標準差 (ddof=1) - 行業標準
        if np.std(excess_returns, ddof=1) == 0:
            return 0.0

        # 日均超額回報
        mean_excess_daily = np.mean(excess_returns)

        # 年化夏普比率
        annual_mean_excess = mean_excess_daily * self.trading_days
        annual_vol = np.std(excess_returns, ddof=1) * np.sqrt(self.trading_days)

        sharpe_ratio = annual_mean_excess / annual_vol

        return sharpe_ratio

    def calculate_sharpe_original_wrong(self, returns: np.ndarray) -> float:
        """
        原始的錯誤計算方法 (用於比較)
        """
        if len(returns) < 2:
            return 0.0

        risk_free_rate = 0.03
        daily_risk_free = risk_free_rate / 365  # 錯誤的簡單除法

        excess_returns = returns - daily_risk_free
        sharpe_ratio = excess_returns.mean() / np.array(returns).std() * np.sqrt(365)  # 錯誤

        return sharpe_ratio

    def calculate_sharpe_industry_methods(self, returns: np.ndarray) -> Dict[str, float]:
        """
        使用多種行業標準方法計算夏普比率
        """
        results = {}

        # 方法1: 經典方法 (我們的正確實現)
        results['classic_correct'] = self.calculate_sharpe_correct(returns)

        # 方法2: 使用empyrical庫 (如果可用)
        try:
            import empyrical
            # empyrical使用年化無風險利率和日回報
            results['empyrical'] = empyrical.sharpe_ratio(
                returns,
                risk_free=self.risk_free_rate,
                period='daily'
            )
        except ImportError:
            results['empyrical'] = None

        # 方法3: VectorBT方法 (如果可用)
        try:
            import vectorbt as vbt
            returns_series = pd.Series(returns)
            # VectorBT的sharpe_ratio方法
            results['vectorbt'] = vbt.returns.SharpeRatio.run(
                returns_series,
                risk_free_rate=self.risk_free_rate
            ).sharpe_ratio.iloc[0]
        except ImportError:
            results['vectorbt'] = None

        # 方法4: 年化回報率方法
        if len(returns) > 0:
            total_return = np.prod(1 + returns) - 1
            annual_return = (1 + total_return) ** (self.trading_days / len(returns)) - 1
            annual_vol = np.std(returns, ddof=1) * np.sqrt(self.trading_days)
            results['annual_return_method'] = (annual_return - self.risk_free_rate) / annual_vol
        else:
            results['annual_return_method'] = 0.0

        return results

    def validate_calculation_methods(self, test_returns: np.ndarray) -> Dict[str, Any]:
        """
        驗證不同計算方法的差異
        """
        methods = self.calculate_sharpe_industry_methods(test_returns)

        # 計算差異
        if methods['classic_correct'] is not None:
            differences = {}
            for method, value in methods.items():
                if value is not None and method != 'classic_correct':
                    diff = abs(value - methods['classic_correct'])
                    diff_pct = (diff / methods['classic_correct']) * 100
                    differences[method] = {
                        'difference': diff,
                        'difference_pct': diff_pct,
                        'value': value
                    }
        else:
            differences = {}

        return {
            'correct_sharpe': methods['classic_correct'],
            'all_methods': methods,
            'differences': differences,
            'conclusion': self._analyze_consistency(methods, differences)
        }

    def _analyze_consistency(self, methods: Dict[str, float], differences: Dict) -> str:
        """
        分析各種方法的一致性
        """
        valid_methods = {k: v for k, v in methods.items() if v is not None}

        if len(valid_methods) < 2:
            return "無法比較 - 只有單一方法可用"

        # 計算最大差異百分比
        if differences:
            max_diff_pct = max([d['difference_pct'] for d in differences.values()])
        else:
            max_diff_pct = 0

        if max_diff_pct < 1:
            return "高度一致 - 所有方法結果相近"
        elif max_diff_pct < 5:
            return "基本一致 - 方法間差異可接受"
        elif max_diff_pct < 15:
            return "中等差異 - 建議使用最嚴格的方法"
        else:
            return "嚴重差異 - 需要檢查計算方法"

    def validate_existing_results(self, results_file: str) -> Dict[str, Any]:
        """
        驗證現有結果文件中的夏普比率
        """
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            validation_results = []

            for strategy in data.get('top_strategies', []):
                # 重新計算這個策略的夏普比率
                # 注意：這裡我們只能演示，因為我們沒有原始回報數據
                validation_results.append({
                    'strategy_id': strategy.get('strategy_id'),
                    'original_sharpe': strategy.get('sharpe_ratio'),
                    'corrected_sharpe': None,  # 需要原始數據才能計算
                    'status': 'needs_original_data'
                })

            return {
                'validation_results': validation_results,
                'message': f"已載入 {len(validation_results)} 個策略進行驗證",
                'requires_raw_data': True
            }

        except Exception as e:
            return {
                'error': f"無法載入結果文件: {e}",
                'message': "需要提供正確的文件路徑"
            }

    def create_correction_report(self) -> str:
        """
        創建詳細的修正報告
        """
        report = f"""
# 夏普比率計算錯誤修正報告
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🚨 發現的關鍵錯誤

### 錯誤1: 無風險利率轉換錯誤
- **原始錯誤**: `daily_risk_free = 0.03 / 365`
- **正確方法**: `daily_risk_free = (1 + 0.03) ** (1/252) - 1`
- **影響**: 低估了無風險利率，導致夏普比率偏離

### 錯誤2: 年化因子錯誤
- **原始錯誤**: 使用 `sqrt(365)`
- **正確方法**: 使用 `sqrt(252)` (交易日)
- **影響**: 年化計算錯誤，導致跨期比較失效

### 錯誤3: 樣本統計錯誤
- **原始錯誤**: 使用總體標準差 `ddof=0`
- **正確方法**: 使用樣本標準差 `ddof=1`
- **影響**: 低估了波動率，導致夏普比率高估

### 錯誤4: 方法混亂
- **原始錯誤**: 分子用excess_returns，分母用原始returns
- **正確方法**: 分子和分母都應使用excess_returns
- **影響**: 數學概念錯誤，導致結果無意義

## ✅ 正確的計算方法

```python
def calculate_sharpe_correct(returns, risk_free_rate=0.03):
    # 1. 正確的日無風險利率轉換
    daily_rf = (1 + risk_free_rate) ** (1/252) - 1

    # 2. 計算超額回報
    excess_returns = returns - daily_rf

    # 3. 使用樣本標準差 (ddof=1)
    mean_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns, ddof=1)

    # 4. 正確的年化
    sharpe = (mean_excess * 252) / (std_excess * np.sqrt(252))

    return sharpe
```

## 📊 預期影響分析

基於錯誤分析，預期修正後的夏普比率可能會：
- 降低10-30%（因為正確的無風險利率和樣本統計）
- 重新排序所有策略排名
- 某些「世界級」策略可能降至普通水平
- 但結果將更加準確和可靠

## 🎯 推薦行動

1. **立即停止使用現有結果**
2. **重新計算所有24,044個策略**
3. **使用標準金融庫進行驗證**
4. **更新所有文檔和聲稱**
5. **實施持續的計算驗證**

## 🔍 驗證工具

本驗證器提供了多種行業標準方法：
- 經典正確方法
- Empyrical庫方法
- VectorBT庫方法
- 年化回報率方法

建議使用至少兩種方法進行交叉驗證。
        """.strip()

        return report

# 測試和演示
def main():
    """主程序 - 演示夏普比率驗證"""
    print("🔍 夏普比率驗證器")
    print("檢測並修正計算錯誤")

    validator = SharpeRatioValidator()

    # 創建測試數據
    np.random.seed(42)
    test_returns = np.random.normal(0.001, 0.02, 252)  # 一年的日回報

    print(f"\n📊 測試數據: {len(test_returns)} 個交易日")
    print(f"日回報均值: {np.mean(test_returns):.6f}")
    print(f"日回報標準差: {np.std(test_returns, ddof=1):.6f}")

    # 驗證計算方法
    validation = validator.validate_calculation_methods(test_returns)

    print(f"\n🔬 計算方法驗證:")
    print(f"正確夏普比率: {validation['correct_sharpe']:.4f}")
    print(f"一致性結論: {validation['conclusion']}")

    print(f"\n📈 所有方法結果:")
    for method, value in validation['all_methods'].items():
        if value is not None:
            print(f"  {method}: {value:.4f}")

    print(f"\n⚠️  方法差異:")
    for method, diff in validation['differences'].items():
        print(f"  {method}: 差異 {diff['difference']:.4f} ({diff['difference_pct']:.2f}%)")

    # 創建修正報告
    print(f"\n📝 生成修正報告...")
    report = validator.create_correction_report()

    with open('sharpe_ratio_correction_report.md', 'w', encoding='utf-8') as f:
        f.write(report)

    print("✅ 修正報告已保存: sharpe_ratio_correction_report.md")

if __name__ == "__main__":
    main()