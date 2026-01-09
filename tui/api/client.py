# tui/api/client.py
import httpx
from typing import Any, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class CBSCAPIClient:
    """CBSC FastAPI 後端客戶端"""

    def __init__(self):
        self.base_url = os.getenv(
            "CBSC_API_URL",
            "http://localhost:3004"
        )
        self.timeout = 30.0

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET 請求"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST 請求"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    # API 方法
    async def get_strategies(self) -> list:
        """獲取策略列表"""
        return await self.get("/api/strategies")

    async def get_portfolio(self) -> Dict:
        """獲取投資組合"""
        return await self.get("/api/portfolio")

    async def get_system_status(self) -> Dict:
        """獲取系統狀態"""
        return await self.get("/api/system/status")
