"""
Test Sentiment-Technical Integration
情緒-技術分析整合測試
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_sentiment_technical_integration():
    """測試情緒-技術分析整合"""
    print("=== Testing Sentiment-Technical Integration ===")

    try:
        from analysis.sentiment_technical_integration import create_sentiment_integrator
        from models.cbsc_models import parse_warrant_sentiment_csv

        # 創建整合器
        integrator = create_sentiment_integrator()
        print("OK: Sentiment-Technical Integrator created")

        # 加載測試數據
        sentiment_path = Path("CODEX--/warrant_sentiment_daily.csv")
        if sentiment_path.exists():
            sentiment_data = parse_warrant_sentiment_csv(str(sentiment_path))
            print(f"OK: Loaded {len(sentiment_data)} sentiment records")

            # 測試情緒指標計算
            sentiment_indicators = integrator.calculate_sentiment_indicators(sentiment_data)
            print(f"OK: Sentiment indicators calculated")
            print(f"  Sentiment trend: {sentiment_indicators['sentiment_trend']}")
            print(f"  Sentiment strength: {sentiment_indicators['sentiment_strength'].name}")
            print(f"  Extreme sentiment ratio: {sentiment_indicators['extreme_sentiment_ratio']:.2%}")

            # 測試信號生成
            import pandas as pd
            import numpy as np

            # 模擬價格數據
            price_data = pd.DataFrame({
                'close': np.linspace(250, 300, 100),
                'date': pd.date_range('2025-01-01', periods=100)
            })

            signal = integrator.generate_trading_signal("0700.HK", price_data, sentiment_data)
            print(f"OK: Trading signal generated")
            print(f"  Signal type: {signal.signal_type}")
            print(f"  Combined score: {signal.combined_score:.3f}")
            print(f"  Confidence: {signal.confidence:.3f}")
            print(f"  Recommendation: {signal.recommendation}")

            # 測試回測
            backtest_result = integrator.backtest_strategy("0700.HK", price_data, sentiment_data)
            print(f"OK: Backtest completed")
            print(f"  Total return: {backtest_result['total_return']:.2%}")
            print(f"  Sharpe ratio: {backtest_result['sharpe_ratio']:.3f}")
            print(f"  Max drawdown: {backtest_result['max_drawdown']:.2%}")
            print(f"  Win rate: {backtest_result['win_rate']:.2%}")
            print(f"  Total trades: {backtest_result['total_trades']}")
            print(f"  Signals count: {backtest_result['signals_count']}")

            return True
        else:
            print(f"WARN: Sentiment data file not found: {sentiment_path}")
            return False

    except Exception as e:
        print(f"FAIL: Sentiment-Technical Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_combinations():
    """測試信號組合邏輯"""
    print("\n=== Testing Signal Combinations ===")

    try:
        from analysis.sentiment_technical_integration import SentimentTechnicalIntegrator

        integrator = SentimentTechnicalIntegrator({
            'sentiment_weight': 0.4,
            'technical_weight': 0.6
        })

        # 測試不同信號組合
        test_cases = [
            (0.8, 0.7, "Bull consensus"),
            (-0.8, -0.7, "Bear consensus"),
            (0.8, -0.7, "Divergent signals"),
            (0.3, 0.2, "Weak consensus"),
            (0.0, 0.0, "Neutral signals")
        ]

        for tech_score, sent_score, description in test_cases:
            combined = integrator.combine_signals(tech_score, sent_score)
            confidence = integrator.calculate_confidence(tech_score, sent_score, [])

            print(f"OK: {description}")
            print(f"  Technical: {tech_score:+.2f}, Sentiment: {sent_score:+.2f}")
            print(f"  Combined: {combined:+.2f}, Confidence: {confidence:.2f}")

        return True

    except Exception as e:
        print(f"FAIL: Signal combinations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("Sentiment-Technical Integration Test Starting...\n")

    # 運行測試
    test_results = []

    result1 = test_sentiment_technical_integration()
    test_results.append(("Sentiment-Technical Integration", result1))

    result2 = test_signal_combinations()
    test_results.append(("Signal Combinations", result2))

    # 總結
    print("\n=== Test Results ===")
    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All sentiment-technical integration tests passed!")
        return True
    else:
        print("WARNING: Some sentiment-technical tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)