"""
Data Service API Example
數據服務API使用示例

Demonstrates how to use the Data Service API v2 endpoints
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:3003/api/v2"
# You would get this token from your authentication endpoint
JWT_TOKEN = "your-jwt-token-here"

# Headers for API requests
headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}


class DataAPIClient:
    """Client for interacting with the Data Service API"""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def get_market_data_history(
        self,
        symbol: str,
        interval: str = "1d",
        start_date: str = None,
        end_date: str = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Get historical market data for a symbol

        Args:
            symbol: Stock symbol (e.g., AAPL, MSFT, 0700.HK)
            interval: Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            page: Page number
            page_size: Records per page

        Returns:
            Dictionary containing historical data
        """
        params = {
            "interval": interval,
            "page": page,
            "page_size": page_size
        }

        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        url = f"{self.base_url}/market-data/{symbol}/history"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def get_real_time_data(self, symbol: str, fields: str = None) -> Dict[str, Any]:
        """
        Get real-time market data for a symbol

        Args:
            symbol: Stock symbol
            fields: Comma-separated list of fields to return

        Returns:
            Dictionary containing real-time data
        """
        params = {}
        if fields:
            params["fields"] = fields

        url = f"{self.base_url}/market-data/{symbol}/realtime"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def get_bulk_real_time_data(
        self,
        symbols: List[str],
        fields: str = None
    ) -> Dict[str, Any]:
        """
        Get real-time data for multiple symbols

        Args:
            symbols: List of stock symbols
            fields: Comma-separated list of fields to return

        Returns:
            Dictionary containing bulk real-time data
        """
        params = {"symbols": ",".join(symbols)}
        if fields:
            params["fields"] = fields

        url = f"{self.base_url}/market-data/bulk/realtime"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def get_market_stats(
        self,
        symbol: str,
        period: str = "1M"
    ) -> Dict[str, Any]:
        """
        Get market statistics for a symbol

        Args:
            symbol: Stock symbol
            period: Statistics period (1D, 1W, 1M, 3M, 6M, 1Y, ALL)

        Returns:
            Dictionary containing market statistics
        """
        params = {"period": period}
        url = f"{self.base_url}/market-data/{symbol}/stats"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def list_economic_indicators(
        self,
        category: str = None,
        country: str = "US"
    ) -> Dict[str, Any]:
        """
        List available economic indicators

        Args:
            category: Filter by category
            country: Country code

        Returns:
            Dictionary containing available indicators
        """
        params = {"country": country}
        if category:
            params["category"] = category

        url = f"{self.base_url}/economic-indicators/"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def get_economic_indicator_data(
        self,
        indicator: str,
        country: str = "US",
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        Get economic indicator data

        Args:
            indicator: Indicator code
            country: Country code
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary containing indicator data
        """
        params = {"country": country}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        url = f"{self.base_url}/economic-indicators/{indicator}/data"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def get_hibor_rates(
        self,
        tenor: str = "ON",
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        Get HIBOR rates

        Args:
            tenor: HIBOR tenor (ON, 1W, 1M, 3M, 6M, 12M)
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary containing HIBOR data
        """
        params = {"tenor": tenor}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        url = f"{self.base_url}/economic-indicators/hibor"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def create_export_job(self, export_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a data export job

        Args:
            export_request: Export request parameters

        Returns:
            Dictionary containing job information
        """
        url = f"{self.base_url}/data/export"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self.headers,
                json=export_request
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_export_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get export job status

        Args:
            job_id: Export job ID

        Returns:
            Dictionary containing job status
        """
        url = f"{self.base_url}/data/export/{job_id}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                return await response.json()

    async def list_export_jobs(
        self,
        status: str = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List export jobs

        Args:
            status: Filter by status
            limit: Maximum number of jobs

        Returns:
            Dictionary containing job list
        """
        params = {"limit": limit}
        if status:
            params["status"] = status

        url = f"{self.base_url}/data/export"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                response.raise_for_status()
                return await response.json()


async def example_usage():
    """Example usage of the Data API client"""

    # Create client instance
    client = DataAPIClient(BASE_URL, JWT_TOKEN)

    print("=== Data API Example ===\n")

    try:
        # 1. Get historical market data
        print("1. Getting historical market data for AAPL...")
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        historical_data = await client.get_market_data_history(
            symbol="AAPL",
            interval="1d",
            start_date=start_date,
            end_date=end_date,
            page_size=10
        )

        print(f"   Retrieved {len(historical_data['data'])} records")
        print(f"   Latest close: ${historical_data['data'][-1]['close']}")
        print()

        # 2. Get real-time data
        print("2. Getting real-time data for multiple symbols...")
        symbols = ["AAPL", "MSFT", "GOOGL"]
        realtime_data = await client.get_bulk_real_time_data(
            symbols=symbols,
            fields="price,change,change_percent,volume"
        )

        for symbol, data in realtime_data["data"].items():
            print(f"   {symbol}: ${data['price']} ({data['change_percent']:+.2f}%)")
        print()

        # 3. Get market statistics
        print("3. Getting market statistics for AAPL...")
        stats = await client.get_market_stats("AAPL", period="1M")

        print(f"   Current price: ${stats['price']['current']}")
        print(f"   Period high: ${stats['price']['high']}")
        print(f"   Period low: ${stats['price']['low']}")
        print(f"   Volatility: {stats['volatility']['daily']:.2f}%")
        print()

        # 4. List economic indicators
        print("4. Listing available economic indicators...")
        indicators = await client.list_economic_indicators(category="interest_rates")

        print("   Available indicators:")
        for category, inds in indicators["indicators"].items():
            print(f"     {category}:")
            for code, info in inds.items():
                print(f"       - {code}: {info['name']}")
        print()

        # 5. Get HIBOR rates
        print("5. Getting HIBOR rates...")
        hibor_data = await client.get_hibor_rates(tenor="3M")

        if hibor_data["data"]:
            latest_rate = hibor_data["data"][-1]
            print(f"   Latest 3M HIBOR: {latest_rate['rate']}%")
        print()

        # 6. Create export job
        print("6. Creating data export job...")
        export_request = {
            "data_type": "market_data",
            "symbols": ["AAPL", "MSFT"],
            "start_date": start_date,
            "end_date": end_date,
            "format": "csv",
            "include_metadata": True
        }

        job = await client.create_export_job(export_request)
        print(f"   Export job created: {job['job_id']}")
        print(f"   Status: {job['status']}")
        print(f"   Estimated time: {job['estimated_time']}")
        print()

        # 7. Check job status (polling)
        print("7. Checking export job status...")
        import time
        time.sleep(2)  # Wait a bit for processing

        job_status = await client.get_export_job_status(job["job_id"])
        print(f"   Job status: {job_status['status']}")
        print(f"   Progress: {job_status['progress']}%")

        if job_status["status"] == "completed":
            print(f"   Download URL: /api/v2/data/export/{job['job_id']}/download")
            print(f"   File size: {job_status['file_size']} bytes")
        print()

        # 8. List all export jobs
        print("8. Listing all export jobs...")
        jobs = await client.list_export_jobs()

        print(f"   Total jobs: {jobs['total']}")
        for job in jobs["jobs"][:5]:  # Show first 5 jobs
            print(f"   - {job['job_id']}: {job['status']} ({job['data_type']})")

    except aiohttp.ClientResponseError as e:
        print(f"   API Error: {e.status} - {e.message}")
    except Exception as e:
        print(f"   Error: {str(e)}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())