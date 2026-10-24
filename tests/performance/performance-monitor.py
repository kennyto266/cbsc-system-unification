"""
Performance Monitoring System
Real-time performance monitoring and reporting for CBSC Trading System
"""

import asyncio
import aiohttp
import time
import json
import psutil
import threading
import queue
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configure matplotlib for server use
plt.switch_backend('Agg')

class PerformanceMonitor:
    """Real-time performance monitoring system"""

    def __init__(self, config_path: str = None):
        self.config = self.load_config(config_path)
        self.db_path = self.config.get('database_path', 'performance_data.db')
        self.metrics_queue = queue.Queue()
        self.alert_thresholds = self.config.get('alert_thresholds', {})
        self.monitoring_active = False
        self.alert_handlers = []

        # Initialize database
        self.init_database()

        # Register default alert handlers
        self.register_alert_handler(self.log_alert)
        self.register_alert_handler(self.email_alert)

    def load_config(self, config_path: Optional[str]) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            'database_path': 'performance_data.db',
            'monitoring_interval': 5,  # seconds
            'retention_days': 30,
            'alert_thresholds': {
                'response_time_ms': 200,
                'error_rate_percent': 5,
                'cpu_usage_percent': 80,
                'memory_usage_percent': 85,
                'disk_usage_percent': 90,
                'concurrent_users': 500
            },
            'api_endpoints': [
                '/api/strategies',
                '/api/monitoring/performance',
                '/api/trades/active',
                '/api/portfolio/summary'
            ],
            'email_alerts': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'recipients': []
            }
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    custom_config = json.load(f)
                default_config.update(custom_config)
            except Exception as e:
                print(f"⚠️ Could not load config file: {e}")

        return default_config

    def init_database(self):
        """Initialize SQLite database for metrics storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables
        tables = {
            'api_metrics': '''
                CREATE TABLE IF NOT EXISTS api_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    response_time_ms REAL,
                    status_code INTEGER,
                    success BOOLEAN,
                    error_message TEXT
                )
            ''',
            'system_metrics': '''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_mb REAL,
                    disk_percent REAL,
                    disk_used_gb REAL,
                    network_sent_mb REAL,
                    network_recv_mb REAL,
                    active_connections INTEGER
                )
            ''',
            'alerts': '''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    metrics_data TEXT,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''',
            'daily_summary': '''
                CREATE TABLE IF NOT EXISTS daily_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE,
                    avg_response_time_ms REAL,
                    total_requests INTEGER,
                    error_rate_percent REAL,
                    peak_cpu_percent REAL,
                    peak_memory_percent REAL,
                    uptime_percentage REAL
                )
            '''
        }

        for table_name, sql in tables.items():
            cursor.execute(sql)

        conn.commit()
        conn.close()

    def register_alert_handler(self, handler_func):
        """Register a custom alert handler"""
        self.alert_handlers.append(handler_func)

    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_active:
            print("⚠️ Monitoring is already active")
            return

        print("🔍 Starting Performance Monitoring...")
        self.monitoring_active = True

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self.monitor_api_endpoints()),
            asyncio.create_task(self.monitor_system_metrics()),
            asyncio.create_task(self.process_metrics_queue()),
            asyncio.create_task(self.generate_daily_reports()),
            asyncio.create_task(self.cleanup_old_data())
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print("\n⚠️ Monitoring stopped")
        finally:
            self.monitoring_active = False

    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        print("\n⏹️ Stopping Performance Monitoring...")

    async def monitor_api_endpoints(self):
        """Monitor API endpoint performance"""
        async with aiohttp.ClientSession() as session:
            while self.monitoring_active:
                try:
                    for endpoint in self.config['api_endpoints']:
                        await self.check_endpoint(session, endpoint)

                    await asyncio.sleep(self.config['monitoring_interval'])

                except Exception as e:
                    print(f"❌ API monitoring error: {e}")
                    await asyncio.sleep(10)

    async def check_endpoint(self, session: aiohttp.ClientSession, endpoint: str):
        """Check individual API endpoint"""
        start_time = time.time()
        success = False
        status_code = 0
        error_message = None

        try:
            async with session.get(f"http://localhost:3003{endpoint}", timeout=10) as response:
                response_time_ms = (time.time() - start_time) * 1000
                status_code = response.status
                success = 200 <= response.status < 400

                if not success:
                    error_message = f"HTTP {response.status}"

                # Store metrics
                self.metrics_queue.put({
                    'type': 'api_metrics',
                    'data': {
                        'endpoint': endpoint,
                        'method': 'GET',
                        'response_time_ms': response_time_ms,
                        'status_code': status_code,
                        'success': success,
                        'error_message': error_message
                    }
                })

                # Check alerts
                if response_time_ms > self.alert_thresholds['response_time_ms']:
                    await self.trigger_alert(
                        'response_time',
                        'warning',
                        f"High response time detected: {response_time_ms:.2f}ms for {endpoint}",
                        {'endpoint': endpoint, 'response_time': response_time_ms}
                    )

        except asyncio.TimeoutError:
            response_time_ms = 10000  # Timeout threshold
            error_message = "Request timeout"
            self.metrics_queue.put({
                'type': 'api_metrics',
                'data': {
                    'endpoint': endpoint,
                    'method': 'GET',
                    'response_time_ms': response_time_ms,
                    'status_code': 0,
                    'success': False,
                    'error_message': error_message
                }
            })

            await self.trigger_alert(
                'timeout',
                'critical',
                f"API timeout for {endpoint}",
                {'endpoint': endpoint}
            )

        except Exception as e:
            error_message = str(e)
            self.metrics_queue.put({
                'type': 'api_metrics',
                'data': {
                    'endpoint': endpoint,
                    'method': 'GET',
                    'response_time_ms': (time.time() - start_time) * 1000,
                    'status_code': 0,
                    'success': False,
                    'error_message': error_message
                }
            })

    async def monitor_system_metrics(self):
        """Monitor system performance metrics"""
        while self.monitoring_active:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                connections = len(psutil.net_connections())

                metrics = {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_mb': memory.used / 1024 / 1024,
                    'disk_percent': disk.percent,
                    'disk_used_gb': disk.used / 1024 / 1024 / 1024,
                    'network_sent_mb': network.bytes_sent / 1024 / 1024,
                    'network_recv_mb': network.bytes_recv / 1024 / 1024,
                    'active_connections': connections
                }

                # Store metrics
                self.metrics_queue.put({
                    'type': 'system_metrics',
                    'data': metrics
                })

                # Check alerts
                if cpu_percent > self.alert_thresholds['cpu_usage_percent']:
                    await self.trigger_alert(
                        'cpu_usage',
                        'warning',
                        f"High CPU usage: {cpu_percent}%",
                        metrics
                    )

                if memory.percent > self.alert_thresholds['memory_usage_percent']:
                    await self.trigger_alert(
                        'memory_usage',
                        'warning',
                        f"High memory usage: {memory.percent}%",
                        metrics
                    )

                if disk.percent > self.alert_thresholds['disk_usage_percent']:
                    await self.trigger_alert(
                        'disk_usage',
                        'critical',
                        f"Low disk space: {disk.percent}% used",
                        metrics
                    )

                await asyncio.sleep(self.config['monitoring_interval'])

            except Exception as e:
                print(f"❌ System monitoring error: {e}")
                await asyncio.sleep(10)

    async def process_metrics_queue(self):
        """Process metrics from queue and store in database"""
        while self.monitoring_active:
            try:
                # Get batch of metrics
                metrics_batch = []
                while not self.metrics_queue.empty() and len(metrics_batch) < 100:
                    try:
                        metric = self.metrics_queue.get_nowait()
                        metrics_batch.append(metric)
                    except queue.Empty:
                        break

                # Store batch in database
                if metrics_batch:
                    await self.store_metrics_batch(metrics_batch)

                await asyncio.sleep(1)

            except Exception as e:
                print(f"❌ Metrics processing error: {e}")
                await asyncio.sleep(5)

    async def store_metrics_batch(self, metrics_batch: List[Dict]):
        """Store a batch of metrics in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for metric in metrics_batch:
                if metric['type'] == 'api_metrics':
                    cursor.execute('''
                        INSERT INTO api_metrics (endpoint, method, response_time_ms, status_code, success, error_message)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        metric['data']['endpoint'],
                        metric['data']['method'],
                        metric['data']['response_time_ms'],
                        metric['data']['status_code'],
                        metric['data']['success'],
                        metric['data']['error_message']
                    ))

                elif metric['type'] == 'system_metrics':
                    cursor.execute('''
                        INSERT INTO system_metrics (
                            cpu_percent, memory_percent, memory_used_mb, disk_percent,
                            disk_used_gb, network_sent_mb, network_recv_mb, active_connections
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        metric['data']['cpu_percent'],
                        metric['data']['memory_percent'],
                        metric['data']['memory_used_mb'],
                        metric['data']['disk_percent'],
                        metric['data']['disk_used_gb'],
                        metric['data']['network_sent_mb'],
                        metric['data']['network_recv_mb'],
                        metric['data']['active_connections']
                    ))

            conn.commit()

        except Exception as e:
            print(f"❌ Database storage error: {e}")
            conn.rollback()
        finally:
            conn.close()

    async def trigger_alert(self, alert_type: str, severity: str, message: str, metrics_data: Dict):
        """Trigger an alert"""
        alert = {
            'type': alert_type,
            'severity': severity,
            'message': message,
            'metrics': metrics_data,
            'timestamp': datetime.now().isoformat()
        }

        # Store alert in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO alerts (alert_type, severity, message, metrics_data)
            VALUES (?, ?, ?, ?)
        ''', (alert_type, severity, message, json.dumps(metrics_data)))
        conn.commit()
        conn.close()

        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                print(f"❌ Alert handler error: {e}")

    async def log_alert(self, alert: Dict):
        """Log alert to console"""
        severity_icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🚨'
        }
        icon = severity_icons.get(alert['severity'], '❗')
        print(f"{icon} [{alert['severity'].upper()}] {alert['message']}")

    async def email_alert(self, alert: Dict):
        """Send email alert (if configured)"""
        if not self.config['email_alerts']['enabled']:
            return

        # Implement email sending logic here
        # This is a placeholder for email implementation
        pass

    async def generate_daily_reports(self):
        """Generate daily performance reports"""
        while self.monitoring_active:
            try:
                # Wait until next day
                now = datetime.now()
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                sleep_seconds = (tomorrow - now).total_seconds()

                await asyncio.sleep(sleep_seconds)

                # Generate report for previous day
                await self.create_daily_summary(now.date())

            except Exception as e:
                print(f"❌ Daily report error: {e}")
                await asyncio.sleep(3600)  # Try again in an hour

    async def create_daily_summary(self, date):
        """Create daily performance summary"""
        conn = sqlite3.connect(self.db_path)

        try:
            # Get API metrics summary
            api_df = pd.read_sql_query('''
                SELECT
                    AVG(response_time_ms) as avg_response_time,
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
                FROM api_metrics
                WHERE DATE(timestamp) = ?
            ''', conn, params=[date])

            # Get system metrics summary
            system_df = pd.read_sql_query('''
                SELECT
                    MAX(cpu_percent) as peak_cpu,
                    MAX(memory_percent) as peak_memory
                FROM system_metrics
                WHERE DATE(timestamp) = ?
            ''', conn, params=[date])

            # Calculate uptime (assuming no major gaps in monitoring)
            monitoring_df = pd.read_sql_query('''
                SELECT COUNT(*) as data_points
                FROM system_metrics
                WHERE DATE(timestamp) = ?
            ''', conn, params=[date])

            expected_points = 24 * 60 * 60 // self.config['monitoring_interval']
            uptime_percentage = (monitoring_df['data_points'][0] / expected_points) * 100

            # Store daily summary
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO daily_summary (
                    date, avg_response_time_ms, total_requests, error_rate_percent,
                    peak_cpu_percent, peak_memory_percent, uptime_percentage
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                date,
                api_df['avg_response_time'][0] if not api_df.empty else 0,
                api_df['total_requests'][0] if not api_df.empty else 0,
                api_df['error_rate'][0] if not api_df.empty else 0,
                system_df['peak_cpu'][0] if not system_df.empty else 0,
                system_df['peak_memory'][0] if not system_df.empty else 0,
                uptime_percentage
            ))
            conn.commit()

            print(f"📊 Daily report generated for {date}")

        except Exception as e:
            print(f"❌ Daily summary error: {e}")
            conn.rollback()
        finally:
            conn.close()

    async def cleanup_old_data(self):
        """Clean up old data beyond retention period"""
        while self.monitoring_active:
            try:
                # Run cleanup daily
                await asyncio.sleep(24 * 60 * 60)

                cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Clean up old metrics
                cursor.execute('DELETE FROM api_metrics WHERE timestamp < ?', (cutoff_date,))
                cursor.execute('DELETE FROM system_metrics WHERE timestamp < ?', (cutoff_date))
                cursor.execute('DELETE FROM alerts WHERE timestamp < ? AND resolved = TRUE', (cutoff_date,))

                conn.commit()
                conn.close()

                print(f"🧹 Cleaned up data older than {cutoff_date}")

            except Exception as e:
                print(f"❌ Cleanup error: {e}")

    def generate_performance_report(self, days: int = 7) -> str:
        """Generate comprehensive performance report"""
        conn = sqlite3.connect(self.db_path)
        report_path = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        try:
            # Get recent data
            start_date = datetime.now() - timedelta(days=days)

            # API Performance
            api_df = pd.read_sql_query('''
                SELECT
                    DATE(timestamp) as date,
                    endpoint,
                    AVG(response_time_ms) as avg_response_time,
                    COUNT(*) as requests,
                    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as error_rate
                FROM api_metrics
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp), endpoint
                ORDER BY date, endpoint
            ''', conn, params=[start_date])

            # System Performance
            system_df = pd.read_sql_query('''
                SELECT
                    DATE(timestamp) as date,
                    AVG(cpu_percent) as avg_cpu,
                    MAX(cpu_percent) as max_cpu,
                    AVG(memory_percent) as avg_memory,
                    MAX(memory_percent) as max_memory,
                    AVG(active_connections) as avg_connections
                FROM system_metrics
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            ''', conn, params=[start_date])

            # Alerts
            alerts_df = pd.read_sql_query('''
                SELECT alert_type, severity, COUNT(*) as count
                FROM alerts
                WHERE timestamp >= ?
                GROUP BY alert_type, severity
                ORDER BY count DESC
            ''', conn, params=[start_date])

            # Generate HTML report
            html_content = self.create_html_report(api_df, system_df, alerts_df, days)

            with open(report_path, 'w') as f:
                f.write(html_content)

            print(f"📄 Performance report generated: {report_path}")
            return report_path

        except Exception as e:
            print(f"❌ Report generation error: {e}")
            return None
        finally:
            conn.close()

    def create_html_report(self, api_df: pd.DataFrame, system_df: pd.DataFrame,
                          alerts_df: pd.DataFrame, days: int) -> str:
        """Create HTML performance report"""
        # Create visualizations
        self.create_performance_charts(api_df, system_df)

        # Calculate summary statistics
        avg_response_time = api_df['avg_response_time'].mean() if not api_df.empty else 0
        total_requests = api_df['requests'].sum() if not api_df.empty else 0
        avg_error_rate = api_df['error_rate'].mean() if not api_df.empty else 0
        avg_cpu = system_df['avg_cpu'].mean() if not system_df.empty else 0
        avg_memory = system_df['avg_memory'].mean() if not system_df.empty else 0

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Report - Last {days} Days</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .metrics {{ display: flex; gap: 20px; margin: 20px 0; }}
                .metric {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; text-align: center; }}
                .metric h3 {{ margin: 0; color: #333; }}
                .metric p {{ font-size: 24px; margin: 10px 0 0 0; color: #007bff; }}
                .section {{ margin: 30px 0; }}
                .chart {{ margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f5f5f5; }}
                .alert-critical {{ color: #dc3545; }}
                .alert-warning {{ color: #ffc107; }}
                .alert-info {{ color: #17a2b8; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>CBSC Trading System Performance Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Period: Last {days} days</p>
            </div>

            <div class="metrics">
                <div class="metric">
                    <h3>Avg Response Time</h3>
                    <p>{avg_response_time:.2f}ms</p>
                </div>
                <div class="metric">
                    <h3>Total Requests</h3>
                    <p>{total_requests:,.0f}</p>
                </div>
                <div class="metric">
                    <h3>Error Rate</h3>
                    <p>{avg_error_rate:.2f}%</p>
                </div>
                <div class="metric">
                    <h3>Avg CPU Usage</h3>
                    <p>{avg_cpu:.1f}%</p>
                </div>
                <div class="metric">
                    <h3>Avg Memory Usage</h3>
                    <p>{avg_memory:.1f}%</p>
                </div>
            </div>

            <div class="section">
                <h2>Performance Charts</h2>
                <div class="chart">
                    <img src="performance_trends.png" alt="Performance Trends" style="max-width: 100%;">
                </div>
            </div>

            <div class="section">
                <h2>API Endpoint Performance</h2>
                <table>
                    <tr>
                        <th>Endpoint</th>
                        <th>Avg Response Time (ms)</th>
                        <th>Requests</th>
                        <th>Error Rate (%)</th>
                    </tr>
        """

        if not api_df.empty:
            endpoint_summary = api_df.groupby('endpoint').agg({
                'avg_response_time': 'mean',
                'requests': 'sum',
                'error_rate': 'mean'
            }).reset_index()

            for _, row in endpoint_summary.iterrows():
                html_template += f"""
                    <tr>
                        <td>{row['endpoint']}</td>
                        <td>{row['avg_response_time']:.2f}</td>
                        <td>{row['requests']:,.0f}</td>
                        <td>{row['error_rate']:.2f}</td>
                    </tr>
                """

        html_template += """
                </table>
            </div>

            <div class="section">
                <h2>Recent Alerts</h2>
                <table>
        """

        if not alerts_df.empty:
            for _, row in alerts_df.iterrows():
                alert_class = f"alert-{row['severity']}"
                html_template += f"""
                    <tr class="{alert_class}">
                        <td>{row['alert_type']}</td>
                        <td>{row['severity'].upper()}</td>
                        <td>{row['count']}</td>
                    </tr>
                """

        html_template += """
                </table>
            </div>
        </body>
        </html>
        """

        return html_template

    def create_performance_charts(self, api_df: pd.DataFrame, system_df: pd.DataFrame):
        """Create performance trend charts"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Performance Trends', fontsize=16)

        # Response time trends
        if not api_df.empty:
            response_pivot = api_df.pivot(index='date', columns='endpoint', values='avg_response_time')
            response_pivot.plot(ax=axes[0, 0], marker='o')
            axes[0, 0].set_title('API Response Time Trends')
            axes[0, 0].set_ylabel('Response Time (ms)')
            axes[0, 0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            axes[0, 0].grid(True)

        # System resource usage
        if not system_df.empty:
            axes[0, 1].plot(system_df['date'], system_df['avg_cpu'], label='CPU', marker='o')
            axes[0, 1].plot(system_df['date'], system_df['avg_memory'], label='Memory', marker='s')
            axes[0, 1].set_title('System Resource Usage')
            axes[0, 1].set_ylabel('Usage (%)')
            axes[0, 1].legend()
            axes[0, 1].grid(True)

        # Error rates
        if not api_df.empty:
            error_pivot = api_df.pivot(index='date', columns='endpoint', values='error_rate')
            error_pivot.plot(ax=axes[1, 0], marker='o')
            axes[1, 0].set_title('Error Rate Trends')
            axes[1, 0].set_ylabel('Error Rate (%)')
            axes[1, 0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            axes[1, 0].grid(True)

        # Request volume
        if not api_df.empty:
            daily_requests = api_df.groupby('date')['requests'].sum()
            daily_requests.plot(kind='bar', ax=axes[1, 1])
            axes[1, 1].set_title('Daily Request Volume')
            axes[1, 1].set_ylabel('Requests')
            axes[1, 1].tick_params(axis='x', rotation=45)
            axes[1, 1].grid(True)

        plt.tight_layout()
        plt.savefig('performance_trends.png', dpi=300, bbox_inches='tight')
        plt.close()


async def main():
    """Main monitoring runner"""
    monitor = PerformanceMonitor()

    try:
        # Start monitoring
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n⚠️ Monitoring stopped by user")
        await monitor.stop_monitoring()
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")
        await monitor.stop_monitoring()


if __name__ == "__main__":
    # Create default config if not exists
    config_path = 'monitoring_config.json'
    if not Path(config_path).exists():
        default_config = {
            "monitoring_interval": 5,
            "alert_thresholds": {
                "response_time_ms": 200,
                "error_rate_percent": 5,
                "cpu_usage_percent": 80,
                "memory_usage_percent": 85
            }
        }
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"📝 Created default config: {config_path}")

    # Run monitoring
    print("🔍 Starting Performance Monitoring System...")
    print("Press Ctrl+C to stop monitoring")
    asyncio.run(main())