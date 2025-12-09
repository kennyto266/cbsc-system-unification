#!/usr/bin/env python3
"""
測試集成交易系統
Test Integrated Trading System
"""

import sys
import os
import asyncio
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from trading.integrated_quantitative_trader import (
        IntegratedQuantitativeTrader,
        TradingSignal,
        SignalType,
        run_comprehensive_trading_analysis
    )
    from indicators.advanced_ta_signals import AdvancedTechnicalSignals
    from data.historical_data_extender import extend_data_records
    from api.stock_api import get_hk_stock_data

    print("=" * 80)
    print("Integrated Trading System Test")
    print("集成交易系統測試")
    print("=" * 80)
    print()

    # 測試1: 單個信號分析
    print("=== Test 1: Single Signal Analysis ===")

    trader = IntegratedQuantitativeTrader(initial_capital=50000)
    print(f"Trader initialized with capital: ${trader.initial_capital:,.2f}")

    # 分析0700.HK
    print("Analyzing 0700.HK...")
    signal = await trader.analyze_symbol('0700.HK')

    if signal:
        print(f"[OK] Signal generated for {signal.symbol}")
        print(f"  Signal Type: {signal.signal_type.value}")
        print(f"  Confidence: {signal.confidence:.3f}")
        print(f"  Signal Strength: {signal.signal_strength:.3f}")
        print(f"  Price: ${signal.price:.2f}")
        print(f"  Risk Score: {signal.risk_score:.3f}")
        print(f"  Expected Return: {signal.expected_return:.1%}")
        print(f"  Time Horizon: {signal.time_horizon}")
        print(f"  Timestamp: {signal.timestamp}")
    else:
        print("[FAIL] No signal generated")

    print()

    # 測試2: 交易決策執行
    print("=== Test 2: Trading Decision Execution ===")

    if signal:
        trade_result = await trader.execute_trading_decision(signal)

        if trade_result:
            print(f"[OK] Trade executed successfully")
            print(f"  Action: {trade_result['action']}")
            print(f"  Symbol: {trade_result['symbol']}")
            print(f"  Quantity: {trade_result['quantity']}")
            print(f"  Price: ${trade_result['price']:.2f}")
            print(f"  Total Cost: ${trade_result['total_cost']:.2f}")
            print(f"  Signal Confidence: {trade_result['signal_confidence']:.3f}")

            if trade_result['action'] == 'SELL':
                print(f"  Realized PnL: ${trade_result['realized_pnl']:.2f}")
                print(f"  PnL %: {trade_result['pnl_percentage']:.1f}%")
        else:
            print("[INFO] No trade executed (signal confidence too low or other constraints)")

    print()

    # 測試3: 多股票交易週期
    print("=== Test 3: Multi-Stock Trading Cycle ===")

    # 測試多個港股
    test_symbols = ['0700.HK', '0941.HK', '1398.HK']
    print(f"Running trading cycle for {len(test_symbols)} symbols...")

    cycle_results = await trader.run_trading_cycle(test_symbols)

    print(f"[OK] Trading cycle completed")
    print(f"  Symbols Analyzed: {cycle_results['symbols_analyzed']}")
    print(f"  Signals Generated: {cycle_results['signals_generated']}")
    print(f"  Trades Executed: {cycle_results['trades_executed']}")
    print(f"  Successful Trades: {cycle_results['successful_trades']}")
    print(f"  Total PnL: ${cycle_results['total_pnl']:.2f}")
    print(f"  Capital Utilization: {cycle_results['capital_utilization']:.1%}")
    print(f"  Open Positions: {cycle_results['open_positions']}")

    if cycle_results['errors']:
        print(f"  Errors: {len(cycle_results['errors'])}")
        for error in cycle_results['errors'][:3]:  # 只顯示前3個錯誤
            print(f"    - {error}")

    print()

    # 測試4: 性能指標計算
    print("=== Test 4: Performance Metrics ===")

    metrics = trader.get_performance_metrics()
    print(f"[OK] Performance metrics calculated")
    print(f"  Total Trades: {metrics['total_trades']}")
    print(f"  Win Rate: {metrics['win_rate']:.1%}")
    print(f"  Total Return: {metrics['total_return']:.2f}%")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    print(f"  Max Drawdown: {metrics['max_drawdown']:.1%}")
    print(f"  Current Capital: ${metrics['current_capital']:,.2f}")
    print(f"  Open Positions: {metrics['open_positions']}")

    print()

    # 測試5: 持倉狀態檢查
    print("=== Test 5: Portfolio Status ===")

    if trader.positions:
        print(f"[OK] Current positions: {len(trader.positions)}")
        for symbol, position in trader.positions.items():
            print(f"  {symbol}:")
            print(f"    Quantity: {position.quantity}")
            print(f"    Entry Price: ${position.entry_price:.2f}")
            print(f"    Current Price: ${position.current_price:.2f}")
            print(f"    Unrealized PnL: ${position.unrealized_pnl:.2f}")
            print(f"    PnL %: {((position.current_price - position.entry_price) / position.entry_price) * 100:.1f}%")
            print(f"    Holding Period: {(datetime.now() - position.entry_date).days} days")
    else:
        print("[INFO] No open positions")

    print()

    # 測試6: 歷史數據擴展驗證
    print("=== Test 6: Historical Data Extension Verification ===")

    # 創建測試數據
    test_data = []
    for i in range(10):
        test_data.append({
            'date': f'2025-01-{(i+1):02d}',
            'price': 100.0 + i * 0.5 + (i % 3 - 1) * 0.2,
            'volume': 1000000 + i * 10000,
            'high': 101.0 + i * 0.5,
            'low': 99.0 + i * 0.5
        })

    print(f"Original data: {len(test_data)} records")

    # 測試數據擴展
    extension_result = extend_data_records(test_data, 1000, 'hybrid_approach')

    if extension_result.get('success'):
        extended_data = extension_result['data']
        print(f"[OK] Data extension successful: {len(test_data)} -> {len(extended_data)} records")
        print(f"  Extension ratio: {extension_result['extension_ratio']:.2f}x")
        print(f"  Method used: {extension_result['method']}")
    else:
        print(f"[FAIL] Data extension failed: {extension_result.get('error', 'Unknown error')}")

    print()

    # 測試7: 信號生成性能測試
    print("=== Test 7: Signal Generation Performance ===")

    import time

    # 測試單個股票信號生成時間
    start_time = time.time()
    test_signals = []

    for symbol in ['0700.HK']:  # 只測試一個以加快測試
        single_start = time.time()
        signal = await trader.analyze_symbol(symbol)
        single_end = time.time()

        if signal:
            test_signals.append(signal)
            print(f"  {symbol}: {single_end - single_start:.3f}s")

    total_time = time.time() - start_time
    print(f"[OK] Performance test completed")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Average time per signal: {total_time / len(test_signals):.3f}s")
    print(f"  Signals per second: {len(test_signals) / total_time:.1f}")

    print()

    # 測試8: 配置驗證
    print("=== Test 8: Configuration Verification ===")

    config = trader.config
    print(f"[OK] Configuration loaded")
    print(f"  Max Position Size: {config['max_position_size']:.1%}")
    print(f"  Stop Loss: {config['stop_loss_pct']:.1%}")
    print(f"  Take Profit: {config['take_profit_pct']:.1%}")
    print(f"  Min Signal Confidence: {config['min_signal_confidence']:.1f}")
    print(f"  Max Positions: {config['max_positions']}")
    print(f"  Rebalance Frequency: {config['rebalance_frequency']}")
    print(f"  Risk Limit: {config['risk_limit']:.1%}")

    print()

    # 測試9: 異存完整性檢查
    print("=== Test 9: Data Integrity Checks ===")

    integrity_checks = {
        'total_trades_match': len(trader.trade_history) == metrics['total_trades'],
        'capital_consistency': trader.current_capital >= 0,
        'position_quantity_valid': all(p.quantity > 0 for p in trader.positions.values()),
        'signal_timestamps_valid': all(
            isinstance(s.timestamp, datetime) for s in trader.signals_history
        )
    }

    passed_checks = sum(1 for check in integrity_checks.values() if check)
    total_checks = len(integrity_checks)

    print(f"[OK] Data integrity checks: {passed_checks}/{total_checks} passed")

    for check_name, passed in integrity_checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {check_name}: {status}")

    print()

    # 測試10: 綜合評估報告
    print("=== Test 10: Comprehensive Assessment ===")

    assessment = {
        'trading_system_status': 'OPERATIONAL' if all(integrity_checks.values()) else 'WARNING',
        'performance_grade': self._calculate_performance_grade(metrics),
        'signal_quality': 'GOOD' if len(test_signals) > 0 and all(s.confidence > 0.5 for s in test_signals) else 'NEEDS_IMPROVEMENT',
        'risk_management': 'ADEQUATE' if trader.config['risk_limit'] <= 0.05 else 'HIGH_RISK',
        'recommendations': self._generate_recommendations(metrics, cycle_results)
    }

    print(f"[OK] Comprehensive assessment completed")
    print(f"  System Status: {assessment['trading_system_status']}")
    print(f"  Performance Grade: {assessment['performance_grade']}")
    print(f"  Signal Quality: {assessment['signal_quality']}")
    print(f"  Risk Management: {assessment['risk_management']}")
    print(f"  Recommendations: {len(assessment['recommendations'])}")

    for i, rec in enumerate(assessment['recommendations'][:3], 1):
        print(f"    {i}. {rec}")

    print()

    # 保存測試結果
    test_results = {
        'test_timestamp': datetime.now().isoformat(),
        'trading_metrics': metrics,
        'cycle_results': cycle_results,
        'assessment': assessment,
        'integrity_checks': integrity_checks,
        'configuration': config
    }

    results_file = f"integrated_trading_system_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)

    print(f"Test results saved to: {results_file}")

    def _calculate_performance_grade(self, metrics: Dict) -> str:
        """計算性能評級"""
        if metrics['total_trades'] == 0:
            return 'N/A'

        score = 0

        # 勝率評分
        if metrics['win_rate'] > 0.6:
            score += 30
        elif metrics['win_rate'] > 0.4:
            score += 20
        else:
            score += 10

        # 總回報評分
        if metrics['total_return'] > 10:
            score += 30
        elif metrics['total_return'] > 0:
            score += 20
        else:
            score += 10

        # Sharpe比率評分
        if metrics['sharpe_ratio'] > 1.5:
            score += 25
        elif metrics['sharpe_ratio'] > 0.5:
            score += 15
        else:
            score += 5

        # 最大回撤評分（回撤越小越好）
        if abs(metrics['max_drawdown']) < 0.05:
            score += 15
        elif abs(metrics['max_drawdown']) < 0.10:
            score += 10
        else:
            score += 5

        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C'
        else:
            return 'D'

    def _generate_recommendations(self, metrics: Dict, cycle_results: Dict) -> List[str]:
        """生成建議"""
        recommendations = []

        if metrics['win_rate'] < 0.4:
            recommendations.append("考慮提高信號質量門檻，改善選股策略")

        if metrics['sharpe_ratio'] < 0.5:
            recommendations.append("優化風險管理，調整持倉比例")

        if metrics['max_drawdown'] < -0.10:
            recommendations.append("加強止損機制，控制最大回撤")

        if cycle_results['capital_utilization'] < 0.5:
            recommendations.append("可考慮增加持倉數量以提高資金利用率")

        if len(cycle_results.get('errors', [])) > 0:
            recommendations.append("修復數據獲取和分析中的錯誤")

        if not recommendations:
            recommendations.append("系統運行良好，繼續監控性能表現")

        return recommendations

except ImportError as e:
    print(f"[IMPORT ERROR] {e}")
    print("Make sure all required modules are available")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Integrated Trading System Test Complete")
print("集成交易系統測試完成")
print("=" * 80)