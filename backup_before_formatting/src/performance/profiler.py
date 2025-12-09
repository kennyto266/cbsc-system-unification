"""
性能分析器和慢路径优化工具

提供全面的性能分析功能，包括：
- CPU profiling (cProfile)
- 内存分析
- 函数级性能监控
- 性能报告生成
- 瓶颈识别
"""

import cProfile
import gc
import io
import logging
import pstats
import sys
import threading
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import psutil

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """性能分析结果"""

    function_name: str
    total_calls: int
    cumulative_time: float
    total_time: float
    per_call_avg: float
    cumulative_calls: int
    memory_usage_mb: float
    timestamp: float = field(default_factory=time.time)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.metrics: Dict[str, Any] = {}

    def start(self):
        """开始监控"""
        self.start_time = time.perf_counter()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024

    def stop(self) -> Dict[str, float]:
        """停止监控并返回指标"""
        if self.start_time is None:
            return {}

        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024

        return {
            "execution_time": end_time - self.start_time,
            "memory_delta": end_memory - self.start_memory,
            "peak_memory": end_memory,
        }


class Profiler:
    """性能分析器主类"""

    def __init__(self, output_dir: str = "performance_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.active_profilers: Dict[str, cProfile.Profile] = {}
        self.results: List[ProfileResult] = []
        self.monitor = PerformanceMonitor()

    def profile_function(
        self,
        func: Callable,
        *args,
        kwargs: Optional[Dict] = None,
        profile_name: Optional[str] = None,
        **kwargs_profiler,
    ) -> Any:
        """
        分析单个函数的性能

        Args:
            func: 要分析的函数
            *args: 位置参数
            kwargs: 关键字参数
            profile_name: 分析名称
            **kwargs_profiler: cProfile参数

        Returns:
            函数执行结果
        """
        name = profile_name or f"{func.__module__}.{func.__name__}"
        pr = cProfile.Profile()

        logger.info(f"开始分析函数: {name}")

        # 启动性能监控
        self.monitor.start()

        # 执行分析
        pr.enable()
        try:
            result = func(*args, **(kwargs or {}))
        finally:
            pr.disable()
            self.monitor.stop()

        # 保存分析结果
        self._save_profile_results(pr, name, **kwargs_profiler)

        return result

    def _save_profile_results(
        self,
        profile: cProfile.Profile,
        name: str,
        sort_by: str = "cumulative",
        top_n: int = 20,
        save_stats: bool = True,
        save_graph: bool = False,
    ):
        """保存性能分析结果"""
        try:
            # 创建字符串流来保存统计信息
            s = io.StringIO()
            ps = pstats.Stats(profile, stream=s).sort_stats(sort_by)

            # 获取统计信息
            stats_list = []

            for func, (cc, nc, tt, ct, callers) in ps.stats.items():
                module, filename, line, func_name = (
                    func if len(func) == 4 else (func[0], func[1], func[2], "unknown")
                )
                per_call = ct / nc if nc > 0 else 0

                result = ProfileResult(
                    function_name=f"{func_name} ({filename}:{line})",
                    total_calls=nc,
                    cumulative_time=ct,
                    total_time=tt,
                    per_call_avg=per_call,
                    cumulative_calls=cc,
                    memory_usage_mb=0,  # 需要单独测量
                )
                stats_list.append(result)

            # 排序并保留前N个
            stats_list.sort(key=lambda x: x.cumulative_time, reverse=True)
            self.results.extend(stats_list[:top_n])

            # 保存文本报告
            if save_stats:
                report_file = self.output_dir / f"{name}_{int(time.time())}.prof.txt"
                with open(report_file, "w", encoding="utf - 8") as f:
                    s.seek(0)
                    f.write(s.getvalue())
                logger.info(f"性能报告已保存: {report_file}")

            # 保存pstats二进制
            stats_file = self.output_dir / f"{name}_{int(time.time())}.prof"
            ps.dump_stats(str(stats_file))
            logger.info(f"性能数据已保存: {stats_file}")

        except Exception as e:
            logger.error(f"保存性能分析结果失败: {e}")
            logger.error(traceback.format_exc())

    @contextmanager
    def profile_block(self, block_name: str, detailed: bool = True):
        """
        使用上下文管理器分析代码块

        Args:
            block_name: 代码块名称
            detailed: 是否保存详细统计
        """
        pr = cProfile.Profile()
        pr.enable()
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            yield
        finally:
            pr.disable()
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024

            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory

            logger.info(f"\n=== {block_name} 性能统计 ===")
            logger.info(f"执行时间: {execution_time:.4f} 秒")
            logger.info(f"内存变化: {memory_delta:+.2f} MB")
            logger.info(f"执行时间: {end_memory:.2f} MB")

            if detailed:
                s = io.StringIO()
                ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
                ps.print_stats(15)
                s.seek(0)
                logger.info(f"详细统计:\n{s.getvalue()}")

            # 保存到文件
            if detailed:
                report_file = (
                    self.output_dir / f"{block_name}_{int(time.time())}.prof.txt"
                )
                with open(report_file, "w", encoding="utf - 8") as f:
                    s.seek(0)
                    f.write(s.getvalue())

    def profile_memory(self, func: Callable, *args, **kwargs) -> Dict[str, float]:
        """
        分析函数的内存使用

        Returns:
            内存使用统计
        """
        # 强制垃圾回收
        gc.collect()

        # 获取初始内存
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        # 执行函数
        result = func(*args, **kwargs)

        # 获取执行后内存
        mid_memory = process.memory_info().rss / 1024 / 1024

        # 强制垃圾回收后再检查
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024

        return {
            "initial_memory_mb": initial_memory,
            "mid_memory_mb": mid_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": mid_memory - initial_memory,
            "memory_after_gc_mb": final_memory - initial_memory,
            "result_size_estimate_mb": sys.getsizeof(result) / 1024 / 1024,
        }

    def profile_concurrent(
        self, func: Callable, num_calls: int = 100, num_threads: int = 4, **kwargs
    ) -> Dict[str, Any]:
        """
        分析并发性能

        Args:
            func: 要分析的函数
            num_calls: 总调用次数
            num_threads: 线程数
            **kwargs: 函数参数

        Returns:
            并发性能统计
        """
        import concurrent.futures
        from threading import Lock

        results = []
        lock = Lock()
        exceptions = []

        def worker():
            try:
                result = func(**kwargs)
                with lock:
                    results.append(result)
            except Exception as e:
                with lock:
                    exceptions.append(e)

        start_time = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_calls)]
            concurrent.futures.wait(futures)

        end_time = time.perf_counter()

        return {
            "total_calls": num_calls,
            "successful_calls": len(results),
            "failed_calls": len(exceptions),
            "total_time": end_time - start_time,
            "avg_time_per_call": (end_time - start_time) / num_calls,
            "calls_per_second": num_calls / (end_time - start_time),
            "exceptions": exceptions[:5],  # 只返回前5个异常
        }

    def benchmark_algorithm(
        self, func: Callable, iterations: int = 1000, warmup_runs: int = 10, **kwargs
    ) -> Dict[str, float]:
        """
        算法基准测试

        Args:
            func: 要测试的函数
            iterations: 测试迭代次数
            warmup_runs: 预热运行次数
            **kwargs: 函数参数

        Returns:
            性能基准数据
        """
        # 预热
        for _ in range(warmup_runs):
            func(**kwargs)

        # 正式测试
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func(**kwargs)
            end = time.perf_counter()
            times.append(end - start)

        return {
            "iterations": iterations,
            "warmup_runs": warmup_runs,
            "total_time": sum(times),
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "median_time": sorted(times)[len(times) // 2],
            "times_per_second": iterations / sum(times),
        }

    def get_top_bottlenecks(self, top_n: int = 10) -> List[ProfileResult]:
        """
        获取性能瓶颈（按累计时间排序）

        Args:
            top_n: 返回前N个瓶颈

        Returns:
            性能瓶颈列表
        """
        if not self.results:
            logger.warning("没有性能数据可分析")
            return []

        sorted_results = sorted(
            self.results, key=lambda x: x.cumulative_time, reverse=True
        )

        return sorted_results[:top_n]

    def generate_report(self) -> str:
        """
        生成性能分析报告

        Returns:
            格式化的报告字符串
        """
        if not self.results:
            return "没有可用的性能数据"

        bottlenecks = self.get_top_bottlenecks()

        report = [
            "\n" + "=" * 80,
            "性能分析报告",
            "=" * 80 + "\n",
            f"分析时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"总函数数: {len(self.results)}",
            f"性能瓶颈数: {len(bottlenecks)}\n",
        ]

        report.append("=" * 80)
        report.append("Top 性能瓶颈")
        report.append("=" * 80)

        for i, result in enumerate(bottlenecks, 1):
            report.append(
                f"\n{i}. {result.function_name}\n"
                f"   累计时间: {result.cumulative_time:.6f}s\n"
                f"   调用次数: {result.total_calls}\n"
                f"   单次平均: {result.per_call_avg:.6f}s\n"
                f"   累计调用: {result.cumulative_calls}\n"
            )

        report.append("\n" + "=" * 80)
        report.append("推荐优化建议")
        report.append("=" * 80)

        # 添加优化建议
        for i, result in enumerate(bottlenecks, 1):
            suggestions = self._get_optimization_suggestions(result)
            if suggestions:
                report.append(f"\n{i}. {result.function_name}")
                for suggestion in suggestions:
                    report.append(f"   - {suggestion}")

        return "\n".join(report)

    def _get_optimization_suggestions(self, result: ProfileResult) -> List[str]:
        """
        根据性能结果生成优化建议

        Args:
            result: 性能分析结果

        Returns:
            优化建议列表
        """
        suggestions = []

        # 长时间执行的函数
        if result.cumulative_time > 1.0:
            suggestions.append("考虑使用异步处理或分批处理")
            suggestions.append("检查是否有重复计算，优化算法复杂度")

        # 调用次数过多的函数
        if result.total_calls > 10000:
            suggestions.append("考虑使用缓存减少重复计算")
            suggestions.append("检查是否可以批量处理而不是逐个处理")

        # 单次调用时间过长的函数
        if result.per_call_avg > 0.01:
            suggestions.append("检查I / O操作，考虑使用连接池")
            suggestions.append("考虑使用更高效的数据结构或算法")

        return suggestions

    def save_report(self, filename: Optional[str] = None) -> Path:
        """
        保存性能报告到文件

        Args:
            filename: 自定义文件名

        Returns:
            报告文件路径
        """
        if filename is None:
            filename = f"performance_report_{int(time.time())}.txt"

        report_file = self.output_dir / filename

        with open(report_file, "w", encoding="utf - 8") as f:
            f.write(self.generate_report())

        logger.info(f"性能报告已保存: {report_file}")
        return report_file

    def clear_results(self):
        """清除之前的分析结果"""
        self.results.clear()
        logger.info("已清除性能分析结果")


def profile(
    profile_name: Optional[str] = None, output_dir: str = "performance_reports"
):
    """
    装饰器：自动分析函数性能

    Args:
        profile_name: 分析名称
        output_dir: 输出目录
    """

    def decorator(func: Callable) -> Callable:
        profiler = Profiler(output_dir)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return profiler.profile_function(
                func, *args, kwargs=kwargs, profile_name=profile_name
            )

        return wrapper

    return decorator


# 便捷函数
def quick_profile(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    快速性能分析

    Args:
        func: 要分析的函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        性能统计
    """
    profiler = Profiler()
    memory_stats = profiler.profile_memory(func, *args, **kwargs)
    benchmark = profiler.benchmark_algorithm(func, iterations=100, **kwargs)

    return {"memory": memory_stats, "benchmark": benchmark}
