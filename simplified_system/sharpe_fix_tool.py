#!/usr / bin / env python3
"""
Sharpe Ratio 計算錯誤修復工具
Fix Sharpe Ratio Calculation Errors

發現問題：
- massive_optimization_results_20251127_063942.csv 出現 658,219,925.42 Sharpe值
- 多個不統一的Sharpe計算函數
- 潛在的除零和數值穩定性問題

修復目標：
- 統一Sharpe計算標準
- 修復數值異常
- 確保計算正確性
"""

import warnings
from typing import Union

import numpy as np
import pandas as pd


def calculate_correct_sharpe_ratio(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = 0.03,
    trading_days: int = 252,
) -> float:
    """
    計算正確的Sharpe Ratio

    Args:
        returns: 日收益率序列 (必須是淨收益率，不是價格序列)
        risk_free_rate: 年化無風險利率 (默認3%)
        trading_days: 年交易日數 (默認252)

    Returns:
        float: 年化Sharpe Ratio

    Formula:
        Sharpe = (mean(returns) - risk_free_rate / 252) / std(returns) * sqrt(252)
    """
    # 轉換為numpy數組
    if isinstance(returns, pd.Series):
        returns = returns.values

    # 過濾無效值
    returns = returns[np.isfinite(returns)]

    if len(returns) == 0:
        return 0.0

    # 計算日無風險收益率
    daily_rf_rate = risk_free_rate / trading_days

    # 計算超額收益率
    excess_returns = returns - daily_rf_rate

    # 檢查標準差是否為0
    std_excess = np.std(excess_returns, ddof = 1)  # 使用樣本標準差

    if std_excess == 0 or np.isnan(std_excess):
        return 0.0

    # 計算Sharpe Ratio
    mean_excess = np.mean(excess_returns)

    if np.isnan(mean_excess):
        return 0.0

    sharpe_daily = mean_excess / std_excess
    sharpe_annualized = sharpe_daily * np.sqrt(trading_days)

    # 檢查最終結果合理性
    if not np.isfinite(sharpe_annualized):
        return 0.0

    # 設定合理範圍警告
    if abs(sharpe_annualized) > 10:
        warnings.warn(f"Sharpe Ratio {sharpe_annualized:.2f} 異常高，請檢查計算邏輯")

    return sharpe_annualized


def calculate_sharpe_from_prices(
    prices: Union[pd.Series, np.ndarray],
    positions: Union[pd.Series, np.ndarray] = None,
    risk_free_rate: float = 0.03,
    trading_days: int = 252,
) -> float:
    """
    從價格數據計算Sharpe Ratio

    Args:
        prices: 價格序列
        positions: 倉位序列 (0 = 現金, 1 = 持倉)，如果為None則假設全程持倉
        risk_free_rate: 年化無風險利率
        trading_days: 年交易日數

    Returns:
        float: 年化Sharpe Ratio
    """
    # 轉換為numpy數組
    if isinstance(prices, pd.Series):
        prices = prices.values
    if isinstance(positions, pd.Series):
        positions = positions.values

    # 計算日收益率
    price_returns = np.diff(prices) / prices[:-1]

    if positions is None:
        # 假設全程投資
        portfolio_returns = price_returns
    else:
        # 根據倉位計算投資組合收益率
        positions = positions[1:] if len(positions) > len(price_returns) else positions
        portfolio_returns = np.where(
            positions == 1,  # 持倉時獲得市場收益
            price_returns,
            risk_free_rate / trading_days,  # 現金時獲得無風險收益
        )

    return calculate_correct_sharpe_ratio(
        portfolio_returns, risk_free_rate, trading_days
    )


