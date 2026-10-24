#!/usr/bin/env python3
"""
監控系統部署腳本
Monitoring System Deployment Script

自動化部署整個監控系統：Prometheus、Grafana、AlertManager等
"""

import os
import sys
import time
import json
import yaml
import logging
import subprocess
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class MonitoringSystemDeployer:
    """監控系統部署器"""

    def __init__(self, config_dir: str = "monitoring_config"):
        """
        初始化部署器

        Args:
            config_dir: 配置目錄
        """
        self.config_dir = Path(config_dir)
        self.deployment_dir = Path("monitoring_deployment")
        self.deployment_dir.mkdir(exist_ok=True)

        # 服務配置
        self.services = {
            "prometheus": {
                "image": "prom/prometheus:latest",
                "port": 9090,
                "config_file": "prometheus.yml",
                "volumes": [
                    f"{self.config_dir}/prometheus:/etc/prometheus",
                    "prometheus_data:/prometheus"
                ]
            },
            "grafana": {
                "image": "grafana/grafana:latest",
                "port": 3000,
                "config_file": "datasources.yml",
                "volumes": [
                    f"{self.config_dir}/grafana:/etc/grafana/provisioning",
                    "grafana_data:/var/lib/grafana"
                ]
            },
            "alertmanager": {
                "image": "prom/alertmanager:latest",
                "port": 9093,
                "config_file": "alertmanager.yml",
                "volumes": [
                    f"{self.config_dir}/alertmanager:/etc/alertmanager",
                    "alertmanager_data:/alertmanager"
                ]
            },
            "node-exporter": {
                "image": "prom/node-exporter:latest",
                "port": 9100,
                "volumes": [
                    "/proc:/host/proc:ro",
                    "/sys:/host/sys:ro",
                    "/:/rootfs:ro"
                ],
                "command": [
                    "--path.procfs=/host/proc",
                    "--path.sysfs=/host/sys",
                    "--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($|/)"
                ]
            },
            "gpu-exporter": {
                "image": "mindprince/gpu-exporter:latest",
                "port": 9445,
                "volumes": [
                    "/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1:/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1:ro",
                    "/usr/bin/nvidia-smi:/usr/bin/nvidia-smi:ro"
                ]
            },
            "docker-exporter": {
                "image": "prom/docker-exporter:latest",
                "port": 9323,
                "volumes": [
                    "/var/run/docker.sock:/var/run/docker.sock:ro"
                ]
            }
        }

        logger.info("Monitoring system deployer initialized")

    def check_prerequisites(self) -> bool:
        """
        檢查部署前置條件

        Returns:
            bool: 是否滿足前置條件
        """
        print("🔍 檢查部署前置條件...")

        # 檢查Docker
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker未安裝或無法訪問")
                return False
            print(f"✅ Docker已安裝: {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ Docker未安裝")
            return False

        # 檢查Docker Compose
        try:
            result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker Compose未安裝")
                return False
            print(f"✅ Docker Compose已安裝: {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ Docker Compose未安裝")
            return False

        # 檢查配置文件
        required_configs = [
            "prometheus/prometheus.yml",
            "alertmanager/alertmanager.yml",
            "grafana/datasources.yml"
        ]

        for config_file in required_configs:
            config_path = self.config_dir / config_file
            if not config_path.exists():
                print(f"❌ 配置文件缺失: {config_file}")
                return False
            print(f"✅ 配置文件存在: {config_file}")

        # 檢查端口可用性
        used_ports = []
        for service_name, service_config in self.services.items():
            port = service_config["port"]
            if port in used_ports:
                print(f"❌ 端口衝突: {port} (服務 {service_name})")
                return False
            used_ports.append(port)

        print("✅ 所有前置條件檢查通過")
        return True

    def generate_docker_compose(self) -> str:
        """
        生成Docker Compose配置

        Returns:
            str: Docker Compose文件路徑
        """
        print("📝 生成Docker Compose配置...")

        compose_config = {
            "version": "3.8",
            "services": {},
            "volumes": {
                "prometheus_data": {},
                "grafana_data": {},
                "alertmanager_data": {}
            },
            "networks": {
                "monitoring": {
                    "driver": "bridge"
                }
            }
        }

        # 配置監控服務
        for service_name, service_config in self.services.items():
            service_definition = {
                "image": service_config["image"],
                "container_name": f"quantitative_{service_name}",
                "ports": [f"{service_config['port']}:9100" if service_name == "node-exporter"
                         else f"{service_config['port']}:9093" if service_name == "alertmanager"
                         else f"{service_config['port']}:3000" if service_name == "grafana"
                         else f"{service_config['port']}:{service_config['port']}"],
                "volumes": service_config.get("volumes", []),
                "networks": ["monitoring"],
                "restart": "unless-stopped"
            }

            # 添加特定配置
            if service_name == "prometheus":
                service_definition["command"] = [
                    "--config.file=/etc/prometheus/prometheus.yml",
                    "--storage.tsdb.path=/prometheus",
                    "--web.console.libraries=/etc/prometheus/console_libraries",
                    "--web.console.templates=/etc/prometheus/consoles",
                    "--storage.tsdb.retention.time=200h",
                    "--web.enable-lifecycle"
                ]

            elif service_name == "grafana":
                service_definition["environment"] = [
                    "GF_SECURITY_ADMIN_PASSWORD=admin123",
                    "GF_USERS_ALLOW_SIGN_UP=false"
                ]
                service_definition["user"] = "472"

            elif service_name == "alertmanager":
                service_definition["command"] = [
                    "--config.file=/etc/alertmanager/alertmanager.yml",
                    "--storage.path=/alertmanager"
                ]

            elif service_name in ["node-exporter", "gpu-exporter", "docker-exporter"]:
                service_definition["pid"] = "host"

                if service_name == "node-exporter":
                    service_definition["ports"] = [f"{service_config['port']}:{service_config['port']}"]

            if "command" in service_config:
                service_definition["command"] = service_config["command"]

            compose_config["services"][service_name] = service_definition

        # 添加量化交易服務監控
        compose_config["services"].update({
            "quantitative-monitoring": {
                "build": ".",
                "container_name": "quantitative_monitoring",
                "volumes": [
                    f"{self.config_dir}:/app/monitoring_config:ro",
                    "../:/app/src:ro"
                ],
                "networks": ["monitoring"],
                "restart": "unless-stopped",
                "command": ["python", "monitoring_system/infrastructure_monitoring.py"],
                "depends_on": ["prometheus"]
            }
        })

        # 保存Docker Compose文件
        compose_file = self.deployment_dir / "docker-compose.yml"
        with open(compose_file, 'w', encoding='utf-8') as f:
            yaml.dump(compose_config, f, default_flow_style=False, allow_unicode=True)

        print(f"✅ Docker Compose配置已生成: {compose_file}")
        return str(compose_file)

    def generate_dockerfile(self) -> str:
        """
        生成Dockerfile

        Returns:
            str: Dockerfile路徑
        """
        print("📝 生成Dockerfile...")

        dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# 複製requirements文件
