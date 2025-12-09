#!/usr / bin / env python3
"""
Phase 4 智能信號融合系統測試
Test Phase 4: Intelligent Signal Fusion System

測試內容：
1. 單指標信號生成 (Phase 4.1)
2. 多指標權重管理 (Phase 4.2)
3. 信號衝突解決 (Phase 4.3)
4. 綜合信號生成 (Phase 4.4)
"""

import json
import logging
import time
from datetime import datetime

import numpy as np
import pandas as pd

# 配置日誌
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 導入其他必要模塊
from src.api.stock_api import get_hk_stock_data
from src.indicators.core_indicators import CoreIndicators

# 導入信號融合系統
from src.signal_fusion import (
    composite_signal_generator,
    conflict_resolver,
    get_signal_recommendations,
    get_system_performance,
    quick_signal_analysis,
    signal_generator,
    weight_manager,
)


def create_test_data(symbol: str = "0700.HK", days: int = 100) -> pd.DataFrame:
    """創建測試數據"""
    try:
        # 嘗試獲取真實數據
        data = get_hk_stock_data(symbol, days)
        if len(data) > 50:
            logger.info(f"獲取真實數據成功：{len(data)} 條記錄")
            return data
    except Exception as e:
        logger.warning(f"獲取真實數據失敗，使用模擬數據: {e}")

    # 創建模擬數據
    np.random.seed(42)
    date_range = pd.date_range(end = datetime.now(), periods = days, freq="D")

    # 模擬股價走勢（趨勢 + 隨機波動）
    price_trend = np.linspace(400, 500, days)
    random_walk = np.cumsum(np.random.normal(0, 5, days))
    close_prices = price_trend + random_walk

    # 生成OHLCV數據
    data = pd.DataFrame(
        {
            "open": close_prices + np.random.normal(0, 2, days),
            "high": close_prices + abs(np.random.normal(3, 1, days)),
            "low": close_prices - abs(np.random.normal(3, 1, days)),
            "close": close_prices,
            "volume": np.random.randint(1000000, 5000000, days),
        },
        index = date_range,
    )

    # 確保 high >= close >= low
    data["high"] = np.maximum(data["high"], data["close"])
    data["low"] = np.minimum(data["low"], data["close"])
    data["open"] = np.clip(data["open"], data["low"], data["high"])

    return data


def test_phase4_1_signal_generation():
    """測試 Phase 4.1: 單指標信號生成"""
    logger.info("🔬 測試 Phase 4.1: 單指標信號生成")

    # 創建測試數據
    data = create_test_data("0700.HK", 60)

    # 計算技術指標
    indicators_engine = CoreIndicators()
    indicators = indicators_engine.calculate_all_indicators(data)

    # 生成信號
    start_time = time.time()
    signals = signal_generator.generate_signals("0700.HK", data, indicators)
    generation_time = time.time() - start_time

    # 驗證結果
    success = True
    errors = []

    # 檢查信號數量
    if len(signals) == 0:
        success = False
        errors.append("❌ 未生成任何信號")
    else:
        logger.info(f"✅ 成功生成 {len(signals)} 個信號")

    # 檢查信號質量
    for signal in signals[:3]:  # 檢查前3個信號
        if not hasattr(signal, "signal_type"):
            success = False
            errors.append(f"❌ 信號缺少 signal_type 屬性")
        elif not hasattr(signal, "strength"):
            success = False
            errors.append(f"❌ 信號缺少 strength 屬性")
        elif not hasattr(signal, "confidence"):
            success = False
            errors.append(f"❌ 信號缺少 confidence 屬性")
        elif not (1 <= signal.strength <= 10):
            success = False
            errors.append(f"❌ 信號強度超出範圍: {signal.strength}")
        elif not (0 <= signal.confidence <= 1):
            success = False
            errors.append(f"❌ 信號置信度超出範圍: {signal.confidence}")

    # 檢查生成時間
    if generation_time > 0.1:  # 100ms
        success = False
        errors.append(f"❌ 信號生成時間過長: {generation_time * 1000:.1f}ms")
    else:
        logger.info(f"✅ 信號生成時間: {generation_time * 1000:.1f}ms")

    # 輸出結果
    if success:
        logger.info("🎉 Phase 4.1 測試通過")

        # 顯示信號摘要
        signal_types = {}
        for signal in signals:
            signal_type = signal.signal_type.value
            signal_types[signal_type] = signal_types.get(signal_type, 0) + 1

        logger.info(f"信號類型分佈: {signal_types}")

        # 顯示示例信號
        if signals:
            example_signal = signals[0]
            logger.info(
                f"示例信號: {example_signal.indicator_name} - {example_signal.signal_type.value} - 強度:{example_signal.strength:.1f} - 置信度:{example_signal.confidence:.2f}"
            )
    else:
        logger.error("❌ Phase 4.1 測試失敗")
        for error in errors:
            logger.error(error)

    return success, signals, generation_time


