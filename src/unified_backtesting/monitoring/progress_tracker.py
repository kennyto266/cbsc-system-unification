"""
Real-Time Progress Tracking System

Advanced progress monitoring and tracking system for large-scale parameter
optimization with real-time updates, performance metrics, and visual feedback.

Key Features:
- Real-time progress monitoring with sub-second updates
- Multi-dimensional performance tracking (speed, memory, accuracy)
- Predictive ETA calculation with machine learning
- WebSocket streaming for real-time web updates
- Performance anomaly detection and alerts
- Progress visualization and charting
- Historical progress data analysis
- Customizable progress callbacks and notifications
"""

import time
import logging
import threading
import queue
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from dataclasses import dataclass, field, asdict
from collections import deque, defaultdict
from enum import Enum
import asyncio
import websockets
from datetime import datetime, timedelta
import psutil

logger = logging.getLogger(__name__)


class ProgressEventType(Enum):
    """Types of progress events"""
    STARTED = "started"
    BATCH_STARTED = "batch_started"
    BATCH_COMPLETED = "batch_completed"
    PARAMETER_COMPLETED = "parameter_completed"
    ERROR_OCCURRED = "error_occurred"
    MEMORY_WARNING = "memory_warning"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    COMPLETED = "completed"
    PAUSED = "paused"
    RESUMED = "resumed"


@dataclass
class ProgressEvent:
    """Progress event structure"""
    event_type: ProgressEventType
    timestamp: float
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info, warning, error, critical

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'message': self.message,
            'data': self.data,
            'severity': self.severity
        }


