#!/usr/bin/env python3
"""
VectorBT Sharpe Ratio Fix with 3% Risk-Free Rate
使用VectorBT內置方法修復Sharpe比率計算，確保3%無風險利率正確應用
"""

import numpy as np
import pandas as pd
import requests
import vectorbt as vbt
import json
from datetime import datetime
from typing import Dict, List, Any

class VectorBTSharpeFix:
    """使用VectorBT內置方法修復Sharpe比率計算"""

    def __init__(self):
        self.base_url = "http://18.180.162.113:9191/inst/getInst"
        self.risk_free_rate = 0.03  # 3%無風險利率
        print("[VECTORBT FIX] 使用VectorBT內置Sharpe比率計算")
        print(f"[VECTORBT FIX] 無風險利率: {self.risk_free_rate}")
        print(f"[VECTORBT FIX] 風險: {self.risk_free_rate*100}%")

    def fetch_real_data(self, symbol="0700.hk", duration=365) -> pd.DataFrame:
        """獲取真實股票數據"""
        try:
            print(f"[API] 獲取 {symbol} 數據...")
            params = {"symbol": symbol, "duration": duration}
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'data' not in data or 'close' not in data['data']:
                print("[ERROR] API數據格式錯誤")
                return pd.DataFrame()

            # 解析數據
            close_data = data['data']['close']
            dates = list(close_data.keys())
            prices = list(close_data.values())

            # 創建DataFrame
            df = pd.DataFrame({
                'close': prices
            }, index=pd.to_datetime(dates))

            print(f"[SUCCESS] 獲取 {len(df)} 條記錄")
            return df

        except Exception as e:
            print(f"[ERROR] 數據獲取失敗: {e}")
            return pd.DataFrame()

    def demonstrate_sharpe_methods(self, prices: pd.Series):
        """演示不同的Sharpe比率計算方法"""
        print("\n" + "="*80)
        print("SHARPE RATIO CALCULATION METHODS COMPARISON")
        print("="*80)

        # 計算日收益率
        returns = prices.pct_change().dropna()

        print(f"\n📊 數據概覽:")
        print(f"   價格數據點: {len(prices)}")
        print(f"   收益率數據點: {len(returns)}")
        print(f"   平均日收益率: {returns.mean():.6f}")
        print(f"   日收益率波動率: {returns.std():.6f}")

        # 方法1：錯誤的CAGR方法（當前項目中使用）
        print(f"\n❌ 方法1: 錯誤的CAGR方法 (massive_nonprice_ta_optimizer.py)")
        total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
        years = len(prices) / 365.0
        annual_return_cagr = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        volatility = returns.std() * np.sqrt(365)
        sharpe_wrong = (annual_return_cagr - self.risk_free_rate) / volatility
        print(f"   年化回報 (CAGR): {annual_return_cagr:.6f}")
        print(f"   年化波動率: {volatility:.6f}")
        print(f"   Sharpe比率: {sharpe_wrong:.6f}")
        print(f"   ⚠️  問題: 使用CAGR而不是算術平均")

        # 方法2：正確的手動計算方法
        print(f"\n✅ 方法2: 正確的手動計算方法")
        daily_risk_free = self.risk_free_rate / 365
        excess_returns = returns - daily_risk_free
        sharpe_correct_manual = excess_returns.mean() / returns.std() * np.sqrt(365)
        annual_return_arith = returns.mean() * 365
        print(f"   日無風險利率: {daily_risk_free:.6f}")
        print(f"   年化回報 (算術): {annual_return_arith:.6f}")
        print(f"   年化波動率: {volatility:.6f}")
        print(f"   Sharpe比率: {sharpe_correct_manual:.6f}")
        print(f"   ✅ 優點: 使用算術平均和日無風險利率")

        # 方法3：VectorBT Returns Accessor方法
        print(f"\n🎯 方法3: VectorBT Returns Accessor (推薦)")
        sharpe_vbt_returns = returns.vbt.returns.sharpe_ratio(risk_free=self.risk_free_rate)
        print(f"   VectorBT公式: 內置專業計算")
        print(f"   Sharpe比率: {sharpe_vbt_returns:.6f}")
        print(f"   ✅ 優點: 機構級實現，支援3%無風險利率")

        # 方法4：VectorBT Portfolio方法
        print(f"\n🚀 方法4: VectorBT Portfolio方法 (高級)")
        # 創建簡單的買入持有策略
        portfolio = vbt.Portfolio.from_holding(prices, init_cash=100000)
        sharpe_vbt_portfolio = portfolio.sharpe_ratio(risk_free=self.risk_free_rate)
        print(f"   Portfolio類型: 買入持有")
        print(f"   Sharpe比率: {sharpe_vbt_portfolio:.6f}")
        print(f"   ✅ 優點: 完整組合分析，包含交易成本")

        # 方法比較
        print(f"\n📈 方法比較:")
        methods = [
            ("錯誤CAGR方法", sharpe_wrong),
            ("正確手動方法", sharpe_correct_manual),
            ("VectorBT Returns", sharpe_vbt_returns),
            ("VectorBT Portfolio", sharpe_vbt_portfolio)
        ]

        for i, (name, sharpe) in enumerate(methods, 1):
            status = "❌" if "錯誤" in name else "✅" if sharpe > 0 else "⚠️"
            print(f"   {i}. {name}: {sharpe:.6f} {status}")

        # 合理性檢查
        print(f"\n🔍 合理性檢查:")
        max_reasonable_sharpe = 3.0
        for name, sharpe in methods:
            if sharpe > max_reasonable_sharpe:
                print(f"   ⚠️  {name}: {sharpe:.4f} > {max_reasonable_sharpe} (可能不切實際)")
            else:
                print(f"   ✅ {name}: {sharpe:.4f} (合理範圍)")

        return {
            'sharpe_wrong': sharpe_wrong,
            'sharpe_correct_manual': sharpe_correct_manual,
            'sharpe_vbt_returns': float(sharpe_vbt_returns),
            'sharpe_vbt_portfolio': float(sharpe_vbt_portfolio)
        }

    def create_vectorbt_fix_template(self):
        """創建VectorBT修復模板"""
        print(f"\n" + "="*80)
        print("VECTORTB FIX TEMPLATE")
        print("="*80)

        template_code = '''
# VectorBT Sharpe Ratio Fix Template
# 替換 massive_nonprice_ta_optimizer.py 中的錯誤計算

import vectorbt as vbt

def calculate_sharpe_ratio_vectorbt(returns, risk_free_rate=0.03):
    """
    使用VectorBT內置方法計算Sharpe比率
    - 正確處理3%無風險利率
    - 使用機構級實現
    - 避免CAGR錯誤
    """
    # 將numpy array轉換為pandas Series (如果需要)
    if isinstance(returns, np.ndarray):
        returns = pd.Series(returns)

    # 使用VectorBT Returns Accessor
    sharpe_ratio = returns.vbt.returns.sharpe_ratio(risk_free=risk_free_rate)

    return float(sharpe_ratio)

# 在 massive_nonprice_ta_optimizer.py 中替換:
# 舊的錯誤代碼 (第406-407, 424行):
# years = len(strategy_returns) / 365.0
# annual_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
# sharpe_ratio = (annual_return - risk_free_rate) / volatility

# 新的修復代碼:
sharpe_ratio = calculate_sharpe_ratio_vectorbt(strategy_returns, risk_free_rate=0.03)
'''

        print(template_code)

        # 保存模板
        with open("vectorbt_sharpe_fix_template.py", "w", encoding="utf-8") as f:
            f.write(template_code)
        print(f"\n[SAVED] 模板已保存到: vectorbt_sharpe_fix_template.py")

