#!/usr/bin/env python3
"""
Grafana儀表板生成器
Grafana Dashboard Generator

為量化交易系統生成專業的Grafana儀表板配置
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class GrafanaDashboardGenerator:
    """Grafana儀表板生成器"""

    def __init__(self, output_dir: str = "monitoring_config/grafana/dashboards"):
        """
        初始化儀表板生成器

        Args:
            output_dir: 輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 儀表板基礎配置
        self.base_dashboard_config = {
            "id": None,
            "title": "",
            "tags": ["quantitative-trading", "monitoring"],
            "timezone": "browser",
            "panels": [],
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "refresh": "30s",
            "schemaVersion": 30,
            "version": 1,
            "templating": {
                "list": []
            }
        }

        logger.info(f"Grafana dashboard generator initialized: {self.output_dir}")

    def generate_system_overview_dashboard(self) -> Dict[str, Any]:
        """
        生成系統概覽儀表板

        Returns:
            Dict[str, Any]: 儀表板配置
        """
        dashboard = self.base_dashboard_config.copy()
        dashboard["title"] = "🏦 量化交易系統概覽"
        dashboard["id"] = 1

        # 添加變量模板
        dashboard["templating"]["list"] = [
            {
                "name": "service",
                "type": "query",
                "datasource": "Prometheus",
                "query": "label_values(up, job)",
                "refresh": 1,
                "includeAll": True,
                "allValue": ".*"
            }
        ]

        # 定義面板
        panels = [
            # 系統狀態總覽
            {
                "title": "🟢 系統服務狀態",
                "type": "stat",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "targets": [
                    {
                        "expr": "sum(up{job=~\"quantitative.*\"})",
                        "legendFormat": "在線服務"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "short",
                        "thresholds": {
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 3},
                                {"color": "green", "value": 5}
                            ]
                        },
                        "mappings": [
                            {"options": {"0": {"text": "🔴 系統故障"}}, "type": "value"},
                            {"options": {"1": {"text": "🟡 部分服務"}, "type": "value"},
                            {"options": {"5": {"text": "🟢 系統正常"}}, "type": "value"}
                        ]
                    }
                },
                "options": {
                    "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": "/^Value$/"},
                    "orientation": "auto",
                    "textMode": "auto",
                    "colorMode": "value",
                    "graphMode": "none"
                }
            },

            # 活躍用戶數
            {
                "title": "👥 活躍用戶數",
                "type": "stat",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "targets": [
                    {
                        "expr": "sum(rate(http_requests_total[5m]))",
                        "legendFormat": "請求率"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "reqps",
                        "mappings": [
                            {"options": {"0": {"text": "無活躍用戶"}}, "type": "value"},
                            {"options": {"from": 1, "to": 10, "text": "低活躍度", "color": "yellow"}},
                            {"options": {"from": 10, "to": 50, "text": "正常活躍度", "color": "green"}},
                            {"options": {"from": 50, "to": 100, "text": "高活躍度", "color": "blue"}}
                        ]
                    }
                }
            },

            # 請求量趨勢
            {
                "title": "📊 請求量趨勢",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "targets": [
                    {
                        "expr": "sum(rate(http_requests_total[5m])) by (job)",
                        "legendFormat": "{{job}}"
                    }
                ],
                "yAxes": [
                    {"label": "請求/秒"},
                    {"show": False}
                ]
            },

            # 響應時間
            {
                "title": "⚡ 響應時間 (95th %ile)",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, job))",
                        "legendFormat": "{{job}}"
                    }
                ],
                "yAxes": [
                    {"label": "秒", "max": 1},
                    {"show": False}
                ]
            },

            # 錯誤率
            {
                "title": "❌ 錯誤率",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                "targets": [
                    {
                        "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100",
                        "legendFormat": "錯誤率"
                    }
                ],
                "yAxes": [
                    {"label": "%", "max": 10},
                    {"show": False}
                ]
            },

            # 系統資源使用率
            {
                "title": "💻 系統資源使用率",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                "targets": [
                    {
                        "expr": "system_cpu_usage_percent",
                        "legendFormat": "CPU使用率"
                    },
                    {
                        "expr": "system_memory_usage_percent",
                        "legendFormat": "內存使用率"
                    },
                    {
                        "expr": "system_disk_usage_percent{mountpoint=\"/\"}",
                        "legendFormat": "磁盤使用率"
                    }
                ],
                "yAxes": [
                    {"label": "%", "max": 100},
                    {"show": False}
                ]
            }
        ]

        dashboard["panels"] = panels

        # 保存儀表板
        self.save_dashboard("system_overview", dashboard)
        return dashboard

    def generate_business_metrics_dashboard(self) -> Dict[str, Any]:
        """
        生成業務指標監控儀表板

        Returns:
            Dict[str, Any]: 儀表板配置
        """
        dashboard = self.base_dashboard_config.copy()
        dashboard["title"] = "📈 業務指標監控"
        dashboard["id"] = 2

        # 添加變量模板
        dashboard["templating"]["list"] = [
            {
                "name": "data_source",
                "type": "query",
                "datasource": "Prometheus",
                "query": "label_values(data_quality_score, data_source)",
                "refresh": 1,
                "includeAll": True,
                "allValue": ".*"
            },
            {
                "name": "strategy",
                "type": "query",
                "datasource": "Prometheus",
                "query": "label_values(current_sharpe_ratio, strategy_name)",
                "refresh": 1,
                "includeAll": True,
                "allValue": ".*"
            }
        ]

        panels = [
            # 數據質量評分
            {
                "title": "🔍 數據質量評分",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                "targets": [
                    {
                        "expr": "data_quality_score{data_source=~\"$data_source\"}",
                        "legendFormat": "{{data_source}}"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "short",
                        "min": 0,
                        "max": 100,
                        "thresholds": {
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 70},
                                {"color": "green", "value": 90}
                            ]
                        }
                    }
                }
            },

            # 當前Sharpe比率
            {
                "title": "🎯 當前Sharpe比率",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                "targets": [
                    {
                        "expr": "current_sharpe_ratio{strategy_name=~\"$strategy\"}",
                        "legendFormat": "{{strategy_name}}_{{symbol}}"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "short",
                        "thresholds": {
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 1},
                                {"color": "green", "value": 2},
                                {"color": "purple", "value": 3}
                            ]
                        }
                    }
                }
            },

            # 數據新鮮度
            {
                "title": "🕒 數據新鮮度",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                "targets": [
                    {
                        "expr": "data_freshness_score{data_source=~\"$data_source\"}",
                        "legendFormat": "{{data_source}}"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "short",
                        "min": 0,
                        "max": 100
                    }
                }
            },

            # GPU加速狀態
            {
                "title": "🚀 GPU加速狀態",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
                "targets": [
                    {
                        "expr": "gpu_acceleration_enabled",
                        "legendFormat": "GPU加速"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "mappings": [
                            {"options": {"0": {"text": "❌ 未啟用"}, "1": {"text": "✅ 已啟用"}}, "type": "value"}
                        ]
                    }
                }
            },

            # 技術指標計算性能
            {
                "title": "⚙️ 技術指標計算性能",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "targets": [
                    {
                        "expr": "rate(indicator_calculation_success_total[5m])",
                        "legendFormat": "成功計算率"
                    },
                    {
                        "expr": "rate(indicator_calculation_errors_total[5m])",
                        "legendFormat": "錯誤率"
                    }
                ],
                "yAxes": [
                    {"label": "計算/秒"},
                    {"show": False}
                ]
            },

            # Sharpe計算性能
            {
                "title": "📊 Sharpe計算性能",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(sharpe_calculation_duration_seconds_bucket[5m]))",
                        "legendFormat": "95th %ile"
                    },
                    {
                        "expr": "histogram_quantile(0.50, rate(sharpe_calculation_duration_seconds_bucket[5m]))",
                        "legendFormat": "50th %ile"
                    }
                ],
                "yAxes": [
                    {"label": "秒"},
                    {"show": False}
                ]
            },

            # 回測執行性能
            {
                "title": "🧪 回測執行性能",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(backtest_execution_duration_seconds_bucket[5m]))",
                        "legendFormat": "95th %ile"
                    },
                    {
                        "expr": "rate(strategies_tested_total[5m])",
                        "legendFormat": "策略測試率"
                    }
                ],
                "yAxes": [
                    {"label": "秒 / 策略/秒"},
                    {"show": False}
                ]
            },

            # 交易信號生成
            {
                "title": "💡 交易信號生成",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                "targets": [
                    {
                        "expr": "rate(trading_signals_generated_total[5m])",
                        "legendFormat": "信號生成率"
                    },
                    {
                        "expr": "signal_confidence_score",
                        "legendFormat": "信號置信度"
                    }
                ],
                "yAxes": [
                    {"label": "信號/秒 / 置信度"},
                    {"show": False}
                ]
            }
        ]

        dashboard["panels"] = panels
        self.save_dashboard("business_metrics", dashboard)
        return dashboard

    def generate_infrastructure_dashboard(self) -> Dict[str, Any]:
        """
        生成基礎設施監控儀表板

        Returns:
            Dict[str, Any]: 儀表板配置
        """
        dashboard = self.base_dashboard_config.copy()
        dashboard["title"] = "🖥️ 基礎設施監控"
        dashboard["id"] = 3

        panels = [
            # CPU使用率
            {
                "title": "💻 CPU使用率",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "targets": [
                    {
                        "expr": "system_cpu_usage_percent",
                        "legendFormat": "{{hostname}}"
                    }
                ],
                "yAxes": [
                    {"label": "%", "max": 100},
                    {"show": False}
                ]
            },

            # 內存使用率
            {
                "title": "🧠 內存使用率",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "targets": [
                    {
                        "expr": "system_memory_usage_percent",
                        "legendFormat": "{{hostname}}"
                    }
                ],
                "yAxes": [
                    {"label": "%", "max": 100},
                    {"show": False}
                ]
            },

            # 磁盤使用率
            {
                "title": "💾 磁盤使用率",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "targets": [
                    {
                        "expr": "system_disk_usage_percent",
                        "legendFormat": "{{hostname}}_{{mountpoint}}"
                    }
                ],
                "yAxes": [
                    {"label": "%", "max": 100},
                    {"show": False}
                ]
            },

            # 網絡流量
            {
                "title": "🌐 網絡流量",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "targets": [
                    {
                        "expr": "rate(system_network_bytes_sent_total[5m]) * 8",
                        "legendFormat": "發送"
                    },
                    {
                        "expr": "rate(system_network_bytes_recv_total[5m]) * 8",
                        "legendFormat": "接收"
                    }
                ],
                "yAxes": [
                    {"label": "bits/sec"},
                    {"show": False}
                ]
            },

            # GPU使用率
            {
                "title": "🎮 GPU使用率",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                "targets": [
                    {
                        "expr": "gpu_utilization_percent",
                        "legendFormat": "GPU{{gpu_id}}"
                    }
                ],
                "yAxes": [
                    {"label": "%", "max": 100},
                    {"show": False}
                ]
            },

            # GPU溫度
            {
                "title": "🌡️ GPU溫度",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                "targets": [
                    {
                        "expr": "gpu_temperature_celsius",
                        "legendFormat": "GPU{{gpu_id}}"
                    }
                ],
                "yAxes": [
                    {"label": "°C"},
                    {"show": False}
                ]
            },

            # GPU內存使用率
            {
                "title": "🧮 GPU內存使用率",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 24},
                "targets": [
                    {
                        "expr": "gpu_memory_usage_percent",
                        "legendFormat": "GPU{{gpu_id}}"
                    }
                ],
                "yAxes": [
                    {"label": "%", "max": 100},
                    {"show": False}
                ]
            },

            # Docker容器狀態
            {
                "title": "🐳 Docker容器狀態",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 24},
                "targets": [
                    {
                        "expr": "docker_containers_running",
                        "legendFormat": "運行中"
                    },
                    {
                        "expr": "docker_containers_stopped",
                        "legendFormat": "已停止"
                    },
                    {
                        "expr": "docker_containers_total",
                        "legendFormat": "總數"
                    }
                ],
                "yAxes": [
                    {"label": "容器數"},
                    {"show": False}
                ]
            }
        ]

        dashboard["panels"] = panels
        self.save_dashboard("infrastructure", dashboard)
        return dashboard

    def generate_security_dashboard(self) -> Dict[str, Any]:
        """
        生成安全監控儀表板

        Returns:
            Dict[str, Any]: 儀表板配置
        """
        dashboard = self.base_dashboard_config.copy()
        dashboard["title"] = "🔒 安全監控"
        dashboard["id"] = 4

        panels = [
            # 安全事件總數
            {
                "title": "🚨 安全事件總數",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                "targets": [
                    {
                        "expr": "sum(security_events_total)",
                        "legendFormat": "總事件數"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": 0},
                                {"color": "yellow", "value": 10},
                                {"color": "red", "value": 50}
                            ]
                        }
                    }
                }
            },

            # 活躍威脅數
            {
                "title": "⚠️ 活躍威脅數",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                "targets": [
                    {
                        "expr": "sum(security_events_active)",
                        "legendFormat": "活躍威脅"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": 0},
                                {"color": "yellow", "value": 1},
                                {"color": "red", "value": 5}
                            ]
                        }
                    }
                }
            },

            # 認證失敗率
            {
                "title": "🔐 認證失敗率",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                "targets": [
                    {
                        "expr": "authentication_failure_rate",
                        "legendFormat": "失敗率"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": 0},
                                {"color": "yellow", "value": 5},
                                {"color": "red", "value": 20}
                            ]
                        }
                    }
                }
            },

            # 封鎖IP數
            {
                "title": "🚫 封鎖IP數",
                "type": "stat",
                "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
                "targets": [
                    {
                        "expr": "suspicious_ips_blocked",
                        "legendFormat": "封鎖IP"
                    }
                ]
            },

            # 安全事件類型分布
            {
                "title": "📊 安全事件類型分布",
                "type": "piechart",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "targets": [
                    {
                        "expr": "sum by (event_type) (security_events_total)",
                        "legendFormat": "{{event_type}}"
                    }
                ]
            },

            # 安全事件嚴重程度分布
            {
                "title": "⚖️ 安全事件嚴重程度分布",
                "type": "piechart",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "targets": [
                    {
                        "expr": "sum by (severity) (security_events_total)",
                        "legendFormat": "{{severity}}"
                    }
                ]
            },

            # 認證嘗試趨勢
            {
                "title": "🔑 認證嘗試趨勢",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                "targets": [
                    {
                        "expr": "rate(authentication_attempts_total[5m])",
                        "legendFormat": "總嘗試率"
                    },
                    {
                        "expr": "rate(authentication_attempts_total{result=\"failure\"}[5m])",
                        "legendFormat": "失敗率"
                    }
                ],
                "yAxes": [
                    {"label": "嘗試/秒"},
                    {"show": False}
                ]
            },

            # 數據訪問監控
            {
                "title": "📁 數據訪問監控",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                "targets": [
                    {
                        "expr": "rate(data_access_total[5m])",
                        "legendFormat": "訪問率"
                    },
                    {
                        "expr": "rate(data_access_total{authorized=\"no\"}[5m])",
                        "legendFormat": "未授權訪問"
                    }
                ],
                "yAxes": [
                    {"label": "訪問/秒"},
                    {"show": False}
                ]
            },

            # 合規違規統計
            {
                "title": "⚖️ 合規違規統計",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 24},
                "targets": [
                    {
                        "expr": "rate(compliance_violations_total[5m])",
                        "legendFormat": "違規率"
                    }
                ],
                "yAxes": [
                    {"label": "違規/秒"},
                    {"show": False}
                ]
            },

            # 交易合規評分
            {
                "title": "🎯 交易合規評分",
                "type": "graph",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 24},
                "targets": [
                    {
                        "expr": "trading_compliance_score",
                        "legendFormat": "{{strategy_name}}"
                    }
                ],
                "yAxes": [
                    {"label": "評分", "min": 0, "max": 100},
                    {"show": False}
                ]
            }
        ]

        dashboard["panels"] = panels
        self.save_dashboard("security", dashboard)
        return dashboard

    def save_dashboard(self, dashboard_name: str, dashboard_config: Dict[str, Any]):
        """
        保存儀表板配置

        Args:
            dashboard_name: 儀表板名稱
            dashboard_config: 儀表板配置
        """
        try:
            filename = f"{dashboard_name}_dashboard.json"
            filepath = self.output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dashboard_config, f, indent=2, ensure_ascii=False)

            logger.info(f"Grafana dashboard saved: {filepath}")

        except Exception as e:
            logger.error(f"Failed to save dashboard {dashboard_name}: {e}")
            raise

    def generate_all_dashboards(self) -> List[str]:
        """
        生成所有儀表板

        Returns:
            List[str]: 生成的儀表板文件列表
        """
        generated_files = []

        dashboards = [
            ("system_overview", self.generate_system_overview_dashboard),
            ("business_metrics", self.generate_business_metrics_dashboard),
            ("infrastructure", self.generate_infrastructure_dashboard),
            ("security", self.generate_security_dashboard)
        ]

        for name, generator in dashboards:
            try:
                dashboard = generator()
                generated_files.append(f"{name}_dashboard.json")
                logger.info(f"Generated dashboard: {name}")
            except Exception as e:
                logger.error(f"Failed to generate dashboard {name}: {e}")

        return generated_files

    def create_dashboard_import_script(self) -> str:
        """
        創建儀表板導入腳本

        Returns:
            str: 導入腳本內容
        """
        script_content = """#!/bin/bash

# Grafana Dashboard Import Script
# Usage: ./import_dashboards.sh [grafana_url] [api_key]

GRAFANA_URL=${1:-"http://localhost:3000"}
API_KEY=${2:-"your-api-key-here"}

DASHBOARD_DIR="monitoring_config/grafana/dashboards"

echo "Importing Grafana dashboards to $GRAFANA_URL"

for dashboard_file in "$DASHBOARD_DIR"/*_dashboard.json; do
    if [ -f "$dashboard_file" ]; then
        dashboard_name=$(basename "$dashboard_file" _dashboard.json)
        echo "Importing dashboard: $dashboard_name"

        curl -X POST \\
            -H "Authorization: Bearer $API_KEY" \\
            -H "Content-Type: application/json" \\
            -d @"$dashboard_file" \\
            "$GRAFANA_URL/api/dashboards/db"

        echo "Dashboard $dashboard_name imported successfully"
        echo "---"
    fi
done

echo "All dashboards imported successfully!"
"""

        script_path = self.output_dir / "import_dashboards.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 設置執行權限
        try:
            import os
            os.chmod(script_path, 0o755)
        except:
            pass

        logger.info(f"Dashboard import script created: {script_path}")
        return str(script_path)

if __name__ == "__main__":
    # 創建儀表板生成器
    generator = GrafanaDashboardGenerator()

    print("Generating Grafana dashboards...")

    # 生成所有儀表板
    generated_files = generator.generate_all_dashboards()

    print(f"\nGenerated {len(generated_files)} dashboards:")
    for file in generated_files:
        print(f"  - {file}")

    # 創建導入腳本
    import_script = generator.create_dashboard_import_script()
    print(f"\nImport script created: {import_script}")

    print("\n🎉 Grafana dashboards generated successfully!")
    print("\nTo import dashboards to Grafana:")
    print("1. Copy JSON files from monitoring_config/grafana/dashboards/")
    print("2. Import manually in Grafana UI or use the import script")
    print("3. Ensure Prometheus datasource is configured")