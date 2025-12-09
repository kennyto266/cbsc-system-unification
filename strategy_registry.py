#!/usr/bin/env python3
"""
Strategy Registry System
Comprehensive strategy management, versioning, and performance tracking
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import sqlite3
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import threading
import pickle

# Import from our framework
from comprehensive_strategy_framework import (
    StrategyType, MarketState, StrategyDefinition,
    BaseStrategy, BacktestResult
)

logger = logging.getLogger(__name__)


class StrategyStatus(Enum):
    """Strategy status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class StrategyPerformance:
    """Strategy performance tracking data"""
    strategy_name: str
    backtest_count: int = 0
    avg_sharpe_ratio: float = 0.0
    avg_total_return: float = 0.0
    avg_max_drawdown: float = 0.0
    best_sharpe_ratio: float = 0.0
    best_total_return: float = 0.0
    worst_sharpe_ratio: float = 0.0
    worst_total_return: float = 0.0
    win_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    risk_rating: str = "medium"  # low, medium, high
    reliability_score: float = 0.0  # 0.0 to 1.0


@dataclass
class StrategyMetadata:
    """Extended strategy metadata"""
    strategy_name: str
    status: StrategyStatus = StrategyStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    creator: str = "system"
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    description: str = ""
    notes: str = ""
    dependencies: List[str] = field(default_factory=list)
    compatibility: List[str] = field(default_factory=list)  # Compatible data sources
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    execution_stats: Dict[str, Any] = field(default_factory=dict)
    rating: float = 0.0  # 0.0 to 5.0
    user_reviews: List[Dict[str, Any]] = field(default_factory=list)


