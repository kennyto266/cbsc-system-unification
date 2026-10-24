"""
市場數據遷移腳本

將現有的市場數據、技術指標和政府數據遷移到統一模型。
"""

import os
import json
import csv
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
import pandas as pd

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import db_manager
from ...models import MarketData, TechnicalIndicator, SentimentData
from ..migration_script import MigrationScript

logger = logging.getLogger(__name__)

class MigrateMarketDataMigration(MigrationScript):
    """市場數據遷移腳本"""

    def __init__(self):
        super().__init__(
            version="003",
            name="migrate_market_data",
            description="遷移CBSC市場數據、技術指標和政府數據到統一模型",
            author="Data Migration System"
        )
        self.data_sources = {
            "market_data": self._find_market_data_files(),
            "technical_indicators": self._find_indicator_files(),
            "government_data": self._find_government_data_files(),
            "real_data": self._find_real_data_files()
        }

    def _find_market_data_files(self) -> List[str]:
        """查找市場數據文件"""
        patterns = [
            "data/**/*.csv",
            "acquired_data/**/*.csv",
            "acheng_sharpe_results.csv"
        ]
        files = []

        for pattern in patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file() and file_path.stat().st_size > 1000:
                    files.append(str(file_path))

        return files

    def _find_indicator_files(self) -> List[str]:
        """查找技術指標文件"""
        patterns = [
            "data/final_real_indicators/**/*.csv",
            "data/real_data/**/*.csv"
        ]
        files = []

        for pattern in patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    files.append(str(file_path))

        return files

    def _find_government_data_files(self) -> List[str]:
        """查找政府數據文件"""
        patterns = [
            "data/government/**/*.json",
            "data/government/**/*.csv"
        ]
        files = []

        for pattern in patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    files.append(str(file_path))

        return files

    def _find_real_data_files(self) -> List[str]:
        """查找實時數據文件"""
        patterns = [
            "data/unified_real_data/**/*.json",
            "data/long_term_storage/**/*.csv"
        ]
        files = []

        for pattern in patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    files.append(str(file_path))

        return files

    def get_up_sql(self) -> str:
        """獲取升級SQL語句"""
        return "-- This migration uses Python logic for data migration"

    def get_down_sql(self) -> str:
        """獲取回滾SQL語句"""
        return """
        DELETE FROM sentiment_data WHERE source LIKE 'migration_%';
        DELETE FROM technical_indicators WHERE source LIKE 'migration_%';
        DELETE FROM market_data WHERE source LIKE 'migration_%';
        """

    async def execute_migration(self, session: AsyncSession) -> Dict[str, Any]:
        """執行數據遷移"""
        result = {
            "success": True,
            "market_data_migrated": 0,
            "technical_indicators_migrated": 0,
            "sentiment_data_migrated": 0,
            "errors": [],
            "migration_details": {
                "files_processed": 0,
                "records_processed": 0,
                "errors_by_file": {}
            }
        }

        try:
            # 1. 遷移市場數據
            market_migration = await self._migrate_market_data(session)
            result.update(market_migration)

            # 2. 遷移技術指標
            indicator_migration = await self._migrate_technical_indicators(session)
            result.update(indicator_migration)

            # 3. 遷移政府數據作為情緒數據
            sentiment_migration = await self._migrate_sentiment_data(session)
            result.update(sentiment_migration)

            await session.commit()
            logger.info(f"Market data migration completed: {result}")

        except Exception as e:
            await session.rollback()
            result["success"] = False
            result["errors"].append(f"Migration failed: {str(e)}")
            logger.error(f"Market data migration failed: {e}")

        return result

    async def _migrate_market_data(self, session: AsyncSession) -> Dict[str, Any]:
        """遷移市場數據"""
        result = {
            "market_data_migrated": 0,
            "errors": []
        }

        try:
            for file_path in self.data_sources["market_data"]:
                try:
                    file_result = await self._process_market_data_file(session, file_path)
                    result["market_data_migrated"] += file_result["records"]
                    logger.info(f"Migrated market data file: {file_path} ({file_result['records']} records)")

                except Exception as e:
                    error_msg = f"Failed to migrate {file_path}: {str(e)}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)

        except Exception as e:
            result["errors"].append(f"Market data migration failed: {str(e)}")
            logger.error(f"Market data migration failed: {e}")

        return result

    async def _process_market_data_file(self, session: AsyncSession, file_path: str) -> Dict[str, Any]:
        """處理單個市場數據文件"""
        result = {"records": 0}

        if file_path.endswith('.csv'):
            result["records"] = await self._process_csv_market_data(session, file_path)
        elif file_path.endswith('.json'):
            result["records"] = await self._process_json_market_data(session, file_path)

        return result

    async def _process_csv_market_data(self, session: AsyncSession, file_path: str) -> int:
        """處理CSV格式的市場數據"""
        records_processed = 0
        batch_size = 1000
        batch_data = []

        try:
            df = pd.read_csv(file_path)

            # 標準化列名
            column_mapping = self._get_market_data_column_mapping(df.columns)
            df = df.rename(columns=column_mapping)

            # 提取時間戳列
            timestamp_col = None
            for col in ['timestamp', 'date', 'datetime', 'time']:
                if col in df.columns:
                    timestamp_col = col
                    break

            if not timestamp_col:
                logger.warning(f"No timestamp column found in {file_path}")
                return 0

            # 處理數據
            for index, row in df.iterrows():
                try:
                    # 解析時間戳
                    timestamp = self._parse_timestamp(row[timestamp_col])
                    if not timestamp:
                        continue

                    # 解析價格數據
                    price_data = {
                        'symbol': row.get('symbol', self._extract_symbol_from_filename(file_path)),
                        'timestamp': timestamp,
                        'timeframe': row.get('timeframe', '1d'),
                        'open_price': self._parse_float(row.get('open_price', row.get('open'))),
                        'high_price': self._parse_float(row.get('high_price', row.get('high'))),
                        'low_price': self._parse_float(row.get('low_price', row.get('low'))),
                        'close_price': self._parse_float(row.get('close_price', row.get('close'))),
                        'volume': self._parse_int(row.get('volume')),
                        'turnover': self._parse_float(row.get('turnover')),
                        'source': f'migration_{Path(file_path).name}'
                    }

                    # 添加到批次
                    batch_data.append(price_data)
                    records_processed += 1

                    # 批次插入
                    if len(batch_data) >= batch_size:
                        await self._insert_market_data_batch(session, batch_data)
                        batch_data = []

                except Exception as e:
                    logger.debug(f"Skipping row {index} in {file_path}: {e}")
                    continue

            # 插入剩餘數據
            if batch_data:
                await self._insert_market_data_batch(session, batch_data)

        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {e}")
            raise

        return records_processed

    async def _process_json_market_data(self, session: AsyncSession, file_path: str) -> int:
        """處理JSON格式的市場數據"""
        records_processed = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 處理不同格式的JSON數據
            if isinstance(data, dict):
                if 'data' in data:
                    # 結構化數據
                    records_processed = await self._process_structured_market_data(session, data, file_path)
                elif 'equity_curve' in data:
                    # 回測結果中的權益曲線數據
                    records_processed = await self._process_equity_curve_data(session, data, file_path)

        except Exception as e:
            logger.error(f"Error processing JSON {file_path}: {e}")
            raise

        return records_processed

    async def _process_structured_market_data(self, session: AsyncSession, data: Dict[str, Any], file_path: str) -> int:
        """處理結構化的市場數據"""
        records_processed = 0
        market_data_list = data.get('data', [])

        batch_size = 1000
        batch_data = []

        for item in market_data_list:
            try:
                timestamp = self._parse_timestamp(item.get('timestamp', item.get('date')))
                if not timestamp:
                    continue

                market_data = {
                    'symbol': item.get('symbol', self._extract_symbol_from_filename(file_path)),
                    'timestamp': timestamp,
                    'timeframe': item.get('timeframe', '1d'),
                    'open_price': self._parse_float(item.get('open_price', item.get('open'))),
                    'high_price': self._parse_float(item.get('high_price', item.get('high'))),
                    'low_price': self._parse_float(item.get('low_price', item.get('low'))),
                    'close_price': self._parse_float(item.get('close_price', item.get('close'))),
                    'volume': self._parse_int(item.get('volume')),
                    'source': f'migration_{Path(file_path).name}'
                }

                batch_data.append(market_data)
                records_processed += 1

                if len(batch_data) >= batch_size:
                    await self._insert_market_data_batch(session, batch_data)
                    batch_data = []

            except Exception as e:
                logger.debug(f"Skipping item in {file_path}: {e}")
                continue

        if batch_data:
            await self._insert_market_data_batch(session, batch_data)

        return records_processed

    async def _process_equity_curve_data(self, session: AsyncSession, data: Dict[str, Any], file_path: str) -> int:
        """處理權益曲線數據"""
        records_processed = 0
        equity_curve = data.get('equity_curve', [])

        if not equity_curve or not isinstance(equity_curve, list):
            return 0

        # 模擬市場數據（基於權益曲線）
        for i, equity_value in enumerate(equity_curve):
            if i == 0:
                continue  # 跳過第一個NaN值

            try:
                market_data = {
                    'symbol': data.get('symbol', self._extract_symbol_from_filename(file_path)),
                    'timestamp': datetime.now() - pd.Timedelta(days=len(equity_curve)-i),
                    'timeframe': '1d',
                    'close_price': float(equity_value),
                    'volume': 1000000,  # 默認成交量
                    'source': f'migration_equity_{Path(file_path).name}'
                }

                market_data_obj = MarketData(**market_data)
                session.add(market_data_obj)
                records_processed += 1

                # 每1000條記錄提交一次
                if records_processed % 1000 == 0:
                    await session.flush()

            except Exception as e:
                logger.debug(f"Skipping equity curve point {i}: {e}")
                continue

        return records_processed

    async def _insert_market_data_batch(self, session: AsyncSession, batch_data: List[Dict[str, Any]]):
        """批量插入市場數據"""
        for data in batch_data:
            try:
                market_data_obj = MarketData(**data)
                session.add(market_data_obj)
            except Exception as e:
                logger.debug(f"Failed to insert market data record: {e}")
                continue

        await session.flush()

    async def _migrate_technical_indicators(self, session: AsyncSession) -> Dict[str, Any]:
        """遷移技術指標數據"""
        result = {
            "technical_indicators_migrated": 0,
            "errors": []
        }

        try:
            for file_path in self.data_sources["technical_indicators"]:
                try:
                    file_result = await self._process_indicator_file(session, file_path)
                    result["technical_indicators_migrated"] += file_result["records"]
                    logger.info(f"Migrated indicator file: {file_path} ({file_result['records']} records)")

                except Exception as e:
                    error_msg = f"Failed to migrate indicators from {file_path}: {str(e)}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)

        except Exception as e:
            result["errors"].append(f"Technical indicators migration failed: {str(e)}")
            logger.error(f"Technical indicators migration failed: {e}")

        return result

    async def _process_indicator_file(self, session: AsyncSession, file_path: str) -> Dict[str, Any]:
        """處理技術指標文件"""
        result = {"records": 0}

        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)

                for index, row in df.iterrows():
                    try:
                        timestamp = self._parse_timestamp(row.get('timestamp', row.get('date')))
                        if not timestamp:
                            continue

                        # 創建技術指標記錄
                        indicator_data = {
                            'symbol': row.get('symbol', self._extract_symbol_from_filename(file_path)),
                            'timestamp': timestamp,
                            'timeframe': row.get('timeframe', '1d'),
                            'indicator_type': row.get('indicator_type', 'custom'),
                            'indicator_name': row.get('indicator_name', 'migrated'),
                            'value': self._parse_float(row.get('value')),
                            'parameters': {'source': 'migration'},
                            'source': f'migration_{Path(file_path).name}'
                        }

                        indicator_obj = TechnicalIndicator(**indicator_data)
                        session.add(indicator_obj)
                        result["records"] += 1

                        if result["records"] % 1000 == 0:
                            await session.flush()

                    except Exception as e:
                        logger.debug(f"Skipping indicator row {index}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error processing indicator file {file_path}: {e}")

        return result

    async def _migrate_sentiment_data(self, session: AsyncSession) -> Dict[str, Any]:
        """遷移情緒數據"""
        result = {
            "sentiment_data_migrated": 0,
            "errors": []
        }

        try:
            for file_path in self.data_sources["government_data"]:
                try:
                    file_result = await self._process_sentiment_file(session, file_path)
                    result["sentiment_data_migrated"] += file_result["records"]
                    logger.info(f"Migrated sentiment file: {file_path} ({file_result['records']} records)")

                except Exception as e:
                    error_msg = f"Failed to migrate sentiment from {file_path}: {str(e)}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)

        except Exception as e:
            result["errors"].append(f"Sentiment data migration failed: {str(e)}")
            logger.error(f"Sentiment data migration failed: {e}")

        return result

    async def _process_sentiment_file(self, session: AsyncSession, file_path: str) -> Dict[str, Any]:
        """處理情緒數據文件"""
        result = {"records": 0}

        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    # 創建情緒數據記錄
                    sentiment_data = {
                        'market': 'HK',
                        'timestamp': datetime.now(),
                        'source': f'migration_gov_{Path(file_path).name}',
                        'sentiment_score': 0.0,
                        'sentiment_label': 'neutral',
                        'confidence': 0.5,
                        'volume_mentions': 1,
                        'impact_level': 'medium',
                        'metadata': {
                            'source_file': file_path,
                            'migration_date': datetime.now().isoformat(),
                            'data_type': 'government'
                        }
                    }

                    sentiment_obj = SentimentData(**sentiment_data)
                    session.add(sentiment_obj)
                    result["records"] = 1

        except Exception as e:
            logger.error(f"Error processing sentiment file {file_path}: {e}")

        return result

    def _get_market_data_column_mapping(self, columns: List[str]) -> Dict[str, str]:
        """獲取列名映射"""
        mapping = {}
        column_lower = [col.lower() for col in columns]

        for i, col_lower in enumerate(column_lower):
            original_col = columns[i]

            if 'timestamp' in col_lower or 'date' in col_lower:
                mapping[original_col] = 'timestamp'
            elif 'open' in col_lower:
                mapping[original_col] = 'open_price'
            elif 'high' in col_lower:
                mapping[original_col] = 'high_price'
            elif 'low' in col_lower:
                mapping[original_col] = 'low_price'
            elif 'close' in col_lower:
                mapping[original_col] = 'close_price'
            elif 'vol' in col_lower:
                mapping[original_col] = 'volume'
            elif 'symbol' in col_lower:
                mapping[original_col] = 'symbol'
            elif 'timeframe' in col_lower or 'period' in col_lower:
                mapping[original_col] = 'timeframe'

        return mapping

    def _parse_timestamp(self, timestamp_value) -> Optional[datetime]:
        """解析時間戳"""
        if timestamp_value is None or pd.isna(timestamp_value):
            return None

        try:
            if isinstance(timestamp_value, str):
                # 嘗試多種時間格式
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d',
                    '%Y/%m/%d',
                    '%d/%m/%Y',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S.%f'
                ]

                for fmt in formats:
                    try:
                        return datetime.strptime(timestamp_value, fmt)
                    except ValueError:
                        continue

                # 嘗試pandas解析
                return pd.to_datetime(timestamp_value)

            elif isinstance(timestamp_value, (int, float)):
                # Unix時間戳
                return datetime.fromtimestamp(timestamp_value)

            elif isinstance(timestamp_value, datetime):
                return timestamp_value

        except Exception as e:
            logger.debug(f"Failed to parse timestamp {timestamp_value}: {e}")

        return None

    def _parse_float(self, value) -> Optional[float]:
        """解析浮點數"""
        if value is None or pd.isna(value):
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value) -> Optional[int]:
        """解析整數"""
        if value is None or pd.isna(value):
            return None

        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _extract_symbol_from_filename(self, file_path: str) -> str:
        """從文件名提取股票代碼"""
        filename = Path(file_path).stem.upper()

        # 常見的股票代碼模式
        if '0700' in filename or 'HK700' in filename:
            return '0700.HK'
        elif 'HK' in filename and '.' in filename:
            # 提取文件名中的股票代碼
            import re
            match = re.search(r'(\d{4})\.HK', filename)
            if match:
                return f"{match.group(1)}.HK"

        # 默認返回文件名
        return filename[:10]  # 限制長度

    async def validate_migration(self, session: AsyncSession) -> Dict[str, Any]:
        """驗證遷移結果"""
        result = {
            "success": True,
            "market_data_count": 0,
            "technical_indicators_count": 0,
            "sentiment_data_count": 0,
            "errors": []
        }

        try:
            # 統計遷移的數據
            market_result = await session.execute(
                select(MarketData).where(MarketData.source.like('migration_%'))
            )
            result["market_data_count"] = len(market_result.scalars().all())

            indicator_result = await session.execute(
                select(TechnicalIndicator).where(TechnicalIndicator.source.like('migration_%'))
            )
            result["technical_indicators_count"] = len(indicator_result.scalars().all())

            sentiment_result = await session.execute(
                select(SentimentData).where(SentimentData.source.like('migration_%'))
            )
            result["sentiment_data_count"] = len(sentiment_result.scalars().all())

            # 驗證數據完整性
            if result["market_data_count"] == 0:
                result["success"] = False
                result["errors"].append("No market data was migrated")

            logger.info(f"Market data migration validation: {result}")

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Validation failed: {str(e)}")
            logger.error(f"Market data migration validation failed: {e}")

        return result

# 註冊遷移腳本
migration = MigrateMarketDataMigration()