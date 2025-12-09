#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Repository - 策略數據訪問層
應用Repository Pattern，解耦策略數據存儲與業務邏輯

Architecture: Repository Pattern + Event Bus Integration
Performance: 索引優化 + 智能緩存
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from .base_repository import BaseRepository, JSONRepository, QuerySpec, CacheManager, IndexManager
from ..events.event_bus import get_event_bus, Event, EventTypes

logger = logging.getLogger__name__

@dataclass
class StrategyEntity:
"""策略實體"""
id: str
name: str
category: str
description: str = ""
parameters: Dict[str, Any] = fielddefault_factory=dict
performance_metrics: Dict[str, float] = fielddefault_factory=dict
created_at: datetime = fielddefault_factory=datetime.now
updated_at: datetime = fielddefault_factory=datetime.now
is_active: bool = True
tags: List[str] = fielddefault_factory=list
author: str = ""
version: str = "1.0.0"

def to_dictself -> Dict[str, Any]:
"""轉換為字典"""
return {
'id': self.id,
'name': self.name,
'category': self.category,
'description': self.description,
'parameters': self.parameters,
'performance_metrics': self.performance_metrics,
'created_at': self.created_at.isoformat(),
'updated_at': self.updated_at.isoformat(),
'is_active': self.is_active,
'tags': self.tags,
'author': self.author,
'version': self.version
}

class StrategyRepositoryJSONRepository[StrategyEntity]:
"""策略Repository"""

def __init__self, file_path: str = "data/strategies.json":
# 創建專用緩存管理器
cache_manager = CacheManagermax_size=500
super().__init__file_path, StrategyEntity, cache_manager

# 定義需要索引的字段
self._index_fields = ['category', 'author', 'is_active', 'name']

self._initialize_indexes()

self._event_bus = get_event_bus()
self._subscribe_to_events()

def _initialize_indexesself:
"""初始化索引"""
for field in self._index_fields:
self.index_manager.create_indexfield

def _subscribe_to_eventsself:
"""訂閱相關事件"""
self._event_bus.subscribe(
EventTypes.STRATEGY_DELETED,
self._handle_strategy_deleted,
async_handler=True
)

async def _handle_strategy_deletedself, event: Event:
"""處理策略刪除事件"""
strategy_id = event.data.get'strategy_id'
if strategy_id:
await self.deletestrategy_id

async def saveself, strategy: StrategyEntity -> StrategyEntity:
"""保存策略並發布事件"""
is_new = not hasattrstrategy, 'id' or not strategy.id

strategy.updated_at = datetime.now()

saved_strategy = await super().savestrategy

if is_new:    event = Event(
event_type=EventTypes.STRATEGY_CREATED,
source="strategy_repository",
data={
'strategy_id': saved_strategy.id,
'strategy_name': saved_strategy.name,
'category': saved_strategy.category
}
)
else:    event = Event(
event_type=EventTypes.STRATEGY_UPDATED,
source="strategy_repository",
data={
'strategy_id': saved_strategy.id,
'strategy_name': saved_strategy.name,
'updated_fields': strategy.parameters
}
)

await self._event_bus.publishevent

logger.info(f"Saved strategy: {saved_strategy.name} {saved_strategy.id}")
return saved_strategy

async def find_by_categoryself, category: str, active_only: bool = True -> List[StrategyEntity]:
"""根據分類查找策略"""
query_spec = QuerySpec(
filters={'category': category}
)

if active_only:    query_spec.filters['is_active'] = True

return await self.find_allquery_spec

async def find_by_authorself, author: str -> List[StrategyEntity]:
"""根據作者查找策略"""
query_spec = QuerySpec(
filters={'author': author}
)
return await self.find_allquery_spec

async def find_by_tagsself, tags: List[str] -> List[StrategyEntity]:
"""根據標籤查找策略"""

all_strategies = await self.find_all()

# 過濾包含指定標籤的策略
filtered_strategies = []
for strategy in all_strategies:
if anytag in strategy.tags for tag in tags:
filtered_strategies.appendstrategy

return filtered_strategies

async def search_strategies(self, keyword: str, category: str = None,
author: str = None) -> List[StrategyEntity]:
"""搜索策略"""

cache_key = f"search_{keyword}_{category}_{author}"
cached = self._get_cached_result'search', key=cache_key
if cached:
return cached

strategies = await self.find_all()

