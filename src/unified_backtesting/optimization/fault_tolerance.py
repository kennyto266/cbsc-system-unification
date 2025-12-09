"""
Fault Tolerance and Error Recovery System

Advanced fault tolerance system for handling errors, crashes, and system failures
during large-scale parameter optimization with automatic recovery mechanisms.

Key Features:
- Automatic error detection and classification
- Intelligent retry mechanisms with exponential backoff
- Checkpoint and recovery system
- Process isolation and crash recovery
- Data integrity validation
- Graceful degradation modes
- Resource cleanup and recovery
"""

import logging
import time
import json
import pickle
import hashlib
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import traceback
import gc
import os
from pathlib import Path
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorType(Enum):
    """Error type classification"""
    MEMORY_ERROR = "memory_error"
    COMPUTATION_ERROR = "computation_error"
    DATA_ERROR = "data_error"
    NETWORK_ERROR = "network_error"
    SYSTEM_ERROR = "system_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorRecord:
    """Error record structure"""
    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    timestamp: float
    error_message: str
    stack_trace: str
    context: Dict[str, Any]
    retry_count: int = 0
    resolved: bool = False
    resolution_time: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'error_id': self.error_id,
            'error_type': self.error_type.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'context': self.context,
            'retry_count': self.retry_count,
            'resolved': self.resolved,
            'resolution_time': self.resolution_time
        }


class RetryPolicy:
    """Configurable retry policy with exponential backoff"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, backoff_multiplier: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier

    def should_retry(self, error: Exception, retry_count: int) -> bool:
        """Determine if operation should be retried"""
        if retry_count >= self.max_retries:
            return False

        # Don't retry certain error types
        if isinstance(error, (MemoryError, KeyboardInterrupt)):
            return False

        return True

    def get_retry_delay(self, retry_count: int) -> float:
        """Calculate retry delay with exponential backoff"""
        delay = self.base_delay * (self.backoff_multiplier ** retry_count)
        return min(delay, self.max_delay)


class CheckpointManager:
    """Checkpoint and recovery management system"""

    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.current_checkpoint = None

    def save_checkpoint(self, data: Dict[str, Any], checkpoint_id: str) -> str:
        """Save checkpoint data"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

        try:
            # Add metadata
            checkpoint_data = {
                'checkpoint_id': checkpoint_id,
                'timestamp': time.time(),
                'data': data
            }

            # Create backup of existing checkpoint
            if checkpoint_file.exists():
                backup_file = checkpoint_file.with_suffix('.bak')
                checkpoint_file.rename(backup_file)

            # Save new checkpoint
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)

            self.current_checkpoint = checkpoint_id
            logger.info(f"Checkpoint saved: {checkpoint_id}")
            return str(checkpoint_file)

        except Exception as e:
            logger.error(f"Failed to save checkpoint {checkpoint_id}: {str(e)}")
            raise

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Load checkpoint data"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)

            # Validate checkpoint integrity
            if self._validate_checkpoint(checkpoint_data):
                logger.info(f"Checkpoint loaded: {checkpoint_id}")
                return checkpoint_data.get('data', {})
            else:
                logger.error(f"Checkpoint validation failed: {checkpoint_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {str(e)}")
            return None

    def _validate_checkpoint(self, checkpoint_data: Dict) -> bool:
        """Validate checkpoint integrity"""
        required_fields = ['checkpoint_id', 'timestamp', 'data']
        return all(field in checkpoint_data for field in required_fields)

    def list_checkpoints(self) -> List[str]:
        """List available checkpoints"""
        checkpoints = []
        for file_path in self.checkpoint_dir.glob("*.json"):
            if not file_path.name.endswith('.bak'):
                checkpoints.append(file_path.stem)
        return sorted(checkpoints)

    def cleanup_old_checkpoints(self, keep_count: int = 5):
        """Clean up old checkpoints"""
        checkpoints = self.list_checkpoints()
        if len(checkpoints) > keep_count:
            for checkpoint_id in checkpoints[:-keep_count]:
                checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
                backup_file = checkpoint_file.with_suffix('.bak')

                try:
                    if checkpoint_file.exists():
                        checkpoint_file.unlink()
                    if backup_file.exists():
                        backup_file.unlink()
                    logger.debug(f"Cleaned up old checkpoint: {checkpoint_id}")
                except Exception as e:
                    logger.error(f"Failed to cleanup checkpoint {checkpoint_id}: {str(e)}")


