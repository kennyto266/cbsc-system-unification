"""
数据同步器

实现价格和非价格数据流的同步管理，确保数据一致性和时间对齐。

Task #31: Data Flow Unification - Price and Non-Price Integration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import weakref

from src.unified.cache_manager import unified_cache_manager
from src.unified.quality_validator import data_quality_validator

logger = logging.getLogger(__name__)

class SyncStatus(Enum):
    """同步状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DataSource(str, Enum):
    """数据源类型"""
    PRICE = "price"
    HKMA = "hkma"
    SENTIMENT = "sentiment"
    ALTERNATIVE = "alternative"

@dataclass
class SyncTask:
    """同步任务"""
    task_id: str
    symbols: List[str]
    sources: List[DataSource]
    start_time: datetime
    end_time: datetime
    status: SyncStatus = SyncStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: Dict[str, float] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataSyncConfig:
    """数据同步配置"""
    max_concurrent_tasks: int = 10
    retry_attempts: int = 3
    retry_delay: float = 1.0
    batch_size: int = 100
    timeout_seconds: int = 300
    enable_quality_check: bool = True
    cache_sync_results: bool = True
    sync_interval: timedelta = field(default_factory=lambda: timedelta(minutes=5))

class DataSynchronizer:
    """数据同步器"""

    def __init__(self, config: Optional[DataSyncConfig] = None):
        self.config = config or DataSyncConfig()
        self.logger = logging.getLogger(__name__)

        # 同步任务管理
        self.active_tasks: Dict[str, SyncTask] = {}
        self.task_history: List[SyncTask] = []
        self.max_history_size = 100

        # 数据源适配器注册
        self.data_adapters: Dict[DataSource, Any] = {}
        self.source_priorities: Dict[DataSource, int] = {
            DataSource.PRICE: 1,
            DataSource.HKMA: 2,
            DataSource.SENTIMENT: 3,
            DataSource.ALTERNATIVE: 4
        }

        # 同步事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {
            'task_started': [],
            'task_completed': [],
            'task_failed': [],
            'data_synced': [],
            'quality_issue': []
        }

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_tasks)

        # 性能统计
        self.sync_stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_symbols_synced': 0,
            'average_sync_time': 0.0,
            'last_sync_time': None
        }

        logger.info(f"数据同步器初始化: 并发任务数={self.config.max_concurrent_tasks}")

    def register_adapter(self, source: DataSource, adapter: Any) -> None:
        """注册数据源适配器"""
        self.data_adapters[source] = adapter
        logger.info(f"注册数据源适配器: {source}")

    def register_callback(self, event: str, callback: Callable) -> None:
        """注册事件回调"""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
            logger.debug(f"注册事件回调: {event}")

    async def sync_data(
        self,
        symbols: List[str],
        sources: List[DataSource],
        start_time: datetime,
        end_time: Optional[datetime] = None,
        task_id: Optional[str] = None
    ) -> str:
        """启动数据同步任务"""
        try:
            # 生成任务ID
            if task_id is None:
                task_id = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(symbols)}_symbols"

            # 创建同步任务
            task = SyncTask(
                task_id=task_id,
                symbols=symbols,
                sources=sources,
                start_time=start_time,
                end_time=end_time or datetime.now()
            )

            # 检查是否有重复任务
            if task_id in self.active_tasks:
                raise ValueError(f"任务 {task_id} 已存在")

            self.active_tasks[task_id] = task
            self.sync_stats['total_tasks'] += 1

            # 启动异步同步任务
            asyncio.create_task(self._execute_sync_task(task))

            logger.info(f"启动同步任务: {task_id}, 股票数: {len(symbols)}, 数据源: {sources}")
            return task_id

        except Exception as e:
            self.logger.error(f"启动同步任务失败: {e}")
            raise

    async def _execute_sync_task(self, task: SyncTask) -> None:
        """执行同步任务"""
        try:
            task.status = SyncStatus.IN_PROGRESS
            task.started_at = datetime.now()

            # 触发任务开始事件
            await self._trigger_event('task_started', task)

            # 按优先级排序数据源
            sorted_sources = sorted(
                task.sources,
                key=lambda x: self.source_priorities.get(x, 999)
            )

            # 分批处理股票
            for i in range(0, len(task.symbols), self.config.batch_size):
                batch_symbols = task.symbols[i:i + self.config.batch_size]
                batch_results = await self._sync_symbol_batch(
                    batch_symbols, sorted_sources, task
                )

                # 更新进度
                progress = (i + len(batch_symbols)) / len(task.symbols)
                task.progress['overall'] = progress

                # 合并结果
                self._merge_batch_results(task.results, batch_results)

            # 任务完成
            task.status = SyncStatus.COMPLETED
            task.completed_at = datetime.now()

            # 更新统计信息
            self._update_sync_stats(task)

            # 缓存同步结果
            if self.config.cache_sync_results:
                await self._cache_sync_results(task)

            # 触发任务完成事件
            await self._trigger_event('task_completed', task)

            logger.info(f"同步任务完成: {task.task_id}")

        except Exception as e:
            task.status = SyncStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()

            self.sync_stats['failed_tasks'] += 1

            # 触发任务失败事件
            await self._trigger_event('task_failed', task)

            logger.error(f"同步任务失败: {task.task_id}, 错误: {e}")

        finally:
            # 移动到历史记录
            self._move_task_to_history(task)

    async def _sync_symbol_batch(
        self,
        symbols: List[str],
        sources: List[DataSource],
        task: SyncTask
    ) -> Dict[str, Any]:
        """同步股票批次"""
        batch_results = {}

        # 并发同步每个数据源
        source_tasks = []
        for source in sources:
            if source in self.data_adapters:
                source_task = self._sync_source_batch(symbols, source, task)
                source_tasks.append(source_task)

        # 等待所有数据源同步完成
        source_results = await asyncio.gather(*source_tasks, return_exceptions=True)

        # 整理结果
        for i, result in enumerate(source_results):
            if isinstance(result, Exception):
                self.logger.error(f"数据源同步失败 {sources[i]}: {result}")
                continue

            source = sources[i]
            batch_results[source.value] = result

        # 数据对齐和质量检查
        aligned_data = await self._align_data_sources(batch_results, symbols)
        if self.config.enable_quality_check:
            await self._perform_quality_check(aligned_data, task)

        return aligned_data

    def _sync_source_batch(
        self,
        symbols: List[str],
        source: DataSource,
        task: SyncTask
    ) -> asyncio.Future:
        """同步单个数据源批次"""
        def sync_in_thread():
            try:
                adapter = self.data_adapters[source]
                source_results = {}

                for symbol in symbols:
                    try:
                        # 调用适配器获取数据
                        data = adapter.get_data(
                            symbol,
                            task.start_time,
                            task.end_time
                        )

                        source_results[symbol] = {
                            'data': data,
                            'source': source.value,
                            'symbol': symbol,
                            'fetch_time': datetime.now().isoformat()
                        }

                    except Exception as e:
                        self.logger.error(f"获取{source.value}数据失败 {symbol}: {e}")
                        source_results[symbol] = {
                            'error': str(e),
                            'source': source.value,
                            'symbol': symbol
                        }

                return source_results

            except Exception as e:
                self.logger.error(f"同步{source.value}数据批次失败: {e}")
                raise

        return self.executor.submit(sync_in_thread)

    async def _align_data_sources(
        self,
        batch_results: Dict[str, Any],
        symbols: List[str]
    ) -> Dict[str, Any]:
        """对齐不同数据源的数据"""
        aligned_data = {}

        for symbol in symbols:
            symbol_data = {
                'symbol': symbol,
                'aligned_data': [],
                'sources_available': [],
                'alignment_issues': []
            }

            # 收集所有时间戳
            all_timestamps = set()
            source_data = {}

            for source_value, source_results in batch_results.items():
                symbol_result = source_results.get(symbol, {})
                if 'data' in symbol_result:
                    data_points = symbol_result['data']
                    source_data[source_value] = data_points

                    for point in data_points:
                        timestamp = self._parse_timestamp(point.get('timestamp'))
                        if timestamp:
                            all_timestamps.add(timestamp)

                    symbol_data['sources_available'].append(source_value)

            # 如果没有数据，跳过
            if not all_timestamps:
                aligned_data[symbol] = symbol_data
                continue

            # 排序时间戳
            sorted_timestamps = sorted(all_timestamps)

            # 创建时间对齐的数据结构
            for timestamp in sorted_timestamps:
                aligned_point = {
                    'timestamp': timestamp.isoformat(),
                    'symbol': symbol
                }

                # 为每个数据源查找对应时间点的数据
                for source_value, data_points in source_data.items():
                    matching_point = self._find_data_point_at_time(
                        data_points, timestamp
                    )
                    if matching_point:
                        aligned_point[source_value] = matching_point

                symbol_data['aligned_data'].append(aligned_point)

            # 检查对齐质量
            alignment_quality = self._check_alignment_quality(
                symbol_data['aligned_data'], symbol_data['sources_available']
            )

            symbol_data['alignment_quality'] = alignment_quality
            if alignment_quality['completeness'] < 0.8:
                symbol_data['alignment_issues'].append(
                    f"数据完整性较低: {alignment_quality['completeness']:.2%}"
                )

            aligned_data[symbol] = symbol_data

        return aligned_data

    def _find_data_point_at_time(
        self,
        data_points: List[Dict[str, Any]],
        target_time: datetime,
        tolerance_seconds: int = 60
    ) -> Optional[Dict[str, Any]]:
        """查找指定时间点的数据"""
        best_match = None
        min_diff = float('inf')

        for point in data_points:
            timestamp = self._parse_timestamp(point.get('timestamp'))
            if timestamp is None:
                continue

            time_diff = abs((timestamp - target_time).total_seconds())
            if time_diff <= tolerance_seconds and time_diff < min_diff:
                min_diff = time_diff
                best_match = point

        return best_match

    def _check_alignment_quality(
        self,
        aligned_data: List[Dict[str, Any]],
        available_sources: List[str]
    ) -> Dict[str, Any]:
        """检查数据对齐质量"""
        if not aligned_data:
            return {'completeness': 0.0, 'consistency': 0.0}

        total_points = len(aligned_data)
        complete_points = 0

        source_availability = {source: 0 for source in available_sources}

        for point in aligned_data:
            # 检查该时间点是否包含所有数据源的数据
            point_sources = [k for k in point.keys() if k in available_sources]
            if len(point_sources) == len(available_sources):
                complete_points += 1

            # 统计每个数据源的可用性
            for source in available_sources:
                if source in point:
                    source_availability[source] += 1

        completeness = complete_points / total_points if total_points > 0 else 0

        # 计算数据源一致性
        source_consistency = {
            source: count / total_points
            for source, count in source_availability.items()
        }

        avg_consistency = sum(source_consistency.values()) / len(source_consistency) if source_consistency else 0

        return {
            'completeness': completeness,
            'consistency': avg_consistency,
            'source_availability': source_consistency,
            'total_points': total_points,
            'complete_points': complete_points
        }

    async def _perform_quality_check(
        self,
        aligned_data: Dict[str, Any],
        task: SyncTask
    ) -> None:
        """执行数据质量检查"""
        try:
            for symbol, symbol_data in aligned_data.items():
                for source_value in symbol_data.get('sources_available', []):
                    # 提取该数据源的数据
                    source_data = []
                    for point in symbol_data.get('aligned_data', []):
                        if source_value in point:
                            source_data.append(point[source_value])

                    if source_data:
                        # 转换为验证器所需的格式
                        formatted_data = []
                        for dp in source_data:
                            formatted_data.append({
                                'timestamp': dp.get('timestamp'),
                                'value': dp.get('value'),
                                'symbol': symbol,
                                'source': source_value,
                                'data_type': source_value,
                                'metadata': dp.get('metadata', {})
                            })

                        # 执行质量验证
                        quality_result = await data_quality_validator.validate_data_quality(
                            formatted_data,
                            source_value,
                            symbol
                        )

                        # 如果质量分数过低，触发事件
                        if quality_result.overall_score < 0.7:
                            await self._trigger_event('quality_issue', {
                                'symbol': symbol,
                                'source': source_value,
                                'quality_result': quality_result,
                                'task_id': task.task_id
                            })

                        # 缓存质量结果
                        await unified_cache_manager.cache_quality_result(
                            source_value, symbol, quality_result.__dict__
                        )

        except Exception as e:
            self.logger.error(f"数据质量检查失败: {e}")

    def _merge_batch_results(self, task_results: Dict[str, Any], batch_results: Dict[str, Any]) -> None:
        """合并批次结果"""
        for symbol, symbol_data in batch_results.items():
            if symbol not in task_results:
                task_results[symbol] = symbol_data
            else:
                # 合并对齐数据
                existing_aligned = task_results[symbol].get('aligned_data', [])
                new_aligned = symbol_data.get('aligned_data', [])

                # 按时间戳合并并去重
                all_timestamps = set()
                for point in existing_aligned + new_aligned:
                    timestamp = point.get('timestamp')
                    if timestamp:
                        all_timestamps.add(timestamp)

                merged_aligned = []
                for timestamp in sorted(all_timestamps):
                    # 查找该时间戳的合并数据
                    merged_point = {'timestamp': timestamp, 'symbol': symbol}

                    # 从现有数据和新数据中合并
                    for source_data in existing_aligned + new_aligned:
                        if source_data.get('timestamp') == timestamp:
                            for key, value in source_data.items():
                                if key not in merged_point:
                                    merged_point[key] = value

                    merged_aligned.append(merged_point)

                task_results[symbol]['aligned_data'] = merged_aligned

                # 合并其他元数据
                if 'sources_available' in symbol_data:
                    existing_sources = set(task_results[symbol].get('sources_available', []))
                    new_sources = set(symbol_data['sources_available'])
                    task_results[symbol]['sources_available'] = list(existing_sources | new_sources)

    def _update_sync_stats(self, task: SyncTask) -> None:
        """更新同步统计信息"""
        self.sync_stats['successful_tasks'] += 1
        self.sync_stats['total_symbols_synced'] += len(task.symbols)

        # 更新平均同步时间
        if task.started_at and task.completed_at:
            sync_duration = (task.completed_at - task.started_at).total_seconds()
            total_successful = self.sync_stats['successful_tasks']

            if total_successful == 1:
                self.sync_stats['average_sync_time'] = sync_duration
            else:
                current_avg = self.sync_stats['average_sync_time']
                self.sync_stats['average_sync_time'] = (
                    (current_avg * (total_successful - 1) + sync_duration) / total_successful
                )

        self.sync_stats['last_sync_time'] = task.completed_at

    async def _cache_sync_results(self, task: SyncTask) -> None:
        """缓存同步结果"""
        try:
            for symbol, symbol_data in task.results.items():
                for source_value in symbol_data.get('sources_available', []):
                    # 提取该数据源的数据序列
                    source_series = []
                    for point in symbol_data.get('aligned_data', []):
                        if source_value in point:
                            source_series.append(point[source_value])

                    if source_series:
                        # 缓存数据序列
                        await unified_cache_manager.cache_unified_series(
                            symbol, source_value, source_series
                        )

        except Exception as e:
            self.logger.error(f"缓存同步结果失败: {e}")

    async def _trigger_event(self, event: str, data: Any) -> None:
        """触发事件回调"""
        try:
            callbacks = self.event_callbacks.get(event, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.error(f"事件回调执行失败 {event}: {e}")

        except Exception as e:
            self.logger.error(f"触发事件失败 {event}: {e}")

    def _move_task_to_history(self, task: SyncTask) -> None:
        """移动任务到历史记录"""
        try:
            # 从活动任务中移除
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]

            # 添加到历史记录
            self.task_history.append(task)

            # 限制历史记录大小
            if len(self.task_history) > self.max_history_size:
                self.task_history = self.task_history[-self.max_history_size:]

        except Exception as e:
            self.logger.error(f"移动任务到历史记录失败: {e}")

    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """解析时间戳"""
        if timestamp is None:
            return None

        try:
            if isinstance(timestamp, datetime):
                return timestamp
            elif isinstance(timestamp, str):
                # 尝试多种时间格式
                formats = [
                    '%Y-%m-%dT%H:%M:%S.%fZ',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%d'
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except ValueError:
                        continue
                return None
            else:
                return None

        except Exception:
            return None

    def get_task_status(self, task_id: str) -> Optional[SyncTask]:
        """获取任务状态"""
        return self.active_tasks.get(task_id)

    def get_active_tasks(self) -> List[SyncTask]:
        """获取活动任务列表"""
        return list(self.active_tasks.values())

    def get_task_history(self, limit: int = 50) -> List[SyncTask]:
        """获取任务历史"""
        return self.task_history[-limit:]

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = SyncStatus.CANCELLED
                task.completed_at = datetime.now()
                self._move_task_to_history(task)
                return True
            return False

        except Exception as e:
            self.logger.error(f"取消任务失败 {task_id}: {e}")
            return False

    def get_sync_stats(self) -> Dict[str, Any]:
        """获取同步统计信息"""
        return self.sync_stats.copy()

    async def cleanup_completed_tasks(self) -> int:
        """清理已完成的任务"""
        try:
            completed_count = 0
            tasks_to_remove = []

            for task_id, task in self.active_tasks.items():
                if task.status in [SyncStatus.COMPLETED, SyncStatus.FAILED, SyncStatus.CANCELLED]:
                    tasks_to_remove.append(task_id)

            for task_id in tasks_to_remove:
                task = self.active_tasks[task_id]
                self._move_task_to_history(task)
                completed_count += 1

            logger.info(f"清理了 {completed_count} 个已完成的任务")
            return completed_count

        except Exception as e:
            self.logger.error(f"清理任务失败: {e}")
            return 0

    async def close(self):
        """关闭数据同步器"""
        try:
            # 取消所有活动任务
            active_task_ids = list(self.active_tasks.keys())
            for task_id in active_task_ids:
                self.cancel_task(task_id)

            # 关闭线程池
            self.executor.shutdown(wait=True)

            logger.info("数据同步器已关闭")

        except Exception as e:
            self.logger.error(f"关闭数据同步器失败: {e}")

# 创建全局数据同步器实例
data_synchronizer = DataSynchronizer()

# 导出主要类和实例
__all__ = [
    'DataSynchronizer',
    'data_synchronizer',
    'SyncTask',
    'SyncStatus',
    'DataSource',
    'DataSyncConfig'
]