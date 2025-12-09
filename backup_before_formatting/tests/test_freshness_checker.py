"""
数据新鲜度检查器测试套件

测试所有核心功能：
- 数据延迟监控
- 更新频率分析
- 缺失数据检测
- 告警管理
- 新鲜度评分
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_freshness_checker")

# 导入被测试模块
from src.data.freshness_checker import (
    DataLatencyMonitor,
    FreshnessAlertManager,
    FreshnessChecker,
    FreshnessResult,
    MissingDataDetector,
    UpdateFrequencyAnalyzer,
    UpdateStatus,
    check_data_freshness,
    create_freshness_checker,
)


class TestDataLatencyMonitor:
    """数据延迟监控器测试"""

    @pytest.fixture
    def monitor(self):
        """创建监控器实例"""
        config = {
            "thresholds": {
                "real_time": 0.5,
                "daily": 2.0,
                "weekly": 24.0,
                "monthly": 72.0,
            }
        }
        return DataLatencyMonitor(config)

    def test_up_to_date_status(self, monitor):
        """测试最新数据状态"""
        last_update = datetime.utcnow() - timedelta(minutes=30)
        result = monitor.check_update_latency(last_update, "real_time")

        assert result["status"] == UpdateStatus.UP_TO_DATE
        assert result["is_within_threshold"] is True
        assert result["severity"] == "none"
        assert 0 <= result["latency_hours"] <= 1.0

    def test_stale_status(self, monitor):
        """测试数据陈旧状态"""
        # 创建超过阈值的更新
        last_update = datetime.utcnow() - timedelta(hours=3)
        result = monitor.check_update_latency(last_update, "daily")

        assert result["status"] in [UpdateStatus.STALE, UpdateStatus.VERY_STALE]
        assert result["latency_hours"] >= 3.0
        assert result["is_within_threshold"] is False

    def test_unknown_status(self, monitor):
        """测试未知状态"""
        result = monitor.check_update_latency(None, "daily")

        assert result["status"] == UpdateStatus.UNKNOWN
        assert result["severity"] == "critical"
        assert result["is_within_threshold"] is False

    def test_multiple_sources_monitoring(self, monitor):
        """测试多源监控"""
        sources = {
            "source1": datetime.utcnow() - timedelta(hours=1),
            "source2": datetime.utcnow() - timedelta(hours=2),
            "source3": datetime.utcnow() - timedelta(minutes=30),
        }

        result = monitor.monitor_multiple_sources(sources, "daily")

        assert "overall_status" in result
        assert "stale_sources" in result
        assert "freshness_scores" in result
        assert isinstance(result["stale_sources"], list)

    def test_custom_thresholds(self):
        """测试自定义阈值"""
        config = {"thresholds": {"daily": 1.0}}
        monitor = DataLatencyMonitor(config)

        # 45分钟前的数据应该仍然新鲜（阈值是1小时）
        last_update = datetime.utcnow() - timedelta(minutes=45)
        result = monitor.check_update_latency(last_update, "daily")

        assert result["status"] == UpdateStatus.UP_TO_DATE

    def test_error_handling(self, monitor):
        """测试错误处理"""
        # 提供无效的datetime对象
        with patch.object(monitor, "thresholds", {"daily": 24.0}):
            result = monitor.check_update_latency("invalid", "daily")
            assert result["status"] == UpdateStatus.ERROR


class TestUpdateFrequencyAnalyzer:
    """更新频率分析器测试"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return UpdateFrequencyAnalyzer()

    def test_daily_pattern_detection(self, analyzer):
        """测试日级模式检测"""
        # 创建每天更新的时间戳
        base_date = datetime(2023, 1, 1)
        timestamps = [base_date + timedelta(days=i) for i in range(10)]

        result = analyzer.analyze_update_pattern(timestamps)

        assert result["pattern_type"] == "daily"
        assert result["average_interval"] > 20 and result["average_interval"] < 30
        assert result["is_regular"] is True
        assert result["consistency_score"] >= 0.7

    def test_weekly_pattern_detection(self, analyzer):
        """测试周级模式检测"""
        # 创建每周更新的时间戳
        base_date = datetime(2023, 1, 1)
        timestamps = [base_date + timedelta(weeks=i) for i in range(5)]

        result = analyzer.analyze_update_pattern(timestamps)

        assert result["pattern_type"] == "weekly"
        assert result["average_interval"] > 150 and result["average_interval"] < 180
        assert result["is_regular"] is True

    def test_irregular_pattern_detection(self, analyzer):
        """测试不规则模式检测"""
        # 创建不规则的时间戳
        timestamps = [
            datetime(2023, 1, 1),
            datetime(2023, 1, 2),  # 1天
            datetime(2023, 1, 10),  # 8天
            datetime(2023, 1, 11),  # 1天
            datetime(2023, 1, 20),  # 9天
        ]

        result = analyzer.analyze_update_pattern(timestamps)

        assert result["consistency_score"] < 0.7
        assert len(result["anomalies"]) > 0
        assert result["is_regular"] is False

    def test_anomaly_detection(self, analyzer):
        """测试异常检测"""
        # 创建一个异常长的间隔
        timestamps = [
            datetime(2023, 1, 1),
            datetime(2023, 1, 2),  # 1天
            datetime(2023, 1, 3),  # 1天
            datetime(2023, 1, 15),  # 12天（异常长）
        ]

        result = analyzer.analyze_update_pattern(timestamps)

        assert len(result["anomalies"]) > 0
        assert any(a["type"] == "unusually_long_interval" for a in result["anomalies"])

    def test_compliance_check(self, analyzer):
        """测试合规性检查"""
        # 创建日级更新
        base_date = datetime(2023, 1, 1)
        timestamps = [base_date + timedelta(days=i) for i in range(10)]

        result = analyzer.compare_with_expected(timestamps, "daily")

        assert result["is_compliant"] is True
        assert result["compliance_score"] >= 0.7
        assert result["expected_interval"] > 0

    def test_insufficient_data(self, analyzer):
        """测试数据不足情况"""
        timestamps = [datetime(2023, 1, 1)]  # 只有一个时间戳

        result = analyzer.analyze_update_pattern(timestamps)

        assert result["average_interval"] == 0.0
        assert result["is_regular"] is False

    def test_empty_timestamps(self, analyzer):
        """测试空时间戳列表"""
        result = analyzer.analyze_update_pattern([])

        assert result["average_interval"] == 0.0
        assert result["consistency_score"] == 0.0
        assert result["is_regular"] is False


