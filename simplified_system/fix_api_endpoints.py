#!/usr / bin / env python3
"""
API端点修复工具
修复HKMA政府数据API的配置问题
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

import requests

# Setup logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class APIEndpointFixer:
    """API端点修复器"""

    def __init__(self):
        self.correct_endpoints = {
            # 经过验证的正确HKMA API端点
            "hibor_rates": {
                "primary": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / hk - interbank - ir - daily",
                "alternative": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - interbank - liquidity",
                "params": {"lang": "en", "limit": "100"},
                "headers": {
                    "Accept": "application / json",
                    "User - Agent": "Mozilla / 5.0 (compatible; QuantSystem / 1.0)",
                },
            },
            "exchange_rates": {
                "primary": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / er - eeri - daily",
                "alternative": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - monetary - base",
                "params": {"lang": "en", "limit": "100"},
                "headers": {"Accept": "application / json"},
            },
            "monetary_base": {
                "primary": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - monetary - base",
                "alternative": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / mo / mo - dm - mb",
                "params": {"lang": "en", "limit": "100"},
                "headers": {"Accept": "application / json"},
            },
            "liquidity": {
                "primary": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - interbank - liquidity",
                "params": {"lang": "en", "limit": "100"},
                "headers": {"Accept": "application / json"},
            },
            "efbn": {
                "primary": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - indicative - price",
                "params": {"lang": "en", "limit": "100"},
                "headers": {"Accept": "application / json"},
            },
        }

    def test_endpoint(self, endpoint_config: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个API端点"""
        results = {"primary": None, "alternative": None, "working": None}

        # 测试主要端点
        if "primary" in endpoint_config:
            try:
                logger.info(f"Testing primary endpoint: {endpoint_config['primary']}")
                response = requests.get(
                    endpoint_config["primary"],
                    params = endpoint_config.get("params", {}),
                    headers = endpoint_config.get("headers", {}),
                    timeout = 30,
                )

                if response.status_code == 200:
                    data = response.json()
                    results["primary"] = {
                        "status": "success",
                        "status_code": response.status_code,
                        "data_keys": (
                            list(data.keys()) if isinstance(data, dict) else "non_dict"
                        ),
                        "response_time": response.elapsed.total_seconds(),
                    }
                    results["working"] = "primary"
                    logger.info(f"Primary endpoint SUCCESS: {response.status_code}")
                else:
                    results["primary"] = {
                        "status": "failed",
                        "status_code": response.status_code,
                        "error": response.text[:200],
                        "response_time": response.elapsed.total_seconds(),
                    }
                    logger.warning(f"Primary endpoint FAILED: {response.status_code}")

            except Exception as e:
                results["primary"] = {
                    "status": "error",
                    "error": str(e),
                    "response_time": None,
                }
                logger.error(f"Primary endpoint ERROR: {e}")

        # 测试备用端点
        if "alternative" in endpoint_config:
            try:
                logger.info(
                    f"Testing alternative endpoint: {endpoint_config['alternative']}"
                )
                response = requests.get(
                    endpoint_config["alternative"],
                    params = endpoint_config.get("params", {}),
                    headers = endpoint_config.get("headers", {}),
                    timeout = 30,
                )

                if response.status_code == 200:
                    data = response.json()
                    results["alternative"] = {
                        "status": "success",
                        "status_code": response.status_code,
                        "data_keys": (
                            list(data.keys()) if isinstance(data, dict) else "non_dict"
                        ),
                        "response_time": response.elapsed.total_seconds(),
                    }
                    if results["working"] is None:
                        results["working"] = "alternative"
                    logger.info(f"Alternative endpoint SUCCESS: {response.status_code}")
                else:
                    results["alternative"] = {
                        "status": "failed",
                        "status_code": response.status_code,
                        "error": response.text[:200],
                        "response_time": response.elapsed.total_seconds(),
                    }
                    logger.warning(
                        f"Alternative endpoint FAILED: {response.status_code}"
                    )

            except Exception as e:
                results["alternative"] = {
                    "status": "error",
                    "error": str(e),
                    "response_time": None,
                }
                logger.error(f"Alternative endpoint ERROR: {e}")

        return results

    def test_all_endpoints(self) -> Dict[str, Any]:
        """测试所有API端点"""
        logger.info("开始测试所有HKMA API端点...")

        test_results = {}
        working_endpoints = 0
        total_endpoints = len(self.correct_endpoints)

        for data_type, endpoint_config in self.correct_endpoints.items():
            logger.info(f"\n=== 测试 {data_type} 端点 ===")
            results = self.test_endpoint(endpoint_config)
            test_results[data_type] = results

            if results["working"] is not None:
                working_endpoints += 1
                logger.info(f"✅ {data_type}: 工作端点 ({results['working']})")
            else:
                logger.error(f"❌ {data_type}: 无可用端点")

        success_rate = working_endpoints / total_endpoints
        logger.info(f"\n=== 测试总结 ===")
        logger.info(
            f"可用端点: {working_endpoints}/{total_endpoints} ({success_rate:.1%})"
        )

        return {
            "summary": {
                "total_endpoints": total_endpoints,
                "working_endpoints": working_endpoints,
                "success_rate": success_rate,
                "test_timestamp": datetime.now().isoformat(),
            },
            "detailed_results": test_results,
        }

    def generate_fixed_config(self, test_results: Dict[str, Any]) -> str:
        """生成修复后的配置文件"""
        config = {
            "hkma_api_config": {
                "version": "2.0",
                "updated": datetime.now().isoformat(),
                "base_settings": {
                    "timeout": 30,
                    "retry_count": 3,
                    "retry_delay": 1,
                    "default_params": {"lang": "en", "limit": "100"},
                    "default_headers": {
                        "Accept": "application / json",
                        "User - Agent": "Mozilla / 5.0 (compatible; QuantSystem / 1.0)",
                    },
                },
                "endpoints": {},
            }
        }

        for data_type, results in test_results["detailed_results"].items():
            endpoint_info = {
                "data_type": data_type,
                "status": "working" if results["working"] else "failed",
                "working_endpoint": results["working"],
            }

            # 添加可用端点配置
            if results["primary"] and results["primary"]["status"] == "success":
                endpoint_info["primary"] = {
                    "url": self.correct_endpoints[data_type]["primary"],
                    "params": self.correct_endpoints[data_type].get("params", {}),
                    "response_time": results["primary"].get("response_time", 0),
                    "data_keys": results["primary"].get("data_keys", []),
                }

            if results["alternative"] and results["alternative"]["status"] == "success":
                endpoint_info["alternative"] = {
                    "url": self.correct_endpoints[data_type]["alternative"],
                    "params": self.correct_endpoints[data_type].get("params", {}),
                    "response_time": results["alternative"].get("response_time", 0),
                    "data_keys": results["alternative"].get("data_keys", []),
                }

            config["hkma_api_config"]["endpoints"][data_type] = endpoint_info

        return json.dumps(config, indent = 2, ensure_ascii = False)

    def save_fixed_config(
        self, config_json: str, filename: str = "fixed_hkma_api_config.json"
    ):
        """保存修复后的配置"""
        try:
            with open(filename, "w", encoding="utf - 8") as f:
                f.write(config_json)
            logger.info(f"✅ 修复配置已保存到: {filename}")
            return True
        except Exception as e:
            logger.error(f"❌ 保存配置失败: {e}")
            return False


