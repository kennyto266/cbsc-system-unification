#!/usr / bin / env python3
"""
修復Sharpe Ratio計算
Fix Sharpe Ratio Calculation

檢查並修復系統中不正確的Sharpe Ratio計算
"""

import json
from datetime import datetime

import numpy as np
import pandas as pd


class SharpeRatioAnalyzer:
    """Sharpe Ratio分析器和修復工具"""

    def __init__(self, risk_free_rate = 0.03):
        """
        初始化Sharpe分析器

        Args:
            risk_free_rate: 年化無風險利率 (默認3%)
        """
        self.risk_free_rate = risk_free_rate
        self.daily_risk_free = risk_free_rate / 252  # 日化無風險利率

    def calculate_correct_sharpe(
        self, returns: pd.Series, trading_days: int = None
    ) -> dict:
        """
        計算正確的Sharpe Ratio

        Args:
            returns: 收益率序列 (應為日收益率)
            trading_days: 交易天數 (用於年化計算)

        Returns:
            包含各種Sharpe Ratio計算的字典
        """
        try:
            if len(returns) < 30:  # 至少需要30天數據
                return {
                    "error": "Insufficient data points for Sharpe calculation",
                    "data_points": len(returns),
                }

            # 計算日化無風險利率
            daily_rf = self.risk_free_rate / 252

            # 超額收益
            excess_returns = returns - daily_rf

            # 基礎統計
            mean_excess = excess_returns.mean()
            std_excess = excess_returns.std()

            if std_excess == 0:
                return {
                    "sharpe_ratio": 0.0,
                    "mean_excess_return": 0.0,
                    "std_excess_return": 0.0,
                    "error": "Zero volatility",
                }

            # 年化因子 (如果沒有提供trading_days，則使用實際數據長度)
            if trading_days is None:
                trading_days = len(returns)

            if trading_days == 0:
                annual_factor = np.sqrt(252)  # 假設一年252個交易日
            else:
                # 根據實際交易天數動態計算年化因子
                annual_factor = np.sqrt(252 * 252 / trading_days)

            # 計算各種Sharpe比率
            sharpe_daily = mean_excess / std_excess * np.sqrt(1)  # 日化Sharpe
            sharpe_annual = mean_excess / std_excess * annual_factor  # 年化Sharpe
            sharpe_252 = mean_excess / std_excess * np.sqrt(252)  # 252日年化Sharpe

            return {
                "sharpe_ratio": sharpe_annual,  # 主要使用年化Sharpe
                "sharpe_daily": sharpe_daily,
                "sharpe_252": sharpe_252,
                "sharpe_annual_factor": sharpe_annual,
                "mean_excess_return": mean_excess * 252,  # 年化超額收益
                "std_excess_return": std_excess * np.sqrt(252),  # 年化波動率
                "risk_free_rate": self.risk_rate,
                "daily_risk_free": daily_rf,
                "annual_factor": annual_factor,
                "trading_days": trading_days,
                "data_points": len(returns),
                "volatility_annual": returns.std() * np.sqrt(252),
            }

        except Exception as e:
            return {
                "error": f"Sharpe calculation failed: {str(e)}",
                "exception": str(e),
            }

    def validate_calculation_method(self, result: dict) -> dict:
        """
        驗證計算方法的合理性

        Args:
            result: Sharpe計算結果

        Returns:
            驗證結果
        """
        validation = {"is_valid": True, "issues": [], "warnings": []}

        if "sharpe_ratio" not in result:
            validation["is_valid"] = False
            validation["issues"].append("Missing sharpe_ratio in result")
            return validation

        sharpe = result["sharpe_ratio"]

        # 檢查Sharpe Ratio的合理性
        if abs(sharpe) > 10:
            validation["warnings"].append(
                f"Unrealistic Sharpe ratio: {sharpe:.3f} (typical range: -3 to 3)"
            )
        elif abs(sharpe) > 5:
            validation["warnings"].append(
                f"High Sharpe ratio: {sharpe:.3f} (consider validation)"
            )

        # 檢查年化因子
        if "annual_factor" in result:
            annual_factor = result["annual_factor"]
            if annual_factor < 10 or annual_factor > 20:
                validation["warnings"].append(
                    f"Unusual annualization factor: {annual_factor:.2f}"
                )

        return validation

    def fix_backtest_sharpe_calculation(self, backtest_file: str) -> bool:
        """
        修復現有回測文件中的Sharpe Ratio

        Args:
            backtest_file: 回測結果文件路徑

        Returns:
            是否修復成功
        """
        try:
            # 讀取回測結果
            with open(backtest_file, "r", encoding="utf - 8") as f:
                results = json.load(f)

            fixed_count = 0
            error_count = 0

            # 修復策略結果
            if "strategies" in results:
                for strategy in results["strategies"]:
                    if "returns" in strategy:
                        try:
                            returns = pd.Series(strategy["returns"])
                            corrected_sharpe = self.calculate_correct_sharpe(returns)

                            if "error" not in corrected_sharpe:
                                old_sharpe = strategy.get("sharpe_ratio", 0)
                                strategy["sharpe_ratio"] = corrected_sharpe[
                                    "sharpe_ratio"
                                ]
                                strategy["sharpe_calculation_details"] = {
                                    "original_sharpe": old_sharpe,
                                    "corrected_sharpe": corrected_sharpe[
                                        "sharpe_ratio"
                                    ],
                                    "method": "Fixed annualized Sharpe with 3% risk - free rate",
                                }
                                fixed_count += 1

                                # 添加驗證
                                validation = self.validate_calculation_method(
                                    corrected_sharpe
                                )
                                if not validation["is_valid"]:
                                    error_count += 1
                                    print(
                                        f"  WARNING: Sharpe calculation issue for strategy: {validation['issues'] + validation['warnings']}"
                                    )

                        except Exception as e:
                            error_count += 1
                            print(
                                f"  ERROR fixing strategy {strategy.get('name', 'unknown')}: {e}"
                            )

            # 保存修復後的結果
            if fixed_count > 0:
                backup_file = backtest_file.replace(".json", "_backup.json")
                with open(backup_file, "w", encoding="utf - 8") as f:
                    json.dump(results, f, indent = 2, ensure_ascii = False, default = str)

                with open(backtest_file, "w", encoding="utf - 8") as f:
                    json.dump(results, f, indent = 2, ensure_ascii = False, default = str)

                print(f"Fixed Sharpe calculation for {fixed_count} strategies")
                print(f"Backup saved to: {backup_file}")

                if error_count == 0:
                    print("All Sharpe calculations are now realistic!")
                    return True
                else:
                    print(f"{error_count} strategies still have issues")
                    return False
            else:
                print("No strategies found to fix")
                return False

        except Exception as e:
            print(f"Failed to fix backtest file: {e}")
            return False