filtered_strategies = []
keyword_lower = keyword.lower()

for strategy in strategies:

text_match = (
keyword_lower in strategy.name.lower() or
keyword_lower in strategy.description.lower()
)

category_match = category is None or strategy.category == category

author_match = author is None or strategy.author == author

if text_match and category_match and author_match:
filtered_strategies.appendstrategy

self._cache_result'search', filtered_strategies, key=cache_key

return filtered_strategies

async def get_top_performing_strategies(self, metric: str = 'sharpe_ratio',
limit: int = 10) -> List[StrategyEntity]:
"""獲取表現最好的策略"""

cache_key = f"top_performing_{metric}_{limit}"
cached = self._get_cached_result'top_performing', key=cache_key
if cached:
return cached

# 獲取所有活動策略
query_spec = QuerySpec(
filters={'is_active': True}
)
strategies = await self.find_allquery_spec

# 過濾有性能數據的策略
strategies_with_metrics = [
s for s in strategies
if metric in s.performance_metrics
]

strategies_with_metrics.sort(
key=lambda s: s.performance_metrics.getmetric, 0,
reverse=True
)

top_strategies = strategies_with_metrics[:limit]

self._cache_result'top_performing', top_strategies, key=cache_key

return top_strategies

async def update_performance_metrics(self, strategy_id: str,
metrics: Dict[str, float]) -> bool:
"""更新策略性能指標"""
try:

strategy = await self.find_by_idstrategy_id
if not strategy:
return False

strategy.performance_metrics.updatemetrics
strategy.updated_at = datetime.now()

await self.savestrategy

# 發布性能更新事件
event = Event(
event_type=EventTypes.PERFORMANCE_ALERT,
source="strategy_repository",
data={
'strategy_id': strategy_id,
'strategy_name': strategy.name,
'metrics': metrics
}
)
await self._event_bus.publishevent

logger.infof"Updated performance metrics for strategy {strategy_id}"
return True

except Exception as e:
logger.errorf"Failed to update performance metrics for strategy {strategy_id}: {e}"
return False

async def get_category_statisticsself -> Dict[str, Dict[str, Any]]:
"""獲取分類統計信息"""

cached = self._get_cached_result'category_stats'
if cached:
return cached

strategies = await self.find_all()

category_stats = {}
for strategy in strategies:    category = strategy.category
if category not in category_stats:    category_stats[category] = {
'total': 0,
'active': 0,
'avg_sharpe': 0.0,
'avg_return': 0.0
}

stats = category_stats[category]
stats['total'] += 1

if strategy.is_active:    stats['active'] += 1

# 計算平均性能指標
if 'sharpe_ratio' in strategy.performance_metrics:    stats['avg_sharpe'] = (
(stats['avg_sharpe'] * stats['total'] - 1 +
strategy.performance_metrics['sharpe_ratio']) / stats['total']
)

if 'total_return' in strategy.performance_metrics:    stats['avg_return'] = (
(stats['avg_return'] * stats['total'] - 1 +
strategy.performance_metrics['total_return']) / stats['total']
)

self._cache_result'category_stats', category_stats

return category_stats

async def batch_update_status(self, strategy_ids: List[str],
is_active: bool) -> Dict[str, bool]:
"""批量更新策略狀態"""
results = {}

for strategy_id in strategy_ids:
try:    strategy = await self.find_by_id(strategy_id)
if strategy:    strategy.is_active = is_active
await self.savestrategy
results[strategy_id] = True
else:    results[strategy_id] = False
except Exception as e:
logger.errorf"Failed to update status for strategy {strategy_id}: {e}"
results[strategy_id] = False

return results

def _dict_to_entityself, data: Dict[str, Any] -> StrategyEntity:
"""字典轉策略實體"""
try:
# 處理日期時間字段
if 'created_at' in data and isinstancedata['created_at'], str:    data['created_at'] = datetime.fromisoformat(data['created_at'])
if 'updated_at' in data and isinstancedata['updated_at'], str:    data['updated_at'] = datetime.fromisoformat(data['updated_at'])

return StrategyEntity**data
except Exception as e:
logger.errorf"Failed to create StrategyEntity from dict: {e}"
raise

def create_strategy_repositoryfile_path: str = "data/strategies.json" -> StrategyRepository:
"""創建策略Repository實例"""
return StrategyRepositoryfile_path