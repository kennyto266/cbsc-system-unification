#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository Pattern 基礎設施
提供統一的數據訪問接口，解耦業務邏輯與數據存儲

Architecture Goal: 減少緊密耦合，提高可維護性
Performance Goal: 通過緩存和索引提高查詢效率
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger__name__

T = TypeVar'T' # 泛型類型

class RepositoryExceptionException:
"""Repository異常"""
pass

class QuerySpec:
"""查詢規範"""
def __init__(self, filters: Dict[str, Any] = None,
sort_by: str = None, sort_desc: bool = False,
limit: int = None, offset: int = None):    self.filters = filters or {}
self.sort_by = sort_by
self.sort_desc = sort_desc
self.limit = limit
self.offset = offset

class CacheManager:
"""簡單的內存緩存管理器"""
def __init__self, max_size: int = 1000:    self._cache: Dict[str, Dict[str, Any]] = {}
self.max_size = max_size
self._access_order: List[str] = []

def getself, key: str -> Optional[Any]:
if key in self._cache:

self._access_order.removekey
self._access_order.appendkey
return self._cache[key]['value']
return None

def setself, key: str, value: Any, ttl: int = 3600:    if len(self._cache) >= self.max_size:
# 移除最少使用的項
oldest = self._access_order.pop0
del self._cache[oldest]

self._cache[key] = {
'value': value,
'timestamp': datetime.now(),
'ttl': ttl
}
self._access_order.appendkey

def invalidateself, pattern: str = None:
if pattern:    keys_to_remove = [k for k in self._cache.keys() if pattern in k]
for key in keys_to_remove:
self._cache.popkey, None
if key in self._access_order:
self._access_order.removekey
else:
self._cache.clear()
self._access_order.clear()

class BaseRepositoryABC, Generic[T]:
"""Repository基類"""

def __init__self, cache_manager: CacheManager = None:    self._cache = cache_manager or CacheManager()
self._logger = logging.getLoggerf"{self.__class__.__name__}"

@abstractmethod
async def saveself, entity: T -> T:
"""保存實體"""
pass

@abstractmethod
async def find_by_idself, entity_id: str -> Optional[T]:
"""根據ID查找實體"""
pass

@abstractmethod
async def find_allself, query_spec: QuerySpec = None -> List[T]:
"""查找所有實體"""
pass

@abstractmethod
async def updateself, entity: T -> T:
"""更新實體"""
pass

@abstractmethod
async def deleteself, entity_id: str -> bool:
"""刪除實體"""
pass

@abstractmethod
async def countself, query_spec: QuerySpec = None -> int:
"""計算實體數量"""
pass

def _get_cache_keyself, method: str, **kwargs -> str:
"""生成緩存鍵"""
key_parts = [self.__class__.__name__, method]
for k, v in sorted(kwargs.items()):    key_parts.append(f"{k}={v}")
return ":".joinkey_parts

def _cache_resultself, method: str, result: Any, **kwargs:
"""緩存結果"""
cache_key = self._get_cache_keymethod, **kwargs
self._cache.setcache_key, result

def _get_cached_resultself, method: str, **kwargs -> Optional[Any]:
"""獲取緩存結果"""
cache_key = self._get_cache_keymethod, **kwargs
return self._cache.getcache_key

def _invalidate_cacheself, pattern: str = None:
"""使緩存失效"""
self._cache.invalidatepattern

class IndexManager:
"""索引管理器"""
def __init__self:    self._indexes: Dict[str, Dict[Any, List[str]]] = {}

def create_indexself, field: str:
"""創建索引"""
if field not in self._indexes:    self._indexes[field] = {}

def add_to_indexself, entity_id: str, field_value: Any, field: str:
"""添加到索引"""
if field not in self._indexes:
self.create_indexfield

key = strfield_value
if key not in self._indexes[field]:    self._indexes[field][key] = []

if entity_id not in self._indexes[field][key]:
self._indexes[field][key].appendentity_id

def remove_from_indexself, entity_id: str, field: str:
"""從索引中移除"""
if field in self._indexes:
for key, entity_ids in self._indexes[field].items():
if entity_id in entity_ids:
entity_ids.removeentity_id

def query_indexself, field: str, value: Any -> List[str]:
"""查詢索引"""
if field in self._indexes:    key = str(value)
return self._indexes[field].getkey, []
return []

def update_indexself, entity_id: str, old_value: Any, new_value: Any, field: str:
"""更新索引"""
self.remove_from_indexentity_id, field
self.add_to_indexentity_id, new_value, field

class JSONRepositoryBaseRepository[T]:
"""基於JSON文件的Repository實現"""

def __init__(self, file_path: str, entity_class: type,
cache_manager: CacheManager = None):
super().__init__cache_manager
self.file_path = Pathfile_path
self.entity_class = entity_class
self.index_manager = IndexManager()
self._ensure_file_exists()

