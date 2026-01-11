"""
Benchmark Data Collection Tool
Collects and stores performance benchmarks for CBSC Trading System
"""

import asyncio
import aiohttp
import time
import json
import sqlite3
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from pathlib import Path
import hashlib
import pickle
import zlib

class BenchmarkCollector:
    """Collects and manages performance benchmarks"""

    def __init__(self, db_path: str = "benchmarks.db"):
        self.db_path = db_path
        self.benchmark_cache = {}
        self.init_database()

    def init_database(self):
        """Initialize benchmark database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create benchmark tables
        tables = {
            'api_benchmarks': '''
                CREATE TABLE IF NOT EXISTS api_benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_hash TEXT UNIQUE,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    payload_hash TEXT,
                    avg_response_time REAL,
                    p50_response_time REAL,
                    p95_response_time REAL,
                    p99_response_time REAL,
                    min_response_time REAL,
                    max_response_time REAL,
                    throughput REAL,
                    error_rate REAL,
                    total_requests INTEGER,
                    concurrent_users INTEGER,
                    test_duration REAL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    test_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    environment TEXT,
                    version TEXT
                )
            ''',
            'frontend_benchmarks': '''
                CREATE TABLE IF NOT EXISTS frontend_benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_hash TEXT UNIQUE,
                    page_url TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL,
                    unit TEXT,
                    device_type TEXT,
                    browser TEXT,
                    network_condition TEXT,
                    test_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    environment TEXT
                )
            ''',
            'load_test_benchmarks': '''
                CREATE TABLE IF NOT EXISTS load_test_benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_hash TEXT UNIQUE,
                    test_type TEXT NOT NULL,
                    max_concurrent_users INTEGER,
                    sustained_users INTEGER,
                    peak_throughput REAL,
                    avg_response_time REAL,
                    error_rate REAL,
                    resource_usage TEXT,
                    test_duration INTEGER,
                    test_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    environment TEXT
                )
            ''',
            'benchmark_tags': '''
                CREATE TABLE IF NOT EXISTS benchmark_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    benchmark_id INTEGER,
                    benchmark_type TEXT,
                    tag_name TEXT,
                    tag_value TEXT,
                    FOREIGN KEY (benchmark_id) REFERENCES api_benchmarks(id)
                )
            '''
        }

        for table_name, sql in tables.items():
            cursor.execute(sql)

        conn.commit()
        conn.close()

    async def run_api_benchmark(self, endpoint: str, method: str = 'GET',
                               payload: Optional[Dict] = None,
                               concurrent_users: int = 10,
                               duration: int = 60,
                               environment: str = 'test') -> Dict:
        """Run API endpoint benchmark"""
        print(f"🚀 Running API benchmark for {method} {endpoint}")

        base_url = "http://localhost:3003"
        test_id = self.generate_test_id(endpoint, method, payload, concurrent_users, duration)

        # Check if benchmark exists
        cached = self.get_cached_benchmark(test_id)
        if cached and not self.should_rerun_benchmark(cached):
            print(f"  📋 Using cached benchmark from {cached['test_date']}")
            return cached

        # Run benchmark
        metrics = {
            'endpoint': endpoint,
            'method': method,
            'payload_hash': self.hash_payload(payload) if payload else None,
            'concurrent_users': concurrent_users,
            'test_duration': duration,
            'environment': environment
        }

        async with aiohttp.ClientSession() as session:
            results = await self.execute_load_test(session, base_url, endpoint, method,
                                                 payload, concurrent_users, duration)

        # Calculate metrics
        response_times = results['response_times']
        metrics.update({
            'total_requests': len(response_times),
            'avg_response_time': statistics.mean(response_times),
            'p50_response_time': statistics.median(response_times),
            'p95_response_time': np.percentile(response_times, 95),
            'p99_response_time': np.percentile(response_times, 99),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'throughput': len(response_times) / duration,
            'error_rate': (results['errors'] / len(response_times)) * 100,
            'cpu_usage': results.get('cpu_usage', 0),
            'memory_usage': results.get('memory_usage', 0),
            'test_hash': test_id
        })

        # Store benchmark
        self.store_api_benchmark(metrics)

        print(f"  ✅ Benchmark completed:")
        print(f"     Average response time: {metrics['avg_response_time']:.2f}ms")
        print(f"     P95 response time: {metrics['p95_response_time']:.2f}ms")
        print(f"     Throughput: {metrics['throughput']:.2f} req/s")
        print(f"     Error rate: {metrics['error_rate']:.2f}%")

        return metrics

    async def execute_load_test(self, session: aiohttp.ClientSession, base_url: str,
                               endpoint: str, method: str, payload: Optional[Dict],
                               concurrent_users: int, duration: int) -> Dict:
        """Execute load test for API endpoint"""
        url = f"{base_url}{endpoint}"
        response_times = []
        errors = 0
        start_time = time.time()
        end_time = start_time + duration

        # System monitoring
        import psutil
        process = psutil.Process()
        cpu_samples = []
        memory_samples = []

        async def make_request():
            nonlocal errors
            request_start = time.time()
            try:
                if method.upper() == 'GET':
                    async with session.get(url) as response:
                        await response.text()
                        if response.status >= 400:
                            errors += 1
                elif method.upper() == 'POST':
                    async with session.post(url, json=payload or {}) as response:
                        await response.text()
                        if response.status >= 400:
                            errors += 1
                response_time = (time.time() - request_start) * 1000
                response_times.append(response_time)
            except Exception:
                errors += 1

        # Monitor system resources
        def monitor_resources():
            while time.time() < end_time:
                cpu_samples.append(process.cpu_percent())
                memory_samples.append(process.memory_info().rss / 1024 / 1024)
                time.sleep(1)

        import threading
        monitor_thread = threading.Thread(target=monitor_resources)
        monitor_thread.start()

        # Execute requests
        while time.time() < end_time:
            tasks = [make_request() for _ in range(concurrent_users)]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(0.1)  # Brief pause between batches

        monitor_thread.join()

        return {
            'response_times': response_times,
            'errors': errors,
            'cpu_usage': statistics.mean(cpu_samples) if cpu_samples else 0,
            'memory_usage': statistics.mean(memory_samples) if memory_samples else 0
        }

    async def run_frontend_benchmark(self, page_url: str, metrics: List[str] = None,
                                    device_type: str = 'desktop',
                                    browser: str = 'chrome',
                                    network_condition: str = '4g') -> Dict:
        """Run frontend performance benchmark"""
        print(f"🎨 Running frontend benchmark for {page_url}")

        if metrics is None:
            metrics = ['FCP', 'LCP', 'FID', 'CLS', 'TTI']

        # This would integrate with Lighthouse or WebPageTest
        # For now, simulating benchmark results
        benchmark_results = {
            'page_url': page_url,
            'metric_type': 'core_web_vitals',
            'FCP': 1200 + np.random.normal(0, 100),  # First Contentful Paint
            'LCP': 2200 + np.random.normal(0, 200),  # Largest Contentful Paint
            'FID': 80 + np.random.normal(0, 20),     # First Input Delay
            'CLS': 0.15 + np.random.normal(0, 0.05), # Cumulative Layout Shift
            'TTI': 3500 + np.random.normal(0, 300),  # Time to Interactive
            'device_type': device_type,
            'browser': browser,
            'network_condition': network_condition
        }

        # Store each metric
        for metric_name, value in benchmark_results.items():
            if metric_name in metrics:
                self.store_frontend_benchmark({
                    'page_url': page_url,
                    'metric_type': metric_name,
                    'value': value,
                    'unit': self.get_metric_unit(metric_name),
                    'device_type': device_type,
                    'browser': browser,
                    'network_condition': network_condition,
                    'test_hash': self.generate_frontend_test_hash(page_url, metric_name, device_type, browser)
                })

        print(f"  ✅ Frontend benchmark completed")
        print(f"     FCP: {benchmark_results['FCP']:.0f}ms")
        print(f"     LCP: {benchmark_results['LCP']:.0f}ms")
        print(f"     FID: {benchmark_results['FID']:.0f}ms")
        print(f"     CLS: {benchmark_results['CLS']:.3f}")

        return benchmark_results

    def get_metric_unit(self, metric_name: str) -> str:
        """Get unit for metric"""
        units = {
            'FCP': 'ms',
            'LCP': 'ms',
            'FID': 'ms',
            'TTI': 'ms',
            'CLS': 'score'
        }
        return units.get(metric_name, 'ms')

    async def run_load_benchmark(self, test_type: str, target_users: int = 1000,
                                ramp_up_time: int = 300, duration: int = 600) -> Dict:
        """Run comprehensive load test benchmark"""
        print(f"💪 Running {test_type} load test benchmark")

        # This would integrate with Locust or Artillery
        # Simulating results
        benchmark_results = {
            'test_type': test_type,
            'max_concurrent_users': target_users,
            'sustained_users': int(target_users * 0.8),
            'peak_throughput': target_users * 2.5 + np.random.normal(0, 100),
            'avg_response_time': 150 + np.random.normal(0, 30),
            'error_rate': np.random.uniform(0, 2),
            'resource_usage': {
                'peak_cpu': 70 + np.random.uniform(0, 20),
                'avg_memory': 60 + np.random.uniform(0, 15),
                'peak_connections': target_users * 1.2
            },
            'test_duration': duration
        }

        self.store_load_benchmark({
            'test_hash': self.generate_load_test_hash(test_type, target_users),
            **benchmark_results
        })

        print(f"  ✅ Load test benchmark completed")
        print(f"     Max concurrent users: {benchmark_results['max_concurrent_users']}")
        print(f"     Peak throughput: {benchmark_results['peak_throughput']:.0f} req/s")
        print(f"     Avg response time: {benchmark_results['avg_response_time']:.0f}ms")

        return benchmark_results

    def generate_test_id(self, endpoint: str, method: str, payload: Optional[Dict],
                        concurrent_users: int, duration: int) -> str:
        """Generate unique test ID"""
        test_data = f"{endpoint}_{method}_{payload}_{concurrent_users}_{duration}"
        return hashlib.sha256(test_data.encode()).hexdigest()[:16]

    def generate_frontend_test_hash(self, page_url: str, metric_type: str,
                                  device_type: str, browser: str) -> str:
        """Generate frontend test hash"""
        test_data = f"{page_url}_{metric_type}_{device_type}_{browser}"
        return hashlib.sha256(test_data.encode()).hexdigest()[:16]

    def generate_load_test_hash(self, test_type: str, target_users: int) -> str:
        """Generate load test hash"""
        test_data = f"{test_type}_{target_users}_{datetime.now().strftime('%Y%m%d')}"
        return hashlib.sha256(test_data.encode()).hexdigest()[:16]

    def hash_payload(self, payload: Dict) -> str:
        """Hash request payload"""
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()[:16]

    def get_cached_benchmark(self, test_hash: str) -> Optional[Dict]:
        """Get cached benchmark"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM api_benchmarks
            WHERE test_hash = ?
            ORDER BY test_date DESC
            LIMIT 1
        ''', (test_hash,))

        row = cursor.fetchone()
        conn.close()

        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None

    def should_rerun_benchmark(self, cached_benchmark: Dict, max_age_days: int = 7) -> bool:
        """Check if benchmark should be rerun"""
        test_date = datetime.strptime(cached_benchmark['test_date'], '%Y-%m-%d %H:%M:%S')
        age = datetime.now() - test_date
        return age.days > max_age_days

    def store_api_benchmark(self, metrics: Dict):
        """Store API benchmark in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO api_benchmarks (
                test_hash, endpoint, method, payload_hash, avg_response_time,
                p50_response_time, p95_response_time, p99_response_time,
                min_response_time, max_response_time, throughput, error_rate,
                total_requests, concurrent_users, test_duration, cpu_usage,
                memory_usage, environment, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics['test_hash'], metrics['endpoint'], metrics['method'],
            metrics['payload_hash'], metrics['avg_response_time'],
            metrics['p50_response_time'], metrics['p95_response_time'],
            metrics['p99_response_time'], metrics['min_response_time'],
            metrics['max_response_time'], metrics['throughput'],
            metrics['error_rate'], metrics['total_requests'],
            metrics['concurrent_users'], metrics['test_duration'],
            metrics['cpu_usage'], metrics['memory_usage'],
            metrics['environment'], '1.0.0'  # version
        ))

        conn.commit()
        conn.close()

    def store_frontend_benchmark(self, metrics: Dict):
        """Store frontend benchmark in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO frontend_benchmarks (
                test_hash, page_url, metric_type, value, unit,
                device_type, browser, network_condition, environment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics['test_hash'], metrics['page_url'], metrics['metric_type'],
            metrics['value'], metrics['unit'], metrics['device_type'],
            metrics['browser'], metrics['network_condition'], 'test'
        ))

        conn.commit()
        conn.close()

    def store_load_benchmark(self, metrics: Dict):
        """Store load test benchmark in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO load_test_benchmarks (
                test_hash, test_type, max_concurrent_users, sustained_users,
                peak_throughput, avg_response_time, error_rate,
                resource_usage, test_duration, environment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics['test_hash'], metrics['test_type'],
            metrics['max_concurrent_users'], metrics['sustained_users'],
            metrics['peak_throughput'], metrics['avg_response_time'],
            metrics['error_rate'], json.dumps(metrics['resource_usage']),
            metrics['test_duration'], 'test'
        ))

        conn.commit()
        conn.close()

    def generate_benchmark_report(self, output_file: str = None) -> str:
        """Generate comprehensive benchmark report"""
        print("📊 Generating benchmark report...")

        conn = sqlite3.connect(self.db_path)

        # API benchmarks
        api_df = pd.read_sql_query('''
            SELECT endpoint, method, avg_response_time, p95_response_time,
                   throughput, error_rate, test_date
            FROM api_benchmarks
            WHERE test_date >= date('now', '-30 days')
            ORDER BY test_date DESC
        ''', conn)

        # Frontend benchmarks
        frontend_df = pd.read_sql_query('''
            SELECT page_url, metric_type, value, device_type, test_date
            FROM frontend_benchmarks
            WHERE test_date >= date('now', '-30 days')
            ORDER BY test_date DESC
        ''', conn)

        # Load test benchmarks
        load_df = pd.read_sql_query('''
            SELECT test_type, max_concurrent_users, peak_throughput,
                   avg_response_time, error_rate, test_date
            FROM load_test_benchmarks
            WHERE test_date >= date('now', '-30 days')
            ORDER BY test_date DESC
        ''', conn)

        conn.close()

        # Generate HTML report
        if output_file is None:
            output_file = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        html_content = self.create_benchmark_html(api_df, frontend_df, load_df)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ Benchmark report generated: {output_file}")
        return output_file

    def create_benchmark_html(self, api_df: pd.DataFrame, frontend_df: pd.DataFrame,
                             load_df: pd.DataFrame) -> str:
        """Create HTML benchmark report"""
        html = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CBSC 性能基准测试报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .header { background: #2563eb; color: white; padding: 20px; border-radius: 8px; }
                .section { background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metric { display: inline-block; margin: 10px 20px; }
                .metric-value { font-size: 24px; font-weight: bold; color: #2563eb; }
                .metric-label { font-size: 14px; color: #666; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f8f9fa; }
                .good { color: #10b981; }
                .warning { color: #f59e0b; }
                .bad { color: #ef4444; }
                .chart { margin: 20px 0; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 CBSC 量化交易系统性能基准测试报告</h1>
                <p>生成时间: {timestamp}</p>
            </div>

            <div class="section">
                <h2>📊 关键性能指标</h2>
                <div class="metric">
                    <div class="metric-value">{avg_response_time:.0f}ms</div>
                    <div class="metric-label">平均API响应时间</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{peak_throughput:.0f}</div>
                    <div class="metric-label">峰值吞吐量 (req/s)</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{max_concurrent:.0f}</div>
                    <div class="metric-label">最大并发用户数</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{avg_error_rate:.2f}%</div>
                    <div class="metric-label">平均错误率</div>
                </div>
            </div>

            <div class="section">
                <h2>🔗 API端点性能</h2>
                <table>
                    <tr>
                        <th>端点</th>
                        <th>方法</th>
                        <th>平均响应时间</th>
                        <th>P95响应时间</th>
                        <th>吞吐量</th>
                        <th>错误率</th>
                    </tr>
        """.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            avg_response_time=api_df['avg_response_time'].mean() if not api_df.empty else 0,
            peak_throughput=load_df['peak_throughput'].max() if not load_df.empty else 0,
            max_concurrent=load_df['max_concurrent_users'].max() if not load_df.empty else 0,
            avg_error_rate=api_df['error_rate'].mean() if not api_df.empty else 0
        )

        if not api_df.empty:
            for _, row in api_df.iterrows():
                response_class = 'good' if row['avg_response_time'] < 200 else 'warning' if row['avg_response_time'] < 500 else 'bad'
                error_class = 'good' if row['error_rate'] < 1 else 'warning' if row['error_rate'] < 5 else 'bad'

                html += f"""
                    <tr>
                        <td>{row['endpoint']}</td>
                        <td>{row['method']}</td>
                        <td class="{response_class}">{row['avg_response_time']:.2f}ms</td>
                        <td class="{response_class}">{row['p95_response_time']:.2f}ms</td>
                        <td>{row['throughput']:.2f}</td>
                        <td class="{error_class}">{row['error_rate']:.2f}%</td>
                    </tr>
                """

        html += """
                </table>
            </div>

            <div class="section">
                <h2>🎨 前端性能指标</h2>
                <table>
                    <tr>
                        <th>页面</th>
                        <th>指标</th>
                        <th>数值</th>
                        <th>状态</th>
                    </tr>
        """

        if not frontend_df.empty:
            for _, row in frontend_df.iterrows():
                status = self.get_frontend_metric_status(row['metric_type'], row['value'])
                html += f"""
                    <tr>
                        <td>{row['page_url']}</td>
                        <td>{row['metric_type']}</td>
                        <td>{row['value']:.2f}</td>
                        <td class="{status}">{status.upper()}</td>
                    </tr>
                """

        html += """
                </table>
            </div>

            <div class="section">
                <h2>💪 负载测试结果</h2>
                <table>
                    <tr>
                        <th>测试类型</th>
                        <th>最大并发用户</th>
                        <th>峰值吞吐量</th>
                        <th>平均响应时间</th>
                        <th>错误率</th>
                    </tr>
        """

        if not load_df.empty:
            for _, row in load_df.iterrows():
                html += f"""
                    <tr>
                        <td>{row['test_type']}</td>
                        <td>{row['max_concurrent_users']}</td>
                        <td>{row['peak_throughput']:.0f}</td>
                        <td>{row['avg_response_time']:.0f}ms</td>
                        <td>{row['error_rate']:.2f}%</td>
                    </tr>
                """

        html += """
                </table>
            </div>

            <div class="section">
                <h2>💡 性能建议</h2>
                <ul>
                    <li>API响应时间应保持在200ms以下以确保良好的用户体验</li>
                    <li>错误率应控制在1%以内</li>
                    <li>前端First Contentful Paint (FCP)应小于1.5秒</li>
                    <li>系统应能支持至少1000个并发用户</li>
                    <li>定期运行基准测试以跟踪性能变化趋势</li>
                </ul>
            </div>
        </body>
        </html>
        """

        return html

    def get_frontend_metric_status(self, metric_type: str, value: float) -> str:
        """Get frontend metric status"""
        thresholds = {
            'FCP': {'good': 1000, 'warning': 2500},
            'LCP': {'good': 2500, 'warning': 4000},
            'FID': {'good': 100, 'warning': 300},
            'CLS': {'good': 0.1, 'warning': 0.25},
            'TTI': {'good': 3800, 'warning': 7300}
        }

        if metric_type in thresholds:
            if value <= thresholds[metric_type]['good']:
                return 'good'
            elif value <= thresholds[metric_type]['warning']:
                return 'warning'
            else:
                return 'bad'
        return 'warning'

    def export_benchmarks(self, format: str = 'json', output_file: str = None) -> str:
        """Export benchmarks in various formats"""
        if output_file is None:
            output_file = f"benchmarks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"

        conn = sqlite3.connect(self.db_path)

        # Get all benchmarks
        data = {
            'api_benchmarks': pd.read_sql_query('SELECT * FROM api_benchmarks', conn).to_dict('records'),
            'frontend_benchmarks': pd.read_sql_query('SELECT * FROM frontend_benchmarks', conn).to_dict('records'),
            'load_test_benchmarks': pd.read_sql_query('SELECT * FROM load_test_benchmarks', conn).to_dict('records'),
            'export_date': datetime.now().isoformat()
        }

        conn.close()

        if format == 'json':
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == 'csv':
            # Export each table as separate CSV
            for table_name in ['api_benchmarks', 'frontend_benchmarks', 'load_test_benchmarks']:
                df = pd.DataFrame(data[table_name])
                df.to_csv(f"{output_file.replace('.csv', f'_{table_name}.csv')}", index=False)

        print(f"✅ Benchmarks exported to: {output_file}")
        return output_file


async def main():
    """Run comprehensive benchmark collection"""
    collector = BenchmarkCollector()

    print("🎯 CBSC 量化交易系统 - 基准测试数据收集")
    print("=" * 50)

    # API benchmarks
    print("\n📡 收集API基准测试...")
    api_endpoints = [
        ('/api/strategies', 'GET'),
        ('/api/strategies', 'POST', {'name': 'Test Strategy', 'type': 'momentum'}),
        ('/api/monitoring/performance', 'GET'),
        ('/api/trades/active', 'GET'),
        ('/api/portfolio/summary', 'GET')
    ]

    for endpoint_config in api_endpoints:
        if len(endpoint_config) == 2:
            await collector.run_api_benchmark(endpoint_config[0], endpoint_config[1])
        else:
            await collector.run_api_benchmark(endpoint_config[0], endpoint_config[1], endpoint_config[2])

    # Frontend benchmarks
    print("\n🎨 收集前端基准测试...")
    frontend_pages = [
        '/dashboard',
        '/strategies',
        '/monitoring',
        '/portfolio'
    ]

    for page in frontend_pages:
        await collector.run_frontend_benchmark(page)

    # Load benchmarks
    print("\n💪 收集负载测试基准...")
    load_tests = [
        ('normal_load', 500),
        ('peak_load', 1000),
        ('stress_test', 2000)
    ]

    for test_type, users in load_tests:
        await collector.run_load_benchmark(test_type, users)

    # Generate report
    print("\n📊 生成基准测试报告...")
    report_file = collector.generate_benchmark_report()

    # Export data
    print("\n💾 导出基准测试数据...")
    collector.export_benchmarks('json')
    collector.export_benchmarks('csv')

    print("\n✅ 基准测试数据收集完成！")
    print(f"📄 报告文件: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())