def test_phase4_2_weight_management():
    """測試 Phase 4.2: 多指標權重管理"""
    logger.info("⚖️ 測試 Phase 4.2: 多指標權重管理")

    success = True
    errors = []

    try:
        # 創建權重投資組合
        portfolio = weight_manager.create_portfolio("0700.HK")

        if not portfolio:
            success = False
            errors.append("❌ 無法創建權重投資組合")
        else:
            logger.info("✅ 成功創建權重投資組合")

        # 獲取權重配置
        weights = weight_manager.get_weights("0700.HK")

        if not weights:
            success = False
            errors.append("❌ 無法獲取權重配置")
        else:
            logger.info(f"✅ 獲取權重配置: {len(weights)} 個指標")

        # 檢查權重總和
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            success = False
            errors.append(f"❌ 權重總和不為1: {total_weight}")
        else:
            logger.info(f"✅ 權重總和正確: {total_weight:.3f}")

        # 模擬性能更新
        performance_data = {
            "RSI": {"accuracy": 0.7, "profitability": 0.6, "stability": 0.8},
            "MACD": {"accuracy": 0.6, "profitability": 0.8, "stability": 0.7},
            "BOLLINGER": {"accuracy": 0.8, "profitability": 0.5, "stability": 0.9},
        }

        updated_weights = weight_manager.update_weights(
            "0700.HK", performance_data, "performance_based"
        )

        if not updated_weights:
            success = False
            errors.append("❌ 權重更新失敗")
        else:
            logger.info("✅ 權重更新成功")

        # 分析權重性能
        analysis = weight_manager.analyze_weight_performance("0700.HK")

        if "error" in analysis:
            success = False
            errors.append(f"❌ 權重性能分析失敗: {analysis['error']}")
        else:
            logger.info("✅ 權重性能分析完成")

    except Exception as e:
        success = False
        errors.append(f"❌ 權重管理測試異常: {e}")

    # 輸出結果
    if success:
        logger.info("🎉 Phase 4.2 測試通過")

        if "weights" in locals():
            logger.info("當前權重配置:")
            for indicator, weight in weights.items():
                logger.info(f"  {indicator}: {weight:.3f}")
    else:
        logger.error("❌ Phase 4.2 測試失敗")
        for error in errors:
            logger.error(error)

    return success


