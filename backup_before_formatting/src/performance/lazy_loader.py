"""
懒加载系统

提供高效的懒加载功能：
- 大数据集懒加载
- 内存管理
- 按需加载
- 数据分页
- 内存监控
- 自动清理
"""

import gc
import json
import logging
import os
import pickle
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    TypeVar,
    Union,
)

import psutil

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class MemoryStats:
    """内存统计信息"""

    used_mb: float
    available_mb: float
    total_mb: float
    usage_percent: float
    timestamp: float = field(default_factory=time.time)


class MemoryManager:
    """
    内存管理器

    负责：
    - 内存使用监控
    - 自动垃圾回收
    - 内存压力检测
    - 内存清理策略
    """

    def __init__(
        self,
        max_memory_percent: float = 80.0,
        gc_threshold: int = 100,
        monitor_interval: float = 5.0,
    ):
        self.max_memory_percent = max_memory_percent
        self.gc_threshold = gc_threshold
        self.monitor_interval = monitor_interval
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stats_history: List[MemoryStats] = []
        self._lock = threading.Lock()

    def start_monitoring(self):
        """启动内存监控"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("内存监控已启动")

    def stop_monitoring(self):
        """停止内存监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
        logger.info("内存监控已停止")

    def _monitor_loop(self):
        """内存监控循环"""
        while self._monitoring:
            try:
                stats = self.get_memory_stats()
                self._record_stats(stats)

                # 检查内存压力
                if stats.usage_percent > self.max_memory_percent:
                    logger.warning(
                        f"内存使用率过高: {stats.usage_percent:.1f}%\n"
                        f"当前: {stats.used_mb:.2f}MB / {stats.total_mb:.2f}MB"
                    )
                    self.trigger_cleanup()

                time.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"内存监控错误: {e}")

    def _record_stats(self, stats: MemoryStats):
        """记录内存统计"""
        with self._lock:
            self._stats_history.append(stats)
            # 只保留最近1000条记录
            if len(self._stats_history) > 1000:
                self._stats_history = self._stats_history[-1000:]

    def get_memory_stats(self) -> MemoryStats:
        """获取当前内存统计"""
        process = psutil.Process()
        memory_info = process.memory_info()
        virtual_memory = psutil.virtual_memory()

        used_mb = memory_info.rss / 1024 / 1024
        total_mb = virtual_memory.total / 1024 / 1024
        available_mb = virtual_memory.available / 1024 / 1024
        usage_percent = (used_mb / total_mb) * 100

        return MemoryStats(
            used_mb=used_mb,
            available_mb=available_mb,
            total_mb=total_mb,
            usage_percent=usage_percent,
        )

    def get_usage_history(self, limit: int = 100) -> List[MemoryStats]:
        """获取内存使用历史"""
        with self._lock:
            return self._stats_history[-limit:]

    def trigger_cleanup(self):
        """触发内存清理"""
        logger.info("执行内存清理...")

        # 强制垃圾回收
        collected = gc.collect()
        logger.info(f"垃圾回收完成，回收对象: {collected}个")

        # 获取清理后内存
        stats_after = self.get_memory_stats()
        logger.info(
            f"清理后内存使用: {stats_after.used_mb:.2f}MB "
            f"({stats_after.usage_percent:.1f}%)"
        )

    def check_memory_pressure(self) -> bool:
        """检查是否有内存压力"""
        stats = self.get_memory_stats()
        return stats.usage_percent > self.max_memory_percent


class LazyLoader(Generic[T]):
    """
    懒加载基类

    特点：
    - 延迟加载数据
    - 按需加载
    - 内存友好
    - 支持缓存
    """

    def __init__(
        self,
        loader_func: Callable[[], T],
        cache: bool = True,
        memory_manager: Optional[MemoryManager] = None,
    ):
        self.loader_func = loader_func
        self.cache = cache
        self.memory_manager = memory_manager
        self._data: Optional[T] = None
        self._loaded = False
        self._lock = threading.RLock()

    def load(self) -> T:
        """
        加载数据（如果尚未加载）

        Returns:
            加载的数据
        """
        with self._lock:
            if not self._loaded:
                logger.info("懒加载器：开始加载数据")
                start_time = time.perf_counter()

                self._data = self.loader_func()

                # 内存监控
                if self.memory_manager:
                    self.memory_manager.trigger_cleanup()

                self._loaded = True
                load_time = time.perf_counter() - start_time
                logger.info(f"懒加载器：数据加载完成，耗时 {load_time:.3f}秒")
            else:
                logger.debug("懒加载器：使用缓存数据")

            return self._data

    def is_loaded(self) -> bool:
        """检查数据是否已加载"""
        return self._loaded

    def unload(self):
        """卸载数据（释放内存）"""
        with self._lock:
            if self.cache:
                # 如果启用缓存，保留数据但标记为未加载
                self._loaded = False
            else:
                # 如果未启用缓存，删除数据
                self._data = None
                self._loaded = False
                gc.collect()

        logger.info("懒加载器：数据已卸载")

    def get(self) -> Optional[T]:
        """
        获取数据（如果已加载，否则返回None）

        Returns:
            数据或None
        """
        if self._loaded:
            return self._data
        return None


