"""
Backtest parallel processing components for CBSC strategy optimization.

This module provides high-performance parallel processing capabilities for backtesting,
enabling massive parameter optimization runs with efficient resource utilization.
"""

from .models import (
    Task, TaskResult, ProcessInfo, ExecutionStats,
    TaskType, TaskComplexity
)

from .process_pool import DynamicProcessPool
from .task_distributor import TaskDistributor
from .ipc_manager import IPCManager
from .fault_handler import FaultHandler
from .parallel_engine import ParallelEngine

from .streaming_loader import (
    StreamingDataLoader, LoaderConfig,
    ChunkStrategy, MemoryPressureLevel
)

from .chunker import DataChunker, ChunkConfig, ChunkStrategy
from .memory_mapper import (
    MemoryMappedFile, CSVMemoryMapper,
    NumPyMemoryMapper, AccessPattern
)

from .shared_memory import (
    SharedMemoryManager, MemoryOptimizer,
    SharedMemoryConfig, MemoryOptimizerConfig
)

from .monitor import (
    BacktestMonitor, ResourceMonitor, ProgressTracker,
    AlertManager, AlertLevel, ResourceMetrics, TaskProgress, Alert,
    get_monitor, start_monitoring, stop_monitoring
)

from .websocket_server import (
    WebSocketManager, MonitoringEventHandler,
    get_websocket_manager, start_websocket_server, stop_websocket_server,
    run_websocket_server_in_thread, stop_websocket_server_in_thread
)

from .performance_metrics import (
    PerformanceMetricsCollector, TaskTimer, ThroughputMetrics,
    LatencyMetrics, EfficiencyMetrics, PerformanceSnapshot,
    get_metrics_collector, start_metrics_collection, stop_metrics_collection,
    time_task
)

# Version information
__version__ = "1.1.0"

# Feature detection
HAS_SHARED_MEMORY = True
HAS_STREAMING = True
HAS_MEMORY_OPTIMIZATION = True
HAS_MONITORING = True
HAS_WEBSOCKET = True
HAS_PERFORMANCE_METRICS = True

# Export main classes
__all__ = [
    # Core components
    "ParallelEngine",
    "DynamicProcessPool",
    "TaskDistributor",
    "IPCManager",
    "FaultHandler",

    # Models
    "Task",
    "TaskResult",
    "ProcessInfo",
    "ExecutionStats",
    "TaskType",
    "TaskComplexity",

    # Streaming components
    "StreamingDataLoader",
    "LoaderConfig",
    "ChunkStrategy",
    "MemoryPressureLevel",

    # Memory components
    "DataChunker",
    "ChunkConfig",
    "MemoryMappedFile",
    "CSVMemoryMapper",
    "NumPyMemoryMapper",
    "AccessPattern",
    "SharedMemoryManager",
    "MemoryOptimizer",
    "SharedMemoryConfig",
    "MemoryOptimizerConfig",

    # Monitoring components
    "BacktestMonitor",
    "ResourceMonitor",
    "ProgressTracker",
    "AlertManager",
    "AlertLevel",
    "ResourceMetrics",
    "TaskProgress",
    "Alert",

    # WebSocket components
    "WebSocketManager",
    "MonitoringEventHandler",

    # Performance metrics
    "PerformanceMetricsCollector",
    "TaskTimer",
    "ThroughputMetrics",
    "LatencyMetrics",
    "EfficiencyMetrics",
    "PerformanceSnapshot",
]

# Configuration helper
def get_parallel_engine_config() -> dict:
    """Get recommended configuration for parallel engine."""
    import psutil
    cpu_count = min(psutil.cpu_count(), 32)  # Cap at 32 as per requirements

    return {
        "min_processes": max(1, cpu_count // 4),
        "max_processes": cpu_count,
        "auto_scaling": True,
        "memory_limit_mb": 4096,  # 4GB limit
        "recycle_interval": 100,
        "fault_recovery": True
    }


def get_monitoring_config() -> dict:
    """Get recommended configuration for monitoring system."""
    return {
        "resource_sampling_interval": 1.0,
        "resource_history_size": 3600,
        "websocket_host": "localhost",
        "websocket_port": 8765,
        "thresholds": {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_io_warning": 100.0,  # MB/s
            "disk_io_critical": 500.0
        }
    }


def get_performance_metrics_config() -> dict:
    """Get recommended configuration for performance metrics."""
    return {
        "history_size": 10000,
        "sampling_interval": 1.0,
        "auto_start_collection": True
    }