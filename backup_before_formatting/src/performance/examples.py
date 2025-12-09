"""
性能优化模块使用示例

展示如何使用各种性能优化功能：
- 性能分析
- 缓存系统
- I / O优化
- 懒加载
- 连接池
"""

import asyncio
import random
import time
from pathlib import Path
from typing import Dict, List

from .cache_layer import CacheManager, MultiLevelCache, cached, get_default_cache
from .connection_pool import (
    ConnectionManager,
    DatabaseConnectionPool,
    HTTPConnectionPool,
    PoolConfig,
    create_database_pool,
    create_http_pool,
)
from .io_optimizer import AsyncIOBatchProcessor, DatabaseQueryOptimizer, IOOptimizer
from .lazy_loader import (
    DataFrameLazyLoader,
    LazyLoader,
    MemoryManagedLoader,
    lazy_load,
    memory_efficient,
)

# 导入性能优化模块
from .profiler import Profiler, profile


def example_performance_profiler():
    """性能分析器使用示例"""
    print("\n=== 性能分析器示例 ===\n")

    profiler = Profiler(output_dir="performance_reports")

    # 示例1: 分析函数性能
    def expensive_calculation(n: int) -> int:
        """模拟耗时计算"""
        time.sleep(0.1)
        return sum(range(n))

    result = profiler.profile_function(
        expensive_calculation, n=10000, profile_name="expensive_calculation_test"
    )
    print(f"计算结果: {result}")

    # 示例2: 使用上下文管理器
    with profiler.profile_block("data_processing_block"):
        data = [random.randint(1, 100) for _ in range(10000)]
        processed = [x * 2 for x in data]
        time.sleep(0.1)  # 模拟处理时间

    # 示例3: 基准测试
    benchmark = profiler.benchmark_algorithm(
        expensive_calculation, iterations=100, n=5000
    )
    print(f"\n基准测试结果: {benchmark}")

    # 示例4: 生成报告
    report = profiler.generate_report()
    print(f"\n性能报告:\n{report}")

    # 示例5: 保存报告
    report_file = profiler.save_report()
    print(f"\n报告已保存到: {report_file}")


def example_cache_system():
    """缓存系统使用示例"""
    print("\n=== 缓存系统示例 ===\n")

    # 示例1: 使用默认缓存
    cache = get_default_cache(
        "example_cache", config={"l1_size": 64, "l2_size": 512, "l2_ttl": 3600}
    )

    # 缓存数据
    cache.put("key1", "value1")
    cache.put("key2", "value2")

    # 获取缓存
    value = cache.get("key1")
    print(f"从缓存获取: key1 = {value}")

    # 统计信息
    stats = cache.get_stats()
    print(f"\n缓存统计: {stats}")

    # 示例2: 使用装饰器
    @cached(cache, cache_name="example_cache")
    def expensive_function(x: int, y: int) -> int:
        """模拟耗时函数"""
        time.sleep(0.2)
        return x * y + random.randint(1, 100)

    # 第一次调用（未缓存）
    start = time.time()
    result1 = expensive_function(10, 20)
    time1 = time.time() - start
    print(f"\n第一次调用结果: {result1}, 耗时: {time1:.3f}s")

    # 第二次调用（已缓存）
    start = time.time()
    result2 = expensive_function(10, 20)
    time2 = time.time() - start
    print(f"第二次调用结果: {result2}, 耗时: {time2:.3f}s")

    # 示例3: 多级缓存
    multi_cache = MultiLevelCache(
        l1_size=32,
        l2_size=256,
        l2_ttl=1800,
        enable_persistence=True,
        persist_file="cache_data.json",
    )

    # 存储数据
    multi_cache.put("data1", {"name": "test", "value": 123})
    multi_cache.put("data2", "large_data" * 1000)  # 大数据

    # 获取数据（自动从L1 / L2 / L3查找）
    data1 = multi_cache.get("data1")
    data2 = multi_cache.get("data2")

    print(f"\n多级缓存数据: {data1}")
    print(f"多级缓存统计: {multi_cache.get_stats()}")


