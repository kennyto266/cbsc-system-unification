"""Component orchestration for Hong Kong quantitative trading system.

This module provides comprehensive component orchestration capabilities including
dependency management, startup / shutdown orchestration, and component lifecycle management.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    """Component types."""

    DATA_ADAPTER = "data_adapter"
    BACKTEST_ENGINE = "backtest_engine"
    AI_AGENT = "ai_agent"
    STRATEGY_MANAGER = "strategy_manager"
    MONITORING = "monitoring"
    INTEGRATION = "integration"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"
    API_SERVER = "api_server"


class ComponentInfo(BaseModel):
    """Component information model."""

    component_id: str = Field(..., description="Component identifier")
    component_type: ComponentType = Field(..., description="Component type")
    description: str = Field("", description="Component description")

    # Dependencies
    dependencies: List[str] = Field(
        default_factory=list, description="Component dependencies"
    )
    optional_dependencies: List[str] = Field(
        default_factory=list, description="Optional dependencies"
    )

    # Lifecycle
    startup_order: int = Field(0, description="Startup order (lower = earlier)")
    shutdown_order: int = Field(0, description="Shutdown order (lower = earlier)")

    # Configuration
    config_section: Optional[str] = Field(None, description="Configuration section")
    required_config: List[str] = Field(
        default_factory=list, description="Required configuration keys"
    )

    # Health check
    health_check_endpoint: Optional[str] = Field(
        None, description="Health check endpoint"
    )
    health_check_interval: int = Field(
        30, description="Health check interval (seconds)"
    )

    # Resource requirements
    memory_limit: Optional[int] = Field(None, description="Memory limit (MB)")
    cpu_limit: Optional[float] = Field(None, description="CPU limit (cores)")

    class Config:
        use_enum_values = True


class OrchestrationPlan(BaseModel):
    """Orchestration plan model."""

    plan_id: str = Field(..., description="Plan identifier")
    plan_type: str = Field(..., description="Plan type (startup, shutdown)")

    # Plan steps
    steps: List["InitializationStep"] = Field(
        default_factory=list, description="Plan steps"
    )

    # Plan metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Plan creation time"
    )
    estimated_duration: int = Field(0, description="Estimated duration (seconds)")

    class Config:
        use_enum_values = True


class InitializationStep(BaseModel):
    """Initialization step model."""

    step_id: str = Field(..., description="Step identifier")
    step_name: str = Field(..., description="Step name")
    component_id: str = Field(..., description="Component identifier")

    # Step details
    step_type: str = Field(
        ..., description="Step type (initialize, start, stop, cleanup)"
    )
    timeout: int = Field(60, description="Step timeout (seconds)")
    retry_attempts: int = Field(3, description="Retry attempts")
    retry_delay: int = Field(5, description="Retry delay (seconds)")

    # Dependencies
    depends_on: List[str] = Field(default_factory=list, description="Step dependencies")

    # Step metadata
    priority: int = Field(0, description="Step priority (higher = more important)")
    parallel: bool = Field(False, description="Can run in parallel")

    class Config:
        use_enum_values = True


class ComponentOrchestrator:
    """Component orchestration manager."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Component registry
        self.components: Dict[str, ComponentInfo] = {}
        self.component_dependencies: Dict[str, Set[str]] = {}
        self.component_dependents: Dict[str, Set[str]] = {}

        # Orchestration state
        self.active_plans: Dict[str, OrchestrationPlan] = {}
        self.plan_history: List[OrchestrationPlan] = []

        # Statistics
        self.stats = {
            "plans_created": 0,
            "plans_executed": 0,
            "plans_failed": 0,
            "components_orchestrated": 0,
            "start_time": None,
        }

    async def initialize(self) -> bool:
        """Initialize the component orchestrator."""
        try:
            self.logger.info("Initializing component orchestrator...")

            # Initialize dependency tracking
            self._initialize_dependency_tracking()

            self.stats["start_time"] = datetime.now()
            self.logger.info("Component orchestrator initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize component orchestrator: {e}")
            return False

    def _initialize_dependency_tracking(self) -> None:
        """Initialize dependency tracking structures."""
        try:
            # Initialize dependency maps
            for component_id in self.components:
                self.component_dependencies[component_id] = set()
                self.component_dependents[component_id] = set()

            # Build dependency relationships
            for component_id, component_info in self.components.items():
                # Add dependencies
                for dep_id in component_info.dependencies:
                    if dep_id in self.components:
                        self.component_dependencies[component_id].add(dep_id)
                        self.component_dependents[dep_id].add(component_id)

                # Add optional dependencies
                for dep_id in component_info.optional_dependencies:
                    if dep_id in self.components:
                        self.component_dependencies[component_id].add(dep_id)
                        self.component_dependents[dep_id].add(component_id)

            self.logger.info("Dependency tracking initialized")

        except Exception as e:
            self.logger.error(f"Error initializing dependency tracking: {e}")

    async def register_component(self, component_info: ComponentInfo) -> bool:
        """Register a component."""
        try:
            # Validate component info
            if not await self._validate_component_info(component_info):
                return False

            # Register component
            self.components[component_info.component_id] = component_info

            # Update dependency tracking
            self._update_dependency_tracking(component_info)

            self.logger.info(f"Component registered: {component_info.component_id}")
            return True

        except Exception as e:
            self.logger.error(
                f"Error registering component {component_info.component_id}: {e}"
            )
            return False

    async def _validate_component_info(self, component_info: ComponentInfo) -> bool:
        """Validate component information."""
        try:
            # Check for duplicate component ID
            if component_info.component_id in self.components:
                self.logger.error(
                    f"Component ID already exists: {component_info.component_id}"
                )
                return False

            # Validate dependencies
            for dep_id in component_info.dependencies:
                if dep_id not in self.components:
                    self.logger.warning(f"Required dependency not found: {dep_id}")
                    # Don't fail for missing dependencies, they might be registered later

            # Validate optional dependencies
            for dep_id in component_info.optional_dependencies:
                if dep_id not in self.components:
                    self.logger.debug(f"Optional dependency not found: {dep_id}")

            return True

        except Exception as e:
            self.logger.error(f"Error validating component info: {e}")
            return False

    def _update_dependency_tracking(self, component_info: ComponentInfo) -> None:
        """Update dependency tracking for a component."""
        try:
            component_id = component_info.component_id

            # Initialize dependency sets
            if component_id not in self.component_dependencies:
                self.component_dependencies[component_id] = set()
            if component_id not in self.component_dependents:
                self.component_dependents[component_id] = set()

            # Add dependencies
            for dep_id in component_info.dependencies:
                if dep_id in self.components:
                    self.component_dependencies[component_id].add(dep_id)
                    self.component_dependents[dep_id].add(component_id)

            # Add optional dependencies
            for dep_id in component_info.optional_dependencies:
                if dep_id in self.components:
                    self.component_dependencies[component_id].add(dep_id)
                    self.component_dependents[dep_id].add(component_id)

        except Exception as e:
            self.logger.error(f"Error updating dependency tracking: {e}")

    async def create_startup_plan(
        self, components: Dict[str, ComponentInfo]
    ) -> List[InitializationStep]:
        """Create a startup orchestration plan."""
        try:
            self.logger.info("Creating startup orchestration plan...")

            # Create plan
            plan = OrchestrationPlan(
                plan_id=f"startup_{int(datetime.now().timestamp())}",
                plan_type="startup",
            )

            # Build dependency graph
            dependency_graph = self._build_dependency_graph(components)

            # Create startup steps
            steps = await self._create_startup_steps(components, dependency_graph)
            plan.steps = steps

            # Calculate estimated duration
            plan.estimated_duration = sum(step.timeout for step in steps)

            # Store plan
            self.active_plans[plan.plan_id] = plan
            self.plan_history.append(plan)
            self.stats["plans_created"] += 1

            self.logger.info(
                f"Startup plan created: {plan.plan_id} with {len(steps)} steps"
            )
            return steps

        except Exception as e:
            self.logger.error(f"Error creating startup plan: {e}")
            return []

    async def create_shutdown_plan(
        self, components: Dict[str, ComponentInfo]
    ) -> List[InitializationStep]:
        """Create a shutdown orchestration plan."""
        try:
            self.logger.info("Creating shutdown orchestration plan...")

            # Create plan
            plan = OrchestrationPlan(
                plan_id=f"shutdown_{int(datetime.now().timestamp())}",
                plan_type="shutdown",
            )

            # Build reverse dependency graph
            reverse_dependency_graph = self._build_reverse_dependency_graph(components)

            # Create shutdown steps
            steps = await self._create_shutdown_steps(
                components, reverse_dependency_graph
            )
            plan.steps = steps

            # Calculate estimated duration
            plan.estimated_duration = sum(step.timeout for step in steps)

            # Store plan
            self.active_plans[plan.plan_id] = plan
            self.plan_history.append(plan)
            self.stats["plans_created"] += 1

            self.logger.info(
                f"Shutdown plan created: {plan.plan_id} with {len(steps)} steps"
            )
            return steps

        except Exception as e:
            self.logger.error(f"Error creating shutdown plan: {e}")
            return []

    def _build_dependency_graph(
        self, components: Dict[str, ComponentInfo]
    ) -> Dict[str, Set[str]]:
        """Build dependency graph for components."""
        try:
            dependency_graph = {}

            for component_id, component_info in components.items():
                dependencies = set()

                # Add required dependencies
                for dep_id in component_info.dependencies:
                    if dep_id in components:
                        dependencies.add(dep_id)

                # Add optional dependencies
                for dep_id in component_info.optional_dependencies:
                    if dep_id in components:
                        dependencies.add(dep_id)

                dependency_graph[component_id] = dependencies

            return dependency_graph

        except Exception as e:
            self.logger.error(f"Error building dependency graph: {e}")
            return {}

    def _build_reverse_dependency_graph(
        self, components: Dict[str, ComponentInfo]
    ) -> Dict[str, Set[str]]:
        """Build reverse dependency graph for shutdown."""
        try:
            reverse_graph = {}

            for component_id in components:
                reverse_graph[component_id] = set()

            # Build reverse dependencies
            for component_id, component_info in components.items():
                for dep_id in component_info.dependencies:
                    if dep_id in reverse_graph:
                        reverse_graph[dep_id].add(component_id)

                for dep_id in component_info.optional_dependencies:
                    if dep_id in reverse_graph:
                        reverse_graph[dep_id].add(component_id)

            return reverse_graph

        except Exception as e:
            self.logger.error(f"Error building reverse dependency graph: {e}")
            return {}

    async def _create_startup_steps(
        self,
        components: Dict[str, ComponentInfo],
        dependency_graph: Dict[str, Set[str]],
    ) -> List[InitializationStep]:
        """Create startup steps based on dependency graph."""
        try:
            steps = []
            processed = set()

            # Sort components by startup order
            sorted_components = sorted(
                components.items(), key=lambda x: x[1].startup_order
            )

            for component_id, component_info in sorted_components:
                # Create initialization step
                step = InitializationStep(
                    step_id=f"init_{component_id}_{int(datetime.now().timestamp())}",
                    step_name=f"Initialize {component_info.component_id}",
                    component_id=component_id,
                    step_type="initialize",
                    timeout=component_info.health_check_interval * 2,
                    retry_attempts=3,
                    retry_delay=5,
                    depends_on=list(dependency_graph.get(component_id, set())),
                    priority=component_info.startup_order,
                    parallel=len(dependency_graph.get(component_id, set())) == 0,
                )

                steps.append(step)
                processed.add(component_id)

            return steps

        except Exception as e:
            self.logger.error(f"Error creating startup steps: {e}")
            return []

    async def _create_shutdown_steps(
        self,
        components: Dict[str, ComponentInfo],
        reverse_dependency_graph: Dict[str, Set[str]],
    ) -> List[InitializationStep]:
        """Create shutdown steps based on reverse dependency graph."""
        try:
            steps = []

            # Sort components by shutdown order (reverse of startup order)
            sorted_components = sorted(
                components.items(), key=lambda x: -x[1].shutdown_order
            )

            for component_id, component_info in sorted_components:
                # Create shutdown step
                step = InitializationStep(
                    step_id=f"shutdown_{component_id}_{int(datetime.now().timestamp())}",
                    step_name=f"Shutdown {component_info.component_id}",
                    component_id=component_id,
                    step_type="shutdown",
                    timeout=30,
                    retry_attempts=2,
                    retry_delay=3,
                    depends_on=list(reverse_dependency_graph.get(component_id, set())),
                    priority=component_info.shutdown_order,
                    parallel=False,  # Shutdown should be sequential
                )

                steps.append(step)

            return steps

        except Exception as e:
            self.logger.error(f"Error creating shutdown steps: {e}")
            return []

    async def execute_plan(self, plan: OrchestrationPlan) -> bool:
        """Execute an orchestration plan."""
        try:
            self.logger.info(f"Executing orchestration plan: {plan.plan_id}")

            # Group steps by dependencies
            step_groups = self._group_steps_by_dependencies(plan.steps)

            # Execute step groups sequentially
            for group in step_groups:
                if len(group) == 1:
                    # Single step
                    success = await self._execute_step(group[0])
                    if not success:
                        self.logger.error(f"Step failed: {group[0].step_name}")
                        self.stats["plans_failed"] += 1
                        return False
                else:
                    # Parallel steps
                    success = await self._execute_parallel_steps(group)
                    if not success:
                        self.logger.error("Parallel step group failed")
                        self.stats["plans_failed"] += 1
                        return False

            self.stats["plans_executed"] += 1
            self.logger.info(
                f"Orchestration plan executed successfully: {plan.plan_id}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error executing orchestration plan: {e}")
            self.stats["plans_failed"] += 1
            return False

    def _group_steps_by_dependencies(
        self, steps: List[InitializationStep]
    ) -> List[List[InitializationStep]]:
        """Group steps by dependencies for execution."""
        try:
            groups = []
            processed = set()

            while len(processed) < len(steps):
                # Find steps that can be executed (all dependencies processed)
                ready_steps = []

                for step in steps:
                    if step.step_id in processed:
                        continue

                    # Check if all dependencies are processed
                    if all(dep in processed for dep in step.depends_on):
                        ready_steps.append(step)

                if not ready_steps:
                    # Circular dependency or error
                    self.logger.error(
                        "Circular dependency detected in orchestration plan"
                    )
                    break

                groups.append(ready_steps)
                processed.update(step.step_id for step in ready_steps)

            return groups

        except Exception as e:
            self.logger.error(f"Error grouping steps by dependencies: {e}")
            return []

    async def _execute_step(self, step: InitializationStep) -> bool:
        """Execute a single step."""
        try:
            self.logger.info(f"Executing step: {step.step_name}")

            # Execute step based on type
            if step.step_type == "initialize":
                success = await self._execute_initialize_step(step)
            elif step.step_type == "start":
                success = await self._execute_start_step(step)
            elif step.step_type == "stop":
                success = await self._execute_stop_step(step)
            elif step.step_type == "cleanup":
                success = await self._execute_cleanup_step(step)
            else:
                self.logger.error(f"Unknown step type: {step.step_type}")
                return False

            if success:
                self.stats["components_orchestrated"] += 1
                self.logger.info(f"Step completed successfully: {step.step_name}")
            else:
                self.logger.error(f"Step failed: {step.step_name}")

            return success

        except Exception as e:
            self.logger.error(f"Error executing step {step.step_name}: {e}")
            return False

    async def _execute_parallel_steps(self, steps: List[InitializationStep]) -> bool:
        """Execute steps in parallel."""
        try:
            self.logger.info(f"Executing {len(steps)} steps in parallel")

            # Create tasks for parallel execution
            tasks = [self._execute_step(step) for step in steps]

            # Execute tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(
                        f"Step {steps[i].step_name} failed with exception: {result}"
                    )
                    return False
                elif not result:
                    self.logger.error(f"Step {steps[i].step_name} failed")
                    return False

            self.logger.info("Parallel steps completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error executing parallel steps: {e}")
            return False

    async def _execute_initialize_step(self, step: InitializationStep) -> bool:
        """Execute initialization step."""
        try:
            # Placeholder implementation
            # In real implementation, would initialize the actual component
            self.logger.debug(f"Initializing component: {step.component_id}")

            # Simulate initialization delay
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            self.logger.error(f"Error executing initialize step: {e}")
            return False

    async def _execute_start_step(self, step: InitializationStep) -> bool:
        """Execute start step."""
        try:
            # Placeholder implementation
            self.logger.debug(f"Starting component: {step.component_id}")

            # Simulate start delay
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            self.logger.error(f"Error executing start step: {e}")
            return False

    async def _execute_stop_step(self, step: InitializationStep) -> bool:
        """Execute stop step."""
        try:
            # Placeholder implementation
            self.logger.debug(f"Stopping component: {step.component_id}")

            # Simulate stop delay
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            self.logger.error(f"Error executing stop step: {e}")
            return False

    async def _execute_cleanup_step(self, step: InitializationStep) -> bool:
        """Execute cleanup step."""
        try:
            # Placeholder implementation
            self.logger.debug(f"Cleaning up component: {step.component_id}")

            # Simulate cleanup delay
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            self.logger.error(f"Error executing cleanup step: {e}")
            return False

    # Public methods
    def get_component_dependencies(self, component_id: str) -> Set[str]:
        """Get component dependencies."""
        return self.component_dependencies.get(component_id, set())

    def get_component_dependents(self, component_id: str) -> Set[str]:
        """Get component dependents."""
        return self.component_dependents.get(component_id, set())

    def get_component_info(self, component_id: str) -> Optional[ComponentInfo]:
        """Get component information."""
        return self.components.get(component_id)

    def get_all_components(self) -> Dict[str, ComponentInfo]:
        """Get all registered components."""
        return self.components.copy()

    def get_active_plans(self) -> Dict[str, OrchestrationPlan]:
        """Get active orchestration plans."""
        return self.active_plans.copy()

    def get_plan_history(self, limit: int = 100) -> List[OrchestrationPlan]:
        """Get orchestration plan history."""
        return self.plan_history[-limit:] if self.plan_history else []

    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "uptime_seconds": uptime,
            "total_components": len(self.components),
            "active_plans": len(self.active_plans),
            "plan_history_count": len(self.plan_history),
            "stats": self.stats.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the component orchestrator."""
        try:
            self.logger.info("Shutting down component orchestrator...")

            # Clear active plans
            self.active_plans.clear()

            # Clear component registry
            self.components.clear()
            self.component_dependencies.clear()
            self.component_dependents.clear()

            self.logger.info("Component orchestrator shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during component orchestrator shutdown: {e}")

    # --- Backtest helpers ---
    async def compute_backtest_sharpe_maxdd(
        self, returns: List[float], risk_free_rate: float = 0.03
    ) -> Dict[str, float]:
        """Compute Sharpe ratio and Max Drawdown from a sequence of periodic returns.

        Args:
            returns: Periodic returns series (e.g., daily). Values should be decimal returns, not percentages.
            risk_free_rate: Annual risk - free rate used for Sharpe ratio.

        Returns:
            Dict with keys: 'sharpe_ratio', 'max_drawdown'.
        """
        try:
            import math

            if not returns or len(returns) < 2:
                return {"sharpe_ratio": 0.0, "max_drawdown": 0.0}

            # Volatility annualized assuming 252 trading days
            mean_ret = sum(returns) / len(returns)
            variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
            daily_std = math.sqrt(variance)
            volatility = daily_std * math.sqrt(252)

            annualized_return = (1 + mean_ret) ** 252 - 1
            excess_return = annualized_return - risk_free_rate
            sharpe_ratio = (excess_return / volatility) if volatility > 0 else 0.0

            # Max drawdown based on cumulative returns
            cumulative = []
            acc = 1.0
            for r in returns:
                acc *= 1 + r
                cumulative.append(acc)
            peak = cumulative[0]
            max_dd = 0.0
            for v in cumulative:
                if v > peak:
                    peak = v
                dd = (peak - v) / peak if peak > 0 else 0.0
                if dd > max_dd:
                    max_dd = dd

            return {"sharpe_ratio": float(sharpe_ratio), "max_drawdown": float(max_dd)}
        except Exception as e:
            self.logger.error(f"Error computing backtest metrics: {e}")
            return {"sharpe_ratio": 0.0, "max_drawdown": 0.0}
