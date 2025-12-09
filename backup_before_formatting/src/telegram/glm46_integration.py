"""GLM4.6 API integration for Telegram Bot.

This module provides integration with GLM4.6 API for AI - powered
responses in the Telegram Bot system.
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx


class GLM46Config:
    """Configuration for GLM4.6 API."""

    def __init__(self):
        self.api_key = "3f3a42c3fd2e443bbd0f0825eba93cf2.UZd0cuO7lgt4tGMW"  # 直接設置
        self.base_url = "https://open.bigmodel.cn / api / paas / v4 / chat / completions"
        self.model = "glm - 4.6"  # 使用 glm - 4.6 模型（按用戶要求）
        self.timeout = 120  # glm - 4.6 需要更長的處理時間
        self.max_tokens = 150  # 適當的輸出長度
        self.temperature = 0.3  # 溫度


class GLM46Integration:
    """GLM4.6 API integration for Telegram Bot."""

    def __init__(self, config: Optional[GLM46Config] = None):
        self.config = config or GLM46Config()
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats = {
            "requests_made": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "total_tokens_used": 0,
            "cache_hits": 0,
        }

        # Response cache
        self.response_cache = {}
        self.cache_max_size = 100
        self.cache_ttl = 3600  # 1小時緩存

        # Request queue and processing
        self.request_queue = asyncio.Queue()
        self.processing_semaphore = asyncio.Semaphore(3)  # 最多同時處理3個請求
        self.is_processing = False

    def _generate_cache_key(
        self, user_message: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate cache key for the request."""
        content = f"{system_prompt or ''}|{user_message}"
        return hashlib.sha256(content.encode("utf - 8")).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired."""
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                self.stats["cache_hits"] += 1
                return cached_data["response"]
            else:
                # Remove expired cache entry
                del self.response_cache[cache_key]
        return None

    def _cache_response(self, cache_key: str, response: Dict[str, Any]) -> None:
        """Cache the response."""
        # Remove oldest entries if cache is full
        if len(self.response_cache) >= self.cache_max_size:
            oldest_key = min(
                self.response_cache.keys(),
                key=lambda k: self.response_cache[k]["timestamp"],
            )
            del self.response_cache[oldest_key]

        self.response_cache[cache_key] = {
            "response": response,
            "timestamp": time.time(),
        }

    async def _make_request(self, messages: list, **kwargs) -> Optional[Dict[str, Any]]:
        """Make request to GLM4.6 API."""
        try:
            if not self.config.api_key:
                self.logger.error("GLM4.6 API key not configured")
                return None

            # Prepare request payload
            payload = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stream": False,
            }

            self.logger.info(
                f"GLM4.6 API request: {json.dumps(payload, ensure_ascii=False)}"
            )

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content - Type": "application / json",
            }

            # Make HTTP request
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    self.config.base_url, json=payload, headers=headers
                )

                self.stats["requests_made"] += 1

                if response.status_code == 200:
                    result = response.json()
                    self.stats["successful_responses"] += 1

                    # Extract token usage if available
                    if "usage" in result:
                        self.stats["total_tokens_used"] += result["usage"].get(
                            "total_tokens", 0
                        )

                    return result
                else:
                    self.logger.error(
                        f"GLM4.6 API error: {response.status_code} - {response.text}"
                    )
                    self.stats["failed_responses"] += 1
                    return None

        except httpx.TimeoutException:
            self.logger.error(f"GLM4.6 API timeout after {self.config.timeout}s")
            self.stats["failed_responses"] += 1
            return None
        except Exception as e:
            self.logger.error(
                f"GLM4.6 API request failed: {type(e).__name__}: {str(e)}"
            )
            self.stats["failed_responses"] += 1
            return None

    async def chat_completion(
        self, user_message: str, system_prompt: Optional[str] = None, **kwargs
    ) -> Optional[str]:
        """Get chat completion from GLM4.6 with caching."""
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(user_message, system_prompt)

            # Check cache first
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                self.logger.info(f"Cache hit for query: {user_message[:50]}...")
                self.stats["cache_hits"] += 1
                return cached_response["choices"][0]["message"]["content"].strip()

            # Prepare messages
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": user_message})

            # Use direct request processing with semaphore protection
            self.stats["requests_made"] += 1
            async with self.processing_semaphore:
                result = await self._make_request(messages, **kwargs)

            if result and "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]
                # GLM 4.6 uses reasoning_content for the actual response
                response_content = message.get("reasoning_content") or message.get(
                    "content", ""
                )
                response_content = response_content.strip()

                # Cache the response
                self._cache_response(cache_key, result)

                self.stats["successful_responses"] += 1
                return response_content
            else:
                self.logger.error("Invalid response format from GLM4.6 API")
                self.stats["failed_responses"] += 1
                return None

        except Exception as e:
            self.logger.error(f"Chat completion failed: {e}")
            self.stats["failed_responses"] += 1
            return None

    async def analyze_trading_signal(
        self, symbol: str, signal_data: Dict[str, Any]
    ) -> Optional[str]:
        """Analyze trading signal using GLM4.6."""
        system_prompt = """您是一個專業的量化交易分析師。請分析提供的交易信號數據，並給出專業的建議。

