"""System initialization for Hong Kong quantitative trading system.

This module provides comprehensive system initialization capabilities including
dependency resolution, initialization sequencing, and system startup validation.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field


class InitializationStatus(str, Enum):
    """Initialization status levels."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class InitializationStep(BaseModel):
    """Initialization step model."""

    step_id: str = Field(..., description="Step identifier")
    step_name: str = Field(..., description="Step name")
    component_id: str = Field(..., description="Component identifier")

    # Step details
    step_type: str = Field(..., description="Step type")
    timeout: int = Field(60, description="Step timeout (seconds)")
    retry_attempts: int = Field(3, description="Retry attempts")
    retry_delay: int = Field(5, description="Retry delay (seconds)")

    # Dependencies
    depends_on: List[str] = Field(default_factory=list, description="Step dependencies")

    # Step metadata
    priority: int = Field(0, description="Step priority")
    parallel: bool = Field(False, description="Can run in parallel")

    class Config:
        use_enum_values = True


class DependencyGraph(BaseModel):
    """Dependency graph model."""

    graph_id: str = Field(..., description="Graph identifier")
    nodes: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Graph nodes"
    )
    edges: List[Tuple[str, str]] = Field(
        default_factory=list, description="Graph edges"
    )

    # Graph metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    total_nodes: int = Field(0, description="Total number of nodes")
    total_edges: int = Field(0, description="Total number of edges")

    class Config:
        use_enum_values = True