COPY requirements.txt .

# 安裝Python依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY monitoring_system/ ./monitoring_system/
COPY simplified_system/ ./simplified_system/
COPY src/ ./src/

# 創建非root用戶
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露指標端口
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8080/metrics')"

# 啟動命令
CMD ["python", "monitoring_system/infrastructure_monitoring.py"]
"""

        dockerfile_path = self.deployment_dir / "Dockerfile"
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)

        print(f"✅ Dockerfile已生成: {dockerfile_path}")
        return str(dockerfile_path)

    def generate_requirements(self) -> str:
        """
        生成requirements.txt

        Returns:
            str: requirements.txt路徑
        """
        print("📝 生成requirements.txt...")

        requirements_content = """# 監控系統依賴
prometheus-client==0.17.1
psutil==5.9.6
GPUtil==1.4.0
docker==6.1.3
aiohttp==3.8.6
asyncio==3.4.3

# 數據處理
pandas==1.5.3
numpy==1.24.4

# 配置管理
pyyaml==6.0.1

# 加密和安全
cryptography==41.0.7

# 網絡請求
requests==2.31.0

# 日誌
logging

# 量化交易系統依賴
vectorbt==0.25.2
"""

        requirements_path = self.deployment_dir / "requirements.txt"
        with open(requirements_path, 'w', encoding='utf-8') as f:
            f.write(requirements_content)

        print(f"✅ requirements.txt已生成: {requirements_path}")
        return str(requirements_path)

    def deploy_services(self) -> bool:
        """
        部署監控服務

        Returns:
            bool: 是否部署成功
        """
        print("🚀 部署監控服務...")

        try:
            # 切換到部署目錄
            os.chdir(self.deployment_dir)

            # 啟動服務
            commands = [
                ["docker-compose", "down"],  # 停止現有服務
                ["docker-compose", "build"],  # 構建鏡像
                ["docker-compose", "up", "-d"]  # 啟動服務
            ]

            for cmd in commands:
                print(f"執行命令: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"❌ 命令執行失敗: {result.stderr}")
                    return False

                print(f"✅ 命令執行成功: {result.stdout}")

            print("✅ 監控服務部署完成")
            return True

        except Exception as e:
            print(f"❌ 部署失敗: {e}")
            return False

    def verify_deployment(self) -> bool:
        """
        驗證部署

        Returns:
            bool: 是否驗證通過
        """
        print("🔍 驗證部署...")

        # 等待服務啟動
        print("等待服務啟動...")
        time.sleep(30)

        verification_results = {}

        # 檢查各個服務
        service_urls = {
            "prometheus": "http://localhost:9090/api/v1/status/config",
            "grafana": "http://localhost:3000/api/health",
            "alertmanager": "http://localhost:9093/api/v1/status"
        }

        for service_name, url in service_urls.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    verification_results[service_name] = "✅ 正常"
                    print(f"✅ {service_name} 服務正常")
                else:
                    verification_results[service_name] = f"❌ HTTP {response.status_code}"
                    print(f"❌ {service_name} 服務異常: HTTP {response.status_code}")
            except Exception as e:
                verification_results[service_name] = f"❌ 連接失敗: {str(e)}"
                print(f"❌ {service_name} 服務連接失敗: {e}")

        # 檢查指標端點
        metrics_endpoints = {
            "node-exporter": "http://localhost:9100/metrics",
            "gpu-exporter": "http://localhost:9445/metrics"
        }

        for service_name, url in metrics_endpoints.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200 and "HELP" in response.text:
                    verification_results[service_name] = "✅ 正常"
                    print(f"✅ {service_name} 指標正常")
                else:
                    verification_results[service_name] = "❌ 指標異常"
                    print(f"❌ {service_name} 指標異常")
            except Exception as e:
                verification_results[service_name] = f"❌ 連接失敗: {str(e)}"
                print(f"❌ {service_name} 指標連接失敗: {e}")

        # 生成驗證報告
        self._generate_verification_report(verification_results)

        # 檢查是否有失敗的服務
        failed_services = [k for k, v in verification_results.items() if "❌" in str(v)]
        if failed_services:
            print(f"❌ 驗證失敗，異常服務: {failed_services}")
            return False

        print("✅ 所有服務驗證通過")
        return True

    def _generate_verification_report(self, results: Dict[str, str]):
        """生成驗證報告"""
        report = {
            "deployment_time": datetime.now().isoformat(),
            "services": results,
            "summary": {
                "total": len(results),
                "success": len([v for v in results.values() if "✅" in str(v)]),
                "failed": len([v for v in results.values() if "❌" in str(v)])
            }
        }

        report_file = self.deployment_dir / f"deployment_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📊 驗證報告已生成: {report_file}")

    def generate_deployment_script(self) -> str:
        """
        生成部署腳本

        Returns:
            str: 部署腳本路徑
        """
        print("📝 生成部署腳本...")

        script_content = """#!/bin/bash