def test_phase4_3_conflict_resolution():
    """測試 Phase 4.3: 信號衝突解決"""
    logger.info("🔧 測試 Phase 4.3: 信號衝突解決")

    success = True
    errors = []

    try:
        from src.signal_fusion.signal_generator import SignalType, TradingSignal

        # 創建測試衝突信號
        conflicting_signals = [
            TradingSignal(
                symbol="0700.HK",
                indicator_name="RSI",
                signal_type = SignalType.BUY,
                strength = 8.0,
                confidence = 0.8,
                timestamp = datetime.now(),
                data_time = pd.Timestamp.now(),
                indicator_value = 25.0,
                trigger_price = 450.0,
                trigger_conditions={},
                reason="RSI超賣",
                explanation="RSI值為25，處於超賣區域",
            ),
            TradingSignal(
                symbol="0700.HK",
                indicator_name="MACD",
                signal_type = SignalType.SELL,
                strength = 7.0,
                confidence = 0.7,
                timestamp = datetime.now(),
                data_time = pd.Timestamp.now(),
                indicator_value = -0.5,
                trigger_price = 450.0,
                trigger_conditions={},
                reason="MACD死亡交叉",
                explanation="MACD線向下穿越信號線",
            ),
            TradingSignal(
                symbol="0700.HK",
                indicator_name="BOLLINGER",
                signal_type = SignalType.BUY,
                strength = 6.0,
                confidence = 0.6,
                timestamp = datetime.now(),
                data_time = pd.Timestamp.now(),
                indicator_value = 0.1,
                trigger_price = 450.0,
                trigger_conditions={},
                reason="觸及下軌",
                explanation="價格觸及布林帶下軌",
            ),
        ]

        # 檢測衝突
        start_time = time.time()
        conflicts = conflict_resolver.detect_conflicts(conflicting_signals)
        detection_time = time.time() - start_time

        if not conflicts:
            success = False
            errors.append("❌ 未檢測到預期的衝突")
        else:
            logger.info(f"✅ 檢測到 {len(conflicts)} 個衝突")

        # 解決衝突
        start_time = time.time()
        resolutions = conflict_resolver.resolve_conflicts(
            conflicts, strategy="weighted_vote"
        )
        resolution_time = time.time() - start_time

        if not resolutions:
            success = False
            errors.append("❌ 衝突解決失敗")
        else:
            logger.info(f"✅ 成功解決 {len(resolutions)} 個衝突")

        # 檢查性能
        if detection_time > 0.05:  # 50ms
            success = False
            errors.append(f"❌ 衝突檢測時間過長: {detection_time * 1000:.1f}ms")
        else:
            logger.info(f"✅ 衝突檢測時間: {detection_time * 1000:.1f}ms")

        if resolution_time > 0.05:  # 50ms
            success = False
            errors.append(f"❌ 衝突解決時間過長: {resolution_time * 1000:.1f}ms")
        else:
            logger.info(f"✅ 衝突解決時間: {resolution_time * 1000:.1f}ms")

        # 檢查解決質量
        if resolutions:
            resolution = resolutions[0]
            if not hasattr(resolution, "final_signal_type"):
                success = False
                errors.append("❌ 解決結果缺少最終信號類型")
            elif not hasattr(resolution, "resolution_quality"):
                success = False
                errors.append("❌ 解決結果缺少質量評分")
            else:
                logger.info(f"✅ 解決質量: {resolution.resolution_quality:.2f}")

    except Exception as e:
        success = False
        errors.append(f"❌ 衝突解決測試異常: {e}")

    # 輸出結果
    if success:
        logger.info("🎉 Phase 4.3 測試通過")

        if "resolutions" in locals() and resolutions:
            resolution = resolutions[0]
            logger.info(f"解決結果: {resolution.final_signal_type.value}")
            logger.info(f"解決策略: {resolution.resolution_strategy.value}")
            logger.info(f"解決理由: {resolution.resolution_reason}")
    else:
        logger.error("❌ Phase 4.3 測試失敗")
        for error in errors:
            logger.error(error)

    return success


