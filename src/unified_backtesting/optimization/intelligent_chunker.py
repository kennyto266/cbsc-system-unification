"""
Intelligent Parameter Chunking System

Advanced chunking algorithms that dynamically optimize batch sizes based on
memory usage, performance metrics, and system characteristics. This system
ensures optimal resource utilization and prevents memory overload during
large-scale parameter optimization.

Key Features:
- Adaptive chunk size calculation based on real-time metrics
- Memory-aware chunking with pressure detection
- Performance-based chunk size optimization
- Strategy-specific chunking profiles
- Predictive chunking using machine learning
- Multi-objective optimization (memory vs performance)
- Real-time chunk size adaptation
"""

import time
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union, Iterator
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import threading
from abc import ABC, abstractmethod
import psutil
import gc

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    ADAPTIVE = "adaptive"
    MEMORY_AWARE = "memory_aware"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    PREDICTIVE = "predictive"
    HYBRID = "hybrid"


@dataclass
class ChunkMetrics:
    """Metrics for chunk performance analysis"""
    chunk_id: int
    chunk_size: int
    processing_time: float
    memory_usage_mb: float
    success_rate: float
    combinations_per_second: float
    memory_efficiency: float
    timestamp: float

    def performance_score(self) -> float:
        """Calculate overall performance score"""
        # Weighted combination of speed and efficiency
        speed_score = min(self.combinations_per_second / 100, 1.0)  # Normalize to 100 cps
        efficiency_score = 1.0 - min(self.memory_efficiency, 1.0)  # Lower memory usage is better
        return 0.6 * speed_score + 0.4 * efficiency_score


@dataclass
class ChunkProfile:
    """Profile for strategy-specific chunking behavior"""
    strategy_name: str
    optimal_chunk_size: int
    min_chunk_size: int
    max_chunk_size: int
    memory_multiplier: float
    performance_multiplier: float
    chunk_size_variance: float
    stability_score: float

    def __post_init__(self):
        """Validate chunk profile"""
        if self.min_chunk_size > self.max_chunk_size:
            raise ValueError("min_chunk_size cannot be greater than max_chunk_size")
        if not (self.min_chunk_size <= self.optimal_chunk_size <= self.max_chunk_size):
            raise ValueError("optimal_chunk_size must be between min and max")


class ChunkingStrategyBase(ABC):
    """Base class for chunking strategies"""

    def __init__(self, name: str):
        self.name = name
        self.metrics_history = deque(maxlen=100)

    @abstractmethod
    def calculate_chunk_size(self, context: Dict[str, Any]) -> int:
        """Calculate optimal chunk size based on context"""
        pass

    def record_chunk_metrics(self, metrics: ChunkMetrics):
        """Record metrics for learning and optimization"""
        self.metrics_history.append(metrics)

    def get_performance_trend(self) -> str:
        """Analyze performance trend from metrics history"""
        if len(self.metrics_history) < 5:
            return "insufficient_data"

        recent_scores = [m.performance_score() for m in list(self.metrics_history)[-5:]]
        trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]

        if trend > 0.01:
            return "improving"
        elif trend < -0.01:
            return "degrading"
        else:
            return "stable"


