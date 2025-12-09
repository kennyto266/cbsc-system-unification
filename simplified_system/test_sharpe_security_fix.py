#!/usr/bin/env python3
"""
Sharpe比率安全修復驗證腳本
Sharpe Ratio Security Fix Verification Script

驗證771,630,339異常值問題是否完全解決
"""

import numpy as np
import pandas as pd
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from backtest.safe_sharpe_calculator import SafeSharpeCalculator, safe_calculate_sharpe_ratio
from backtest.vectorbt_engine import VectorBTEngine


def create_problematic_test_cases() -> List[Dict[str, Any]]:
    """創建可能導致異常Sharpe值的測試案例"""
    test_cases = []

    # 案例1：接近零波動率
    print("創建測試案例1：接近零波動率...")
    low_vol_returns = np.random.normal(0.0001, 0.00001, 100)  # 極低波動
    test_cases.append({
        'name': '接近零波動率',
        'returns': low_vol_returns,
        'expected_behavior': '應觸發最小波動率保護',
        'total_trades': 5
    })

    # 案例2：單次交易
    print("創建測試案例2：單次交易...")
    single_trade_returns = np.zeros(252)
    single_trade_returns[100] = 0.1  # 單次10%收益
    test_cases.append({
        'name': '單次交易',
        'returns': single_trade_returns,
        'expected_behavior': '應觸發交易次數不足保護',
        'total_trades': 1
    })

    # 案例3：極端值
    print("創建測試案例3：極端值...")
    normal_returns = np.random.normal(0.001, 0.02, 100)
    extreme_returns = np.append(normal_returns, [5.0])  # 500%單日收益
    test_cases.append({
        'name': '極端值',
        'returns': extreme_returns,
        'expected_behavior': '應處理極端值而不崩潰',
        'total_trades': 20
    })

    # 案例4：包含NaN和無窮大
    print("創建測試案例4：包含異常值...")
    messy_returns = np.random.normal(0.001, 0.02, 100)
    messy_returns[10] = np.nan
    messy_returns[20] = np.inf
    messy_returns[30] = -np.inf
    test_cases.append({
        'name': '包含NaN和無窮大',
        'returns': messy_returns,
        'expected_behavior': '應清理異常值',
        'total_trades': 25
    })

    # 案例5：數據不足
    print("創建測試案例5：數據不足...")
    short_returns = np.random.normal(0.001, 0.02, 5)  # 只有5個數據點
    test_cases.append({
        'name': '數據不足',
        'returns': short_returns,
        'expected_behavior': '應觸發數據不足保護',
        'total_trades': 3
    })

    return test_cases


def test_problematic_scenarios(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """測試問題場景"""
    print(f"\n🧪 測試 {len(test_cases)} 個問題場景...")
    print("=" * 80)

    calculator = SafeSharpeCalculator(enable_validation=True)
    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n測試案例 {i}: {test_case['name']}")
        print("-" * 40)
        print(f"預期行為: {test_case['expected_behavior']}")

        # 執行測試
        result = calculator.calculate_sharpe_ratio(
            test_case['returns'],
            method="safe_standard",
            total_trades=test_case['total_trades']
        )

        # 驗證結果
        sharpe = result['sharpe_ratio']
        is_safe = np.isfinite(sharpe) and abs(sharpe) <= 10.0

        print(f"計算結果: Sharpe = {sharpe:.6f}")
        print(f"數據點數: {result['data_points']}")
        print(f"計算方法: {result['method']}")
        print(f"是否安全: {'✅' if is_safe else '❌'}")

        # 檢查是否有安全回退
        if result.get('is_safe_fallback', False):
            print(f"安全回退原因: {result['failure_reason']}")

        # 檢查預處理信息
        if 'preprocessing_info' in result:
            info = result['preprocessing_info']
            if info.get('nan_count', 0) > 0 or info.get('inf_count', 0) > 0:
                print(f"清理異常值: NaN={info.get('nan_count', 0)}, Inf={info.get('inf_count', 0)}")

        # 驗證關鍵要求
        assert np.isfinite(sharpe), f"Sharpe應該是有限數值: {sharpe}"
        assert abs(sharpe) <= 10.0, f"Sharpe應該在[-10, 10]範圍內: {sharpe}"

        results.append({
            'case_name': test_case['name'],
            'sharpe_ratio': sharpe,
            'is_safe': is_safe,
            'is_fallback': result.get('is_safe_fallback', False),
            'failure_reason': result.get('failure_reason', 'None'),
            'data_points': result['data_points'],
            'preprocessing_info': result.get('preprocessing_info', {})
        })

        print(f"✅ 測試通過: Sharpe安全且合理")

    return {
        'total_tests': len(test_cases),
        'all_safe': all(r['is_safe'] for r in results),
        'results': results
    }


def test_vectorbt_engine_integration():
    """測試VectorBT引擎集成"""
    print(f"\n🔧 測試VectorBT引擎集成...")
    print("=" * 80)

    try:
        # 創建VectorBT引擎
        engine = VectorBTEngine()

        # 創建模擬數據
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'open': np.random.uniform(100, 200, 100),
            'high': np.random.uniform(101, 201, 100),
            'low': np.random.uniform(99, 199, 100),
            'close': np.random.uniform(100, 200, 100),
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)

        # 執行回測
        result = engine.backtest_strategy(
            data,
            "RSI_MEAN_REVERSION",
            {"period": 14, "oversold": 30, "overbought": 70},
            "TEST_SYMBOL"
        )

        sharpe = result.sharpe_ratio
        is_safe = np.isfinite(sharpe) and abs(sharpe) <= 10.0

        print(f"VectorBT引擎測試:")
        print(f"  Sharpe比率: {sharpe:.6f}")
        print(f"  總回報: {result.total_return:.4f}")
        print(f"  最大回撤: {result.max_drawdown:.4f}")
        print(f"  交易次數: {result.total_trades}")
        print(f"  是否安全: {'✅' if is_safe else '❌'}")

        # 驗證結果
        assert np.isfinite(sharpe), f"VectorBT Sharpe應該是有限數值: {sharpe}"
        assert abs(sharpe) <= 10.0, f"VectorBT Sharpe應該在合理範圍內: {sharpe}"

        print("✅ VectorBT引擎集成測試通過")
        return {'success': True, 'sharpe': sharpe, 'safe': is_safe}

    except Exception as e:
        print(f"❌ VectorBT引擎集成測試失敗: {e}")
        return {'success': False, 'error': str(e)}