class DataFrameLazyLoader(LazyLoader):
    """
    DataFrame懒加载器

    专为pandas DataFrame优化：
    - 支持列懒加载
    - 支持分块加载
    - 内存监控
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        memory_manager: Optional[MemoryManager] = None,
        chunk_size: Optional[int] = None,
        columns: Optional[List[str]] = None,
        dtype: Optional[Dict[str, Any]] = None,
        nrows: Optional[int] = None,
    ):
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.columns = columns
        self.dtype = dtype
        self.nrows = nrows
        self._data = None
        self._metadata: Optional[Dict[str, Any]] = None

        # 获取数据大小（用于内存估算）
        self._file_size = self.file_path.stat().st_size / 1024 / 1024  # MB

        super().__init__(
            loader_func=self._load_dataframe, cache=True, memory_manager=memory_manager
        )

    def _load_dataframe(self):
        """加载DataFrame"""
        import pandas as pd

        logger.info(f"加载DataFrame: {self.file_path}")
        logger.info(f"预估文件大小: {self._file_size:.2f}MB")

        # 根据文件大小决定加载策略
        if self._file_size > 500:  # 500MB
            logger.warning("文件较大，建议使用chunk_size分块加载")
        elif self._file_size > 100:  # 100MB
            logger.info("文件较大，使用分块加载")
            self.chunk_size = self.chunk_size or 50000

        # 加载数据
        try:
            if self.chunk_size:
                # 分块加载
                chunks = []
                total_rows = 0

                for chunk in pd.read_csv(
                    self.file_path,
                    chunksize=self.chunk_size,
                    usecols=self.columns,
                    dtype=self.dtype,
                    nrows=self.nrows,
                ):
                    # 内存压力检查
                    if (
                        self.memory_manager
                        and self.memory_manager.check_memory_pressure()
                    ):
                        logger.warning("内存压力较高，停止加载")
                        break

                    chunks.append(chunk)
                    total_rows += len(chunk)

                    logger.debug(f"已加载 {total_rows} 行")

                # 合并所有块
                data = (
                    pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
                )
            else:
                # 一次性加载
                data = pd.read_csv(
                    self.file_path,
                    usecols=self.columns,
                    dtype=self.dtype,
                    nrows=self.nrows,
                )

            # 保存元数据
            self._metadata = {
                "shape": data.shape,
                "columns": list(data.columns),
                "dtypes": {col: str(dtype) for col, dtype in data.dtypes.items()},
                "memory_usage_mb": data.memory_usage(deep=True).sum() / 1024 / 1024,
            }

            logger.info(f"DataFrame加载完成: {data.shape}")

            # 内存监控
            if self.memory_manager:
                self.memory_manager.trigger_cleanup()

            return data

        except Exception as e:
            logger.error(f"加载DataFrame失败: {e}")
            raise

    def load_columns(self, columns: List[str]) -> "DataFrameLazyLoader":
        """
        加载指定列

        Args:
            columns: 列名列表

        Returns:
            新的懒加载器
        """
        return DataFrameLazyLoader(
            file_path=self.file_path,
            memory_manager=self.memory_manager,
            chunk_size=self.chunk_size,
            columns=columns,
            dtype=self.dtype,
            nrows=self.nrows,
        )

    def load_sample(
        self, frac: float = 0.1, random_state: int = 42
    ) -> "DataFrameLazyLoader":
        """
        加载样本数据

        Args:
            frac: 采样比例
            random_state: 随机种子

        Returns:
            新的懒加载器
        """
        import pandas as pd

        # 使用pandas的采样功能
        def load_sample_data():
            data = self.load()
            return data.sample(frac=frac, random_state=random_state)

        return DataFrameLazyLoader(
            file_path=self.file_path,
            memory_manager=self.memory_manager,
            chunk_size=self.chunk_size,
            columns=self.columns,
            dtype=self.dtype,
            nrows=self.nrows,
        )

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """获取DataFrame元数据"""
        if self._metadata is None and self._loaded:
            import pandas as pd

            data = self._data
            self._metadata = {
                "shape": data.shape,
                "columns": list(data.columns),
                "dtypes": {col: str(dtype) for col, dtype in data.dtypes.items()},
                "memory_usage_mb": data.memory_usage(deep=True).sum() / 1024 / 1024,
            }
        return self._metadata

    def get_memory_usage(self) -> float:
        """获取内存使用量（MB）"""
        if not self._loaded:
            return 0.0

        if self._metadata and "memory_usage_mb" in self._metadata:
            return self._metadata["memory_usage_mb"]

        import pandas as pd

        if isinstance(self._data, pd.DataFrame):
            return self._data.memory_usage(deep=True).sum() / 1024 / 1024

        return 0.0


class PagedDataLoader(Generic[T]):
    """
    分页数据加载器

    特点：
    - 大数据集分页处理
    - 按需加载页面
    - 支持多种数据源
    - 内存友好
    """

    def __init__(
        self,
        data_source: Union[Iterator[T], Callable[[int, int], List[T]]],
        total_count: Optional[int] = None,
        page_size: int = 1000,
        preloaded_pages: int = 2,
    ):
        self.data_source = data_source
        self.total_count = total_count
        self.page_size = page_size
        self.preloaded_pages = preloaded_pages

        self._cache: Dict[int, List[T]] = {}
        self._page_count = (
            (total_count + page_size - 1) // page_size if total_count else None
        )
        self._loaded_pages: set[int] = set()
        self._lock = threading.RLock()

    def get_page(self, page_num: int) -> List[T]:
        """
        获取指定页

        Args:
            page_num: 页码（从0开始）

        Returns:
            页面数据
        """
        with self._lock:
            # 检查缓存
            if page_num in self._cache:
                logger.debug(f"从缓存获取页: {page_num}")
                return self._cache[page_num]

            # 加载数据
            start_idx = page_num * self.page_size
            end_idx = min(start_idx + self.page_size, self.total_count or float("inf"))

            if callable(self.data_source):
                # 如果是函数，直接调用
                data = self.data_source(start_idx, end_idx)
            else:
                # 如果是迭代器，需要转换
                data = list(self.data_source)

            # 缓存数据
            self._cache[page_num] = data
            self._loaded_pages.add(page_num)

            # 预加载相邻页面
            self._preload_pages(page_num)

            logger.info(f"加载页: {page_num}, 数据量: {len(data)}")

            return data

    def _preload_pages(self, current_page: int):
        """预加载相邻页面"""
        for offset in range(1, self.preloaded_pages + 1):
            # 预加载下一页
            next_page = current_page + offset
            if next_page not in self._cache and self._is_page_valid(next_page):
                self._load_page_async(next_page)

            # 预加载上一页
            prev_page = current_page - offset
            if prev_page not in self._cache and self._is_page_valid(prev_page):
                self._load_page_async(prev_page)

    def _is_page_valid(self, page_num: int) -> bool:
        """检查页码是否有效"""
        if self.total_count is None:
            return True

        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        return 0 <= page_num < total_pages

    def _load_page_async(self, page_num: int):
        """异步加载页面"""

        def _load():
            self.get_page(page_num)

        import threading

        thread = threading.Thread(target=_load, daemon=True)
        thread.start()

    def get_total_pages(self) -> Optional[int]:
        """获取总页数"""
        if self._page_count is not None:
            return self._page_count

        # 如果没有指定总数，尝试计算
        if callable(self.data_source):
            # 尝试加载第一页来估算
            first_page = self.get_page(0)
            if not first_page:
                return 0

            # 如果数据源返回了实际数量
            if hasattr(first_page, "__len__"):
                # 估算总页数
                # 注意：这不是精确的总数
                pass

        return self._page_count

    def get_stats(self) -> Dict[str, Any]:
        """获取分页统计信息"""
        return {
            "total_pages": self.get_total_pages(),
            "page_size": self.page_size,
            "loaded_pages": len(self._loaded_pages),
            "cache_size": len(self._cache),
            "loaded_page_numbers": sorted(list(self._loaded_pages)),
        }


class MemoryManagedLoader:
    """
    内存管理的数据加载器

    特点：
    - 自动内存管理
    - 内存压力检测
    - 智能缓存策略
    - 内存清理
    """

    def __init__(
        self,
        max_memory_mb: float = 1000.0,
        gc_trigger_threshold: float = 0.8,
        monitor_interval: float = 5.0,
    ):
        self.max_memory_mb = max_memory_mb
        self.gc_trigger_threshold = gc_trigger_threshold
        self.monitor_interval = monitor_interval

        self.memory_manager = MemoryManager(
            max_memory_percent=(gc_trigger_threshold * 100),
            monitor_interval=monitor_interval,
        )

        self._active_loaders: List[LazyLoader] = []
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()

        # 启动内存监控
        self.memory_manager.start_monitoring()

    def register_loader(self, loader: LazyLoader):
        """注册懒加载器"""
        with self._lock:
            self._active_loaders.append(loader)

        logger.info(f"注册懒加载器，当前活跃: {len(self._active_loaders)}个")

    def unregister_loader(self, loader: LazyLoader):
        """注销懒加载器"""
        with self._lock:
            if loader in self._active_loaders:
                self._active_loaders.remove(loader)
                logger.info(f"注销懒加载器，当前活跃: {len(self._active_loaders)}个")

    def get_cached_data(
        self, key: str, loader_func: Callable[[], Any], force_reload: bool = False
    ) -> Any:
        """
        获取缓存数据

        Args:
            key: 缓存键
            loader_func: 加载函数
            force_reload: 是否强制重新加载

        Returns:
            数据
        """
        with self._lock:
            # 检查缓存
            if not force_reload and key in self._cache:
                return self._cache[key]

            # 内存压力检查
            if self.memory_manager.check_memory_pressure():
                logger.warning("内存压力较高，清理缓存")
                self.clear_cache()

            # 加载数据
            data = loader_func()

            # 添加到缓存
            self._cache[key] = data

            # 注册为懒加载器
            loader = LazyLoader(
                loader_func=lambda: self._cache[key],
                cache=True,
                memory_manager=self.memory_manager,
            )
            self.register_loader(loader)

            return data

    def clear_cache(self, keep_keys: Optional[List[str]] = None):
        """
        清空缓存

        Args:
            keep_keys: 保留的键
        """
        with self._lock:
            if keep_keys is None:
                keep_keys = []

            # 保留指定键，删除其他
            keys_to_remove = [k for k in self._cache.keys() if k not in keep_keys]
            for key in keys_to_remove:
                del self._cache[key]

            # 触发垃圾回收
            self.memory_manager.trigger_cleanup()

            logger.info(f"清空缓存，保留: {keep_keys}")

    def get_memory_stats(self) -> MemoryStats:
        """获取内存统计"""
        return self.memory_manager.get_memory_stats()

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计信息"""
        return {
            "memory": {
                "max_memory_mb": self.max_memory_mb,
                "current": self.get_memory_stats().__dict__,
            },
            "cache": {"size": len(self._cache), "keys": list(self._cache.keys())},
            "loaders": {"active_count": len(self._active_loaders)},
        }

    def shutdown(self):
        """关闭加载器并清理资源"""
        logger.info("关闭内存管理加载器")

        # 停止监控
        self.memory_manager.stop_monitoring()

        # 清空缓存
        self.clear_cache()

        # 卸载所有懒加载器
        with self._lock:
            for loader in self._active_loaders:
                loader.unload()
            self._active_loaders.clear()

        logger.info("内存管理加载器已关闭")