class TestMissingDataDetector:
    """缺失数据检测器测试"""

    @pytest.fixture
    def detector(self):
        """创建检测器实例"""
        return MissingDataDetector()

    def test_no_missing_data(self):
        """测试无缺失数据"""
        detector = MissingDataDetector()

        # 创建连续日期的数据
        dates = pd.date_range("2023 - 01 - 01", periods=10, freq="D")
        data = pd.DataFrame({"date": dates, "value": range(10)})

        result = detector.detect_data_gaps(data, "daily")

        assert result["has_gaps"] is False
        assert result["gap_count"] == 0
        assert result["completeness"] == 1.0

    def test_detect_data_gaps(self):
        """测试检测数据缺口"""
        detector = MissingDataDetector()

        # 创建有缺口的日期
        dates = pd.date_range("2023 - 01 - 01", periods=10, freq="D")
        missing_dates = [dates[3], dates[4]]  # 缺失两天
        valid_dates = dates[~dates.isin(missing_dates)]

        data = pd.DataFrame({"date": valid_dates, "value": range(len(valid_dates))})

        result = detector.detect_data_gaps(data, "daily")

        assert result["has_gaps"] is True
        assert result["gap_count"] > 0
        assert result["completeness"] < 1.0
        assert len(result["gap_periods"]) > 0

    def test_weekly_gap_detection(self):
        """测试周级数据缺口检测"""
        detector = MissingDataDetector()

        # 创建周级数据，有缺口
        dates = pd.date_range("2023 - 01 - 01", periods=20, freq="W")
        missing_weeks = dates[5:8]  # 缺失3周
        valid_weeks = dates[~dates.isin(missing_weeks)]

        data = pd.DataFrame({"date": valid_weeks, "value": range(len(valid_weeks))})

        result = detector.detect_data_gaps(data, "weekly")

        assert result["has_gaps"] is True
        assert result["gap_count"] > 0

    def test_estimate_expected_count(self, detector):
        """测试估算预期数据点数量"""
        dates = pd.date_range("2023 - 01 - 01", periods=10, freq="D")

        expected = detector.estimate_expected_data_count(dates, "daily")

        assert expected > 0
        assert isinstance(expected, int)

    def test_empty_data(self, detector):
        """测试空数据"""
        empty_data = pd.DataFrame()

        result = detector.detect_data_gaps(empty_data, "daily")

        assert result["has_gaps"] is True
        assert result["completeness"] == 0.0
        assert result["gap_count"] == 0