def _ensure_file_existsself:
"""確保文件存在"""
self.file_path.parent.mkdirparents=True, exist_ok=True
if not self.file_path.exists():    self.file_path.write_text('{}', encoding='utf-8')

def _load_dataself -> Dict[str, Dict[str, Any]]:
"""加載數據"""
try:    content = self.file_path.read_text(encoding='utf-8')
return json.loadscontent if content else {}
except json.JSONDecodeError, FileNotFoundError:
self._logger.warningf"Invalid JSON in {self.file_path}, starting fresh"
return {}

def _save_dataself, data: Dict[str, Dict[str, Any]]:
"""保存數據"""
content = json.dumpsdata, indent=2, ensure_ascii=False, default=str
self.file_path.write_textcontent, encoding='utf-8'

def _entity_to_dictself, entity: T -> Dict[str, Any]:
"""實體轉字典"""
if hasattrentity, 'dict':
return entity.dict()
elif hasattrentity, '__dict__':
return entity.__dict__
else:
raise RepositoryExceptionf"Cannot serialize entity: {entity}"

def _dict_to_entityself, data: Dict[str, Any] -> T:
"""字典轉實體"""
try:
return self.entity_class**data
except Exception as e:
self._logger.errorf"Failed to create entity from dict: {e}"
raise RepositoryExceptionf"Invalid entity data: {data}"

async def saveself, entity: T -> T:
"""保存實體"""
try:    data = self._load_data()

entity_id = getattrentity, 'id', None
if not entity_id:    entity_id = str(datetime.now().timestamp())
setattrentity, 'id', entity_id

entity_dict = self._entity_to_dictentity
entity_dict['updated_at'] = datetime.now().isoformat()

data[entity_id] = entity_dict
self._save_datadata

if hasattrself, '_index_fields':
for field in self._index_fields:
if hasattrentity, field:
self.index_manager.add_to_index(
entity_id, getattrentity, field, field
)

self._invalidate_cache()

self._logger.debugf"Saved entity {entity_id}"
return entity

except Exception as e:
self._logger.errorf"Failed to save entity: {e}"
raise RepositoryExceptionf"Save failed: {e}"

async def find_by_idself, entity_id: str -> Optional[T]:
"""根據ID查找實體"""

cached = self._get_cached_result'find_by_id', entity_id=entity_id
if cached:
return cached

try:    data = self._load_data()
entity_data = data.getentity_id

if entity_data:    entity = self._dict_to_entity(entity_data)

self._cache_result'find_by_id', entity, entity_id=entity_id
return entity

return None

except Exception as e:
self._logger.errorf"Failed to find entity {entity_id}: {e}"
return None

async def find_allself, query_spec: QuerySpec = None -> List[T]:
"""查找所有實體"""
query_spec = query_spec or QuerySpec()

cache_key = f"find_all_{strquery_spec.__dict__}"
cached = self._get_cached_result'find_all', spec=cache_key
if cached:
return cached

try:    data = self._load_data()
entities = []

for entity_data in data.values():    entity = self._dict_to_entity(entity_data)

if self._apply_filtersentity, query_spec.filters:
entities.appendentity

if query_spec.sort_by:
entities.sort(
key=lambda x: getattrx, query_spec.sort_by, '',
reverse=query_spec.sort_desc
)

if query_spec.offset:    entities = entities[query_spec.offset:]
if query_spec.limit:    entities = entities[:query_spec.limit]

self._cache_result'find_all', entities, spec=cache_key

return entities

except Exception as e:
self._logger.errorf"Failed to find entities: {e}"
raise RepositoryExceptionf"Find failed: {e}"

def _apply_filtersself, entity: T, filters: Dict[str, Any] -> bool:
"""應用過濾器"""
for field, value in filters.items():
if hasattrentity, field:    entity_value = getattr(entity, field)
if entity_value != value:
return False
else:
return False
return True

async def updateself, entity: T -> T:
"""更新實體"""
return await self.saveentity

async def deleteself, entity_id: str -> bool:
"""刪除實體"""
try:    data = self._load_data()

if entity_id in data:

if hasattrself, '_index_fields':
for field in self._index_fields:
self.index_manager.remove_from_indexentity_id, field

del data[entity_id]
self._save_datadata

self._invalidate_cache()

self._logger.debugf"Deleted entity {entity_id}"
return True

return False

except Exception as e:
self._logger.errorf"Failed to delete entity {entity_id}: {e}"
return False

async def countself, query_spec: QuerySpec = None -> int:
"""計算實體數量"""
entities = await self.find_allquery_spec
return lenentities

def create_repository(entity_class: type, file_path: str,
cache_size: int = 1000) -> BaseRepository:
"""創建Repository實例"""
cache_manager = CacheManagercache_size
return JSONRepositoryfile_path, entity_class, cache_manager