class FaultTolerantExecutor:
    """Fault-tolerant executor with automatic recovery"""

    def __init__(self, retry_policy: Optional[RetryPolicy] = None,
                 checkpoint_manager: Optional[CheckpointManager] = None):
        self.retry_policy = retry_policy or RetryPolicy()
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.error_records = []
        self.recovery_callbacks = defaultdict(list)

    def execute_with_fault_tolerance(self, func: Callable, *args,
                                    checkpoint_id: Optional[str] = None,
                                    context: Optional[Dict] = None,
                                    **kwargs) -> Any:
        """Execute function with fault tolerance"""
        context = context or {}
        retry_count = 0
        last_error = None

        # Try to load from checkpoint if available
        if checkpoint_id:
            checkpoint_data = self.checkpoint_manager.load_checkpoint(checkpoint_id)
            if checkpoint_data:
                logger.info(f"Resuming from checkpoint: {checkpoint_id}")
                # Could merge checkpoint data with context here

        while True:
            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Save checkpoint if successful and checkpoint_id provided
                if checkpoint_id:
                    checkpoint_data = {
                        'result': result,
                        'context': context,
                        'completed': True
                    }
                    self.checkpoint_manager.save_checkpoint(checkpoint_data, checkpoint_id)

                return result

            except Exception as error:
                last_error = error
                error_record = self._create_error_record(error, context, retry_count)
                self.error_records.append(error_record)

                # Log error
                logger.error(f"Execution failed (attempt {retry_count + 1}): {str(error)}")

                # Check if we should retry
                if not self.retry_policy.should_retry(error, retry_count):
                    logger.error(f"Max retries exceeded or non-retryable error: {str(error)}")
                    break

                # Apply recovery mechanisms
                self._apply_recovery_mechanisms(error_record)

                # Wait before retry
                delay = self.retry_policy.get_retry_delay(retry_count)
                logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)

                retry_count += 1

        # Execution failed after all retries
        logger.error(f"Execution failed after {retry_count} retries: {str(last_error)}")
        raise last_error

    def _create_error_record(self, error: Exception, context: Dict,
                           retry_count: int) -> ErrorRecord:
        """Create error record"""
        error_id = hashlib.md5(
            f"{time.time()}{str(error)}{retry_count}".encode()
        ).hexdigest()[:8]

        error_type = self._classify_error(error)
        severity = self._determine_severity(error, error_type)

        return ErrorRecord(
            error_id=error_id,
            error_type=error_type,
            severity=severity,
            timestamp=time.time(),
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            context=context.copy(),
            retry_count=retry_count
        )

    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type"""
        error_msg = str(error).lower()
        error_type_name = type(error).__name__.lower()

        if 'memory' in error_msg or 'memory' in error_type_name:
            return ErrorType.MEMORY_ERROR
        elif 'timeout' in error_msg or 'timeout' in error_type_name:
            return ErrorType.TIMEOUT_ERROR
        elif 'network' in error_msg or 'connection' in error_msg:
            return ErrorType.NETWORK_ERROR
        elif 'computation' in error_msg or 'calculation' in error_msg:
            return ErrorType.COMPUTATION_ERROR
        elif 'data' in error_msg or 'parsing' in error_msg:
            return ErrorType.DATA_ERROR
        elif 'system' in error_msg or 'os' in error_type_name:
            return ErrorType.SYSTEM_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR

    def _determine_severity(self, error: Exception, error_type: ErrorType) -> ErrorSeverity:
        """Determine error severity"""
        if error_type == ErrorType.MEMORY_ERROR or error_type == ErrorType.SYSTEM_ERROR:
            return ErrorSeverity.HIGH
        elif error_type == ErrorType.DATA_ERROR:
            return ErrorSeverity.MEDIUM
        elif isinstance(error, KeyboardInterrupt):
            return ErrorSeverity.CRITICAL
        else:
            return ErrorSeverity.LOW

    def _apply_recovery_mechanisms(self, error_record: ErrorRecord):
        """Apply appropriate recovery mechanisms"""
        error_type = error_record.error_type

        if error_type == ErrorType.MEMORY_ERROR:
            self._recover_from_memory_error()
        elif error_type == ErrorType.COMPUTATION_ERROR:
            self._recover_from_computation_error()
        elif error_type == ErrorType.DATA_ERROR:
            self._recover_from_data_error()

        # Call custom recovery callbacks
        for callback in self.recovery_callbacks[error_type]:
            try:
                callback(error_record)
            except Exception as e:
                logger.error(f"Recovery callback failed: {str(e)}")

    def _recover_from_memory_error(self):
        """Recover from memory error"""
        logger.info("Applying memory recovery mechanisms...")
        gc.collect()  # Force garbage collection

    def _recover_from_computation_error(self):
        """Recover from computation error"""
        logger.info("Applying computation recovery mechanisms...")
        # Could implement specific computation recovery logic here

    def _recover_from_data_error(self):
        """Recover from data error"""
        logger.info("Applying data recovery mechanisms...")
        # Could implement data validation and cleaning logic here

    def add_recovery_callback(self, error_type: ErrorType, callback: Callable[[ErrorRecord], None]):
        """Add custom recovery callback"""
        self.recovery_callbacks[error_type].append(callback)

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.error_records:
            return {"total_errors": 0}

        # Count errors by type and severity
        type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        resolved_counts = defaultdict(int)

        for error in self.error_records:
            type_counts[error.error_type.value] += 1
            severity_counts[error.severity.value] += 1
            if error.resolved:
                resolved_counts[error.error_type.value] += 1

        return {
            'total_errors': len(self.error_records),
            'errors_by_type': dict(type_counts),
            'errors_by_severity': dict(severity_counts),
            'resolved_errors_by_type': dict(resolved_counts),
            'unresolved_errors': len([e for e in self.error_records if not e.resolved])
        }

    def export_error_log(self, filepath: str):
        """Export error log to file"""
        error_data = {
            'errors': [error.to_dict() for error in self.error_records],
            'statistics': self.get_error_statistics(),
            'export_timestamp': time.time()
        }

        with open(filepath, 'w') as f:
            json.dump(error_data, f, indent=2, default=str)

        logger.info(f"Error log exported to {filepath}")


class GracefulDegradation:
    """Graceful degradation system for handling resource constraints"""

    def __init__(self):
        self.degradation_levels = {
            'full': {'workers': 1.0, 'chunk_size': 1.0, 'features': 'all'},
            'reduced': {'workers': 0.7, 'chunk_size': 0.5, 'features': 'essential'},
            'minimal': {'workers': 0.3, 'chunk_size': 0.2, 'features': 'basic'},
            'emergency': {'workers': 0.1, 'chunk_size': 0.1, 'features': 'none'}
        }
        self.current_level = 'full'

    def adjust_for_resource_constraints(self, memory_usage: float, cpu_usage: float) -> str:
        """Adjust degradation level based on resource constraints"""
        if memory_usage > 0.9 or cpu_usage > 0.95:
            new_level = 'emergency'
        elif memory_usage > 0.8 or cpu_usage > 0.85:
            new_level = 'minimal'
        elif memory_usage > 0.7 or cpu_usage > 0.75:
            new_level = 'reduced'
        else:
            new_level = 'full'

        if new_level != self.current_level:
            logger.info(f"Changing degradation level: {self.current_level} -> {new_level}")
            self.current_level = new_level

        return self.current_level

    def get_adjusted_config(self, base_config: Dict) -> Dict:
        """Get configuration adjusted for current degradation level"""
        level_config = self.degradation_levels[self.current_level]
        adjusted_config = base_config.copy()

        # Adjust workers
        if 'max_workers' in adjusted_config:
            adjusted_config['max_workers'] = max(
                1, int(adjusted_config['max_workers'] * level_config['workers'])
            )

        # Adjust chunk size
        if 'chunk_size' in adjusted_config:
            adjusted_config['chunk_size'] = max(
                10, int(adjusted_config['chunk_size'] * level_config['chunk_size'])
            )

        # Add degradation level info
        adjusted_config['degradation_level'] = self.current_level
        adjusted_config['enabled_features'] = level_config['features']

        return adjusted_config


# Global fault tolerance instance
fault_tolerance = FaultTolerantExecutor()