class SystemInitializer:
    """System initialization manager."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialization state
        self.initialization_steps: Dict[str, InitializationStep] = {}
        self.step_status: Dict[str, InitializationStatus] = {}
        self.step_results: Dict[str, Any] = {}

        # Dependency management
        self.dependency_graph: Optional[DependencyGraph] = None
        self.resolved_dependencies: Dict[str, Set[str]] = {}

        # Initialization history
        self.initialization_history: List[Dict[str, Any]] = []

        # Statistics
        self.stats = {
            "initializations_attempted": 0,
            "initializations_successful": 0,
            "initializations_failed": 0,
            "steps_executed": 0,
            "steps_failed": 0,
            "dependency_resolutions": 0,
            "start_time": None,
        }

    async def initialize(self) -> bool:
        """Initialize the system initializer."""
        try:
            self.logger.info("Initializing system initializer...")

            # Initialize dependency resolution
            await self._initialize_dependency_resolution()

            self.stats["start_time"] = datetime.now()
            self.logger.info("System initializer initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize system initializer: {e}")
            return False

    async def _initialize_dependency_resolution(self) -> None:
        """Initialize dependency resolution system."""
        try:
            # Initialize dependency tracking
            self.resolved_dependencies = {}

            self.logger.info("Dependency resolution system initialized")

        except Exception as e:
            self.logger.error(f"Error initializing dependency resolution: {e}")

    async def add_initialization_step(self, step: InitializationStep) -> bool:
        """Add an initialization step."""
        try:
            # Validate step
            if not await self._validate_initialization_step(step):
                return False

            # Add step
            self.initialization_steps[step.step_id] = step
            self.step_status[step.step_id] = InitializationStatus.PENDING

            self.logger.debug(f"Initialization step added: {step.step_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error adding initialization step: {e}")
            return False

    async def _validate_initialization_step(self, step: InitializationStep) -> bool:
        """Validate an initialization step."""
        try:
            # Check for duplicate step ID
            if step.step_id in self.initialization_steps:
                self.logger.error(f"Step ID already exists: {step.step_id}")
                return False

            # Validate dependencies
            for dep_id in step.depends_on:
                if dep_id not in self.initialization_steps:
                    self.logger.warning(f"Dependency not found: {dep_id}")
                    # Don't fail for missing dependencies, they might be added later

            return True

        except Exception as e:
            self.logger.error(f"Error validating initialization step: {e}")
            return False

    async def build_dependency_graph(self) -> bool:
        """Build dependency graph from initialization steps."""
        try:
            self.logger.info("Building dependency graph...")

            # Create dependency graph
            graph = DependencyGraph(
                graph_id=f"init_graph_{int(datetime.now().timestamp())}",
                nodes={},
                edges=[],
            )

            # Add nodes
            for step_id, step in self.initialization_steps.items():
                graph.nodes[step_id] = {
                    "step_name": step.step_name,
                    "component_id": step.component_id,
                    "step_type": step.step_type,
                    "priority": step.priority,
                    "parallel": step.parallel,
                }

            # Add edges
            for step_id, step in self.initialization_steps.items():
                for dep_id in step.depends_on:
                    if dep_id in self.initialization_steps:
                        graph.edges.append((dep_id, step_id))

            # Update graph metadata
            graph.total_nodes = len(graph.nodes)
            graph.total_edges = len(graph.edges)

            # Validate graph
            if not await self._validate_dependency_graph(graph):
                return False

            self.dependency_graph = graph
            self.stats["dependency_resolutions"] += 1

            self.logger.info(
                f"Dependency graph built: {graph.total_nodes} nodes, {graph.total_edges} edges"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error building dependency graph: {e}")
            return False

    async def _validate_dependency_graph(self, graph: DependencyGraph) -> bool:
        """Validate dependency graph for cycles."""
        try:
            # Check for cycles using DFS
            visited = set()
            rec_stack = set()

            def has_cycle(node):
                visited.add(node)
                rec_stack.add(node)

                # Check all neighbors
                for edge in graph.edges:
                    if edge[0] == node:
                        neighbor = edge[1]
                        if neighbor not in visited:
                            if has_cycle(neighbor):
                                return True
                        elif neighbor in rec_stack:
                            return True

                rec_stack.remove(node)
                return False

            # Check each node for cycles
            for node in graph.nodes:
                if node not in visited:
                    if has_cycle(node):
                        self.logger.error(
                            "Circular dependency detected in initialization graph"
                        )
                        return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating dependency graph: {e}")
            return False

    async def execute_initialization(self) -> bool:
        """Execute system initialization."""
        try:
            self.logger.info("Starting system initialization...")
            self.stats["initializations_attempted"] += 1

            # Build dependency graph
            if not await self.build_dependency_graph():
                self.logger.error("Failed to build dependency graph")
                return False

            # Create execution plan
            execution_plan = await self._create_execution_plan()

            # Execute plan
            success = await self._execute_initialization_plan(execution_plan)

            if success:
                self.stats["initializations_successful"] += 1
                self.logger.info("System initialization completed successfully")
            else:
                self.stats["initializations_failed"] += 1
                self.logger.error("System initialization failed")

            return success

        except Exception as e:
            self.logger.error(f"Error executing initialization: {e}")
            self.stats["initializations_failed"] += 1
            return False

    async def _create_execution_plan(self) -> List[List[InitializationStep]]:
        """Create execution plan from dependency graph."""
        try:
            if not self.dependency_graph:
                return []

            # Group steps by dependency level
            execution_groups = []
            processed = set()

            while len(processed) < len(self.initialization_steps):
                # Find steps that can be executed (all dependencies processed)
                ready_steps = []

                for step_id, step in self.initialization_steps.items():
                    if step_id in processed:
                        continue

                    # Check if all dependencies are processed
                    if all(dep_id in processed for dep_id in step.depends_on):
                        ready_steps.append(step)

                if not ready_steps:
                    # Circular dependency or error
                    self.logger.error("Circular dependency detected in execution plan")
                    break

                execution_groups.append(ready_steps)
                processed.update(step.step_id for step in ready_steps)

            return execution_groups

        except Exception as e:
            self.logger.error(f"Error creating execution plan: {e}")
            return []

    async def _execute_initialization_plan(
        self, execution_plan: List[List[InitializationStep]]
    ) -> bool:
        """Execute initialization plan."""
        try:
            for group_index, step_group in enumerate(execution_plan):
                self.logger.info(
                    f"Executing initialization group {group_index + 1}/{len(execution_plan)}"
                )

                if len(step_group) == 1:
                    # Single step
                    success = await self._execute_initialization_step(step_group[0])
                    if not success:
                        self.logger.error(
                            f"Initialization step failed: {step_group[0].step_name}"
                        )
                        return False
                else:
                    # Parallel steps
                    success = await self._execute_parallel_initialization_steps(
                        step_group
                    )
                    if not success:
                        self.logger.error("Parallel initialization group failed")
                        return False

            return True

        except Exception as e:
            self.logger.error(f"Error executing initialization plan: {e}")
            return False

    async def _execute_initialization_step(self, step: InitializationStep) -> bool:
        """Execute a single initialization step."""
        try:
            self.logger.info(f"Executing initialization step: {step.step_name}")

            # Update status
            self.step_status[step.step_id] = InitializationStatus.IN_PROGRESS

            # Execute step based on type
            success = await self._execute_step_by_type(step)

            if success:
                self.step_status[step.step_id] = InitializationStatus.COMPLETED
                self.step_results[step.step_id] = {
                    "success": True,
                    "message": "Step completed successfully",
                }
                self.stats["steps_executed"] += 1

                # Record in history
                self.initialization_history.append(
                    {
                        "step_id": step.step_id,
                        "step_name": step.step_name,
                        "component_id": step.component_id,
                        "status": InitializationStatus.COMPLETED.value,
                        "timestamp": datetime.now(),
                        "duration": 0.0,  # Would calculate actual duration
                    }
                )

                self.logger.info(f"Initialization step completed: {step.step_name}")
            else:
                self.step_status[step.step_id] = InitializationStatus.FAILED
                self.step_results[step.step_id] = {
                    "success": False,
                    "message": "Step failed",
                }
                self.stats["steps_failed"] += 1

                # Record in history
                self.initialization_history.append(
                    {
                        "step_id": step.step_id,
                        "step_name": step.step_name,
                        "component_id": step.component_id,
                        "status": InitializationStatus.FAILED.value,
                        "timestamp": datetime.now(),
                        "duration": 0.0,
                    }
                )

                self.logger.error(f"Initialization step failed: {step.step_name}")

            return success

        except Exception as e:
            self.logger.error(
                f"Error executing initialization step {step.step_name}: {e}"
            )
            self.step_status[step.step_id] = InitializationStatus.FAILED
            self.stats["steps_failed"] += 1
            return False

    async def _execute_parallel_initialization_steps(
        self, steps: List[InitializationStep]
    ) -> bool:
        """Execute initialization steps in parallel."""
        try:
            self.logger.info(f"Executing {len(steps)} initialization steps in parallel")

            # Create tasks for parallel execution
            tasks = [self._execute_initialization_step(step) for step in steps]

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

            self.logger.info("Parallel initialization steps completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error executing parallel initialization steps: {e}")
            return False

    async def _execute_step_by_type(self, step: InitializationStep) -> bool:
        """Execute step based on its type."""
        try:
            if step.step_type == "database_init":
                return await self._execute_database_initialization(step)
            elif step.step_type == "cache_init":
                return await self._execute_cache_initialization(step)
            elif step.step_type == "agent_init":
                return await self._execute_agent_initialization(step)
            elif step.step_type == "service_init":
                return await self._execute_service_initialization(step)
            elif step.step_type == "monitoring_init":
                return await self._execute_monitoring_initialization(step)
            elif step.step_type == "integration_init":
                return await self._execute_integration_initialization(step)
            else:
                self.logger.warning(f"Unknown step type: {step.step_type}")
                return await self._execute_generic_initialization(step)

        except Exception as e:
            self.logger.error(f"Error executing step by type: {e}")
            return False

    async def _execute_database_initialization(self, step: InitializationStep) -> bool:
        """Execute database initialization."""
        try:
            self.logger.info(
                f"Initializing database for component: {step.component_id}"
            )

            # Placeholder implementation
            # In real implementation, would initialize database connections, create tables, etc.
            await asyncio.sleep(0.1)  # Simulate initialization delay

            return True

        except Exception as e:
            self.logger.error(f"Error executing database initialization: {e}")
            return False

    async def _execute_cache_initialization(self, step: InitializationStep) -> bool:
        """Execute cache initialization."""
        try:
            self.logger.info(f"Initializing cache for component: {step.component_id}")

            # Placeholder implementation
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            self.logger.error(f"Error executing cache initialization: {e}")
            return False

    async def _execute_agent_initialization(self, step: InitializationStep) -> bool:
        """Execute AI agent initialization."""
        try:
            self.logger.info(f"Initializing AI agent: {step.component_id}")

            # Placeholder implementation
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            self.logger.error(f"Error executing agent initialization: {e}")
            return False

    async def _execute_service_initialization(self, step: InitializationStep) -> bool:
        """Execute service initialization."""
        try:
            self.logger.info(f"Initializing service: {step.component_id}")

            # Placeholder implementation
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            self.logger.error(f"Error executing service initialization: {e}")
            return False

    async def _execute_monitoring_initialization(
        self, step: InitializationStep
    ) -> bool:
        """Execute monitoring initialization."""
        try:
            self.logger.info(f"Initializing monitoring: {step.component_id}")

            # Placeholder implementation
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            self.logger.error(f"Error executing monitoring initialization: {e}")
            return False

    async def _execute_integration_initialization(
        self, step: InitializationStep
    ) -> bool:
        """Execute integration initialization."""
        try:
            self.logger.info(f"Initializing integration: {step.component_id}")

            # Placeholder implementation
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            self.logger.error(f"Error executing integration initialization: {e}")
            return False

    async def _execute_generic_initialization(self, step: InitializationStep) -> bool:
        """Execute generic initialization."""
        try:
            self.logger.info(f"Executing generic initialization: {step.step_name}")

            # Placeholder implementation
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            self.logger.error(f"Error executing generic initialization: {e}")
            return False

    # Public methods
    def get_step_status(self, step_id: str) -> Optional[InitializationStatus]:
        """Get step status."""
        return self.step_status.get(step_id)

    def get_step_result(self, step_id: str) -> Optional[Any]:
        """Get step result."""
        return self.step_results.get(step_id)

    def get_initialization_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get initialization history."""
        return (
            self.initialization_history[-limit:] if self.initialization_history else []
        )

    def get_dependency_graph(self) -> Optional[DependencyGraph]:
        """Get dependency graph."""
        return self.dependency_graph

    def get_statistics(self) -> Dict[str, Any]:
        """Get initializer statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "uptime_seconds": uptime,
            "total_steps": len(self.initialization_steps),
            "completed_steps": len(
                [
                    s
                    for s in self.step_status.values()
                    if s == InitializationStatus.COMPLETED
                ]
            ),
            "failed_steps": len(
                [
                    s
                    for s in self.step_status.values()
                    if s == InitializationStatus.FAILED
                ]
            ),
            "pending_steps": len(
                [
                    s
                    for s in self.step_status.values()
                    if s == InitializationStatus.PENDING
                ]
            ),
            "stats": self.stats.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the system initializer."""
        try:
            self.logger.info("Shutting down system initializer...")

            # Clear initialization data
            self.initialization_steps.clear()
            self.step_status.clear()
            self.step_results.clear()
            self.initialization_history.clear()

            # Clear dependency graph
            self.dependency_graph = None
            self.resolved_dependencies.clear()

            self.logger.info("System initializer shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during system initializer shutdown: {e}")
