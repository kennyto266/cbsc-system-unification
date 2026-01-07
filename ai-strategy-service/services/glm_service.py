"""
GLM Service
Integration with Zhipu AI's GLM-4-plus model for strategy generation
"""
import os
from typing import List, Optional
import httpx
from pydantic import BaseModel


class GLMMessage(BaseModel):
    """Message format for GLM API"""
    role: str
    content: str


class GLMRequest(BaseModel):
    """Request format for GLM API"""
    model: str = "glm-4-plus"
    messages: List[GLMMessage]
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2000


class GLMService:
    """
    Service for interacting with GLM API
    Handles authentication, request formatting, and response parsing
    """

    def __init__(self):
        self.api_key = os.getenv("GLM_API_KEY")
        if not self.api_key:
            raise ValueError("GLM_API_KEY environment variable not set")

        self.base_url = "https://open.bigmodel.cn/api/paas/v4/"
        self.client = httpx.AsyncClient(timeout=60.0)

    async def chat(self, messages: List[GLMMessage]) -> str:
        """
        Send chat request to GLM API

        Args:
            messages: List of conversation messages

        Returns:
            Assistant's response content

        Raises:
            Exception: If API request fails
        """
        # Convert Pydantic models to dicts for JSON serialization
        messages_dict = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        request_data = {
            "model": "glm-4-plus",
            "messages": messages_dict,
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2000
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        response = await self.client.post(
            f"{self.base_url}chat/completions",
            json=request_data,
            headers=headers
        )

        response.raise_for_status()
        data = response.json()

        if not data.get("choices"):
            raise ValueError("GLM API returned no choices")

        return data["choices"][0]["message"]["content"]

    async def generate_strategy(self, description: str) -> str:
        """
        Generate trading strategy from description

        Args:
            description: Natural language description of the strategy

        Returns:
            Generated Python code for the strategy
        """
        system_prompt = GLMMessage(
            role="system",
            content="""You are a quantitative trading strategy expert. Generate Python code for trading strategies.
The strategy should be structured as a Jupyter notebook with the following cells:
1. Imports and configuration
2. Data fetching
3. Strategy parameters
4. Signal generation
5. Backtesting
6. Results visualization

Return ONLY valid Python code that can be executed in a Jupyter notebook."""
        )

        user_prompt = GLMMessage(
            role="user",
            content=f"Create a trading strategy: {description}"
        )

        return await self.chat([system_prompt, user_prompt])

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
