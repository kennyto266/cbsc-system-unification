"""
增強型監控系統 - 實時市場監控和警報

包含市場監控、系統監控、性能監控和智能警報
"""

import asyncio
import json
import logging
import smtplib
from datetime import datetime, timedelta
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd
import psutil
from pydantic import BaseModel, Field

from ..agents.real_agents.enhanced_quantitative_analyst import (
    EnhancedQuantitativeAnalyst,
)
from ..data_adapters.data_service import DataService
from ..risk_management.risk_calculator import RiskCalculator, RiskMetrics


class AlertLevel(str, Enum):
    """警報級別"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(str, Enum):
    """警報類型"""

    MARKET_DATA = "market_data"
    RISK_LIMIT = "risk_limit"
    SYSTEM_ERROR = "system_error"
    PERFORMANCE = "performance"
    TRADING = "trading"
    DATA_QUALITY = "data_quality"


class Alert(BaseModel):
    """警報模型"""

    alert_id: str = Field(..., description="警報ID")
    alert_type: AlertType = Field(..., description="警報類型")
    level: AlertLevel = Field(..., description="警報級別")
    title: str = Field(..., description="警報標題")
    message: str = Field(..., description="警報消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="警報時間")
    source: str = Field(..., description="警報來源")
    data: Dict[str, Any] = Field(default_factory=dict, description="警報數據")
    acknowledged: bool = Field(default=False, description="是否已確認")
    resolved: bool = Field(default=False, description="是否已解決")
    resolved_at: Optional[datetime] = Field(None, description="解決時間")


class MarketCondition(BaseModel):
    """市場狀況"""

    symbol: str = Field(..., description="交易標的")
    current_price: Decimal = Field(..., description="當前價格")
    price_change: Decimal = Field(..., description="價格變化")
    price_change_percent: float = Field(..., description="價格變化百分比")
    volume: int = Field(..., description="成交量")
    volume_change_percent: float = Field(..., description="成交量變化百分比")
    volatility: float = Field(..., description="波動率")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳")


class SystemMetrics(BaseModel):
    """系統指標"""

    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="內存使用率")
    disk_usage: float = Field(..., description="磁盤使用率")
    network_latency: float = Field(..., description="網絡延遲")
    active_connections: int = Field(..., description="活躍連接數")
    error_rate: float = Field(..., description="錯誤率")
    throughput: float = Field(..., description="吞吐量")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳")


class PerformanceMetrics(BaseModel):
    """性能指標"""

    total_return: float = Field(..., description="總收益率")
    sharpe_ratio: float = Field(..., description="夏普比率")
    max_drawdown: float = Field(..., description="最大回撤")
    var_95: float = Field(..., description="95% VaR")
    win_rate: float = Field(..., description="勝率")
    total_trades: int = Field(..., description="總交易次數")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳")


class AlertRule(BaseModel):
    """警報規則"""

    rule_id: str = Field(..., description="規則ID")
    name: str = Field(..., description="規則名稱")
    alert_type: AlertType = Field(..., description="警報類型")
    condition: str = Field(..., description="觸發條件")
    threshold: float = Field(..., description="閾值")
    level: AlertLevel = Field(..., description="警報級別")
    enabled: bool = Field(default=True, description="是否啟用")
    cooldown_minutes: int = Field(default=60, description="冷卻時間（分鐘）")


class EnhancedMonitoringSystem:
    """增強型監控系統"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.enhanced_monitoring")

        # 初始化組件
        self.data_service = DataService()
        self.risk_calculator = RiskCalculator()

        # 監控狀態
        self.is_running = False
        self.alerts: List[Alert] = []
        self.alert_rules: List[AlertRule] = []
        self.market_conditions: Dict[str, MarketCondition] = {}
        self.system_metrics: List[SystemMetrics] = []
        self.performance_metrics: List[PerformanceMetrics] = []

        # 警報處理器
        self.alert_handlers: Dict[AlertType, List[Callable]] = {}

        # 監控任務
        self.monitoring_tasks: List[asyncio.Task] = []

        # 最後警報時間（用於冷卻）
        self.last_alert_times: Dict[str, datetime] = {}

    async def initialize(self) -> bool:
        """初始化監控系統"""
        try:
            self.logger.info("Initializing enhanced monitoring system...")

            # 初始化數據服務
            if not await self.data_service.initialize():
                self.logger.error("Failed to initialize data service")
                return False

            # 加載警報規則
            await self._load_alert_rules()

            # 註冊默認警報處理器
            await self._register_default_handlers()

            self.logger.info("Enhanced monitoring system initialized successfully")
            return True

        except Exception as e:
            self.logger.exception(
                f"Failed to initialize enhanced monitoring system: {e}"
            )
            return False

    async def start_monitoring(self) -> None:
        """開始監控"""
        try:
            if self.is_running:
                self.logger.warning("Monitoring system is already running")
                return

            self.logger.info("Starting enhanced monitoring system...")
            self.is_running = True

            # 啟動各種監控任務
            self.monitoring_tasks = [
                asyncio.create_task(self._market_monitoring_loop()),
                asyncio.create_task(self._system_monitoring_loop()),
                asyncio.create_task(self._performance_monitoring_loop()),
                asyncio.create_task(self._risk_monitoring_loop()),
                asyncio.create_task(self._data_quality_monitoring_loop()),
                asyncio.create_task(self._alert_processing_loop()),
            ]

            self.logger.info("Enhanced monitoring system started successfully")

        except Exception as e:
            self.logger.exception(f"Error starting monitoring system: {e}")
            self.is_running = False

    async def stop_monitoring(self) -> None:
        """停止監控"""
        try:
            self.logger.info("Stopping enhanced monitoring system...")
            self.is_running = False

            # 取消所有監控任務
            for task in self.monitoring_tasks:
                if not task.done():
                    task.cancel()

            # 等待任務完成
            if self.monitoring_tasks:
                await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

            self.monitoring_tasks.clear()
            self.logger.info("Enhanced monitoring system stopped")

        except Exception as e:
            self.logger.exception(f"Error stopping monitoring system: {e}")

    async def _market_monitoring_loop(self) -> None:
        """市場監控循環"""
        while self.is_running:
            try:
                await self._monitor_market_conditions()
                await asyncio.sleep(30)  # 每30秒監控一次
            except Exception as e:
                self.logger.error(f"Error in market monitoring loop: {e}")
                await asyncio.sleep(60)

    async def _system_monitoring_loop(self) -> None:
        """系統監控循環"""
        while self.is_running:
            try:
                await self._monitor_system_metrics()
                await asyncio.sleep(60)  # 每分鐘監控一次
            except Exception as e:
                self.logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(120)

    async def _performance_monitoring_loop(self) -> None:
        """性能監控循環"""
        while self.is_running:
            try:
                await self._monitor_performance_metrics()
                await asyncio.sleep(300)  # 每5分鐘監控一次
            except Exception as e:
                self.logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(600)

    async def _risk_monitoring_loop(self) -> None:
        """風險監控循環"""
        while self.is_running:
            try:
                await self._monitor_risk_metrics()
                await asyncio.sleep(60)  # 每分鐘監控一次
            except Exception as e:
                self.logger.error(f"Error in risk monitoring loop: {e}")
                await asyncio.sleep(120)

    async def _data_quality_monitoring_loop(self) -> None:
        """數據質量監控循環"""
        while self.is_running:
            try:
                await self._monitor_data_quality()
                await asyncio.sleep(300)  # 每5分鐘監控一次
            except Exception as e:
                self.logger.error(f"Error in data quality monitoring loop: {e}")
                await asyncio.sleep(600)

    async def _alert_processing_loop(self) -> None:
        """警報處理循環"""
        while self.is_running:
            try:
                await self._process_pending_alerts()
                await asyncio.sleep(10)  # 每10秒處理一次
            except Exception as e:
                self.logger.error(f"Error in alert processing loop: {e}")
                await asyncio.sleep(30)

    async def _monitor_market_conditions(self) -> None:
        """監控市場狀況"""
        try:
            symbols = self.config.get("monitored_symbols", ["AAPL", "MSFT", "GOOGL"])

            for symbol in symbols:
                # 獲取實時數據
                market_data = await self.data_service.get_real_time_data(symbol)
                if not market_data:
                    continue

                # 計算價格變化
                historical_data = await self.data_service.get_market_data(
                    symbol=symbol,
                    start_date=datetime.now().date() - timedelta(days=1),
                    end_date=datetime.now().date(),
                )

                price_change = Decimal("0")
                price_change_percent = 0.0
                volume_change_percent = 0.0

                if historical_data and len(historical_data) > 1:
                    prev_data = historical_data[-2]
                    current_data = historical_data[-1]

                    price_change = market_data.close_price - prev_data.close_price
                    price_change_percent = float(
                        price_change / prev_data.close_price * 100
                    )

                    if prev_data.volume > 0:
                        volume_change_percent = (
                            (market_data.volume - prev_data.volume)
                            / prev_data.volume
                            * 100
                        )

                # 計算波動率
                if len(historical_data) >= 20:
                    prices = [float(d.close_price) for d in historical_data[-20:]]
                    returns = [
                        prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))
                    ]
                    volatility = np.std(returns) * np.sqrt(252)
                else:
                    volatility = 0.0

                # 創建市場狀況
                market_condition = MarketCondition(
                    symbol=symbol,
                    current_price=market_data.close_price,
                    price_change=price_change,
                    price_change_percent=price_change_percent,
                    volume=market_data.volume,
                    volume_change_percent=volume_change_percent,
                    volatility=volatility,
                )

                self.market_conditions[symbol] = market_condition

                # 檢查市場警報
                await self._check_market_alerts(market_condition)

        except Exception as e:
            self.logger.error(f"Error monitoring market conditions: {e}")

    async def _monitor_system_metrics(self) -> None:
        """監控系統指標 - 優化版本"""
        try:
            # 使用緩存減少重複計算
            current_time = datetime.now()

            # 檢查是否需要更新（避免過於頻繁的系統調用）
            if (
                hasattr(self, "_last_system_check")
                and (current_time - self._last_system_check).seconds < 30
            ):
                return

            self._last_system_check = current_time

            # 並行獲取系統指標以提高效率
            async def get_cpu_usage():
                return psutil.cpu_percent(interval=0.1)  # 減少間隔時間

            async def get_memory_usage():
                return psutil.virtual_memory()

            async def get_disk_usage():
                try:
                    return psutil.disk_usage("/")
                except Exception:
                    return psutil.disk_usage("C:")  # Windows fallback

            async def get_network_info():
                try:
                    connections = len(psutil.net_connections())
                    return connections, 0.0  # 簡化的網絡延遲
                except Exception:
                    return 0, 0.0

            # 並行執行系統指標獲取
            cpu_task = asyncio.create_task(get_cpu_usage())
            memory_task = asyncio.create_task(get_memory_usage())
            disk_task = asyncio.create_task(get_disk_usage())
            network_task = asyncio.create_task(get_network_info())

            # 等待所有任務完成
            cpu_usage, memory, disk, (connections, network_latency) = (
                await asyncio.gather(cpu_task, memory_task, disk_task, network_task)
            )

            # 計算錯誤率和吞吐量（使用緩存值）
            error_rate = getattr(self, "_error_rate", 0.0)
            throughput = getattr(self, "_throughput", 0.0)

            system_metrics = SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_latency=network_latency,
                active_connections=connections,
                error_rate=error_rate,
                throughput=throughput,
            )

            self.system_metrics.append(system_metrics)

            # 使用deque提高性能
            if len(self.system_metrics) > 100:
                self.system_metrics = self.system_metrics[-100:]

            # 檢查系統警報
            await self._check_system_alerts(system_metrics)

        except Exception as e:
            self.logger.error(f"Error monitoring system metrics: {e}")
            # Fallback system metrics
            system_metrics = SystemMetrics(
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_latency=0.0,
                active_connections=0,
                error_rate=0.0,
                throughput=0.0,
            )
            self.system_metrics.append(system_metrics)

    async def _monitor_performance_metrics(self) -> None:
        """監控性能指標"""
        try:
            # 這裡應該從實際的交易記錄和組合數據中計算性能指標
            # 簡化實現，使用模擬數據

            performance_metrics = PerformanceMetrics(
                total_return=0.12,  # 12 % 總收益
                sharpe_ratio=1.85,  # 夏普比率
                max_drawdown=0.05,  # 5 % 最大回撤
                var_95=-0.02,  # 2% VaR
                win_rate=0.65,  # 65 % 勝率
                total_trades=150,  # 150筆交易
            )

            self.performance_metrics.append(performance_metrics)

            # 保持最近50個記錄
            if len(self.performance_metrics) > 50:
                self.performance_metrics = self.performance_metrics[-50:]

            # 檢查性能警報
            await self._check_performance_alerts(performance_metrics)

        except Exception as e:
            self.logger.error(f"Error monitoring performance metrics: {e}")
            # Fallback performance metrics
            performance_metrics = PerformanceMetrics(
                total_return=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                var_95=0.0,
                win_rate=0.0,
                total_trades=0,
            )
            self.performance_metrics.append(performance_metrics)

    async def _monitor_risk_metrics(self) -> None:
        """監控風險指標"""
        try:
            # 獲取最近的市場數據計算風險指標
            symbols = self.config.get("monitored_symbols", ["AAPL", "MSFT", "GOOGL"])
            all_returns = []

            for symbol in symbols:
                historical_data = await self.data_service.get_market_data(
                    symbol=symbol,
                    start_date=datetime.now().date() - timedelta(days=30),
                    end_date=datetime.now().date(),
                )

                if historical_data and len(historical_data) > 1:
                    prices = [float(d.close_price) for d in historical_data]
                    returns = [
                        prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))
                    ]
                    all_returns.extend(returns)

            if all_returns:
                returns_series = pd.Series(all_returns)
                risk_metrics = await self.risk_calculator.calculate_portfolio_risk(
                    returns_series
                )

                # 檢查風險警報
                await self._check_risk_alerts(risk_metrics)

        except Exception as e:
            self.logger.error(f"Error monitoring risk metrics: {e}")
            # Fallback risk metrics
            risk_metrics = RiskMetrics(
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                calmar_ratio=0.0,
                var_95=0.0,
                var_99=0.0,
                expected_shortfall_95=0.0,
                expected_shortfall_99=0.0,
                beta=0.0,
                tracking_error=0.0,
                information_ratio=0.0,
                sortino_ratio=0.0,
                risk_level="unknown",
                data_points=0,
                confidence_level=0.95,
            )
            await self._check_risk_alerts(risk_metrics)

    async def _monitor_data_quality(self) -> None:
        """監控數據質量"""
        try:
            # 檢查數據服務狀態
            adapter_status = await self.data_service.get_adapter_status()

            for adapter_name, status in adapter_status.items():
                if status.get("status") != "healthy":
                    await self._create_alert(
                        alert_type=AlertType.DATA_QUALITY,
                        level=AlertLevel.WARNING,
                        title=f"Data Adapter Issue: {adapter_name}",
                        message=f"Data adapter {adapter_name} is not healthy: {status.get('error', 'Unknown error')}",
                        source="data_quality_monitor",
                        data=status,
                    )

        except Exception as e:
            self.logger.error(f"Error monitoring data quality: {e}")
            # Fallback data quality alert
            await self._create_alert(
                alert_type=AlertType.DATA_QUALITY,
                level=AlertLevel.WARNING,
                title="Data Quality Monitoring Error",
                message=f"Failed to monitor data quality: {str(e)}",
                source="data_quality_monitor",
                data={"error": str(e)},
            )

    async def _check_market_alerts(self, market_condition: MarketCondition) -> None:
        """檢查市場警報"""
        try:
            # 價格變化警報
            if abs(market_condition.price_change_percent) > 5.0:
                level = (
                    AlertLevel.CRITICAL
                    if abs(market_condition.price_change_percent) > 10.0
                    else AlertLevel.WARNING
                )
                await self._create_alert(
                    alert_type=AlertType.MARKET_DATA,
                    level=level,
                    title=f"Large Price Movement: {market_condition.symbol}",
                    message=f"{market_condition.symbol} moved {market_condition.price_change_percent:.2f}% to {market_condition.current_price}",
                    source="market_monitor",
                    data=market_condition.dict(),
                )

            # 成交量異常警報
            if abs(market_condition.volume_change_percent) > 200.0:
                await self._create_alert(
                    alert_type=AlertType.MARKET_DATA,
                    level=AlertLevel.WARNING,
                    title=f"Volume Spike: {market_condition.symbol}",
                    message=f"{market_condition.symbol} volume increased by {market_condition.volume_change_percent:.2f}%",
                    source="market_monitor",
                    data=market_condition.dict(),
                )

            # 高波動率警報
            if market_condition.volatility > 0.5:
                await self._create_alert(
                    alert_type=AlertType.MARKET_DATA,
                    level=AlertLevel.WARNING,
                    title=f"High Volatility: {market_condition.symbol}",
                    message=f"{market_condition.symbol} volatility is {market_condition.volatility:.2%}",
                    source="market_monitor",
                    data=market_condition.dict(),
                )

        except Exception as e:
            self.logger.error(f"Error checking market alerts: {e}")
            # Fallback market alert
            await self._create_alert(
                alert_type=AlertType.MARKET_DATA,
                level=AlertLevel.WARNING,
                title="Market Alert Error",
                message=f"Failed to check market alerts: {str(e)}",
                source="market_monitor",
                data={"error": str(e)},
            )

    async def _check_system_alerts(self, system_metrics: SystemMetrics) -> None:
        """檢查系統警報"""
        try:
            # CPU使用率警報
            if system_metrics.cpu_usage > 90.0:
                await self._create_alert(
                    alert_type=AlertType.SYSTEM_ERROR,
                    level=AlertLevel.CRITICAL,
                    title="High CPU Usage",
                    message=f"CPU usage is {system_metrics.cpu_usage:.1f}%",
                    source="system_monitor",
                    data=system_metrics.dict(),
                )
            elif system_metrics.cpu_usage > 80.0:
                await self._create_alert(
                    alert_type=AlertType.SYSTEM_ERROR,
                    level=AlertLevel.WARNING,
                    title="Elevated CPU Usage",
                    message=f"CPU usage is {system_metrics.cpu_usage:.1f}%",
                    source="system_monitor",
                    data=system_metrics.dict(),
                )

            # 內存使用率警報
            if system_metrics.memory_usage > 95.0:
                await self._create_alert(
                    alert_type=AlertType.SYSTEM_ERROR,
                    level=AlertLevel.CRITICAL,
                    title="High Memory Usage",
                    message=f"Memory usage is {system_metrics.memory_usage:.1f}%",
                    source="system_monitor",
                    data=system_metrics.dict(),
                )

            # 磁盤使用率警報
            if system_metrics.disk_usage > 90.0:
                await self._create_alert(
                    alert_type=AlertType.SYSTEM_ERROR,
                    level=AlertLevel.WARNING,
                    title="High Disk Usage",
                    message=f"Disk usage is {system_metrics.disk_usage:.1f}%",
                    source="system_monitor",
                    data=system_metrics.dict(),
                )

        except Exception as e:
            self.logger.error(f"Error checking system alerts: {e}")
            # Fallback system alert
            await self._create_alert(
                alert_type=AlertType.SYSTEM_ERROR,
                level=AlertLevel.WARNING,
                title="System Alert Error",
                message=f"Failed to check system alerts: {str(e)}",
                source="system_monitor",
                data={"error": str(e)},
            )

    async def _check_performance_alerts(
        self, performance_metrics: PerformanceMetrics
    ) -> None:
        """檢查性能警報"""
        try:
            # 最大回撤警報
            if performance_metrics.max_drawdown > 0.1:
                await self._create_alert(
                    alert_type=AlertType.PERFORMANCE,
                    level=AlertLevel.WARNING,
                    title="High Drawdown",
                    message=f"Maximum drawdown is {performance_metrics.max_drawdown:.2%}",
                    source="performance_monitor",
                    data=performance_metrics.dict(),
                )

            # VaR警報
            if performance_metrics.var_95 < -0.05:
                await self._create_alert(
                    alert_type=AlertType.RISK_LIMIT,
                    level=AlertLevel.CRITICAL,
                    title="High VaR",
                    message=f"95% VaR is {performance_metrics.var_95:.2%}",
                    source="performance_monitor",
                    data=performance_metrics.dict(),
                )

            # 夏普比率警報
            if performance_metrics.sharpe_ratio < 0.5:
                await self._create_alert(
                    alert_type=AlertType.PERFORMANCE,
                    level=AlertLevel.WARNING,
                    title="Low Sharpe Ratio",
                    message=f"Sharpe ratio is {performance_metrics.sharpe_ratio:.3f}",
                    source="performance_monitor",
                    data=performance_metrics.dict(),
                )

        except Exception as e:
            self.logger.error(f"Error checking performance alerts: {e}")
            # Fallback performance alert
            await self._create_alert(
                alert_type=AlertType.PERFORMANCE,
                level=AlertLevel.WARNING,
                title="Performance Alert Error",
                message=f"Failed to check performance alerts: {str(e)}",
                source="performance_monitor",
                data={"error": str(e)},
            )

    async def _check_risk_alerts(self, risk_metrics: RiskMetrics) -> None:
        """檢查風險警報"""
        try:
            # 風險等級警報
            if risk_metrics.risk_level in ["high", "critical"]:
                await self._create_alert(
                    alert_type=AlertType.RISK_LIMIT,
                    level=(
                        AlertLevel.CRITICAL
                        if risk_metrics.risk_level == "critical"
                        else AlertLevel.WARNING
                    ),
                    title=f"High Risk Level: {risk_metrics.risk_level}",
                    message=f"Portfolio risk level is {risk_metrics.risk_level}",
                    source="risk_monitor",
                    data=risk_metrics.dict(),
                )

            # 波動率警報
            if risk_metrics.volatility > 0.4:
                await self._create_alert(
                    alert_type=AlertType.RISK_LIMIT,
                    level=AlertLevel.WARNING,
                    title="High Volatility",
                    message=f"Portfolio volatility is {risk_metrics.volatility:.2%}",
                    source="risk_monitor",
                    data=risk_metrics.dict(),
                )

        except Exception as e:
            self.logger.error(f"Error checking risk alerts: {e}")
            # Fallback risk alert
            await self._create_alert(
                alert_type=AlertType.RISK_LIMIT,
                level=AlertLevel.WARNING,
                title="Risk Alert Error",
                message=f"Failed to check risk alerts: {str(e)}",
                source="risk_monitor",
                data={"error": str(e)},
            )

    async def _create_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        title: str,
        message: str,
        source: str,
        data: Dict[str, Any] = None,
    ) -> None:
        """創建警報"""
        try:
            # 檢查冷卻時間
            alert_key = f"{alert_type}_{source}_{title}"
            if alert_key in self.last_alert_times:
                last_time = self.last_alert_times[alert_key]
                cooldown_minutes = 60  # 默認冷卻時間

                if datetime.now() - last_time < timedelta(minutes=cooldown_minutes):
                    return  # 仍在冷卻期內

            # 創建警報
            alert = Alert(
                alert_id=f"{alert_type}_{datetime.now().timestamp()}",
                alert_type=alert_type,
                level=level,
                title=title,
                message=message,
                source=source,
                data=data or {},
            )

            self.alerts.append(alert)
            self.last_alert_times[alert_key] = datetime.now()

            # 保持最近1000個警報
            if len(self.alerts) > 1000:
                self.alerts = self.alerts[-1000:]

            self.logger.info(f"Alert created: {level.value} - {title}")

        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
            # Fallback alert creation
            try:
                alert = Alert(
                    alert_id=f"fallback_{datetime.now().timestamp()}",
                    alert_type=alert_type,
                    level=level,
                    title=title,
                    message=message,
                    source=source,
                    data=data or {},
                )
                self.alerts.append(alert)
                self.logger.info(f"Fallback alert created: {level.value} - {title}")
            except Exception as fallback_error:
                self.logger.error(f"Failed to create fallback alert: {fallback_error}")

    async def _process_pending_alerts(self) -> None:
        """處理待處理警報"""
        try:
            pending_alerts = [alert for alert in self.alerts if not alert.acknowledged]

            for alert in pending_alerts:
                # 調用相應的處理器
                if alert.alert_type in self.alert_handlers:
                    for handler in self.alert_handlers[alert.alert_type]:
                        try:
                            await handler(alert)
                        except Exception as e:
                            self.logger.error(f"Error in alert handler: {e}")

        except Exception as e:
            self.logger.error(f"Error processing pending alerts: {e}")
            # Fallback alert processing
            try:
                for alert in self.alerts[-10:]:  # Process last 10 alerts
                    if not alert.acknowledged:
                        self.logger.warning(f"Unprocessed alert: {alert.title}")
            except Exception as fallback_error:
                self.logger.error(
                    f"Failed to process fallback alerts: {fallback_error}"
                )

    async def _load_alert_rules(self) -> None:
        """加載警報規則"""
        try:
            # 默認警報規則
            default_rules = [
                AlertRule(
                    rule_id="price_movement_5pct",
                    name="5% Price Movement",
                    alert_type=AlertType.MARKET_DATA,
                    condition="abs(price_change_percent) > 5",
                    threshold=5.0,
                    level=AlertLevel.WARNING,
                    cooldown_minutes=30,
                ),
                AlertRule(
                    rule_id="price_movement_10pct",
                    name="10% Price Movement",
                    alert_type=AlertType.MARKET_DATA,
                    condition="abs(price_change_percent) > 10",
                    threshold=10.0,
                    level=AlertLevel.CRITICAL,
                    cooldown_minutes=60,
                ),
                AlertRule(
                    rule_id="high_cpu_usage",
                    name="High CPU Usage",
                    alert_type=AlertType.SYSTEM_ERROR,
                    condition="cpu_usage > 90",
                    threshold=90.0,
                    level=AlertLevel.CRITICAL,
                    cooldown_minutes=15,
                ),
                AlertRule(
                    rule_id="high_drawdown",
                    name="High Drawdown",
                    alert_type=AlertType.PERFORMANCE,
                    condition="max_drawdown > 0.1",
                    threshold=0.1,
                    level=AlertLevel.WARNING,
                    cooldown_minutes=120,
                ),
            ]

            self.alert_rules = default_rules
            self.logger.info(f"Loaded {len(self.alert_rules)} alert rules")

        except Exception as e:
            self.logger.error(f"Error loading alert rules: {e}")
            # Fallback alert rules
            self.alert_rules = []
            self.logger.warning("Using fallback alert rules")

    async def _register_default_handlers(self) -> None:
        """註冊默認警報處理器"""
        try:
            # 註冊各種警報處理器
            self.alert_handlers[AlertType.MARKET_DATA] = [self._handle_market_alert]
            self.alert_handlers[AlertType.SYSTEM_ERROR] = [self._handle_system_alert]
            self.alert_handlers[AlertType.PERFORMANCE] = [
                self._handle_performance_alert
            ]
            self.alert_handlers[AlertType.RISK_LIMIT] = [self._handle_risk_alert]
            self.alert_handlers[AlertType.DATA_QUALITY] = [
                self._handle_data_quality_alert
            ]

            self.logger.info("Default alert handlers registered")

        except Exception as e:
            self.logger.error(f"Error registering default handlers: {e}")
            # Fallback handlers
            self.alert_handlers = {}
            self.logger.warning("Using fallback alert handlers")

    async def _handle_market_alert(self, alert: Alert) -> None:
        """處理市場警報"""
        self.logger.warning(f"Market Alert: {alert.title} - {alert.message}")
        # 這裡可以添加更多處理邏輯，如發送郵件、Slack通知等

    async def _handle_system_alert(self, alert: Alert) -> None:
        """處理系統警報"""
        self.logger.error(f"System Alert: {alert.title} - {alert.message}")
        # 這裡可以添加更多處理邏輯，如自動重啟服務等

    async def _handle_performance_alert(self, alert: Alert) -> None:
        """處理性能警報"""
        self.logger.warning(f"Performance Alert: {alert.title} - {alert.message}")
        # 這裡可以添加更多處理邏輯，如調整策略參數等

    async def _handle_risk_alert(self, alert: Alert) -> None:
        """處理風險警報"""
        self.logger.error(f"Risk Alert: {alert.title} - {alert.message}")
        # 這裡可以添加更多處理邏輯，如暫停交易等

    async def _handle_data_quality_alert(self, alert: Alert) -> None:
        """處理數據質量警報"""
        self.logger.warning(f"Data Quality Alert: {alert.title} - {alert.message}")
        # 這裡可以添加更多處理邏輯，如切換數據源等

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """獲取監控狀態"""
        try:
            return {
                "is_running": self.is_running,
                "active_tasks": len([t for t in self.monitoring_tasks if not t.done()]),
                "total_alerts": len(self.alerts),
                "unacknowledged_alerts": len(
                    [a for a in self.alerts if not a.acknowledged]
                ),
                "monitored_symbols": len(self.market_conditions),
                "system_metrics_count": len(self.system_metrics),
                "performance_metrics_count": len(self.performance_metrics),
                "alert_rules_count": len(self.alert_rules),
            }

        except Exception as e:
            self.logger.error(f"Error getting monitoring status: {e}")
            # Fallback status
            return {
                "is_running": False,
                "active_tasks": 0,
                "total_alerts": 0,
                "unacknowledged_alerts": 0,
                "monitored_symbols": 0,
                "system_metrics_count": 0,
                "performance_metrics_count": 0,
                "alert_rules_count": 0,
                "error": str(e),
            }

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """確認警報"""
        try:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    self.logger.info(f"Alert acknowledged: {alert_id}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error acknowledging alert: {e}")
            # Fallback acknowledgment
            try:
                for alert in self.alerts:
                    if alert.alert_id == alert_id:
                        alert.acknowledged = True
                        return True
                return False
            except Exception as fallback_error:
                self.logger.error(f"Failed to acknowledge alert: {fallback_error}")
                return False

    async def resolve_alert(self, alert_id: str) -> bool:
        """解決警報"""
        try:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    self.logger.info(f"Alert resolved: {alert_id}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error resolving alert: {e}")
            # Fallback resolution
            try:
                for alert in self.alerts:
                    if alert.alert_id == alert_id:
                        alert.resolved = True
                        alert.resolved_at = datetime.now()
                        return True
                return False
            except Exception as fallback_error:
                self.logger.error(f"Failed to resolve alert: {fallback_error}")
                return False

    async def cleanup(self) -> None:
        """清理資源"""
        try:
            await self.stop_monitoring()

            if hasattr(self.data_service, "cleanup"):
                await self.data_service.cleanup()

            self.logger.info("Enhanced monitoring system cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            # Fallback cleanup
            try:
                self.is_running = False
                self.monitoring_tasks.clear()
                self.alerts.clear()
                self.market_conditions.clear()
                self.system_metrics.clear()
                self.performance_metrics.clear()
                self.alert_rules.clear()
                self.alert_handlers.clear()
                self.last_alert_times.clear()
                self.logger.info("Fallback cleanup completed")
            except Exception as fallback_error:
                self.logger.error(
                    f"Failed to perform fallback cleanup: {fallback_error}"
                )