class TestFreshnessAlertManager:
    """新鲜度告警管理器测试"""

    @pytest.fixture
    def alert_manager(self):
        """创建告警管理器实例"""
        config = {
            "alert_rules": {
                UpdateStatus.UP_TO_DATE: {"enabled": False, "channels": []},
                UpdateStatus.SLIGHTLY_STALE: {"enabled": True, "channels": ["log"]},
                UpdateStatus.STALE: {"enabled": True, "channels": ["log", "email"]},
                UpdateStatus.VERY_STALE: {
                    "enabled": True,
                    "channels": ["log", "email", "webhook"],
                },
            },
            "alert_cooldown": 3600,
        }
        return FreshnessAlertManager(config)

    @pytest.mark.asyncio
    async def test_log_alert(self, alert_manager):
        """测试日志告警"""
        result = FreshnessResult(
            symbol="0700.HK",
            timestamp=datetime.utcnow(),
            last_update=datetime.utcnow() - timedelta(hours=3),
            status=UpdateStatus.SLIGHTLY_STALE,
            age_hours=3.0,
            expected_frequency="daily",
            freshness_score=0.5,
            recommendations=["检查数据源"],
        )

        alerts = await alert_manager.check_and_alert(result)

        assert len(alerts) > 0
        assert alerts[0]["severity"] in ["low", "medium"]
        assert "log" in [a["channel"] for a in alerts[0]["actions_taken"]]

    @pytest.mark.asyncio
    async def test_critical_alert(self, alert_manager):
        """测试严重告警"""
        result = FreshnessResult(
            symbol="0700.HK",
            timestamp=datetime.utcnow(),
            last_update=datetime.utcnow() - timedelta(hours=5),
            status=UpdateStatus.VERY_STALE,
            age_hours=5.0,
            expected_frequency="daily",
            freshness_score=0.2,
            recommendations=["立即检查系统"],
        )

        alerts = await alert_manager.check_and_alert(result)

        assert len(alerts) > 0
        assert alerts[0]["severity"] == "high"
        assert len(alerts[0]["actions_taken"]) >= 2  # 多个告警通道

    @pytest.mark.asyncio
    async def test_no_alert_for_up_to_date(self, alert_manager):
        """测试最新数据不告警"""
        result = FreshnessResult(
            symbol="0700.HK",
            timestamp=datetime.utcnow(),
            last_update=datetime.utcnow() - timedelta(minutes=30),
            status=UpdateStatus.UP_TO_DATE,
            age_hours=0.5,
            expected_frequency="daily",
            freshness_score=0.95,
            recommendations=[],
        )

        alerts = await alert_manager.check_and_alert(result)

        # UP_TO_DATE 默认不发送告警
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_error_status_alert(self, alert_manager):
        """测试错误状态告警"""
        result = FreshnessResult(
            symbol="0700.HK",
            timestamp=datetime.utcnow(),
            last_update=None,
            status=UpdateStatus.ERROR,
            age_hours=0.0,
            expected_frequency="unknown",
            freshness_score=0.0,
            recommendations=["检查系统状态"],
        )

        alerts = await alert_manager.check_and_alert(result)

        assert len(alerts) > 0
        assert alerts[0]["severity"] == "critical"

    def test_alert_history(self, alert_manager):
        """测试告警历史"""
        # 模拟添加告警历史
        alert_manager.alert_history = [
            {"timestamp": "2023 - 01 - 01", "symbol": "0700.HK"},
            {"timestamp": "2023 - 01 - 02", "symbol": "0388.HK"},
        ]

        assert len(alert_manager.alert_history) == 2
        assert alert_manager.alert_history[0]["symbol"] == "0700.HK"

    def test_severity_mapping(self, alert_manager):
        """测试严重程度映射"""
        assert alert_manager._get_severity(UpdateStatus.UP_TO_DATE) == "info"
        assert alert_manager._get_severity(UpdateStatus.SLIGHTLY_STALE) == "low"
        assert alert_manager._get_severity(UpdateStatus.STALE) == "medium"
        assert alert_manager._get_severity(UpdateStatus.VERY_STALE) == "high"
        assert alert_manager._get_severity(UpdateStatus.ERROR) == "critical"

    def test_alert_message_generation(self, alert_manager):
        """测试告警消息生成"""
        result = FreshnessResult(
            symbol="0700.HK",
            timestamp=datetime.utcnow(),
            last_update=datetime.utcnow() - timedelta(hours=2),
            status=UpdateStatus.STALE,
            age_hours=2.0,
            expected_frequency="daily",
            freshness_score=0.6,
            recommendations=["检查数据源"],
        )

        message = alert_manager._generate_alert_message(result)

        assert "0700.HK" in message
        assert "stale" in message.lower()
        assert "检查数据源" in message