def validate_existing_sharpe_calculations(csv_file_path: str):
    """
    驗證現有CSV文件中的Sharpe計算結果

    Args:
        csv_file_path: CSV結果文件路徑
    """
    print(f"🔍 驗證 Sharpe 計算結果: {csv_file_path}")

    try:
        df = pd.read_csv(csv_file_path)
        print(f"📊 文件包含 {len(df)} 個策略結果")

        # 檢查Sharpe值範圍
        sharpe_stats = df["sharpe"].describe()
        print(f"\n📈 Sharpe Ratio 統計:")
        print(f"   數量: {sharpe_stats['count']:.0f}")
        print(f"   均值: {sharpe_stats['mean']:.2f}")
        print(f"   標準差: {sharpe_stats['std']:.2f}")
        print(f"   最小值: {sharpe_stats['min']:.2f}")
        print(f"   最大值: {sharpe_stats['max']:.2f}")

        # 標記異常值
        abnormal_mask = (df["sharpe"].abs() > 50) | (~np.isfinite(df["sharpe"]))
        abnormal_count = abnormal_mask.sum()

        if abnormal_count > 0:
            print(f"\n⚠️ 發現 {abnormal_count} 個異常Sharpe值:")
            abnormal_results = df[abnormal_mask][
                ["strategy", "params", "sharpe", "total_return"]
            ]
            print(abnormal_results.head(10).to_string(index = False))

            if abnormal_count > 10:
                print(f"... 還有 {abnormal_count - 10} 個異常值")

        # 顯示合理範圍內的最佳策略
        normal_mask = ~abnormal_mask
        if normal_mask.sum() > 0:
            normal_results = df[normal_mask].nlargest(5, "sharpe")
            print(f"\n✅ 正常範圍內的前5個策略:")
            print(
                normal_results[
                    ["strategy", "params", "sharpe", "total_return"]
                ].to_string(index = False)
            )

        return df, abnormal_mask

    except Exception as e:
        print(f"❌ 文件處理錯誤: {e}")
        return None, None


def fix_sharpe_calculations(csv_file_path: str, output_file_path: str = None):
    """
    修復CSV文件中的Sharpe計算錯誤

    Args:
        csv_file_path: 輸入CSV文件
        output_file_path: 輸出CSV文件 (可選)
    """
    df, abnormal_mask = validate_existing_sharpe_calculations(csv_file_path)

    if df is None:
        return

    if abnormal_mask.sum() == 0:
        print("✅ 未發現異常Sharpe值，無需修復")
        return

    print(f"\n🔧 開始修復 {abnormal_mask.sum()} 個異常值...")

    # 修復異常值（設置為0或重新計算）
    df.loc[abnormal_mask, "sharpe"] = 0.0

    # 重新排序
    df = df.sort_values("sharpe", ascending = False).reset_index(drop = True)

    # 保存修復結果
    if output_file_path is None:
        output_file_path = csv_file_path.replace(".csv", "_fixed.csv")

    df.to_csv(output_file_path, index = False)
    print(f"✅ 修復完成，結果已保存到: {output_file_path}")


def main():
    """主函數 - 演示修復過程"""
    print("=" * 80)
    print("Sharpe Ratio Calculation Error Fix Tool")
    print("=" * 80)

    # 查找需要修復的文件
    import glob

    csv_files = glob.glob("simplified_system / *results*.csv")

    print(f"Found {len(csv_files)} result files:")
    for f in csv_files:
        print(f"   - {f}")

    # 重點檢查有問題的文件
    problematic_files = [
        "simplified_system / massive_optimization_results_20251127_063942.csv",
        "simplified_system / massive_optimization_results_20251127_063726.csv",
    ]

    for file_path in problematic_files:
        if file_path in csv_files:
            print(f"\n" + "=" * 60)
            validate_existing_sharpe_calculations(file_path)
            print("\n建議修復命令:")
            print(f"python sharpe_fix_tool.py --fix {file_path}")

    print(f"\n" + "=" * 80)
    print("🎯 修復建議:")
    print("1. 統一使用 calculate_correct_sharpe_ratio() 函數")
    print("2. 將所有異常Sharpe值設置為0並重新排序")
    print("3. 增加合理性檢查防止未來錯誤")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sharpe Ratio 計算錯誤修復工具")
    parser.add_argument("--fix", help="修復指定CSV文件的Sharpe計算錯誤")
    parser.add_argument("--validate", help="驗證指定CSV文件的Sharpe計算結果")

    args = parser.parse_args()

    if args.fix:
        fix_sharpe_calculations(args.fix)
    elif args.validate:
        validate_existing_sharpe_calculations(args.validate)
    else:
        main()