# 量化交易監控系統部署腳本
# Usage: ./deploy_monitoring.sh [start|stop|restart|status]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 顏色定義
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安裝"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose未安裝"
        exit 1
    fi

    print_status "Docker環境檢查通過"
}

# 啟動服務
start_services() {
    print_status "啟動監控服務..."

    docker-compose down
    docker-compose build
    docker-compose up -d

    print_status "等待服務啟動..."
    sleep 30

    # 檢查服務狀態
    if docker-compose ps | grep -q "Up"; then
        print_status "服務啟動成功"
        show_service_urls
    else
        print_error "服務啟動失敗"
        docker-compose ps
        exit 1
    fi
}

# 停止服務
stop_services() {
    print_status "停止監控服務..."
    docker-compose down
    print_status "服務已停止"
}

# 重啟服務
restart_services() {
    print_status "重啟監控服務..."
    stop_services
    start_services
}

# 顯示服務狀態
show_status() {
    print_status "服務狀態:"
    docker-compose ps

    echo ""
    print_status "服務URL:"
    show_service_urls
}

# 顯示服務URL
show_service_urls() {
    echo "🔗 Prometheus: http://localhost:9090"
    echo "🔗 Grafana: http://localhost:3000 (admin/admin123)"
    echo "🔗 AlertManager: http://localhost:9093"
    echo ""
    echo "🔗 Node Exporter: http://localhost:9100/metrics"
    echo "🔗 GPU Exporter: http://localhost:9445/metrics (如果GPU可用)"
    echo "🔗 Docker Exporter: http://localhost:9323/metrics"
}

