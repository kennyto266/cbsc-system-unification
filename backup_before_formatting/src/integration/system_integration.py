"""System integration for Hong Kong quantitative trading.

This module provides comprehensive system integration capabilities including
component orchestration, configuration management, and system lifecycle management.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from .component_orchestrator import ComponentInfo, ComponentOrchestrator, ComponentType
from .config_manager import ConfigManager, EnvironmentConfig
from .health_monitor import HealthCheckResult, SystemHealth, SystemHealthMonitor
from .system_initializer import (
    InitializationStatus,
    InitializationStep,
    SystemInitializer,
)


class SystemStatus(str, Enum):
    """System status levels."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ComponentStatus(str, Enum):
    """Component status levels."""

    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class IntegrationError(Exception):
    """System integration error."""

    pass


class IntegrationConfig(BaseModel):
    """System integration configuration."""

    system_id: str = Field(..., description="System identifier")
    system_name: str = Field(..., description="System name")
    version: str = Field("1.0.0", description="System version")

    # System settings
    auto_start: bool = Field(True, description="Auto start system")
    auto_restart: bool = Field(True, description="Auto restart on failure")
    max_restart_attempts: int = Field(3, description="Maximum restart attempts")
    restart_delay: int = Field(30, description="Restart delay in seconds")

    # Component settings
    component_startup_timeout: int = Field(
        60, description="Component startup timeout (seconds)"
    )
    component_shutdown_timeout: int = Field(
        30, description="Component shutdown timeout (seconds)"
    )
    health_check_interval: int = Field(
        30, description="Health check interval (seconds)"
    )

    # Monitoring settings
    monitoring_enabled: bool = Field(True, description="Enable system monitoring")
    alerting_enabled: bool = Field(True, description="Enable alerting")
    logging_level: str = Field("INFO", description="Logging level")

    # Environment settings
    environment: str = Field(
        "development", description="Environment (development, staging, production)"
    )
    debug_mode: bool = Field(False, description="Debug mode")

    class Config:
        use_enum_values = True