def test_original_problem_case():
    """測試原始問題案例（模擬導致771,630,339的情況）"""
    print(f"\n🎯 測試原始問題案例...")
    print("=" * 80)

    # 模擬可能導致異常Sharpe的數據
    # 案例1：幾乎所有收益都相同，只有一個微小差異
    print("創建原始問題案例：幾乎零波動率...")
    almost_constant_returns = np.full(252, 0.0001)
    almost_constant_returns[100] = 0.0002  # 微小差異

    # 使用新安全計算器
    safe_sharpe = safe_calculate_sharpe_ratio(
        almost_constant_returns,
        total_trades=1
    )

    print(f"安全計算器結果: {safe_sharpe:.6f}")
    assert np.isfinite(safe_sharpe), "安全計算器應返回有限數值"
    assert abs(safe_sharpe) <= 10.0, "安全計算器應返回合理範圍內的數值"

    # 案例2：模擬單次大收益
    print("創建原始問題案例：單次大收益...")
    single_big_return = np.zeros(252)
    single_big_return[150] = 1.0  # 100%單日收益

    safe_sharpe_2 = safe_calculate_sharpe_ratio(
        single_big_return,
        total_trades=1
    )

    print(f"安全計算器結果（單次大收益）: {safe_sharpe_2:.6f}")
    assert np.isfinite(safe_sharpe_2), "安全計算器應返回有限數值"
    assert abs(safe_sharpe_2) <= 10.0, "安全計算器應返回合理範圍內的數值"

    print("✅ 原始問題案例測試通過")
    return True


def generate_security_report(test_results: Dict[str, Any], vectorbt_result: Dict[str, Any]):
    """生成安全修復報告"""
    print(f"\n📋 生成安全修復報告...")
    print("=" * 80)

    report = {
        'verification_date': datetime.now().isoformat(),
        'problem_statement': '修復Sharpe比率計算中的異常值771,630,339問題',
        'solution': '實施SafeSharpeCalculator多層保護機制',
        'test_results': test_results,
        'vectorbt_integration': vectorbt_result,
        'security_measures': {
            'minimum_volatility_threshold': 0.001,
            'maximum_sharpe_ratio': 10.0,
            'minimum_trades_required': 20,
            'statistical_validation': True,
            'numerical_stability_checks': True
        },
        'validation_status': 'PASSED' if test_results['all_safe'] and vectorbt_result.get('success', False) else 'FAILED'
    }

    # 保存報告
    report_file = f'sharpe_security_fix_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"📄 報告已保存: {report_file}")
    return report


def main():
    """主函數"""
    print("🛡️ Sharpe比率安全修復驗證")
    print("🎯 目標：驗證771,630,339異常值問題是否完全解決")
    print("=" * 80)

    try:
        # 1. 創建問題測試案例
        test_cases = create_problematic_test_cases()

        # 2. 測試問題場景
        test_results = test_problematic_scenarios(test_cases)

        # 3. 測試原始問題案例
        original_case_result = test_original_problem_case()

        # 4. 測試VectorBT引擎集成
        vectorbt_result = test_vectorbt_engine_integration()

        # 5. 生成安全報告
        report = generate_security_report(test_results, vectorbt_result)

        # 6. 總結
        print(f"\n🎉 安全修復驗證完成!")
        print("=" * 80)
        print(f"總測試案例: {test_results['total_tests']}")
        print(f"所有安全: {'✅' if test_results['all_safe'] else '❌'}")
        print(f"VectorBT集成: {'✅' if vectorbt_result.get('success', False) else '❌'}")
        print(f"驗證狀態: {report['validation_status']}")

        if report['validation_status'] == 'PASSED':
            print("\n✅ 771,630,339異常值問題已完全解決!")
            print("🛡️ 系統現在具有完整的安全保護機制")
        else:
            print("\n❌ 驗證失敗，需要進一步檢查")

        return report['validation_status'] == 'PASSED'

    except Exception as e:
        print(f"\n💥 驗證過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)