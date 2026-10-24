#!/usr/bin/env python3
"""
基础监控系统 - 简化版
Basic Monitoring System - Simplified Edition

系统性能监控和健康检查

Author: Claude Code Assistant
Created: 2025-11-29
Version: 1.0.0
"""

import logging
import os
import psutil
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class BasicMonitor:
    """
    基础监控系统
    提供系统性能监控和健康检查功能
    """

    def __init__(self):
        """初始化监控系统"""
        self.start_time = datetime.now()
        self.metrics_history = []
        self.alerts = []

        logger.info("基础监控系统初始化完成")

    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_used = memory.used / (1024**3)  # GB
            memory_total = memory.total / (1024**3)  # GB
            memory_percent = memory.percent

            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_used = disk.used / (1024**3)  # GB
            disk_total = disk.total / (1024**3)  # GB
            disk_percent = (disk.used / disk.total) * 100

            # 网络IO
            network = psutil.net_io_counters()
            bytes_sent = network.bytes_sent / (1024**2)  # MB
            bytes_recv = network.bytes_recv / (1024**2)  # MB

            # 系统负载
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)

            # 进程信息
            process = psutil.Process()
            process_memory = process.memory_info().rss / (1024**2)  # MB
            process_cpu = process.cpu_percent()

            metrics = {
                'timestamp': datetime.now().isoformat(),
                'uptime': str(datetime.now() - self.start_time),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_avg': list(load_avg)
                },
                'memory': {
                    'used_gb': round(memory_used, 2),
                    'total_gb': round(memory_total, 2),
                    'percent': memory_percent
                },
                'disk': {
                    'used_gb': round(disk_used, 2),
                    'total_gb': round(disk_total, 2),
                    'percent': round(disk_percent, 2)
                },
                'network': {
                    'bytes_sent_mb': round(bytes_sent, 2),
                    'bytes_recv_mb': round(bytes_recv, 2)
                },
                'process': {
                    'memory_mb': round(process_memory, 2),
                    'cpu_percent': process_cpu,
                    'pid': process.pid
                }
            }

            return metrics

        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        try:
            metrics = self.get_system_metrics()
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'status': 'healthy',
                'checks': {}
            }

            # CPU检查
            cpu_percent = metrics.get('cpu', {}).get('percent', 0)
            if cpu_percent > 90:
                health_status['checks']['cpu'] = {'status': 'critical', 'message': f'CPU使用率过高: {cpu_percent}%'}
                health_status['status'] = 'critical'
            elif cpu_percent > 70:
                health_status['checks']['cpu'] = {'status': 'warning', 'message': f'CPU使用率较高: {cpu_percent}%'}
                if health_status['status'] == 'healthy':
                    health_status['status'] = 'warning'
            else:
                health_status['checks']['cpu'] = {'status': 'ok', 'message': f'CPU正常: {cpu_percent}%'}

            # 内存检查
            memory_percent = metrics.get('memory', {}).get('percent', 0)
            if memory_percent > 90:
                health_status['checks']['memory'] = {'status': 'critical', 'message': f'内存使用率过高: {memory_percent}%'}
                health_status['status'] = 'critical'
            elif memory_percent > 80:
                health_status['checks']['memory'] = {'status': 'warning', 'message': f'内存使用率较高: {memory_percent}%'}
                if health_status['status'] == 'healthy':
                    health_status['status'] = 'warning'
            else:
                health_status['checks']['memory'] = {'status': 'ok', 'message': f'内存正常: {memory_percent}%'}

            # 磁盘检查
            disk_percent = metrics.get('disk', {}).get('percent', 0)
            if disk_percent > 95:
                health_status['checks']['disk'] = {'status': 'critical', 'message': f'磁盘空间不足: {disk_percent:.1f}%'}
                health_status['status'] = 'critical'
            elif disk_percent > 85:
                health_status['checks']['disk'] = {'status': 'warning', 'message': f'磁盘空间较少: {disk_percent:.1f}%'}
                if health_status['status'] == 'healthy':
                    health_status['status'] = 'warning'
            else:
                health_status['checks']['disk'] = {'status': 'ok', 'message': f'磁盘空间充足: {disk_percent:.1f}%'}

            return health_status

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'unknown',
                'error': str(e)
            }

    def record_metrics(self):
        """记录当前指标到历史"""
        try:
            metrics = self.get_system_metrics()
            self.metrics_history.append(metrics)

            # 限制历史记录数量
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]

        except Exception as e:
            logger.error(f"记录指标失败: {e}")

    def get_metrics_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取指标历史"""
        return self.metrics_history[-limit:] if limit > 0 else self.metrics_history

    def check_alerts(self) -> List[Dict[str, Any]]:
        """检查告警条件"""
        try:
            metrics = self.get_system_metrics()
            current_alerts = []

            # CPU告警
            cpu_percent = metrics.get('cpu', {}).get('percent', 0)
            if cpu_percent > 90:
                current_alerts.append({
                    'type': 'cpu',
                    'level': 'critical',
                    'message': f'CPU使用率过高: {cpu_percent}%',
                    'timestamp': datetime.now().isoformat()
                })
            elif cpu_percent > 70:
                current_alerts.append({
                    'type': 'cpu',
                    'level': 'warning',
                    'message': f'CPU使用率较高: {cpu_percent}%',
                    'timestamp': datetime.now().isoformat()
                })

            # 内存告警
            memory_percent = metrics.get('memory', {}).get('percent', 0)
            if memory_percent > 90:
                current_alerts.append({
                    'type': 'memory',
                    'level': 'critical',
                    'message': f'内存使用率过高: {memory_percent}%',
                    'timestamp': datetime.now().isoformat()
                })
            elif memory_percent > 80:
                current_alerts.append({
                    'type': 'memory',
                    'level': 'warning',
                    'message': f'内存使用率较高: {memory_percent}%',
                    'timestamp': datetime.now().isoformat()
                })

            # 磁盘告警
            disk_percent = metrics.get('disk', {}).get('percent', 0)
            if disk_percent > 95:
                current_alerts.append({
                    'type': 'disk',
                    'level': 'critical',
                    'message': f'磁盘空间不足: {disk_percent:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })
            elif disk_percent > 85:
                current_alerts.append({
                    'type': 'disk',
                    'level': 'warning',
                    'message': f'磁盘空间较少: {disk_percent:.1f}%',
                    'timestamp': datetime.now().isoformat()
                })

            # 记录新告警
            new_alerts = [alert for alert in current_alerts if alert not in self.alerts[-10:]]
            self.alerts.extend(new_alerts)

            # 限制告警历史
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]

            return current_alerts

        except Exception as e:
            logger.error(f"告警检查失败: {e}")
            return []

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取告警历史"""
        return self.alerts[-limit:] if limit > 0 else self.alerts

    def clear_alerts(self):
        """清空告警历史"""
        self.alerts.clear()
        logger.info("告警历史已清空")

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            if not self.metrics_history:
                return {}

            # 计算平均值
            cpu_values = [m.get('cpu', {}).get('percent', 0) for m in self.metrics_history if 'cpu' in m]
            memory_values = [m.get('memory', {}).get('percent', 0) for m in self.metrics_history if 'memory' in m]

            summary = {
                'period': f'{len(self.metrics_history)} 个数据点',
                'time_range': {
                    'start': self.metrics_history[0].get('timestamp'),
                    'end': self.metrics_history[-1].get('timestamp')
                },
                'averages': {}
            }

            if cpu_values:
                summary['averages']['cpu'] = {
                    'mean': sum(cpu_values) / len(cpu_values),
                    'max': max(cpu_values),
                    'min': min(cpu_values)
                }

            if memory_values:
                summary['averages']['memory'] = {
                    'mean': sum(memory_values) / len(memory_values),
                    'max': max(memory_values),
                    'min': min(memory_values)
                }

            return summary

        except Exception as e:
            logger.error(f"性能摘要生成失败: {e}")
            return {}

    def start_monitoring(self, interval: int = 60):
        """
        开始监控循环

        Args:
            interval: 监控间隔（秒）
        """
        try:
            logger.info(f"开始系统监控，间隔: {interval}秒")

            while True:
                self.record_metrics()
                alerts = self.check_alerts()

                if alerts:
                    for alert in alerts:
                        level = alert['level'].upper()
                        logger.warning(f"[{level}] {alert['message']}")

                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("监控已停止")
        except Exception as e:
            logger.error(f"监控出错: {e}")

    def export_metrics(self, filename: str) -> bool:
        """
        导出指标数据到文件

        Args:
            filename: 文件名

        Returns:
            成功返回True，失败返回False
        """
        try:
            import json

            export_data = {
                'export_time': datetime.now().isoformat(),
                'metrics_history': self.metrics_history,
                'alerts': self.alerts,
                'performance_summary': self.get_performance_summary()
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"指标数据已导出到: {filename}")
            return True

        except Exception as e:
            logger.error(f"指标导出失败: {e}")
            return False


# 便捷函数
def get_monitor() -> BasicMonitor:
    """获取监控实例"""
    return BasicMonitor()

def quick_health_check() -> Dict[str, Any]:
    """快速健康检查"""
    monitor = BasicMonitor()
    return monitor.get_health_status()