def example_io_optimizer():
    """I / O优化器使用示例"""
    print("\n=== I / O优化器示例 ===\n")

    # 创建测试数据
    test_data = [
        {"id": i, "name": f"User{i}", "value": random.randint(1, 100)}
        for i in range(10000)
    ]

    # 示例1: 批量处理
    def process_batch(batch: List[Dict]) -> List[Dict]:
        """模拟批处理"""
        for item in batch:
            item["processed"] = True
            item["timestamp"] = time.time()
        return batch

    from .io_optimizer import batch_process

    batch_size = 1000

    start = time.time()
    results = batch_process(test_data, batch_size, process_batch)
    processing_time = time.time() - start

    print(f"批处理完成: {len(results)} 个批次")
    print(f"处理时间: {processing_time:.3f}s")

    # 示例2: 异步文件I / O
    async def async_file_io_example():
        processor = AsyncIOBatchProcessor(max_workers=4, chunk_size=5000)

        # 创建测试文件
        test_file = Path("test_data.csv")
        test_file.write_text(
            "id,name,value\n"
            + "\n".join(
                f"{item['id']},{item['name']},{item['value']}"
                for item in test_data[:1000]
            )
        )

        # 异步读取和处理
        chunk_count = 0
        async for chunk in processor.read_csv_async(test_file):
            chunk_count += 1
            if chunk_count <= 2:
                print(f"  读取块 {chunk_count}: {len(chunk)} 行")

        print(f"\n异步文件I / O完成: 读取 {chunk_count} 个数据块")

    # 运行异步示例
    asyncio.run(async_file_io_example())


def example_lazy_loader():
    """懒加载系统使用示例"""
    print("\n=== 懒加载系统示例 ===\n")

    # 示例1: 简单懒加载
    def load_heavy_data():
        """模拟加载大量数据"""
        print("  [懒加载] 正在加载大量数据...")
        time.sleep(1)  # 模拟加载时间
        return [random.randint(1, 100) for _ in range(10000)]

    lazy_data = LazyLoader(load_heavy_data)

    print("创建懒加载器（未实际加载）")
    print(f"是否已加载: {lazy_data.is_loaded()}")

    print("\n调用 load() 方法加载数据...")
    data = lazy_data.load()
    print(f"数据长度: {len(data)}")
    print(f"是否已加载: {lazy_data.is_loaded()}")

    # 示例2: 使用装饰器
    @lazy_load()
    def get_configuration():
        """获取配置（模拟）"""
        print("  [装饰器懒加载] 加载配置...")
        time.sleep(0.5)
        return {
            "database": "postgresql://localhost / db",
            "cache_ttl": 3600,
            "max_connections": 20,
        }

    print("\n使用@lazy_load装饰器:")
    config1 = get_configuration()
    print(f"配置: {config1}")

    print("再次调用（从缓存获取）:")
    config2 = get_configuration()
    print(f"配置: {config2}")

    # 示例3: DataFrame懒加载
    print("\nDataFrame懒加载示例:")
    try:
        import pandas as pd

        # 创建测试CSV文件
        csv_file = Path("test_df.csv")
        df = pd.DataFrame(
            {
                "A": [random.randint(1, 100) for _ in range(5000)],
                "B": [random.random() for _ in range(5000)],
                "C": [f"Item_{i}" for i in range(5000)],
            }
        )
        df.to_csv(csv_file, index=False)

        # 使用懒加载器
        lazy_df = DataFrameLazyLoader(csv_file, chunk_size=1000)  # 分块加载

        print(f"DataFrame元数据: {lazy_df.get_metadata()}")
        df_data = lazy_df.load()
        print(f"DataFrame形状: {df_data.shape}")
        print(f"内存使用: {lazy_df.get_memory_usage():.2f} MB")

    except ImportError:
        print("  跳过DataFrame示例（需要安装pandas）")

    # 示例4: 内存管理加载器
    print("\n内存管理加载器示例:")
    memory_loader = MemoryManagedLoader(max_memory_mb=100, gc_trigger_threshold=0.8)

    # 注册数据加载器
    data_loader = LazyLoader(
        lambda: [random.randint(1, 100) for _ in range(1000)],
        memory_manager=memory_loader.memory_manager,
    )
    memory_loader.register_loader(data_loader)

    # 获取统计信息
    print(f"内存统计: {memory_loader.get_memory_stats()}")