# 清理日誌
clean_logs() {
    print_status "清理服務日誌..."
    docker-compose logs --tail=0 -f > /dev/null 2>&1 &
    print_status "日誌已清理"
}

# 查看日誌
view_logs() {
    docker-compose logs -f
}

# 主函數
case "${1:-start}" in
    start)
        check_docker
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        check_docker
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        view_logs
        ;;
    clean)
        clean_logs
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|clean}"
        echo ""
        echo "  start   - 啟動監控服務"
        echo "  stop    - 停止監控服務"
        echo "  restart - 重啟監控服務"
        echo "  status  - 顯示服務狀態"
        echo "  logs    - 查看服務日誌"
        echo "  clean   - 清理服務日誌"
        exit 1
        ;;
esac
"""

        script_path = self.deployment_dir / "deploy_monitoring.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 設置執行權限
        try:
            import os
            os.chmod(script_path, 0o755)
        except:
            pass

        print(f"✅ 部署腳本已生成: {script_path}")
        return str(script_path)

    def generate_documentation(self) -> str:
        """
        生成部署文檔

        Returns:
            str: 文檔文件路徑
        """
        print("📝 生成部署文檔...")

        doc_content = """# 量化交易監控系統部署指南

## 概述

本監控系統為量化交易平台提供完整的監控和警報解決方案，包括：

- 🖥️ **基礎設施監控**: CPU、內存、磁盤、網絡、GPU
- 🏗️ **微服務監控**: 5個量化交易微服務的健康狀態和性能
- 📊 **業務指標監控**: 數據質量、技術指標計算、Sharpe比率、回測性能
- 🔒 **安全監控**: 認證、數據訪問、配置變更、合規性
- 📈 **可視化**: Grafana儀表板和實時監控
- 🚨 **智能警報**: 多級警報和自動化通知

## 系統架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   量化交易服務   │    │   基礎設施監控   │    │   業務指標監控   │
│                 │    │                 │    │                 │
│ • Data Service  │◄──►│ • System Metrics │◄──►│ • Data Quality  │
│ • Analytics     │    │ • GPU Monitoring │    │ • Performance   │
│ • Backtest      │    │ • Docker Stats   │    │ • Sharpe Ratio  │
│ • Notification  │    │ • Network Stats  │    │ • Trading Signals│
│ • Config        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   監控數據收集器   │
                    │                 │
                    │ • Prometheus    │
                    │ • AlertManager  │
                    │ • Node Exporter │
                    │ • GPU Exporter   │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   可視化和警報   │
                    │                 │
                    │ • Grafana       │
                    │ • Alerting      │
                    │ • Notifications │
                    └─────────────────┘
```

## 快速開始

### 1. 前置條件

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ 內存
- 20GB+ 磁盤空間

### 2. 一鍵部署

```bash
# 克隆項目
git clone <repository-url>
cd CODEX--

# 生成監控配置
python monitoring_system/deploy_monitoring.py

# 部署服務
cd monitoring_deployment
./deploy_monitoring.sh start
```

### 3. 驗證部署

```bash
# 檢查服務狀態
./deploy_monitoring.sh status

