#!/usr / bin / env python3
"""
API文檔生成器
港股量化交易系統 - 自動化API文檔生成

從統一API網關自動生成標準化的API文檔，
包括OpenAPI規範、交互式文檔、SDK等。

主要功能:
- 生成OpenAPI 3.0規範
- 創建交互式API文檔
- 生成客戶端SDK
- 創建API使用示例
- 版本化文檔管理
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class OpenAPIGenerator:
    """OpenAPI規範生成器"""

    def __init__(self):
        self.openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "港股量化交易系統 API",
                "description": "企業級量化交易平台統一API接口",
                "version": "1.0.0",
                "contact": {
                    "name": "CODEX-- Team",
                    "email": "support@codex - quant.com",
                    "url": "https://codex - quant.com",
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org / licenses / MIT",
                },
            },
            "servers": [
                {"url": "http://localhost:7777", "description": "開發環境"},
                {"url": "https://api.codex - quant.com", "description": "生產環境"},
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "responses": {},
                "parameters": {},
                "examples": {},
                "requestBodies": {},
                "headers": {},
                "securitySchemes": {},
                "links": {},
                "callbacks": {},
            },
            "security": [],
            "tags": [],
        }

    def generate_spec(self, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """生成完整的OpenAPI規範"""
        # 添加標籤
        self._add_tags()

        # 添加安全方案
        self._add_security_schemes()

        # 添加通用組件
        self._add_common_components()

        # 添加路徑
        self._add_paths(api_config)

        return self.openapi_spec

    def _add_tags(self):
        """添加API標籤"""
        self.openapi_spec["tags"] = [
            {"name": "認證", "description": "用戶認證和授權相關接口"},
            {"name": "系統", "description": "系統狀態和監控接口"},
            {"name": "股票數據", "description": "股票基礎數據和實時行情接口"},
            {"name": "技術分析", "description": "技術指標計算和分析接口"},
            {"name": "策略回測", "description": "量化策略開發和回測接口"},
            {"name": "交易執行", "description": "訂單執行和交易管理接口"},
            {"name": "投資組合", "description": "投資組合管理和分析接口"},
            {"name": "風險管理", "description": "風險監控和管理接口"},
            {"name": "機器學習", "description": "AI模型訓練和預測接口"},
            {"name": "數據導出", "description": "數據查詢和導出接口"},
        ]

    def _add_security_schemes(self):
        """添加安全認證方案"""
        self.openapi_spec["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "輸入JWT令牌進行認證",
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X - API - Key",
                "description": "API密鑰認證",
            },
        }

        self.openapi_spec["security"] = [{"BearerAuth": []}, {"ApiKeyAuth": []}]

    def _add_common_components(self):
        """添加通用組件"""
        # 標準響應模型
        self.openapi_spec["components"]["schemas"]["StandardResponse"] = {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "請求是否成功",
                    "example": True,
                },
                "data": {
                    "description": "響應數據",
                    "example": {"id": 1, "name": "example"},
                },
                "error": {"$re": "#/components / schemas / StandardError"},
                "meta": {"$re": "#/components / schemas / ResponseMetadata"},
                "timestamp": {
                    "type": "string",
                    "format": "date - time",
                    "description": "響應時間戳",
                },
            },
            "required": ["success", "timestamp"],
        }

        # 標準錯誤模型
        self.openapi_spec["components"]["schemas"]["StandardError"] = {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "錯誤代碼",
                    "example": "INVALID_REQUEST",
                },
                "message": {
                    "type": "string",
                    "description": "錯誤消息",
                    "example": "請求參數無效",
                },
                "details": {"type": "object", "description": "錯誤詳情"},
                "request_id": {
                    "type": "string",
                    "description": "請求ID",
                    "example": "req_1642594200000_123456",
                },
            },
            "required": ["code", "message"],
        }

        # 響應元數據
        self.openapi_spec["components"]["schemas"]["ResponseMetadata"] = {
            "type": "object",
            "properties": {
                "version": {
                    "type": "string",
                    "description": "API版本",
                    "example": "v1",
                },
                "request_id": {"type": "string", "description": "請求ID"},
                "processing_time": {
                    "type": "number",
                    "format": "float",
                    "description": "處理時間(秒)",
                },
                "endpoint": {"type": "string", "description": "端點路徑"},
                "method": {"type": "string", "description": "HTTP方法"},
            },
        }

        # 分頁信息
        self.openapi_spec["components"]["schemas"]["PaginationInfo"] = {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "當前頁碼", "example": 1},
                "page_size": {
                    "type": "integer",
                    "description": "每頁大小",
                    "example": 20,
                },
                "total_items": {
                    "type": "integer",
                    "description": "總條目數",
                    "example": 100,
                },
                "total_pages": {
                    "type": "integer",
                    "description": "總頁數",
                    "example": 5,
                },
                "has_next": {"type": "boolean", "description": "是否有下一頁"},
                "has_prev": {"type": "boolean", "description": "是否有上一頁"},
            },
        }

        # 股票數據模型
        self.openapi_spec["components"]["schemas"]["StockData"] = {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代碼",
                    "example": "0700.HK",
                },
                "name": {
                    "type": "string",
                    "description": "股票名稱",
                    "example": "騰訊控股",
                },
                "price": {
                    "type": "number",
                    "format": "float",
                    "description": "當前價格",
                    "example": 320.50,
                },
                "change": {
                    "type": "number",
                    "format": "float",
                    "description": "漲跌額",
                    "example": 2.50,
                },
                "change_percent": {
                    "type": "number",
                    "format": "float",
                    "description": "漲跌幅(%)",
                    "example": 0.79,
                },
                "volume": {
                    "type": "integer",
                    "description": "成交量",
                    "example": 15000000,
                },
                "market_cap": {
                    "type": "number",
                    "format": "float",
                    "description": "市值",
                    "example": 3080000000000,
                },
                "timestamp": {
                    "type": "string",
                    "format": "date - time",
                    "description": "數據時間戳",
                },
            },
        }

        # 技術指標模型
        self.openapi_spec["components"]["schemas"]["TechnicalIndicators"] = {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "股票代碼"},
                "indicators": {
                    "type": "object",
                    "properties": {
                        "sma_20": {
                            "type": "number",
                            "format": "float",
                            "description": "20日均線",
                        },
                        "sma_50": {
                            "type": "number",
                            "format": "float",
                            "description": "50日均線",
                        },
                        "rsi": {
                            "type": "number",
                            "format": "float",
                            "description": "RSI指標",
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "macd": {
                            "type": "number",
                            "format": "float",
                            "description": "MACD指標",
                        },
                        "bollinger_upper": {
                            "type": "number",
                            "format": "float",
                            "description": "布林上軌",
                        },
                        "bollinger_lower": {
                            "type": "number",
                            "format": "float",
                            "description": "布林下軌",
                        },
                    },
                },
                "timestamp": {
                    "type": "string",
                    "format": "date - time",
                    "description": "計算時間戳",
                },
            },
        }

        # 通用響應
        self.openapi_spec["components"]["responses"]["Success"] = {
            "description": "成功響應",
            "content": {
                "application / json": {
                    "schema": {"$re": "#/components / schemas / StandardResponse"}
                }
            },
        }

        self.openapi_spec["components"]["responses"]["BadRequest"] = {
            "description": "錯誤請求",
            "content": {
                "application / json": {
                    "schema": {"$re": "#/components / schemas / StandardResponse"},
                    "example": {
                        "success": False,
                        "error": {"code": "BAD_REQUEST", "message": "請求參數無效"},
                        "timestamp": "2025 - 01 - 19T10:30:00Z",
                    },
                }
            },
        }

        self.openapi_spec["components"]["responses"]["Unauthorized"] = {
            "description": "未授權",
            "content": {
                "application / json": {
                    "schema": {"$re": "#/components / schemas / StandardResponse"},
                    "example": {
                        "success": False,
                        "error": {"code": "UNAUTHORIZED", "message": "認證失敗"},
                        "timestamp": "2025 - 01 - 19T10:30:00Z",
                    },
                }
            },
        }

    def _add_paths(self, api_config: Dict[str, Any]):
        """添加API路徑"""
        services = api_config.get("services", {})

        # 認證路徑
        self._add_auth_paths()

        # 系統路徑
        self._add_system_paths()

        # 服務路徑
        for service_name, service_config in services.items():
            self._add_service_paths(service_name, service_config)

    def _add_auth_paths(self):
        """添加認證相關路徑"""
        # 登錄
        self.openapi_spec["paths"]["/auth / login"] = {
            "post": {
                "tags": ["認證"],
                "summary": "用戶登錄",
                "description": "用戶名密碼登錄，返回JWT令牌",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application / json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "username": {
                                        "type": "string",
                                        "description": "用戶名",
                                    },
                                    "password": {
                                        "type": "string",
                                        "format": "password",
                                        "description": "密碼",
                                    },
                                },
                                "required": ["username", "password"],
                            },
                            "example": {"username": "admin", "password": "admin123"},
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "登錄成功",
                        "content": {
                            "application / json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "token": {
                                                    "type": "string",
                                                    "description": "JWT令牌",
                                                },
                                                "expires_in": {
                                                    "type": "integer",
                                                    "description": "過期時間(秒)",
                                                },
                                            },
                                        },
                                    },
                                }
                            }
                        },
                    },
                    "401": {"$re": "#/components / responses / Unauthorized"},
                },
            }
        }

    def _add_system_paths(self):
        """添加系統相關路徑"""
        # 健康檢查
        self.openapi_spec["paths"]["/health"] = {
            "get": {
                "tags": ["系統"],
                "summary": "健康檢查",
                "description": "檢查API網關和後端服務健康狀態",
                "responses": {
                    "200": {
                        "description": "服務健康",
                        "content": {
                            "application / json": {
                                "schema": {
                                    "allOf": [
                                        {
                                            "$re": "#/components / schemas / StandardResponse"
                                        },
                                        {
                                            "type": "object",
                                            "properties": {
                                                "data": {
                                                    "type": "object",
                                                    "properties": {
                                                        "status": {"type": "string"},
                                                        "services": {
                                                            "type": "object",
                                                            "properties": {
                                                                "total_services": {
                                                                    "type": "integer"
                                                                },
                                                                "healthy_services": {
                                                                    "type": "integer"
                                                                },
                                                            },
                                                        },
                                                    },
                                                }
                                            },
                                        },
                                    ]
                                }
                            }
                        },
                    }
                },
            }
        }

        # 指標
        self.openapi_spec["paths"]["/metrics"] = {
            "get": {
                "tags": ["系統"],
                "summary": "系統指標",
                "description": "獲取API網關性能指標",
                "security": [{"BearerAuth": []}, {"ApiKeyAuth": []}],
                "responses": {
                    "200": {"$re": "#/components / responses / Success"},
                    "401": {"$re": "#/components / responses / Unauthorized"},
                },
            }
        }

    def _add_service_paths(self, service_name: str, service_config: Dict[str, Any]):
        """添加服務路徑"""
        prefix = service_config.get("prefix", f"/api / v1/{service_name}")

        # 根據服務類型添加特定路徑
        if service_name == "dashboard":
            self._add_dashboard_paths(prefix)
        elif service_name == "analysis":
            self._add_analysis_paths(prefix)
        elif service_name == "trading":
            self._add_trading_paths(prefix)
        elif service_name == "ml":
            self._add_ml_paths(prefix)
        elif service_name == "portfolio":
            self._add_portfolio_paths(prefix)
        elif service_name == "risk":
            self._add_risk_paths(prefix)

    def _add_dashboard_paths(self, prefix: str):
        """添加儀表板路徑"""
        # 總覽
        self.openapi_spec["paths"][f"{prefix}/summary"] = {
            "get": {
                "tags": ["系統"],
                "summary": "儀表板總覽",
                "description": "獲取系統總覽信息",
                "security": [{"BearerAuth": []}, {"ApiKeyAuth": []}],
                "responses": {
                    "200": {"$re": "#/components / responses / Success"},
                    "401": {"$re": "#/components / responses / Unauthorized"},
                },
            }
        }

    def _add_analysis_paths(self, prefix: str):
        """添加分析服務路徑"""
        # 股票數據
        self.openapi_spec["paths"][f"{prefix}/stocks/{{symbol}}"] = {
            "get": {
                "tags": ["股票數據"],
                "summary": "獲取股票數據",
                "description": "獲取指定股票的實時數據",
                "security": [{"BearerAuth": []}, {"ApiKeyAuth": []}],
                "parameters": [
                    {
                        "name": "symbol",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "股票代碼",
                        "example": "0700.HK",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application / json": {
                                "schema": {
                                    "allOf": [
                                        {
                                            "$re": "#/components / schemas / StandardResponse"
                                        },
                                        {
                                            "type": "object",
                                            "properties": {
                                                "data": {
                                                    "$re": "#/components / schemas / StockData"
                                                }
                                            },
                                        },
                                    ]
                                }
                            }
                        },
                    },
                    "401": {"$re": "#/components / responses / Unauthorized"},
                    "404": {"$re": "#/components / responses / BadRequest"},
                },
            }
        }

        # 技術指標
        self.openapi_spec["paths"][f"{prefix}/stocks/{{symbol}}/indicators"] = {
            "get": {
                "tags": ["技術分析"],
                "summary": "計算技術指標",
                "description": "計算指定股票的技術指標",
                "security": [{"BearerAuth": []}, {"ApiKeyAuth": []}],
                "parameters": [
                    {
                        "name": "symbol",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "股票代碼",
                    },
                    {
                        "name": "indicators",
                        "in": "query",
                        "schema": {"type": "array", "items": {"type": "string"}},
                        "description": "要計算的指標列表",
                    },
                ],
                "responses": {
                    "200": {
                        "description": "成功",
                        "content": {
                            "application / json": {
                                "schema": {
                                    "allOf": [
                                        {
                                            "$re": "#/components / schemas / StandardResponse"
                                        },
                                        {
                                            "type": "object",
                                            "properties": {
                                                "data": {
                                                    "$re": "#/components / schemas / TechnicalIndicators"
                                                }
                                            },
                                        },
                                    ]
                                }
                            }
                        },
                    }
                },
            }
        }

    def _add_trading_paths(self, prefix: str):
        """添加交易服務路徑"""
        # 下單
        self.openapi_spec["paths"][f"{prefix}/orders"] = {
            "post": {
                "tags": ["交易執行"],
                "summary": "提交訂單",
                "description": "提交新的交易訂單",
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application / json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "symbol": {
                                        "type": "string",
                                        "description": "股票代碼",
                                    },
                                    "side": {
                                        "type": "string",
                                        "enum": ["BUY", "SELL"],
                                        "description": "買賣方向",
                                    },
                                    "quantity": {
                                        "type": "integer",
                                        "description": "數量",
                                    },
                                    "price": {"type": "number", "description": "價格"},
                                    "order_type": {
                                        "type": "string",
                                        "enum": ["MARKET", "LIMIT"],
                                        "description": "訂單類型",
                                    },
                                },
                                "required": ["symbol", "side", "quantity"],
                            }
                        }
                    },
                },
                "responses": {
                    "201": {"$re": "#/components / responses / Success"},
                    "401": {"$re": "#/components / responses / Unauthorized"},
                },
            }
        }

    def _add_ml_paths(self, prefix: str):
        """添加機器學習服務路徑"""
        # 價格預測
        self.openapi_spec["paths"][f"{prefix}/predict/{{symbol}}"] = {
            "post": {
                "tags": ["機器學習"],
                "summary": "價格預測",
                "description": "使用AI模型預測股價",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "symbol",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "股票代碼",
                    }
                ],
                "requestBody": {
                    "content": {
                        "application / json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "model": {
                                        "type": "string",
                                        "description": "模型名稱",
                                    },
                                    "horizon": {
                                        "type": "integer",
                                        "description": "預測天數",
                                    },
                                },
                            }
                        }
                    }
                },
                "responses": {"200": {"$re": "#/components / responses / Success"}},
            }
        }

    def _add_portfolio_paths(self, prefix: str):
        """添加投資組合服務路徑"""
        # 獲取投資組合
        self.openapi_spec["paths"][f"{prefix}/portfolios"] = {
            "get": {
                "tags": ["投資組合"],
                "summary": "獲取投資組合",
                "description": "獲取用戶的投資組合信息",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"$re": "#/components / responses / Success"}},
            }
        }

    def _add_risk_paths(self, prefix: str):
        """添加風險管理服務路徑"""
        # 風險指標
        self.openapi_spec["paths"][f"{prefix}/risk / metrics"] = {
            "get": {
                "tags": ["風險管理"],
                "summary": "風險指標",
                "description": "獲取投資組合的風險指標",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"$re": "#/components / responses / Success"}},
            }
        }

    def export_json(self, file_path: str):
        """導出JSON格式的OpenAPI規範"""
        with open(file_path, "w", encoding="utf - 8") as f:
            json.dump(self.openapi_spec, f, indent=2, ensure_ascii=False)
        logger.info(f"OpenAPI JSON規範已導出: {file_path}")

    def export_yaml(self, file_path: str):
        """導出YAML格式的OpenAPI規範"""
        with open(file_path, "w", encoding="utf - 8") as f:
            yaml.dump(
                self.openapi_spec, f, default_flow_style=False, allow_unicode=True
            )
        logger.info(f"OpenAPI YAML規範已導出: {file_path}")


class DocumentationGenerator:
    """文檔生成器"""

    def __init__(self, output_dir: str = "docs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_all_documentation(self, api_config: Dict[str, Any]):
        """生成所有文檔"""
        logger.info("開始生成API文檔...")

        # 生成OpenAPI規範
        generator = OpenAPIGenerator()
        spec = generator.generate_spec(api_config)

        # 導出規範文件
        generator.export_json(self.output_dir / "openapi.json")
        generator.export_yaml(self.output_dir / "openapi.yaml")

        # 生成Markdown文檔
        self._generate_markdown_docs(spec)

        # 生成HTML文檔
        self._generate_html_docs(spec)

        # 生成客戶端SDK
        self._generate_client_sdks(spec)

        # 生成使用示例
        self._generate_examples(spec)

        logger.info(f"API文檔生成完成，輸出到: {self.output_dir}")

    def _generate_markdown_docs(self, spec: Dict[str, Any]):
        """生成Markdown文檔"""
        md_content = """# {spec['info']['title']}