class AdaptiveChunkingStrategy(ChunkingStrategyBase):
    """Adaptive chunking that responds to system conditions"""

    def __init__(self, base_chunk_size: int = 1000):
        super().__init__("adaptive")
        self.base_chunk_size = base_chunk_size
        self.adjustment_factor = 1.0
        self.last_adjustment_time = 0
        self.adjustment_cooldown = 30  # seconds

    def calculate_chunk_size(self, context: Dict[str, Any]) -> int:
        """Calculate chunk size with adaptive adjustments"""
        current_time = time.time()

        # Check if enough time has passed since last adjustment
        if current_time - self.last_adjustment_time < self.adjustment_cooldown:
            return int(self.base_chunk_size * self.adjustment_factor)

        # Get current metrics
        memory_usage = context.get('memory_usage_percent', 0)
        cpu_usage = context.get('cpu_usage_percent', 0)
        processing_speed = context.get('combinations_per_second', 0)

        # Calculate adjustment factors
        memory_factor = max(0.5, 1.0 - memory_usage / 100)  # Reduce if memory pressure
        cpu_factor = max(0.5, 1.0 - cpu_usage / 100)  # Reduce if CPU pressure
        speed_factor = min(2.0, processing_speed / 50)  # Increase if fast processing

        # Combine factors
        combined_factor = (memory_factor * 0.4 + cpu_factor * 0.3 + speed_factor * 0.3)

        # Apply smoothing to avoid oscillations
        self.adjustment_factor = 0.7 * self.adjustment_factor + 0.3 * combined_factor
        self.last_adjustment_time = current_time

        # Calculate final chunk size with bounds
        chunk_size = int(self.base_chunk_size * self.adjustment_factor)
        return max(100, min(5000, chunk_size))  # Reasonable bounds