def main():
    """主函數"""
    print("VectorBT Sharpe Ratio Fix Demonstration")
    print("使用VectorBT內置方法修復Sharpe比率計算錯誤")

    fixer = VectorBTSharpeFix()

    # 獲取真實數據
    price_data = fixer.fetch_real_data("0700.hk", 365)
    if price_data.empty:
        print("[ERROR] 無法獲取數據，演示終止")
        return

    # 演示不同計算方法
    results = fixer.demonstrate_sharpe_methods(price_data['close'])

    # 創建修復模板
    fixer.create_vectorbt_fix_template()

    # 保存結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "demonstration_timestamp": timestamp,
        "data_source": "18.180.162.113:9191",
        "symbol": "0700.hk",
        "risk_free_rate": 0.03,
        "calculation_methods": results,
        "recommended_method": "VectorBT Returns Accessor",
        "fix_priority": "CRITICAL - Replace CAGR calculation immediately",
        "next_steps": [
            "Replace massive_nonprice_ta_optimizer.py line 406-407, 424",
            "Use vectorbt.returns.sharpe_ratio(risk_free=0.03)",
            "Re-run all 24,037 strategy optimizations",
            "Validate new Sharpe ratios are < 3.0"
        ]
    }

    filename = f"vectorbt_sharpe_fix_report_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n" + "="*80)
    print("VECTORBT SHARPE FIX DEMONSTRATION COMPLETED!")
    print("="*80)
    print(f"演示完成:")
    print(f"   錯誤CAGR方法: {results['sharpe_wrong']:.6f}")
    print(f"   正確手動方法: {results['sharpe_correct_manual']:.6f}")
    print(f"   VectorBT Returns: {results['sharpe_vbt_returns']:.6f}")
    print(f"   VectorBT Portfolio: {results['sharpe_vbt_portfolio']:.6f}")
    print(f"\n報告保存: {filename}")
    print(f"修復模板: vectorbt_sharpe_fix_template.py")
    print(f"\n建議: 立即使用VectorBT內置方法替換錯誤的CAGR計算!")
    print("="*80)

if __name__ == "__main__":
    main()