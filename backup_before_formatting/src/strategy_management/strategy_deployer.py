"""Strategy deployment system for Hong Kong quantitative trading.

This module provides comprehensive strategy deployment capabilities including
deployment management, rollback strategies, and deployment monitoring.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from .strategy_manager import StrategyInstance, StrategyStatus


class DeploymentStatus(str, Enum):
    """Deployment status levels."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class RollbackStrategy(str, Enum):
    """Rollback strategies."""

    IMMEDIATE = "immediate"
    GRACEFUL = "graceful"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class DeploymentConfig(BaseModel):
    """Deployment configuration model."""

    deployment_id: str = Field(..., description="Deployment identifier")
    strategy_instance_id: str = Field(..., description="Strategy instance identifier")

    # Deployment settings
    deployment_type: str = Field("blue_green", description="Deployment type")
    rollback_strategy: RollbackStrategy = Field(
        RollbackStrategy.GRACEFUL, description="Rollback strategy"
    )
    health_check_timeout: int = Field(300, description="Health check timeout (seconds)")
    max_rollback_attempts: int = Field(3, description="Maximum rollback attempts")

    # Environment settings
    target_environment: str = Field("production", description="Target environment")
    resource_limits: Dict[str, Any] = Field(
        default_factory=dict, description="Resource limits"
    )
    environment_variables: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )

    # Monitoring settings
    monitoring_enabled: bool = Field(True, description="Enable deployment monitoring")
    alert_on_failure: bool = Field(True, description="Alert on deployment failure")
    performance_tracking: bool = Field(True, description="Enable performance tracking")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    created_by: str = Field("system", description="Creator")
    version: str = Field("1.0.0", description="Deployment version")

    class Config:
        use_enum_values = True


class DeploymentResult(BaseModel):
    """Deployment result model."""

    deployment_id: str = Field(..., description="Deployment identifier")
    strategy_instance_id: str = Field(..., description="Strategy instance identifier")

    # Deployment status
    status: DeploymentStatus = Field(..., description="Deployment status")
    success: bool = Field(False, description="Deployment success status")

    # Timing information
    started_at: Optional[datetime] = Field(None, description="Deployment start time")
    completed_at: Optional[datetime] = Field(
        None, description="Deployment completion time"
    )
    duration_seconds: float = Field(0.0, description="Deployment duration in seconds")

    # Deployment details
    deployment_url: Optional[str] = Field(None, description="Deployment URL")
    resource_usage: Dict[str, Any] = Field(
        default_factory=dict, description="Resource usage"
    )
    health_check_results: Dict[str, Any] = Field(
        default_factory=dict, description="Health check results"
    )

    # Error information
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    stack_trace: Optional[str] = Field(None, description="Stack trace if failed")

    # Rollback information
    rollback_attempted: bool = Field(False, description="Rollback attempted")
    rollback_successful: bool = Field(False, description="Rollback successful")
    rollback_reason: Optional[str] = Field(None, description="Rollback reason")

    class Config:
        use_enum_values = True


