#!/usr/bin/env python3
"""
API維護和監控系統
API Maintenance and Monitoring System

專門解決政府API維護問題的完整解決方案
"""

import sys
import os
sys.path.append('src')

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
from dataclasses import dataclass
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_maintenance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class APIStatus(Enum):
    """API狀態枚舉"""
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

@dataclass
class APIHealthCheck:
    """API健康檢查結果"""
    endpoint_name: str
    url: str
    status: APIStatus
    response_time_ms: float
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    consecutive_failures: int
    data_quality_score: float
    error_message: Optional[str] = None

class APIMaintenanceMonitor:
    """API維護監控系統"""

    def __init__(self):
        self.health_checks: Dict[str, APIHealthCheck] = {}
        self.maintenance_schedule = {}
        self.alert_history = []
        self.performance_metrics = {}

        # 監控配置
        self.monitoring_config = {
            'health_check_interval_minutes': 30,
            'max_consecutive_failures': 5,
            'response_time_threshold_ms': 5000,
            'data_quality_threshold': 0.8,
            'alert_cooldown_minutes': 60
        }

        # API端點配置
        self.api_endpoints = {
            'hibor_primary': {
                'name': 'HIBOR主要端點',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ihb',
                'priority': 1
            },
            'exchange_primary': {
                'name': '匯率主要端點',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ex',
                'priority': 1
            },
            'monetary_primary': {
                'name': '貨幣基礎主要端點',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/mo/mo-dm-mb',
                'priority': 1
            },
            'hibor_alternative': {
                'name': 'HIBOR備選端點',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity',
                'priority': 2
            },
            'monetary_alternative': {
                'name': '貨幣基礎備選端點',
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base',
                'priority': 2
            }
        }

        # 初始化健康檢查
        self._initialize_health_checks()

        # 監控線程
        self.monitoring_thread = None
        self.is_monitoring = False

    def _initialize_health_checks(self):
        """初始化健康檢查記錄"""
        for endpoint_id, config in self.api_endpoints.items():
            self.health_checks[endpoint_id] = APIHealthCheck(
                endpoint_name=config['name'],
                url=config['url'],
                status=APIStatus.UNKNOWN,
                response_time_ms=0,
                last_success=None,
                last_failure=None,
                consecutive_failures=0,
                data_quality_score=0.0
            )

    def start_monitoring(self):
        """啟動監控"""
        if self.is_monitoring:
            logger.warning("監控已經在運行")
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("API維護監控已啟動")

    def stop_monitoring(self):
        """停止監控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        logger.info("API維護監控已停止")

    def _monitoring_loop(self):
        """監控循環"""
        logger.info("開始監控循環")

        while self.is_monitoring:
            try:
                self._perform_health_checks()
                self._analyze_health_status()
                self._check_for_alerts()

                # 等待下一次檢查
                time.sleep(self.monitoring_config['health_check_interval_minutes'] * 60)

            except Exception as e:
                logger.error(f"監控循環錯誤: {e}")
                time.sleep(60)  # 出錯時等待1分鐘再重試

    def _perform_health_checks(self):
        """執行健康檢查"""
        logger.info("執行API健康檢查...")

        for endpoint_id, health_check in self.health_checks.items():
            try:
                start_time = time.time()

                # 執行API請求
                response = requests.get(
                    health_check.url,
                    params={'pagesize': 1, 'page': 1},  # 只請求最少數據
                    timeout=10,
                    headers={'User-Agent': 'APIMonitor/1.0'}
                )

                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    # 請求成功
                    health_check.status = APIStatus.HEALTHY
                    health_check.response_time_ms = response_time
                    health_check.last_success = datetime.now()
                    health_check.consecutive_failures = 0

                    # 評估數據質量
                    data = response.json()
                    health_check.data_quality_score = self._assess_data_quality(data)

                    logger.info(f"{health_check.endpoint_name}: 健康 ({response_time:.0f}ms)")

                else:
                    # HTTP錯誤
                    self._handle_api_failure(health_check, f"HTTP {response.status_code}")

            except requests.exceptions.Timeout:
                self._handle_api_failure(health_check, "請求超時")

            except requests.exceptions.ConnectionError:
                self._handle_api_failure(health_check, "連接錯誤")

            except Exception as e:
                self._handle_api_failure(health_check, str(e))

    def _assess_data_quality(self, data: Dict) -> float:
        """評估數據質量"""
        try:
            score = 0.0

            # 檢查數據結構
            if 'records' in data or 'data' in data:
                score += 0.3

                # 檢查記錄數量
                records = data.get('records', []) or data.get('data', [])
                if len(records) > 0:
                    score += 0.3

                    # 檢查記錄質量
                    sample_record = records[0]
                    if isinstance(sample_record, dict) and len(sample_record) > 0:
                        score += 0.2

                        # 檢查關鍵字段
                        if any(key in sample_record for key in ['date', 'timestamp', 'value', 'rate']):
                            score += 0.2

            return min(1.0, score)

        except Exception:
            return 0.0

    def _handle_api_failure(self, health_check: APIHealthCheck, error_message: str):
        """處理API失敗"""
        health_check.status = APIStatus.WARNING if health_check.consecutive_failures < 3 else APIStatus.CRITICAL
        health_check.last_failure = datetime.now()
        health_check.consecutive_failures += 1
        health_check.error_message = error_message

        logger.warning(f"{health_check.endpoint_name}: 失敗 ({health_check.consecutive_failures}連續失敗) - {error_message}")

    def _analyze_health_status(self):
        """分析整體健康狀態"""
        total_endpoints = len(self.health_checks)
        healthy_endpoints = sum(1 for check in self.health_checks.values() if check.status == APIStatus.HEALTHY)
        critical_endpoints = sum(1 for check in self.health_checks.values() if check.status == APIStatus.CRITICAL)

        # 記錄性能指標
        self.performance_metrics = {
            'timestamp': datetime.now().isoformat(),
            'total_endpoints': total_endpoints,
            'healthy_endpoints': healthy_endpoints,
            'critical_endpoints': critical_endpoints,
            'overall_health_rate': healthy_endpoints / total_endpoints if total_endpoints > 0 else 0,
            'average_response_time': self._calculate_average_response_time(),
            'endpoints_with_failures': sum(1 for check in self.health_checks.values() if check.consecutive_failures > 0)
        }

        logger.info(f"健康狀態: {healthy_endpoints}/{total_endpoints} 端點健康, {critical_endpoints} 個嚴重")

    def _calculate_average_response_time(self) -> float:
        """計算平均響應時間"""
        response_times = [check.response_time_ms for check in self.health_checks.values() if check.response_time_ms > 0]
        return sum(response_times) / len(response_times) if response_times else 0

    def _check_for_alerts(self):
        """檢查是否需要發送警報"""
        current_time = datetime.now()

        for endpoint_id, health_check in self.health_checks.items():
            # 檢查嚴重狀態
            if health_check.status == APIStatus.CRITICAL:
                self._send_alert(f"CRITICAL: {health_check.endpoint_name} API處於嚴重狀態", health_check)

            # 檢查響應時間
            if health_check.response_time_ms > self.monitoring_config['response_time_threshold_ms']:
                self._send_alert(f"WARNING: {health_check.endpoint_name} API響應時間過長", health_check)

            # 檢查數據質量
            if health_check.data_quality_score < self.monitoring_config['data_quality_threshold']:
                self._send_alert(f"WARNING: {health_check.endpoint_name} API數據質量下降", health_check)

    def _send_alert(self, message: str, health_check: APIHealthCheck):
        """發送警報"""
        # 檢查冷卻時間
        current_time = datetime.now()
        recent_alerts = [
            alert for alert in self.alert_history
            if alert['endpoint_id'] == endpoint_id and
               (current_time - datetime.fromisoformat(alert['timestamp'])).total_seconds() < self.monitoring_config['alert_cooldown_minutes'] * 60
        ]

        if recent_alerts:
            return  # 在冷卻期內，不重複發送

        # 記錄警報
        alert = {
            'timestamp': current_time.isoformat(),
            'endpoint_id': endpoint_id,
            'endpoint_name': health_check.endpoint_name,
            'message': message,
            'status': health_check.status.value,
            'consecutive_failures': health_check.consecutive_failures,
            'response_time_ms': health_check.response_time_ms,
            'data_quality_score': health_check.data_quality_score
        }

        self.alert_history.append(alert)

        # 限制歷史記錄數量
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-500:]

        # 記錄警報日誌
        logger.warning(f"警報: {message}")

    def get_health_report(self) -> Dict[str, Any]:
        """獲取健康報告"""
        current_time = datetime.now()

        report = {
            'report_timestamp': current_time.isoformat(),
            'monitoring_config': self.monitoring_config,
            'overall_status': {
                'total_endpoints': len(self.health_checks),
                'healthy_count': sum(1 for check in self.health_checks.values() if check.status == APIStatus.HEALTHY),
                'warning_count': sum(1 for check in self.health_checks.values() if check.status == APIStatus.WARNING),
                'critical_count': sum(1 for check in self.health_checks.values() if check.status == APIStatus.CRITICAL),
                'health_rate': self.performance_metrics.get('overall_health_rate', 0),
                'monitoring_active': self.is_monitoring
            },
            'endpoint_details': {},
            'recent_alerts': self.alert_history[-10:],  # 最近10個警報
            'performance_summary': self.performance_metrics,
            'recommendations': self._generate_recommendations()
        }

        # 添加端點詳細信息
        for endpoint_id, health_check in self.health_checks.items():
            report['endpoint_details'][endpoint_id] = {
                'name': health_check.endpoint_name,
                'url': health_check.url,
                'status': health_check.status.value,
                'response_time_ms': health_check.response_time_ms,
                'consecutive_failures': health_check.consecutive_failures,
                'data_quality_score': health_check.data_quality_score,
                'last_success': health_check.last_success.isoformat() if health_check.last_success else None,
                'last_failure': health_check.last_failure.isoformat() if health_check.last_failure else None,
                'uptime_percentage': self._calculate_uptime_percentage(health_check)
            }

        return report

    def _calculate_uptime_percentage(self, health_check: APIHealthCheck) -> float:
        """計算運行時間百分比"""
        if not health_check.last_success:
            return 0.0

        # 假設我們過去24小時的監控數據
        monitoring_period = 24 * 60  # 分鐘
        check_interval = self.monitoring_config['health_check_interval_minutes']
        total_checks = monitoring_period / check_interval

        if total_checks <= 0:
            return 0.0

        # 計算成功率
        recent_failures = health_check.consecutive_failures
        successful_checks = max(0, total_checks - recent_failures)

        return successful_checks / total_checks

    def _generate_recommendations(self) -> List[str]:
        """生成維護建議"""
        recommendations = []

        # 分析整體狀態
        if self.performance_metrics.get('overall_health_rate', 0) < 0.8:
            recommendations.append("整體API健康率較低，建議檢查網絡連接和API端點配置")

        # 分析響應時間
        avg_response_time = self.performance_metrics.get('average_response_time', 0)
        if avg_response_time > 3000:  # 3秒
            recommendations.append(f"平均響應時間過長({avg_response_time:.0f}ms)，建議優化網絡或增加超時時間")

        # 分析失敗端點
        failing_endpoints = [
            endpoint_id for endpoint_id, check in self.health_checks.items()
            if check.consecutive_failures > 0
        ]

        if failing_endpoints:
            recommendations.append(f"以下端點存在連續失敗: {', '.join(failing_endpoints)}")

        # 分析數據質量
        low_quality_endpoints = [
            check.endpoint_name for check in self.health_checks.values()
            if check.data_quality_score < 0.7
        ]

        if low_quality_endpoints:
            recommendations.append(f"以下端點數據質量較低: {', '.join(low_quality_endpoints)}")

        # 通用建議
        if not recommendations:
            recommendations.append("所有API端點運行正常，建議繼續定期監控")
        else:
            recommendations.append("建議建立自動化恢復機制和通知系統")

        return recommendations

    def force_health_check(self, endpoint_id: Optional[str] = None):
        """強制執行健康檢查"""
        if endpoint_id:
            if endpoint_id in self.health_checks:
                logger.info(f"強制檢查端點: {endpoint_id}")
                self._check_single_endpoint(endpoint_id)
            else:
                logger.error(f"未知端點: {endpoint_id}")
        else:
            logger.info("強制檢查所有端點")
            self._perform_health_checks()

    def _check_single_endpoint(self, endpoint_id: str):
        """檢查單個端點"""
        health_check = self.health_checks[endpoint_id]

        try:
            start_time = time.time()
            response = requests.get(
                health_check.url,
                params={'pagesize': 1, 'page': 1},
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                health_check.status = APIStatus.HEALTHY
                health_check.response_time_ms = response_time
                health_check.last_success = datetime.now()
                health_check.consecutive_failures = 0
                logger.info(f"端點 {endpoint_id} 強制檢查成功")
            else:
                self._handle_api_failure(health_check, f"HTTP {response.status_code}")

        except Exception as e:
            self._handle_api_failure(health_check, str(e))
            logger.error(f"端點 {endpoint_id} 強制檢查失敗: {e}")

def main():
    """主函數"""
    print("啟動API維護監控系統...")
    print("=" * 60)

    monitor = APIMaintenanceMonitor()

    try:
        # 啟動監控
        print("\n1. 啟動監控服務...")
        monitor.start_monitoring()

        # 執行初始健康檢查
        print("\n2. 執行初始健康檢查...")
        monitor.force_health_check()

        # 等待檢查完成
        time.sleep(10)

        # 獲取健康報告
        print("\n3. 生成健康報告...")
        health_report = monitor.get_health_report()

        # 顯示報告摘要
        print("\n" + "=" * 60)
        print("API健康報告摘要")
        print("=" * 60)

        overall = health_report['overall_status']
        print(f"監控狀態: {'運行中' if overall['monitoring_active'] else '已停止'}")
        print(f"總端點數: {overall['total_endpoints']}")
        print(f"健康端點: {overall['healthy_count']}")
        print(f"警告端點: {overall['warning_count']}")
        print(f"嚴重端點: {overall['critical_count']}")
        print(f"健康率: {overall['health_rate']:.1%}")

        if health_report['performance_summary']:
            perf = health_report['performance_summary']
            print(f"平均響應時間: {perf.get('average_response_time', 0):.0f}ms")

        print("\n各端點狀態:")
        for endpoint_id, details in health_report['endpoint_details'].items():
            status = details['status']
            status_icon = "[OK]" if status == "HEALTHY" else "[WARN]" if status == "WARNING" else "[CRITICAL]"
            uptime = details['uptime_percentage']

            print(f"  {details['name']}: {status_icon}")
            print(f"    狀態: {status}")
            print(f"    運行率: {uptime:.1%}")
            print(f"    響應時間: {details['response_time_ms']:.0f}ms")
            print(f"    連續失敗: {details['consecutive_failures']}")

        print("\n維護建議:")
        recommendations = health_report['recommendations']
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

        if health_report['recent_alerts']:
            print(f"\n最近警報 ({len(health_report['recent_alerts'])} 個):")
            for alert in health_report['recent_alerts'][-3:]:  # 顯示最近3個
                timestamp = alert['timestamp'][:19]  # 只顯示到秒
                print(f"  {timestamp}: {alert['message']}")

        # 詢問是否保持監控運行
        print(f"\n監控服務正在運行中...")
        print("按 Ctrl+C 停止監控")

        # 保存報告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"api_health_report_{timestamp}.json"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(health_report, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n詳細報告已保存到: {report_file}")
        except Exception as e:
            print(f"\n報告保存失敗: {e}")

        # 保持運行直到用戶停止
        try:
            while True:
                time.sleep(60)
                # 每分鐘顯示一次狀態
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                overall = monitor.get_health_report()['overall_status']
                print(f"\r[{current_time}] 健康率: {overall['health_rate']:.1%} ({overall['healthy_count']}/{overall['total_endpoints']})", end='', flush=True)

        except KeyboardInterrupt:
            print("\n\n用戶停止監控")

    except Exception as e:
        logger.error(f"監控系統錯誤: {e}")
        print(f"\n錯誤: {e}")

    finally:
        # 停止監控
        monitor.stop_monitoring()
        print("\n監控服務已停止")

    return health_report

if __name__ == "__main__":
    health_report = main()