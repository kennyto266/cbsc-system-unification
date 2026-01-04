#!/usr/bin/env python3
"""
CBS-C Trading Strategy Management System - System Launcher
啟動整個CBS-C量化交易策略管理系統
"""

import os
import sys
import time
import subprocess
import signal
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
import requests
from datetime import datetime

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cbsc_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('CBSC-Launcher')

class CMBSystemLauncher:
    """CBS-C系統啟動器"""

    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.project_root = project_root
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """加載系統配置"""
        config_file = self.project_root / "system_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 默認配置
        return {
            "services": {
                "database": {
                    "enabled": True,
                    "port": 5432,
                    "check_url": "http://localhost:5432"
                },
                "redis": {
                    "enabled": True,
                    "port": 6379,
                    "check_url": "http://localhost:6379"
                },
                "backend": {
                    "enabled": True,
                    "port": 3004,
                    "check_url": "http://localhost:3004/health",
                    "command": ["python", "-m", "uvicorn", "main:app", "--reload", "--port", "3004"],
                    "cwd": "src/api"
                },
                "frontend": {
                    "enabled": True,
                    "port": 3000,
                    "check_url": "http://localhost:3000",
                    "command": ["npm", "run", "dev"],
                    "cwd": "frontend",
                    "env": {"PORT": "3000"}
                },
                "monitoring": {
                    "enabled": True,
                    "port": 3001,
                    "check_url": "http://localhost:3001",
                    "command": ["python", "app.py"],
                    "cwd": "monitoring"
                },
                "influxdb": {
                    "enabled": False,
                    "port": 8086,
                    "check_url": "http://localhost:8086/ping"
                }
            },
            "startup_order": ["database", "redis", "backend", "frontend", "monitoring", "influxdb"],
            "health_check_interval": 5,
            "max_retries": 30
        }

    def check_service_health(self, service_name: str, service_config: Dict) -> bool:
        """檢查服務健康狀態"""
        if not service_config.get("check_url"):
            return True

        try:
            response = requests.get(
                service_config["check_url"],
                timeout=5,
                verify=False
            )
            return response.status_code < 500
        except:
            return False

    def start_service(self, service_name: str) -> bool:
        """啟動單個服務"""
        if service_name not in self.config["services"]:
            logger.error(f"未知的服務: {service_name}")
            return False

        service_config = self.config["services"][service_name]

        if not service_config.get("enabled", True):
            logger.info(f"服務 {service_name} 已禁用，跳過啟動")
            return True

        logger.info(f"啟動服務: {service_name}")

        # 檢查端口是否已被占用
        if "port" in service_config:
            if self.is_port_in_use(service_config["port"]):
                logger.warning(f"端口 {service_config['port']} 已被占用，檢查是否是 {service_name} 服務")
                if self.check_service_health(service_name, service_config):
                    logger.info(f"服務 {service_name} 已在運行")
                    return True
                else:
                    logger.error(f"端口 {service_config['port']} 被其他進程占用")
                    return False

        # 啟動服務
        if "command" in service_config:
            cwd = self.project_root / service_config.get("cwd", "")
            env = os.environ.copy()
            if "env" in service_config:
                env.update(service_config["env"])

            try:
                process = subprocess.Popen(
                    service_config["command"],
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                self.processes[service_name] = process

                # 等待服務啟動
                retries = 0
                while retries < self.config["max_retries"]:
                    if self.check_service_health(service_name, service_config):
                        logger.info(f"✅ 服務 {service_name} 啟動成功")
                        return True

                    if process.poll() is not None:
                        stdout, stderr = process.communicate()
                        logger.error(f"❌ 服務 {service_name} 啟動失敗")
                        logger.error(f"STDOUT: {stdout}")
                        logger.error(f"STDERR: {stderr}")
                        return False

                    time.sleep(self.config["health_check_interval"])
                    retries += 1

                logger.error(f"❌ 服務 {service_name} 健康檢查超時")
                process.terminate()
                return False

            except Exception as e:
                logger.error(f"❌ 啟動服務 {service_name} 時發生錯誤: {str(e)}")
                return False
        else:
            # 對於沒有命令的服務（如外部數據庫），只做健康檢查
            if self.check_service_health(service_name, service_config):
                logger.info(f"✅ 服務 {service_name} 已可用")
                return True
            else:
                logger.warning(f"⚠️ 服務 {service_name} 不可用，請確保其已正確啟動")
                return True  # 不阻斷其他服務啟動

    def is_port_in_use(self, port: int) -> bool:
        """檢查端口是否被占用"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return False
            except:
                return True

    def start_all_services(self) -> bool:
        """按順序啟動所有服務"""
        logger.info("=" * 60)
        logger.info("CBS-C量化交易策略管理系統啟動中...")
        logger.info("=" * 60)

        start_time = time.time()

        # 註冊信號處理器
        def signal_handler(signum, frame):
            logger.info("\n收到中斷信號，正在停止所有服務...")
            self.stop_all_services()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 按順序啟動服務
        success_count = 0
        for service_name in self.config["startup_order"]:
            if self.start_service(service_name):
                success_count += 1
            else:
                logger.error(f"服務 {service_name} 啟動失敗，繼續啟動其他服務...")

        end_time = time.time()
        duration = end_time - start_time

        # 輸出啟動結果
        logger.info("=" * 60)
        logger.info(f"系統啟動完成！耗時: {duration:.2f}秒")
        logger.info("=" * 60)

        # 輸出服務狀態
        self.print_service_status()

        # 輸出訪問信息
        self.print_access_info()

        return success_count > 0

    def print_service_status(self):
        """打印所有服務狀態"""
        logger.info("\n📊 服務狀態:")
        for service_name, process in self.processes.items():
            if process.poll() is None:
                logger.info(f"  ✅ {service_name}: 運行中 (PID: {process.pid})")
            else:
                logger.error(f"  ❌ {service_name}: 已停止")

    def print_access_info(self):
        """打印訪問信息"""
        logger.info("\n🌐 系統訪問地址:")
        services = self.config["services"]

        if services["backend"]["enabled"]:
            logger.info(f"  • API服務: http://localhost:{services['backend']['port']}")
            logger.info(f"  • API文檔: http://localhost:{services['backend']['port']}/docs")
            logger.info(f"  • 健康檢查: http://localhost:{services['backend']['port']}/health")

        if services["frontend"]["enabled"]:
            logger.info(f"  • 前端界面: http://localhost:{services['frontend']['port']}")

        if services["monitoring"]["enabled"]:
            logger.info(f"  • 監控面板: http://localhost:{services['monitoring']['port']}")
            logger.info(f"  • Grafana: http://localhost:3001 (如果啟用)")
            logger.info(f"  • Prometheus: http://localhost:9090 (如果啟用)")

    def stop_all_services(self):
        """停止所有服務"""
        logger.info("\n正在停止所有服務...")
        for service_name, process in self.processes.items():
            if process.poll() is None:
                logger.info(f"停止服務: {service_name}")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"強制終止服務: {service_name}")
                    process.kill()
        logger.info("所有服務已停止")

    def run_system_checks(self):
        """運行系統檢查"""
        logger.info("\n🔍 運行系統檢查...")

        # 檢查Python版本
        python_version = sys.version.split()[0]
        logger.info(f"Python版本: {python_version}")

        # 檢查必要的依賴
        required_modules = ["fastapi", "uvicorn", "sqlalchemy", "redis"]
        for module in required_modules:
            try:
                __import__(module)
                logger.info(f"✅ {module} 已安裝")
            except ImportError:
                logger.error(f"❌ {module} 未安裝")

        # 檢查環境變量
        env_file = self.project_root / ".env"
        if env_file.exists():
            logger.info("✅ 找到.env配置文件")
        else:
            logger.warning("⚠️  未找到.env配置文件")

    def generate_startup_report(self):
        """生成啟動報告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "system_info": {
                "python_version": sys.version.split()[0],
                "platform": sys.platform
            }
        }

        for service_name, process in self.processes.items():
            report["services"][service_name] = {
                "status": "running" if process.poll() is None else "stopped",
                "pid": process.pid if process.poll() is None else None
            }

        report_file = self.project_root / "startup_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"\n📄 啟動報告已生成: {report_file}")

def main():
    """主函數"""
    print("\n" + "="*60)
    print("CBS-C 量化交易策略管理系統")
    print("Enhanced Trading Strategy Management System")
    print("="*60 + "\n")

    launcher = CMBSystemLauncher()

    # 運行系統檢查
    launcher.run_system_checks()

    # 啟動所有服務
    if launcher.start_all_services():
        # 生成啟動報告
        launcher.generate_startup_report()

        # 保持運行
        try:
            logger.info("\n系統運行中... 按 Ctrl+C 停止")
            while True:
                time.sleep(1)
                # 檢查關鍵服務是否還在運行
                for service_name, process in launcher.processes.items():
                    if process.poll() is not None:
                        logger.error(f"服務 {service_name} 已意外停止！")
        except KeyboardInterrupt:
            pass
    else:
        logger.error("系統啟動失敗")
        sys.exit(1)

    # 清理
    launcher.stop_all_services()

if __name__ == "__main__":
    main()