def example_connection_pool():
    """连接池使用示例"""
    print("\n=== 连接池系统示例 ===\n")

    # 示例1: HTTP连接池
    async def http_pool_example():
        print("HTTP连接池示例:")

        # 创建HTTP连接池
        http_pool = create_http_pool(
            name="api_pool",
            base_url="https://httpbin.org",
            config=PoolConfig(min_size=5, max_size=10, connection_timeout=5.0),
        )

        # 初始化连接池
        await http_pool.initialize()

        # 发起请求
        try:
            async with http_pool.acquire() as conn:
                response = await conn.request("GET", "/get")
                print(f"  HTTP状态码: {response.status}")
        except Exception as e:
            print(f"  HTTP请求错误: {e}")

        # 关闭连接池
        await http_pool.close()

    # 示例2: 数据库连接池（模拟）
    def database_pool_example():
        print("\n数据库连接池示例:")

        # 注意：这里只是演示用法，需要实际的PostgreSQL数据库
        # db_pool = create_database_pool(
        #     name="db_pool",
        #     dsn="postgresql://user:password@localhost / dbname",
        #     config=PoolConfig(min_size=5, max_size=20)
        # )

        print("  数据库连接池已创建（需要实际数据库连接）")

    # 运行示例
    asyncio.run(http_pool_example())
    database_pool_example()

    # 示例3: 连接管理器
    print("\n连接管理器示例:")
    manager = ConnectionManager()

    # 创建多个连接池
    http_pool = manager.create_http_pool("api1", "https://api1.example.com")
    http_pool2 = manager.create_http_pool("api2", "https://api2.example.com")

    print(f"  已创建 {len(manager.get_all_pools())} 个连接池")
    print(f"  连接池列表: {list(manager.get_all_pools().keys())}")


def example_comprehensive():
    """综合示例"""
    print("\n=== 综合性能优化示例 ===\n")

    # 创建性能监控器
    from .profiler import PerformanceMonitor

    monitor = PerformanceMonitor()
    monitor.start()

    # 使用缓存
    cache = get_default_cache("comprehensive")
    cache.put("key", "value")

    # 使用懒加载
    @lazy_load()
    def get_data():
        time.sleep(0.1)
        return "data"

    data = get_data()

    # 使用I / O优化
    from .io_optimizer import batch_process

    test_list = list(range(1000))
    results = batch_process(test_list, 100, lambda x: [i * 2 for i in x])

    # 获取监控结果
    metrics = monitor.stop()
    print(f"性能监控结果: {metrics}")

    print("\n=== 优化建议 ===")
    print("1. 使用性能分析器识别瓶颈")
    print("2. 使用缓存减少重复计算")
    print("3. 使用懒加载延迟加载大数据")
    print("4. 使用连接池复用连接")
    print("5. 使用批量操作减少I / O次数")
    print("6. 使用异步I / O提高并发性能")


if __name__ == "__main__":
    # 运行所有示例
    try:
        example_performance_profiler()
    except Exception as e:
        print(f"性能分析示例错误: {e}")

    try:
        example_cache_system()
    except Exception as e:
        print(f"缓存系统示例错误: {e}")

    try:
        example_io_optimizer()
    except Exception as e:
        print(f"I / O优化器示例错误: {e}")

    try:
        example_lazy_loader()
    except Exception as e:
        print(f"懒加载系统示例错误: {e}")

    try:
        example_connection_pool()
    except Exception as e:
        print(f"连接池示例错误: {e}")

    try:
        example_comprehensive()
    except Exception as e:
        print(f"综合示例错误: {e}")

    print("\n=== 所有示例完成 ===\n")