class TestFreshnessChecker:
    """数据新鲜度检查器综合测试"""

    @pytest.fixture
    def checker(self):
        """创建检查器实例"""
        config = {
            "latency": {"thresholds": {"daily": 4.0}},
            "alert": {
                "alert_rules": {
                    UpdateStatus.SLIGHTLY_STALE: {"enabled": True, "channels": ["log"]},
                    UpdateStatus.STALE: {"enabled": True, "channels": ["log"]},
                }
            },
        }
        return FreshnessChecker(config)

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        dates = pd.date_range("2023 - 01 - 01", periods=50, freq="D")
        return pd.DataFrame(
            {
                "date": dates,
                "open": 100 + np.random.normal(0, 2, 50),
                "high": 102 + np.random.normal(0, 2, 50),
                "low": 98 + np.random.normal(0, 2, 50),
                "close": 101 + np.random.normal(0, 2, 50),
                "volume": 1000 + np.random.randint(0, 500, 50),
            }
        )

    @pytest.mark.asyncio
    async def test_check_freshness_with_data(self, checker, sample_data):
        """测试带数据的检查"""
        last_update = datetime.utcnow() - timedelta(hours=1)
        result = await checker.check("0700.HK", sample_data, last_update)

        assert isinstance(result, FreshnessResult)
        assert result.symbol == "0700.HK"
        assert result.last_update is not None
        assert result.freshness_score >= 0.0
        assert result.freshness_score <= 1.0
        assert isinstance(result.recommendations, list)
        assert isinstance(result.anomalies, list)

    @pytest.mark.asyncio
    async def test_check_freshness_without_data(self, checker):
        """测试无数据的检查"""
        last_update = datetime.utcnow() - timedelta(hours=2)
        result = await checker.check("0700.HK", None, last_update)

        assert isinstance(result, FreshnessResult)
        assert result.symbol == "0700.HK"
        assert result.status in [UpdateStatus.UP_TO_DATE, UpdateStatus.SLIGHTLY_STALE]

    @pytest.mark.asyncio
    async def test_check_freshness_no_last_update(self, checker, sample_data):
        """测试无最后更新时间"""
        result = await checker.check("0700.HK", sample_data, None)

        assert isinstance(result, FreshnessResult)
        # 应该从数据中提取时间
        assert result.last_update is not None

    @pytest.mark.asyncio
    async def test_error_handling(self, checker):
        """测试错误处理"""
        # 传入无效数据
        with patch.object(
            checker, "_extract_last_update", side_effect=Exception("Test error")
        ):
            result = await checker.check("0700.HK", "invalid", None)

        assert isinstance(result, FreshnessResult)
        assert result.status == UpdateStatus.ERROR
        assert len(result.anomalies) > 0

    def test_get_expected_frequency(self, checker):
        """测试获取预期频率"""
        # 预设频率
        freq = checker._get_expected_frequency("0700.HK")
        assert freq == "daily"

        # 默认频率
        freq = checker._get_expected_frequency("UNKNOWN")
        assert freq == "daily"

    def test_extract_last_update(self, checker):
        """测试提取最后更新时间"""
        # 从列中提取
        data = pd.DataFrame(
            {
                "date": pd.date_range("2023 - 01 - 01", periods=10, freq="D"),
                "value": range(10),
            }
        )
        last_update = checker._extract_last_update(data)
        assert last_update is not None

        # 从索引中提取
        data_indexed = data.set_index("date")
        last_update = checker._extract_last_update(data_indexed)
        assert last_update is not None

    def test_extract_timestamps(self, checker):
        """测试提取时间戳"""
        dates = pd.date_range("2023 - 01 - 01", periods=10, freq="D")
        data = pd.DataFrame({"date": dates, "value": range(10)})

        timestamps = checker._extract_timestamps(data)

        assert len(timestamps) == 10
        assert all(isinstance(ts, (pd.Timestamp, datetime)) for ts in timestamps)

    def test_stats_tracking(self, checker):
        """测试统计跟踪"""
        initial_stats = checker.get_stats()
        assert "total_checks" in initial_stats
        assert "alerts_sent" in initial_stats

        # 记录统计
        checker.stats["total_checks"] = 5
        stats = checker.get_stats()
        assert stats["total_checks"] == 5

    def test_stats_reset(self, checker):
        """测试重置统计"""
        # 修改统计
        checker.stats["total_checks"] = 100

        # 重置
        checker.reset_stats()

        # 验证重置
        stats = checker.get_stats()
        assert stats["total_checks"] == 0

    @pytest.mark.asyncio
    async def test_missing_data_detection(self, checker):
        """测试缺失数据检测"""
        # 创建有缺口的数据
        dates = pd.date_range("2023 - 01 - 01", periods=50, freq="D")
        missing_dates = dates[10:15]  # 缺失5天
        valid_dates = dates[~dates.isin(missing_dates)]

        data = pd.DataFrame({"date": valid_dates, "value": range(len(valid_dates))})

        result = await checker.check("0700.HK", data, datetime.utcnow())

        # 应该检测到缺口
        assert len(result.anomalies) > 0

    @pytest.mark.asyncio
    async def test_freshness_score_calculation(self, checker, sample_data):
        """测试新鲜度分数计算"""
        last_update = datetime.utcnow() - timedelta(hours=1)
        result = await checker.check("0700.HK", sample_data, last_update)

        # 分数应该在0 - 1之间
        assert 0.0 <= result.freshness_score <= 1.0

        # 越新的数据分数越高
        old_result = await checker.check(
            "0700.HK", sample_data, datetime.utcnow() - timedelta(hours=5)
        )
        assert old_result.freshness_score <= result.freshness_score

    @pytest.mark.asyncio
    async def test_alert_triggering(self, checker):
        """测试告警触发"""
        # 创建一个陈旧的数据
        result = FreshnessResult(
            symbol="0700.HK",
            timestamp=datetime.utcnow(),
            last_update=datetime.utcnow() - timedelta(hours=5),
            status=UpdateStatus.STALE,
            age_hours=5.0,
            expected_frequency="daily",
            freshness_score=0.3,
            recommendations=["检查系统"],
        )

        # 模拟发送告警
        with patch.object(
            checker.alert_manager, "check_and_alert", new_callable=AsyncMock
        ) as mock_alert:
            mock_alert.return_value = [{"alert": "test"}]

            await checker.alert_manager.check_and_alert(result)

            # 验证告警被调用
            assert mock_alert.called


