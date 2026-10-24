#!/usr/bin/env python3
"""
Performance Test Script for CBSC Partitioned Tables
Compares query performance before and after partitioning
"""

import os
import sys
import time
import json
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Tuple
import psycopg2
from psycopg2 import sql

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'cbsc'),
    'user': os.getenv('DB_USER', 'cbsc_app'),
    'password': os.getenv('DB_PASSWORD')
}

class PerformanceTester:
    """Test query performance before and after partitioning"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.conn = None
        self.results = []

    def connect(self):
        """Establish database connection"""
        self.conn = psycopg2.connect(**self.db_config)
        self.conn.autocommit = False

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def execute_query(self, query: str, params: Tuple = None) -> Tuple[float, int]:
        """Execute query and return execution time and row count"""
        start_time = time.time()

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                row_count = cur.rowcount
                # Consume results to ensure full execution
                if cur.description:
                    cur.fetchall()

            execution_time = time.time() - start_time
            self.conn.rollback()  # Don't commit changes
            return execution_time, row_count

        except Exception as e:
            self.conn.rollback()
            raise e

    def run_query_test(self, test_name: str, query: str, params: Tuple = None, iterations: int = 5) -> Dict:
        """Run query multiple times and collect statistics"""
        print(f"Running test: {test_name}")
        execution_times = []
        row_counts = []

        for i in range(iterations):
            try:
                exec_time, row_count = self.execute_query(query, params)
                execution_times.append(exec_time)
                row_counts.append(row_count)
                print(f"  Iteration {i+1}: {exec_time:.3f}s, {row_count} rows")
            except Exception as e:
                print(f"  Iteration {i+1}: ERROR - {e}")
                continue

        if not execution_times:
            return {
                'test_name': test_name,
                'status': 'failed',
                'error': 'All iterations failed'
            }

        # Calculate statistics
        result = {
            'test_name': test_name,
            'status': 'completed',
            'iterations': len(execution_times),
            'execution_times': {
                'min': min(execution_times),
                'max': max(execution_times),
                'mean': statistics.mean(execution_times),
                'median': statistics.median(execution_times),
                'stdev': statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            },
            'row_count': row_counts[0] if row_counts else 0,
            'query': query.strip(),
            'improvement': None
        }

        print(f"  Results: avg={result['execution_times']['mean']:.3f}s, "
              f"min={result['execution_times']['min']:.3f}s, "
              f"max={result['execution_times']['max']:.3f}s")

        return result

    def get_test_queries(self) -> List[Dict]:
        """Get list of test queries"""
        queries = [
            {
                'name': 'Recent strategy performance (30 days)',
                'query': '''
                    SELECT strategy_id, AVG(total_return) as avg_return, COUNT(*) as days
                    FROM strategy_performance
                    WHERE date >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY strategy_id
                    ORDER BY avg_return DESC
                    LIMIT 100
                '''
            },
            {
                'name': 'Strategy performance for specific date range',
                'query': '''
                    SELECT *
                    FROM strategy_performance
                    WHERE date BETWEEN %s AND %s
                    AND strategy_id = %s
                    ORDER BY date
                ''',
                'params': ('2024-01-01', '2024-01-31', 'strategy-id-1')
            },
            {
                'name': 'Top performing strategies (Sharpe ratio)',
                'query': '''
                    SELECT
                        sp.strategy_id,
                        s.name as strategy_name,
                        AVG(sp.sharpe_ratio) as avg_sharpe,
                        AVG(sp.total_return) as avg_return,
                        COUNT(*) as days
                    FROM strategy_performance sp
                    JOIN strategies s ON sp.strategy_id = s.id
                    WHERE sp.date >= CURRENT_DATE - INTERVAL '90 days'
                    GROUP BY sp.strategy_id, s.name
                    HAVING COUNT(*) >= 30
                    ORDER BY avg_sharpe DESC
                    LIMIT 50
                '''
            },
            {
                'name': 'Monthly performance aggregation',
                'query': '''
                    SELECT
                        strategy_id,
                        DATE_TRUNC('month', date) as month,
                        AVG(total_return) as avg_return,
                        MAX(total_return) as max_return,
                        MIN(total_return) as min_return,
                        SUM(total_trades) as total_trades
                    FROM strategy_performance
                    WHERE date >= CURRENT_DATE - INTERVAL '12 months'
                    GROUP BY strategy_id, DATE_TRUNC('month', date)
                    ORDER BY strategy_id, month
                '''
            },
            {
                'name': 'Recent trading volume (last 7 days)',
                'query': '''
                    SELECT
                        symbol,
                        COUNT(*) as trade_count,
                        SUM(quantity) as total_quantity,
                        SUM(notional) as total_notional,
                        AVG(price) as avg_price
                    FROM trades
                    WHERE trade_time >= NOW() - INTERVAL '7 days'
                    GROUP BY symbol
                    ORDER BY total_notional DESC
                    LIMIT 100
                '''
            },
            {
                'name': 'Performance metrics trends',
                'query': '''
                    SELECT
                        strategy_id,
                        metric_name,
                        DATE_TRUNC('month', calculation_date) as month,
                        AVG(value) as avg_value
                    FROM performance_metrics
                    WHERE metric_type = 'return'
                      AND calculation_date >= CURRENT_DATE - INTERVAL '6 months'
                    GROUP BY strategy_id, metric_name, DATE_TRUNC('month', calculation_date)
                    ORDER BY strategy_id, metric_name, month
                '''
            },
            {
                'name': 'Strategy performance with join (complex)',
                'query': '''
                    SELECT
                        s.id as strategy_id,
                        s.name,
                        s.strategy_type,
                        s.risk_level,
                        COUNT(DISTINCT sp.date) as active_days,
                        AVG(sp.total_return) as avg_return,
                        AVG(sp.sharpe_ratio) as avg_sharpe,
                        AVG(sp.max_drawdown) as avg_drawdown,
                        SUM(sp.total_trades) as total_trades
                    FROM strategies s
                    LEFT JOIN strategy_performance sp ON s.id = sp.strategy_id
                        AND sp.date >= CURRENT_DATE - INTERVAL '90 days'
                    WHERE s.status = 'active'
                      AND s.is_deleted = false
                    GROUP BY s.id, s.name, s.strategy_type, s.risk_level
                    ORDER BY avg_return DESC NULLS LAST
                    LIMIT 200
                '''
            }
        ]

        return queries

    def run_performance_tests(self, table_suffix: str = '') -> Dict:
        """Run all performance tests"""
        print(f"\n=== Running Performance Tests for {table_suffix or 'current'} tables ===")

        # Update queries with table suffix if provided
        queries = self.get_test_queries()
        if table_suffix:
            for query in queries:
                query['query'] = query['query'].replace('strategy_performance', f'strategy_performance{table_suffix}')
                query['query'] = query['query'].replace('trades', f'trades{table_suffix}')
                query['query'] = query['query'].replace('performance_metrics', f'performance_metrics{table_suffix}')

        test_results = []
        total_start_time = time.time()

        for query_info in queries:
            try:
                result = self.run_query_test(
                    query_info['name'],
                    query_info['query'],
                    query_info.get('params'),
                    iterations=3  # Fewer iterations for faster testing
                )
                test_results.append(result)
                print()
            except Exception as e:
                print(f"  ERROR: {e}\n")
                test_results.append({
                    'test_name': query_info['name'],
                    'status': 'failed',
                    'error': str(e)
                })

        total_duration = time.time() - total_start_time

        return {
            'table_suffix': table_suffix,
            'started_at': datetime.now(timezone.utc).isoformat(),
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'total_duration': total_duration,
            'test_results': test_results,
            'summary': self.calculate_summary(test_results)
        }

    def calculate_summary(self, test_results: List[Dict]) -> Dict:
        """Calculate summary statistics"""
        successful_tests = [r for r in test_results if r['status'] == 'completed']
        failed_tests = [r for r in test_results if r['status'] == 'failed']

        if not successful_tests:
            return {
                'total_tests': len(test_results),
                'successful_tests': 0,
                'failed_tests': len(failed_tests),
                'overall_status': 'failed'
            }

        avg_times = [r['execution_times']['mean'] for r in successful_tests]
        total_rows = sum(r['row_count'] for r in successful_tests)

        summary = {
            'total_tests': len(test_results),
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'overall_status': 'completed' if len(failed_tests) == 0 else 'partial',
            'performance': {
                'avg_execution_time': statistics.mean(avg_times),
                'min_execution_time': min(avg_times),
                'max_execution_time': max(avg_times),
                'total_rows_processed': total_rows
            }
        }

        return summary

    def compare_performance(self, before_results: Dict, after_results: Dict) -> Dict:
        """Compare performance before and after partitioning"""
        comparison = {
            'comparison_date': datetime.now(timezone.utc).isoformat(),
            'before': {
                'summary': before_results['summary'],
                'total_duration': before_results['total_duration']
            },
            'after': {
                'summary': after_results['summary'],
                'total_duration': after_results['total_duration']
            }
        }

        # Compare individual tests
        test_comparisons = []
        before_dict = {r['test_name']: r for r in before_results['test_results']}
        after_dict = {r['test_name']: r for r in after_results['test_results']}

        for test_name in before_dict:
            if test_name in after_dict:
                before = before_dict[test_name]
                after = after_dict[test_name]

                if before['status'] == 'completed' and after['status'] == 'completed':
                    before_time = before['execution_times']['mean']
                    after_time = after['execution_times']['mean']
                    improvement = ((before_time - after_time) / before_time) * 100

                    test_comparison = {
                        'test_name': test_name,
                        'before_time': before_time,
                        'after_time': after_time,
                        'improvement_percent': improvement,
                        'speedup': before_time / after_time if after_time > 0 else None
                    }

                    if improvement > 0:
                        test_comparison['status'] = 'improved'
                    elif improvement < -5:  # More than 5% slower
                        test_comparison['status'] = 'degraded'
                    else:
                        test_comparison['status'] = 'stable'

                    test_comparisons.append(test_comparison)

        comparison['test_comparisons'] = test_comparisons

        # Calculate overall improvement
        if test_comparisons:
            improvements = [tc['improvement_percent'] for tc in test_comparisons if tc['improvement_percent'] is not None]
            if improvements:
                comparison['overall_improvement'] = {
                    'average_improvement_percent': statistics.mean(improvements),
                    'median_improvement_percent': statistics.median(improvements),
                    'improved_tests': len([tc for tc in test_comparisons if tc['status'] == 'improved']),
                    'degraded_tests': len([tc for tc in test_comparisons if tc['status'] == 'degraded']),
                    'stable_tests': len([tc for tc in test_comparisons if tc['status'] == 'stable'])
                }

        return comparison

    def run_comparison_test(self) -> Dict:
        """Run comparison test between original and partitioned tables"""
        print("=== Performance Comparison Test ===")
        print("This will test performance on both original and partitioned tables")

        # Test original tables (with _backup suffix)
        print("\n1. Testing original tables (backup)")
        self.connect()
        before_results = self.run_performance_tests('_backup')
        self.disconnect()

        # Test partitioned tables
        print("\n2. Testing partitioned tables")
        self.connect()
        after_results = self.run_performance_tests()
        self.disconnect()

        # Compare results
        print("\n3. Comparing results")
        comparison = self.compare_performance(before_results, after_results)

        return {
            'before_results': before_results,
            'after_results': after_results,
            'comparison': comparison
        }

    def generate_report(self, results: Dict, filename: str = None) -> str:
        """Generate performance report"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'performance_test_report_{timestamp}.json'

        report = {
            'report_type': 'partition_performance_test',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'results': results
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        return filename

def print_summary(results: Dict):
    """Print performance summary"""
    if 'comparison' not in results:
        print("No comparison results available")
        return

    comparison = results['comparison']
    overall = comparison.get('overall_improvement', {})

    print("\n=== Performance Improvement Summary ===")
    if overall:
        print(f"Average improvement: {overall['average_improvement_percent']:.1f}%")
        print(f"Median improvement: {overall['median_improvement_percent']:.1f}%")
        print(f"Improved tests: {overall['improved_tests']}")
        print(f"Degraded tests: {overall['degraded_tests']}")
        print(f"Stable tests: {overall['stable_tests']}")

    print("\n=== Individual Test Results ===")
    for test_comp in comparison['test_comparisons']:
        status_icon = "✅" if test_comp['status'] == 'improved' else "⚠️" if test_comp['status'] == 'degraded' else "➡️"
        print(f"{status_icon} {test_comp['test_name']}")
        print(f"   Before: {test_comp['before_time']:.3f}s")
        print(f"   After:  {test_comp['after_time']:.3f}s")
        print(f"   Change: {test_comp['improvement_percent']:+.1f}%")
        if test_comp['speedup']:
            print(f"   Speedup: {test_comp['speedup']:.2f}x")
        print()

def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Test performance of CBSC partitioned tables')
    parser.add_argument('--comparison', action='store_true',
                       help='Run comparison test between original and partitioned tables')
    parser.add_argument('--table-suffix', type=str,
                       help='Test specific table variant (e.g., _backup, _partitioned)')
    parser.add_argument('--report-file', type=str,
                       help='Save report to specified file')

    args = parser.parse_args()

    if not DB_CONFIG['password']:
        print("Error: DB_PASSWORD environment variable is required")
        sys.exit(1)

    tester = PerformanceTester(DB_CONFIG)

    try:
        if args.comparison:
            results = tester.run_comparison_test()
        else:
            tester.connect()
            results = tester.run_performance_tests(args.table_suffix or '')
            tester.disconnect()

        # Generate report
        report_file = tester.generate_report(results, args.report_file)
        print(f"\nReport saved to: {report_file}")

        # Print summary if comparison
        if args.comparison:
            print_summary(results)

        # Check if 50% improvement target was met
        if 'comparison' in results and 'overall_improvement' in results['comparison']:
            avg_improvement = results['comparison']['overall_improvement']['average_improvement_percent']
            if avg_improvement >= 50:
                print(f"\n🎉 SUCCESS: Achieved {avg_improvement:.1f}% average improvement (target: 50%)")
            else:
                print(f"\n⚠️  WARNING: Only {avg_improvement:.1f}% average improvement (target: 50%)")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()