class MemoryAwareChunkingStrategy(ChunkingStrategyBase):
    """Memory-aware chunking that optimizes for memory constraints"""

    def __init__(self, memory_limit_gb: float = 4.0, safety_margin: float = 0.8):
        super().__init__("memory_aware")
        self.memory_limit_gb = memory_limit_gb
        self.safety_margin = safety_margin
        self.effective_limit_gb = memory_limit_gb * safety_margin

    def calculate_chunk_size(self, context: Dict[str, Any]) -> int:
        """Calculate chunk size based on memory constraints"""
        current_memory_gb = context.get('memory_usage_gb', 1.0)
        total_combinations = context.get('total_combinations', 0)
        remaining_combinations = context.get('remaining_combinations', total_combinations)

        # Calculate memory pressure
        memory_pressure = current_memory_gb / self.effective_limit_gb

        if memory_pressure > 0.9:
            # High pressure: very small chunks
            return max(50, remaining_combinations // 100)
        elif memory_pressure > 0.7:
            # Medium pressure: moderate chunks
            return max(200, remaining_combinations // 50)
        elif memory_pressure > 0.5:
            # Low pressure: larger chunks
            return max(500, remaining_combinations // 20)
        else:
            # No pressure: can use larger chunks
            return min(2000, remaining_combinations // 10)


class PerformanceOptimizedChunkingStrategy(ChunkingStrategyBase):
    """Performance-optimized chunking that maximizes throughput"""

    def __init__(self):
        super().__init__("performance_optimized")
        self.optimal_chunk_size = 1000
        self.performance_window = deque(maxlen=10)

    def calculate_chunk_size(self, context: Dict[str, Any]) -> int:
        """Calculate chunk size optimized for performance"""
        current_speed = context.get('combinations_per_second', 0)
        worker_count = context.get('worker_count', 4)

        # Add to performance tracking
        self.performance_window.append(current_speed)

        if len(self.performance_window) < 3:
            return self.optimal_chunk_size

        # Analyze performance trend
        recent_speeds = list(self.performance_window)
        avg_speed = np.mean(recent_speeds)
        speed_std = np.std(recent_speeds)

        # Adjust chunk size based on performance consistency
        if speed_std < avg_speed * 0.1:  # Very consistent performance
            # Can increase chunk size
            new_chunk_size = int(self.optimal_chunk_size * 1.2)
        elif speed_std > avg_speed * 0.3:  # High variance
            # Should decrease chunk size
            new_chunk_size = int(self.optimal_chunk_size * 0.8)
        else:
            # Keep current size
            new_chunk_size = self.optimal_chunk_size

        # Adjust for worker count
        worker_adjusted_size = new_chunk_size * (worker_count / 4)  # Normalize to 4 workers

        # Update optimal size with bounds
        self.optimal_chunk_size = max(200, min(3000, int(worker_adjusted_size)))
        return self.optimal_chunk_size


class PredictiveChunkingStrategy(ChunkingStrategyBase):
    """Predictive chunking using historical performance data"""

    def __init__(self):
        super().__init__("predictive")
        self.performance_model = {}
        self.feature_cache = {}

    def calculate_chunk_size(self, context: Dict[str, Any]) -> int:
        """Calculate chunk size using predictive model"""
        # Extract features
        features = self._extract_features(context)
        strategy_name = context.get('strategy_name', 'unknown')

        # Get cached prediction or calculate new one
        cache_key = (strategy_name, tuple(sorted(features.items())))

        if cache_key in self.feature_cache:
            prediction = self.feature_cache[cache_key]
        else:
            prediction = self._predict_optimal_chunk_size(strategy_name, features)
            self.feature_cache[cache_key] = prediction

        # Apply bounds and safety factors
        chunk_size = int(prediction * 0.9)  # 10% safety margin
        return max(100, min(2000, chunk_size))

    def _extract_features(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Extract relevant features for prediction"""
        return {
            'memory_usage': context.get('memory_usage_percent', 0) / 100,
            'cpu_usage': context.get('cpu_usage_percent', 0) / 100,
            'total_combinations': np.log10(max(1, context.get('total_combinations', 1))),
            'remaining_ratio': context.get('remaining_combinations', 1) / max(1, context.get('total_combinations', 1)),
            'worker_count': context.get('worker_count', 4) / 8,  # Normalize to 8 workers
            'avg_combination_complexity': context.get('complexity_score', 1.0)
        }

    def _predict_optimal_chunk_size(self, strategy_name: str, features: Dict[str, float]) -> float:
        """Predict optimal chunk size using simple linear model"""
        if strategy_name not in self.performance_model:
            # Initialize model with default coefficients
            self.performance_model[strategy_name] = {
                'memory_coeff': -500,
                'cpu_coeff': -300,
                'size_coeff': 200,
                'remaining_coeff': 1000,
                'worker_coeff': 150,
                'complexity_coeff': -200,
                'base_size': 800
            }

        model = self.performance_model[strategy_name]

        # Simple linear prediction
        prediction = (
            model['base_size'] +
            model['memory_coeff'] * features['memory_usage'] +
            model['cpu_coeff'] * features['cpu_usage'] +
            model['size_coeff'] * features['total_combinations'] +
            model['remaining_coeff'] * features['remaining_ratio'] +
            model['worker_coeff'] * features['worker_count'] +
            model['complexity_coeff'] * features['avg_combination_complexity']
        )

        return max(100, prediction)


class HybridChunkingStrategy(ChunkingStrategyBase):
    """Hybrid strategy that combines multiple approaches"""

    def __init__(self):
        super().__init__("hybrid")
        self.strategies = {
            'adaptive': AdaptiveChunkingStrategy(),
            'memory_aware': MemoryAwareChunkingStrategy(),
            'performance_optimized': PerformanceOptimizedChunkingStrategy(),
            'predictive': PredictiveChunkingStrategy()
        }
        self.strategy_weights = {
            'adaptive': 0.3,
            'memory_aware': 0.3,
            'performance_optimized': 0.2,
            'predictive': 0.2
        }

    def calculate_chunk_size(self, context: Dict[str, Any]) -> int:
        """Calculate chunk size using weighted combination of strategies"""
        strategy_results = {}

        # Get recommendations from all strategies
        for name, strategy in self.strategies.items():
            try:
                strategy_results[name] = strategy.calculate_chunk_size(context)
            except Exception as e:
                logger.warning(f"Strategy {name} failed: {str(e)}")
                strategy_results[name] = 1000  # Default fallback

        # Calculate weighted average
        weighted_sum = sum(
            size * self.strategy_weights[name]
            for name, size in strategy_results.items()
        )

        # Add variance to avoid getting stuck in local optima
        noise_factor = np.random.normal(0, 50)
        final_size = int(weighted_sum + noise_factor)

        # Apply bounds
        return max(100, min(2000, final_size))

    def update_strategy_weights(self, performance_feedback: Dict[str, float]):
        """Update strategy weights based on performance feedback"""
        for strategy_name, performance_score in performance_feedback.items():
            if strategy_name in self.strategy_weights:
                # Simple reinforcement learning update
                current_weight = self.strategy_weights[strategy_name]
                self.strategy_weights[strategy_name] = (
                    0.8 * current_weight + 0.2 * performance_score
                )

        # Normalize weights
        total_weight = sum(self.strategy_weights.values())
        if total_weight > 0:
            for name in self.strategy_weights:
                self.strategy_weights[name] /= total_weight


class IntelligentChunker:
    """
    Main intelligent chunking system that coordinates multiple strategies

    Provides intelligent parameter chunking for large-scale optimization
    with adaptive algorithms and real-time performance monitoring.
    """

    def __init__(self, config=None):
        """Initialize intelligent chunker"""
        if config is None:
            from ..core.config import DEFAULT_CONFIG
            config = DEFAULT_CONFIG

        self.config = config
        self.memory_limit_gb = config.memory_limit_gb

        # Initialize strategies
        self.strategies = {
            ChunkingStrategy.ADAPTIVE: AdaptiveChunkingStrategy(config.chunk_size),
            ChunkingStrategy.MEMORY_AWARE: MemoryAwareChunkingStrategy(self.memory_limit_gb),
            ChunkingStrategy.PERFORMANCE_OPTIMIZED: PerformanceOptimizedChunkingStrategy(),
            ChunkingStrategy.PREDICTIVE: PredictiveChunkingStrategy(),
            ChunkingStrategy.HYBRID: HybridChunkingStrategy()
        }

        self.current_strategy = ChunkingStrategy.HYBRID
        self.chunk_profiles = {}
        self.metrics_history = defaultdict(list)

        # Performance tracking
        self.performance_optimizer = threading.Thread(target=self._performance_optimization_loop, daemon=True)
        self.performance_optimizer.start()

        logger.info(f"Initialized IntelligentChunker with {len(self.strategies)} strategies")

    def calculate_optimal_chunk_size(self, strategy_name: str, total_combinations: int,
                                  remaining_combinations: int, current_memory_gb: float,
                                  additional_context: Optional[Dict] = None) -> int:
        """
        Calculate optimal chunk size for current conditions

        Args:
            strategy_name: Name of the strategy being optimized
            total_combinations: Total number of parameter combinations
            remaining_combinations: Remaining combinations to process
            current_memory_gb: Current memory usage in GB
            additional_context: Additional context information

        Returns:
            Optimal chunk size
        """
        # Get system metrics
        memory_percent = (current_memory_gb / self.memory_limit_gb) * 100
        cpu_percent = psutil.cpu_percent(interval=1)

        # Build context for strategies
        context = {
            'strategy_name': strategy_name,
            'total_combinations': total_combinations,
            'remaining_combinations': remaining_combinations,
            'memory_usage_gb': current_memory_gb,
            'memory_usage_percent': memory_percent,
            'cpu_usage_percent': cpu_percent,
            'worker_count': self.config.max_workers,
            'timestamp': time.time()
        }

        # Add additional context if provided
        if additional_context:
            context.update(additional_context)

        # Get strategy-specific chunk profile if available
        if strategy_name in self.chunk_profiles:
            profile = self.chunk_profiles[strategy_name]
            context['profile_optimal_size'] = profile.optimal_chunk_size
            context['profile_memory_multiplier'] = profile.memory_multiplier

        # Calculate chunk size using current strategy
        strategy = self.strategies[self.current_strategy]
        optimal_size = strategy.calculate_chunk_size(context)

        # Apply final bounds and safety checks
        final_size = self._apply_safety_bounds(optimal_size, context)

        # Log decision for debugging
        logger.debug(f"Chunk size calculation: strategy={self.current_strategy.value}, "
                    f"size={final_size}, memory={memory_percent:.1f}%, cpu={cpu_percent:.1f}%")

        return final_size

    def _apply_safety_bounds(self, chunk_size: int, context: Dict[str, Any]) -> int:
        """Apply safety bounds to calculated chunk size"""
        # Memory-based bounds
        memory_pressure = context.get('memory_usage_percent', 0) / 100
        if memory_pressure > 0.9:
            chunk_size = min(chunk_size, 100)
        elif memory_pressure > 0.7:
            chunk_size = min(chunk_size, 500)

        # Remaining combinations bound
        remaining = context.get('remaining_combinations', float('inf'))
        if chunk_size > remaining:
            chunk_size = max(1, int(remaining))

        # Strategy-specific bounds
        strategy_name = context.get('strategy_name', '')
        if strategy_name in self.chunk_profiles:
            profile = self.chunk_profiles[strategy_name]
            chunk_size = max(profile.min_chunk_size, min(profile.max_chunk_size, chunk_size))

        # System-wide bounds
        chunk_size = max(10, min(5000, chunk_size))

        return chunk_size

    def record_chunk_performance(self, strategy_name: str, chunk_metrics: ChunkMetrics):
        """Record performance metrics for a processed chunk"""
        self.metrics_history[strategy_name].append(chunk_metrics)

        # Update strategy metrics
        strategy = self.strategies[self.current_strategy]
        strategy.record_chunk_metrics(chunk_metrics)

        # Periodically update chunk profile
        if len(self.metrics_history[strategy_name]) % 10 == 0:
            self._update_chunk_profile(strategy_name)

    def _update_chunk_profile(self, strategy_name: str):
        """Update chunk profile based on recent performance"""
        if len(self.metrics_history[strategy_name]) < 5:
            return

        recent_metrics = self.metrics_history[strategy_name][-20:]  # Last 20 chunks

        # Calculate statistics
        chunk_sizes = [m.chunk_size for m in recent_metrics]
        performance_scores = [m.performance_score() for m in recent_metrics]
        success_rates = [m.success_rate for m in recent_metrics]

        # Find optimal chunk size
        optimal_idx = np.argmax(performance_scores)
        optimal_size = chunk_sizes[optimal_idx]

        # Calculate profile characteristics
        profile = ChunkProfile(
            strategy_name=strategy_name,
            optimal_chunk_size=optimal_size,
            min_chunk_size=max(10, int(np.percentile(chunk_sizes, 10))),
            max_chunk_size=min(5000, int(np.percentile(chunk_sizes, 90))),
            memory_multiplier=1.0,  # Would be calculated from actual metrics
            performance_multiplier=performance_scores[optimal_idx],
            chunk_size_variance=np.std(chunk_sizes),
            stability_score=1.0 - np.std(success_rates)
        )

        self.chunk_profiles[strategy_name] = profile

        logger.info(f"Updated chunk profile for {strategy_name}: optimal_size={optimal_size}")

    def _performance_optimization_loop(self):
        """Background thread for performance optimization"""
        while True:
            try:
                time.sleep(60)  # Check every minute

                # Analyze current strategy performance
                strategy = self.strategies[self.current_strategy]
                trend = strategy.get_performance_trend()

                # Consider strategy switching if performance is degrading
                if trend == "degrading":
                    self._consider_strategy_switch()

                # Optimize strategy weights for hybrid strategy
                if isinstance(strategy, HybridChunkingStrategy):
                    self._optimize_hybrid_weights(strategy)

            except Exception as e:
                logger.error(f"Performance optimization error: {str(e)}")

    def _consider_strategy_switch(self):
        """Consider switching to a different chunking strategy"""
        current_performance = self._evaluate_strategy_performance(self.current_strategy)

        best_strategy = self.current_strategy
        best_performance = current_performance

        # Evaluate all strategies
        for strategy_type, strategy in self.strategies.items():
            if strategy_type == self.current_strategy:
                continue

            performance = self._evaluate_strategy_performance(strategy_type)
            if performance > best_performance * 1.1:  # 10% improvement threshold
                best_strategy = strategy_type
                best_performance = performance

        # Switch if better strategy found
        if best_strategy != self.current_strategy:
            logger.info(f"Switching chunking strategy: {self.current_strategy.value} -> {best_strategy.value}")
            self.current_strategy = best_strategy

    def _evaluate_strategy_performance(self, strategy_type: ChunkingStrategy) -> float:
        """Evaluate the performance of a specific strategy"""
        strategy = self.strategies[strategy_type]

        if len(strategy.metrics_history) < 5:
            return 0.5  # Default score for insufficient data

        recent_metrics = list(strategy.metrics_history)[-10:]
        performance_scores = [m.performance_score() for m in recent_metrics]

        return np.mean(performance_scores)

    def _optimize_hybrid_weights(self, hybrid_strategy: HybridChunkingStrategy):
        """Optimize weights for hybrid strategy based on recent performance"""
        performance_feedback = {}

        for name, strategy in hybrid_strategy.strategies.items():
            if len(strategy.metrics_history) >= 3:
                recent_metrics = list(strategy.metrics_history)[-5:]
                avg_performance = np.mean([m.performance_score() for m in recent_metrics])
                performance_feedback[name] = avg_performance

        if performance_feedback:
            hybrid_strategy.update_strategy_weights(performance_feedback)

    def get_chunking_statistics(self) -> Dict[str, Any]:
        """Get comprehensive chunking statistics"""
        stats = {
            'current_strategy': self.current_strategy.value,
            'chunk_profiles': {},
            'strategy_performance': {},
            'recent_metrics': {}
        }

        # Add chunk profiles
        for strategy_name, profile in self.chunk_profiles.items():
            stats['chunk_profiles'][strategy_name] = {
                'optimal_chunk_size': profile.optimal_chunk_size,
                'stability_score': profile.stability_score,
                'chunk_size_variance': profile.chunk_size_variance
            }

        # Add strategy performance
        for strategy_type, strategy in self.strategies.items():
            stats['strategy_performance'][strategy_type.value] = {
                'trend': strategy.get_performance_trend(),
                'metrics_count': len(strategy.metrics_history)
            }

        # Add recent metrics for current strategy
        current_strategy = self.strategies[self.current_strategy]
        if current_strategy.metrics_history:
            recent_metrics = list(current_strategy.metrics_history)[-5:]
            stats['recent_metrics'] = {
                'avg_chunk_size': np.mean([m.chunk_size for m in recent_metrics]),
                'avg_processing_time': np.mean([m.processing_time for m in recent_metrics]),
                'avg_success_rate': np.mean([m.success_rate for m in recent_metrics]),
                'avg_performance_score': np.mean([m.performance_score() for m in recent_metrics])
            }

        return stats

    def switch_strategy(self, strategy_type: ChunkingStrategy):
        """Manually switch to a specific chunking strategy"""
        if strategy_type in self.strategies:
            self.current_strategy = strategy_type
            logger.info(f"Manually switched to {strategy_type.value} chunking strategy")
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy_type}")

    def reset_metrics(self):
        """Reset all metrics and learning data"""
        for strategy in self.strategies.values():
            strategy.metrics_history.clear()

        self.metrics_history.clear()
        self.chunk_profiles.clear()

        logger.info("Reset all chunking metrics and learning data")

    def export_chunk_profiles(self, filepath: str):
        """Export chunk profiles to file"""
        import json

        profiles_data = {}
        for strategy_name, profile in self.chunk_profiles.items():
            profiles_data[strategy_name] = {
                'optimal_chunk_size': profile.optimal_chunk_size,
                'min_chunk_size': profile.min_chunk_size,
                'max_chunk_size': profile.max_chunk_size,
                'memory_multiplier': profile.memory_multiplier,
                'performance_multiplier': profile.performance_multiplier,
                'chunk_size_variance': profile.chunk_size_variance,
                'stability_score': profile.stability_score
            }

        with open(filepath, 'w') as f:
            json.dump(profiles_data, f, indent=2)

        logger.info(f"Exported chunk profiles to {filepath}")

    def import_chunk_profiles(self, filepath: str):
        """Import chunk profiles from file"""
        import json

        with open(filepath, 'r') as f:
            profiles_data = json.load(f)

        for strategy_name, profile_data in profiles_data.items():
            self.chunk_profiles[strategy_name] = ChunkProfile(
                strategy_name=strategy_name,
                **profile_data
            )

        logger.info(f"Imported {len(profiles_data)} chunk profiles from {filepath}")