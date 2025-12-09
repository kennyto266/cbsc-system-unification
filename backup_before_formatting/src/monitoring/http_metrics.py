"""
HTTP監控端點

提供Prometheus指標暴露端點，用於監控HTTP客戶端性能
"""

import logging
from typing import Any, Dict

from aiohttp import ClientSession, web
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    exposition,
    generate_latest,
    multiprocess,
)

logger = logging.getLogger(__name__)


async def metrics_handler(request: web.Request) -> web.Response:
    """
    Prometheus /metrics端點處理器

    Args:
        request: AIOHTTP請求對象

    Returns:
        包含Prometheus指標的響應
    """
    try:
        # 生成Prometheus指標
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)

        # 如果沒有多進程，使用默認registry
        data = generate_latest(registry)

        logger.debug("Metrics endpoint accessed successfully")
        return web.Response(body=data, content_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return web.Response(status=500, text=f"Error generating metrics: {e}")


async def health_check_handler(request: web.Request) -> web.Response:
    """
    健康檢查端點

    Args:
        request: AIOHTTP請求對象

    Returns:
        健康檢查響應
    """
    try:
        # 簡單的健康檢查
        return web.json_response(
            {
                "status": "healthy",
                "service": "http - client",
                "version": "1.0.0",
                "timestamp": web.web_request.Application.router.__str__(),
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.json_response({"status": "unhealthy", "error": str(e)}, status=500)


def create_monitoring_app() -> web.Application:
    """
    創建監控應用

    Returns:
        AIOHTTP應用實例
    """
    app = web.Application()

    # 添加路由
    app.router.add_get("/metrics", metrics_handler)
    app.router.add_get("/health", health_check_handler)

    logger.info("Monitoring routes configured: /metrics, /health")
    return app


async def start_monitoring_server(
    port: int = 8000, host: str = "0.0.0.0"
) -> web.AppRunner:
    """
    啟動監控服務器

    Args:
        port: 監控端口
        host: 監控主機

    Returns:
        AIOHTTP應用運行器
    """
    app = create_monitoring_app()
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info(f"Monitoring server started on {host}:{port}")
    logger.info(f"Metrics available at http://{host}:{port}/metrics")
    logger.info(f"Health check available at http://{host}:{port}/health")

    return runner


def setup_monitoring_routes(app: web.Application) -> None:
    """
    為現有應用添加監控路由

    Args:
        app: AIOHTTP應用實例
    """
    app.router.add_get("/metrics", metrics_handler)
    app.router.add_get("/api / v1 / metrics", metrics_handler)  # 兼容老版本
    app.router.add_get("/health", health_check_handler)

    logger.info("Monitoring routes added to existing application")


async def get_http_metrics() -> Dict[str, Any]:
    """
    獲取HTTP指標（用於程序化訪問）

    Returns:
        HTTP指標字典
    """
    try:
        async with ClientSession() as session:
            async with session.get("http://localhost:8000 / metrics") as response:
                if response.status == 200:
                    data = await response.text()
                    return {"status": "success", "data": data}
                else:
                    return {"status": "error", "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    # 測試監控服務器
    import asyncio

    async def test():
        runner = await start_monitoring_server(port=8000)
        print("Monitoring server running. Press Ctrl + C to stop.")

        try:
            await asyncio.Future()  # 永久運行
        except KeyboardInterrupt:
            print("\nShutting down...")
            await runner.cleanup()

    asyncio.run(test())
