"""
Data Sharding Engine for VectorBT Multiprocessing
==============================================

高性能數據分片引擎，支持：
- 多種分片策略（時間、股票、大小、均勻、自適應）
- 內存優化的分片管理
- 分片緩存和性能統計
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import hashlib
import pickle
import psutil
import os
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ShardingStrategy(str, Enum):
    """分片策略"""
    TIME_BASED = "time_based"
    SYMBOL_BASED = "symbol_based"
    SIZE_BASED = "size_based"
    EVEN_DISTRIBUTION = "even_distribution"
    ADAPTIVE = "adaptive"
    HYBRID = "hybrid"


class CacheLevel(str, Enum):
    """緩存級別"""
    MEMORY = "memory"
    DISK = "disk"
    REDIS = "redis"
    NONE = "none"


@dataclass
class DataShard:
    """數據分片"""
    shard_id: str
    strategy: ShardingStrategy
    data: pd.DataFrame
    metadata: Dict[str, Any] = field(default_factory=dict)
    size_bytes: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0

    def __post_init__(self):
        """計算數據大小"""
        if hasattr(self.data, 'memory_usage'):
            self.size_bytes = self.data.memory_usage(deep=True)
        else:
            # 估算DataFrame大小
            self.size_bytes = self.data.shape[0] * self.data.shape[1] * 8  # 假設每個元素8字節


@dataclass
class ShardingConfig:
    """分片配置"""
    strategy: ShardingStrategy = ShardingStrategy.EVEN_DISTRIBUTION
    target_shard_size: int = 10000  # 目標每個分片的行數
    max_shard_size: int = 50000  # 最大分片大小
    min_shard_size: int = 1000    # 最小分片大小
    cache_level: CacheLevel = CacheLevel.MEMORY
    cache_dir: str = "./shard_cache"
    enable_compression: bool = True
    max_memory_usage: float = 0.8  # 最大內存使用率

    # 性能調優
    compression_level: int = 5  # 1-9 (pickle壓縮級別)
    chunk_overlap: int = 100     # 分片間重疊行數
    prefetch_enabled: bool = True
    parallel_processing: bool = True


class ShardingCache:
    """分片緩存管理器"""

    def __init__(self, config: ShardingConfig):
        self.config = config
        self.memory_cache: Dict[str, DataShard] = {}
        self.disk_cache_path = Path(config.cache_dir)
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }

        # 創建緩存目錄
        self.disk_cache_path.mkdir(parents=True, exist_ok=True)

        # 記置緩存大小限制
        self.max_memory_shards = max(1, int(psutil.virtual_memory().available /
                                       (config.max_shard_size * 8 * config.max_memory_usage)))

        logger.info(f"ShardingCache initialized with max_memory_shards={self.max_memory_shards}")

    async def get_shard(self, shard_id: str) -> Optional[DataShard]:
        """獲取分片"""
        self.cache_stats['total_requests'] += 1

        # 先檢查內存緩存
        if shard_id in self.memory_cache:
            self.cache_stats['hits'] += 1
            shard = self.memory_cache[shard_id]
            shard.last_accessed = datetime.now()
            shard.access_count += 1
            return shard

        # 檢查磁盤緩存
        disk_file = self.disk_cache_path / f"{shard_id}.pkl"
        if disk_file.exists():
            try:
                with open(disk_file, 'rb') as f:
                    if self.config.enable_compression:
                        shard = pickle.load(f)
                    else:
                        shard = pickle.load(f)

                # 加載到內存緩存
                await self._load_to_memory(shard)
                self.cache_stats['hits'] += 1
                return shard

            except Exception as e:
                logger.error(f"Failed to load shard {shard_id} from disk: {e}")

        self.cache_stats['misses'] += 1
        return None

    async def put_shard(self, shard: DataShard) -> bool:
        """存儲分片"""
        try:
            # 根據緩存級別存儲
            if self.config.cache_level in [CacheLevel.MEMORY, CacheLevel.REDIS]:
                await self._load_to_memory(shard)

            if self.config.cache_level in [CacheLevel.DISK, CacheLevel.REDIS]:
                await self._save_to_disk(shard)

            return True

        except Exception as e:
            logger.error(f"Failed to save shard {shard.shard_id}: {e}")
            return False

    async def _load_to_memory(self, shard: DataShard):
        """加載到內存緩存"""
        # 檢查內存限制
        while len(self.memory_cache) >= self.max_memory_shards:
            await self._evict_lru_shard()

        self.memory_cache[shard.shard_id] = shard
        shard.last_accessed = datetime.now()

    async def _save_to_disk(self, shard: DataShard):
        """保存到磁盤緩存"""
        disk_file = self.disk_cache_path / f"{shard.shard_id}.pkl"

        try:
            with open(disk_file, 'wb') as f:
                if self.config.enable_compression:
                    pickle.dump(shard, f, protocol=pickle.HIGHEST_PROTOCOL)
                else:
                    pickle.dump(shard, f)
        except Exception as e:
            logger.error(f"Failed to save shard {shard.shard_id} to disk: {e}")

    async def _evict_lru_shard(self):
        """驅逐最少使用的分片"""
        if not self.memory_cache:
            return

        # 找到最少使用的分片
        lru_shard_id = min(
            self.memory_cache.keys(),
            key=lambda k: (self.memory_cache[k].last_accessed,
                          self.memory_cache[k].access_count)
        )

        evicted_shard = self.memory_cache.pop(lru_shard_id)
        self.cache_stats['evictions'] += 1

        # 如果是DISK緩存級別，保留在磁盤上
        if self.config.cache_level != CacheLevel.MEMORY:
            await self._save_to_disk(evicted_shard)

        logger.debug(f"Evicted shard {lru_shard_id} from memory cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        total_requests = self.cache_stats['total_requests']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100
                    if total_requests > 0 else 0)

        return {
            **self.cache_stats,
            'hit_rate_percent': hit_rate,
            'memory_shards': len(self.memory_cache),
            'disk_shards': len(list(self.disk_cache_path.glob("*.pkl"))),
            'cache_efficiency': hit_rate / 100 if hit_rate > 0 else 0
        }

    async def clear_cache(self):
        """清空緩存"""
        self.memory_cache.clear()

        # 清空磁盤緩存
        for cache_file in self.disk_cache_path.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"Failed to delete cache file {cache_file}: {e}")

        logger.info("Sharding cache cleared")


class DataShardingEngine:
    """數據分片引擎主類"""

    def __init__(self, config: Optional[ShardingConfig] = None):
        self.config = config or ShardingConfig()
        self.cache = ShardingCache(self.config)

        # 分片索引
        self.shard_index: Dict[str, DataShard] = {}

        # 分片統計
        self.shard_stats = {
            'total_shards': 0,
            'total_data_size': 0,
            'average_shard_size': 0,
            'sharding_efficiency': 0,
            'last_shard_time': None
        }

        logger.info(f"DataShardingEngine initialized with strategy: {self.config.strategy}")

    async def shard_data(
        self,
        data: pd.DataFrame,
        symbols: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DataShard]:
        """
        對數據進行分片

        Args:
            data: 輸入數據
            symbols: 股票列表（可選）
            metadata: 元數據（可選）

        Returns:
            分片列表
        """
        start_time = datetime.now()

        try:
            # 根據策略進行分片
            if self.config.strategy == ShardingStrategy.TIME_BASED:
                shards = await self._shard_by_time(data, metadata)
            elif self.config.strategy == ShardingStrategy.SYMBOL_BASED:
                shards = await self._shard_by_symbol(data, symbols, metadata)
            elif self.config.strategy == ShardingStrategy.SIZE_BASED:
                shards = await self._shard_by_size(data, metadata)
            elif self.config.strategy == ShardingStrategy.EVEN_DISTRIBUTION:
                shards = await self._shard_evenly(data, metadata)
            elif self.config.strategy == ShardingStrategy.ADAPTIVE:
                shards = await self._shard_adaptive(data, metadata)
            elif self.config.strategy == ShardingStrategy.HYBRID:
                shards = await self._shard_hybrid(data, symbols, metadata)
            else:
                raise ValueError(f"Unsupported sharding strategy: {self.config.strategy}")

            # 添加重疊
            if self.config.chunk_overlap > 0:
                shards = await self._add_chunk_overlap(shards)

            # 更新統計
            await self._update_shard_stats(shards, start_time)

            # 緩存分片
            for shard in shards:
                await self.cache.put_shard(shard)
                self.shard_index[shard.shard_id] = shard

            logger.info(f"Sharded data into {len(shards)} shards "
                       f"({sum(s.size_bytes for s in shards) / 1024 / 1024:.1f} MB)")

            return shards

        except Exception as e:
            logger.error(f"Data sharding failed: {e}")
            raise

    async def get_shard(self, shard_id: str) -> Optional[DataShard]:
        """獲取特定分片"""
        return await self.cache.get_shard(shard_id)

    async def get_shards_for_symbol(
        self,
        symbol: str
    ) -> List[DataShard]:
        """獲取特定股票的所有分片"""
        symbol_shards = []

        for shard in self.shard_index.values():
            if (shard.metadata.get('symbol') == symbol or
                (shard.data is not None and
                 'symbol' in shard.data.columns and
                 symbol in shard.data['symbol'].unique())):
                symbol_shards.append(shard)

        return sorted(symbol_shards, key=lambda s: s.created_at)

    async def get_shards_for_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[DataShard]:
        """獲取日期範圍內的所有分片"""
        date_shards = []

        for shard in self.shard_index.values():
            if (shard.metadata.get('start_date') and
                shard.metadata.get('end_date')):
                shard_start = shard.metadata['start_date']
                shard_end = shard.metadata['end_date']

                if (isinstance(shard_start, str)):
                    shard_start = pd.to_datetime(shard_start)
                if (isinstance(shard_end, str)):
                    shard_end = pd.to_datetime(shard_end)

                if (shard_start >= start_date and shard_end <= end_date):
                    date_shards.append(shard)

        return sorted(date_shards, key=lambda s: s.created_at)

    async def combine_shards(self, shard_ids: List[str]) -> Optional[pd.DataFrame]:
        """合併多個分片"""
        shards = []

        # 獲取所有分片
        for shard_id in shard_ids:
            shard = await self.get_shard(shard_id)
            if shard:
                shards.append(shard)

        if not shards:
            return None

        # 按時間排序
        shards.sort(key=lambda s: s.metadata.get('start_date', s.created_at))

        # 合併數據
        combined_data = pd.concat([shard.data for shard in shards],
                               ignore_index=True)

        # 去重（如果有的重疊）
        if self.config.chunk_overlap > 0:
            combined_data = combined_data.drop_duplicates()

        return combined_data

    async def _shard_by_time(
        self,
        data: pd.DataFrame,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DataShard]:
        """按時間分片"""
        shards = []

        if 'date' not in data.index.names:
            # 如果沒有日期索引，使用索引
            data = data.copy()
            data['date'] = data.index

        # 按日期分組
        date_groups = data.groupby('date')

        for date_str, date_data in date_groups:
            # 檢查是否需要進一步分片
            if len(date_data) > self.config.max_shard_size:
                # 進一步按大小分片
                sub_shards = await self._shard_by_size(
                    date_data,
                    {**(metadata or {}), 'date': date_str, 'strategy': 'time_based'}
                )
                shards.extend(sub_shards)
            else:
                # 創建分片
                shard_id = f"time_{date_str}_{hashlib.md5(str(date_str)).hexdigest()[:8]}"

                shard = DataShard(
                    shard_id=shard_id,
                    strategy=ShardingStrategy.TIME_BASED,
                    data=date_data,
                    metadata={
                        **(metadata or {}),
                        'date': date_str,
                        'start_date': date_data.index.min(),
                        'end_date': date_data.index.max(),
                        'row_count': len(date_data)
                    }
                )
                shards.append(shard)

        return shards

    async def _shard_by_symbol(
        self,
        data: pd.DataFrame,
        symbols: Optional[List[str]],
        metadata: Optional[Dict[str, Any]]
    ) -> List[DataShard]:
        """按股票分片"""
        shards = []

        if 'symbol' not in data.columns:
            # 添加符號列
            data = data.copy()
            if symbols:
                # 根�索引推斷符號
                symbols_in_data = []
                for idx in data.index:
                    if hasattr(idx, '__str__'):
                        idx_str = str(idx)
                        for symbol in symbols:
                            if symbol in idx_str:
                                symbols_in_data.append(symbol)
                                break

                data['symbol'] = symbols_in_data
            else:
                # 無法確定符號
                data['symbol'] = 'UNKNOWN'

        # 按符號分組
        symbol_groups = data.groupby('symbol')

        for symbol, symbol_data in symbol_groups:
            # 檢查是否需要進一步分片
            if len(symbol_data) > self.config.max_shard_size:
                sub_shards = await self._shard_by_size(
                    symbol_data,
                    {**(metadata or {}), 'symbol': symbol, 'strategy': 'symbol_based'}
                )
                shards.extend(sub_shards)
            else:
                # 創建分片
                shard_id = f"symbol_{symbol}_{hashlib.md5(str(len(symbol_data))).hexdigest()[:8]}"

                shard = DataShard(
                    shard_id=shard_id,
                    strategy=ShardingStrategy.SYMBOL_BASED,
                    data=symbol_data,
                    metadata={
                        **(metadata or {}),
                        'symbol': symbol,
                        'start_date': symbol_data.index.min(),
                        'end_date': symbol_data.index.max(),
                        'row_count': len(symbol_data)
                    }
                )
                shards.append(shard)

        return shards

    async def _shard_by_size(
        self,
        data: pd.DataFrame,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DataShard]:
        """按大小分片"""
        shards = []
        total_rows = len(data)

        # 計算分片大小
        shard_size = min(max(self.config.min_shard_size,
                          self.config.target_shard_size),
                          self.config.max_shard_size)

        # 分片數量
        num_shards = max(1, (total_rows + shard_size - 1) // shard_size)

        for i in range(num_shards):
            start_idx = i * shard_size
            end_idx = min((i + 1) * shard_size, total_rows)

            shard_data = data.iloc[start_idx:end_idx]

            shard_id = f"size_{i}_{hashlib.md5(f'{i}_{len(shard_data)}').encode()).hexdigest()[:8]}"

            shard = DataShard(
                shard_id=shard_id,
                strategy=ShardingStrategy.SIZE_BASED,
                data=shard_data,
                metadata={
                    **(metadata or {}),
                    'shard_index': i,
                    'total_shards': num_shards,
                    'start_index': start_idx,
                    'end_index': end_idx - 1,
                    'row_count': len(shard_data)
                }
            )
            shards.append(shard)

        return shards

    async def _shard_evenly(
        self,
        data: pd.DataFrame,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DataShard]:
        """均勻分片"""
        total_rows = len(data)
        target_shard_size = min(self.config.target_shard_size,
                                 self.config.max_shard_size)

        # 計算最優分片數
        num_shards = max(1, min(total_rows // target_shard_size,
                             total_rows // self.config.min_shard_size))

        if num_shards == 1:
            # 不需要分片
            shard_id = f"even_single_{hashlib.md5(str(total_rows)).hexdigest()[:8]}"
            shard = DataShard(
                shard_id=shard_id,
                strategy=ShardingStrategy.EVEN_DISTRIBUTION,
                data=data,
                metadata={
                    **(metadata or {}),
                    'total_shards': 1,
                    'row_count': total_rows
                }
            )
            return [shard]

        # 均勻分片
        shard_size = total_rows // num_shards
        remainder = total_rows % num_shards

        shards = []
        start_idx = 0

        for i in range(num_shards):
            # 計算當前分片大小
            current_size = shard_size + (1 if i < remainder else 0)
            end_idx = start_idx + current_size

            shard_data = data.iloc[start_idx:end_idx]

            shard_id = f"even_{i}_{hashlib.md5(f'{i}_{current_size}').encode()).hexdigest()[:8]}"

            shard = DataShard(
                shard_id=shard_id,
                strategy=ShardingStrategy.EVEN_DISTRIBUTION,
                data=shard_data,
                metadata={
                    **(metadata or {}),
                    'shard_index': i,
                    'total_shards': num_shards,
                    'start_index': start_idx,
                    'end_index': end_idx - 1,
                    'row_count': len(shard_data),
                    'target_size': target_shard_size
                }
            )
            shards.append(shard)
            start_idx = end_idx

        return shards

    async def _shard_adaptive(
        self,
        data: pd.DataFrame,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DataShard]:
        """自適應分片"""
        # 分析數據特徵
        data_features = self._analyze_data_features(data)

        # 根據特徵選擇最佳策略
        if data_features['has_time_series']:
            strategy = ShardingStrategy.TIME_BASED
        elif data_features['multiple_symbols']:
            strategy = ShardingStrategy.SYMBOL_BASED
        elif data_features['large_dataset']:
            strategy = ShardingStrategy.SIZE_BASED
        else:
            strategy = ShardingStrategy.EVEN_DISTRIBUTION

        logger.info(f"Adaptive sharding selected strategy: {strategy}")

        # 使用選定的策略
        if strategy == ShardingStrategy.TIME_BASED:
            return await self._shard_by_time(data, metadata)
        elif strategy == ShardingStrategy.SYMBOL_BASED:
            return await self._shard_by_symbol(data, None, metadata)
        elif strategy == Sharding.SIZE_BASED:
            return await self._shard_by_size(data, metadata)
        else:
            return await self._shard_evenly(data, metadata)

    async def _shard_hybrid(
        self,
        data: pd.DataFrame,
        symbols: Optional[List[str]],
        metadata: Optional[Dict[str, Any]]
    ) -> List[DataShard]:
        """混合分片策略"""
        shards = []

        # 首先按符號分片
        if symbols:
            symbol_shards = await self._shard_by_symbol(data, symbols, metadata)

            # 檢查每個符號分片是否過大
            for symbol_shard in symbol_shards:
                if len(symbol_shard.data) > self.config.max_shard_size:
                    # 對過大的分片進一步按大小分片
                    sub_shards = await self._shard_by_size(
                        symbol_shard.data,
                        {**symbol_shard.metadata, 'parent_shard': symbol_shard.shard_id}
                    )
                    shards.extend(sub_shards)
                else:
                    shards.append(symbol_shard)
        else:
            # 沒有符號信息，使用均勻分片
            shards.extend(await self._shard_evenly(data, metadata))

        return shards

    async def _add_chunk_overlap(self, shards: List[DataShard]) -> List[Shard]:
        """添加分片間重疊"""
        if self.config.chunk_overlap <= 0:
            return shards

        overlapped_shards = []

        for i, shard in enumerate(shards):
            data = shard.data

            # 添加重疊
            if i > 0:
                # 與前一個分片的尾部
                prev_shard = shards[i-1]
                overlap_data = prev_shard.data.tail(self.config.chunk_overlap)
                data = pd.concat([overlap_data, data], ignore_index=True)

            if i < len(shards) - 1:
                # 下一個分片的頭部
                next_shard = shards[i+1]
                overlap_data = next_shard.data.head(self.config.chunk_overlap)
                data = pd.concat([data, overlap_data], ignore_index=True)

            # 創建新分片
            overlapped_shard = DataShard(
                shard_id=f"{shard.shard_id}_overlap",
                strategy=shard.strategy,
                data=data,
                metadata={
                    **shard.metadata,
                    'has_overlap': True,
                    'overlap_size': self.config.chunk_overlap
                }
            )
            overlapped_shards.append(overlapped_shard)

        return overlapped_shards

    def _analyze_data_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析數據特徵"""
        features = {
            'total_rows': len(data),
            'total_columns': len(data.columns),
            'has_time_series': False,
            'multiple_symbols': False,
            'large_dataset': False,
            'memory_estimate': 0,
            'data_types': {}
        }

        # 檢查是否有時間序列
        if hasattr(data.index, 'names') and 'date' in data.index.names:
            features['has_time_series'] = True
        elif hasattr(data.index, 'dtype') and data.index.dtype in ['datetime64[ns]']:
            features['has_time_series'] = True

        # 檢查多符號
        if 'symbol' in data.columns:
            unique_symbols = data['symbol'].nunique()
            features['multiple_symbols'] = unique_symbols > 1
            features['symbol_count'] = unique_symbols

        # 檢查數據集大小
        features['large_dataset'] = features['total_rows'] > self.config.max_shard_size * 5

        # 估算內存使用
        features['memory_estimate'] = features['total_rows'] * features['total_columns'] * 8

        # 分析數據類型
        for col in data.columns:
            features['data_types'][col] = str(data[col].dtype)

        return features

    async def _update_shard_stats(
        self,
        shards: List[DataShard],
        start_time: datetime
    ):
        """更新分片統計"""
        self.shard_stats['total_shards'] = len(shards)
        self.shard_stats['total_data_size'] = sum(s.size_bytes for s in shards)

        if shards:
            self.shard_stats['average_shard_size'] = (
                self.shard_stats['total_data_size'] / len(shards)
            )

        self.shard_stats['sharding_efficiency'] = (
            self.shard_stats['average_shard_size'] / self.config.target_shard_size
        )

        self.shard_stats['last_shard_time'] = datetime.now() - start_time

        # 記算分片時間效率
        total_time = self.shard_stats['last_shard_time']
        if total_time.total_seconds() > 0:
            rows_per_second = sum(len(s.data) for s in shards) / total_time.total_seconds()
            self.shard_stats['rows_per_second'] = rows_per_second
            self.shard_stats['mb_per_second'] = (
                self.shard_stats['total_data_size'] / 1024 / 1024 / total_time.total_seconds()
            )

    def get_shard_stats(self) -> Dict[str, Any]:
        """獲取分片統計"""
        stats = self.shard_stats.copy()
        stats['cache_stats'] = self.cache.get_cache_stats()
        return stats

    async def preload_shards(self, shard_ids: List[str]):
        """預加載分片到內存"""
        logger.info(f"Preloading {len(shard_ids)} shards to memory")

        for shard_id in shard_ids:
            await self.cache.get_shard(shard_id)

        logger.info("Shard preloading completed")

    async def optimize_shard_distribution(self):
        """優化分片分佈"""
        # 獲取緩存統計
        cache_stats = self.cache.get_cache_stats()

        # 分析熱門分片
        hot_shards = []
        for shard_id, shard in self.cache.memory_cache.items():
            if shard.access_count > 10:  # 高頻訪問的分片
                hot_shards.append(shard_id)

        # 記算當前資源使用
        memory_usage = psutil.virtual_memory().percent
        if memory_usage > 0.8:
            # 高內存使用，減少緩存
            await self.cache.clear_cache()
            logger.warning("High memory usage detected, clearing cache")

        logger.info(f"Shard distribution optimization completed. "
                   f"Cache hit rate: {cache_stats['hit_rate_percent']:.1f}%")

    async def cleanup_expired_shards(self, max_age_hours: float = 24.0):
        """清理過期分片"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        expired_shards = []

        for shard_id, shard in list(self.shard_index.items()):
            if shard.created_at < cutoff_time:
                expired_shards.append(shard_id)

        # 清理過期分片
        for shard_id in expired_shards:
            # 從索引中移除
            del self.shard_index[shard_id]

            # 從緩存中移除
            if shard_id in self.cache.memory_cache:
                del self.cache.memory_cache[shard_id]

            # 從磁盤緩存中刪除
            disk_file = self.cache.disk_cache_path / f"{shard_id}.pkl"
            if disk_file.exists():
                try:
                    disk_file.unlink()
                except Exception as e:
                    logger.error(f"Failed to delete expired shard file {disk_file}: {e}")

        if expired_shards:
            logger.info(f"Cleaned up {len(expired_shards)} expired shards")