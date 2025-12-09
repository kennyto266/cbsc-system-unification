"""Base classes for real AI agents with actual market data integration."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from ...backtest.engine_interface import BacktestMetrics
from ...core.message_queue import Message, message_queue
from ...data_adapters.base_adapter import DataValidationResult, RealMarketData
from ..base_agent import AgentConfig, AgentStatus, BaseAgent
from .real_data_analyzer import AnalysisResult, RealDataAnalyzer, SignalStrength


class RealAgentStatus(str, Enum):
    """Real agent operational status."""

    INITIALIZING = "initializing"
    DATA_CONNECTING = "data_connecting"
    MODEL_LOADING = "model_loading"
    READY = "ready"
    ANALYZING = "analyzing"
    TRADING = "trading"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class RealAgentConfig(BaseModel):
    """Configuration for real AI agents."""

    # Agent identification
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(
        ..., description="Type of agent (quantitative_analyst, trader, etc.)"
    )
    name: str = Field(..., description="Human - readable agent name")

    # Data configuration
    data_sources: List[str] = Field(
        default_factory=list, description="List of data source names to use"
    )
    update_frequency: int = Field(
        60, ge=1, description="Data update frequency in seconds"
    )
    lookback_period: int = Field(
        252, ge=1, description="Days of historical data to analyze"
    )

    # Analysis configuration
    analysis_methods: List[str] = Field(
        default_factory=list, description="Analysis methods to use"
    )
    signal_threshold: float = Field(
        0.6, ge=0.0, le=1.0, description="Minimum signal strength threshold"
    )
    confidence_threshold: float = Field(
        0.7, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )

    # Machine learning configuration
    ml_models: List[str] = Field(default_factory=list, description="ML models to use")
    model_update_frequency: int = Field(
        86400, ge=1, description="Model retraining frequency in seconds"
    )
    feature_engineering: bool = Field(True, description="Enable feature engineering")

    # Risk management
    max_position_size: float = Field(
        0.1, ge=0.0, le=1.0, description="Maximum position size as fraction of capital"
    )
    stop_loss_threshold: float = Field(0.05, ge=0.0, description="Stop loss threshold")
    take_profit_threshold: float = Field(
        0.1, ge=0.0, description="Take profit threshold"
    )

    # Performance tracking
    performance_tracking: bool = Field(True, description="Enable performance tracking")
    backtest_enabled: bool = Field(True, description="Enable strategy backtesting")

    # Logging and monitoring
    log_level: str = Field("INFO", description="Logging level")
    enable_metrics: bool = Field(
        True, description="Enable performance metrics collection"
    )

    @validator("agent_type")
    def validate_agent_type(cls, v):
        valid_types = [
            "quantitative_analyst",
            "quantitative_trader",
            "portfolio_manager",
            "risk_analyst",
            "data_scientist",
            "quantitative_engineer",
            "research_analyst",
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid agent type: {v}. Must be one of {valid_types}")
        return v

    class Config:
        use_enum_values = True


class BaseRealAgent(BaseAgent):
    """Base class for real AI agents with actual market data integration."""

    def __init__(self, config: RealAgentConfig):
        # 将 RealAgentConfig 适配为 BaseAgent 期望的 AgentConfig
        agent_cfg = AgentConfig(
            agent_id=config.agent_id,
            agent_type=config.agent_type,
            config={
                "name": config.name,
                "data_sources": config.data_sources,
                "update_frequency": config.update_frequency,
                "lookback_period": config.lookback_period,
                "analysis_methods": config.analysis_methods,
                "signal_threshold": config.signal_threshold,
                "confidence_threshold": config.confidence_threshold,
                "ml_models": config.ml_models,
                "model_update_frequency": getattr(
                    config, "model_update_frequency", 86400
                ),
                "feature_engineering": getattr(config, "feature_engineering", True),
                "max_position_size": config.max_position_size,
                "stop_loss_threshold": config.stop_loss_threshold,
                "take_profit_threshold": config.take_profit_threshold,
                "performance_tracking": config.performance_tracking,
                "backtest_enabled": config.backtest_enabled,
                "log_level": config.log_level,
                "enable_metrics": config.enable_metrics,
            },
        )
        # 使用全局消息队列实例（未初始化也可工作于本地流程，不订阅即可）
        super().__init__(agent_cfg, message_queue)

        self.config = config
        self.real_status = RealAgentStatus.INITIALIZING
        self.data_analyzer = RealDataAnalyzer(config)
        self.ml_models: Dict[str, Any] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.last_analysis: Optional[AnalysisResult] = None
        self.current_positions: Dict[str, float] = {}

        # Setup logging
        self.logger = logging.getLogger(f"hk_quant_system.real_agent.{config.agent_id}")
        self.logger.setLevel(getattr(logging, config.log_level.upper()))

    async def initialize(self) -> bool:
        """Initialize the real agent with data connections and ML models."""
        try:
            self.logger.info(f"Initializing real agent: {self.config.name}")
            self.real_status = RealAgentStatus.INITIALIZING

            # Initialize data analyzer
            if not await self.data_analyzer.initialize():
                self.logger.error("Failed to initialize data analyzer")
                self.real_status = RealAgentStatus.ERROR
                return False

            self.real_status = RealAgentStatus.DATA_CONNECTING
            self.logger.info("Data analyzer initialized successfully")

            # Load ML models if configured
            if self.config.ml_models:
                self.real_status = RealAgentStatus.MODEL_LOADING
                await self._load_ml_models()

            # Initialize agent - specific components
            if not await self._initialize_specific():
                self.logger.error("Failed to initialize agent - specific components")
                self.real_status = RealAgentStatus.ERROR
                return False

            self.real_status = RealAgentStatus.READY
            self.status = AgentStatus.RUNNING
            self.logger.info(f"Real agent {self.config.name} initialized successfully")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize real agent: {e}")
            self.real_status = RealAgentStatus.ERROR
            self.status = AgentStatus.ERROR
            return False

    @abstractmethod
    async def _initialize_specific(self) -> bool:
        """Initialize agent - specific components. Must be implemented by subclasses."""
        pass

    async def _load_ml_models(self) -> None:
        """Load machine learning models."""
        try:
            from .ml_integration import MLModelManager

            ml_manager = MLModelManager()
            for model_name in self.config.ml_models:
                model = await ml_manager.load_model(model_name)
                if model:
                    self.ml_models[model_name] = model
                    self.logger.info(f"Loaded ML model: {model_name}")
                else:
                    self.logger.warning(f"Failed to load ML model: {model_name}")

        except Exception as e:
            self.logger.exception(f"Error loading ML models: {e}")

    async def analyze_market_data(
        self, market_data: List[RealMarketData]
    ) -> AnalysisResult:
        """Analyze market data and generate insights."""
        try:
            self.real_status = RealAgentStatus.ANALYZING
            self.logger.debug(f"Analyzing {len(market_data)} market data points")

            # Use data analyzer to process market data
            analysis_result = await self.data_analyzer.analyze(market_data)

            # Apply agent - specific analysis
            enhanced_result = await self._enhance_analysis(analysis_result, market_data)

            # Update last analysis
            self.last_analysis = enhanced_result

            self.logger.info(
                f"Analysis completed. Signal strength: {enhanced_result.signal_strength}"
            )
            return enhanced_result

        except Exception as e:
            self.logger.exception(f"Error analyzing market data: {e}")
            self.real_status = RealAgentStatus.ERROR
            raise

    @abstractmethod
    async def _enhance_analysis(
        self, base_result: AnalysisResult, market_data: List[RealMarketData]
    ) -> AnalysisResult:
        """Enhance analysis with agent - specific logic. Must be implemented by subclasses."""
        pass

    async def generate_trading_signals(
        self, analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Generate trading signals based on analysis results."""
        try:
            if analysis_result.signal_strength < self.config.signal_threshold:
                self.logger.debug(
                    "Signal strength below threshold, no signals generated"
                )
                return []

            if analysis_result.confidence < self.config.confidence_threshold:
                self.logger.debug("Confidence below threshold, no signals generated")
                return []

            # Generate base signals
            signals = await self._generate_base_signals(analysis_result)

            # Apply agent - specific signal generation
            enhanced_signals = await self._enhance_signals(signals, analysis_result)

            # Filter and validate signals
            validated_signals = await self._validate_signals(enhanced_signals)

            self.logger.info(f"Generated {len(validated_signals)} trading signals")
            return validated_signals

        except Exception as e:
            self.logger.exception(f"Error generating trading signals: {e}")
            return []

    async def _generate_base_signals(
        self, analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Generate basic trading signals. Can be overridden by subclasses."""
        signals = []

        for symbol, metrics in analysis_result.technical_indicators.items():
            signal = {
                "symbol": symbol,
                "signal_type": (
                    "buy"
                    if metrics.get("rsi", 50) < 30
                    else "sell" if metrics.get("rsi", 50) > 70 else "hold"
                ),
                "strength": analysis_result.signal_strength,
                "confidence": analysis_result.confidence,
                "timestamp": datetime.now(),
                "reasoning": f"RSI - based signal: {metrics.get('rsi', 50):.2f}",
            }
            signals.append(signal)

        return signals

    @abstractmethod
    async def _enhance_signals(
        self, base_signals: List[Dict[str, Any]], analysis_result: AnalysisResult
    ) -> List[Dict[str, Any]]:
        """Enhance signals with agent - specific logic. Must be implemented by subclasses."""
        pass

    async def _validate_signals(
        self, signals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and filter trading signals."""
        validated_signals = []

        for signal in signals:
            # Check signal strength
            if signal.get("strength", 0) < self.config.signal_threshold:
                continue

            # Check confidence
            if signal.get("confidence", 0) < self.config.confidence_threshold:
                continue

            # Validate required fields
            required_fields = ["symbol", "signal_type", "strength", "confidence"]
            if not all(field in signal for field in required_fields):
                self.logger.warning(f"Signal missing required fields: {signal}")
                continue

            # Add position size based on risk management
            signal["position_size"] = self._calculate_position_size(signal)

            validated_signals.append(signal)

        return validated_signals

    def _calculate_position_size(self, signal: Dict[str, Any]) -> float:
        """Calculate position size based on risk management rules."""
        base_size = self.config.max_position_size

        # Adjust based on signal strength
        strength_multiplier = signal.get("strength", 0.5)

        # Adjust based on confidence
        confidence_multiplier = signal.get("confidence", 0.5)

        # Calculate final position size
        position_size = base_size * strength_multiplier * confidence_multiplier

        return min(position_size, self.config.max_position_size)

    async def execute_strategy(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute trading strategy based on signals."""
        try:
            self.real_status = RealAgentStatus.TRADING
            execution_results = {
                "executed_signals": [],
                "failed_signals": [],
                "total_executed": 0,
                "execution_timestamp": datetime.now(),
            }

            for signal in signals:
                try:
                    # Execute individual signal
                    result = await self._execute_signal(signal)
                    execution_results["executed_signals"].append(result)
                    execution_results["total_executed"] += 1

                except Exception as e:
                    self.logger.error(f"Failed to execute signal: {signal}, error: {e}")
                    execution_results["failed_signals"].append(
                        {"signal": signal, "error": str(e)}
                    )

            self.logger.info(
                f"Strategy execution completed. {execution_results['total_executed']} signals executed"
            )
            return execution_results

        except Exception as e:
            self.logger.exception(f"Error executing strategy: {e}")
            self.real_status = RealAgentStatus.ERROR
            raise

    @abstractmethod
    async def _execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual trading signal. Must be implemented by subclasses."""
        pass

    async def backtest_strategy(
        self, strategy_params: Dict[str, Any], market_data: List[RealMarketData]
    ) -> Optional[BacktestMetrics]:
        """Backtest the agent's strategy."""
        if not self.config.backtest_enabled:
            self.logger.warning("Backtesting is disabled for this agent")
            return None

        try:
            # This would integrate with the backtest engine
            # For now, return a placeholder
            self.logger.info("Running strategy backtest...")

            # TODO: Integrate with actual backtest engine
            return None

        except Exception as e:
            self.logger.exception(f"Error during backtest: {e}")
            return None

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        metrics = {
            "agent_id": self.config.agent_id,
            "agent_name": self.config.name,
            "real_status": self.real_status,
            "base_status": self.status,
            "last_analysis_time": (
                self.last_analysis.timestamp if self.last_analysis else None
            ),
            "current_positions": self.current_positions,
            "performance_history_count": len(self.performance_history),
            "ml_models_loaded": list(self.ml_models.keys()),
            "data_sources": self.config.data_sources,
            "update_frequency": self.config.update_frequency,
        }

        if self.last_analysis:
            metrics.update(
                {
                    "last_signal_strength": self.last_analysis.signal_strength,
                    "last_confidence": self.last_analysis.confidence,
                    "last_analysis_symbols": list(
                        self.last_analysis.technical_indicators.keys()
                    ),
                }
            )

        return metrics

    async def cleanup(self) -> None:
        """Cleanup agent resources."""
        try:
            self.logger.info(f"Cleaning up real agent: {self.config.name}")

            # Cleanup data analyzer
            if hasattr(self.data_analyzer, "cleanup"):
                await self.data_analyzer.cleanup()

            # Cleanup ML models
            for model_name, model in self.ml_models.items():
                if hasattr(model, "cleanup"):
                    await model.cleanup()

            self.ml_models.clear()
            self.performance_history.clear()
            self.current_positions.clear()

            self.real_status = RealAgentStatus.MAINTENANCE
            self.status = AgentStatus.STOPPED

            self.logger.info("Real agent cleanup completed")

        except Exception as e:
            self.logger.exception(f"Error during cleanup: {e}")

    async def handle_message(self, message: Message) -> Optional[Message]:
        """Handle incoming messages. Can be overridden by subclasses."""
        self.logger.debug(f"Received message: {message.type} from {message.sender}")

        # Handle common message types
        if message.type == "get_status":
            metrics = await self.get_performance_metrics()
            return Message(
                id=f"{self.config.agent_id}_{datetime.now().timestamp()}",
                type="status_response",
                sender=self.config.agent_id,
                receiver=message.sender,
                content=metrics,
                timestamp=datetime.now(),
            )

        elif message.type == "force_analysis":
            # Trigger new analysis if market data is provided
            if "market_data" in message.content:
                try:
                    analysis_result = await self.analyze_market_data(
                        message.content["market_data"]
                    )
                    return Message(
                        id=f"{self.config.agent_id}_{datetime.now().timestamp()}",
                        type="analysis_response",
                        sender=self.config.agent_id,
                        receiver=message.sender,
                        content={"analysis_result": analysis_result.model_dump()},
                        timestamp=datetime.now(),
                    )
                except Exception as e:
                    return Message(
                        id=f"{self.config.agent_id}_{datetime.now().timestamp()}",
                        type="error_response",
                        sender=self.config.agent_id,
                        receiver=message.sender,
                        content={"error": str(e)},
                        timestamp=datetime.now(),
                    )

        # Let subclasses handle other message types
        return await self._handle_specific_message(message)

    async def _handle_specific_message(self, message: Message) -> Optional[Message]:
        """Handle agent - specific messages. Can be overridden by subclasses."""
        return None
