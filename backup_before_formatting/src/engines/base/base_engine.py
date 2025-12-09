"""
Base Engine Implementation
基礎引擎實現

Provides abstract base class and common interfaces for all analysis engines.
為所有分析引擎提供抽象基類和通用接口。
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ...core.logging import get_logger
from ...core.exceptions import EngineError


class EngineStatus(Enum):
    """Engine status enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    READY = "ready"
    DISABLED = "disabled"


@dataclass
class EngineConfig:
    """Engine configuration."""

    name: str
    version: str = "1.0.0"
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    cache_enabled: bool = True
    cache_ttl: int = 300
    parallel_processing: bool = True
    max_workers: int = 4
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineResult:
    """Standard result format for all engines."""

    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    engine_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "timestamp": self.timestamp.isoformat(),
            "engine_version": self.engine_version
        }


class BaseEngine(ABC):
    """
    Abstract base class for all analysis engines.
    所有分析引擎的抽象基類。

    This class provides common functionality and enforces a consistent interface
    across all analysis engines, ensuring modularity and testability.
    """

    def __init__(self, config: EngineConfig):
        """
        Initialize the base engine.

        Args:
            config: Engine configuration
        """
        self.config = config
        self.status = EngineStatus.IDLE
        self.logger = get_logger(f"engines.{config.name}")
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._error_count = 0
        self._last_error: Optional[str] = None

        self.logger.info(
            "Engine initialized",
            name=config.name,
            version=config.version,
            enabled=config.enabled
        )

    @property
    def is_healthy(self) -> bool:
        """Check if engine is healthy."""
        return (
            self.status != EngineStatus.ERROR and
            self.config.enabled and
            self._error_count < self.config.max_retries
        )

    @property
    def statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        avg_execution_time = (
            self._total_execution_time / max(1, self._execution_count)
        )

        return {
            "execution_count": self._execution_count,
            "total_execution_time": self._total_execution_time,
            "average_execution_time": avg_execution_time,
            "error_count": self._error_count,
            "success_rate": (
                (self._execution_count - self._error_count) /
                max(1, self._execution_count) * 100
            ),
            "status": self.status.value,
            "is_healthy": self.is_healthy
        }

    async def execute(self, data: Dict[str, Any], **kwargs) -> EngineResult:
        """
        Execute the analysis with error handling and timing.

        Args:
            data: Input data for analysis
            **kwargs: Additional parameters

        Returns:
            EngineResult with analysis results
        """
        if not self.config.enabled:
            return EngineResult(
                success=False,
                error=f"Engine {self.config.name} is disabled"
            )

        if self.status == EngineStatus.BUSY:
            return EngineResult(
                success=False,
                error=f"Engine {self.config.name} is busy"
            )

        start_time = datetime.now()
        self.status = EngineStatus.BUSY
        self._execution_count += 1

        try:
            self.logger.debug(
                "Starting engine execution",
                engine=self.config.name,
                data_keys=list(data.keys())
            )

            # Execute the specific analysis
            result_data = await self._analyze(data, **kwargs)

            execution_time = (datetime.now() - start_time).total_seconds()
            self._total_execution_time += execution_time

            self.status = EngineStatus.READY

            result = EngineResult(
                success=True,
                data=result_data,
                execution_time=execution_time,
                engine_version=self.config.version,
                metadata={
                    "engine_name": self.config.name,
                    "data_points": len(data.get("data", [])),
                    "parameters": kwargs
                }
            )

            self.logger.info(
                "Engine execution completed",
                engine=self.config.name,
                execution_time=execution_time,
                data_points=len(data.get("data", []))
            )

            return result

        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            self.status = EngineStatus.ERROR

            execution_time = (datetime.now() - start_time).total_seconds()

            self.logger.error(
                "Engine execution failed",
                engine=self.config.name,
                error=str(e),
                execution_time=execution_time
            )

            return EngineResult(
                success=False,
                error=str(e),
                execution_time=execution_time,
                engine_version=self.config.version
            )

    @abstractmethod
    async def _analyze(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Perform the actual analysis. Must be implemented by subclasses.

        Args:
            data: Input data for analysis
            **kwargs: Additional parameters

        Returns:
            Dictionary with analysis results
        """
        pass

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data. Can be overridden by subclasses.

        Args:
            data: Input data to validate

        Returns:
            True if data is valid, False otherwise
        """
        if not data:
            self.logger.warning("Empty input data provided")
            return False

        if not isinstance(data, dict):
            self.logger.warning("Input data must be a dictionary")
            return False

        return True

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the engine.

        Returns:
            Health check results
        """
        try:
            # Test basic functionality
            test_data = {"test": True, "timestamp": datetime.now().isoformat()}

            if await self.validate_input(test_data):
                test_result = await self.execute(test_data, test_mode=True)

                return {
                    "status": "healthy" if test_result.success else "unhealthy",
                    "last_check": datetime.now().isoformat(),
                    "statistics": self.statistics,
                    "test_result": test_result.success,
                    "config": {
                        "name": self.config.name,
                        "version": self.config.version,
                        "enabled": self.config.enabled
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "last_check": datetime.now().isoformat(),
                    "error": "Input validation failed"
                }

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }

    def reset_statistics(self):
        """Reset engine statistics."""
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._error_count = 0
        self._last_error = None
        self.status = EngineStatus.IDLE

        self.logger.info("Engine statistics reset", engine=self.config.name)

    def get_config(self) -> Dict[str, Any]:
        """Get engine configuration."""
        return {
            "name": self.config.name,
            "version": self.config.version,
            "enabled": self.config.enabled,
            "timeout_seconds": self.config.timeout_seconds,
            "max_retries": self.config.max_retries,
            "cache_enabled": self.config.cache_enabled,
            "cache_ttl": self.config.cache_ttl,
            "parallel_processing": self.config.parallel_processing,
            "max_workers": self.config.max_workers,
            "custom_settings": self.config.custom_settings
        }

    def update_config(self, **kwargs):
        """Update engine configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.debug(
                    "Configuration updated",
                    key=key,
                    value=value
                )
            else:
                self.logger.warning(
                    "Unknown configuration parameter",
                    key=key
                )

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.config.name}, status={self.status.value})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"{self.__class__.__name__}("
            f"name={self.config.name}, "
            f"version={self.config.version}, "
            f"status={self.status.value}, "
            f"healthy={self.is_healthy})"
        )