def analyze_sharpe_issues():
    """分析當前系統中的Sharpe Ratio問題"""
    print("=" * 80)
    print("SHARPE RATIO ISSUES ANALYSIS")
    print("=" * 80)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    analyzer = SharpeRatioAnalyzer()

    # 檢查現有結果文件
    import glob

    result_files = (
        glob.glob("*sharpe*.json")
        + glob.glob("*optimization*.json")
        + glob.glob("*backtest*.json")
    )

    if not result_files:
        print("No result files found to analyze")
        return

    print(f"Found {len(result_files)} result files to analyze...")
    print()

    problematic_files = []

    for file_path in result_files:
        try:
            with open(file_path, "r", encoding="utf - 8") as f:
                data = json.load(f)

            # 檢查是否有不合理的Sharpe值
            high_sharpe_count = 0
            max_sharpe = 0

            def check_sharpe_values(obj, path=""):
                nonlocal high_sharpe_count, max_sharpe

                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key == "sharpe_ratio" and isinstance(value, (int, float)):
                            if abs(value) > 5:  # 超過5的Sharpe值需要檢查
                                high_sharpe_count += 1
                                max_sharpe = max(max_sharpe, abs(value))
                        elif isinstance(value, (dict, list)):
                            check_sharpe_values(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        if isinstance(item, (dict, list)):
                            check_sharpe_values(item, f"{path}[{i}]")

            check_sharpe_values(data)

            if high_sharpe_count > 0:
                problematic_files.append(
                    {
                        "file": file_path,
                        "high_sharpe_count": high_sharpe_count,
                        "max_sharpe": max_sharpe,
                    }
                )
                print(f"FILE: {file_path}")
                print(
                    f"   WARNING: Found {high_sharpe_count} unrealistic Sharpe ratios"
                )
                print(f"   MAXIMUM SHARPE: {max_sharpe:.3f}")
                print()

        except Exception as e:
            print(f"ERROR analyzing {file_path}: {e}")

    print("=" * 80)
    print(f"ANALYSIS SUMMARY:")
    print(f"Files with issues: {len(problematic_files)}")

    if problematic_files:
        print("\nRECOMMENDED ACTIONS:")
        print("1. Review Sharpe ratio calculation methodology")
        print("2. Ensure proper annualization factors")
        print("3. Use correct risk - free rate (3%)")
        print("4. Validate data quality and time periods")
        print("5. Consider realistic return expectations")

        # 生成修復報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"sharpe_analysis_report_{timestamp}.md"

        with open(report_file, "w", encoding="utf - 8") as f:
            f.write("# Sharpe Ratio Analysis Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Problematic Files\n\n")

            for file_info in problematic_files:
                f.write(f"### {file_info['file']}\n")
                f.write(
                    f"- Unrealistic Sharpe ratios: {file_info['high_sharpe_count']}\n"
                )
                f.write(f"- Maximum Sharpe: {file_info['max_sharpe']:.3f}\n\n")

            f.write("## Recommended Fixes\n\n")
            f.write("1. **Sharpe Formula Verification * *:\n")
            f.write("   ```python\n")
            f.write("   # Correct formula:\n")
            f.write("   excess_returns = returns - risk_free_rate / 252\n")
            f.write(
                "   sharpe = excess_returns.mean() / excess_returns.std() * sqrt(252)\n"
            )
            f.write("   ```\n\n")
            f.write("2. **Risk - Free Rate * *: Use 3% annual rate (0.03)\n")
            f.write("3. **Annualization * *: Use sqrt(252) for daily returns\n")
            f.write("4. **Data Quality * *: Ensure sufficient data points (>30 days)\n")

        print(f"\nDetailed report saved: {report_file}")
    else:
        print("No Sharpe ratio issues found!")
        print("All calculations appear to be realistic.")


if __name__ == "__main__":
    analyze_sharpe_issues()