class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_check_data_freshness(self):
        """测试便捷检查函数"""
        dates = pd.date_range("2023 - 01 - 01", periods=10, freq="D")
        data = pd.DataFrame({"date": dates, "value": range(10)})
        last_update = datetime.utcnow() - timedelta(hours=1)

        result = await check_data_freshness("0700.HK", data, last_update)

        assert isinstance(result, FreshnessResult)
        assert result.symbol == "0700.HK"

    def test_create_freshness_checker(self):
        """测试创建检查器"""
        config = {"latency": {"thresholds": {"daily": 2.0}}}
        checker = create_freshness_checker(config)

        assert isinstance(checker, FreshnessChecker)
        assert checker.config == config


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程"""
        # 创建配置
        config = {
            "latency": {"thresholds": {"daily": 4.0}},
            "frequency": {
                "frequency_rules": {"daily": {"min_interval": 20, "max_interval": 30}}
            },
            "missing": {"gap_thresholds": {"daily": 4.0}},
            "alert": {
                "alert_rules": {
                    UpdateStatus.STALE: {"enabled": True, "channels": ["log"]}
                }
            },
        }

        # 创建检查器
        checker = FreshnessChecker(config)

        # 创建测试数据（稍微陈旧）
        dates = pd.date_range("2023 - 01 - 01", periods=20, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "open": 100 + np.random.normal(0, 2, 20),
                "close": 101 + np.random.normal(0, 2, 20),
            }
        )

        # 模拟3小时前更新
        last_update = datetime.utcnow() - timedelta(hours=3)

        # 执行检查
        result = await checker.check("0700.HK", data, last_update)

        # 验证结果
        assert isinstance(result, FreshnessResult)
        assert result.symbol == "0700.HK"
        assert result.freshness_score > 0
        assert isinstance(result.recommendations, list)

        # 获取统计
        stats = checker.get_stats()
        assert stats["total_checks"] > 0

    @pytest.mark.asyncio
    async def test_multiple_stocks(self):
        """测试多股票检查"""
        checker = create_freshness_checker()

        symbols = ["0700.HK", "0388.HK", "0939.HK"]
        results = []

        for symbol in symbols:
            # 创建测试数据
            dates = pd.date_range("2023 - 01 - 01", periods=30, freq="D")
            data = pd.DataFrame(
                {"date": dates, "close": 100 + np.random.normal(0, 5, 30)}
            )

            result = await checker.check(symbol, data, datetime.utcnow())
            results.append(result)

        # 验证所有股票都被检查
        assert len(results) == 3
        for result in results:
            assert isinstance(result, FreshnessResult)
            assert result.symbol in symbols

    @pytest.mark.asyncio
    async def test_real_time_vs_daily_comparison(self):
        """测试实时与日级数据比较"""
        checker = create_freshness_checker()

        # 实时数据（1小时前更新）
        real_time_data = pd.DataFrame(
            {
                "date": pd.date_range("2023 - 01 - 01", periods=5, freq="H"),
                "value": range(5),
            }
        )
        rt_result = await checker.check(
            "0700.HK", real_time_data, datetime.utcnow() - timedelta(hours=1)
        )

        # 日级数据（6小时前更新）
        daily_data = pd.DataFrame(
            {
                "date": pd.date_range("2023 - 01 - 01", periods=5, freq="D"),
                "value": range(5),
            }
        )
        daily_result = await checker.check(
            "0700.HK", daily_data, datetime.utcnow() - timedelta(hours=6)
        )

        # 实时数据应该分数更高
        assert rt_result.freshness_score >= daily_result.freshness_score


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