{spec['info']['description']}

## 基本信息

- **版本**: {spec['info']['version']}
- **基礎URL**: {spec['servers'][0]['url']}
- **聯係方式**: {spec['info']['contact']['email']}
- **許可證**: {spec['info']['license']['name']}

## 認證

API支持以下認證方式:

### JWT認證 (Bearer Token)

在請求頭中添加:
```
Authorization: Bearer <your - jwt - token>
```

### API密鑰認證

在請求頭中添加:
```
X - API - Key: <your - api - key>
```

## API端點

"""

        # 添加每個標籤的端點
        tags = {tag["name"]: tag["description"] for tag in spec["tags"]}

        for tag_name, description in tags.items():
            md_content += f"### {tag_name}\n\n{description}\n\n"

            # 查找相關端點
            for path, path_item in spec["paths"].items():
                for method, operation in path_item.items():
                    if method in ["get", "post", "put", "delete", "patch"]:
                        operation_tags = operation.get("tags", [])
                        if tag_name in operation_tags:
                            md_content += f"#### {method.upper()} {path}\n\n"
                            md_content += f"{operation.get('summary', '')}\n\n"
                            md_content += f"{operation.get('description', '')}\n\n"

                            # 參數
                            parameters = operation.get("parameters", [])
                            if parameters:
                                md_content += "**參數:**\n\n"
                                for param in parameters:
                                    md_content += f"- `{param['name']}` ({param.get('in', 'query')}): {param.get('description', '')}\n"
                                md_content += "\n"

                            # 響應
                            responses = operation.get("responses", {})
                            if "200" in responses:
                                md_content += "**響應:**\n\n"
                                md_content += f"```json\n{json.dumps(responses['200'], indent=2, ensure_ascii=False)}\n```\n\n"

        with open(self.output_dir / "api_documentation.md", "w", encoding="utf - 8") as f:
            f.write(md_content)

        logger.info("Markdown文檔已生成")

    def _generate_html_docs(self, spec: Dict[str, Any]):
        """生成HTML文檔"""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>{spec['info']['title']}</title>
    <meta charset="utf - 8">
    <style>
        body {{ font - family: Arial, sans - serif; margin: 40px; }}
        .header {{ background: #f5f5f5; padding: 20px; border - radius: 5px; }}
        .endpoint {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border - radius: 5px; }}
        .method {{ display: inline - block; padding: 3px 8px; border - radius: 3px; color: white; font - weight: bold; }}
        .get {{ background: #61affe; }}
        .post {{ background: #49cc90; }}
        .put {{ background: #fca130; }}
        .delete {{ background: #f93e3e; }}
        .path {{ font - family: monospace; font - size: 1.1em; margin: 0 10px; }}
        pre {{ background: #f5f5f5; padding: 10px; border - radius: 3px; overflow - x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{spec['info']['title']}</h1>
        <p>{spec['info']['description']}</p>
        <p><strong>版本:</strong> {spec['info']['version']}</p>
        <p><strong>基礎URL:</strong> {spec['servers'][0]['url']}</p>
    </div>

    <h2>認證</h2>
    <p>API支持JWT Bearer Token和API密鑰認證。</p>

    <h2>API端點</h2>
"""

        # 添加端點
        for path, path_item in spec["paths"].items():
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    html_content += """
    <div class="endpoint">
        <span class="method {method}">{method.upper()}</span>
        <span class="path">{path}</span>
        <h3>{operation.get('summary', '')}</h3>
        <p>{operation.get('description', '')}</p>
"""
                    # 參數
                    parameters = operation.get("parameters", [])
                    if parameters:
                        html_content += "<h4>參數:</h4><ul>"
                        for param in parameters:
                            html_content += f"<li><code>{param['name']}</code> ({param.get('in', 'query')}): {param.get('description', '')}</li>"
                        html_content += "</ul>"

                    # 響應示例
                    if "200" in operation["responses"]:
                        html_content += "<h4>響應示例:</h4>"
                        html_content += f"<pre>{json.dumps(operation['responses']['200'], indent=2, ensure_ascii=False)}</pre>"

                    html_content += "</div>"

        html_content += """
</body>
</html>
"""

        with open(
            self.output_dir / "api_documentation.html", "w", encoding="utf - 8"
        ) as f:
            f.write(html_content)

        logger.info("HTML文檔已生成")

    def _generate_client_sdks(self, spec: Dict[str, Any]):
        """生成客戶端SDK"""
        # Python SDK
        self._generate_python_sdk(spec)

        # JavaScript SDK
        self._generate_javascript_sdk(spec)

        # cURL示例
        self._generate_curl_examples(spec)

    def _generate_python_sdk(self, spec: Dict[str, Any]):
        """生成Python SDK"""
        sdk_dir = self.output_dir / "sdk" / "python"
        sdk_dir.mkdir(parents=True, exist_ok=True)

        python_client = '''"""港股量化交易系統 Python SDK"""

import requests
import json
from typing import Dict, Any, Optional


class CodexQuantClient:
    """CODEX-- 量化交易系統客戶端"""

    def __init__(self, base_url: str = "http://localhost:7777", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"X - API - Key": api_key})

    def set_jwt_token(self, token: str):
        """設置JWT認證令牌"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用戶登錄"""
        response = self.session.post(
            f"{self.base_url}/auth / login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()

    def get_health(self) -> Dict[str, Any]:
        """獲取系統健康狀態"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """獲取股票數據"""
        response = self.session.get(f"{self.base_url}/api / v1 / analysis / stocks/{symbol}")
        response.raise_for_status()
        return response.json()

    def get_technical_indicators(self, symbol: str, indicators: list = None) -> Dict[str, Any]:
        """獲取技術指標"""
        params = {}
        if indicators:
            params["indicators"] = ",".join(indicators)

        response = self.session.get(
            f"{self.base_url}/api / v1 / analysis / stocks/{symbol}/indicators",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def create_order(self, symbol: str, side: str, quantity: int, price: float = None, order_type: str = "MARKET") -> Dict[str, Any]:
        """提交訂單"""
        order_data = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order_type": order_type
        }

        if price and order_type == "LIMIT":
            order_data["price"] = price

        response = self.session.post(f"{self.base_url}/api / v1 / trading / orders", json=order_data)
        response.raise_for_status()
        return response.json()

    def predict_price(self, symbol: str, model: str = "lstm", horizon: int = 5) -> Dict[str, Any]:
        """價格預測"""
        response = self.session.post(
            f"{self.base_url}/api / v1 / ml / predict/{symbol}",
            json={"model": model, "horizon": horizon}
        )
        response.raise_for_status()
        return response.json()

    def get_portfolio(self) -> Dict[str, Any]:
        """獲取投資組合"""
        response = self.session.get(f"{self.base_url}/api / v1 / portfolio / portfolios")
        response.raise_for_status()
        return response.json()

    def get_risk_metrics(self) -> Dict[str, Any]:
        """獲取風險指標"""
        response = self.session.get(f"{self.base_url}/api / v1 / risk / risk / metrics")
        response.raise_for_status()
        return response.json()


# 使用示例
if __name__ == "__main__":
    # 初始化客戶端
    client = CodexQuantClient(api_key="your - api - key")

    # 或者使用用戶名密碼登錄
    # client = CodexQuantClient()
    # login_result = client.login("username", "password")
    # client.set_jwt_token(login_result["data"]["token"])

    # 獲取股票數據
    stock_data = client.get_stock_data("0700.HK")
    print("股票數據:", json.dumps(stock_data, indent=2, ensure_ascii=False))

    # 獲取技術指標
    indicators = client.get_technical_indicators("0700.HK", ["sma", "rsi", "macd"])
    print("技術指標:", json.dumps(indicators, indent=2, ensure_ascii=False))

    # 價格預測
    prediction = client.predict_price("0700.HK")
    print("價格預測:", json.dumps(prediction, indent=2, ensure_ascii=False))
'''

        with open(sdk_dir / "codex_quant_client.py", "w", encoding="utf - 8") as f:
            f.write(python_client)

        # 生成requirements.txt
        with open(sdk_dir / "requirements.txt", "w") as f:
            f.write("requests>=2.25.0\n")

        # 生成README
        with open(sdk_dir / "README.md", "w", encoding="utf - 8") as f:
            f.write(
                """# Python SDK

港股量化交易系統 Python客戶端SDK。

## 安裝

```bash
pip install -r requirements.txt
```

## 使用

```python
from codex_quant_client import CodexQuantClient

# 使用API密鑰
client = CodexQuantClient(api_key="your - api - key")

# 或使用用戶名密碼登錄
client = CodexQuantClient()
login_result = client.login("username", "password")
client.set_jwt_token(login_result["data"]["token"])

# 獲取股票數據
stock_data = client.get_stock_data("0700.HK")
print(stock_data)
```
"""
            )

        logger.info("Python SDK已生成")

    def _generate_javascript_sdk(self, spec: Dict[str, Any]):
        """生成JavaScript SDK"""
        sdk_dir = self.output_dir / "sdk" / "javascript"
        sdk_dir.mkdir(parents=True, exist_ok=True)

        js_client = """/**
 * 港股量化交易系統 JavaScript SDK
 */

class CodexQuantClient {
    constructor(baseUrl = 'http://localhost:7777', apiKey = null) {
        this.baseUrl = baseUrl.replace(/\\/$/, '');
        this.apiKey = apiKey;
        this.jwtToken = null;
    }

    setApiKey(apiKey) {
        this.apiKey = apiKey;
    }

    setJwtToken(token) {
        this.jwtToken = token;
    }

    async _request(method, endpoint, data = null, params = null) {
        const url = new URL(`${this.baseUrl}${endpoint}`);

        // 添加查詢參數
        if (params) {
            Object.keys(params).forEach(key =>
                url.searchParams.append(key, params[key])
            );
        }

        const options = {
            method,
            headers: {
                'Content - Type': 'application / json',
            }
        };

        // 添加認證頭
        if (this.jwtToken) {
            options.headers.Authorization = `Bearer ${this.jwtToken}`;
        } else if (this.apiKey) {
            options.headers['X - API - Key'] = this.apiKey;
        }

        // 添加請求體
        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        return await response.json();
    }

    async login(username, password) {
        return await this._request('POST', '/auth / login', {
            username,
            password
        });
    }

    async getHealth() {
        return await this._request('GET', '/health');
    }

    async getStockData(symbol) {
        return await this._request('GET', `/api / v1 / analysis / stocks/${symbol}`);
    }

    async getTechnicalIndicators(symbol, indicators = null) {
        const params = {};
        if (indicators) {
            params.indicators = indicators.join(',');
        }
        return await this._request('GET', `/api / v1 / analysis / stocks/${symbol}/indicators`, null, params);
    }

    async createOrder(symbol, side, quantity, price = null, orderType = 'MARKET') {
        const orderData = {
            symbol,
            side,
            quantity,
            order_type: orderType
        };

        if (price && orderType === 'LIMIT') {
            orderData.price = price;
        }

        return await this._request('POST', '/api / v1 / trading / orders', orderData);
    }

    async predictPrice(symbol, model = 'lstm', horizon = 5) {
        return await this._request('POST', `/api / v1 / ml / predict/${symbol}`, {
            model,
            horizon
        });
    }

    async getPortfolio() {
        return await this._request('GET', '/api / v1 / portfolio / portfolios');
    }

    async getRiskMetrics() {
        return await this._request('GET', '/api / v1 / risk / risk / metrics');
    }
}

// 使用示例
/*
// 初始化客戶端
const client = new CodexQuantClient();

// 使用API密鑰
client.setApiKey('your - api - key');

// 或者登錄獲取JWT令牌
const loginResult = await client.login('username', 'password');
client.setJwtToken(loginResult.data.token);

// 獲取股票數據
const stockData = await client.getStockData('0700.HK');
console.log('股票數據:', stockData);

// 獲取技術指標
const indicators = await client.getTechnicalIndicators('0700.HK', ['sma', 'rsi', 'macd']);
console.log('技術指標:', indicators);
*/

// Node.js導出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CodexQuantClient;
}
"""

        with open(sdk_dir / "codex_quant_client.js", "w", encoding="utf - 8") as f:
            f.write(js_client)

        # 生成package.json
        package_json = """{
  "name": "codex - quant - client",
  "version": "1.0.0",
  "description": "港股量化交易系統 JavaScript SDK",
  "main": "codex_quant_client.js",
  "scripts": {
    "test": "node test.js"
  },
  "keywords": ["quant", "trading", "hong", "kong", "stocks"],
  "author": "CODEX-- Team",
  "license": "MIT"
}
"""
        with open(sdk_dir / "package.json", "w", encoding="utf - 8") as f:
            f.write(package_json)

        logger.info("JavaScript SDK已生成")

    def _generate_curl_examples(self, spec: Dict[str, Any]):
        """生成cURL示例"""
        examples_file = self.output_dir / "curl_examples.md"

        examples = """# cURL API調用示例

## 認證

### 用戶登錄

```bash
curl -X POST "http://localhost:7777 / auth / login" \\
  -H "Content - Type: application / json" \\
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### 使用JWT令牌

```bash
curl -X GET "http://localhost:7777 / health" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 使用API密鑰

```bash
curl -X GET "http://localhost:7777 / health" \\
  -H "X - API - Key: YOUR_API_KEY"
```

## API端點

### 獲取系統健康狀態

```bash
curl -X GET "http://localhost:7777 / health"
```

### 獲取股票數據

```bash
curl -X GET "http://localhost:7777 / api / v1 / analysis / stocks / 0700.HK" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 獲取技術指標

```bash
curl -X GET "http://localhost:7777 / api / v1 / analysis / stocks / 0700.HK / indicators?indicators=sma,rsi,macd" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 提交訂單

```bash
curl -X POST "http://localhost:7777 / api / v1 / trading / orders" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content - Type: application / json" \\
  -d '{
    "symbol": "0700.HK",
    "side": "BUY",
    "quantity": 100,
    "order_type": "MARKET"
  }'
```

### 價格預測

```bash
curl -X POST "http://localhost:7777 / api / v1 / ml / predict / 0700.HK" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content - Type: application / json" \\
  -d '{
    "model": "lstm",
    "horizon": 5
  }'
```

### 獲取投資組合

```bash
curl -X GET "http://localhost:7777 / api / v1 / portfolio / portfolios" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 獲取風險指標

```bash
curl -X GET "http://localhost:7777 / api / v1 / risk / risk / metrics" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```
"""

        with open(examples_file, "w", encoding="utf - 8") as f:
            f.write(examples)

        logger.info("cURL示例已生成")

    def _generate_examples(self, spec: Dict[str, Any]):
        """生成使用示例"""
        examples_dir = self.output_dir / "examples"
        examples_dir.mkdir(exist_ok=True)

        # Python示例
        python_example = '''#!/usr / bin / env python3
"""
港股量化交易系統 Python使用示例
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sdk', 'python'))

from codex_quant_client import CodexQuantClient
import json

def main():
    # 初始化客戶端
    client = CodexQuantClient("http://localhost:7777")

    try:
        # 1. 用戶登錄
        print("1. 用戶登錄...")
        login_result = client.login("admin", "admin123")

        if login_result.get("success"):
            token = login_result["data"]["token"]
            client.set_jwt_token(token)
            print("登錄成功!")
        else:
            print("登錄失敗:", login_result)
            return

        # 2. 檢查系統健康狀態
        print("\\n2. 檢查系統健康狀態...")
        health = client.get_health()
        print("系統狀態:", json.dumps(health, indent=2, ensure_ascii=False))

        # 3. 獲取股票數據
        print("\\n3. 獲取騰訊股票數據...")
        stock_data = client.get_stock_data("0700.HK")
        print("股票數據:", json.dumps(stock_data, indent=2, ensure_ascii=False))

        # 4. 獲取技術指標
        print("\\n4. 獲取技術指標...")
        indicators = client.get_technical_indicators("0700.HK", ["sma", "rsi", "macd"])
        print("技術指標:", json.dumps(indicators, indent=2, ensure_ascii=False))

        # 5. 價格預測
        print("\\n5. 價格預測...")
        prediction = client.predict_price("0700.HK", "lstm", 5)
        print("價格預測:", json.dumps(prediction, indent=2, ensure_ascii=False))

        # 6. 獲取投資組合
        print("\\n6. 獲取投資組合...")
        portfolio = client.get_portfolio()
        print("投資組合:", json.dumps(portfolio, indent=2, ensure_ascii=False))

        # 7. 獲取風險指標
        print("\\n7. 獲取風險指標...")
        risk_metrics = client.get_risk_metrics()
        print("風險指標:", json.dumps(risk_metrics, indent=2, ensure_ascii=False))

        print("\\n示例執行完成!")

    except Exception as e:
        print(f"執行過程中出錯: {e}")

if __name__ == "__main__":
    main()
'''

        with open(examples_dir / "python_example.py", "w", encoding="utf - 8") as f:
            f.write(python_example)

        # JavaScript示例
        js_example = """/**
 * 港股量化交易系統 JavaScript使用示例
 */

// 假設已加載SDK
// const CodexQuantClient = require('./codex_quant_client.js');

async function runExample() {
    // 初始化客戶端
    const client = new CodexQuantClient('http://localhost:7777');

    try {
        // 1. 用戶登錄
        console.log('1. 用戶登錄...');
        const loginResult = await client.login('admin', 'admin123');

        if (loginResult.success) {
            const token = loginResult.data.token;
            client.setJwtToken(token);
            console.log('登錄成功!');
        } else {
            console.log('登錄失敗:', loginResult);
            return;
        }

        // 2. 檢查系統健康狀態
        console.log('\\n2. 檢查系統健康狀態...');
        const health = await client.getHealth();
        console.log('系統狀態:', JSON.stringify(health, null, 2));

        // 3. 獲取股票數據
        console.log('\\n3. 獲取騰訊股票數據...');
        const stockData = await client.getStockData('0700.HK');
        console.log('股票數據:', JSON.stringify(stockData, null, 2));

        // 4. 獲取技術指標
        console.log('\\n4. 獲取技術指標...');
        const indicators = await client.getTechnicalIndicators('0700.HK', ['sma', 'rsi', 'macd']);
        console.log('技術指標:', JSON.stringify(indicators, null, 2));

        // 5. 價格預測
        console.log('\\n5. 價格預測...');
        const prediction = await client.predictPrice('0700.HK', 'lstm', 5);
        console.log('價格預測:', JSON.stringify(prediction, null, 2));

        // 6. 獲取投資組合
        console.log('\\n6. 獲取投資組合...');
        const portfolio = await client.getPortfolio();
        console.log('投資組合:', JSON.stringify(portfolio, null, 2));

        // 7. 獲取風險指標
        console.log('\\n7. 獲取風險指標...');
        const riskMetrics = await client.getRiskMetrics();
        console.log('風險指標:', JSON.stringify(riskMetrics, null, 2));

        console.log('\\n示例執行完成!');

    } catch (error) {
        console.error('執行過程中出錯:', error);
    }
}

// 運行示例
runExample();
"""

        with open(examples_dir / "javascript_example.js", "w", encoding="utf - 8") as f:
            f.write(js_example)

        logger.info("使用示例已生成")


def main():
    """主函數"""
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 模擬API配置
    api_config = {
        "services": {
            "dashboard": {"prefix": "/api / v2"},
            "analysis": {"prefix": "/api / v1"},
            "trading": {"prefix": "/api / v1"},
            "ml": {"prefix": "/api / v1"},
            "portfolio": {"prefix": "/api / v1"},
            "risk": {"prefix": "/api / v1"},
        }
    }

    # 生成文檔
    generator = DocumentationGenerator()
    generator.generate_all_documentation(api_config)

    print("\nAPI文檔生成完成!")
    print("生成的文件:")
    print("- openapi.json - OpenAPI 3.0規範")
    print("- openapi.yaml - OpenAPI YAML格式")
    print("- api_documentation.md - Markdown文檔")
    print("- api_documentation.html - HTML文檔")
    print("- sdk / python/ - Python SDK")
    print("- sdk / javascript/ - JavaScript SDK")
    print("- curl_examples.md - cURL示例")
    print("- examples/ - 使用示例")


if __name__ == "__main__":
    main()
