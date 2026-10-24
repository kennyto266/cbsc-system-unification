#!/usr/bin/env python3
"""
Government Data Storage System
Specialized storage for HKMA and other government economic data
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Union
import logging

try:
    import pyarrow
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False

try:
    import fastparquet
    FASTPARQUET_AVAILABLE = True
except ImportError:
    FASTPARQUET_AVAILABLE = False

logger = logging.getLogger(__name__)


class GovernmentDataStorage:
    """
    Specialized storage system for government economic data

    Features:
    - Parquet format optimized for economic indicators
    - Year-based partitioning
    - Multi-source data fusion support
    - Economic data validation
    - Metadata management
    """

    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = Path("C:/Users/Penguin8n/CODEX--/data/government_storage")
        else:
            base_path = Path(base_path)

        self.base_path = Path(base_path)
        self.hibor_path = self.base_path / "hibor"
        self.monetary_path = self.base_path / "monetary"
        self.exchange_path = self.base_path / "exchange"
        self.liquidity_path = self.base_path / "liquidity"
        self.metadata_path = self.base_path / "metadata"

        # Create directory structure
        self._create_directory_structure()

        # Validate Parquet availability
        if not PARQUET_AVAILABLE and not FASTPARQUET_AVAILABLE:
            raise ImportError("Neither PyArrow nor fastparquet available")

        logger.info(f"Government Data Storage initialized at: {self.base_path}")

    def _create_directory_structure(self):
        """Create directory structure for government data"""
        directories = [
            self.base_path,
            self.hibor_path,
            self.monetary_path,
            self.exchange_path,
            self.liquidity_path,
            self.metadata_path
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_partition_path(self, data_type: str, year: int) -> Path:
        """Get partition path for data type and year"""
        if data_type == 'hibor':
            return self.hibor_path / f"year={year}"
        elif data_type == 'monetary':
            return self.monetary_path / f"year={year}"
        elif data_type == 'exchange':
            return self.exchange_path / f"year={year}"
        elif data_type == 'liquidity':
            return self.liquidity_path / f"year={year}"
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

    def store_government_data(
        self,
        data_type: str,
        data: pd.DataFrame,
        overwrite: bool = False
    ) -> Dict[str, any]:
        """
        Store government economic data

        Args:
            data_type: Type of economic data (hibor, monetary, exchange, liquidity)
            data: DataFrame with economic data
            overwrite: Whether to overwrite existing data

        Returns:
            Storage metadata and statistics
        """
        try:
            # Validate input data
            self._validate_government_data(data, data_type)

            # Group data by year for partitioning
            data_by_year = {}
            for year, year_data in data.groupby(data.index.year):
                data_by_year[year] = year_data.copy()

            storage_stats = {
                'data_type': data_type,
                'total_records': len(data),
                'years_stored': list(data_by_year.keys()),
                'date_range': {
                    'start': str(data.index.min().date()),
                    'end': str(data.index.max().date())
                },
                'partitions_created': 0,
                'storage_size_mb': 0
            }

            # Store each year's data
            for year, year_data in data_by_year.items():
                partition_path = self.get_partition_path(data_type, year)
                partition_path.mkdir(parents=True, exist_ok=True)

                file_path = partition_path / f"{data_type}_data.parquet"

                # Check if file exists
                if file_path.exists() and not overwrite:
                    logger.info(f"Skipping existing {data_type} data for year {year}")
                    continue

                # Optimize data types for storage
                optimized_data = self._optimize_government_dtypes(year_data, data_type)

                # Add metadata
                optimized_data['data_type'] = data_type
                optimized_data['year'] = year
                optimized_data['ingestion_date'] = datetime.now()

                # Store as Parquet
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

                # Update statistics
                file_size = file_path.stat().st_size
                storage_stats['storage_size_mb'] += file_size / (1024 * 1024)
                storage_stats['partitions_created'] += 1

                logger.info(f"Stored {len(year_data)} {data_type} records for year {year}")

            # Store metadata
            self._store_government_metadata(data_type, storage_stats)

            logger.info(f"Successfully stored {storage_stats['total_records']} {data_type} records")
            return storage_stats

        except Exception as e:
            logger.error(f"Failed to store {data_type} data: {e}")
            raise

    def load_government_data(
        self,
        data_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Load government economic data

        Args:
            data_type: Type of economic data
            start_date: Start date for data loading
            end_date: End date for data loading

        Returns:
            DataFrame with government data
        """
        try:
            # Determine which years to load
            if start_date is None and end_date is None:
                # Load all available data
                data_path = self.get_partition_path(data_type, 2020).parent
                if not data_path.exists():
                    return pd.DataFrame()

                year_partitions = [int(p.name.replace('year=', ''))
                                 for p in data_path.iterdir()
                                 if p.name.startswith('year=')]
            else:
                # Load specific date range
                start_date = start_date or date(2000, 1, 1)
                end_date = end_date or date.today()

                years = range(start_date.year, end_date.year + 1)
                year_partitions = [year for year in years
                                 if self.get_partition_path(data_type, year).exists()]

            if not year_partitions:
                logger.warning(f"No {data_type} data found")
                return pd.DataFrame()

            # Load data from partitions
            data_frames = []
            for year in sorted(year_partitions):
                partition_path = self.get_partition_path(data_type, year)
                file_path = partition_path / f"{data_type}_data.parquet"

                if file_path.exists():
                    try:
                        year_data = pd.read_parquet(file_path)
                        data_frames.append(year_data)
                    except Exception as e:
                        logger.warning(f"Failed to load {data_type} data for year {year}: {e}")

            if not data_frames:
                logger.warning(f"No valid {data_type} data found")
                return pd.DataFrame()

            # Combine all year data
            combined_data = pd.concat(data_frames, ignore_index=False)
            combined_data = combined_data.sort_index()

            # Apply date filtering
            if start_date or end_date:
                date_mask = pd.Series(True, index=combined_data.index)
                if start_date:
                    date_mask &= combined_data.index >= pd.to_datetime(start_date)
                if end_date:
                    date_mask &= combined_data.index <= pd.to_datetime(end_date)
                combined_data = combined_data[date_mask]

            # Clean up metadata columns
            metadata_cols = ['data_type', 'year', 'ingestion_date']
            for col in metadata_cols:
                if col in combined_data.columns:
                    combined_data = combined_data.drop(columns=[col])

            logger.info(f"Loaded {len(combined_data)} {data_type} records")
            return combined_data

        except Exception as e:
            logger.error(f"Failed to load {data_type} data: {e}")
            return pd.DataFrame()

    def get_available_data_types(self) -> List[str]:
        """Get list of available data types"""
        data_types = []
        for data_type in ['hibor', 'monetary', 'exchange', 'liquidity']:
            path = self.get_partition_path(data_type, 2020).parent
            if path.exists() and any(path.iterdir()):
                data_types.append(data_type)
        return data_types

    def get_data_summary(self) -> Dict[str, any]:
        """Get comprehensive data summary"""
        summary = {
            'data_types': {},
            'total_size_mb': 0,
            'total_partitions': 0,
            'date_coverage': {}
        }

        for data_type in ['hibor', 'monetary', 'exchange', 'liquidity']:
            try:
                type_summary = self._get_data_type_summary(data_type)
                summary['data_types'][data_type] = type_summary
                summary['total_size_mb'] += type_summary.get('size_mb', 0)
                summary['total_partitions'] += type_summary.get('partitions', 0)

                # Update date coverage
                if type_summary.get('start_year') and type_summary.get('end_year'):
                    if data_type not in summary['date_coverage']:
                        summary['date_coverage'][data_type] = {
                            'start_year': type_summary['start_year'],
                            'end_year': type_summary['end_year']
                        }
                    else:
                        summary['date_coverage'][data_type]['start_year'] = min(
                            summary['date_coverage'][data_type]['start_year'],
                            type_summary['start_year']
                        )
                        summary['date_coverage'][data_type]['end_year'] = max(
                            summary['date_coverage'][data_type]['end_year'],
                            type_summary['end_year']
                        )
            except Exception as e:
                logger.warning(f"Failed to get summary for {data_type}: {e}")

        return summary

    def _get_data_type_summary(self, data_type: str) -> Dict[str, any]:
        """Get summary for specific data type"""
        summary = {
            'data_type': data_type,
            'partitions': 0,
            'size_mb': 0,
            'start_year': None,
            'end_year': None
        }

        try:
            data_path = self.get_partition_path(data_type, 2020).parent
            if not data_path.exists():
                return summary

            for item in data_path.iterdir():
                if item.name.startswith('year=') and item.is_dir():
                    year = int(item.name.replace('year=', ''))
                    summary['partitions'] += 1

                    file_path = item / f"{data_type}_data.parquet"
                    if file_path.exists():
                        size_mb = file_path.stat().st_size / (1024 * 1024)
                        summary['size_mb'] += size_mb

                        if summary['start_year'] is None:
                            summary['start_year'] = year
                        summary['end_year'] = max(summary.get('end_year', year), year)

        except Exception as e:
            logger.warning(f"Failed to get summary for {data_type}: {e}")

        return summary

    def _validate_government_data(self, data: pd.DataFrame, data_type: str):
        """Validate government economic data"""
        if len(data) == 0:
            raise ValueError("Empty DataFrame provided")

        # Check for datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")

        # Check data type specific columns
        if data_type == 'hibor':
            required_cols = ['tenor', 'rate']
            missing = [col for col in required_cols if col not in data.columns]
            if missing:
                raise ValueError(f"Missing required HIBOR columns: {missing}")

        elif data_type == 'monetary':
            if 'metric' not in data.columns or 'value' not in data.columns:
                raise ValueError("Monetary data must have 'metric' and 'value' columns")

        elif data_type == 'exchange':
            if 'currency_pair' not in data.columns or 'exchange_rate' not in data.columns:
                raise ValueError("Exchange data must have 'currency_pair' and 'exchange_rate' columns")

        elif data_type == 'liquidity':
            if 'metric' not in data.columns or 'value' not in data.columns:
                raise ValueError("Liquidity data must have 'metric' and 'value' columns")

    def _optimize_government_dtypes(self, data: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Optimize data types for government data"""
        optimized = data.copy()

        # Convert numeric columns to appropriate types
        if data_type == 'hibor':
            if 'rate' in optimized.columns:
                optimized['rate'] = optimized['rate'].astype('float32')
        elif data_type in ['monetary', 'liquidity']:
            if 'value' in optimized.columns:
                optimized['value'] = optimized['value'].astype('float64')
        elif data_type == 'exchange':
            if 'exchange_rate' in optimized.columns:
                optimized['exchange_rate'] = optimized['exchange_rate'].astype('float32')

        # Convert categorical columns
        if data_type == 'hibor':
            if 'tenor' in optimized.columns:
                optimized['tenor'] = optimized['tenor'].astype('category')
            if 'tenor_name' in optimized.columns:
                optimized['tenor_name'] = optimized['tenor_name'].astype('category')
        elif data_type in ['monetary', 'liquidity']:
            if 'metric' in optimized.columns:
                optimized['metric'] = optimized['metric'].astype('category')
        elif data_type == 'exchange':
            if 'currency_pair' in optimized.columns:
                optimized['currency_pair'] = optimized['currency_pair'].astype('category')

        return optimized

    def _store_government_metadata(self, data_type: str, stats: Dict[str, any]):
        """Store metadata for government data"""
        try:
            metadata_file = self.metadata_path / f"{data_type}_metadata.json"

            # Load existing metadata
            existing_metadata = {}
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r') as f:
                    existing_metadata = json.load(f)

            # Update metadata
            existing_metadata.update({
                'data_type': data_type,
                'last_updated': datetime.now().isoformat(),
                'storage_stats': stats
            })

            # Save metadata
            import json
            with open(metadata_file, 'w') as f:
                json.dump(existing_metadata, f, indent=2, default=str)

        except Exception as e:
            logger.warning(f"Failed to store metadata for {data_type}: {e}")