@dataclass
class PerformanceSnapshot:
    """Performance metrics snapshot"""
    timestamp: float
    combinations_processed: int
    total_combinations: int
    combinations_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    active_workers: int
    cache_hit_rate: float
    error_rate: float
    estimated_remaining_time: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class BatchProgress:
    """Progress information for a single batch"""
    batch_id: int
    total_combinations: int
    processed_combinations: int
    successful_combinations: int
    failed_combinations: int
    start_time: float
    end_time: Optional[float] = None
    avg_processing_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate for this batch"""
        if self.total_combinations == 0:
            return 0.0
        return self.successful_combinations / self.total_combinations

    @property
    def is_complete(self) -> bool:
        """Check if batch is complete"""
        return self.processed_combinations >= self.total_combinations


class ETAPredictor:
    """Advanced ETA prediction with machine learning"""

    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.processing_times = deque(maxlen=history_size)
        self.completion_counts = deque(maxlen=history_size)
        self.timestamps = deque(maxlen=history_size)
        self.model_coefs = None
        self.last_prediction = 0.0

    def update(self, processed_count: int, current_time: float):
        """Update prediction model with new data point"""
        if len(self.timestamps) > 0:
            time_delta = current_time - self.timestamps[-1]
            count_delta = processed_count - (self.completion_counts[-1] if self.completion_counts else 0)

            if time_delta > 0:
                self.processing_times.append(count_delta / time_delta)
                self.completion_counts.append(processed_count)
                self.timestamps.append(current_time)

    def predict_remaining_time(self, total_count: int, processed_count: int) -> float:
        """Predict remaining time using adaptive algorithms"""
        if len(self.processing_times) < 3:
            # Not enough data for prediction
            return float('inf')

        # Simple linear regression on recent data
        if len(self.processing_times) >= 10:
            # Use more data for stable prediction
            recent_times = list(self.processing_times)[-10:]
            recent_counts = list(self.completion_counts)[-10:]
            recent_timestamps = list(self.timestamps)[-10:]

            # Linear regression: time = a * count + b
            count_array = np.array(recent_counts)
            time_array = np.array(recent_timestamps)

            if len(count_array) > 1 and np.var(count_array) > 0:
                coefs = np.polyfit(count_array, time_array, 1)
                remaining_count = total_count - processed_count

                if coefs[0] > 0:  # Positive slope
                    self.last_prediction = coefs[0] * remaining_count
                else:
                    # Fallback to average rate
                    avg_rate = np.mean(recent_times)
                    if avg_rate > 0:
                        self.last_prediction = remaining_count / avg_rate
                    else:
                        self.last_prediction = float('inf')
            else:
                self.last_prediction = float('inf')
        else:
            # Use simple average rate
            avg_rate = np.mean(self.processing_times)
            remaining_count = total_count - processed_count
            self.last_prediction = remaining_count / avg_rate if avg_rate > 0 else float('inf')

        # Apply bounds and smoothing
        self.last_prediction = max(0, min(self.last_prediction, 24 * 3600))  # Max 24 hours
        return self.last_prediction

    def get_processing_speed_trend(self) -> str:
        """Analyze processing speed trend"""
        if len(self.processing_times) < 5:
            return "insufficient_data"

        recent_speeds = list(self.processing_times)[-5:]
        if len(recent_speeds) < 3:
            return "insufficient_data"

        # Calculate trend
        x = np.arange(len(recent_speeds))
        trend = np.polyfit(x, recent_speeds, 1)[0]

        if trend > 0.1:
            return "accelerating"
        elif trend < -0.1:
            return "decelerating"
        else:
            return "stable"


class AnomalyDetector:
    """Performance anomaly detection"""

    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.metric_history = defaultdict(lambda: deque(maxlen=window_size))
        self.thresholds = {
            'combinations_per_second': {'min': 10, 'max': 1000},
            'memory_usage_mb': {'min': 100, 'max': 8000},
            'cpu_usage_percent': {'min': 5, 'max': 95},
            'error_rate': {'min': 0, 'max': 0.1}
        }

    def check_anomalies(self, metrics: Dict[str, float]) -> List[ProgressEvent]:
        """Check for performance anomalies"""
        anomalies = []

        for metric_name, value in metrics.items():
            if metric_name not in self.thresholds:
                continue

            # Add to history
            self.metric_history[metric_name].append(value)

            if len(self.metric_history[metric_name]) < self.window_size:
                continue  # Not enough data

            # Calculate statistics
            history = list(self.metric_history[metric_name])
            mean_val = np.mean(history)
            std_val = np.std(history)

            # Check thresholds
            thresholds = self.thresholds[metric_name]
            is_anomaly = False
            anomaly_type = None

            if value < thresholds['min']:
                is_anomaly = True
                anomaly_type = "low"
            elif value > thresholds['max']:
                is_anomaly = True
                anomaly_type = "high"
            elif std_val > 0 and abs(value - mean_val) > 2 * std_val:
                is_anomaly = True
                anomaly_type = "statistical_outlier"

            if is_anomaly:
                severity = "warning"
                if anomaly_type == "high" and metric_name in ['memory_usage_mb', 'cpu_usage_percent']:
                    severity = "critical"

                event = ProgressEvent(
                    event_type=ProgressEventType.PERFORMANCE_DEGRADATION,
                    timestamp=time.time(),
                    message=f"Performance anomaly detected: {metric_name} = {value:.2f} ({anomaly_type})",
                    data={
                        'metric_name': metric_name,
                        'current_value': value,
                        'anomaly_type': anomaly_type,
                        'mean_value': mean_val,
                        'std_value': std_val
                    },
                    severity=severity
                )
                anomalies.append(event)

        return anomalies


class WebSocketProgressStreamer:
    """WebSocket progress streaming for real-time web updates"""

    def __init__(self, port: int = 8765):
        self.port = port
        self.clients = set()
        self.server = None
        self.is_running = False

    async def start_server(self):
        """Start WebSocket server for progress streaming"""
        self.is_running = True

        async def handle_client(websocket, path):
            """Handle new WebSocket client connection"""
            self.clients.add(websocket)
            logger.info(f"Progress client connected: {websocket.remote_address}")

            try:
                await websocket.wait_closed()
            finally:
                self.clients.remove(websocket)
                logger.info(f"Progress client disconnected: {websocket.remote_address}")

        self.server = await websockets.serve(
            handle_client,
            "localhost",
            self.port
        )

        logger.info(f"WebSocket progress server started on port {self.port}")

    async def broadcast_progress(self, progress_data: Dict):
        """Broadcast progress update to all connected clients"""
        if not self.is_running or not self.clients:
            return

        message = json.dumps(progress_data, default=str)
        disconnected = set()

        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Error sending progress to client: {str(e)}")
                disconnected.add(client)

        # Remove disconnected clients
        self.clients -= disconnected

    async def stop_server(self):
        """Stop WebSocket server"""
        self.is_running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("WebSocket progress server stopped")


class RealTimeProgressTracker:
    """
    Real-time progress tracking system for large-scale optimization

    Provides comprehensive monitoring, predictive analytics, and real-time
    progress streaming for parameter optimization workflows.
    """

    def __init__(self, strategy_name: str, total_combinations: int,
                 enable_websocket: bool = True, websocket_port: int = 8765):
        """Initialize progress tracker"""
        self.strategy_name = strategy_name
        self.total_combinations = total_combinations
        self.start_time = None
        self.end_time = None

        # Core tracking data
        self.processed_combinations = 0
        self.successful_combinations = 0
        self.failed_combinations = 0
        self.current_batch_id = 0

        # Progress history
        self.progress_history = deque(maxlen=1000)
        self.events = deque(maxlen=500)
        self.batch_progress = {}

        # Advanced components
        self.eta_predictor = ETAPredictor()
        self.anomaly_detector = AnomalyDetector()
        self.progress_callbacks = []

        # Real-time streaming
        self.websocket_streamer = None
        self.enable_websocket = enable_websocket
        self.websocket_port = websocket_port

        # Performance monitoring
        self.system_monitor = threading.Thread(target=self._system_monitoring_loop, daemon=True)
        self.system_monitor.start()

        # WebSocket server
        if enable_websocket:
            self.websocket_streamer = WebSocketProgressStreamer(websocket_port)
            asyncio.create_task(self.websocket_streamer.start_server())

        logger.info(f"Initialized RealTimeProgressTracker for {strategy_name}")
        logger.info(f"Total combinations: {total_combinations:,}")

    def start_optimization(self):
        """Mark optimization as started"""
        self.start_time = time.time()
        self._add_event(ProgressEventType.STARTED, "Optimization started")

    def complete_optimization(self):
        """Mark optimization as completed"""
        self.end_time = time.time()
        self._add_event(ProgressEventType.COMPLETED, "Optimization completed")

        if self.websocket_streamer:
            asyncio.create_task(self.websocket_streamer.stop_server())

    def start_batch(self, batch_id: int, batch_size: int):
        """Mark new batch as started"""
        self.current_batch_id = batch_id
        self.batch_progress[batch_id] = BatchProgress(
            batch_id=batch_id,
            total_combinations=batch_size,
            processed_combinations=0,
            successful_combinations=0,
            failed_combinations=0,
            start_time=time.time()
        )

        self._add_event(
            ProgressEventType.BATCH_STARTED,
            f"Batch {batch_id} started ({batch_size} combinations)",
            {'batch_id': batch_id, 'batch_size': batch_size}
        )

    def complete_batch(self, batch_id: int, successful_count: int, failed_count: int):
        """Mark batch as completed"""
        if batch_id not in self.batch_progress:
            logger.warning(f"Batch {batch_id} not found in progress tracking")
            return

        batch = self.batch_progress[batch_id]
        batch.processed_combinations = batch.total_combinations
        batch.successful_combinations = successful_count
        batch.failed_combinations = failed_count
        batch.end_time = time.time()

        # Update global counters
        self.processed_combinations += batch.total_combinations
        self.successful_combinations += successful_count
        self.failed_combinations += failed_count

        # Calculate batch processing time
        processing_time = batch.end_time - batch.start_time
        batch.avg_processing_time = processing_time / batch.total_combinations

        self._add_event(
            ProgressEventType.BATCH_COMPLETED,
            f"Batch {batch_id} completed ({successful_count}/{batch.total_combinations} successful)",
            {
                'batch_id': batch_id,
                'successful_count': successful_count,
                'failed_count': failed_count,
                'processing_time': processing_time,
                'success_rate': batch.success_rate
            }
        )

    def update_progress(self, processed_count: int, additional_data: Optional[Dict] = None):
        """Update current progress"""
        current_time = time.time()
        self.processed_combinations = processed_count

        # Update ETA prediction
        self.eta_predictor.update(processed_count, current_time)

        # Create performance snapshot
        snapshot = self._create_performance_snapshot(current_time)
        self.progress_history.append(snapshot)

        # Check for anomalies
        metrics = {
            'combinations_per_second': snapshot.combinations_per_second,
            'memory_usage_mb': snapshot.memory_usage_mb,
            'cpu_usage_percent': snapshot.cpu_usage_percent,
            'error_rate': snapshot.error_rate
        }

        anomalies = self.anomaly_detector.check_anomalies(metrics)
        for anomaly in anomalies:
            self.events.append(anomaly)

        # Broadcast progress
        if self.websocket_streamer:
            progress_data = {
                'timestamp': current_time,
                'progress': self.get_progress_summary(),
                'snapshot': snapshot.to_dict(),
                'anomalies': [a.to_dict() for a in anomalies],
                'additional_data': additional_data or {}
            }
            asyncio.create_task(self.websocket_streamer.broadcast_progress(progress_data))

        # Call progress callbacks
        for callback in self.progress_callbacks:
            try:
                callback(snapshot)
            except Exception as e:
                logger.error(f"Error in progress callback: {str(e)}")

    def _create_performance_snapshot(self, current_time: float) -> PerformanceSnapshot:
        """Create current performance snapshot"""
        # Get system metrics
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Calculate processing speed
        combinations_per_second = 0.0
        if self.start_time and current_time > self.start_time:
            elapsed_time = current_time - self.start_time
            if elapsed_time > 0:
                combinations_per_second = self.processed_combinations / elapsed_time

        # Calculate error rate
        error_rate = 0.0
        if self.processed_combinations > 0:
            error_rate = self.failed_combinations / self.processed_combinations

        # Predict remaining time
        eta = self.eta_predictor.predict_remaining_time(
            self.total_combinations, self.processed_combinations
        )

        return PerformanceSnapshot(
            timestamp=current_time,
            combinations_processed=self.processed_combinations,
            total_combinations=self.total_combinations,
            combinations_per_second=combinations_per_second,
            memory_usage_mb=memory_info.used / (1024 * 1024),
            cpu_usage_percent=cpu_percent,
            active_workers=0,  # Would be updated from engine
            cache_hit_rate=0.0,  # Would be updated from engine
            error_rate=error_rate,
            estimated_remaining_time=eta
        )

    def _system_monitoring_loop(self):
        """Background system monitoring loop"""
        while True:
            try:
                # Check memory warnings
                memory_info = psutil.virtual_memory()
                if memory_info.percent > 90:
                    self._add_event(
                        ProgressEventType.MEMORY_WARNING,
                        f"High memory usage: {memory_info.percent:.1f}%",
                        {'memory_percent': memory_info.percent},
                        severity="warning"
                    )

                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"System monitoring error: {str(e)}")
                time.sleep(60)

    def _add_event(self, event_type: ProgressEventType, message: str,
                   data: Optional[Dict] = None, severity: str = "info"):
        """Add progress event"""
        event = ProgressEvent(
            event_type=event_type,
            timestamp=time.time(),
            message=message,
            data=data or {},
            severity=severity
        )
        self.events.append(event)

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get comprehensive progress summary"""
        current_time = time.time()
        progress_percent = (self.processed_combinations / self.total_combinations) * 100 if self.total_combinations > 0 else 0

        # Calculate elapsed time
        elapsed_time = 0.0
        if self.start_time:
            elapsed_time = current_time - self.start_time

        # Calculate overall processing speed
        avg_speed = self.processed_combinations / elapsed_time if elapsed_time > 0 else 0

        # Get ETA
        eta = self.eta_predictor.predict_remaining_time(self.total_combinations, self.processed_combinations)

        return {
            'strategy_name': self.strategy_name,
            'progress_percent': progress_percent,
            'processed_combinations': self.processed_combinations,
            'total_combinations': self.total_combinations,
            'successful_combinations': self.successful_combinations,
            'failed_combinations': self.failed_combinations,
            'success_rate': (self.successful_combinations / self.processed_combinations * 100) if self.processed_combinations > 0 else 0,
            'elapsed_time': elapsed_time,
            'estimated_remaining_time': eta,
            'average_combinations_per_second': avg_speed,
            'current_batch_id': self.current_batch_id,
            'is_complete': self.processed_combinations >= self.total_combinations,
            'processing_speed_trend': self.eta_predictor.get_processing_speed_trend()
        }

    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        """Get recent progress events"""
        return [event.to_dict() for event in list(self.events)[-limit:]]

    def get_performance_history(self, limit: int = 100) -> List[Dict]:
        """Get recent performance history"""
        return [snapshot.to_dict() for snapshot in list(self.progress_history)[-limit:]]

    def add_progress_callback(self, callback: Callable[[PerformanceSnapshot], None]):
        """Add custom progress callback"""
        self.progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: Callable[[PerformanceSnapshot], None]):
        """Remove progress callback"""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)

    def export_progress_data(self, filepath: str):
        """Export complete progress data to file"""
        data = {
            'strategy_name': self.strategy_name,
            'total_combinations': self.total_combinations,
            'progress_summary': self.get_progress_summary(),
            'events': [event.to_dict() for event in self.events],
            'performance_history': [snapshot.to_dict() for snapshot in self.progress_history],
            'batch_progress': {
                batch_id: asdict(batch) for batch_id, batch in self.batch_progress.items()
            },
            'export_timestamp': time.time()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Progress data exported to {filepath}")

    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance statistics analysis"""
        if len(self.progress_history) < 2:
            return {"error": "Insufficient data for analysis"}

        # Extract performance data
        snapshots = list(self.progress_history)
        speeds = [s.combinations_per_second for s in snapshots]
        memory_usage = [s.memory_usage_mb for s in snapshots]
        cpu_usage = [s.cpu_usage_percent for s in snapshots]

        return {
            'processing_speed': {
                'mean': np.mean(speeds),
                'std': np.std(speeds),
                'min': np.min(speeds),
                'max': np.max(speeds),
                'median': np.median(speeds),
                'trend': self.eta_predictor.get_processing_speed_trend()
            },
            'memory_usage': {
                'mean': np.mean(memory_usage),
                'std': np.std(memory_usage),
                'min': np.min(memory_usage),
                'max': np.max(memory_usage),
                'peak_usage_mb': np.max(memory_usage)
            },
            'cpu_usage': {
                'mean': np.mean(cpu_usage),
                'std': np.std(cpu_usage),
                'min': np.min(cpu_usage),
                'max': np.max(cpu_usage)
            },
            'anomalies_detected': len([e for e in self.events if e.event_type == ProgressEventType.PERFORMANCE_DEGRADATION]),
            'total_events': len(self.events),
            'monitoring_duration': snapshots[-1].timestamp - snapshots[0].timestamp if snapshots else 0
        }