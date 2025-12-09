#!/usr/bin/env python3
"""
Long-Term Data Storage Architecture
Optimized storage for 5+ year backtesting using Parquet with partitioning
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Union
import yfinance as yf
import logging

try:
    import pyarrow
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False
    print("Warning: PyArrow not available. Install with: pip install pyarrow")

try:
    import fastparquet
    FASTPARQUET_AVAILABLE = True
except ImportError:
    FASTPARQUET_AVAILABLE = False

logger = logging.getLogger(__name__)


class LongTermDataStorage:
    """
    Long-term data storage system optimized for 5+ year backtesting

    Features:
    - Parquet format for optimal compression and performance
    - Year-based partitioning for efficient querying
    - Multi-tier caching strategy
    - Data validation and quality checks
    - Incremental updates support
    """

    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = Path("C:/Users/Penguin8n/CODEX--/data/long_term_storage")
        else:
            base_path = Path(base_path)

        self.base_path = Path(base_path)
        self.cache_path = self.base_path / "cache"
        self.raw_path = self.base_path / "raw"
        self.processed_path = self.base_path / "processed"
        self.metadata_path = self.base_path / "metadata"

        # Create directory structure
        self._create_directory_structure()

        # Validate Parquet availability
        if not PARQUET_AVAILABLE and not FASTPARQUET_AVAILABLE:
            raise ImportError("Neither PyArrow nor fastparquet available. Install one with: pip install pyarrow or pip install fastparquet")

        logger.info(f"Long-term storage initialized at: {self.base_path}")

    def _create_directory_structure(self):
        """Create the directory structure for data storage"""
        directories = [
            self.base_path,
            self.cache_path,
            self.raw_path,
            self.processed_path,
            self.metadata_path
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_partition_path(self, symbol: str, year: int, data_type: str = "processed") -> Path:
        """Get the partition path for a symbol and year"""
        # Normalize symbol (remove .HK for cleaner paths)
        clean_symbol = symbol.replace('.HK', '').lower()
        return self.processed_path / data_type / f"symbol={clean_symbol}" / f"year={year}"

    def store_historical_data(
        self,
        symbol: str,
        data: pd.DataFrame,
        data_type: str = "daily",
        overwrite: bool = False
    ) -> Dict[str, any]:
        """
        Store historical data with year-based partitioning

        Args:
            symbol: Stock symbol (e.g., '0700.HK')
            data: DataFrame with datetime index and OHLCV columns
            data_type: Type of data (daily, weekly, monthly)
            overwrite: Whether to overwrite existing data

        Returns:
            Storage metadata and statistics
        """
        try:
            # Validate input data
            self._validate_input_data(data)

            # Group data by year for partitioning
            data_by_year = {}
            for year, year_data in data.groupby(data.index.year):
                data_by_year[year] = year_data.copy()

            storage_stats = {
                'symbol': symbol,
                'total_records': len(data),
                'years_stored': list(data_by_year.keys()),
                'date_range': {
                    'start': str(data.index.min().date()),
                    'end': str(data.index.max().date())
                },
                'partitions_created': 0,
                'storage_size_mb': 0,
                'compression_ratio': 0
            }

            # Store each year's data in separate partition
            for year, year_data in data_by_year.items():
                partition_path = self.get_partition_path(symbol, year, data_type)
                partition_path.mkdir(parents=True, exist_ok=True)

                file_path = partition_path / f"data.parquet"

                # Check if file exists and handle overwrite logic
                if file_path.exists() and not overwrite:
                    logger.info(f"Skipping existing data for {symbol} year {year}")
                    continue

                # Optimize data types for storage
                optimized_data = self._optimize_dtypes(year_data)

                # Add metadata columns
                optimized_data['symbol'] = symbol
                optimized_data['data_type'] = data_type
                optimized_data['year'] = year
                optimized_data['ingestion_date'] = datetime.now()

                # Store as Parquet with compression
                original_size = optimized_data.memory_usage(deep=True).sum()

                if PARQUET_AVAILABLE:
                    optimized_data.to_parquet(
                        file_path,
                        engine='pyarrow',
                        compression='snappy',
                        index=True
                    )
                else:
                    optimized_data.to_parquet(
                        file_path,
                        engine='fastparquet',
                        compression='snappy',
                        index=True
                    )

                # Calculate storage statistics
                file_size = file_path.stat().st_size
                storage_stats['storage_size_mb'] += file_size / (1024 * 1024)
                storage_stats['partitions_created'] += 1

                compression_ratio = (original_size / file_size) if file_size > 0 else 0
                storage_stats['compression_ratio'] = max(storage_stats['compression_ratio'], compression_ratio)

                logger.info(f"Stored {len(year_data)} records for {symbol} year {year}")

            # Store metadata
            self._store_metadata(symbol, storage_stats, data_type)

            logger.info(f"Successfully stored {storage_stats['total_records']} records for {symbol}")
            return storage_stats

        except Exception as e:
            logger.error(f"Failed to store data for {symbol}: {e}")
            raise

    def load_historical_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        data_type: str = "daily"
    ) -> pd.DataFrame:
        """
        Load historical data from partitioned storage

        Args:
            symbol: Stock symbol
            start_date: Start date for data loading
            end_date: End date for data loading
            data_type: Type of data to load

        Returns:
            DataFrame with requested historical data
        """
        try:
            # Determine which years to load
            if start_date is None and end_date is None:
                # Load all available data
                symbol_path = self.processed_path / data_type / f"symbol={symbol.replace('.HK', '').lower()}"
                if not symbol_path.exists():
                    return pd.DataFrame()

                year_partitions = [int(p.name.replace('year=', ''))
                                 for p in symbol_path.iterdir()
                                 if p.name.startswith('year=')]
            else:
                # Load specific date range
                start_date = start_date or date(2000, 1, 1)
                end_date = end_date or date.today()

                years = range(start_date.year, end_date.year + 1)
                year_partitions = [year for year in years
                                 if self.get_partition_path(symbol, year, data_type).exists()]

            if not year_partitions:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            # Load data from relevant partitions
            data_frames = []
            for year in sorted(year_partitions):
                partition_path = self.get_partition_path(symbol, year, data_type)
                file_path = partition_path / "data.parquet"

                if file_path.exists():
                    try:
                        year_data = pd.read_parquet(file_path)
                        data_frames.append(year_data)
                    except Exception as e:
                        logger.warning(f"Failed to load data for {symbol} year {year}: {e}")

            if not data_frames:
                logger.warning(f"No valid data found for {symbol}")
                return pd.DataFrame()

            # Combine all year data
            combined_data = pd.concat(data_frames, ignore_index=False)
            combined_data = combined_data.sort_index()

            # Apply date filtering if specified
            if start_date or end_date:
                date_mask = pd.Series(True, index=combined_data.index)
                if start_date:
                    date_mask &= combined_data.index >= pd.to_datetime(start_date)
                if end_date:
                    date_mask &= combined_data.index <= pd.to_datetime(end_date)
                combined_data = combined_data[date_mask]

            # Clean up metadata columns
            metadata_cols = ['symbol', 'data_type', 'year', 'ingestion_date']
            for col in metadata_cols:
                if col in combined_data.columns:
                    combined_data = combined_data.drop(columns=[col])

            logger.info(f"Loaded {len(combined_data)} records for {symbol}")
            return combined_data

        except Exception as e:
            logger.error(f"Failed to load data for {symbol}: {e}")
            return pd.DataFrame()

    def get_available_symbols(self, data_type: str = "daily") -> List[str]:
        """Get list of symbols available in storage"""
        try:
            symbol_path = self.processed_path / data_type
            if not symbol_path.exists():
                return []

            symbols = []
            for item in symbol_path.iterdir():
                if item.name.startswith('symbol=') and item.is_dir():
                    symbol = item.name.replace('symbol=', '').upper() + '.HK'
                    symbols.append(symbol)

            return sorted(symbols)

        except Exception as e:
            logger.error(f"Failed to get available symbols: {e}")
            return []

    def get_storage_statistics(self) -> Dict[str, any]:
        """Get comprehensive storage statistics"""
        try:
            stats = {
                'total_symbols': 0,
                'total_partitions': 0,
                'storage_size_mb': 0,
                'date_coverage': {},
                'data_types': {}
            }

            # Scan processed data directory
            for data_type_dir in self.processed_path.iterdir():
                if data_type_dir.is_dir():
                    data_type = data_type_dir.name
                    stats['data_types'][data_type] = {
                        'symbols': [],
                        'total_size_mb': 0
                    }

                    for symbol_dir in data_type_dir.iterdir():
                        if symbol_dir.name.startswith('symbol=') and symbol_dir.is_dir():
                            symbol = symbol_dir.name.replace('symbol=', '').upper() + '.HK'
                            stats['data_types'][data_type]['symbols'].append(symbol)
                            stats['total_symbols'] = max(stats['total_symbols'],
                                                        len(stats['data_types'][data_type]['symbols']))

                            for year_dir in symbol_dir.iterdir():
                                if year_dir.name.startswith('year=') and year_dir.is_dir():
                                    year = int(year_dir.name.replace('year=', ''))
                                    stats['total_partitions'] += 1

                                    # Calculate size of this partition
                                    file_path = year_dir / "data.parquet"
                                    if file_path.exists():
                                        size_mb = file_path.stat().st_size / (1024 * 1024)
                                        stats['storage_size_mb'] += size_mb
                                        stats['data_types'][data_type]['total_size_mb'] += size_mb

                                        # Track date coverage
                                        if data_type not in stats['date_coverage']:
                                            stats['date_coverage'][data_type] = {'start_year': year, 'end_year': year}
                                        else:
                                            stats['date_coverage'][data_type]['start_year'] = min(
                                                stats['date_coverage'][data_type]['start_year'], year)
                                            stats['date_coverage'][data_type]['end_year'] = max(
                                                stats['date_coverage'][data_type]['end_year'], year)

            return stats

        except Exception as e:
            logger.error(f"Failed to get storage statistics: {e}")
            return {}

    def _validate_input_data(self, data: pd.DataFrame):
        """Validate input data format and quality"""
        if len(data) == 0:
            raise ValueError("Empty DataFrame provided")

        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            # Try alternative column names
            col_mapping = {
                'Open': 'open', 'High': 'high', 'Low': 'low',
                'Close': 'close', 'Volume': 'volume'
            }

            for alt_col, req_col in col_mapping.items():
                if alt_col in data.columns and req_col in missing_columns:
                    data = data.rename(columns={alt_col: req_col})
                    missing_columns.remove(req_col)

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Check data types
        for col in ['open', 'high', 'low', 'close']:
            if not pd.api.types.is_numeric_dtype(data[col]):
                try:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
                except:
                    raise ValueError(f"Cannot convert {col} to numeric")

        if not pd.api.types.is_numeric_dtype(data['volume']):
            try:
                data['volume'] = pd.to_numeric(data['volume'], errors='coerce').fillna(0)
            except:
                raise ValueError("Cannot convert volume to numeric")

        # Check for invalid prices
        if (data[['open', 'high', 'low', 'close']] <= 0).any().any():
            raise ValueError("Price data contains non-positive values")

    def _optimize_dtypes(self, data: pd.DataFrame) -> pd.DataFrame:
        """Optimize data types for efficient storage"""
        optimized = data.copy()

        # Convert float columns to float32 for space efficiency
        float_cols = ['open', 'high', 'low', 'close']
        for col in float_cols:
            if col in optimized.columns:
                optimized[col] = optimized[col].astype('float32')

        # Convert volume to int32
        if 'volume' in optimized.columns:
            optimized['volume'] = optimized['volume'].astype('int32')

        # Convert categorical columns to category type
        categorical_cols = ['symbol', 'data_type', 'tenor']
        for col in categorical_cols:
            if col in optimized.columns:
                optimized[col] = optimized[col].astype('category')

        return optimized

    def _store_metadata(self, symbol: str, stats: Dict[str, any], data_type: str):
        """Store metadata for the symbol"""
        try:
            metadata_file = self.metadata_path / f"{symbol}_{data_type}_metadata.json"

            # Load existing metadata if available
            existing_metadata = {}
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r') as f:
                    existing_metadata = json.load(f)

            # Update metadata
            existing_metadata.update({
                'symbol': symbol,
                'data_type': data_type,
                'last_updated': datetime.now().isoformat(),
                'storage_stats': stats
            })

            # Save metadata
            import json
            with open(metadata_file, 'w') as f:
                json.dump(existing_metadata, f, indent=2, default=str)

        except Exception as e:
            logger.warning(f"Failed to store metadata for {symbol}: {e}")

    def cleanup_cache(self):
        """Clean up cache directory"""
        try:
            import shutil
            if self.cache_path.exists():
                shutil.rmtree(self.cache_path)
                self.cache_path.mkdir(exist_ok=True)
                logger.info("Cache cleaned successfully")
        except Exception as e:
            logger.error(f"Failed to clean cache: {e}")