class StrategyDeployer:
    """Strategy deployment system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Deployment state
        self.active_deployments: Dict[str, DeploymentResult] = {}
        self.deployment_history: List[DeploymentResult] = []
        self.rollback_history: List[Dict[str, Any]] = []

        # Deployment handlers
        self.deployment_handlers: Dict[str, Callable] = {}
        self.rollback_handlers: Dict[RollbackStrategy, Callable] = {}

        # Health check functions
        self.health_checkers: List[Callable] = []

        # Statistics
        self.stats = {
            "deployments_attempted": 0,
            "deployments_successful": 0,
            "deployments_failed": 0,
            "rollbacks_attempted": 0,
            "rollbacks_successful": 0,
            "average_deployment_time": 0.0,
            "start_time": None,
        }

        # Initialize handlers
        self._initialize_handlers()

    def _initialize_handlers(self) -> None:
        """Initialize deployment and rollback handlers."""
        try:
            # Deployment handlers
            self.deployment_handlers["blue_green"] = self._deploy_blue_green
            self.deployment_handlers["rolling"] = self._deploy_rolling
            self.deployment_handlers["canary"] = self._deploy_canary
            self.deployment_handlers["recreate"] = self._deploy_recreate

            # Rollback handlers
            self.rollback_handlers[RollbackStrategy.IMMEDIATE] = (
                self._rollback_immediate
            )
            self.rollback_handlers[RollbackStrategy.GRACEFUL] = self._rollback_graceful
            self.rollback_handlers[RollbackStrategy.SCHEDULED] = (
                self._rollback_scheduled
            )
            self.rollback_handlers[RollbackStrategy.MANUAL] = self._rollback_manual

            self.logger.info(
                f"Initialized {len(self.deployment_handlers)} deployment handlers and {len(self.rollback_handlers)} rollback handlers"
            )

        except Exception as e:
            self.logger.error(f"Error initializing handlers: {e}")

    async def deploy_strategy(
        self, instance: StrategyInstance, config: DeploymentConfig
    ) -> DeploymentResult:
        """Deploy a strategy instance."""
        try:
            self.logger.info(f"Starting deployment for strategy {instance.instance_id}")

            # Create deployment result
            deployment_result = DeploymentResult(
                deployment_id=config.deployment_id,
                strategy_instance_id=instance.instance_id,
                status=DeploymentStatus.PENDING,
                started_at=datetime.now(),
            )

            # Store active deployment
            self.active_deployments[config.deployment_id] = deployment_result
            self.stats["deployments_attempted"] += 1

            try:
                # Update status to in progress
                deployment_result.status = DeploymentStatus.IN_PROGRESS

                # Get deployment handler
                handler = self.deployment_handlers.get(config.deployment_type)
                if not handler:
                    raise ValueError(
                        f"Unknown deployment type: {config.deployment_type}"
                    )

                # Execute deployment
                deployment_success = await handler(instance, config)

                if deployment_success:
                    # Perform health checks
                    health_check_results = await self._perform_health_checks(
                        instance, config
                    )

                    if health_check_results["success"]:
                        deployment_result.status = DeploymentStatus.COMPLETED
                        deployment_result.success = True
                        deployment_result.health_check_results = health_check_results
                        self.stats["deployments_successful"] += 1

                        self.logger.info(
                            f"Deployment completed successfully: {config.deployment_id}"
                        )
                    else:
                        deployment_result.status = DeploymentStatus.FAILED
                        deployment_result.error_message = "Health checks failed"
                        self.stats["deployments_failed"] += 1

                        # Attempt rollback
                        await self._attempt_rollback(
                            deployment_result, config, "Health checks failed"
                        )
                else:
                    deployment_result.status = DeploymentStatus.FAILED
                    deployment_result.error_message = "Deployment handler failed"
                    self.stats["deployments_failed"] += 1

                    # Attempt rollback
                    await self._attempt_rollback(
                        deployment_result, config, "Deployment handler failed"
                    )

            except Exception as e:
                deployment_result.status = DeploymentStatus.FAILED
                deployment_result.success = False
                deployment_result.error_message = str(e)
                deployment_result.error_code = "DEPLOYMENT_ERROR"
                self.stats["deployments_failed"] += 1

                self.logger.error(
                    f"Deployment failed: {config.deployment_id} - {str(e)}"
                )

                # Attempt rollback
                await self._attempt_rollback(deployment_result, config, str(e))

            finally:
                # Update completion time and duration
                deployment_result.completed_at = datetime.now()
                if deployment_result.started_at:
                    deployment_result.duration_seconds = (
                        deployment_result.completed_at - deployment_result.started_at
                    ).total_seconds()

                # Update average deployment time
                self._update_average_deployment_time(deployment_result.duration_seconds)

                # Move to history
                self.deployment_history.append(deployment_result)
                if config.deployment_id in self.active_deployments:
                    del self.active_deployments[config.deployment_id]

            return deployment_result

        except Exception as e:
            self.logger.error(f"Error deploying strategy: {e}")
            return DeploymentResult(
                deployment_id=config.deployment_id,
                strategy_instance_id=instance.instance_id,
                status=DeploymentStatus.FAILED,
                success=False,
                error_message=str(e),
                error_code="DEPLOYMENT_ERROR",
            )

    async def _deploy_blue_green(
        self, instance: StrategyInstance, config: DeploymentConfig
    ) -> bool:
        """Deploy using blue - green strategy."""
        try:
            self.logger.info(
                f"Deploying using blue - green strategy: {config.deployment_id}"
            )

            # Blue - green deployment steps:
            # 1. Deploy to green environment
            # 2. Run health checks
            # 3. Switch traffic to green
            # 4. Keep blue as backup

            # Step 1: Deploy to green environment
            green_deployment = await self._deploy_to_environment(
                instance, config, "green"
            )
            if not green_deployment["success"]:
                return False

            # Step 2: Run health checks on green
            green_health = await self._check_environment_health("green", config)
            if not green_health["healthy"]:
                await self._cleanup_environment("green", config)
                return False

            # Step 3: Switch traffic to green
            traffic_switch = await self._switch_traffic_to_green(config)
            if not traffic_switch["success"]:
                await self._cleanup_environment("green", config)
                return False

            # Step 4: Keep blue as backup (already done)
            self.logger.info(f"Blue - green deployment completed: {config.deployment_id}")
            return True

        except Exception as e:
            self.logger.error(f"Blue - green deployment failed: {e}")
            return False

    async def _deploy_rolling(
        self, instance: StrategyInstance, config: DeploymentConfig
    ) -> bool:
        """Deploy using rolling update strategy."""
        try:
            self.logger.info(
                f"Deploying using rolling update strategy: {config.deployment_id}"
            )

            # Rolling deployment steps:
            # 1. Get current instances
            # 2. Deploy new instances gradually
            # 3. Remove old instances
            # 4. Verify deployment

            # Step 1: Get current instances
            current_instances = await self._get_current_instances(instance)

            # Step 2: Deploy new instances gradually
            new_instances = []
            for i, old_instance in enumerate(current_instances):
                new_instance = await self._deploy_new_instance(
                    instance, config, f"rolling_{i}"
                )
                if not new_instance["success"]:
                    # Rollback already deployed instances
                    await self._rollback_rolling_deployment(new_instances, config)
                    return False

                new_instances.append(new_instance)

                # Wait for health check
                health_check = await self._check_instance_health(
                    new_instance["instance_id"], config
                )
                if not health_check["healthy"]:
                    await self._rollback_rolling_deployment(new_instances, config)
                    return False

            # Step 3: Remove old instances
            for old_instance in current_instances:
                await self._remove_old_instance(old_instance["instance_id"], config)

            # Step 4: Verify deployment
            final_health = await self._verify_rolling_deployment(new_instances, config)
            if not final_health["success"]:
                return False

            self.logger.info(f"Rolling deployment completed: {config.deployment_id}")
            return True

        except Exception as e:
            self.logger.error(f"Rolling deployment failed: {e}")
            return False

    async def _deploy_canary(
        self, instance: StrategyInstance, config: DeploymentConfig
    ) -> bool:
        """Deploy using canary strategy."""
        try:
            self.logger.info(f"Deploying using canary strategy: {config.deployment_id}")

            # Canary deployment steps:
            # 1. Deploy to small percentage of traffic
            # 2. Monitor performance
            # 3. Gradually increase traffic
            # 4. Full deployment or rollback

            # Step 1: Deploy to small percentage
            canary_deployment = await self._deploy_canary_instance(
                instance, config, 10
            )  # 10% traffic
            if not canary_deployment["success"]:
                return False

            # Step 2: Monitor performance
            monitoring_result = await self._monitor_canary_performance(
                canary_deployment["instance_id"], config
            )
            if not monitoring_result["success"]:
                await self._rollback_canary_deployment(
                    canary_deployment["instance_id"], config
                )
                return False

            # Step 3: Gradually increase traffic
            traffic_percentages = [25, 50, 75, 100]
            for percentage in traffic_percentages:
                traffic_increase = await self._increase_canary_traffic(
                    canary_deployment["instance_id"], percentage, config
                )
                if not traffic_increase["success"]:
                    await self._rollback_canary_deployment(
                        canary_deployment["instance_id"], config
                    )
                    return False

                # Monitor after each increase
                monitoring_result = await self._monitor_canary_performance(
                    canary_deployment["instance_id"], config
                )
                if not monitoring_result["success"]:
                    await self._rollback_canary_deployment(
                        canary_deployment["instance_id"], config
                    )
                    return False

            self.logger.info(f"Canary deployment completed: {config.deployment_id}")
            return True

        except Exception as e:
            self.logger.error(f"Canary deployment failed: {e}")
            return False

    async def _deploy_recreate(
        self, instance: StrategyInstance, config: DeploymentConfig
    ) -> bool:
        """Deploy using recreate strategy."""
        try:
            self.logger.info(
                f"Deploying using recreate strategy: {config.deployment_id}"
            )

            # Recreate deployment steps:
            # 1. Stop all current instances
            # 2. Deploy new instances
            # 3. Verify deployment

            # Step 1: Stop all current instances
            stop_result = await self._stop_all_instances(instance, config)
            if not stop_result["success"]:
                return False

            # Step 2: Deploy new instances
            new_deployment = await self._deploy_new_instances(instance, config)
            if not new_deployment["success"]:
                return False

            # Step 3: Verify deployment
            verification = await self._verify_recreate_deployment(
                new_deployment["instances"], config
            )
            if not verification["success"]:
                return False

            self.logger.info(f"Recreate deployment completed: {config.deployment_id}")
            return True

        except Exception as e:
            self.logger.error(f"Recreate deployment failed: {e}")
            return False

    async def rollback_deployment(
        self, deployment_id: str, reason: str = "Manual rollback"
    ) -> bool:
        """Rollback a deployment."""
        try:
            self.logger.info(f"Starting rollback for deployment {deployment_id}")

            # Find deployment
            deployment = None
            for d in self.deployment_history:
                if d.deployment_id == deployment_id:
                    deployment = d
                    break

            if not deployment:
                self.logger.error(f"Deployment not found: {deployment_id}")
                return False

            # Get rollback strategy
            rollback_strategy = RollbackStrategy.GRACEFUL  # Default strategy

            # Get rollback handler
            handler = self.rollback_handlers.get(rollback_strategy)
            if not handler:
                self.logger.error(
                    f"No rollback handler for strategy: {rollback_strategy}"
                )
                return False

            # Execute rollback
            rollback_success = await handler(deployment, reason)

            if rollback_success:
                deployment.rollback_attempted = True
                deployment.rollback_successful = True
                deployment.rollback_reason = reason
                deployment.status = DeploymentStatus.ROLLED_BACK

                self.stats["rollbacks_attempted"] += 1
                self.stats["rollbacks_successful"] += 1

                self.logger.info(f"Rollback completed successfully: {deployment_id}")
            else:
                deployment.rollback_attempted = True
                deployment.rollback_successful = False
                deployment.rollback_reason = reason

                self.stats["rollbacks_attempted"] += 1

                self.logger.error(f"Rollback failed: {deployment_id}")

            return rollback_success

        except Exception as e:
            self.logger.error(f"Error rolling back deployment: {e}")
            return False

    async def _rollback_immediate(
        self, deployment: DeploymentResult, reason: str
    ) -> bool:
        """Immediate rollback strategy."""
        try:
            self.logger.info(
                f"Executing immediate rollback: {deployment.deployment_id}"
            )

            # Immediate rollback: stop everything immediately
            stop_result = await self._stop_deployment_immediately(deployment)
            if not stop_result["success"]:
                return False

            # Restore previous version
            restore_result = await self._restore_previous_version(deployment)
            if not restore_result["success"]:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Immediate rollback failed: {e}")
            return False

    async def _rollback_graceful(
        self, deployment: DeploymentResult, reason: str
    ) -> bool:
        """Graceful rollback strategy."""
        try:
            self.logger.info(f"Executing graceful rollback: {deployment.deployment_id}")

            # Graceful rollback: allow current operations to complete
            graceful_stop_result = await self._stop_deployment_gracefully(deployment)
            if not graceful_stop_result["success"]:
                return False

            # Restore previous version
            restore_result = await self._restore_previous_version(deployment)
            if not restore_result["success"]:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Graceful rollback failed: {e}")
            return False

    async def _rollback_scheduled(
        self, deployment: DeploymentResult, reason: str
    ) -> bool:
        """Scheduled rollback strategy."""
        try:
            self.logger.info(
                f"Executing scheduled rollback: {deployment.deployment_id}"
            )

            # Schedule rollback for later
            rollback_time = datetime.now() + timedelta(minutes=5)  # 5 minutes from now

            # Schedule the rollback
            asyncio.create_task(
                self._execute_scheduled_rollback(deployment, rollback_time)
            )

            return True

        except Exception as e:
            self.logger.error(f"Scheduled rollback failed: {e}")
            return False

    async def _rollback_manual(self, deployment: DeploymentResult, reason: str) -> bool:
        """Manual rollback strategy."""
        try:
            self.logger.info(f"Manual rollback required: {deployment.deployment_id}")

            # Manual rollback: require human intervention
            # In real implementation, this would send alerts to administrators

            self.logger.warning(
                f"Manual rollback required for deployment {deployment.deployment_id}: {reason}"
            )

            # For now, just log the requirement
            return True

        except Exception as e:
            self.logger.error(f"Manual rollback failed: {e}")
            return False

    # Helper methods
    async def _perform_health_checks(
        self, instance: StrategyInstance, config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Perform health checks on deployed strategy."""
        try:
            health_results = {
                "success": True,
                "checks": [],
                "overall_health": "healthy",
            }

            # Run all registered health checkers
            for checker in self.health_checkers:
                try:
                    check_result = await checker(instance, config)
                    health_results["checks"].append(check_result)

                    if not check_result.get("healthy", False):
                        health_results["success"] = False
                        health_results["overall_health"] = "unhealthy"

                except Exception as e:
                    self.logger.error(f"Health check failed: {e}")
                    health_results["checks"].append(
                        {"name": "unknown", "healthy": False, "error": str(e)}
                    )
                    health_results["success"] = False
                    health_results["overall_health"] = "unhealthy"

            return health_results

        except Exception as e:
            self.logger.error(f"Error performing health checks: {e}")
            return {"success": False, "overall_health": "unhealthy", "error": str(e)}

    async def _attempt_rollback(
        self, deployment_result: DeploymentResult, config: DeploymentConfig, reason: str
    ) -> None:
        """Attempt to rollback a failed deployment."""
        try:
            self.logger.info(
                f"Attempting rollback for failed deployment: {deployment_result.deployment_id}"
            )

            # Attempt rollback
            rollback_success = await self.rollback_deployment(
                deployment_result.deployment_id, reason
            )

            if rollback_success:
                self.logger.info(
                    f"Rollback successful: {deployment_result.deployment_id}"
                )
            else:
                self.logger.error(f"Rollback failed: {deployment_result.deployment_id}")

        except Exception as e:
            self.logger.error(f"Error attempting rollback: {e}")

    def _update_average_deployment_time(self, duration: float) -> None:
        """Update average deployment time."""
        try:
            if self.stats["deployments_successful"] > 0:
                current_avg = self.stats["average_deployment_time"]
                new_avg = (
                    (current_avg * (self.stats["deployments_successful"] - 1))
                    + duration
                ) / self.stats["deployments_successful"]
                self.stats["average_deployment_time"] = new_avg
            else:
                self.stats["average_deployment_time"] = duration

        except Exception as e:
            self.logger.error(f"Error updating average deployment time: {e}")

    # Placeholder methods for deployment operations
    async def _deploy_to_environment(
        self, instance: StrategyInstance, config: DeploymentConfig, environment: str
    ) -> Dict[str, Any]:
        """Deploy to specific environment."""
        # Placeholder implementation
        return {"success": True, "environment": environment}

    async def _check_environment_health(
        self, environment: str, config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Check environment health."""
        # Placeholder implementation
        return {"healthy": True, "environment": environment}

    async def _cleanup_environment(
        self, environment: str, config: DeploymentConfig
    ) -> None:
        """Cleanup environment."""
        # Placeholder implementation
        pass

    async def _switch_traffic_to_green(
        self, config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Switch traffic to green environment."""
        # Placeholder implementation
        return {"success": True}

    async def _get_current_instances(
        self, instance: StrategyInstance
    ) -> List[Dict[str, Any]]:
        """Get current instances."""
        # Placeholder implementation
        return []

    async def _deploy_new_instance(
        self, instance: StrategyInstance, config: DeploymentConfig, name: str
    ) -> Dict[str, Any]:
        """Deploy new instance."""
        # Placeholder implementation
        return {"success": True, "instance_id": f"instance_{name}"}

    async def _rollback_rolling_deployment(
        self, instances: List[Dict[str, Any]], config: DeploymentConfig
    ) -> None:
        """Rollback rolling deployment."""
        # Placeholder implementation
        pass

    async def _check_instance_health(
        self, instance_id: str, config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Check instance health."""
        # Placeholder implementation
        return {"healthy": True, "instance_id": instance_id}

    async def _remove_old_instance(
        self, instance_id: str, config: DeploymentConfig
    ) -> None:
        """Remove old instance."""
        # Placeholder implementation
        pass

    async def _verify_rolling_deployment(
        self, instances: List[Dict[str, Any]], config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Verify rolling deployment."""
        # Placeholder implementation
        return {"success": True}

    async def _deploy_canary_instance(
        self,
        instance: StrategyInstance,
        config: DeploymentConfig,
        traffic_percentage: int,
    ) -> Dict[str, Any]:
        """Deploy canary instance."""
        # Placeholder implementation
        return {"success": True, "instance_id": f"canary_{traffic_percentage}"}

    async def _monitor_canary_performance(
        self, instance_id: str, config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Monitor canary performance."""
        # Placeholder implementation
        return {"success": True, "instance_id": instance_id}

    async def _increase_canary_traffic(
        self, instance_id: str, percentage: int, config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Increase canary traffic."""
        # Placeholder implementation
        return {"success": True, "percentage": percentage}

    async def _rollback_canary_deployment(
        self, instance_id: str, config: DeploymentConfig
    ) -> None:
        """Rollback canary deployment."""
        # Placeholder implementation
        pass

    async def _stop_all_instances(
        self, instance: StrategyInstance, config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Stop all instances."""
        # Placeholder implementation
        return {"success": True}

    async def _deploy_new_instances(
        self, instance: StrategyInstance, config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Deploy new instances."""
        # Placeholder implementation
        return {"success": True, "instances": []}

    async def _verify_recreate_deployment(
        self, instances: List[Dict[str, Any]], config: DeploymentConfig
    ) -> Dict[str, Any]:
        """Verify recreate deployment."""
        # Placeholder implementation
        return {"success": True}

    async def _stop_deployment_immediately(
        self, deployment: DeploymentResult
    ) -> Dict[str, Any]:
        """Stop deployment immediately."""
        # Placeholder implementation
        return {"success": True}

    async def _restore_previous_version(
        self, deployment: DeploymentResult
    ) -> Dict[str, Any]:
        """Restore previous version."""
        # Placeholder implementation
        return {"success": True}

    async def _stop_deployment_gracefully(
        self, deployment: DeploymentResult
    ) -> Dict[str, Any]:
        """Stop deployment gracefully."""
        # Placeholder implementation
        return {"success": True}

    async def _execute_scheduled_rollback(
        self, deployment: DeploymentResult, rollback_time: datetime
    ) -> None:
        """Execute scheduled rollback."""
        # Placeholder implementation
        pass

    # Public methods
    def add_health_checker(self, checker: Callable) -> None:
        """Add health checker function."""
        self.health_checkers.append(checker)

    def get_deployment(self, deployment_id: str) -> Optional[DeploymentResult]:
        """Get deployment by ID."""
        # Check active deployments
        if deployment_id in self.active_deployments:
            return self.active_deployments[deployment_id]

        # Check history
        for deployment in self.deployment_history:
            if deployment.deployment_id == deployment_id:
                return deployment

        return None

    def get_active_deployments(self) -> List[DeploymentResult]:
        """Get all active deployments."""
        return list(self.active_deployments.values())

    def get_deployment_history(self, limit: int = 100) -> List[DeploymentResult]:
        """Get deployment history."""
        return self.deployment_history[-limit:] if self.deployment_history else []

    def get_statistics(self) -> Dict[str, Any]:
        """Get deployment statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "uptime_seconds": uptime,
            "active_deployments": len(self.active_deployments),
            "deployment_history_count": len(self.deployment_history),
            "rollback_history_count": len(self.rollback_history),
            "stats": self.stats.copy(),
        }
