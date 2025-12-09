"""
I / O优化器

提供数据库查询和文件I / O优化功能：
- 数据库连接池
- 查询优化
- 批量操作
- 异步I / O
- 读写分离
- 查询缓存
"""

import asyncio

import aiofiles
import aiohttp

try:
    import asyncpg
except ImportError:
    asyncpg = None
import csv
import hashlib
import json
import logging
import pickle
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class QueryResult:
    """查询结果"""

    rows: List[Dict[str, Any]]
    execution_time: float
    row_count: int
    query_hash: str


@dataclass
class BatchOperation:
    """批量操作"""

    operation_type: str  # 'insert', 'update', 'delete'
    table_name: str
    data: List[Dict[str, Any]]
    batch_size: int = 1000
    chunk_size: int = 100


class DatabaseQueryOptimizer:
    """
    数据库查询优化器

    功能：
    - 查询计划分析
    - 索引建议
    - 查询缓存
    - 慢查询检测
    - 批量操作优化
    """

    def __init__(
        self, connection_pool: Optional["asyncpg.Pool"] = None, cache_ttl: float = 300
    ):
        self.connection_pool = connection_pool
        self.cache_ttl = cache_ttl
        self._query_cache: Dict[str, Tuple[QueryResult, float]] = {}
        self._slow_queries: List[Tuple[str, float]] = []
        self._slow_query_threshold = 1.0  # 秒
        self._lock = threading.Lock()
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "slow_queries": 0,
        }

    def _generate_query_hash(self, query: str, params: Tuple) -> str:
        """生成查询哈希"""
        query_data = f"{query}:{str(params)}"
        return hashlib.sha256(query_data.encode()).hexdigest()

    def _is_cache_valid(self, timestamp: float) -> bool:
        """检查缓存是否有效"""
        return time.time() - timestamp < self.cache_ttl

    async def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> QueryResult:
        """
        执行查询（带优化）

        Args:
            query: SQL查询
            params: 查询参数
            use_cache: 是否使用缓存
            force_refresh: 是否强制刷新缓存

        Returns:
            查询结果
        """
        if not self.connection_pool:
            raise ValueError("数据库连接池未配置")

        start_time = time.perf_counter()
        query_hash = self._generate_query_hash(query, params or ())

        # 尝试从缓存获取
        if use_cache and not force_refresh:
            with self._lock:
                if query_hash in self._query_cache:
                    result, cache_time = self._query_cache[query_hash]
                    if self._is_cache_valid(cache_time):
                        self._stats["cache_hits"] += 1
                        return result
                    else:
                        # 缓存过期，删除
                        del self._query_cache[query_hash]

        # 执行查询
        async with self.connection_pool.acquire() as conn:
            try:
                if params:
                    rows = await conn.fetch(query, *params)
                else:
                    rows = await conn.fetch(query)

                execution_time = time.perf_counter() - start_time
                result = QueryResult(
                    rows=[dict(row) for row in rows],
                    execution_time=execution_time,
                    row_count=len(rows),
                    query_hash=query_hash,
                )

                # 统计
                with self._lock:
                    self._stats["total_queries"] += 1
                    if execution_time > self._slow_query_threshold:
                        self._slow_queries.append((query, execution_time))
                        self._stats["slow_queries"] += 1

                # 缓存结果
                if use_cache:
                    with self._lock:
                        self._query_cache[query_hash] = (result, time.time())

                # 检查慢查询
                if execution_time > self._slow_query_threshold:
                    logger.warning(
                        f"慢查询检测: {execution_time:.3f}s\n"
                        f"Query: {query[:100]}..."
                    )

                return result

            except Exception as e:
                execution_time = time.perf_counter() - start_time
                logger.error(
                    f"查询执行失败: {e}\nQuery: {query}\nTime: {execution_time:.3f}s"
                )
                raise

    async def execute_batch(
        self, batch_ops: List[BatchOperation], transaction: bool = True
    ) -> List[bool]:
        """
        批量执行操作

        Args:
            batch_ops: 批量操作列表
            transaction: 是否使用事务

        Returns:
            操作结果列表
        """
        if not self.connection_pool:
            raise ValueError("数据库连接池未配置")

        results = []

        if transaction:
            async with self.connection_pool.acquire() as conn:
                async with conn.transaction():
                    for op in batch_ops:
                        result = await self._execute_batch_operation(conn, op)
                        results.append(result)
        else:
            for op in batch_ops:
                result = await self._execute_batch_operation(op)
                results.append(result)

        return results

    async def _execute_batch_operation(self, conn: Any, op: BatchOperation) -> bool:
        """执行单个批量操作"""
        try:
            if op.operation_type == "insert":
                return await self._batch_insert(conn, op)
            elif op.operation_type == "update":
                return await self._batch_update(conn, op)
            elif op.operation_type == "delete":
                return await self._batch_delete(conn, op)
            else:
                raise ValueError(f"不支持的操作类型: {op.operation_type}")
        except Exception as e:
            logger.error(f"批量操作失败: {e}")
            return False

    async def _batch_insert(self, conn: Any, op: BatchOperation) -> bool:
        """批量插入"""
        if not op.data:
            return True

        # 构建插入语句
        columns = list(op.data[0].keys())
        placeholders = ", ".join([f"${i}" for i in range(1, len(columns) + 1)])

        query = f"INSERT INTO {op.table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        # 分批执行
        for i in range(0, len(op.data), op.batch_size):
            batch = op.data[i : i + op.batch_size]
            values = []

            for row in batch:
                row_values = tuple(row[col] for col in columns)
                values.extend(row_values)

            try:
                await conn.execute(query, *values)
            except Exception as e:
                logger.error(f"批量插入失败 (batch {i}): {e}")
                return False

        return True

    async def _batch_update(self, conn: Any, op: BatchOperation) -> bool:
        """批量更新"""
        # 实现批量更新逻辑
        # 这里需要根据具体表结构来实现
        for row in op.data:
            conditions = " AND ".join(
                [f"{k} = ${i}" for i, k in enumerate(row.keys(), 1)]
            )
            query = f"UPDATE {op.table_name} SET {', '.join([f'{k} = ${i}' for i, k in enumerate(row.keys(), 1)])} WHERE {conditions}"

            try:
                await conn.execute(query, *row.values())
            except Exception as e:
                logger.error(f"批量更新失败: {e}")
                return False

        return True

    async def _batch_delete(self, conn: Any, op: BatchOperation) -> bool:
        """批量删除"""
        # 实现批量删除逻辑
        if not op.data:
            return True

        # 使用WHERE IN子句
        for i in range(0, len(op.data), op.batch_size):
            batch = op.data[i : i + op.batch_size]
            # 假设有主键列 'id'
            ids = [row.get("id") for row in batch if "id" in row]
            if ids:
                placeholders = ", ".join([f"${i}" for i in range(1, len(ids) + 1)])
                query = f"DELETE FROM {op.table_name} WHERE id IN ({placeholders})"

                try:
                    await conn.execute(query, *ids)
                except Exception as e:
                    logger.error(f"批量删除失败: {e}")
                    return False

        return True

    def analyze_query_performance(self) -> Dict[str, Any]:
        """分析查询性能"""
        with self._lock:
            total = self._stats["total_queries"]
            cache_hit_rate = self._stats["cache_hits"] / total if total > 0 else 0

            # 慢查询分析
            slow_queries_sorted = sorted(
                self._slow_queries, key=lambda x: x[1], reverse=True
            )[
                :10
            ]  # Top 10

            return {
                "total_queries": total,
                "cache_hit_rate": cache_hit_rate,
                "cache_hits": self._stats["cache_hits"],
                "cache_misses": self._stats["cache_misses"],
                "slow_queries_count": self._stats["slow_queries"],
                "slow_queries": [
                    {"query": q[:100] + "...", "time": t}
                    for q, t in slow_queries_sorted
                ],
            }

    def clear_cache(self):
        """清空查询缓存"""
        with self._lock:
            self._query_cache.clear()

    def clear_stats(self):
        """清空统计信息"""
        with self._lock:
            self._stats = {
                "total_queries": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "slow_queries": 0,
            }
            self._slow_queries.clear()