# 便捷装饰器
def lazy_load(cache: bool = True, memory_manager: Optional[MemoryManager] = None):
    """
    懒加载装饰器

    Args:
        cache: 是否缓存结果
        memory_manager: 内存管理器

    Usage:
        @lazy_load()
        def expensive_function():
            return heavy_computation()
    """

    def decorator(func: Callable) -> Callable:
        loader = LazyLoader(
            loader_func=func, cache=cache, memory_manager=memory_manager
        )

        @wraps(func)
        def wrapper(*args, **kwargs):
            return loader.load()

        # 添加额外方法
        wrapper.load = loader.load
        wrapper.unload = loader.unload
        wrapper.is_loaded = loader.is_loaded

        return wrapper

    return decorator


def memory_efficient(chunk_size: int = 10000, max_memory_mb: float = 1000.0):
    """
    内存高效装饰器

    Args:
        chunk_size: 批处理大小
        max_memory_mb: 最大内存使用

    Usage:
        @memory_efficient(chunk_size=5000)
        def process_large_data(data):
            for chunk in chunked(data, chunk_size):
                process(chunk)
    """

    def decorator(func: Callable) -> Callable:
        memory_manager = MemoryManager(
            max_memory_percent=(max_memory_mb / 1024) * 100 if max_memory_mb else None
        )
        memory_manager.start_monitoring()

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 内存压力检查
            if memory_manager.check_memory_pressure():
                memory_manager.trigger_cleanup()

            result = func(*args, **kwargs)

            # 清理
            memory_manager.trigger_cleanup()

            return result

        wrapper.memory_manager = memory_manager
        wrapper.shutdown = memory_manager.stop_monitoring

        return wrapper

    return decorator


# 全局内存管理器实例
_global_memory_manager = MemoryManager()
