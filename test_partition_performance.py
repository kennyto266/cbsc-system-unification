#!/usr/bin/env python3
"""
分区性能验证测试
Partition Performance Validation Test

测试分区表的查询性能改进
"""

import asyncio
import time
import sys
import os
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('performance_test')

class PartitionPerformanceTester:
    """分区性能测试器"""

    def __init__(self, db_url: str):
        """初始化测试器"""
        self.db_url = db_url
        self.test_results = []

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def generate_test_data(self, table_name: str, record_count: int) -> bool:
        """生成测试数据"""
        logger.info(f"为表 {table_name} 生成 {record_count:,} 条测试数据...")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                batch_size = 1000
                for i in range(0, record_count, batch_size):
                    batch_end = min(i + batch_size, record_count)
                    batch = []

                    for j in range(i, batch_end):
                        if table_name == 'strategy_signals':
                            # 生成策略信号测试数据
                            base_time = datetime.now() - timedelta(days=365)
                            signal_time = base_time + timedelta(seconds=j * 60)

                            batch.append((
                                f"signal_{j:010d}",
                                f"strategy_{j % 100:03d}",
                                ['direct_rsi', 'dual_rsi', 'composite'][j % 3],
                                ['BUY', 'SELL', 'HOLD'][j % 3],
                                round(j % 100 / 100, 2),
                                round(j % 100 / 100, 2),
                                f"{700 + (j % 1000):04d}.HK",
                                signal_time,
                                None,
                                None,
                                None,
                                signal_time
                            ))
                        elif table_name == 'stock_data':
                            # 生成股票数据测试数据
                            base_time = datetime.now() - timedelta(days=365)
                            data_time = base_time + timedelta(seconds=j * 60)

                            batch.append((
                                j + 1,
                                f"{700 + (j % 1000):04d}.HK",
                                data_time,
                                round(100 + (j % 50), 2),
                                round(100 + (j % 50) + (j % 10), 2),
                                round(100 + (j % 50) - (j % 10), 2),
                                round(100 + (j % 50) + (j % 5), 2),
                                1000000 + (j % 1000000),
                                'test_source',
                                data_time
                            ))

                    # 批量插入
                    if table_name == 'strategy_signals':
                        insert_query = """
                            INSERT INTO strategy_signals (
                                signal_id, strategy_id, strategy_type, signal_type,
                                strength, confidence, symbol, timestamp,
                                market_data, parameters, metadata, created_at
                            ) VALUES %s
                        """
                    elif table_name == 'stock_data':
                        insert_query = """
                            INSERT INTO stock_data (
                                id, symbol, timestamp, open_price, high_price,
                                low_price, close_price, volume, source, created_at
                            ) VALUES %s
                        """

                    from psycopg2.extras import execute_values
                    execute_values(cursor, insert_query, batch)
                    conn.commit()

                    if (i // batch_size + 1) % 10 == 0:
                        logger.info(f"已生成 {batch_end:,} 条数据")

                logger.info(f"✅ 成功生成 {record_count:,} 条测试数据")
                return True

        except Exception as e:
            logger.error(f"生成测试数据失败: {e}")
            return False

    def test_query_performance(self, query_name: str, query: str, iterations: int = 5) -> Dict[str, Any]:
        """测试查询性能"""
        logger.info(f"测试查询: {query_name}")

        times = []

        for i in range(iterations):
            start_time = time.time()

            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    result = cursor.fetchall()

                elapsed_time = time.time() - start_time
                times.append(elapsed_time)

                logger.info(f"  第 {i+1} 次执行: {elapsed_time:.3f}s, 返回 {len(result)} 行")

            except Exception as e:
                logger.error(f"查询执行失败: {e}")
                return {
                    'query_name': query_name,
                    'success': False,
                    'error': str(e),
                    'iterations': i + 1
                }

        # 计算统计信息
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        result = {
            'query_name': query_name,
            'success': True,
            'iterations': iterations,
            'avg_time': avg_time,
            'median_time': median_time,
            'min_time': min_time,
            'max_time': max_time,
            'std_dev': std_dev,
            'times': times
        }

        logger.info(f"  平均时间: {avg_time:.3f}s, 中位数: {median_time:.3f}s")
        return result

    def run_performance_tests(self) -> List[Dict[str, Any]]:
        """运行性能测试套件"""
        logger.info("开始运行性能测试...")

        tests = [
            # 策略信号查询测试
            (
                "策略信号 - 最近7天",
                """
                SELECT strategy_id, COUNT(*) as signal_count
                FROM strategy_signals
                WHERE timestamp > NOW() - INTERVAL '7 days'
                GROUP BY strategy_id
                ORDER BY signal_count DESC
                """
            ),
            (
                "策略信号 - 特定策略所有历史",
                """
                SELECT signal_type, COUNT(*) as count
                FROM strategy_signals
                WHERE strategy_id = 'strategy_001'
                GROUP BY signal_type
                """
            ),
            (
                "策略信号 - 按日期范围",
                """
                SELECT DATE_TRUNC('day', timestamp) as day, COUNT(*) as daily_count
                FROM strategy_signals
                WHERE timestamp BETWEEN '2024-01-01' AND '2024-01-31'
                GROUP BY DATE_TRUNC('day', timestamp)
                ORDER BY day
                """
            ),

            # 股票数据查询测试
            (
                "股票数据 - 特定股票最近数据",
                """
                SELECT timestamp, close_price, volume
                FROM stock_data
                WHERE symbol = '0700.HK'
                AND timestamp > NOW() - INTERVAL '30 days'
                ORDER BY timestamp DESC
                """
            ),
            (
                "股票数据 - 日线聚合",
                """
                SELECT symbol, DATE_TRUNC('day', timestamp) as day,
                       MIN(close_price) as day_low,
                       MAX(close_price) as day_high,
                       LAST_VALUE(close_price) OVER (PARTITION BY symbol, DATE_TRUNC('day', timestamp) ORDER BY timestamp DESC) as day_close
                FROM stock_data
                WHERE timestamp > NOW() - INTERVAL '30 days'
                GROUP BY symbol, DATE_TRUNC('day', timestamp), timestamp, close_price
                ORDER BY day DESC
                """
            ),

            # 复杂聚合查询测试
            (
                "聚合视图 - 策略信号日统计",
                """
                SELECT * FROM v_strategy_signals_daily
                WHERE signal_date > NOW() - INTERVAL '7 days'
                ORDER BY signal_date DESC, total_signals DESC
                LIMIT 100
                """
            ),
            (
                "聚合视图 - 股票数据统计",
                """
                SELECT * FROM v_stock_data_stats
                ORDER BY total_records DESC
                LIMIT 50
                """
            )
        ]

        results = []

        for query_name, query in tests:
            result = self.test_query_performance(query_name, query, iterations=3)
            results.append(result)
            self.test_results.append(result)

        return results

    def test_partition_pruning(self) -> Dict[str, Any]:
        """测试分区裁剪效果"""
        logger.info("测试分区裁剪效果...")

        # 测试不同时间范围的查询
        queries = [
            ("1天数据", "WHERE timestamp > NOW() - INTERVAL '1 day'"),
            ("7天数据", "WHERE timestamp > NOW() - INTERVAL '7 days'"),
            ("30天数据", "WHERE timestamp > NOW() - INTERVAL '30 days'"),
            ("90天数据", "WHERE timestamp > NOW() - INTERVAL '90 days'"),
            ("1年数据", "WHERE timestamp > NOW() - INTERVAL '1 year'")
        ]

        results = {}

        for desc, where_clause in queries:
            query = f"""
                EXPLAIN (ANALYZE, BUFFERS)
                SELECT COUNT(*) FROM strategy_signals {where_clause}
            """

            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    explain_result = cursor.fetchall()

                # 解析执行计划以检查分区裁剪
                plan_text = '\n'.join([str(row[0]) for row in explain_result])
                partitions_scanned = plan_text.count('Partition')

                results[desc] = {
                    'partitions_scanned': partitions_scanned,
                    'plan_text': plan_text,
                    'query_time': self._extract_execution_time(plan_text)
                }

                logger.info(f"  {desc}: 扫描 {partitions_scanned} 个分区")

            except Exception as e:
                logger.error(f"测试分区裁剪失败 ({desc}): {e}")
                results[desc] = {'error': str(e)}

        return results

    def _extract_execution_time(self, plan_text: str) -> float:
        """从执行计划中提取执行时间"""
        import re
        match = re.search(r'Execution Time: ([\d.]+) ms', plan_text)
        if match:
            return float(match.group(1))
        return 0.0

    def test_data_loading_performance(self, record_count: int = 10000) -> Dict[str, Any]:
        """测试数据加载性能"""
        logger.info(f"测试数据加载性能 ({record_count:,} 条记录)...")

        results = {}

        # 测试批量插入性能
        start_time = time.time()
        success = self.generate_test_data('strategy_signals', record_count)
        insert_time = time.time() - start_time

        if success:
            results['insert'] = {
                'record_count': record_count,
                'time_seconds': insert_time,
                'records_per_second': record_count / insert_time
            }
            logger.info(f"  插入性能: {record_count/insert_time:.0f} 记录/秒")
        else:
            results['insert'] = {'success': False}

        # 测试查询性能
        test_queries = [
            ("全表扫描", "SELECT COUNT(*) FROM strategy_signals"),
            ("索引查询", "SELECT COUNT(*) FROM strategy_signals WHERE strategy_id = 'strategy_001'"),
            ("时间范围查询", "SELECT COUNT(*) FROM strategy_signals WHERE timestamp > NOW() - INTERVAL '7 days'")
        ]

        results['queries'] = {}

        for query_name, query in test_queries:
            start_time = time.time()
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    result = cursor.fetchone()
                query_time = time.time() - start_time
                results['queries'][query_name] = {
                    'time_seconds': query_time,
                    'result_count': result[0] if result else 0
                }
                logger.info(f"  {query_name}: {query_time:.3f}s")
            except Exception as e:
                results['queries'][query_name] = {'error': str(e)}

        return results

    def generate_performance_report(self, results: List[Dict[str, Any]]) -> str:
        """生成性能报告"""
        report_lines = [
            "=" * 80,
            "分区性能测试报告",
            "=" * 80,
            f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "查询性能测试结果:",
            "-" * 40
        ]

        for result in results:
            if result['success']:
                report_lines.extend([
                    f"\n{result['query_name']}:",
                    f"  平均时间: {result['avg_time']:.3f}s",
                    f"  中位数时间: {result['median_time']:.3f}s",
                    f"  最小时间: {result['min_time']:.3f}s",
                    f"  最大时间: {result['max_time']:.3f}s",
                    f"  标准差: {result['std_dev']:.3f}s"
                ])
            else:
                report_lines.extend([
                    f"\n{result['query_name']}:",
                    f"  状态: 失败",
                    f"  错误: {result['error']}"
                ])

        # 性能要求检查
        report_lines.extend([
            "\n\n性能要求检查:",
            "-" * 40
        ])

        successful_results = [r for r in results if r['success']]
        if successful_results:
            avg_query_time = statistics.mean([r['avg_time'] for r in successful_results])
            if avg_query_time < 0.5:
                report_lines.append("✅ 平均查询时间 < 0.5s")
            else:
                report_lines.append(f"❌ 平均查询时间 >= 0.5s (实际: {avg_query_time:.3f}s)")

        # 添加分区裁剪测试结果
        partition_results = self.test_partition_pruning()
        if partition_results:
            report_lines.extend([
                "\n\n分区裁剪效果:",
                "-" * 40
            ])
            for desc, result in partition_results.items():
                if 'error' not in result:
                    report_lines.append(f"{desc}: 扫描 {result['partitions_scanned']} 个分区")
                else:
                    report_lines.append(f"{desc}: 测试失败")

        report_lines.extend([
            "\n\n" + "=" * 80,
            "报告结束",
            "=" * 80
        ])

        return '\n'.join(report_lines)

async def main():
    """主测试函数"""
    import argparse

    parser = argparse.ArgumentParser(description='分区性能验证测试')
    parser.add_argument('--db-url', help='数据库URL (默认使用环境变量 DATABASE_URL)')
    parser.add_argument('--test-data-count', type=int, default=10000, help='测试数据数量')
    parser.add_argument('--report-file', help='性能报告文件路径')
    parser.add_argument('--skip-data-gen', action='store_true', help='跳过测试数据生成')

    args = parser.parse_args()

    db_url = args.db_url or os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/quant_system')

    try:
        logger.info("开始分区性能验证测试")

        # 创建测试器
        tester = PartitionPerformanceTester(db_url)

        # 生成测试数据
        if not args.skip_data_gen:
            logger.info(f"生成 {args.test_data_count:,} 条测试数据...")
            if not tester.generate_test_data('strategy_signals', args.test_data_count):
                logger.error("生成测试数据失败")
                sys.exit(1)

        # 运行性能测试
        results = tester.run_performance_tests()

        # 生成报告
        report = tester.generate_performance_report(results)

        # 输出报告
        print(report)

        # 保存报告到文件
        if args.report_file:
            with open(args.report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"性能报告已保存到: {args.report_file}")

        # 检查是否满足性能要求
        successful_results = [r for r in results if r['success']]
        if successful_results:
            avg_time = statistics.mean([r['avg_time'] for r in successful_results])
            if avg_time < 0.5:
                logger.info("✅ 性能验证通过: 平均查询时间 < 0.5s")
            else:
                logger.warning(f"⚠️ 性能警告: 平均查询时间 {avg_time:.3f}s >= 0.5s")

        logger.info("性能验证测试完成")

    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())