分析格式：
1. 信號評級：🌟🌟🌟🌟🌟 (1 - 5星)
2. 風險評估：低 / 中 / 高
3. 建議操作：買入 / 賣出 / 持有
4. 分析理由：詳細說明
5. 注意事項：風險提醒
- 使用繁體中文回應"""

        user_message = """請分析以下交易信號：

股票代碼：{symbol}
信號方向：{signal_data.get('side', 'N / A')}
信號強度：{signal_data.get('strength', 'N / A')}
置信度：{signal_data.get('confidence', 'N / A')}
當前價格：{signal_data.get('price', 'N / A')}
策略名稱：{signal_data.get('strategy_name', 'N / A')}
風險等級：{signal_data.get('risk_level', 'N / A')}

預期回報：{signal_data.get('expected_return', 'N / A')}
止損價格：{signal_data.get('stop_loss', 'N / A')}
止盈價格：{signal_data.get('take_profit', 'N / A')}

理由：{signal_data.get('reasoning', 'N / A')}"""

        return await self.chat_completion(user_message, system_prompt)

    async def get_market_analysis(self, market_data: Dict[str, Any]) -> Optional[str]:
        """Get market analysis using GLM4.6."""
        system_prompt = """您是一個專業的金融市場分析師。請基於提供的市場數據給出專業分析。

分析內容應包括：
1. 市場趨勢分析
2. 關鍵技術指標解讀
3. 市場情緒評估
4. 短期預測
5. 投資建議
- 使用繁體中文回應"""

        user_message = """請分析以下市場數據：

{json.dumps(market_data, ensure_ascii=False, indent=2)}"""

        return await self.chat_completion(user_message, system_prompt)

    async def answer_general_question(self, question: str) -> Optional[str]:
        """Answer general question using GLM4.6."""
        system_prompt = """您是專業的企鵝助手。請簡潔回答，控制在100字內。

回答要求：
- 精簡扼要，最多100字
- 直接回答重點
- 實用性強
- 針對企業需求
- 使用繁體中文回應"""

        return await self.chat_completion(question, system_prompt)

    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics."""
        success_rate = 0
        if self.stats["requests_made"] > 0:
            success_rate = (
                self.stats["successful_responses"] / self.stats["requests_made"]
            )

        return {
            "api_configured": bool(self.config.api_key),
            "base_url": self.config.base_url,
            "model": self.config.model,
            "stats": self.stats.copy(),
            "success_rate": success_rate,
        }

    def is_configured(self) -> bool:
        """Check if GLM4.6 API is properly configured."""
        return bool(self.config.api_key)

    async def _process_queue(self):
        """Process requests from the queue with concurrency control."""
        try:
            while not self.request_queue.empty():
                try:
                    # Get request from queue
                    request_item = await asyncio.wait_for(
                        self.request_queue.get(), timeout=1.0
                    )

                    # Process with semaphore protection
                    async with self.processing_semaphore:
                        await self._execute_queued_request(request_item)

                except asyncio.TimeoutError:
                    # No more requests in queue
                    break
                except Exception as e:
                    self.logger.error(f"Queue processing error: {e}")
        finally:
            # Reset processing flag when done
            self.is_processing = False

    async def _execute_queued_request(self, request_item: Dict[str, Any]):
        """Execute a queued request."""
        try:
            method = request_item["method"]
            args = request_item["args"]
            kwargs = request_item["kwargs"]

            if method == "chat_completion":
                result = await self._make_request(*args, **kwargs)
                # Store result for the waiting coroutine
                request_item["future"].set_result(result)

        except Exception as e:
            if "future" in request_item:
                request_item["future"].set_exception(e)
            self.logger.error(f"Queued request execution failed: {e}")

    async def _queue_request(self, method: str, *args, **kwargs) -> Any:
        """Queue a request for processing."""
        # Create a Future for the result
        future = asyncio.Future()

        request_item = {
            "method": method,
            "args": args,
            "kwargs": kwargs,
            "future": future,
            "timestamp": time.time(),
        }

        # Add to queue
        await self.request_queue.put(request_item)

        # Start queue processing if not already running
        if not self.is_processing:
            self.is_processing = True
            asyncio.create_task(self._process_queue())

        # Wait for result with timeout
        try:
            result = await asyncio.wait_for(future, timeout=self.config.timeout + 10)
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"Queued request timed out: {method}")
            raise


# Global instance for easy access
_glm46_instance: Optional[GLM46Integration] = None


def get_glm46_instance() -> GLM46Integration:
    """Get or create GLM4.6 integration instance."""
    global _glm46_instance
    if _glm46_instance is None:
        _glm46_instance = GLM46Integration()
    return _glm46_instance


async def call_glm46_api(
    user_message: str, system_prompt: Optional[str] = None, **kwargs
) -> Optional[str]:
    """Convenience function to call GLM4.6 API."""
    glm46 = get_glm46_instance()
    return await glm46.chat_completion(user_message, system_prompt, **kwargs)
