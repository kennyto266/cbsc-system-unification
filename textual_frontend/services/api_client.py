"""
多进程回测 API 通信的客户端类
=======================================

功能：
- 提交批量回测任务
- 查询任务状态和进度
- 获取回测结果
- 取消运行中的任务
- 获取系统健康状态

Author: CBSC Quant Team
Version: 1.0.0
"""

import logging
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class APIClient:
    """
    API 客户端类

    功能：
    - 提交批量回测任务
    - 查询任务状态和进度
    - 获取回测结果
    - 取消运行中的任务
    - 获取系统健康状态
    """

    def __init__(self, base_url: str = "http://localhost:3007", timeout: int = 30):
        """
        初始化 API 客户端

        Args:
            base_url: API 基础地址
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()

    async def submit_batch_backtest(
        self,
        configs: List[Dict[str, Any]],
        parallel_level: str = "strategy",
        max_workers: int = 4,
        max_concurrent: Optional[int] = None,
        enable_auto_scaling: bool = True,
        save_results: bool = True,
        generate_report: bool = False,
    ) -> Dict[str, Any]:
        """
        提交批量回测任务

        Args:
            configs: 回测配置列表
            parallel_level: 并行级别 ('strategy', 'symbol', 'parameter', 'hybrid')
            max_workers: 最大工作进程数
            max_concurrent: 最大并发数（None = max_workers）
            enable_auto_scaling: 是否启用自动扩容
            save_results: 是否保存结果到数据库
            generate_report: 是否生成报告

        Returns:
            API响应数据
        """
        try:
            url = f"{self.base_url}/api/v1/backtest/multiprocess/batch"

            request_data = {
                "backtest_configs": configs,
                "parallel_level": parallel_level,
                "max_workers": max_workers,
                "max_concurrent": max_concurrent or max_workers,
                "enable_auto_scaling": enable_auto_scaling,
                "save_results": save_results,
                "generate_report": generate_report,
            }

            response = await self.client.post(
                url, json=request_data, headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise Exception(f"API请求超时")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise Exception(f"HTTP 错误: {e}")

        except Exception as e:
            logger.error(f"API请求失败: {e}")
            raise Exception(f"API请求失败: {e}")

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询任务状态和进度

        Args:
            task_id: 任务ID

        Returns:
            任务状态数据
        """
        try:
            url = f"{self.base_url}/api/v1/backtest/multiprocess/status/{task_id}"

            response = await self.client.get(url)
            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise Exception(f"API请求超时")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise Exception(f"HTTP 错误: {e}")

        except Exception as e:
            logger.error(f"API请求失败: {e}")
            raise Exception(f"API请求失败: {e}")

    async def get_backtest_results(self, task_id: str) -> Dict[str, Any]:
        """
        获取回测结果

        Args:
            task_id: 任务ID

        Returns:
            回测结果数据
        """
        try:
            url = f"{self.base_url}/api/v1/backtest/multiprocess/results/{task_id}"

            response = await self.client.get(url)
            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise Exception(f"API请求超时")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise Exception(f"HTTP 错误: {e}")

        except Exception as e:
            logger.error(f"API请求失败: {e}")
            raise Exception(f"API请求失败: {e}")

    async def cancel_backtest(self, task_id: str) -> Dict[str, Any]:
        """
        取消回测任务

        Args:
            task_id: 任务ID

        Returns:
            API响应数据
        """
        try:
            url = f"{self.base_url}/api/v1/backtest/multiprocess/cancel/{task_id}"

            response = await self.client.delete(url)
            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise Exception(f"API请求超时")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise Exception(f"HTTP 错误: {e}")

        except Exception as e:
            logger.error(f"API请求失败: {e}")
            raise Exception(f"API请求失败: {e}")

    async def get_health(self) -> Dict[str, Any]:
        """
        获取系统健康状态

        Returns:
            系统状态数据
        """
        try:
            url = f"{self.base_url}/api/v1/backtest/multiprocess/health"

            response = await self.client.get(url)
            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise Exception(f"API请求超时")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise Exception(f"HTTP 错误: {e}")

        except Exception as e:
            logger.error(f"API请求失败: {e}")
            raise Exception(f"API请求失败: {e}")

    async def get_strategies(self) -> List[Dict[str, Any]]:
        """
        获取策略列表

        Returns:
            策略列表
        """
        try:
            url = f"{self.base_url}/api/v1/strategies"

            response = await self.client.get(url)
            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise Exception(f"API请求超时")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise Exception(f"HTTP 错误: {e}")

        except Exception as e:
            logger.error(f"API请求失败: {e}")
            raise Exception(f"API请求失败: {e}")

    async def create_strategy(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建策略

        Args:
            strategy_data: 策略数据

        Returns:
            创建的策略数据
        """
        try:
            url = f"{self.base_url}/api/v1/strategies"

            response = await self.client.post(
                url, json=strategy_data, headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise Exception(f"API请求超时")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise Exception(f"HTTP 错误: {e}")

        except Exception as e:
            logger.error(f"API请求失败: {e}")
            raise Exception(f"API请求失败: {e}")

    async def update_strategy(
        self, strategy_id: str, strategy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新策略

        Args:
            strategy_id: 策略ID
            strategy_data: 策略数据

        Returns:
            更新的策略数据
        """
        try:
            url = f"{self.base_url}/api/v1/strategies/{strategy_id}"

            response = await self.client.put(
                url, json=strategy_data, headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise Exception(f"API请求超时")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise Exception(f"HTTP 错误: {e}")

        except Exception as e:
            logger.error(f"API请求失败: {e}")
            raise Exception(f"API请求失败: {e}")

    async def delete_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """
        删除策略

        Args:
            strategy_id: 策略ID

        Returns:
            删除响应数据
        """
        try:
            url = f"{self.base_url}/api/v1/strategies/{strategy_id}"

            response = await self.client.delete(url)
            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise Exception(f"API请求超时")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise Exception(f"HTTP 错误: {e}")

        except Exception as e:
            logger.error(f"API请求失败: {e}")
            raise Exception(f"API请求失败: {e}")