def test_phase4_4_composite_signal_generation():
    """測試 Phase 4.4: 綜合信號生成"""
    logger.info("🎯 測試 Phase 4.4: 綜合信號生成")

    success = True
    errors = []

    try:
        # 創建測試數據
        data = create_test_data("0700.HK", 100)

        # 計算技術指標
        indicators_engine = CoreIndicators()
        indicators = indicators_engine.calculate_all_indicators(data)

        # 生成綜合信號
        start_time = time.time()
        composite_signal = composite_signal_generator.generate_composite_signal(
            symbol="0700.HK", data = data, indicators = indicators
        )
        generation_time = time.time() - start_time

        # 驗證綜合信號
        if not composite_signal:
            success = False
            errors.append("❌ 未生成綜合信號")
        else:
            logger.info("✅ 成功生成綜合信號")

        # 檢查信號屬性
        required_attributes = [
            "signal_type",
            "strength",
            "confidence",
            "quality_score",
            "risk_level",
            "decision_reason",
            "component_signals",
        ]

        for attr in required_attributes:
            if not hasattr(composite_signal, attr):
                success = False
                errors.append(f"❌ 綜合信號缺少屬性: {attr}")

        # 檢查質量評分
        if composite_signal and not (0 <= composite_signal.quality_score <= 100):
            success = False
            errors.append(f"❌ 質量評分超出範圍: {composite_signal.quality_score}")

        # 檢查生成時間
        if generation_time > 0.1:  # 100ms
            success = False
            errors.append(f"❌ 綜合信號生成時間過長: {generation_time * 1000:.1f}ms")
        else:
            logger.info(f"✅ 綜合信號生成時間: {generation_time * 1000:.1f}ms")

        # 生成信號報告
        if composite_signal:
            start_time = time.time()
            report = composite_signal_generator.generate_signal_report(
                composite_signal, data
            )
            report_time = time.time() - start_time

            if not report:
                success = False
                errors.append("❌ 信號報告生成失敗")
            else:
                logger.info(f"✅ 信號報告生成時間: {report_time * 1000:.1f}ms")

    except Exception as e:
        success = False
        errors.append(f"❌ 綜合信號生成測試異常: {e}")

    # 輸出結果
    if success:
        logger.info("🎉 Phase 4.4 測試通過")

        if "composite_signal" in locals() and composite_signal:
            logger.info(f"綜合信號摘要:")
            logger.info(f"  信號類型: {composite_signal.signal_type.value}")
            logger.info(f"  強度: {composite_signal.strength:.1f}/10")
            logger.info(f"  置信度: {composite_signal.confidence:.1%}")
            logger.info(f"  質量評分: {composite_signal.quality_score:.1f}/100")
            logger.info(f"  風險等級: {composite_signal.risk_level.value}")
            logger.info(f"  組成信號數: {len(composite_signal.component_signals)}")
            logger.info(f"  決策理由: {composite_signal.decision_reason}")

            if "report" in locals() and report:
                logger.info(f"信號報告:")
                logger.info(f"  技術分析: {len(report.technical_analysis)} 項")
                logger.info(f"  風險分析: {len(report.risk_analysis)} 項")
                logger.info(f"  建議數量: {len(report.recommendations)} 項")
    else:
        logger.error("❌ Phase 4.4 測試失敗")
        for error in errors:
            logger.error(error)

    return success, composite_signal if "composite_signal" in locals() else None


def test_integration():
    """集成測試"""
    logger.info("🔄 進行集成測試")

    success = True
    errors = []

    try:
        # 創建測試數據
        data = create_test_data("0700.HK", 100)

        # 計算技術指標
        indicators_engine = CoreIndicators()
        indicators = indicators_engine.calculate_all_indicators(data)

        # 使用快速分析功能
        start_time = time.time()
        analysis_result = quick_signal_analysis("0700.HK", data, indicators)
        total_time = time.time() - start_time

        if not analysis_result:
            success = False
            errors.append("❌ 快速分析失敗")
        else:
            logger.info("✅ 快速分析成功")

        # 檢查完整時間
        if total_time > 0.2:  # 200ms
            success = False
            errors.append(f"❌ 集成測試時間過長: {total_time * 1000:.1f}ms")
        else:
            logger.info(f"✅ 集成測試時間: {total_time * 1000:.1f}ms")

        # 獲取建議
        if (
            "composite_signal" in analysis_result
            and analysis_result["composite_signal"]
        ):
            recommendations = get_signal_recommendations(
                "0700.HK", analysis_result["composite_signal"]
            )

            if not recommendations:
                success = False
                errors.append("❌ 無法生成建議")
            else:
                logger.info(f"✅ 生成 {len(recommendations)} 條建議")

        # 獲取系統性能
        performance = get_system_performance()

        if not performance:
            success = False
            errors.append("❌ 無法獲取系統性能")
        else:
            logger.info("✅ 系統性能統計獲取成功")

    except Exception as e:
        success = False
        errors.append(f"❌ 集成測試異常: {e}")

    # 輸出結果
    if success:
        logger.info("🎉 集成測試通過")

        if "performance" in locals() and performance:
            logger.info("系統性能統計:")
            for component, stats in performance.items():
                logger.info(f"  {component}:")
                for key, value in stats.items():
                    if isinstance(value, float):
                        logger.info(f"    {key}: {value:.3f}")
                    else:
                        logger.info(f"    {key}: {value}")
    else:
        logger.error("❌ 集成測試失敗")
        for error in errors:
            logger.error(error)

    return success


