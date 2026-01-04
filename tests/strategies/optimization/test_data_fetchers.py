"""Tests for data fetchers module"""
import pytest
from src.strategies.optimization.data.fetchers import YahooFinanceFetcher


def test_yahoo_fetcher_initialization():
    """Test Yahoo Finance fetcher can be initialized"""
    fetcher = YahooFinanceFetcher()
    assert fetcher is not None
    assert fetcher.base_url == "https://query1.finance.yahoo.com"


def test_yahoo_fetcher_fetch_single_ticker():
    """Test fetching single ticker data"""
    fetcher = YahooFinanceFetcher()
    data = fetcher.fetch("AAPL", period="1mo")
    assert data is not None
    assert len(data) > 0
    assert "close" in data.columns