class StrategyRegistry:
    """Comprehensive strategy registry with database backend"""

    def __init__(self, db_path: str = "data/strategy_registry.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._performance_cache: Dict[str, StrategyPerformance] = {}
        self._metadata_cache: Dict[str, StrategyMetadata] = {}

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._initialize_database()

        # Load existing strategies
        self._load_cached_strategies()

    def _initialize_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Strategies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategies (
                    name TEXT PRIMARY KEY,
                    strategy_type TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    version TEXT DEFAULT '1.0.0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    creator TEXT DEFAULT 'system',
                    tags TEXT DEFAULT '[]',
                    description TEXT DEFAULT '',
                    rating REAL DEFAULT 0.0
                )
            ''')

            # Performance tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    backtest_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sharpe_ratio REAL,
                    total_return REAL,
                    max_drawdown REAL,
                    win_rate REAL,
                    execution_time REAL,
                    data_period TEXT,
                    parameters TEXT,
                    performance_metrics TEXT,
                    FOREIGN KEY (strategy_name) REFERENCES strategies (name)
                )
            ''')

            # Strategy versions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    definition TEXT NOT NULL,
                    changelog TEXT,
                    is_current BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (strategy_name) REFERENCES strategies (name)
                )
            ''')

            # Strategy dependencies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_dependencies (
                    strategy_name TEXT NOT NULL,
                    dependency_name TEXT NOT NULL,
                    dependency_type TEXT NOT NULL,
                    version_constraint TEXT,
                    PRIMARY KEY (strategy_name, dependency_name),
                    FOREIGN KEY (strategy_name) REFERENCES strategies (name)
                )
            ''')

            # User reviews table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    review_text TEXT,
                    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    helpful_count INTEGER DEFAULT 0,
                    FOREIGN KEY (strategy_name) REFERENCES strategies (name)
                )
            ''')

            conn.commit()

    def _load_cached_strategies(self):
        """Load existing strategies into cache"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Load strategies
            cursor.execute('SELECT * FROM strategies')
            for row in cursor.fetchall():
                strategy_name = row[0]
                metadata = StrategyMetadata(
                    strategy_name=strategy_name,
                    status=StrategyStatus(row[4]),
                    created_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[7]) if row[7] else datetime.now(),
                    creator=row[8],
                    version=row[9],
                    tags=json.loads(row[10]) if row[10] else [],
                    description=row[11],
                    rating=row[12]
                )
                self._metadata_cache[strategy_name] = metadata

            # Load performance data
            cursor.execute('''
                SELECT strategy_name,
                       COUNT(*) as backtest_count,
                       AVG(sharpe_ratio) as avg_sharpe,
                       AVG(total_return) as avg_return,
                       AVG(max_drawdown) as avg_drawdown,
                       MAX(sharpe_ratio) as best_sharpe,
                       MAX(total_return) as best_return,
                       MIN(sharpe_ratio) as worst_sharpe,
                       MIN(total_return) as worst_return
                FROM strategy_performance
                GROUP BY strategy_name
            ''')

            for row in cursor.fetchall():
                strategy_name = row[0]
                performance = StrategyPerformance(
                    strategy_name=strategy_name,
                    backtest_count=row[1],
                    avg_sharpe_ratio=row[2] or 0.0,
                    avg_total_return=row[3] or 0.0,
                    avg_max_drawdown=row[4] or 0.0,
                    best_sharpe_ratio=row[5] or 0.0,
                    best_total_return=row[6] or 0.0,
                    worst_sharpe_ratio=row[7] or 0.0,
                    worst_total_return=row[8] or 0.0
                )
                self._performance_cache[strategy_name] = performance

        self.logger.info(f"Loaded {len(self._metadata_cache)} strategies and {len(self._performance_cache)} performance records")

    def register_strategy(self, strategy: BaseStrategy, definition: StrategyDefinition = None) -> bool:
        """Register a new strategy"""
        with self._lock:
            try:
                strategy_name = strategy.name

                # Create definition if not provided
                if definition is None:
                    definition = StrategyDefinition(
                        name=strategy_name,
                        strategy_type=strategy.strategy_type,
                        description=f"{strategy.strategy_type.value} strategy",
                        parameters=strategy.parameters,
                        tags=[strategy.strategy_type.value]
                    )

                # Create metadata
                metadata = StrategyMetadata(
                    strategy_name=strategy_name,
                    status=StrategyStatus.ACTIVE,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    version="1.0.0",
                    tags=definition.tags,
                    description=definition.description
                )

                # Store in database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Insert strategy
                    cursor.execute('''
                        INSERT OR REPLACE INTO strategies
                        (name, strategy_type, parameters, definition, status, version, created_at, updated_at, tags, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        strategy_name,
                        strategy.strategy_type.value,
                        json.dumps(strategy.parameters),
                        json.dumps(asdict(definition)),
                        metadata.status.value,
                        metadata.version,
                        metadata.created_at.isoformat(),
                        metadata.updated_at.isoformat(),
                        json.dumps(metadata.tags),
                        metadata.description
                    ))

                    conn.commit()

                # Update cache
                self._metadata_cache[strategy_name] = metadata

                # Initialize performance if not exists
                if strategy_name not in self._performance_cache:
                    self._performance_cache[strategy_name] = StrategyPerformance(
                        strategy_name=strategy_name
                    )

                self.logger.info(f"Registered strategy: {strategy_name}")
                return True

            except Exception as e:
                self.logger.error(f"Error registering strategy {strategy.name}: {e}")
                return False

    def update_strategy_performance(self, result: BacktestResult) -> bool:
        """Update strategy performance with new backtest results"""
        with self._lock:
            try:
                strategy_name = result.strategy_name

                # Update cache
                if strategy_name not in self._performance_cache:
                    self._performance_cache[strategy_name] = StrategyPerformance(
                        strategy_name=strategy_name
                    )

                perf = self._performance_cache[strategy_name]
                perf.backtest_count += 1

                # Update averages
                total_count = perf.backtest_count
                old_count = total_count - 1

                sharpe = result.sharpe_ratio
                total_return = result.performance_metrics.get('total_return', 0)
                max_dd = result.max_drawdown

                perf.avg_sharpe_ratio = (perf.avg_sharpe_ratio * old_count + sharpe) / total_count
                perf.avg_total_return = (perf.avg_total_return * old_count + total_return) / total_count
                perf.avg_max_drawdown = (perf.avg_max_drawdown * old_count + max_dd) / total_count

                # Update best/worst
                perf.best_sharpe_ratio = max(perf.best_sharpe_ratio, sharpe)
                perf.best_total_return = max(perf.best_total_return, total_return)
                perf.worst_sharpe_ratio = min(perf.worst_sharpe_ratio, sharpe) if perf.worst_sharpe_ratio > 0 else sharpe
                perf.worst_total_return = min(perf.worst_total_return, total_return)

                perf.last_updated = datetime.now()

                # Add to performance history
                perf.performance_history.append({
                    'date': result.end_date.isoformat(),
                    'sharpe_ratio': sharpe,
                    'total_return': total_return,
                    'max_drawdown': max_dd,
                    'execution_time': result.execution_time
                })

                # Keep only last 100 entries
                if len(perf.performance_history) > 100:
                    perf.performance_history = perf.performance_history[-100:]

                # Store in database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT INTO strategy_performance
                        (strategy_name, backtest_date, sharpe_ratio, total_return, max_drawdown,
                         win_rate, execution_time, parameters, performance_metrics)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        strategy_name,
                        result.end_date.isoformat(),
                        result.sharpe_ratio,
                        result.performance_metrics.get('total_return', 0),
                        result.max_drawdown,
                        result.win_rate,
                        result.execution_time,
                        json.dumps(result.parameters),
                        json.dumps(result.performance_metrics)
                    ))

                    conn.commit()

                # Update reliability score based on consistency
                self._update_reliability_score(strategy_name)

                self.logger.info(f"Updated performance for {strategy_name}: Sharpe={sharpe:.3f}, Return={total_return:.2%}")
                return True

            except Exception as e:
                self.logger.error(f"Error updating performance for {result.strategy_name}: {e}")
                return False

    def _update_reliability_score(self, strategy_name: str):
        """Calculate reliability score based on performance consistency"""
        if strategy_name not in self._performance_cache:
            return

        perf = self._performance_cache[strategy_name]

        if perf.backtest_count < 5:
            perf.reliability_score = 0.5  # Insufficient data
            return

        # Calculate reliability based on:
        # 1. Consistency of Sharpe ratio
        # 2. Low volatility in returns
        # 3. Reasonable maximum drawdown
        # 4. Consistency across different time periods

        recent_performances = perf.performance_history[-10:] if perf.performance_history else []

        if len(recent_performances) >= 3:
            sharpe_values = [p['sharpe_ratio'] for p in recent_performances]
            return_values = [p['total_return'] for p in recent_performances]

            # Sharpe ratio consistency (lower std dev is better)
            sharpe_std = pd.Series(sharpe_values).std()
            sharpe_consistency = max(0, 1 - (sharpe_std / max(abs(min(sharpe_values)), abs(max(sharpe_values)), 1)))

            # Return stability (lower std dev relative to mean is better)
            return_std = pd.Series(return_values).std()
            return_mean = pd.Series(return_values).mean()
            return_stability = max(0, 1 - (return_std / max(abs(return_mean), 1)))

            # Drawdown control (lower max drawdown is better)
            max_dd = max([p['max_drawdown'] for p in recent_performances])
            drawdown_score = max(0, 1 - abs(max_dd) * 2)  # Penalize high drawdowns

            # Combine scores
            perf.reliability_score = (sharpe_consistency * 0.4 +
                                     return_stability * 0.3 +
                                     drawdown_score * 0.3)

            # Update risk rating
            if perf.reliability_score > 0.8:
                perf.risk_rating = "low"
            elif perf.reliability_score > 0.6:
                perf.risk_rating = "medium"
            else:
                perf.risk_rating = "high"

    def get_strategy_performance(self, strategy_name: str) -> Optional[StrategyPerformance]:
        """Get performance data for a specific strategy"""
        return self._performance_cache.get(strategy_name)

    def get_strategy_metadata(self, strategy_name: str) -> Optional[StrategyMetadata]:
        """Get metadata for a specific strategy"""
        return self._metadata_cache.get(strategy_name)

    def search_strategies(self,
                         strategy_type: Optional[StrategyType] = None,
                         min_sharpe: Optional[float] = None,
                         min_return: Optional[float] = None,
                         max_drawdown: Optional[float] = None,
                         tags: Optional[List[str]] = None,
                         status: Optional[StrategyStatus] = None) -> List[str]:
        """Search strategies by multiple criteria"""
        matching_strategies = []

        for strategy_name in self._metadata_cache:
            metadata = self._metadata_cache[strategy_name]
            performance = self._performance_cache.get(strategy_name)

            # Filter by status
            if status and metadata.status != status:
                continue

            # Filter by strategy type
            if strategy_type:
                # Check tags for strategy type
                if strategy_type.value not in metadata.tags:
                    continue

            # Filter by performance criteria
            if performance:
                if min_sharpe and performance.avg_sharpe_ratio < min_sharpe:
                    continue
                if min_return and performance.avg_total_return < min_return:
                    continue
                if max_drawdown and abs(performance.avg_max_drawdown) > max_drawdown:
                    continue

            # Filter by tags
            if tags:
                if not any(tag in metadata.tags for tag in tags):
                    continue

            matching_strategies.append(strategy_name)

        return matching_strategies

    def get_top_strategies(self,
                          metric: str = 'sharpe_ratio',
                          limit: int = 10,
                          min_backtests: int = 1) -> List[Tuple[str, float]]:
        """Get top performing strategies by specified metric"""
        strategies = []

        for strategy_name, performance in self._performance_cache.items():
            if performance.backtest_count < min_backtests:
                continue

            if metric == 'sharpe_ratio':
                value = performance.avg_sharpe_ratio
            elif metric == 'total_return':
                value = performance.avg_total_return
            elif metric == 'reliability':
                value = performance.reliability_score
            else:
                continue

            strategies.append((strategy_name, value))

        # Sort by value (descending)
        strategies.sort(key=lambda x: x[1], reverse=True)
        return strategies[:limit]

    def get_strategy_correlation_matrix(self, strategy_names: List[str] = None) -> pd.DataFrame:
        """Calculate correlation matrix between strategies"""
        if strategy_names is None:
            strategy_names = list(self._performance_cache.keys())

        if len(strategy_names) < 2:
            return pd.DataFrame()

        # Extract performance history for correlation analysis
        performance_data = {}
        min_length = float('inf')

        for strategy_name in strategy_names:
            perf = self._performance_cache.get(strategy_name)
            if perf and perf.performance_history:
                returns = [p['total_return'] for p in perf.performance_history]
                performance_data[strategy_name] = returns
                min_length = min(min_length, len(returns))

        if not performance_data:
            return pd.DataFrame()

        # Align data lengths
        aligned_data = {}
        for strategy_name, returns in performance_data.items():
            aligned_data[strategy_name] = returns[-min_length:]

        # Calculate correlation matrix
        df = pd.DataFrame(aligned_data)
        correlation_matrix = df.corr()

        return correlation_matrix

    def get_registry_statistics(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics"""
        with self._lock:
            stats = {
                'total_strategies': len(self._metadata_cache),
                'active_strategies': len([m for m in self._metadata_cache.values() if m.status == StrategyStatus.ACTIVE]),
                'strategies_with_performance': len(self._performance_cache),
                'strategy_types': {},
                'average_sharpe_ratio': 0,
                'best_performing_strategy': None,
                'most_reliable_strategy': None,
                'total_backtests': sum(p.backtest_count for p in self._performance_cache.values()),
                'last_updated': datetime.now().isoformat()
            }

            # Count by strategy type
            for metadata in self._metadata_cache.values():
                for tag in metadata.tags:
                    stats['strategy_types'][tag] = stats['strategy_types'].get(tag, 0) + 1

            # Calculate averages
            if self._performance_cache:
                sharpe_ratios = [p.avg_sharpe_ratio for p in self._performance_cache.values() if p.backtest_count > 0]
                if sharpe_ratios:
                    stats['average_sharpe_ratio'] = sum(sharpe_ratios) / len(sharpe_ratios)

                # Find best performing
                best_strategy = max(self._performance_cache.items(),
                                   key=lambda x: x[1].avg_sharpe_ratio if x[1].backtest_count > 0 else 0)
                stats['best_performing_strategy'] = {
                    'name': best_strategy[0],
                    'avg_sharpe_ratio': best_strategy[1].avg_sharpe_ratio,
                    'avg_total_return': best_strategy[1].avg_total_return
                }

                # Find most reliable
                most_reliable = max(self._performance_cache.items(),
                                    key=lambda x: x[1].reliability_score)
                stats['most_reliable_strategy'] = {
                    'name': most_reliable[0],
                    'reliability_score': most_reliable[1].reliability_score,
                    'backtest_count': most_reliable[1].backtest_count
                }

            return stats

    def export_strategies(self, file_path: str, strategy_names: List[str] = None):
        """Export strategies to JSON file"""
        if strategy_names is None:
            strategy_names = list(self._metadata_cache.keys())

        export_data = {
            'export_date': datetime.now().isoformat(),
            'strategies': []
        }

        for strategy_name in strategy_names:
            metadata = self._metadata_cache.get(strategy_name)
            performance = self._performance_cache.get(strategy_name)

            strategy_data = {
                'metadata': asdict(metadata) if metadata else None,
                'performance': asdict(performance) if performance else None
            }

            export_data['strategies'].append(strategy_data)

        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        self.logger.info(f"Exported {len(strategy_names)} strategies to {file_path}")

    def import_strategies(self, file_path: str) -> int:
        """Import strategies from JSON file"""
        try:
            with open(file_path, 'r') as f:
                import_data = json.load(f)

            imported_count = 0
            for strategy_data in import_data.get('strategies', []):
                # Reconstruct metadata
                metadata_dict = strategy_data.get('metadata')
                if metadata_dict:
                    metadata_dict['status'] = StrategyStatus(metadata_dict.get('status', 'active'))
                    metadata_dict['created_at'] = datetime.fromisoformat(metadata_dict['created_at'])
                    metadata_dict['updated_at'] = datetime.fromisoformat(metadata_dict['updated_at'])
                    metadata = StrategyMetadata(**metadata_dict)
                    self._metadata_cache[metadata.strategy_name] = metadata

                # Reconstruct performance
                perf_dict = strategy_data.get('performance')
                if perf_dict:
                    perf_dict['last_updated'] = datetime.fromisoformat(perf_dict['last_updated'])
                    performance = StrategyPerformance(**perf_dict)
                    self._performance_cache[performance.strategy_name] = performance

                imported_count += 1

            self.logger.info(f"Imported {imported_count} strategies from {file_path}")
            return imported_count

        except Exception as e:
            self.logger.error(f"Error importing strategies from {file_path}: {e}")
            return 0

    def cleanup_old_data(self, days_to_keep: int = 365):
        """Clean up old performance data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Delete old performance records
            cursor.execute('''
                DELETE FROM strategy_performance
                WHERE backtest_date < ?
            ''', (cutoff_date.isoformat(),))

            deleted_count = cursor.rowcount
            conn.commit()

        self.logger.info(f"Cleaned up {deleted_count} old performance records")

        # Clear cache and reload
        self._performance_cache.clear()
        self._load_cached_strategies()


# Factory function
def create_strategy_registry(db_path: str = "data/strategy_registry.db") -> StrategyRegistry:
    """Factory function to create strategy registry"""
    return StrategyRegistry(db_path)


# Main execution for testing
if __name__ == "__main__":
    # Test the registry system
    print("Strategy Registry System Test")
    print("=" * 40)

    # Create registry
    registry = create_strategy_registry()

    # Print statistics
    stats = registry.get_registry_statistics()
    print(f"Registry Statistics:")
    print(f"  Total Strategies: {stats['total_strategies']}")
    print(f"  Active Strategies: {stats['active_strategies']}")
    print(f"  Strategies with Performance: {stats['strategies_with_performance']}")
    print(f"  Total Backtests: {stats['total_backtests']}")

    if stats['strategy_types']:
        print(f"  Strategy Types: {stats['strategy_types']}")

    if stats['best_performing_strategy']:
        best = stats['best_performing_strategy']
        print(f"\nBest Performing Strategy:")
        print(f"  Name: {best['name']}")
        print(f"  Avg Sharpe: {best['avg_sharpe_ratio']:.3f}")
        print(f"  Avg Return: {best['avg_total_return']:.2%}")

    if stats['most_reliable_strategy']:
        reliable = stats['most_reliable_strategy']
        print(f"\nMost Reliable Strategy:")
        print(f"  Name: {reliable['name']}")
        print(f"  Reliability Score: {reliable['reliability_score']:.3f}")
        print(f"  Backtest Count: {reliable['backtest_count']}")

    # Test search functionality
    print(f"\nTesting search functionality...")
    high_sharpe_strategies = registry.search_strategies(min_sharpe=1.0)
    print(f"Strategies with Sharpe > 1.0: {len(high_sharpe_strategies)}")

    # Test top strategies
    top_strategies = registry.get_top_strategies('sharpe_ratio', limit=5)
    print(f"\nTop 5 Strategies by Sharpe Ratio:")
    for i, (name, sharpe) in enumerate(top_strategies, 1):
        print(f"  {i}. {name}: {sharpe:.3f}")

    # Test correlation matrix
    if len(registry._performance_cache) >= 2:
        print(f"\nCalculating strategy correlation matrix...")
        strategy_names = list(registry._performance_cache.keys())[:5]  # First 5 strategies
        correlation_matrix = registry.get_strategy_correlation_matrix(strategy_names)
        if not correlation_matrix.empty:
            print("Correlation Matrix:")
            print(correlation_matrix.round(3))

    # Export test
    export_file = "strategy_registry_export_test.json"
    registry.export_strategies(export_file)
    print(f"\nExported strategies to: {export_file}")

    print("\nStrategy Registry test completed successfully!")