#!/usr/bin/env python3
"""
API端点验证脚本
API Endpoint Verification Script

用途: 验证所有API端点的可访问性和正确性
Usage: Verify accessibility and correctness of all API endpoints

作者: Claude Code API Architecture Specialist
日期: 2026-01-04
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import httpx
    from rich.console import Console
    from rich.table import Table
    from rich.progress import track
    from rich.panel import Panel
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: rich or httpx not installed. Install with: pip install rich httpx")

# ============================================================================
# 配置
# ============================================================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3007")
TIMEOUT = 5.0

# 预期的API端点列表
EXPECTED_ENDPOINTS = {
    # 策略API
    "strategies": {
        "GET /api/strategies/": {"description": "获取策略列表", "auth": False},
        "GET /api/strategies/{id}": {"description": "获取策略详情", "auth": False},
        "POST /api/strategies/": {"description": "创建策略", "auth": True},
        "PUT /api/strategies/{id}": {"description": "更新策略", "auth": True},
        "DELETE /api/strategies/{id}": {"description": "删除策略", "auth": True},
    },

    # 认证API
    "auth": {
        "POST /api/auth/login": {"description": "用户登录", "auth": False},
        "POST /api/auth/logout": {"description": "用户登出", "auth": True},
        "GET /api/auth/me": {"description": "获取当前用户", "auth": True},
        "POST /api/auth/refresh": {"description": "刷新令牌", "auth": True},
    },

    # V2策略API
    "strategies_v2": {
        "GET /api/v2/strategies": {"description": "V2获取策略列表", "auth": False},
        "GET /api/v2/strategies/{id}": {"description": "V2获取策略详情", "auth": False},
    },

    # V2认证API
    "auth_v2": {
        "POST /api/v2/auth/login": {"description": "V2用户登录", "auth": False},
        "GET /api/v2/auth/me": {"description": "V2获取当前用户", "auth": True},
    },
}

# ============================================================================
# 验证器类
# ============================================================================

class ApiEndpointVerifier:
    """API端点验证器"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.results = []
        self.client = None
        self.auth_token = None

        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    def log(self, message: str, level: str = "info"):
        """记录日志"""
        if self.console:
            if level == "success":
                self.console.print(f"[green]✓[/green] {message}")
            elif level == "error":
                self.console.print(f"[red]✗[/red] {message}")
            elif level == "warning":
                self.console.print(f"[yellow]⚠[/yellow] {message}")
            else:
                self.console.print(message)
        else:
            prefix = {
                "success": "✓",
                "error": "✗",
                "warning": "⚠",
                "info": "→",
            }.get(level, "→")
            print(f"{prefix} {message}")

    async def check_server_health(self) -> bool:
        """检查服务器健康状态"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log("服务器健康检查通过", "success")
                return True
            else:
                self.log(f"服务器健康检查失败: {response.status_code}", "error")
                return False
        except Exception as e:
            self.log(f"无法连接到服务器: {e}", "error")
            return False

    async def test_login(self) -> Optional[str]:
        """尝试登录获取令牌"""
        try:
            # 尝试使用测试凭据登录
            response = await self.client.post(
                f"{self.base_url}/api/auth/login",
                json={
                    "username": "test_user",  # 替换为实际测试用户
                    "password": "test_password"
                }
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                if token:
                    self.auth_token = token
                    self.log("测试登录成功，获取到认证令牌", "success")
                    return token
            else:
                self.log("测试登录失败，将跳过需要认证的端点", "warning")
                return None
        except Exception as e:
            self.log(f"登录过程出错: {e}", "warning")
            return None

    async def verify_endpoint(
        self,
        method: str,
        path: str,
        description: str,
        requires_auth: bool = False
    ) -> Dict[str, Any]:
        """验证单个端点"""

        url = f"{self.base_url}{path}"
        headers = {}

        # 添加认证令牌
        if requires_auth and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        result = {
            "method": method,
            "path": path,
            "description": description,
            "requires_auth": requires_auth,
            "url": url,
            "status": "unknown",
            "status_code": None,
            "response_time": None,
            "error": None,
        }

        try:
            import time
            start_time = time.time()

            # 发送请求
            if method == "GET":
                response = await self.client.get(url, headers=headers)
            elif method == "POST":
                response = await self.client.post(url, headers=headers, json={})
            elif method == "PUT":
                response = await self.client.put(url, headers=headers, json={})
            elif method == "DELETE":
                response = await self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            response_time = (time.time() - start_time) * 1000  # 转换为毫秒

            result["status_code"] = response.status_code
            result["response_time"] = response_time

            # 判断端点是否可访问
            # 200-299: 成功
            # 401: 需要认证但未提供令牌（预期行为）
            # 404: 端点不存在（错误）
            # 405: 方法不允许（错误）
            # 其他: 错误

            if 200 <= response.status_code < 300:
                result["status"] = "success"
                self.log(f"{method} {path} - {response.status_code} ({response_time:.0f}ms)", "success")
            elif response.status_code == 401 and requires_auth and not self.auth_token:
                result["status"] = "auth_required"
                self.log(f"{method} {path} - 需要认证", "warning")
            elif response.status_code == 404:
                result["status"] = "not_found"
                self.log(f"{method} {path} - 端点不存在", "error")
            elif response.status_code == 405:
                result["status"] = "method_not_allowed"
                self.log(f"{method} {path} - 方法不允许", "error")
            else:
                result["status"] = "error"
                result["error"] = response.text
                self.log(f"{method} {path} - {response.status_code}", "warning")

        except httpx.TimeoutException:
            result["status"] = "timeout"
            result["error"] = "请求超时"
            self.log(f"{method} {path} - 请求超时", "error")
        except httpx.ConnectError:
            result["status"] = "connection_error"
            result["error"] = "连接失败"
            self.log(f"{method} {path} - 连接失败", "error")
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            self.log(f"{method} {path} - {e}", "error")

        self.results.append(result)
        return result

    async def verify_all_endpoints(self):
        """验证所有端点"""

        self.log(f"\n开始验证API端点 - {self.base_url}\n")

        # 检查服务器健康
        if not await self.check_server_health():
            self.log("服务器不健康，终止验证", "error")
            return

        # 尝试登录
        await self.test_login()

        # 验证各个类别的端点
        for category, endpoints in EXPECTED_ENDPOINTS.items():
            self.log(f"\n验证 {category} 端点:", "info")

            for endpoint_key, config in endpoints.items():
                method, path = endpoint_key.split(" ", 1)
                description = config["description"]
                requires_auth = config["auth"]

                await self.verify_endpoint(
                    method=method,
                    path=path,
                    description=description,
                    requires_auth=requires_auth
                )

    def print_summary(self):
        """打印验证摘要"""

        if not self.console:
            return

        # 统计结果
        total = len(self.results)
        success = sum(1 for r in self.results if r["status"] == "success")
        not_found = sum(1 for r in self.results if r["status"] == "not_found")
        error = sum(1 for r in self.results if r["status"] in ["error", "timeout", "connection_error"])
        auth_required = sum(1 for r in self.results if r["status"] == "auth_required")
        method_not_allowed = sum(1 for r in self.results if r["status"] == "method_not_allowed")

        # 创建摘要表格
        table = Table(title="\nAPI端点验证摘要", show_header=True, header_style="bold magenta")
        table.add_column("状态", style="cyan", width=12)
        table.add_column("数量", justify="right", style="green")
        table.add_column("占比", justify="right", style="yellow")

        table.add_row("✓ 成功", str(success), f"{success/total*100:.1f}%")
        table.add_row("⚠ 需要认证", str(auth_required), f"{auth_required/total*100:.1f}%")
        table.add_row("✗ 不存在", str(not_found), f"{not_found/total*100:.1f}%")
        table.add_row("✗ 方法错误", str(method_not_allowed), f"{method_not_allowed/total*100:.1f}%")
        table.add_row("✗ 其他错误", str(error), f"{error/total*100:.1f}%")
        table.add_row("总计", str(total), "100%")

        self.console.print(table)

        # 打印失败的端点
        if not_found > 0 or method_not_allowed > 0:
            self.console.print("\n[red]失败的端点:[/red]")
            for result in self.results:
                if result["status"] in ["not_found", "method_not_allowed"]:
                    self.console.print(
                        f"  [red]✗[/red] {result['method']} {result['path']} - {result['description']}"
                    )

        # 打印建议
        if not_found > 0:
            self.console.print(
                "\n[yellow]建议:[/yellow] 检查API路由注册，确保所有端点都已正确定义"
            )

    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""

        report = {
            "timestamp": datetime.now().isoformat(),
            "api_base_url": self.base_url,
            "summary": {
                "total": len(self.results),
                "success": sum(1 for r in self.results if r["status"] == "success"),
                "not_found": sum(1 for r in self.results if r["status"] == "not_found"),
                "error": sum(1 for r in self.results if r["status"] in ["error", "timeout", "connection_error"]),
                "auth_required": sum(1 for r in self.results if r["status"] == "auth_required"),
                "method_not_allowed": sum(1 for r in self.results if r["status"] == "method_not_allowed"),
            },
            "endpoints": self.results,
        }

        return report

    def save_report(self, filepath: str):
        """保存验证报告到文件"""
        report = self.generate_report()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.log(f"\n报告已保存到: {filepath}", "success")


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主函数"""

    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel.fit(
            "[bold cyan]API端点验证脚本[/bold cyan]\n"
            "[dim]API Endpoint Verification Script[/dim]",
            border_style="cyan"
        ))

    # 创建验证器
    verifier = ApiEndpointVerifier(API_BASE_URL)

    # 执行验证
    async with verifier:
        await verifier.verify_all_endpoints()

    # 打印摘要
    if RICH_AVAILABLE:
        verifier.print_summary()

    # 保存报告
    report_dir = PROJECT_ROOT / ".claude" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"api-verification-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    verifier.save_report(str(report_file))

    # 返回退出码
    success_count = verifier.generate_report()["summary"]["success"]
    total_count = verifier.generate_report()["summary"]["total"]

    if success_count == total_count:
        return 0
    elif success_count > total_count * 0.8:  # 80%成功率
        return 0
    else:
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="API端点验证脚本")
    parser.add_argument(
        "--url",
        default=API_BASE_URL,
        help=f"API基础URL (默认: {API_BASE_URL})"
    )

    args = parser.parse_args()
    API_BASE_URL = args.url

    # 运行验证
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
