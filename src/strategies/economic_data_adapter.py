"""
Economic Data Adapter

This module provides data access and processing for economic indicators
used by fundamental strategies.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import requests
import warnings

try:
    from .data_loader import DataLoader
except ImportError:
    DataLoader = None


class EconomicDataAdapter:
    """
    Adapter for accessing and processing economic data
    """

    def __init__(self, data_loader=None):
        """
        Initialize Economic Data Adapter

        Args:
            data_loader: Optional data loader instance
        """
        self.data_loader = data_loader
        self.cache = {}

    def get_hibor_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get HIBOR rate data

        Args:
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with HIBOR rate data
        """
        cache_key = f"hibor_{start_date}_{end_date}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Try to get from data loader
        if self.data_loader:
            data = self.data_loader.load_hibor_rates(start_date, end_date)
            if data is not None:
                self.cache[cache_key] = data
                return data

        # Fallback to mock data for testing
        data = self._generate_mock_hibor_data(start_date, end_date)
        self.cache[cache_key] = data

        return data

    def get_gdp_data(self, start_date: datetime, end_date: datetime, frequency: str = "quarterly") -> pd.DataFrame:
        """
        Get GDP growth data

        Args:
            start_date: Start date for data
            end_date: End date for data
            frequency: Data frequency ('monthly', 'quarterly', 'annual')

        Returns:
            DataFrame with GDP data
        """
        cache_key = f"gdp_{frequency}_{start_date}_{end_date}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Try to get from data loader
        if self.data_loader:
            data = self.data_loader.load_gdp_data(start_date, end_date, frequency)
            if data is not None:
                self.cache[cache_key] = data
                return data

        # Fallback to mock data
        data = self._generate_mock_gdp_data(start_date, end_date, frequency)
        self.cache[cache_key] = data

        return data

    def get_visitor_arrivals_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get Hong Kong visitor arrivals data

        Args:
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with visitor arrival data
        """
        cache_key = f"visitors_{start_date}_{end_date}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Try to get from data loader
        if self.data_loader:
            data = self.data_loader.load_visitor_arrivals(start_date, end_date)
            if data is not None:
                self.cache[cache_key] = data
                return data

        # Fallback to mock data
        data = self._generate_mock_visitor_data(start_date, end_date)
        self.cache[cache_key] = data

        return data

    def get_pmi_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get PMI data

        Args:
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with PMI data
        """
        cache_key = f"pmi_{start_date}_{end_date}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Try to get from data loader
        if self.data_loader:
            data = self.data_loader.load_pmi_data(start_date, end_date)
            if data is not None:
                self.cache[cache_key] = data
                return data

        # Fallback to mock data
        data = self._generate_mock_pmi_data(start_date, end_date)
        self.cache[cache_key] = data

        return data

    def get_unemployment_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get unemployment rate data

        Args:
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with unemployment data
        """
        cache_key = f"unemployment_{start_date}_{end_date}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Try to get from data loader
        if self.data_loader:
            data = self.data_loader.load_unemployment_data(start_date, end_date)
            if data is not None:
                self.cache[cache_key] = data
                return data

        # Fallback to mock data
        data = self._generate_mock_unemployment_data(start_date, end_date)
        self.cache[cache_key] = data

        return data

    def get_all_economic_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get all available economic data

        Args:
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with all economic indicators
        """
        all_data = pd.DataFrame(index=pd.date_range(start=start_date, end=end_date, freq='D'))

        # Get each economic indicator
        indicators = [
            ('hibor_rate', self.get_hibor_data),
            ('gdp_growth', lambda s, e: self.get_gdp_data(s, e, 'quarterly')),
            ('visitor_arrivals', self.get_visitor_arrivals_data),
            ('pmi_manufacturing', self.get_pmi_data),
            ('pmi_services', self.get_pmi_data),
            ('unemployment_rate', self.get_unemployment_data)
        ]

        for indicator_name, indicator_func in indicators:
            try:
                data = indicator_func(start_date, end_date)
                if data is not None and not data.empty:
                    # Resample to daily frequency if needed
                    if data.index.freq != 'D':
                        data = data.resample('D').asfreq()

                    # Merge with main dataframe
                    all_data = all_data.join(data, how='left')
            except Exception as e:
                warnings.warn(f"Failed to load {indicator_name}: {e}")

        return all_data

    def _generate_mock_hibor_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Generate mock HIBOR data for testing"""
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        np.random.seed(42)

        # Generate realistic HIBOR rates (2-6% range)
        base_rate = 4.0
        hibor_rates = base_rate + np.sin(np.linspace(0, 4*np.pi, len(dates))) * 1.5
        hibor_rates += np.random.normal(0, 0.2, len(dates))
        hibor_rates = np.clip(hibor_rates, 1.0, 8.0)

        return pd.DataFrame({
            'date': dates,
            'hibor_rate': hibor_rates
        }).set_index('date')

    def _generate_mock_gdp_data(self, start_date: datetime, end_date: datetime, frequency: str = "quarterly") -> pd.DataFrame:
        """Generate mock GDP data"""
        if frequency == 'quarterly':
            dates = pd.date_range(start=start_date, end=end_date, freq='Q')
        elif frequency == 'monthly':
            dates = pd.date_range(start=start_date, end=end_date, freq='M')
        else:  # annual
            dates = pd.date_range(start=start_date, end=end_date, freq='A')

        np.random.seed(42)

        # Generate realistic GDP growth rates (-2% to 6%)
        base_growth = 2.5
        gdp_growth = base_growth + np.sin(np.linspace(0, 2*np.pi, len(dates))) * 2.0
        gdp_growth += np.random.normal(0, 1.0, len(dates))
        gdp_growth = np.clip(gdp_growth, -5.0, 8.0)

        return pd.DataFrame({
            'date': dates,
            'gdp_growth': gdp_growth,
            'frequency': frequency
        }).set_index('date')

    def _generate_mock_visitor_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Generate mock visitor arrival data"""
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        np.random.seed(42)

        # Generate realistic visitor numbers (2-8 million)
        base_visitors = 4.5  # million
        seasonal_factor = 1.0 + 0.5 * np.sin(np.linspace(0, 2*np.pi, len(dates)))
        trend_factor = np.linspace(1.0, 1.2, len(dates))

        visitors = base_visitors * seasonal_factor * trend_factor
        visitors += np.random.normal(0, 0.5, len(dates))
        visitors = np.maximum(visitors, 1.0)

        return pd.DataFrame({
            'date': dates,
            'visitor_arrivals': visitors * 1e6  # Convert to actual numbers
        }).set_index('date')

    def _generate_mock_pmi_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Generate mock PMI data"""
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        np.random.seed(42)

        # Generate realistic PMI values (35-65 range)
        base_pmi = 50.0
        business_cycle = 10 * np.sin(np.linspace(0, 4*np.pi, len(dates)))

        manufacturing_pmi = base_pmi + business_cycle + np.random.normal(0, 3, len(dates))
        services_pmi = base_pmi + business_cycle * 0.8 + np.random.normal(0, 2.5, len(dates))

        manufacturing_pmi = np.clip(manufacturing_pmi, 30, 70)
        services_pmi = np.clip(services_pmi, 35, 65)

        return pd.DataFrame({
            'date': dates,
            'pmi_manufacturing': manufacturing_pmi,
            'pmi_services': services_pmi
        }).set_index('date')

    def _generate_mock_unemployment_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Generate mock unemployment data"""
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        np.random.seed(42)

        # Generate realistic unemployment rates (2.5% - 7.5%)
        base_unemployment = 4.5
        cyclical_factor = 2.0 * np.sin(np.linspace(0, 3*np.pi, len(dates)))
        trend_factor = np.linspace(0, 1.0, len(dates))

        unemployment = base_unemployment + cyclical_factor + trend_factor
        unemployment += np.random.normal(0, 0.5, len(dates))
        unemployment = np.clip(unemployment, 2.0, 10.0)

        return pd.DataFrame({
            'date': dates,
            'unemployment_rate': unemployment
        }).set_index('date')

    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()

    def get_data_summary(self) -> Dict[str, Dict]:
        """
        Get summary of available data

        Returns:
            Dictionary with data summary
        """
        summary = {
            'cache_size': len(self.cache),
            'cached_indicators': list(self.cache.keys()),
            'data_loader_available': self.data_loader is not None
        }

        return summary


# Singleton instance for global access
_economic_data_adapter = None


def get_economic_data_adapter() -> EconomicDataAdapter:
    """Get or create economic data adapter singleton"""
    global _economic_data_adapter
    if _economic_data_adapter is None:
        _economic_data_adapter = EconomicDataAdapter()
    return _economic_data_adapter


__all__ = [
    'EconomicDataAdapter',
    'get_economic_data_adapter'
]