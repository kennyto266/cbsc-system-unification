#!/usr/bin/env python3
"""
策略API迁移脚本
Strategy API Migration Script

将旧版策略API适配到新架构，提供向后兼容性
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIMapper:
    """API映射器，将旧API请求映射到新API"""

    def __init__(self):
        # 旧API端点到新API端点的映射
        self.endpoint_mappings = {
            # 策略CRUD
            "GET /api/strategies": "GET /api/v2/strategies",
            "POST /api/strategies": "POST /api/v2/strategies",
            "GET /api/strategies/{strategy_id}": "GET /api/v2/strategies/{strategy_id}",
            "PUT /api/strategies/{strategy_id}": "PUT /api/v2/strategies/{strategy_id}",
            "DELETE /api/strategies/{strategy_id}": "DELETE /api/v2/strategies/{strategy_id}",

            # 策略执行
            "POST /api/strategies/{strategy_id}/execute": "POST /api/v2/strategies/{strategy_id}/execute",
            "GET /api/strategies/{strategy_id}/status": "GET /api/v2/strategies/{strategy_id}/executions/{execution_id}/status",
            "POST /api/strategies/{strategy_id}/stop": "POST /api/v2/strategies/{strategy_id}/stop",

            # 策略模板
            "GET /api/strategies/templates": "GET /api/v2/strategies/templates/list",

            # 批量操作
            "POST /api/strategies/batch": "POST /api/v2/strategies/batch",
        }

        # 请求参数映射
        self.parameter_mappings = {
            # 分页参数
            "offset": "page",
            "limit": "page_size",
            "type": "strategy_type",
        }

        # 响应格式转换器
        self.response_transformers = {
            "strategy_list": self._transform_strategy_list,
            "strategy_detail": self._transform_strategy_detail,
            "execution_status": self._transform_execution_status,
        }

    async def map_request(self, old_endpoint: str, old_params: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        映射旧API请求到新API

        Args:
            old_endpoint: 旧API端点
            old_params: 旧API参数

        Returns:
            (新端点, 新参数)
        """
        # 查找新端点
        new_endpoint = self.endpoint_mappings.get(old_endpoint)
        if not new_endpoint:
            raise ValueError(f"未找到端点映射: {old_endpoint}")

        # 转换参数
        new_params = {}
        for old_key, value in old_params.items():
            new_key = self.parameter_mappings.get(old_key, old_key)
            new_params[new_key] = value

        # 特殊处理
        if "page" in new_params and "page_size" in new_params:
            # 将offset转换为page
            if "offset" in old_params:
                page_size = new_params["page_size"]
                offset = old_params["offset"]
                new_params["page"] = (offset // page_size) + 1

        return new_endpoint, new_params

    async def transform_response(self, old_endpoint: str, new_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换新API响应到旧API格式

        Args:
            old_endpoint: 旧API端点
            new_response: 新API响应

        Returns:
            旧格式的响应
        """
        # 确定响应类型
        response_type = self._get_response_type(old_endpoint)

        # 应用转换器
        transformer = self.response_transformers.get(response_type)
        if transformer:
            return transformer(new_response)

        # 默认转换
        return self._default_transform(new_response)

    def _get_response_type(self, endpoint: str) -> str:
        """获取响应类型"""
        if "strategies" in endpoint and endpoint.endswith("/strategies"):
            return "strategy_list"
        elif "{strategy_id}" in endpoint and endpoint.endswith("/strategies/{strategy_id}"):
            return "strategy_detail"
        elif "status" in endpoint:
            return "execution_status"
        return "default"

    def _transform_strategy_list(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """转换策略列表响应"""
        data = response.get("data", {})

        # 提取分页信息
        pagination = data.get("pagination", {})
        items = data.get("items", [])

        return {
            "success": response.get("success", True),
            "data": items,
            "pagination": {
                "total": pagination.get("total", 0),
                "offset": (pagination.get("page", 1) - 1) * pagination.get("page_size", 20),
                "limit": pagination.get("page_size", 20)
            },
            "message": response.get("message", "操作成功")
        }

    def _transform_strategy_detail(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """转换策略详情响应"""
        data = response.get("data", {})

        # 展平嵌套的策略数据
        strategy = data.get("strategy", {})
        if "performance_summary" in strategy:
            strategy["performance"] = strategy.pop("performance_summary")

        return {
            "success": response.get("success", True),
            "data": strategy,
            "message": response.get("message", "获取策略详情成功")
        }

    def _transform_execution_status(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """转换执行状态响应"""
        data = response.get("data", {})

        return {
            "success": response.get("success", True),
            "execution_id": data.get("execution_id"),
            "strategy_id": data.get("strategy_id"),
            "status": data.get("status"),
            "progress": data.get("progress", 0),
            "message": response.get("message", "获取执行状态成功")
        }

    def _default_transform(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """默认响应转换"""
        return {
            "success": response.get("success", True),
            "data": response.get("data"),
            "message": response.get("message", "操作成功")
        }


class APIAdapter:
    """API适配器，提供旧API的向后兼容性"""

    def __init__(self):
        self.mapper = APIMapper()
        self.migration_log = []

    async def handle_request(
        self,
        old_endpoint: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理旧API请求

        Args:
            old_endpoint: 旧API端点
            method: HTTP方法
            params: 查询参数
            body: 请求体

        Returns:
            旧格式的响应
        """
        start_time = datetime.now()

        try:
            # 记录请求
            self._log_request(old_endpoint, method, params, body)

            # 映射到新API
            new_endpoint, new_params = await self.mapper.map_request(
                f"{method} {old_endpoint}",
                params or {}
            )

            logger.info(f"映射请求: {old_endpoint} -> {new_endpoint}")

            # 这里应该调用新API
            # 简化实现，返回模拟响应
            new_response = await self._call_new_api(new_endpoint, method, new_params, body)

            # 转换响应格式
            old_response = await self.mapper.transform_response(
                f"{method} {old_endpoint}",
                new_response
            )

            # 记录成功
            self._log_success(old_endpoint, start_time)

            return old_response

        except Exception as e:
            # 记录错误
            self._log_error(old_endpoint, e, start_time)

            # 返回错误响应
            return {
                "success": False,
                "error": str(e),
                "message": "请求处理失败"
            }

    async def _call_new_api(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any],
        body: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """调用新API（简化实现）"""
        # 这里应该实现实际的新API调用
        # 暂时返回模拟响应

        if "strategies" in endpoint and method == "GET":
            return {
                "success": True,
                "data": {
                    "pagination": {
                        "total": 100,
                        "page": params.get("page", 1),
                        "page_size": params.get("page_size", 20)
                    },
                    "items": [
                        {
                            "id": "strategy_1",
                            "name": "示例策略",
                            "type": "RSI",
                            "status": "active"
                        }
                    ]
                },
                "message": "获取成功"
            }

        return {
            "success": True,
            "data": None,
            "message": "操作成功"
        }

    def _log_request(self, endpoint: str, method: str, params: Any, body: Any):
        """记录请求"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "endpoint": endpoint,
            "method": method,
            "params": params,
            "body": body
        }
        self.migration_log.append(log_entry)
        logger.info(f"记录请求: {log_entry}")

    def _log_success(self, endpoint: str, start_time: datetime):
        """记录成功"""
        duration = (datetime.now() - start_time).total_seconds()
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "success",
            "endpoint": endpoint,
            "duration_ms": duration * 1000
        }
        self.migration_log.append(log_entry)
        logger.info(f"请求成功: {endpoint}, 耗时: {duration:.3f}s")

    def _log_error(self, endpoint: str, error: Exception, start_time: datetime):
        """记录错误"""
        duration = (datetime.now() - start_time).total_seconds()
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "endpoint": endpoint,
            "error": str(error),
            "duration_ms": duration * 1000
        }
        self.migration_log.append(log_entry)
        logger.error(f"请求失败: {endpoint}, 错误: {error}, 耗时: {duration:.3f}s")

    def get_migration_stats(self) -> Dict[str, Any]:
        """获取迁移统计信息"""
        total_requests = len(self.migration_log)
        successful_requests = len([e for e in self.migration_log if e["type"] == "success"])
        error_requests = len([e for e in self.migration_log if e["type"] == "error"])

        avg_duration = 0
        if self.migration_log:
            durations = [e.get("duration_ms", 0) for e in self.migration_log if "duration_ms" in e]
            avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "error_requests": error_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "average_duration_ms": avg_duration
        }

    def export_migration_log(self, filename: str = None):
        """导出迁移日志"""
        if not filename:
            filename = f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.migration_log, f, ensure_ascii=False, indent=2)

        logger.info(f"迁移日志已导出到: {filename}")


async def main():
    """主函数，运行迁移示例"""
    adapter = APIAdapter()

    # 测试示例请求
    test_requests = [
        {
            "endpoint": "/api/strategies",
            "method": "GET",
            "params": {"offset": 0, "limit": 10, "type": "RSI"}
        },
        {
            "endpoint": "/api/strategies/strategy_123",
            "method": "GET",
            "params": {}
        },
        {
            "endpoint": "/api/strategies/strategy_123/execute",
            "method": "POST",
            "body": {"execution_mode": "backtest"}
        }
    ]

    # 处理测试请求
    for req in test_requests:
        response = await adapter.handle_request(
            old_endpoint=req["endpoint"],
            method=req["method"],
            params=req.get("params"),
            body=req.get("body")
        )
        print(f"\n请求: {req['method']} {req['endpoint']}")
        print(f"响应: {json.dumps(response, ensure_ascii=False, indent=2)}")

    # 输出统计信息
    stats = adapter.get_migration_stats()
    print(f"\n迁移统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")

    # 导出日志
    adapter.export_migration_log()


if __name__ == "__main__":
    asyncio.run(main())