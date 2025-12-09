#!/usr/bin/env python3
"""
企業級監控系統 - 監控配置管理中心
Enterprise Monitoring System - Configuration Management Center

統一管理監控系統配置、指標定義、警報規則和部署配置
"""

import os
import json
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """監控系統配置"""
    # 基礎設施配置
    prometheus_config: Dict[str, Any] = field(default_factory=dict)
    grafana_config: Dict[str, Any] = field(default_factory=dict)
    alertmanager_config: Dict[str, Any] = field(default_factory=dict)

    # 微服務監控配置
    services_config: Dict[str, Any] = field(default_factory=dict)

    # 業務指標配置
    business_metrics_config: Dict[str, Any] = field(default_factory=dict)

    # GPU監控配置
    gpu_monitoring_config: Dict[str, Any] = field(default_factory=dict)

class MonitoringSystemConfig:
    """監控系統配置管理器"""

    def __init__(self, config_dir: str = "monitoring_config"):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目錄
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        # 創建子目錄
        (self.config_dir / "prometheus").mkdir(exist_ok=True)
        (self.config_dir / "grafana").mkdir(exist_ok=True)
        (self.config_dir / "alertmanager").mkdir(exist_ok=True)
        (self.config_dir / "dashboards").mkdir(exist_ok=True)

        logger.info(f"Monitoring system config initialized: {self.config_dir}")

    def generate_prometheus_config(self) -> Dict[str, Any]:
        """
        生成Prometheus配置

        Returns:
            Prometheus配置字典
        """
        config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "rule_files": [
                "/etc/prometheus/rules/*.yml"
            ],
            "alerting": {
                "alertmanagers": [
                    {
                        "static_configs": [
                            {
                                "targets": ["alertmanager:9093"]
                            }
                        ]
                    }
                ]
            },
            "scrape_configs": [
                # Prometheus自身監控
                {
                    "job_name": "prometheus",
                    "static_configs": [
                        {
                            "targets": ["localhost:9090"]
                        }
                    ]
                },

                # 量化交易微服務監控
                {
                    "job_name": "quantitative-data-service",
                    "static_configs": [
                        {
                            "targets": ["localhost:8001"],
                            "labels": {
                                "service": "data-service",
                                "environment": "production"
                            }
                        }
                    ],
                    "scrape_interval": "10s",
                    "metrics_path": "/metrics"
                },
                {
                    "job_name": "quantitative-analytics-service",
                    "static_configs": [
                        {
                            "targets": ["localhost:8002"],
                            "labels": {
                                "service": "analytics-service",
                                "environment": "production"
                            }
                        }
                    ],
                    "scrape_interval": "10s",
                    "metrics_path": "/metrics"
                },
                {
                    "job_name": "quantitative-backtest-service",
                    "static_configs": [
                        {
                            "targets": ["localhost:8003"],
                            "labels": {
                                "service": "backtest-service",
                                "environment": "production"
                            }
                        }
                    ],
                    "scrape_interval": "30s",
                    "metrics_path": "/metrics"
                },
                {
                    "job_name": "quantitative-notification-service",
                    "static_configs": [
                        {
                            "targets": ["localhost:8004"],
                            "labels": {
                                "service": "notification-service",
                                "environment": "production"
                            }
                        }
                    ],
                    "scrape_interval": "15s",
                    "metrics_path": "/metrics"
                },
                {
                    "job_name": "quantitative-config-service",
                    "static_configs": [
                        {
                            "targets": ["localhost:8005"],
                            "labels": {
                                "service": "config-service",
                                "environment": "production"
                            }
                        }
                    ],
                    "scrape_interval": "30s",
                    "metrics_path": "/metrics"
                },

                # 基礎設施監控
                {
                    "job_name": "node-exporter",
                    "static_configs": [
                        {
                            "targets": ["localhost:9100"],
                            "labels": {
                                "service": "node-exporter",
                                "environment": "production"
                            }
                        }
                    ]
                },
                {
                    "job_name": "gpu-exporter",
                    "static_configs": [
                        {
                            "targets": ["localhost:9445"],
                            "labels": {
                                "service": "gpu-exporter",
                                "environment": "production"
                            }
                        }
                    ],
                    "scrape_interval": "5s"
                },
                {
                    "job_name": "docker-exporter",
                    "static_configs": [
                        {
                            "targets": ["localhost:9323"],
                            "labels": {
                                "service": "docker-exporter",
                                "environment": "production"
                            }
                        }
                    ]
                },

                # 數據庫監控
                {
                    "job_name": "postgres-exporter",
                    "static_configs": [
                        {
                            "targets": ["localhost:9187"],
                            "labels": {
                                "service": "postgres-exporter",
                                "environment": "production"
                            }
                        }
                    ]
                },
                {
                    "job_name": "redis-exporter",
                    "static_configs": [
                        {
                            "targets": ["localhost:9121"],
                            "labels": {
                                "service": "redis-exporter",
                                "environment": "production"
                            }
                        }
                    ]
                }
            ]
        }

        return config

    def generate_alertmanager_config(self) -> Dict[str, Any]:
        """
        生成AlertManager配置

        Returns:
            AlertManager配置字典
        """
        config = {
            "global": {
                "smtp_smarthost": "localhost:587",
                "smtp_from": "alerts@quantitative-trading.com"
            },
            "route": {
                "group_by": ["alertname", "service"],
                "group_wait": "10s",
                "group_interval": "10s",
                "repeat_interval": "1h",
                "receiver": "default",
                "routes": [
                    {
                        "match": {
                            "severity": "critical"
                        },
                        "receiver": "critical-alerts",
                        "group_wait": "0s"
                    },
                    {
                        "match": {
                            "severity": "warning"
                        },
                        "receiver": "warning-alerts"
                    }
                ]
            },
            "receivers": [
                {
                    "name": "default",
                    "email_configs": [
                        {
                            "to": "admin@quantitative-trading.com",
                            "subject": "[ALERT] Quantitative Trading System",
                            "body": "{{ range .Alerts }}{{ .Annotations.summary }}\\n{{ .Annotations.description }}{{ end }}"
                        }
                    ],
                    "webhook_configs": [
                        {
                            "url": "http://localhost:8004/webhooks/alerts",
                            "send_resolved": True
                        }
                    ]
                },
                {
                    "name": "critical-alerts",
                    "email_configs": [
                        {
                            "to": "critical@quantitative-trading.com",
                            "subject": "[CRITICAL] Production Alert",
                            "body": "{{ range .Alerts }}{{ .Annotations.summary }}\\n{{ .Annotations.description }}{{ end }}"
                        }
                    ],
                    "webhook_configs": [
                        {
                            "url": "http://localhost:8004/webhooks/critical",
                            "send_resolved": True
                        }
                    ]
                },
                {
                    "name": "warning-alerts",
                    "webhook_configs": [
                        {
                            "url": "http://localhost:8004/webhooks/warnings",
                            "send_resolved": True
                        }
                    ]
                }
            ]
        }

        return config

    def generate_grafana_datasources_config(self) -> Dict[str, Any]:
        """
        生成Grafana數據源配置

        Returns:
            Grafana數據源配置字典
        """
        return {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "access": "proxy",
                    "url": "http://prometheus:9090",
                    "isDefault": True,
                    "jsonData": {
                        "timeInterval": "15s"
                    }
                },
                {
                    "name": "InfluxDB",
                    "type": "influxdb",
                    "access": "proxy",
                    "url": "http://influxdb:8086",
                    "database": "quantitative_trading",
                    "jsonData": {
                        "version": "Flux"
                    }
                },
                {
                    "name": "PostgreSQL",
                    "type": "postgres",
                    "access": "proxy",
                    "url": "postgres:5432",
                    "database": "quantitative_trading",
                    "user": "grafana",
                    "jsonData": {
                        "sslmode": "disable"
                    }
                }
            ]
        }

    def generate_monitoring_rules(self) -> List[Dict[str, Any]]:
        """
        生成監控規則

        Returns:
            監控規則列表
        """
        rules = [
            # 系統級規則
            {
                "name": "system.rules.yml",
                "content": {
                    "groups": [
                        {
                            "name": "system.alerts",
                            "rules": [
                                {
                                    "alert": "ServiceDown",
                                    "expr": "up{job=~\"quantitative.*\"} == 0",
                                    "for": "1m",
                                    "labels": {
                                        "severity": "critical"
                                    },
                                    "annotations": {
                                        "summary": "Quantitative trading service is down",
                                        "description": "Service {{ $labels.job }} on {{ $labels.instance }} has been down for more than 1 minute."
                                    }
                                },
                                {
                                    "alert": "HighErrorRate",
                                    "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) > 0.05",
                                    "for": "2m",
                                    "labels": {
                                        "severity": "warning"
                                    },
                                    "annotations": {
                                        "summary": "High error rate detected",
                                        "description": "Error rate is {{ $value | humanizePercentage }} for service {{ $labels.job }}"
                                    }
                                },
                                {
                                    "alert": "HighResponseTime",
                                    "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1",
                                    "for": "5m",
                                    "labels": {
                                        "severity": "warning"
                                    },
                                    "annotations": {
                                        "summary": "High response time detected",
                                        "description": "95th percentile response time is {{ $value }}s for service {{ $labels.job }}"
                                    }
                                }
                            ]
                        }
                    ]
                }
            },

            # 基礎設施規則
            {
                "name": "infrastructure.rules.yml",
                "content": {
                    "groups": [
                        {
                            "name": "infrastructure.alerts",
                            "rules": [
                                {
                                    "alert": "HighCPUUsage",
                                    "expr": "100 - (avg by(instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100) > 80",
                                    "for": "5m",
                                    "labels": {
                                        "severity": "warning"
                                    },
                                    "annotations": {
                                        "summary": "High CPU usage",
                                        "description": "CPU usage is {{ $value }}% on instance {{ $labels.instance }}"
                                    }
                                },
                                {
                                    "alert": "HighMemoryUsage",
                                    "expr": "((node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes) * 100 > 85",
                                    "for": "5m",
                                    "labels": {
                                        "severity": "warning"
                                    },
                                    "annotations": {
                                        "summary": "High memory usage",
                                        "description": "Memory usage is {{ $value }}% on instance {{ $labels.instance }}"
                                    }
                                },
                                {
                                    "alert": "DiskSpaceLow",
                                    "expr": "((node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes) * 100 > 90",
                                    "for": "10m",
                                    "labels": {
                                        "severity": "critical"
                                    },
                                    "annotations": {
                                        "summary": "Disk space running low",
                                        "description": "Disk usage is {{ $value }}% on {{ $labels.instance }}:{{ $labels.mountpoint }}"
                                    }
                                }
                            ]
                        }
                    ]
                }
            },

            # GPU監控規則
            {
                "name": "gpu.rules.yml",
                "content": {
                    "groups": [
                        {
                            "name": "gpu.alerts",
                            "rules": [
                                {
                                    "alert": "GPUHighUtilization",
                                    "expr": "gpu_utilization_percent > 95",
                                    "for": "10m",
                                    "labels": {
                                        "severity": "warning"
                                    },
                                    "annotations": {
                                        "summary": "GPU high utilization",
                                        "description": "GPU utilization is {{ $value }}% on {{ $labels.instance }}"
                                    }
                                },
                                {
                                    "alert": "GPUHighTemperature",
                                    "expr": "gpu_temperature_celsius > 85",
                                    "for": "5m",
                                    "labels": {
                                        "severity": "critical"
                                    },
                                    "annotations": {
                                        "summary": "GPU high temperature",
                                        "description": "GPU temperature is {{ $value }}°C on {{ $labels.instance }}"
                                    }
                                },
                                {
                                    "alert": "GPUMemoryLow",
                                    "expr": "(gpu_memory_used_bytes / gpu_memory_total_bytes) * 100 > 90",
                                    "for": "5m",
                                    "labels": {
                                        "severity": "warning"
                                    },
                                    "annotations": {
                                        "summary": "GPU memory running low",
                                        "description": "GPU memory usage is {{ $value }}% on {{ $labels.instance }}"
                                    }
                                }
                            ]
                        }
                    ]
                }
            },

            # 業務指標規則
            {
                "name": "business.rules.yml",
                "content": {
                    "groups": [
                        {
                            "name": "business.alerts",
                            "rules": [
                                {
                                    "alert": "LowDataQualityScore",
                                    "expr": "data_quality_score < 70",
                                    "for": "2m",
                                    "labels": {
                                        "severity": "warning"
                                    },
                                    "annotations": {
                                        "summary": "Low data quality score",
                                        "description": "Data quality score is {{ $value }} for {{ $labels.data_source }}"
                                    }
                                },
                                {
                                    "alert": "SharpeCalculationError",
                                    "expr": "rate(sharpe_calculation_errors_total[5m]) > 0",
                                    "for": "1m",
                                    "labels": {
                                        "severity": "critical"
                                    },
                                    "annotations": {
                                        "summary": "Sharpe ratio calculation errors",
                                        "description": "Sharpe calculation error rate is {{ $value }}/s"
                                    }
                                },
                                {
                                    "alert": "SlowBacktestExecution",
                                    "expr": "histogram_quantile(0.95, rate(backtest_execution_duration_seconds_bucket[5m])) > 60",
                                    "for": "10m",
                                    "labels": {
                                        "severity": "warning"
                                    },
                                    "annotations": {
                                        "summary": "Slow backtest execution",
                                        "description": "95th percentile backtest time is {{ $value }}s"
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        ]

        return rules

    def save_configurations(self) -> None:
        """保存所有配置文件"""
        try:
            # 保存Prometheus配置
            prometheus_config = self.generate_prometheus_config()
            with open(self.config_dir / "prometheus" / "prometheus.yml", "w", encoding="utf-8") as f:
                yaml.dump(prometheus_config, f, default_flow_style=False, allow_unicode=True)

            # 保存AlertManager配置
            alertmanager_config = self.generate_alertmanager_config()
            with open(self.config_dir / "alertmanager" / "alertmanager.yml", "w", encoding="utf-8") as f:
                yaml.dump(alertmanager_config, f, default_flow_style=False, allow_unicode=True)

            # 保存Grafana數據源配置
            grafana_config = self.generate_grafana_datasources_config()
            with open(self.config_dir / "grafana" / "datasources.yml", "w", encoding="utf-8") as f:
                yaml.dump(grafana_config, f, default_flow_style=False, allow_unicode=True)

            # 保存監控規則
            rules = self.generate_monitoring_rules()
            for rule in rules:
                with open(self.config_dir / "prometheus" / "rules" / rule["name"], "w", encoding="utf-8") as f:
                    yaml.dump(rule["content"], f, default_flow_style=False, allow_unicode=True)

            logger.info("All monitoring configurations saved successfully")

        except Exception as e:
            logger.error(f"Failed to save configurations: {e}")
            raise

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        獲取特定服務的監控配置

        Args:
            service_name: 服務名稱

        Returns:
            服務監控配置
        """
        service_configs = {
            "data-service": {
                "port": 8001,
                "metrics_endpoint": "/metrics",
                "health_endpoint": "/health",
                "key_metrics": [
                    "data_fetch_duration_seconds",
                    "data_quality_score",
                    "api_requests_total",
                    "cache_hit_ratio"
                ],
                "slo": {
                    "availability": 99.9,
                    "response_time_p95": 500,  # ms
                    "error_rate": 1.0  # %
                }
            },
            "analytics-service": {
                "port": 8002,
                "metrics_endpoint": "/metrics",
                "health_endpoint": "/health",
                "key_metrics": [
                    "indicator_calculation_duration_seconds",
                    "strategy_analysis_duration_seconds",
                    "sharpe_calculation_errors_total",
                    "gpu_acceleration_enabled"
                ],
                "slo": {
                    "availability": 99.9,
                    "response_time_p95": 2000,  # ms
                    "error_rate": 2.0  # %
                }
            },
            "backtest-service": {
                "port": 8003,
                "metrics_endpoint": "/metrics",
                "health_endpoint": "/health",
                "key_metrics": [
                    "backtest_execution_duration_seconds",
                    "backtest_queue_depth",
                    "strategy_performance_score",
                    "concurrent_backtests"
                ],
                "slo": {
                    "availability": 99.5,
                    "response_time_p95": 30000,  # ms (30s)
                    "error_rate": 5.0  # %
                }
            },
            "notification-service": {
                "port": 8004,
                "metrics_endpoint": "/metrics",
                "health_endpoint": "/health",
                "key_metrics": [
                    "notification_delivery_duration_seconds",
                    "telegram_alerts_total",
                    "email_alerts_total",
                    "alert_failure_rate"
                ],
                "slo": {
                    "availability": 99.99,
                    "response_time_p95": 1000,  # ms
                    "error_rate": 0.5  # %
                }
            },
            "config-service": {
                "port": 8005,
                "metrics_endpoint": "/metrics",
                "health_endpoint": "/health",
                "key_metrics": [
                    "config_fetch_duration_seconds",
                    "configuration_updates_total",
                    "cache_miss_ratio",
                    "config_validation_errors_total"
                ],
                "slo": {
                    "availability": 99.99,
                    "response_time_p95": 100,  # ms
                    "error_rate": 0.1  # %
                }
            }
        }

        return service_configs.get(service_name, {})

# 全局配置管理器實例
monitoring_config_manager = MonitoringSystemConfig()

def get_monitoring_config() -> MonitoringSystemConfig:
    """獲取監控配置管理器實例"""
    return monitoring_config_manager

if __name__ == "__main__":
    # 生成並保存所有監控配置
    config_manager = MonitoringSystemConfig()
    config_manager.save_configurations()

    print("Monitoring system configurations generated successfully!")
    print(f"Configurations saved to: {config_manager.config_dir}")

    # 打印配置摘要
    print("\n=== Configuration Summary ===")
    print("✅ Prometheus configuration: prometheus/prometheus.yml")
    print("✅ AlertManager configuration: alertmanager/alertmanager.yml")
    print("✅ Grafana datasources: grafana/datasources.yml")
    print("✅ Monitoring rules: prometheus/rules/")
    print("\nGenerated monitoring rules:")
    rules = config_manager.generate_monitoring_rules()
    for rule in rules:
        print(f"  - {rule['name']}")