def main():
    """主函数"""
    print("=" * 60)
    print("HKMA API Endpoint Fix Tool")
    print("=" * 60)

    fixer = APIEndpointFixer()

    # 测试所有端点
    test_results = fixer.test_all_endpoints()

    # 显示测试结果
    print(f"\nTest Results:")
    print(f"Total Endpoints: {test_results['summary']['total_endpoints']}")
    print(f"Working Endpoints: {test_results['summary']['working_endpoints']}")
    print(f"Success Rate: {test_results['summary']['success_rate']:.1%}")

    print(f"\nDetailed Results:")
    for data_type, results in test_results["detailed_results"].items():
        status_icon = "OK" if results["working"] else "FAIL"
        print(f"{status_icon} {data_type}: {results['working'] or 'FAILED'}")

        if results["primary"]:
            primary_status = results["primary"]["status"]
            rt = results["primary"].get("response_time", 0)
            print(f"   Primary: {primary_status} ({rt:.2f}s)")

        if results["alternative"]:
            alt_status = results["alternative"]["status"]
            rt = results["alternative"].get("response_time", 0)
            print(f"   Alternative: {alt_status} ({rt:.2f}s)")

    # 生成修复配置
    if test_results["summary"]["working_endpoints"] > 0:
        print(f"\nGenerating fixed config...")
        fixed_config = fixer.generate_fixed_config(test_results)

        # 保存配置
        if fixer.save_fixed_config(fixed_config):
            print(f"Config file generated: fixed_hkma_api_config.json")

            # 提供下一步建议
            print(f"\nNext Steps:")
            print(
                f"1. Copy fixed_hkma_api_config.json to simplified_system / src / api / config/"
            )
            print(f"2. Update endpoint configuration in government_data.py")
            print(f"3. Re - run integration tests to verify fixes")
        else:
            print(f"Failed to save config file")
    else:
        print(f"\nNo working endpoints available, cannot generate fixed config")
        print(f"Please check network connection or contact system administrator")

    print(f"\n" + "=" * 60)
    print("API Endpoint Fix Complete")
    print("=" * 60)

    return test_results


if __name__ == "__main__":
    results = main()
