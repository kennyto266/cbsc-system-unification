"""
Data API Tests
數據API測試

Test suite for the Data Service API v2 endpoints
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.main import app
from src.models.user import User

# Create test client
client = TestClient(app)

# Test user data
test_user = User(
    id=1,
    username="testuser",
    email="test@example.com",
    is_active=True
)

# Mock authentication
def get_current_user_mock():
    return test_user

# Mock data
mock_market_data = [
    {
        "time": "2024-01-01T00:00:00Z",
        "open": 185.50,
        "high": 187.20,
        "low": 184.80,
        "close": 186.90,
        "volume": 52345678,
        "adjusted_close": 186.90
    },
    {
        "time": "2024-01-02T00:00:00Z",
        "open": 186.90,
        "high": 188.00,
        "low": 185.50,
        "close": 187.50,
        "volume": 45678901,
        "adjusted_close": 187.50
    }
]

mock_realtime_data = {
    "price": 195.50,
    "volume": 15234567,
    "bid": 195.45,
    "ask": 195.55,
    "high": 196.00,
    "low": 194.80,
    "timestamp": datetime.utcnow().isoformat()
}

mock_economic_data = [
    {
        "time": "2024-01-01T00:00:00Z",
        "value": 5.25,
        "unit": "percent",
        "source": "Federal Reserve"
    }
]


class TestMarketDataEndpoints:
    """Test market data endpoints"""

    @patch('src.api.data.market_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    @patch('src.api.data.market_data_endpoints.influxdb_service')
    @patch('src.api.data.market_data_endpoints.cache_service')
    def test_get_market_data_history_success(self, mock_cache, mock_influxdb, mock_auth):
        """Test successful retrieval of market data history"""
        # Setup mocks
        mock_cache.get.return_value = None
        mock_influxdb.get_market_data.return_value = mock_market_data
        mock_cache.set.return_value = True

        # Make request
        response = client.get(
            "/api/v2/market-data/AAPL/history",
            params={
                "interval": "1d",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "page": 1,
                "page_size": 100
            }
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["interval"] == "1d"
        assert len(data["data"]) == 2
        assert "pagination" in data
        assert "metadata" in data

    @patch('src.api.data.market_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_get_market_data_history_invalid_date_format(self, mock_auth):
        """Test with invalid date format"""
        response = client.get(
            "/api/v2/market-data/AAPL/history",
            params={
                "start_date": "2024/01/01",  # Invalid format
                "end_date": "2024-01-31"
            }
        )

        assert response.status_code == 400
        assert "Invalid start_date format" in response.json()["detail"]

    @patch('src.api.data.market_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_get_market_data_history_invalid_interval(self, mock_auth):
        """Test with invalid interval"""
        response = client.get(
            "/api/v2/market-data/AAPL/history",
            params={
                "interval": "2d"  # Invalid interval
            }
        )

        assert response.status_code == 422  # Validation error

    @patch('src.api.data.market_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    @patch('src.api.data.market_data_endpoints.influxdb_service')
    @patch('src.api.data.market_data_endpoints.cache_service')
    def test_get_real_time_data_success(self, mock_cache, mock_influxdb, mock_auth):
        """Test successful retrieval of real-time data"""
        # Setup mocks
        mock_cache.get.return_value = None
        mock_influxdb.get_latest_market_data.return_value = mock_realtime_data
        mock_influxdb.get_previous_close.return_value = 194.30
        mock_cache.set.return_value = True

        # Make request
        response = client.get("/api/v2/market-data/AAPL/realtime")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "price" in data
        assert "change" in data
        assert "change_percent" in data
        assert "timestamp" in data

    @patch('src.api.data.market_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    @patch('src.api.data.market_data_endpoints.influxdb_service')
    def test_get_real_time_data_not_found(self, mock_influxdb, mock_auth):
        """Test when no data is found"""
        mock_influxdb.get_latest_market_data.return_value = None

        response = client.get("/api/v2/market-data/INVALID/realtime")

        assert response.status_code == 404
        assert "No real-time data found" in response.json()["detail"]

    @patch('src.api.data.market_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    @patch('src.api.data.market_data_endpoints.influxdb_service')
    @patch('src.api.data.market_data_endpoints.cache_service')
    def test_get_bulk_real_time_data_success(self, mock_cache, mock_influxdb, mock_auth):
        """Test bulk real-time data retrieval"""
        # Setup mocks
        mock_cache.get.return_value = None
        mock_influxdb.get_latest_market_data.return_value = mock_realtime_data
        mock_influxdb.get_previous_close.return_value = 194.30
        mock_cache.set.return_value = True

        # Make request
        response = client.get(
            "/api/v2/market-data/bulk/realtime",
            params={"symbols": "AAPL,MSFT,GOOGL"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 3
        assert "symbols_requested" in data
        assert data["symbols_requested"] == 3

    @patch('src.api.data.market_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_get_bulk_real_time_data_too_many_symbols(self, mock_auth):
        """Test with too many symbols"""
        symbols = ",".join([f"SYM{i}" for i in range(101)])  # 101 symbols

        response = client.get(
            "/api/v2/market-data/bulk/realtime",
            params={"symbols": symbols}
        )

        assert response.status_code == 400
        assert "Maximum 100 symbols" in response.json()["detail"]


class TestEconomicIndicatorsEndpoints:
    """Test economic indicators endpoints"""

    @patch('src.api.data.economic_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_list_economic_indicators_success(self, mock_auth):
        """Test listing economic indicators"""
        response = client.get("/api/v2/economic-indicators/")

        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data
        assert "categories" in data
        assert isinstance(data["indicators"], dict)
        assert isinstance(data["categories"], list)

    @patch('src.api.data.economic_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_list_economic_indicators_with_category(self, mock_auth):
        """Test listing indicators with category filter"""
        response = client.get(
            "/api/v2/economic-indicators/",
            params={"category": "interest_rates"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "interest_rates" in data["indicators"]
        assert len(data["indicators"]) == 1

    @patch('src.api.data.economic_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_list_economic_indicators_invalid_category(self, mock_auth):
        """Test with invalid category"""
        response = client.get(
            "/api/v2/economic-indicators/",
            params={"category": "invalid_category"}
        )

        assert response.status_code == 400
        assert "Invalid category" in response.json()["detail"]

    @patch('src.api.data.economic_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    @patch('src.api.data.economic_data_endpoints.influxdb_service')
    @patch('src.api.data.economic_data_endpoints.cache_service')
    def test_get_economic_indicator_data_success(self, mock_cache, mock_influxdb, mock_auth):
        """Test getting economic indicator data"""
        # Setup mocks
        mock_cache.get.return_value = None
        mock_influxdb.get_economic_data.return_value = mock_economic_data
        mock_cache.set.return_value = True

        # Make request
        response = client.get("/api/v2/economic-indicators/Fed_Funds/data")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["indicator"] == "Fed_Funds"
        assert "data" in data
        assert "statistics" in data
        assert "metadata" in data

    @patch('src.api.data.economic_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_get_economic_indicator_data_invalid_indicator(self, mock_auth):
        """Test with invalid indicator"""
        response = client.get("/api/v2/economic-indicators/INVALID/data")

        assert response.status_code == 400
        assert "Invalid indicator" in response.json()["detail"]

    @patch('src.api.data.economic_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    @patch('src.api.data.economic_data_endpoints.cache_service')
    def test_get_hibor_rates_success(self, mock_cache, mock_auth):
        """Test getting HIBOR rates"""
        # Setup mock
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True

        # Make request
        response = client.get(
            "/api/v2/economic-indicators/hibor",
            params={"tenor": "1M"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["tenor"] == "1M"
        assert data["currency"] == "HKD"
        assert "data" in data
        assert "statistics" in data

    @patch('src.api.data.economic_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    @patch('src.api.data.economic_data_endpoints.cache_service')
    def test_get_economic_dashboard_success(self, mock_cache, mock_auth):
        """Test economic dashboard"""
        # Setup mock
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True

        # Make request
        response = client.get("/api/v2/economic-indicators/dashboard")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "dashboard" in data
        assert "market_context" in data
        assert isinstance(data["dashboard"], dict)


class TestDataExportEndpoints:
    """Test data export endpoints"""

    @patch('src.api.data.export_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_create_export_job_success(self, mock_auth):
        """Test creating export job"""
        export_request = {
            "data_type": "market_data",
            "symbols": ["AAPL", "MSFT"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "format": "csv"
        }

        response = client.post(
            "/api/v2/data/export",
            json=export_request
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        assert "estimated_time" in data

    @patch('src.api.data.export_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_create_export_job_missing_data_type(self, mock_auth):
        """Test creating export job without data_type"""
        export_request = {
            "symbols": ["AAPL", "MSFT"],
            "format": "csv"
        }

        response = client.post(
            "/api/v2/data/export",
            json=export_request
        )

        assert response.status_code == 400
        assert "data_type is required" in response.json()["detail"]

    @patch('src.api.data.export_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_get_export_job_status_success(self, mock_auth):
        """Test getting export job status"""
        # First create a job
        export_request = {
            "data_type": "market_data",
            "symbols": ["AAPL"],
            "format": "csv"
        }
        create_response = client.post("/api/v2/data/export", json=export_request)
        job_id = create_response.json()["job_id"]

        # Get status
        response = client.get(f"/api/v2/data/export/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "progress" in data

    @patch('src.api.data.export_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_get_export_job_status_not_found(self, mock_auth):
        """Test getting status of non-existent job"""
        response = client.get("/api/v2/data/export/invalid-job-id")

        assert response.status_code == 404
        assert "Export job not found" in response.json()["detail"]

    @patch('src.api.data.export_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_list_export_jobs_success(self, mock_auth):
        """Test listing export jobs"""
        response = client.get("/api/v2/data/export")

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert isinstance(data["jobs"], list)

    @patch('src.api.data.export_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_list_export_jobs_with_status_filter(self, mock_auth):
        """Test listing export jobs with status filter"""
        response = client.get(
            "/api/v2/data/export",
            params={"status": "completed"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        # All returned jobs should have the specified status
        for job in data["jobs"]:
            assert job["status"] == "completed"


class TestDataAPIInfoEndpoints:
    """Test data API information endpoints"""

    def test_get_data_api_version(self):
        """Test getting API version info"""
        response = client.get("/api/v2/data/version")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "name" in data
        assert "features" in data
        assert data["version"] == "2.0.0"

    @patch('src.api.data.routes.InfluxDBService')
    @patch('src.api.data.routes.CacheService')
    def test_health_check_success(self, mock_cache, mock_influxdb):
        """Test API health check"""
        # Setup mocks
        mock_cache_instance = Mock()
        mock_cache_instance.set.return_value = True
        mock_cache_instance.get.return_value = "ok"
        mock_cache.return_value = mock_cache_instance

        response = client.get("/api/v2/data/health")

        assert response.status_code == 200
        data = response.json()
        assert "api" in data
        assert "services" in data
        assert "timestamp" in data

    def test_get_market_data_info(self):
        """Test getting market data service info"""
        response = client.get("/api/v2/data/info/market")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "market_data"
        assert "capabilities" in data
        assert "rate_limits" in data
        assert "data_retention" in data

    def test_get_economic_data_info(self):
        """Test getting economic data service info"""
        response = client.get("/api/v2/data/info/economic")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "economic_indicators"
        assert "categories" in data
        assert "countries" in data

    def test_get_export_service_info(self):
        """Test getting export service info"""
        response = client.get("/api/v2/data/info/export")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "data_export"
        assert "formats" in data
        assert "limits" in data
        assert "features" in data


class TestErrorHandling:
    """Test error handling across all endpoints"""

    def test_unauthorized_access(self):
        """Test access without authentication"""
        # This would require removing the auth mock
        response = client.get("/api/v2/market-data/AAPL/history")

        # Should return 401 or 403 depending on implementation
        assert response.status_code in [401, 403]

    @patch('src.api.data.market_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_server_error_handling(self, mock_auth):
        """Test handling of server errors"""
        with patch('src.api.data.market_data_endpoints.influxdb_service') as mock_service:
            mock_service.get_market_data.side_effect = Exception("Database connection failed")

            response = client.get("/api/v2/market-data/AAPL/history")

            assert response.status_code == 500
            assert "Failed to fetch market data" in response.json()["detail"]

    @patch('src.api.data.market_data_endpoints.get_current_user', side_effect=get_current_user_mock)
    def test_rate_limiting(self, mock_auth):
        """Test rate limiting (if implemented)"""
        # This test would require implementing rate limiting middleware
        # and making many rapid requests
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])