# 訪問監控界面
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin123)
# AlertManager: http://localhost:9093
```

## 詳細配置

### 服務配置

| 服務 | 端口 | 配置文件 | 描述 |
|------|------|----------|------|
| Prometheus | 9090 | `prometheus.yml` | 指標收集和存儲 |
| Grafana | 3000 | `datasources.yml` | 數據可視化 |
| AlertManager | 9093 | `alertmanager.yml` | 警報管理 |
| Node Exporter | 9100 | - | 系統指標 |
| GPU Exporter | 9445 | - | GPU指標 |
| Docker Exporter | 9323 | - | 容器指標 |

### 監控指標

#### 基礎設施指標
- CPU使用率、負載、頻率
- 內存使用率、交換分區
- 磁盤使用率、I/O統計
- 網絡流量、連接數
- GPU使用率、溫度、內存

#### 微服務指標
- 服務可用性、響應時間
- 請求量、錯誤率、成功率
- 併發連接數、隊列深度
- 服務依賴和調用鏈

#### 業務指標
- 數據質量評分、新鮮度、完整性
- 技術指標計算性能、GPU加速效果
- Sharpe比率計算正確性
- 回測執行效率、策略性能
- 交易信號生成、置信度

#### 安全指標
- 認證成功/失敗率
- 未授權訪問嘗試
- 配置變更審計
- 數據訪問控制
- 合規性檢查

### 警報規則

#### 系統警報
- 服務宕機 (可用性<99.9%)
- 高錯誤率 (>5%)
- 高響應時間 (>1秒)
- 資源使用率告警 (>80%)

#### 業務警報
- 數據源中斷
- 數據質量下降 (<70分)
- 計算錯誤檢測
- GPU故障

#### 安全警報
- 未授權訪問嘗試
- 配置未授權修改
- 異常交易活動

## Grafana儀表板

### 1. 系統概覽儀表板
- 服務健康狀態總覽
- 活躍用戶數和請求量
- 系統資源使用情況
- 關鍵性能指標

### 2. 業務監控儀表板
- 實時數據質量評分
- 技術指標計算性能
- GPU加速效果監控
- Sharpe計算正確性監控

### 3. 金融風險監控儀表板
- 策略回報實時追蹤
- 風險指標監控
- 市場波動率監控
- 異常交易模式檢測

### 4. 運維監控儀表板
- 容器健康狀態
- GPU利用率監控
- 數據庫性能
- 網絡流量分析

## 通知配置

### 支持的通知渠道
- 📧 **郵件通知**: SMTP配置，支持HTML格式
- 📱 **Telegram Bot**: 即時推送，支持豐富格式
- 💬 **Slack**: 頻道通知，支持交互式操作
- 🔗 **Webhook**: 自定義集成，支持REST API
- 📱 **SMS**: 短信通知 (需要提供商)

### 警報級別
- **Critical**: 系統宕機、數據丟失
- **Warning**: 性能下降、資源不足
- **Info**: 配置變更、定期報告

## 維護操作

### 日常維護
```bash
# 查看服務狀態
./deploy_monitoring.sh status

# 查看服務日誌
./deploy_monitoring.sh logs

# 重啟服務
./deploy_monitoring.sh restart

# 清理日誌
./deploy_monitoring.sh clean
```

### 數據備份
```bash
# 備份Prometheus數據
docker run --rm -v quantitative_prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus_$(date +%Y%m%d).tar.gz -C /data .

# 備份Grafana配置
docker run --rm -v quantitative_grafana_data:/data -v $(pwd):/backup alpine tar czf /backup/grafana_$(date +%Y%m%d).tar.gz -C /data .
```

### 性能優化
```bash
# 調整Prometheus存儲保留期
# 編輯 monitoring_config/prometheus/prometheus.yml
# 修改 --storage.tsdb.retention.time=200h

# 調整Grafana內存限制
# 編輯 docker-compose.yml，添加環境變量
# GF_SECURITY_ADMIN_MEMORY_LIMIT=2Gi
```

## 故障排除

### 常見問題

#### 1. 服務無法啟動
```bash
# 檢查端口占用
netstat -tulpn | grep :9090

# 檢查Docker日誌
docker logs quantitative_prometheus

# 重置部署
./deploy_monitoring.sh stop
./deploy_monitoring.sh start
```

#### 2. 指標收集異常
```bash
# 檢查Prometheus目標
curl http://localhost:9090/api/v1/targets

# 檢查節點指標
curl http://localhost:9100/metrics

# 檢查GPU指標 (如果可用)
curl http://localhost:9445/metrics
```

#### 3. Grafana無法連接數據源
```bash
# 檢查數據源配置
cat monitoring_config/grafana/datasources.yml

# 重啟Grafana
docker restart quantitative_grafana

