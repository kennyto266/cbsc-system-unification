#!/usr / bin / env python3
"""
股票API單元測試
Unit tests for Stock API functionality
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

# Add simplified_system to path
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent.parent / "simplified_system")
)

from src.api.stock_api import StockDataAPI, get_hk_stock_data, get_stock_data


class TestStockDataAPI:
    """股票數據API測試類"""

    @pytest.fixture
    def api_client(self):
        """創建API客戶端fixture"""
        return StockDataAPI()

    @pytest.fixture
    def mock_response(self):
        """模擬API響應fixture"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "close": {
                    "2024 - 01 - 01": 320.50,
                    "2024 - 01 - 02": 318.20,
                    "2024 - 01 - 03": 325.80,
                }
            }
        }
        return mock_resp

    def test_init(self, api_client):
        """測試API客戶端初始化"""
        assert api_client.api_base_url is not None
        assert api_client.request_timeout > 0
        assert isinstance(api_client.cache, dict)
        assert api_client.cache_timeout > 0

    def test_get_cache_key(self, api_client):
        """測試緩存鍵生成"""
        cache_key = api_client._get_cache_key("0700.HK", 30)
        assert cache_key == "0700.HK_30"

        # 測試不同參數
        cache_key2 = api_client._get_cache_key("0941.HK", 365)
        assert cache_key2 == "0941.HK_365"
        assert cache_key != cache_key2

    def test_is_cache_valid_empty(self, api_client):
        """測試空緩存驗證"""
        assert not api_client._is_cache_valid("nonexistent_key")

    def test_is_cache_valid_expired(self, api_client):
        """測試過期緩存驗證"""
        # 手動設置一個過期的緩存項
        import time

        api_client.cache["test_key"] = {
            "data": {"test": "data"},
            "timestamp": time.time() - (api_client.cache_timeout + 100),
        }
        assert not api_client._is_cache_valid("test_key")

    def test_is_cache_valid_fresh(self, api_client):
        """測試新鮮緩存驗證"""
        import time

        api_client.cache["test_key"] = {
            "data": {"test": "data"},
            "timestamp": time.time() - 100,  # 100秒前，應該還是新的
        }
        assert api_client._is_cache_valid("test_key")

    @patch("requests.get")
    def test_get_stock_data_success(self, mock_get, api_client, mock_response):
        """測試成功獲取股票數據"""
        mock_get.return_value = mock_response

        result = api_client.get_stock_data("0700.HK", 30)

        assert result is not None
        assert "data" in result
        assert "close" in result["data"]
        assert isinstance(result["data"]["close"], dict)

        # 驗證API調用
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "symbol" in call_args[1]
        assert "duration" in call_args[1]

    @patch("requests.get")
    def test_get_stock_data_http_error(self, mock_get, api_client):
        """測試HTTP錯誤處理"""
        mock_get.return_value.status_code = 404

        result = api_client.get_stock_data("INVALID.HK", 30)

        assert result is None

    @patch("requests.get")
    def test_get_stock_data_invalid_format(self, mock_get, api_client):
        """測試無效數據格式處理"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"invalid": "format"}
        mock_get.return_value = mock_resp

        result = api_client.get_stock_data("0700.HK", 30)

        assert result is None

    @patch("requests.get")
    def test_get_stock_data_timeout(self, mock_get, api_client):
        """測試請求超時處理"""
        mock_get.side_effect = requests.exceptions.Timeout()

        result = api_client.get_stock_data("0700.HK", 30)

        assert result is None

    @patch("requests.get")
    def test_get_stock_data_caching(self, mock_get, api_client, mock_response):
        """測試緩存功能"""
        mock_get.return_value = mock_response

        # 第一次調用
        result1 = api_client.get_stock_data("0700.HK", 30)
        assert result1 is not None
        assert mock_get.call_count == 1

        # 第二次調用應該使用緩存
        result2 = api_client.get_stock_data("0700.HK", 30)
        assert result2 is not None
        assert result1 == result2
        assert mock_get.call_count == 1  # 沒有新的API調用

    def test_get_stock_prices_dataframe_no_data(self, api_client):
        """測試無數據時DataFrame轉換"""
        result = api_client.get_stock_prices_dataframe("0700.HK", 30)
        assert result is None

    @patch("requests.get")
    def test_get_stock_prices_dataframe_success(
        self, mock_get, api_client, mock_response
    ):
        """測試成功DataFrame轉換"""
        mock_get.return_value = mock_response

        result = api_client.get_stock_prices_dataframe("0700.HK", 30)

        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert "price" in result.columns
        assert len(result) > 0
        assert isinstance(result.index, pd.DatetimeIndex)

    @patch("requests.get")
    def test_get_multiple_stocks(self, mock_get, api_client, mock_response):
        """測試批量獲取股票數據"""
        mock_get.return_value = mock_response

        symbols = ["0700.HK", "0941.HK"]
        results = api_client.get_multiple_stocks(symbols, 30)

        assert isinstance(results, dict)
        assert len(results) == 2
        assert "0700.HK" in results
        assert "0941.HK" in results
        assert isinstance(results["0700.HK"], pd.DataFrame)

    @patch("requests.get")
    def test_get_real_time_price(self, mock_get, api_client, mock_response):
        """測試獲取實時價格"""
        mock_response.json.return_value = {
            "data": {
                "close": {
                    "2024 - 01 - 01": 320.50,
                    "2024 - 01 - 02": 325.80,
                }
            }
        }
        mock_get.return_value = mock_response

        result = api_client.get_real_time_price("0700.HK")

        assert result is not None
        assert isinstance(result, float)
        assert result > 0


class TestStockAPIConvenienceFunctions:
    """測試股票API便捷函數"""

    @patch("src.api.stock_api.stock_api.get_stock_data")
    def test_get_stock_data_function(self, mock_get):
        """測試get_stock_data便捷函數"""
        mock_get.return_value = {"test": "data"}

        result = get_stock_data("0700.HK", 30)

        assert result == {"test": "data"}
        mock_get.assert_called_once_with("0700.HK", 30)

    @patch("src.api.stock_api.stock_api.get_stock_data")
    def test_get_hk_stock_data_function(self, mock_get):
        """測試get_hk_stock_data便捷函數"""
        mock_get.return_value = {"test": "data"}

        result = get_hk_stock_data("0700.HK", 30)

        assert result == {"test": "data"}
        mock_get.assert_called_once_with("0700.HK", 30)


class TestStockAPIEdgeCases:
    """測試股票API邊界情況"""

    @pytest.fixture
    def api_client(self):
        return StockDataAPI()

    def test_empty_symbol(self, api_client):
        """測試空股票代碼"""
        with patch("requests.get") as mock_get:
            mock_get.return_value = Mock(status_code = 404)
            result = api_client.get_stock_data("", 30)
            assert result is None

    def test_invalid_symbol_format(self, api_client):
        """測試無效股票代碼格式"""
        with patch("requests.get") as mock_get:
            mock_get.return_value = Mock(status_code = 404)
            result = api_client.get_stock_data("INVALID_SYMBOL", 30)
            assert result is None

    def test_zero_duration(self, api_client):
        """測試零持續時間"""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": {"close": {}}}
            mock_get.return_value = mock_response

            result = api_client.get_stock_data("0700.HK", 0)
            assert result is not None

    def test_negative_duration(self, api_client):
        """測試負數持續時間"""
        with patch("requests.get") as mock_get:
            mock_get.return_value = Mock(status_code = 404)
            result = api_client.get_stock_data("0700.HK", -10)
            assert result is None


@pytest.mark.integration
class TestStockAPIIntegration:
    """股票API集成測試（需要真實API）"""

    @pytest.mark.slow
    @pytest.mark.external
    def test_real_api_call(self):
        """測試真實API調用（標記為slow和external）"""
        # 這個測試需要真實的API連接，只在特定情況下運行
        pytest.skip("Skip real API call in unit tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