class AsyncIOBatchProcessor:
    """
    异步I / O批量处理器

    功能：
    - 异步文件读写
    - 批量数据处理
    - 流式处理
    - 内存优化
    """

    def __init__(
        self, max_workers: int = 4, chunk_size: int = 10000, max_memory_mb: int = 100
    ):
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def read_csv_async(
        self,
        file_path: Union[str, Path],
        encoding: str = "utf - 8",
        has_header: bool = True,
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        异步读取CSV文件（分块）

        Args:
            file_path: 文件路径
            encoding: 编码
            has_header: 是否有表头

        Yields:
            数据块
        """
        file_path = Path(file_path)

        async with aiofiles.open(file_path, "r", encoding=encoding) as f:
            chunk = []
            header = None

            async for line in f:
                line = line.strip()
                if not line:
                    continue

                if has_header and header is None:
                    header = next(csv.reader([line]))
                    continue

                row = next(csv.reader([line]))
                if header:
                    row_dict = dict(zip(header, row))
                else:
                    row_dict = {f"col_{i}": val for i, val in enumerate(row)}

                chunk.append(row_dict)

                if len(chunk) >= self.chunk_size:
                    yield chunk
                    chunk = []

            if chunk:
                yield chunk

    async def write_csv_async(
        self,
        file_path: Union[str, Path],
        data_iter: Iterator[Dict[str, Any]],
        encoding: str = "utf - 8",
    ):
        """
        异步写入CSV文件

        Args:
            file_path: 文件路径
            data_iter: 数据迭代器
            encoding: 编码
        """
        file_path = Path(file_path)

        # 准备文件
        first_row = None
        fieldnames = None

        # 获取字段名
        async for chunk in self._iterate_data(data_iter):
            if chunk:
                fieldnames = list(chunk[0].keys())
                first_row = chunk[0]
                break

        if not first_row:
            logger.warning("没有数据可写入")
            return

        # 写入文件
        async with aiofiles.open(file_path, "w", encoding=encoding, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            await writer.writeheader()

            # 写入第一行
            await writer.writerow(first_row)

            # 写入剩余数据
            remaining_written = False
            async for chunk in self._iterate_data(data_iter):
                for row in chunk:
                    if row != first_row or not remaining_written:
                        await writer.writerow(row)
                        remaining_written = True

    async def _iterate_data(
        self, data_iter: Iterator[Dict[str, Any]]
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """迭代数据（转换为异步）"""
        loop = asyncio.get_event_loop()

        def _next_chunk():
            chunk = []
            try:
                for _ in range(self.chunk_size):
                    chunk.append(next(data_iter))
            except StopIteration:
                pass
            return chunk

        while True:
            chunk = await loop.run_in_executor(self._executor, _next_chunk)
            if not chunk:
                break
            yield chunk

    async def process_large_file(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        processor: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]],
        input_format: str = "csv",
        output_format: str = "csv",
    ):
        """
        处理大文件（流式处理）

        Args:
            input_path: 输入文件
            output_path: 输出文件
            processor: 处理函数
            input_format: 输入格式
            output_format: 输出格式
        """
        logger.info(f"开始处理文件: {input_path}")

        if input_format == "csv":
            data_generator = self.read_csv_async(input_path)
        else:
            raise ValueError(f"不支持的输入格式: {input_format}")

        # 创建输出迭代器
        async def output_generator():
            async for chunk in data_generator:
                processed = processor(chunk)
                for row in processed:
                    yield row

        if output_format == "csv":
            await self.write_csv_async(output_path, output_generator())
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")

        logger.info(f"文件处理完成: {output_path}")

    async def parallel_process_files(
        self,
        file_paths: List[Union[str, Path]],
        processor: Callable[[Path], Any],
        max_concurrent: int = 4,
    ) -> List[Any]:
        """
        并行处理多个文件

        Args:
            file_paths: 文件路径列表
            processor: 处理函数
            max_concurrent: 最大并发数

        Returns:
            处理结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def process_single_file(file_path):
            async with semaphore:
                return await processor(Path(file_path))

        tasks = [process_single_file(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks)

        return results

    async def load_dataframe_chunks(
        self,
        file_path: Union[str, Path],
        chunk_processor: Callable[[List[Dict[str, Any]]], Any],
        max_chunks: Optional[int] = None,
    ) -> List[Any]:
        """
        分块加载数据并处理

        Args:
            file_path: 文件路径
            chunk_processor: 块处理器
            max_chunks: 最大块数

        Returns:
            处理结果列表
        """
        results = []
        chunk_count = 0

        async for chunk in self.read_csv_async(file_path):
            if max_chunks and chunk_count >= max_chunks:
                break

            result = await asyncio.get_event_loop().run_in_executor(
                self._executor, chunk_processor, chunk
            )
            results.append(result)
            chunk_count += 1

            if chunk_count % 10 == 0:
                logger.info(f"已处理 {chunk_count} 个数据块")

        logger.info(f"总计处理 {chunk_count} 个数据块")
        return results


class IOOptimizer:
    """
    I / O优化器主类

    统一管理：
    - 数据库优化
    - 文件I / O优化
    - 缓存策略
    """

    def __init__(self):
        self.query_optimizer: Optional[DatabaseQueryOptimizer] = None
        self.batch_processor = AsyncIOBatchProcessor()
        self._initialized = False

    def init_database(
        self, dsn: str, min_connections: int = 5, max_connections: int = 20
    ):
        """
        初始化数据库连接

        Args:
            dsn: 数据库连接字符串
            min_connections: 最小连接数
            max_connections: 最大连接数
        """

        async def _create_pool():
            pool = await asyncpg.create_pool(
                dsn,
                min_size=min_connections,
                max_size=max_connections,
                command_timeout=60,
            )
            return pool

        # 在事件循环中创建连接池
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，在新线程中创建
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _create_pool())
                    pool = future.result()
            else:
                pool = loop.run_until_complete(_create_pool())

            self.query_optimizer = DatabaseQueryOptimizer(pool)
            self._initialized = True
            logger.info("数据库连接池初始化成功")

        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            raise

    def optimize_file_operations(self, operations: List[Dict[str, Any]]) -> List[Any]:
        """
        优化文件操作

        Args:
            operations: 操作列表

        Returns:
            处理结果
        """
        results = []

        def sync_operation(op: Dict[str, Any]):
            op_type = op.get("type")

            if op_type == "read_csv":
                import pandas as pd

                return pd.read_csv(
                    op["file_path"], chunksize=op.get("chunksize", 10000)
                )
            elif op_type == "write_csv":
                import pandas as pd

                df = pd.DataFrame(op["data"])
                df.to_csv(op["file_path"], index=False)
                return True
            else:
                raise ValueError(f"不支持的操作类型: {op_type}")

        # 并行执行操作
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(sync_operation, op): i
                for i, op in enumerate(operations)
            }

            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"操作执行失败: {e}")
                    results.append(None)

        return results

    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        stats = {
            "database_optimization": None,
            "batch_processing": {
                "max_workers": self.batch_processor.max_workers,
                "chunk_size": self.batch_processor.chunk_size,
                "max_memory_mb": self.batch_processor.max_memory_mb,
            },
        }

        if self.query_optimizer:
            stats["database_optimization"] = (
                self.query_optimizer.analyze_query_performance()
            )

        return stats

    def cleanup(self):
        """清理资源"""
        if self.query_optimizer:
            # 关闭数据库连接池
            # 注意：asyncpg的pool没有close方法，需要使用terminate
            pass

        self._executor = None


# 便捷函数
def create_db_pool(dsn: str) -> "asyncpg.Pool":
    """创建数据库连接池"""

    async def _create():
        return await asyncpg.create_pool(
            dsn, min_size=5, max_connection=20, command_timeout=60
        )

    return asyncio.run(_create())


def batch_process(
    data: List[Any], batch_size: int, processor: Callable[[List[Any]], Any]
) -> List[Any]:
    """
    批量处理数据

    Args:
        data: 数据列表
        batch_size: 批次大小
        processor: 处理函数

    Returns:
        处理结果
    """
    results = []
    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        result = processor(batch)
        results.append(result)
    return results


def profile_io(func: Callable):
    """I / O性能分析装饰器"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        execution_time = time.perf_counter() - start_time

        logger.info(
            "I / O操作性能统计:\n"
            f"  函数: {func.__name__}\n"
            f"  执行时间: {execution_time:.4f}秒\n"
        )
        return result

    return wrapper