# 檢查網絡連接
docker exec quantitative_grafana wget -qO- http://prometheus:9090/api/v1/status/config
```

#### 4. 警報不發送
```bash
# 檢查AlertManager配置
cat monitoring_config/alertmanager/alertmanager.yml

# 檢查警報規則
curl http://localhost:9093/api/v1/alerts

# 測試郵件配置
docker exec quantitative_alertmanager amtool config routes test
```

### 性能調優

#### Prometheus優化
- 增加存儲空間
- 調整採樣間隔
- 配置記錄規則
- 啟用遠程寫入

#### Grafana優化
- 啟用緩存
- 調整查詢超時
- 優化儀表板查詢
- 使用數據源代理

## 擴展和集成

### 添加新指標
1. 在應用中集成Prometheus客戶端
2. 定義自定義指標
3. 更新Prometheus配置
4. 創建Grafana儀表板

### 集成第三方監控
- New Relic
- DataDog
- CloudWatch
- Azure Monitor

### 高可用部署
- 多節点Prometheus集群
- Grafana高可用配置
- AlertManager联邦
- 外部存儲集成

## 安全考慮

- 🔐 啟用認證和授權
- 🔒 配置HTTPS/TLS
- 🛡️ 網絡隔離和防火牆
- 👤 用戶權限管理
- 📊 數據加密和隱私
- 🔍 審計日誌和合規

## 支持和文檔

- 📖 [完整文檔](docs/)
- 🐛 [問題報告](issues/)
- 💬 [社區討論](discussions/)
- 📧 [技術支持](mailto:support@quantitative-trading.com)

---

**版本**: 1.0.0
**更新時間**: $(date)
**維護者**: 量化交易團隊
"""

        doc_path = self.deployment_dir / "DEPLOYMENT_GUIDE.md"
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)

        print(f"✅ 部署文檔已生成: {doc_path}")
        return str(doc_path)

    def deploy_complete_system(self) -> bool:
        """
        完整部署監控系統

        Returns:
            bool: 是否部署成功
        """
        try:
            print("🚀 開始完整部署監控系統...")

            # 1. 檢查前置條件
            if not self.check_prerequisites():
                print("❌ 前置條件檢查失敗")
                return False

            # 2. 生成配置文件
            print("\n📝 生成配置文件...")
            self.generate_docker_compose()
            self.generate_dockerfile()
            self.generate_requirements()

            # 3. 生成部署腳本和文檔
            print("\n📝 生成部署腳本和文檔...")
            deploy_script = self.generate_deployment_script()
            doc_file = self.generate_documentation()

            # 4. 部署服務
            print("\n🚀 部署監控服務...")
            if not self.deploy_services():
                print("❌ 服務部署失敗")
                return False

            # 5. 驗證部署
            print("\n🔍 驗證部署...")
            if not self.verify_deployment():
                print("❌ 部署驗證失敗")
                return False

            # 6. 生成Grafana儀表板
            print("\n📊 生成Grafana儀表板...")
            from grafana_dashboards import GrafanaDashboardGenerator
            generator = GrafanaDashboardGenerator()
            generator.generate_all_dashboards()

            print("\n🎉 監控系統部署完成！")
            print("\n📋 部署摘要:")
            print(f"📁 部署目錄: {self.deployment_dir}")
            print(f"📄 部署腳本: {deploy_script}")
            print(f"📖 部署文檔: {doc_file}")
            print("\n🔗 訪問地址:")
            print("  📊 Prometheus: http://localhost:9090")
            print("  📈 Grafana: http://localhost:3000 (admin/admin123)")
            print("  🚨 AlertManager: http://localhost:9093")
            print("\n🛠️ 管理命令:")
            print(f"  cd {self.deployment_dir}")
            print("  ./deploy_monitoring.sh {start|stop|restart|status|logs}")

            return True

        except Exception as e:
            print(f"❌ 部署失敗: {e}")
            logger.error(f"Deployment failed: {e}", exc_info=True)
            return False

if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 創建部署器
    deployer = MonitoringSystemDeployer()

    # 執行完整部署
    success = deployer.deploy_complete_system()

    if success:
        print("\n✅ 監控系統部署成功！")
        sys.exit(0)
    else:
        print("\n❌ 監控系統部署失敗！")
        sys.exit(1)