def run_all_tests():
    """運行所有測試"""
    logger.info("🚀 開始 Phase 4 智能信號融合系統完整測試")
    logger.info("=" * 60)

    # 記錄測試結果
    test_results = {
        "phase4_1": {"name": "單指標信號生成", "success": False, "time": 0},
        "phase4_2": {"name": "多指標權重管理", "success": False, "time": 0},
        "phase4_3": {"name": "信號衝突解決", "success": False, "time": 0},
        "phase4_4": {"name": "綜合信號生成", "success": False, "time": 0},
        "integration": {"name": "集成測試", "success": False, "time": 0},
    }

    total_start_time = time.time()

    # 運行各階段測試
    try:
        success, signals, gen_time = test_phase4_1_signal_generation()
        test_results["phase4_1"]["success"] = success
        test_results["phase4_1"]["time"] = gen_time
    except Exception as e:
        logger.error(f"Phase 4.1 測試異常: {e}")

    try:
        success = test_phase4_2_weight_management()
        test_results["phase4_2"]["success"] = success
    except Exception as e:
        logger.error(f"Phase 4.2 測試異常: {e}")

    try:
        success = test_phase4_3_conflict_resolution()
        test_results["phase4_3"]["success"] = success
    except Exception as e:
        logger.error(f"Phase 4.3 測試異常: {e}")

    try:
        success, composite_signal = test_phase4_4_composite_signal_generation()
        test_results["phase4_4"]["success"] = success
        test_results["phase4_4"]["time"] = 0
    except Exception as e:
        logger.error(f"Phase 4.4 測試異常: {e}")

    try:
        success = test_integration()
        test_results["integration"]["success"] = success
    except Exception as e:
        logger.error(f"集成測試異常: {e}")

    total_time = time.time() - total_start_time

    # 生成測試報告
    logger.info("=" * 60)
    logger.info("📊 測試結果摘要")
    logger.info("=" * 60)

    passed_tests = 0
    total_tests = len(test_results)

    for phase, result in test_results.items():
        status = "✅ 通過" if result["success"] else "❌ 失敗"
        time_info = f"({result['time']*1000:.1f}ms)" if result["time"] > 0 else ""
        logger.info(f"{result['name']}: {status} {time_info}")

        if result["success"]:
            passed_tests += 1

    # 總體評估
    logger.info("-" * 60)
    success_rate = (passed_tests / total_tests) * 100
    logger.info(f"總體成功率: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    logger.info(f"總測試時間: {total_time * 1000:.1f}ms")

    if success_rate >= 80:
        logger.info("🎉 Phase 4 智能信號融合系統測試成功完成！")
        logger.info("✅ 系統已準備投入生產使用")
    else:
        logger.error("❌ Phase 4 測試未完全通過，需要進行修復")
        logger.error("⚠️ 請檢查失敗的測試並修復相關問題")

    # 生成測試報告文件
    report_data = {
        "test_time": datetime.now().isoformat(),
        "total_time_ms": total_time * 1000,
        "success_rate": success_rate,
        "passed_tests": passed_tests,
        "total_tests": total_tests,
        "test_results": {
            phase: {
                "name": result["name"],
                "success": result["success"],
                "time_ms": result["time"] * 1000 if result["time"] > 0 else None,
            }
            for phase, result in test_results.items()
        },
        "system_performance": get_system_performance(),
    }

    report_file = f"phase4_signal_fusion_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        with open(report_file, "w", encoding="utf - 8") as f:
            json.dump(report_data, f, indent = 2, ensure_ascii = False)
        logger.info(f"📄 測試報告已保存: {report_file}")
    except Exception as e:
        logger.error(f"❌ 保存測試報告失敗: {e}")

    return success_rate >= 80


if __name__ == "__main__":
    # 檢查依賴
    try:
        import numpy as np
        import pandas as pd

        logger.info("✅ 依賴檢查通過")
    except ImportError as e:
        logger.error(f"❌ 依賴檢查失敗: {e}")
        logger.error("請確保已安裝所需依賴: pip install pandas numpy")
        exit(1)

    # 運行測試
    success = run_all_tests()

    # 返回結果
    exit(0 if success else 1)
