"""Strategy management system for Hong Kong quantitative trading.

This module provides comprehensive strategy lifecycle management including
strategy registration, deployment, monitoring, and optimization.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from ..agents.real_agents.base_real_agent import BaseRealAgent
from ..backtest.engine_interface import BaseBacktestEngine, StrategyPerformance


class StrategyType(str, Enum):
    """Types of trading strategies."""

    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"
    TREND_FOLLOWING = "trend_following"
    CONTRARIAN = "contrarian"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"
    MACHINE_LEARNING = "machine_learning"
    CUSTOM = "custom"


class StrategyStatus(str, Enum):
    """Strategy status levels."""

    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class OptimizationMethod(str, Enum):
    """Strategy optimization methods."""

    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    GENETIC_ALGORITHM = "genetic_algorithm"
    PARTICLE_SWARM = "particle_swarm"
    SIMULATED_ANNEALING = "simulated_annealing"
    MACHINE_LEARNING = "machine_learning"


class StrategyConfig(BaseModel):
    """Strategy configuration model."""

    strategy_id: str = Field(..., description="Unique strategy identifier")
    name: str = Field(..., description="Strategy name")
    description: str = Field("", description="Strategy description")
    strategy_type: StrategyType = Field(..., description="Strategy type")

    # Strategy parameters
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Strategy parameters"
    )
    risk_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Risk management parameters"
    )

    # Execution settings
    enabled: bool = Field(True, description="Strategy enabled status")
    max_position_size: float = Field(1000000.0, description="Maximum position size")
    max_drawdown: float = Field(0.1, description="Maximum drawdown threshold")
    stop_loss: Optional[float] = Field(None, description="Stop loss percentage")
    take_profit: Optional[float] = Field(None, description="Take profit percentage")

    # Optimization settings
    optimization_enabled: bool = Field(
        True, description="Enable automatic optimization"
    )
    optimization_frequency: str = Field("daily", description="Optimization frequency")
    optimization_method: OptimizationMethod = Field(
        OptimizationMethod.BAYESIAN_OPTIMIZATION, description="Optimization method"
    )

    # Monitoring settings
    monitoring_enabled: bool = Field(True, description="Enable strategy monitoring")
    performance_threshold: float = Field(
        0.05, description="Performance threshold for alerts"
    )
    risk_threshold: float = Field(0.02, description="Risk threshold for alerts")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )
    created_by: str = Field("system", description="Creator")
    version: str = Field("1.0.0", description="Strategy version")

    class Config:
        use_enum_values = True


class StrategyInstance(BaseModel):
    """Strategy instance model."""

    instance_id: str = Field(..., description="Strategy instance identifier")
    strategy_id: str = Field(..., description="Parent strategy identifier")
    config: StrategyConfig = Field(..., description="Strategy configuration")

    # Instance state
    status: StrategyStatus = Field(StrategyStatus.DRAFT, description="Current status")
    agent_id: Optional[str] = Field(None, description="Associated agent ID")
    deployment_id: Optional[str] = Field(None, description="Deployment ID")

    # Performance tracking
    current_performance: Optional[StrategyPerformance] = Field(
        None, description="Current performance"
    )
    historical_performance: List[StrategyPerformance] = Field(
        default_factory=list, description="Historical performance"
    )

    # Instance metadata
    started_at: Optional[datetime] = Field(None, description="Start time")
    stopped_at: Optional[datetime] = Field(None, description="Stop time")
    last_optimization: Optional[datetime] = Field(
        None, description="Last optimization time"
    )

    class Config:
        use_enum_values = True


class StrategyManager:
    """Strategy management system for handling strategy lifecycle."""

    def __init__(self, backtest_engine: Optional[BaseBacktestEngine] = None):
        self.backtest_engine = backtest_engine
        self.logger = logging.getLogger(__name__)

        # Strategy storage
        self.strategies: Dict[str, StrategyConfig] = {}
        self.strategy_instances: Dict[str, StrategyInstance] = {}
        self.active_instances: Dict[str, StrategyInstance] = {}

        # Strategy handlers
        self.strategy_handlers: Dict[StrategyType, Callable] = {}
        self.optimization_handlers: Dict[OptimizationMethod, Callable] = {}

        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []

        # Statistics
        self.stats = {
            "strategies_registered": 0,
            "instances_created": 0,
            "instances_active": 0,
            "optimizations_performed": 0,
            "deployments_successful": 0,
            "deployments_failed": 0,
            "start_time": None,
        }

        # Management state
        self.is_running = False
        self.management_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize the strategy manager."""
        try:
            self.logger.info("Initializing strategy manager...")

            # Register default strategy handlers
            await self._register_default_handlers()

            # Start management task
            self.management_task = asyncio.create_task(self._strategy_management_loop())

            self.is_running = True
            self.stats["start_time"] = datetime.now()
            self.logger.info("Strategy manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize strategy manager: {e}")
            return False

    async def _register_default_handlers(self) -> None:
        """Register default strategy and optimization handlers."""
        try:
            # Register strategy handlers
            self.strategy_handlers[StrategyType.MOMENTUM] = (
                self._handle_momentum_strategy
            )
            self.strategy_handlers[StrategyType.MEAN_REVERSION] = (
                self._handle_mean_reversion_strategy
            )
            self.strategy_handlers[StrategyType.ARBITRAGE] = (
                self._handle_arbitrage_strategy
            )
            self.strategy_handlers[StrategyType.MARKET_MAKING] = (
                self._handle_market_making_strategy
            )
            self.strategy_handlers[StrategyType.TREND_FOLLOWING] = (
                self._handle_trend_following_strategy
            )
            self.strategy_handlers[StrategyType.CONTRARIAN] = (
                self._handle_contrarian_strategy
            )
            self.strategy_handlers[StrategyType.STATISTICAL_ARBITRAGE] = (
                self._handle_statistical_arbitrage_strategy
            )
            self.strategy_handlers[StrategyType.MACHINE_LEARNING] = (
                self._handle_machine_learning_strategy
            )

            # Register optimization handlers
            self.optimization_handlers[OptimizationMethod.GRID_SEARCH] = (
                self._optimize_grid_search
            )
            self.optimization_handlers[OptimizationMethod.RANDOM_SEARCH] = (
                self._optimize_random_search
            )
            self.optimization_handlers[OptimizationMethod.BAYESIAN_OPTIMIZATION] = (
                self._optimize_bayesian
            )
            self.optimization_handlers[OptimizationMethod.GENETIC_ALGORITHM] = (
                self._optimize_genetic
            )
            self.optimization_handlers[OptimizationMethod.PARTICLE_SWARM] = (
                self._optimize_particle_swarm
            )
            self.optimization_handlers[OptimizationMethod.SIMULATED_ANNEALING] = (
                self._optimize_simulated_annealing
            )

            self.logger.info(
                f"Registered {len(self.strategy_handlers)} strategy handlers and {len(self.optimization_handlers)} optimization handlers"
            )

        except Exception as e:
            self.logger.error(f"Error registering default handlers: {e}")

    async def _strategy_management_loop(self) -> None:
        """Main strategy management loop."""
        while self.is_running:
            try:
                # Monitor active strategies
                await self._monitor_active_strategies()

                # Perform scheduled optimizations
                await self._perform_scheduled_optimizations()

                # Update performance metrics
                await self._update_performance_metrics()

                # Wait for next cycle
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error in strategy management loop: {e}")
                await asyncio.sleep(5)

    async def _monitor_active_strategies(self) -> None:
        """Monitor active strategy instances."""
        try:
            for instance_id, instance in self.active_instances.items():
                # Check strategy health
                health_status = await self._check_strategy_health(instance)

                if health_status["status"] != "healthy":
                    self.logger.warning(
                        f"Strategy instance {instance_id} is unhealthy: {health_status['message']}"
                    )

                    # Take corrective action
                    await self._handle_unhealthy_strategy(instance, health_status)

                # Update performance
                await self._update_instance_performance(instance)

        except Exception as e:
            self.logger.error(f"Error monitoring active strategies: {e}")

    async def _perform_scheduled_optimizations(self) -> None:
        """Perform scheduled strategy optimizations."""
        try:
            for instance_id, instance in self.active_instances.items():
                if not instance.config.optimization_enabled:
                    continue

                # Check if optimization is due
                if await self._is_optimization_due(instance):
                    self.logger.info(
                        f"Performing optimization for strategy {instance_id}"
                    )

                    # Perform optimization
                    optimization_result = await self._optimize_strategy(instance)

                    if optimization_result["success"]:
                        # Apply optimized parameters
                        await self._apply_optimized_parameters(
                            instance, optimization_result["parameters"]
                        )
                        instance.last_optimization = datetime.now()
                        self.stats["optimizations_performed"] += 1
                    else:
                        self.logger.warning(
                            f"Optimization failed for strategy {instance_id}: {optimization_result['error']}"
                        )

        except Exception as e:
            self.logger.error(f"Error performing scheduled optimizations: {e}")

    async def _update_performance_metrics(self) -> None:
        """Update performance metrics for all strategies."""
        try:
            for instance_id, instance in self.active_instances.items():
                # Get current performance
                current_performance = await self._get_current_performance(instance)

                if current_performance:
                    instance.current_performance = current_performance
                    instance.historical_performance.append(current_performance)

                    # Keep only recent performance history
                    if len(instance.historical_performance) > 1000:
                        instance.historical_performance = (
                            instance.historical_performance[-1000:]
                        )

        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")

    # Strategy registration and management
    async def register_strategy(self, config: StrategyConfig) -> bool:
        """Register a new strategy."""
        try:
            # Validate strategy configuration
            if not await self._validate_strategy_config(config):
                return False

            # Store strategy
            self.strategies[config.strategy_id] = config
            self.stats["strategies_registered"] += 1

            self.logger.info(
                f"Strategy registered: {config.name} ({config.strategy_id})"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error registering strategy: {e}")
            return False

    async def create_strategy_instance(
        self, strategy_id: str, agent_id: Optional[str] = None
    ) -> Optional[str]:
        """Create a new strategy instance."""
        try:
            if strategy_id not in self.strategies:
                self.logger.error(f"Strategy not found: {strategy_id}")
                return None

            # Create instance
            instance_id = f"instance_{uuid.uuid4().hex[:8]}"
            config = self.strategies[strategy_id]

            instance = StrategyInstance(
                instance_id=instance_id,
                strategy_id=strategy_id,
                config=config,
                agent_id=agent_id,
            )

            # Store instance
            self.strategy_instances[instance_id] = instance
            self.stats["instances_created"] += 1

            self.logger.info(
                f"Strategy instance created: {instance_id} for strategy {strategy_id}"
            )
            return instance_id

        except Exception as e:
            self.logger.error(f"Error creating strategy instance: {e}")
            return None

    async def deploy_strategy(self, instance_id: str) -> bool:
        """Deploy a strategy instance."""
        try:
            if instance_id not in self.strategy_instances:
                self.logger.error(f"Strategy instance not found: {instance_id}")
                return False

            instance = self.strategy_instances[instance_id]

            # Check if strategy can be deployed
            if not await self._can_deploy_strategy(instance):
                return False

            # Deploy strategy
            deployment_result = await self._deploy_strategy_instance(instance)

            if deployment_result["success"]:
                instance.status = StrategyStatus.ACTIVE
                instance.started_at = datetime.now()
                instance.deployment_id = deployment_result["deployment_id"]

                # Add to active instances
                self.active_instances[instance_id] = instance
                self.stats["instances_active"] += 1
                self.stats["deployments_successful"] += 1

                self.logger.info(f"Strategy deployed successfully: {instance_id}")
                return True
            else:
                self.stats["deployments_failed"] += 1
                self.logger.error(
                    f"Strategy deployment failed: {instance_id} - {deployment_result['error']}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error deploying strategy: {e}")
            return False

    async def stop_strategy(self, instance_id: str) -> bool:
        """Stop a strategy instance."""
        try:
            if instance_id not in self.strategy_instances:
                self.logger.error(f"Strategy instance not found: {instance_id}")
                return False

            instance = self.strategy_instances[instance_id]

            # Stop strategy
            stop_result = await self._stop_strategy_instance(instance)

            if stop_result["success"]:
                instance.status = StrategyStatus.STOPPED
                instance.stopped_at = datetime.now()

                # Remove from active instances
                if instance_id in self.active_instances:
                    del self.active_instances[instance_id]
                    self.stats["instances_active"] -= 1

                self.logger.info(f"Strategy stopped: {instance_id}")
                return True
            else:
                self.logger.error(
                    f"Strategy stop failed: {instance_id} - {stop_result['error']}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error stopping strategy: {e}")
            return False

    async def optimize_strategy(
        self, instance_id: str, method: Optional[OptimizationMethod] = None
    ) -> Dict[str, Any]:
        """Optimize a strategy instance."""
        try:
            if instance_id not in self.strategy_instances:
                return {"success": False, "error": "Strategy instance not found"}

            instance = self.strategy_instances[instance_id]

            # Use specified method or strategy default
            optimization_method = method or instance.config.optimization_method

            # Perform optimization
            result = await self._optimize_strategy(instance, optimization_method)

            if result["success"]:
                instance.last_optimization = datetime.now()
                self.stats["optimizations_performed"] += 1

            return result

        except Exception as e:
            self.logger.error(f"Error optimizing strategy: {e}")
            return {"success": False, "error": str(e)}

    # Strategy handlers
    async def _handle_momentum_strategy(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Handle momentum strategy execution."""
        try:
            # Momentum strategy logic
            # In real implementation, this would execute the actual strategy
            return {"success": True, "message": "Momentum strategy executed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_mean_reversion_strategy(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Handle mean reversion strategy execution."""
        try:
            # Mean reversion strategy logic
            return {"success": True, "message": "Mean reversion strategy executed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_arbitrage_strategy(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Handle arbitrage strategy execution."""
        try:
            # Arbitrage strategy logic
            return {"success": True, "message": "Arbitrage strategy executed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_market_making_strategy(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Handle market making strategy execution."""
        try:
            # Market making strategy logic
            return {"success": True, "message": "Market making strategy executed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_trend_following_strategy(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Handle trend following strategy execution."""
        try:
            # Trend following strategy logic
            return {"success": True, "message": "Trend following strategy executed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_contrarian_strategy(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Handle contrarian strategy execution."""
        try:
            # Contrarian strategy logic
            return {"success": True, "message": "Contrarian strategy executed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_statistical_arbitrage_strategy(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Handle statistical arbitrage strategy execution."""
        try:
            # Statistical arbitrage strategy logic
            return {
                "success": True,
                "message": "Statistical arbitrage strategy executed",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_machine_learning_strategy(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Handle machine learning strategy execution."""
        try:
            # Machine learning strategy logic
            return {"success": True, "message": "Machine learning strategy executed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # Optimization handlers
    async def _optimize_grid_search(self, instance: StrategyInstance) -> Dict[str, Any]:
        """Optimize strategy using grid search."""
        try:
            # Grid search optimization logic
            return {"success": True, "parameters": {}, "performance": 0.0}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _optimize_random_search(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Optimize strategy using random search."""
        try:
            # Random search optimization logic
            return {"success": True, "parameters": {}, "performance": 0.0}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _optimize_bayesian(self, instance: StrategyInstance) -> Dict[str, Any]:
        """Optimize strategy using Bayesian optimization."""
        try:
            # Bayesian optimization logic
            return {"success": True, "parameters": {}, "performance": 0.0}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _optimize_genetic(self, instance: StrategyInstance) -> Dict[str, Any]:
        """Optimize strategy using genetic algorithm."""
        try:
            # Genetic algorithm optimization logic
            return {"success": True, "parameters": {}, "performance": 0.0}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _optimize_particle_swarm(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Optimize strategy using particle swarm optimization."""
        try:
            # Particle swarm optimization logic
            return {"success": True, "parameters": {}, "performance": 0.0}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _optimize_simulated_annealing(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Optimize strategy using simulated annealing."""
        try:
            # Simulated annealing optimization logic
            return {"success": True, "parameters": {}, "performance": 0.0}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper methods
    async def _validate_strategy_config(self, config: StrategyConfig) -> bool:
        """Validate strategy configuration."""
        try:
            # Basic validation
            if not config.name or not config.strategy_id:
                return False

            # Parameter validation
            if config.max_position_size <= 0:
                return False

            if config.max_drawdown < 0 or config.max_drawdown > 1:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating strategy config: {e}")
            return False

    async def _can_deploy_strategy(self, instance: StrategyInstance) -> bool:
        """Check if strategy can be deployed."""
        try:
            # Check if strategy is in valid state
            if instance.status not in [StrategyStatus.DRAFT, StrategyStatus.STOPPED]:
                return False

            # Check resource availability
            # In real implementation, check system resources

            return True

        except Exception as e:
            self.logger.error(f"Error checking deployment capability: {e}")
            return False

    async def _deploy_strategy_instance(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Deploy a strategy instance."""
        try:
            # Get strategy handler
            handler = self.strategy_handlers.get(instance.config.strategy_type)
            if not handler:
                return {
                    "success": False,
                    "error": f"No handler for strategy type {instance.config.strategy_type}",
                }

            # Execute strategy handler
            result = await handler(instance)

            if result["success"]:
                return {
                    "success": True,
                    "deployment_id": f"deploy_{uuid.uuid4().hex[:8]}",
                    "message": result.get("message", "Strategy deployed successfully"),
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown deployment error"),
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _stop_strategy_instance(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Stop a strategy instance."""
        try:
            # Stop strategy execution
            # In real implementation, this would stop the actual strategy

            return {"success": True, "message": "Strategy stopped successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _check_strategy_health(
        self, instance: StrategyInstance
    ) -> Dict[str, Any]:
        """Check strategy health status."""
        try:
            # Basic health checks
            if instance.status != StrategyStatus.ACTIVE:
                return {"status": "unhealthy", "message": "Strategy is not active"}

            # Performance checks
            if instance.current_performance:
                if instance.current_performance.sharpe_ratio < -2.0:
                    return {"status": "unhealthy", "message": "Sharpe ratio too low"}

                if (
                    instance.current_performance.max_drawdown
                    > instance.config.max_drawdown
                ):
                    return {
                        "status": "unhealthy",
                        "message": "Drawdown exceeds threshold",
                    }

            return {"status": "healthy", "message": "Strategy is healthy"}

        except Exception as e:
            return {"status": "unhealthy", "message": f"Health check failed: {str(e)}"}

    async def _handle_unhealthy_strategy(
        self, instance: StrategyInstance, health_status: Dict[str, Any]
    ) -> None:
        """Handle unhealthy strategy."""
        try:
            self.logger.warning(
                f"Handling unhealthy strategy {instance.instance_id}: {health_status['message']}"
            )

            # Take corrective action based on health status
            if "drawdown" in health_status["message"].lower():
                # Pause strategy due to high drawdown
                instance.status = StrategyStatus.PAUSED
                self.logger.info(
                    f"Strategy {instance.instance_id} paused due to high drawdown"
                )

            elif "sharpe" in health_status["message"].lower():
                # Stop strategy due to poor performance
                await self.stop_strategy(instance.instance_id)
                self.logger.info(
                    f"Strategy {instance.instance_id} stopped due to poor performance"
                )

        except Exception as e:
            self.logger.error(f"Error handling unhealthy strategy: {e}")

    async def _update_instance_performance(self, instance: StrategyInstance) -> None:
        """Update strategy instance performance."""
        try:
            # In real implementation, this would get actual performance data
            # For now, simulate performance update
            pass

        except Exception as e:
            self.logger.error(f"Error updating instance performance: {e}")

    async def _is_optimization_due(self, instance: StrategyInstance) -> bool:
        """Check if optimization is due for a strategy."""
        try:
            if not instance.config.optimization_enabled:
                return False

            if not instance.last_optimization:
                return True  # Never optimized

            # Check frequency
            frequency = instance.config.optimization_frequency
            now = datetime.now()

            if frequency == "daily":
                return (now - instance.last_optimization).days >= 1
            elif frequency == "weekly":
                return (now - instance.last_optimization).days >= 7
            elif frequency == "monthly":
                return (now - instance.last_optimization).days >= 30

            return False

        except Exception as e:
            self.logger.error(f"Error checking optimization due: {e}")
            return False

    async def _optimize_strategy(
        self, instance: StrategyInstance, method: OptimizationMethod
    ) -> Dict[str, Any]:
        """Optimize a strategy using specified method."""
        try:
            handler = self.optimization_handlers.get(method)
            if not handler:
                return {
                    "success": False,
                    "error": f"No optimization handler for method {method}",
                }

            return await handler(instance)

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _apply_optimized_parameters(
        self, instance: StrategyInstance, parameters: Dict[str, Any]
    ) -> None:
        """Apply optimized parameters to strategy instance."""
        try:
            # Update strategy parameters
            instance.config.parameters.update(parameters)
            instance.config.updated_at = datetime.now()

            self.logger.info(
                f"Applied optimized parameters to strategy {instance.instance_id}"
            )

        except Exception as e:
            self.logger.error(f"Error applying optimized parameters: {e}")

    async def _get_current_performance(
        self, instance: StrategyInstance
    ) -> Optional[StrategyPerformance]:
        """Get current performance for strategy instance."""
        try:
            # In real implementation, this would get actual performance data
            # For now, return None
            return None

        except Exception as e:
            self.logger.error(f"Error getting current performance: {e}")
            return None

    # Public methods
    def get_strategy(self, strategy_id: str) -> Optional[StrategyConfig]:
        """Get strategy configuration by ID."""
        return self.strategies.get(strategy_id)

    def get_strategy_instance(self, instance_id: str) -> Optional[StrategyInstance]:
        """Get strategy instance by ID."""
        return self.strategy_instances.get(instance_id)

    def get_active_strategies(self) -> List[StrategyInstance]:
        """Get all active strategy instances."""
        return list(self.active_instances.values())

    def get_strategy_statistics(self) -> Dict[str, Any]:
        """Get strategy management statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "total_strategies": len(self.strategies),
            "total_instances": len(self.strategy_instances),
            "active_instances": len(self.active_instances),
            "stats": self.stats.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the strategy manager."""
        try:
            self.logger.info("Shutting down strategy manager...")
            self.is_running = False

            # Stop all active strategies
            for instance_id in list(self.active_instances.keys()):
                await self.stop_strategy(instance_id)

            # Cancel management task
            if self.management_task:
                self.management_task.cancel()
                try:
                    await self.management_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Strategy manager shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during strategy manager shutdown: {e}")