class SystemIntegration:
    """System integration manager."""

    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # System state
        self.status = SystemStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.stop_time: Optional[datetime] = None

        # Component management
        self.components: Dict[str, ComponentInfo] = {}
        self.component_status: Dict[str, ComponentStatus] = {}
        self.component_instances: Dict[str, Any] = {}

        # Integration components
        self.config_manager = ConfigManager()
        self.component_orchestrator = ComponentOrchestrator()
        self.system_initializer = SystemInitializer()
        self.health_monitor = SystemHealthMonitor()

        # System tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            "startup_attempts": 0,
            "shutdown_attempts": 0,
            "restart_attempts": 0,
            "component_failures": 0,
            "health_checks": 0,
            "alerts_triggered": 0,
        }

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "system_started": [],
            "system_stopped": [],
            "component_started": [],
            "component_stopped": [],
            "component_failed": [],
            "health_check_failed": [],
        }

    async def initialize(self) -> bool:
        """Initialize the system integration."""
        try:
            self.logger.info(
                f"Initializing system integration: {self.config.system_name}"
            )

            # Initialize configuration manager
            if not await self.config_manager.initialize():
                self.logger.error("Failed to initialize configuration manager")
                return False

            # Initialize component orchestrator
            if not await self.component_orchestrator.initialize():
                self.logger.error("Failed to initialize component orchestrator")
                return False

            # Initialize system initializer
            if not await self.system_initializer.initialize():
                self.logger.error("Failed to initialize system initializer")
                return False

            # Initialize health monitor
            if not await self.health_monitor.initialize():
                self.logger.error("Failed to initialize health monitor")
                return False

            # Register system components
            await self._register_system_components()

            self.logger.info("System integration initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize system integration: {e}")
            return False

    async def _register_system_components(self) -> None:
        """Register all system components."""
        try:
            # Data adapters
            await self._register_component(
                "data_adapters",
                ComponentType.DATA_ADAPTER,
                "Data adapters for market data ingestion",
            )

            # Backtest engine
            await self._register_component(
                "backtest_engine",
                ComponentType.BACKTEST_ENGINE,
                "Backtesting engine for strategy validation",
            )

            # AI Agents
            await self._register_component(
                "quantitative_analyst",
                ComponentType.AI_AGENT,
                "Quantitative analyst AI agent",
            )

            await self._register_component(
                "quantitative_trader",
                ComponentType.AI_AGENT,
                "Quantitative trader AI agent",
            )

            await self._register_component(
                "portfolio_manager",
                ComponentType.AI_AGENT,
                "Portfolio manager AI agent",
            )

            await self._register_component(
                "risk_analyst", ComponentType.AI_AGENT, "Risk analyst AI agent"
            )

            await self._register_component(
                "data_scientist", ComponentType.AI_AGENT, "Data scientist AI agent"
            )

            await self._register_component(
                "quantitative_engineer",
                ComponentType.AI_AGENT,
                "Quantitative engineer AI agent",
            )

            await self._register_component(
                "research_analyst", ComponentType.AI_AGENT, "Research analyst AI agent"
            )

            # Strategy management
            await self._register_component(
                "strategy_manager",
                ComponentType.STRATEGY_MANAGER,
                "Strategy management system",
            )

            # Monitoring system
            await self._register_component(
                "monitoring_system",
                ComponentType.MONITORING,
                "Real - time monitoring and alerting system",
            )

            # Telegram integration
            await self._register_component(
                "telegram_integration",
                ComponentType.INTEGRATION,
                "Telegram bot integration",
            )

            self.logger.info(f"Registered {len(self.components)} system components")

        except Exception as e:
            self.logger.error(f"Error registering system components: {e}")

    async def _register_component(
        self, component_id: str, component_type: ComponentType, description: str
    ) -> None:
        """Register a system component."""
        try:
            component_info = ComponentInfo(
                component_id=component_id,
                component_type=component_type,
                description=description,
                dependencies=[],
                startup_order=0,
                shutdown_order=0,
            )

            self.components[component_id] = component_info
            self.component_status[component_id] = ComponentStatus.UNINITIALIZED

            self.logger.debug(f"Registered component: {component_id}")

        except Exception as e:
            self.logger.error(f"Error registering component {component_id}: {e}")

    async def start_system(self) -> bool:
        """Start the entire system."""
        try:
            if self.status == SystemStatus.RUNNING:
                self.logger.warning("System is already running")
                return True

            self.logger.info("Starting system...")
            self.status = SystemStatus.STARTING
            self.stats["startup_attempts"] += 1

            # Create orchestration plan
            orchestration_plan = await self.component_orchestrator.create_startup_plan(
                self.components
            )

            # Execute orchestration plan
            startup_success = await self._execute_orchestration_plan(orchestration_plan)

            if startup_success:
                self.status = SystemStatus.RUNNING
                self.start_time = datetime.now()

                # Start monitoring tasks
                await self._start_monitoring_tasks()

                # Trigger event
                await self._trigger_event(
                    "system_started", {"start_time": self.start_time}
                )

                self.logger.info("System started successfully")
                return True
            else:
                self.status = SystemStatus.ERROR
                self.logger.error("System startup failed")
                return False

        except Exception as e:
            self.status = SystemStatus.ERROR
            self.logger.error(f"Error starting system: {e}")
            return False

    async def _execute_orchestration_plan(self, plan: List[InitializationStep]) -> bool:
        """Execute the orchestration plan."""
        try:
            for step in plan:
                self.logger.info(f"Executing step: {step.step_name}")

                # Initialize component
                success = await self._initialize_component(step.component_id)

                if not success:
                    self.logger.error(
                        f"Failed to initialize component: {step.component_id}"
                    )
                    return False

                # Wait for component to be ready
                if not await self._wait_for_component_ready(step.component_id):
                    self.logger.error(f"Component not ready: {step.component_id}")
                    return False

                self.logger.info(
                    f"Component initialized successfully: {step.component_id}"
                )

            return True

        except Exception as e:
            self.logger.error(f"Error executing orchestration plan: {e}")
            return False

    async def _initialize_component(self, component_id: str) -> bool:
        """Initialize a specific component."""
        try:
            if component_id not in self.components:
                self.logger.error(f"Component not found: {component_id}")
                return False

            component_info = self.components[component_id]
            self.component_status[component_id] = ComponentStatus.INITIALIZING

            # Create component instance
            component_instance = await self._create_component_instance(component_info)

            if component_instance:
                self.component_instances[component_id] = component_instance
                self.component_status[component_id] = ComponentStatus.RUNNING

                # Trigger event
                await self._trigger_event(
                    "component_started",
                    {
                        "component_id": component_id,
                        "component_type": component_info.component_type.value,
                    },
                )

                return True
            else:
                self.component_status[component_id] = ComponentStatus.ERROR
                self.stats["component_failures"] += 1

                # Trigger event
                await self._trigger_event(
                    "component_failed",
                    {
                        "component_id": component_id,
                        "error": "Failed to create component instance",
                    },
                )

                return False

        except Exception as e:
            self.logger.error(f"Error initializing component {component_id}: {e}")
            self.component_status[component_id] = ComponentStatus.ERROR
            self.stats["component_failures"] += 1
            return False

    async def _create_component_instance(
        self, component_info: ComponentInfo
    ) -> Optional[Any]:
        """Create a component instance."""
        try:
            # This is a simplified implementation
            # In real implementation, would create actual component instances

            if component_info.component_type == ComponentType.DATA_ADAPTER:
                # Create data adapter instance
                return await self._create_data_adapter_instance(component_info)
            elif component_info.component_type == ComponentType.BACKTEST_ENGINE:
                # Create backtest engine instance
                return await self._create_backtest_engine_instance(component_info)
            elif component_info.component_type == ComponentType.AI_AGENT:
                # Create AI agent instance
                return await self._create_ai_agent_instance(component_info)
            elif component_info.component_type == ComponentType.STRATEGY_MANAGER:
                # Create strategy manager instance
                return await self._create_strategy_manager_instance(component_info)
            elif component_info.component_type == ComponentType.MONITORING:
                # Create monitoring system instance
                return await self._create_monitoring_system_instance(component_info)
            elif component_info.component_type == ComponentType.INTEGRATION:
                # Create integration instance
                return await self._create_integration_instance(component_info)
            else:
                self.logger.warning(
                    f"Unknown component type: {component_info.component_type}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error creating component instance: {e}")
            return None

    async def _create_data_adapter_instance(
        self, component_info: ComponentInfo
    ) -> Optional[Any]:
        """Create data adapter instance."""
        try:
            # Placeholder implementation
            return {"type": "data_adapter", "id": component_info.component_id}
        except Exception as e:
            self.logger.error(f"Error creating data adapter instance: {e}")
            return None

    async def _create_backtest_engine_instance(
        self, component_info: ComponentInfo
    ) -> Optional[Any]:
        """Create backtest engine instance."""
        try:
            # Placeholder implementation
            return {"type": "backtest_engine", "id": component_info.component_id}
        except Exception as e:
            self.logger.error(f"Error creating backtest engine instance: {e}")
            return None

    async def _create_ai_agent_instance(
        self, component_info: ComponentInfo
    ) -> Optional[Any]:
        """Create AI agent instance."""
        try:
            # Placeholder implementation
            return {"type": "ai_agent", "id": component_info.component_id}
        except Exception as e:
            self.logger.error(f"Error creating AI agent instance: {e}")
            return None

    async def _create_strategy_manager_instance(
        self, component_info: ComponentInfo
    ) -> Optional[Any]:
        """Create strategy manager instance."""
        try:
            # Placeholder implementation
            return {"type": "strategy_manager", "id": component_info.component_id}
        except Exception as e:
            self.logger.error(f"Error creating strategy manager instance: {e}")
            return None

    async def _create_monitoring_system_instance(
        self, component_info: ComponentInfo
    ) -> Optional[Any]:
        """Create monitoring system instance."""
        try:
            # Placeholder implementation
            return {"type": "monitoring_system", "id": component_info.component_id}
        except Exception as e:
            self.logger.error(f"Error creating monitoring system instance: {e}")
            return None

    async def _create_integration_instance(
        self, component_info: ComponentInfo
    ) -> Optional[Any]:
        """Create integration instance."""
        try:
            # Placeholder implementation
            return {"type": "integration", "id": component_info.component_id}
        except Exception as e:
            self.logger.error(f"Error creating integration instance: {e}")
            return None

    async def _wait_for_component_ready(
        self, component_id: str, timeout: int = 60
    ) -> bool:
        """Wait for component to be ready."""
        try:
            start_time = datetime.now()

            while (datetime.now() - start_time).total_seconds() < timeout:
                if self.component_status.get(component_id) == ComponentStatus.RUNNING:
                    return True

                await asyncio.sleep(1)

            return False

        except Exception as e:
            self.logger.error(f"Error waiting for component ready: {e}")
            return False

    async def stop_system(self) -> bool:
        """Stop the entire system."""
        try:
            if self.status == SystemStatus.STOPPED:
                self.logger.warning("System is already stopped")
                return True

            self.logger.info("Stopping system...")
            self.status = SystemStatus.STOPPING
            self.stats["shutdown_attempts"] += 1

            # Stop monitoring tasks
            await self._stop_monitoring_tasks()

            # Create shutdown plan
            shutdown_plan = await self.component_orchestrator.create_shutdown_plan(
                self.components
            )

            # Execute shutdown plan
            shutdown_success = await self._execute_shutdown_plan(shutdown_plan)

            if shutdown_success:
                self.status = SystemStatus.STOPPED
                self.stop_time = datetime.now()

                # Trigger event
                await self._trigger_event(
                    "system_stopped", {"stop_time": self.stop_time}
                )

                self.logger.info("System stopped successfully")
                return True
            else:
                self.status = SystemStatus.ERROR
                self.logger.error("System shutdown failed")
                return False

        except Exception as e:
            self.status = SystemStatus.ERROR
            self.logger.error(f"Error stopping system: {e}")
            return False

    async def _execute_shutdown_plan(self, plan: List[InitializationStep]) -> bool:
        """Execute the shutdown plan."""
        try:
            for step in plan:
                self.logger.info(f"Shutting down component: {step.component_id}")

                # Stop component
                success = await self._stop_component(step.component_id)

                if not success:
                    self.logger.warning(
                        f"Failed to stop component: {step.component_id}"
                    )
                    # Continue with other components

                self.logger.info(f"Component stopped: {step.component_id}")

            return True

        except Exception as e:
            self.logger.error(f"Error executing shutdown plan: {e}")
            return False

    async def _stop_component(self, component_id: str) -> bool:
        """Stop a specific component."""
        try:
            if component_id not in self.component_instances:
                self.logger.warning(f"Component instance not found: {component_id}")
                return True

            self.component_status[component_id] = ComponentStatus.STOPPING

            # Stop component instance
            component_instance = self.component_instances[component_id]
            # In real implementation, would call component's stop method

            self.component_status[component_id] = ComponentStatus.STOPPED
            del self.component_instances[component_id]

            # Trigger event
            await self._trigger_event(
                "component_stopped", {"component_id": component_id}
            )

            return True

        except Exception as e:
            self.logger.error(f"Error stopping component {component_id}: {e}")
            self.component_status[component_id] = ComponentStatus.ERROR
            return False

    async def _start_monitoring_tasks(self) -> None:
        """Start monitoring tasks."""
        try:
            if self.config.monitoring_enabled:
                # Start health monitoring
                self.health_check_task = asyncio.create_task(
                    self._health_monitoring_loop()
                )

                # Start system monitoring
                self.monitoring_task = asyncio.create_task(
                    self._system_monitoring_loop()
                )

                self.logger.info("Monitoring tasks started")

        except Exception as e:
            self.logger.error(f"Error starting monitoring tasks: {e}")

    async def _stop_monitoring_tasks(self) -> None:
        """Stop monitoring tasks."""
        try:
            # Cancel health check task
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass

            # Cancel monitoring task
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Monitoring tasks stopped")

        except Exception as e:
            self.logger.error(f"Error stopping monitoring tasks: {e}")

    async def _health_monitoring_loop(self) -> None:
        """Health monitoring loop."""
        while self.status == SystemStatus.RUNNING:
            try:
                # Perform health checks
                health_result = await self.health_monitor.check_system_health()

                # Process health result
                await self._process_health_result(health_result)

                self.stats["health_checks"] += 1

                # Wait for next check
                await asyncio.sleep(self.config.health_check_interval)

            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _system_monitoring_loop(self) -> None:
        """System monitoring loop."""
        while self.status == SystemStatus.RUNNING:
            try:
                # Monitor system components
                await self._monitor_system_components()

                # Wait for next check
                await asyncio.sleep(10)

            except Exception as e:
                self.logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _process_health_result(self, health_result: SystemHealth) -> None:
        """Process health check result."""
        try:
            if health_result.overall_status != "healthy":
                self.logger.warning(
                    f"System health check failed: {health_result.summary}"
                )

                # Trigger event
                await self._trigger_event(
                    "health_check_failed",
                    {
                        "health_result": health_result.model_dump(),
                        "timestamp": datetime.now(),
                    },
                )

                # Handle unhealthy components
                for component_id, component_health in health_result.components.items():
                    if component_health.status != "healthy":
                        await self._handle_unhealthy_component(
                            component_id, component_health
                        )

        except Exception as e:
            self.logger.error(f"Error processing health result: {e}")

    async def _monitor_system_components(self) -> None:
        """Monitor system components."""
        try:
            for component_id, status in self.component_status.items():
                if status == ComponentStatus.ERROR:
                    # Handle failed component
                    await self._handle_failed_component(component_id)
                elif status == ComponentStatus.STOPPED:
                    # Handle stopped component
                    await self._handle_stopped_component(component_id)

        except Exception as e:
            self.logger.error(f"Error monitoring system components: {e}")

    async def _handle_unhealthy_component(
        self, component_id: str, component_health: Any
    ) -> None:
        """Handle unhealthy component."""
        try:
            self.logger.warning(
                f"Component {component_id} is unhealthy: {component_health.message}"
            )

            # Attempt to restart component
            if self.config.auto_restart:
                await self._restart_component(component_id)

        except Exception as e:
            self.logger.error(f"Error handling unhealthy component: {e}")

    async def _handle_failed_component(self, component_id: str) -> None:
        """Handle failed component."""
        try:
            self.logger.error(f"Component {component_id} has failed")

            # Attempt to restart component
            if self.config.auto_restart:
                await self._restart_component(component_id)

        except Exception as e:
            self.logger.error(f"Error handling failed component: {e}")

    async def _handle_stopped_component(self, component_id: str) -> None:
        """Handle stopped component."""
        try:
            self.logger.warning(f"Component {component_id} has stopped")

            # Attempt to restart component
            if self.config.auto_restart:
                await self._restart_component(component_id)

        except Exception as e:
            self.logger.error(f"Error handling stopped component: {e}")

    async def _restart_component(self, component_id: str) -> bool:
        """Restart a component."""
        try:
            if self.stats["restart_attempts"] >= self.config.max_restart_attempts:
                self.logger.error(
                    f"Maximum restart attempts reached for component {component_id}"
                )
                return False

            self.logger.info(f"Restarting component: {component_id}")

            # Stop component
            await self._stop_component(component_id)

            # Wait for restart delay
            await asyncio.sleep(self.config.restart_delay)

            # Start component
            success = await self._initialize_component(component_id)

            if success:
                self.stats["restart_attempts"] += 1
                self.logger.info(f"Component restarted successfully: {component_id}")
            else:
                self.logger.error(f"Failed to restart component: {component_id}")

            return success

        except Exception as e:
            self.logger.error(f"Error restarting component {component_id}: {e}")
            return False

    async def _trigger_event(self, event_name: str, event_data: Dict[str, Any]) -> None:
        """Trigger system event."""
        try:
            if event_name in self.event_handlers:
                for handler in self.event_handlers[event_name]:
                    try:
                        await handler(event_data)
                    except Exception as e:
                        self.logger.error(
                            f"Error in event handler for {event_name}: {e}"
                        )

        except Exception as e:
            self.logger.error(f"Error triggering event {event_name}: {e}")

    # Public methods
    def add_event_handler(self, event_name: str, handler: Callable) -> None:
        """Add event handler."""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status."""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "system_id": self.config.system_id,
            "system_name": self.config.system_name,
            "version": self.config.version,
            "status": self.status.value,
            "uptime_seconds": uptime,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "components": {
                component_id: {
                    "status": status.value,
                    "type": self.components[component_id].component_type.value,
                }
                for component_id, status in self.component_status.items()
            },
            "stats": self.stats.copy(),
        }

    def get_component_status(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Get component status."""
        if component_id not in self.components:
            return None

        return {
            "component_id": component_id,
            "component_type": self.components[component_id].component_type.value,
            "status": self.component_status.get(
                component_id, ComponentStatus.UNINITIALIZED
            ).value,
            "description": self.components[component_id].description,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            "system_status": self.status.value,
            "total_components": len(self.components),
            "running_components": len(
                [
                    c
                    for c, s in self.component_status.items()
                    if s == ComponentStatus.RUNNING
                ]
            ),
            "failed_components": len(
                [
                    c
                    for c, s in self.component_status.items()
                    if s == ComponentStatus.ERROR
                ]
            ),
            "stats": self.stats.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the system integration."""
        try:
            self.logger.info("Shutting down system integration...")

            # Stop system
            await self.stop_system()

            # Shutdown components
            await self.config_manager.shutdown()
            await self.component_orchestrator.shutdown()
            await self.system_initializer.shutdown()
            await self.health_monitor.shutdown()

            self.logger.info("System integration shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during system integration shutdown: {e}")
