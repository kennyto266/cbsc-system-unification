from fastapi import FastAPI, APIRouter
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any
import json
import os
import logging

logger = logging.getLogger('quant_system')

class EnhancedAPIDocs:
    """增强的API文档生成器"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.custom_openapi_schema = None

    def generate_enhanced_openapi(self) -> Dict[str, Any]:
        """生成增强的OpenAPI规范"""
        if self.custom_openapi_schema:
            return self.custom_openapi_schema

        # 获取基础OpenAPI规范
        openapi_schema = get_openapi(
            title=self.app.title,
            version=self.app.version,
            description=self.app.description,
            routes=self.app.routes,
        )

        # 增强规范
        openapi_schema.update({
            "info": {
                "title": "CODEX-- 量化交易系统 API",
                "version": "2.0.0",
                "description": """
                企业级量化交易分析系统API

                ## 功能特性
                - 实时股票数据分析
                - 多策略回测引擎
                - 机器学习预测模型
                - WebSocket实时数据推送
                - 完整的监控和指标收集

                ## 认证
                大部分API端点需要JWT令牌认证。

                ## 限流
                API有速率限制保护，请合理使用。
                """,
                "contact": {
                    "name": "CODEX-- Team",
                    "email": "support@codex-quant.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": os.getenv('API_BASE_URL', 'http://localhost:8001'),
                    "description": "主服务器"
                },
                {
                    "url": "https://api.codex-quant.com",
                    "description": "生产服务器"
                }
            ],
            "security": [
                {"BearerAuth": []}
            ],
            "components": {
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "输入JWT令牌进行认证"
                    }
                },
                "schemas": {
                    "StockData": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "example": "AAPL"},
                            "price": {"type": "number", "example": 150.25},
                            "change": {"type": "number", "example": 2.5},
                            "change_percent": {"type": "number", "example": 1.69},
                            "volume": {"type": "integer", "example": 1000000}
                        }
                    },
                    "StrategySignal": {
                        "type": "object",
                        "properties": {
                            "strategy_name": {"type": "string", "example": "SMA_Crossover"},
                            "signal_type": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
                            "confidence": {"type": "number", "example": 0.85}
                        }
                    },
                    "ErrorResponse": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"},
                            "message": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    }
                }
            },
            "tags": [
                {
                    "name": "股票分析",
                    "description": "股票技术分析和基本面分析"
                },
                {
                    "name": "策略回测",
                    "description": "量化策略开发和回测"
                },
                {
                    "name": "机器学习",
                    "description": "AI模型训练和预测"
                },
                {
                    "name": "实时数据",
                    "description": "WebSocket实时数据流"
                },
                {
                    "name": "系统监控",
                    "description": "系统状态和性能监控"
                },
                {
                    "name": "用户管理",
                    "description": "用户认证和权限管理"
                }
            ]
        })

        # 添加限流信息到响应头
        for path_data in openapi_schema.get("paths", {}).values():
            for operation_data in path_data.values():
                if isinstance(operation_data, dict):
                    operation_data.setdefault("responses", {}).setdefault("429", {
                        "description": "Too Many Requests - 速率限制",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    })

        self.custom_openapi_schema = openapi_schema
        return openapi_schema

    def get_swagger_ui_html(self, **kwargs):
        """获取增强的Swagger UI"""
        return get_swagger_ui_html(
            openapi_url=self.app.openapi_url,
            title="CODEX-- API 文档 - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            **kwargs
        )

    def get_redoc_html(self, **kwargs):
        """获取增强的ReDoc"""
        return get_redoc_html(
            openapi_url=self.app.openapi_url,
            title="CODEX-- API 文档 - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            **kwargs
        )

    def export_openapi_json(self, filepath: str):
        """导出OpenAPI规范为JSON文件"""
        schema = self.generate_enhanced_openapi()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        logger.info(f"OpenAPI schema exported to {filepath}")

    def export_openapi_yaml(self, filepath: str):
        """导出OpenAPI规范为YAML文件"""
        try:
            import yaml
            schema = self.generate_enhanced_openapi()
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(schema, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"OpenAPI schema exported to {filepath}")
        except ImportError:
            logger.warning("PyYAML not installed, YAML export not available")

def create_api_docs_router() -> APIRouter:
    """创建API文档路由"""
    router = APIRouter()

    @router.get("/docs", include_in_schema=False)
    async def swagger_ui_html():
        """Swagger UI文档"""
        from src.api_docs import EnhancedAPIDocs
        # 这里需要获取app实例，实际使用时需要传入
        return {"message": "Use main app for docs"}

    @router.get("/redoc", include_in_schema=False)
    async def redoc_html():
        """ReDoc文档"""
        return {"message": "Use main app for redoc"}

    @router.get("/openapi.json", include_in_schema=False)
    async def get_openapi_json():
        """OpenAPI JSON规范"""
        return {"message": "Use main app for openapi"}

    return router

# 使用示例
"""
from fastapi import FastAPI
from src.api_docs import EnhancedAPIDocs

app = FastAPI(title="Quant System", version="2.0.0")

# 初始化增强文档
api_docs = EnhancedAPIDocs(app)

# 设置自定义OpenAPI schema
app.openapi = api_docs.generate_enhanced_openapi

# 添加文档路由
app.include_router(create_api_docs_router())
"""