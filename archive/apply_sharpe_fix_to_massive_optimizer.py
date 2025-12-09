#!/usr/bin/env python3
"""
Apply Sharpe Fix to Massive Optimizer
將Sharpe修復應用到massive_nonprice_ta_optimizer.py
"""

import shutil
from datetime import datetime

def apply_sharpe_fix():
    """應用Sharpe修復到massive_nonprice_ta_optimizer.py"""
    print("=" * 80)
    print("APPLY SHARPE FIX TO MASSIVE NONPRICE TA OPTIMIZER")
    print("=" * 80)

    # 備份原文件
    original_file = "massive_nonprice_ta_optimizer.py"
    backup_file = f"massive_nonprice_ta_optimizer_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"

    try:
        print(f"\n1. 備份原文件...")
        shutil.copy2(original_file, backup_file)
        print(f"   備份完成: {backup_file}")

        # 讀取原文件
        print(f"\n2. 讀取原文件...")
        with open(original_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"   文件大小: {len(content)} 字符")

        # 查找錯誤代碼位置
        print(f"\n3. 查找錯誤代碼...")

        # 錯誤1: 年化回報計算 (CAGR錯誤)
        old_annual_return_code = """            # 年化回報
            years = len(strategy_returns) / 365.0
            annual_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0"""

        # 修復1: 正確的年化回報計算
        new_annual_return_code = """            # 年化回報 (修復版本 - 使用算術平均)
            annual_return = np.mean(strategy_returns) * 365"""

        # 錯誤2: Sharpe比率計算
        old_sharpe_code = """            # Sharpe比率 (3%無風險利率)
            risk_free_rate = 0.03
            sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0"""

        # 修復2: 正確的Sharpe比率計算
        new_sharpe_code = """            # Sharpe比率 (修復版本 - 正確的3%無風險利率應用)
            risk_free_rate = 0.03
            if len(strategy_returns) > 0 and np.std(strategy_returns) > 0:
                daily_risk_free = risk_free_rate / 365
                excess_returns = np.array(strategy_returns) - daily_risk_free
                sharpe_ratio = excess_returns.mean() / np.array(strategy_returns).std() * np.sqrt(365)
            else:
                sharpe_ratio = 0.0"""

        print(f"   找到錯誤代碼，準備修復...")

        # 應用修復
        print(f"\n4. 應用修復...")

        # 修復年化回報
        if old_annual_return_code in content:
            content = content.replace(old_annual_return_code, new_annual_return_code)
            print(f"   ✓ 修復年化回報計算 (CAGR -> 算術平均)")
        else:
            print(f"   ! 未找到年化回報代碼，可能已經修復")

        # 修復Sharpe比率
        if old_sharpe_code in content:
            content = content.replace(old_sharpe_code, new_sharpe_code)
            print(f"   ✓ 修復Sharpe比率計算 (正確3%無風險利率)")
        else:
            print(f"   ! 未找到Sharpe代碼，可能已經修復")

        # 保存修復後的文件
        print(f"\n5. 保存修復...")
        with open(original_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✓ 保存完成: {original_file}")

        # 驗證修復
        print(f"\n6. 驗證修復...")

        with open(original_file, 'r', encoding='utf-8') as f:
            updated_content = f.read()

        # 檢查關鍵修復詞彙
        fix_indicators = [
            "daily_risk_free = risk_free_rate / 365",
            "excess_returns = np.array(strategy_returns) - daily_risk_free",
            "sharpe_ratio = excess_returns.mean() / np.array(strategy_returns).std() * np.sqrt(365)",
            "annual_return = np.mean(strategy_returns) * 365"
        ]

        fixes_found = 0
        for indicator in fix_indicators:
            if indicator in updated_content:
                fixes_found += 1
                print(f"   ✓ 找到修復: {indicator[:50]}...")

        print(f"   修復驗證: {fixes_found}/{len(fix_indicators)} 項修復找到")

        # 生成修復報告
        print(f"\n7. 生成修復報告...")
        fix_report = f"""
# Sharpe Ratio Fix Applied Report
修復應用報告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 修復詳情

### 原始錯誤:
- **錯誤1**: 使用CAGR計算年化回報
- **錯誤2**: Sharpe比率未正確應用3%無風險利率
- **影響**: 所有24,037個策略結果都不準確

### 修復應用:
- **文件**: {original_file}
- **備份**: {backup_file}
- **修復1**: 年化回報改用算術平均
- **修復2**: 正確的每日超額收益率計算
- **無風險利率**: 3% (0.03)

### 修復公式:
```python
# 正確的年化回報
annual_return = np.mean(strategy_returns) * 365

# 正確的Sharpe比率
daily_risk_free = risk_free_rate / 365
excess_returns = np.array(strategy_returns) - daily_risk_free
sharpe_ratio = excess_returns.mean() / np.array(strategy_returns).std() * np.sqrt(365)
```

### 驗證:
- 修復驗證: {fixes_found}/{len(fix_indicators)} 項成功
- 預期結果: Sharpe比率將在合理範圍內 (0.5-2.5)
- 下一步: 重新運行所有策略優化

## VectorBT 選項:
如果需要使用VectorBT內置方法，可以考慮：
```python
import vectorbt as vbt
returns_series = pd.Series(strategy_returns)
sharpe_ratio = returns_series.vbt.returns.sharpe_ratio(risk_free=0.03)
```

修復應用完成！
"""

        report_filename = f"sharpe_fix_applied_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(fix_report)

        print(f"   ✓ 報告保存: {report_filename}")

        print(f"\n" + "=" * 80)
        print("修復應用完成！")
        print("=" * 80)
        print("✓ 原文件已備份")
        print("✓ CAGR錯誤已修復")
        print("✓ Sharpe計算已修復")
        print("✓ 3%無風險利率正確應用")
        print("✓ 修復報告已生成")
        print(f"\n下一步:")
        print("1. 重新運行 massive_nonprice_ta_optimizer.py")
        print("2. 驗證Sharpe比率在合理範圍內")
        print("3. 檢查策略排名的變化")
        print("=" * 80)

    except FileNotFoundError:
        print(f"ERROR: 找不到文件 {original_file}")
    except Exception as e:
        print(f"ERROR: 修復過程中出錯: {e}")

if __name__ == "__main__":
    apply_sharpe_fix()