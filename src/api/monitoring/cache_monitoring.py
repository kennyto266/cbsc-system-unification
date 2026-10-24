"""
缓存监控端点
Cache Monitoring Endpoints

提供缓存系统的监控和健康检查端点
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Dict, Any, Optional
import logging
import time
from datetime import datetime, timedelta

from ..services.cache_manager import get_cache_manager
from ...monitoring.cache_metrics import get_metrics_collector, get_metrics_export

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/monitoring/cache", tags=["cache-monitoring"])


# ============================================================================
# 基础监控端点 (Basic Monitoring Endpoints)
# ============================================================================

@router.get("/health")
async def cache_health_check() -> Dict[str, Any]:
    """
    缓存系统健康检查

    返回缓存系统的整体健康状态，包括：
    - Redis连接状态
    - 内存缓存状态
    - 错误率
    - 响应时间
    """
    try:
        cache_manager = get_cache_manager()
        cache_info = cache_manager.get_cache_info()

        # 获取指标收集器
        metrics_collector = get_metrics_collector()
        metrics_collector.update_metrics()

        # 计算健康状态
        health_status = "healthy"
        issues = []

        # 检查Redis连接
        if not cache_info.get("redis_connected", False) and cache_info.get("redis_enabled", False):
            health_status = "degraded"
            issues.append("Redis连接失败")

        # 检查内存使用
        total_metrics = cache_info.get("total_metrics", {})
        overall_hit_rate = total_metrics.get("overall_hit_rate", 0.0)

        if overall_hit_rate < 0.5:  # 命中率低于50%
            health_status = "degraded" if health_status == "healthy" else "unhealthy"
            issues.append(f"缓存命中率过低: {overall_hit_rate:.1%}")

        # 检查错误率
        total_errors = sum(m.get_errors + m.set_errors for m in cache_manager.get_metrics().values())
        total_operations = sum(m.hits + m.misses + m.sets for m in cache_manager.get_metrics().values())

        if total_operations > 0:
            error_rate = total_errors / total_operations
            if error_rate > 0.05:  # 错误率超过5%
                health_status = "unhealthy"
                issues.append(f"错误率过高: {error_rate:.1%}")

        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "redis_connected": cache_info.get("redis_connected", False),
                "redis_enabled": cache_info.get("redis_enabled", False),
                "overall_hit_rate": overall_hit_rate,
                "error_rate": error_rate if total_operations > 0 else 0.0
            },
            "issues": issues,
            "cache_info": cache_info
        }

    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/metrics")
async def get_cache_metrics() -> PlainTextResponse:
    """
    获取Prometheus格式的缓存指标

    返回符合Prometheus格式的指标数据，可以用于Grafana等监控工具
    """
    try:
        # 获取指标导出
        metrics_data = get_metrics_export()

        return PlainTextResponse(
            content=metrics_data,
            media_type="text/plain; version=0.0.4"
        )

    except Exception as e:
        logger.error(f"Failed to get cache metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取缓存指标失败: {str(e)}"
        )


@router.get("/stats")
async def get_cache_statistics() -> Dict[str, Any]:
    """
    获取缓存统计信息

    返回详细的缓存统计信息，包括：
    - 各策略的命中率和性能
    - 内存使用情况
    - Redis状态
    - 热点键分析
    """
    try:
        cache_manager = get_cache_manager()
        metrics_collector = get_metrics_collector()

        # 更新指标
        metrics_collector.update_metrics()

        # 获取基础信息
        cache_info = cache_manager.get_cache_info()

        # 获取各策略详细指标
        strategies_metrics = {}
        strategies = cache_manager.list_strategies()

        for strategy_name, strategy in strategies.items():
            metrics = cache_manager.get_metrics(strategy_name)

            strategies_metrics[strategy_name] = {
                "hits": metrics.hits,
                "misses": metrics.misses,
                "sets": metrics.sets,
                "deletes": metrics.deletes,
                "hit_rate": metrics.hit_rate,
                "avg_get_time": metrics.avg_get_time,
                "avg_set_time": metrics.avg_set_time,
                "get_errors": metrics.get_errors,
                "set_errors": metrics.set_errors,
                "cache_level": strategy.cache_level.value,
                "ttl_seconds": strategy.ttl_seconds,
                "max_memory_items": strategy.max_memory_items,
                "enable_compression": strategy.enable_compression
            }

        # 添加内存缓存信息
        memory_caches = {}
        for name, cache in cache_info.get("memory_caches", {}).items():
            memory_caches[name] = {
                "size": cache["size"],
                "max_size": cache["max_size"],
                "utilization": cache["size"] / cache["max_size"] if cache["max_size"] > 0 else 0.0
            }

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall": cache_info.get("total_metrics", {}),
            "strategies": strategies_metrics,
            "memory_caches": memory_caches,
            "redis": {
                "enabled": cache_info.get("redis_enabled", False),
                "connected": cache_info.get("redis_connected", False),
                "info": cache_info.get("redis_info", {})
            }
        }

    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取缓存统计失败: {str(e)}"
        )


@router.get("/performance")
async def get_cache_performance(
    strategy: Optional[str] = Query(None, description="策略名称过滤"),
    time_range: str = Query("1h", description="时间范围: 1h, 6h, 24h, 7d")
) -> Dict[str, Any]:
    """
    获取缓存性能分析

    Args:
        strategy: 可选的策略名称过滤
        time_range: 时间范围

    返回缓存性能分析数据，包括：
    - 响应时间趋势
    - 命中率变化
    - 吞吐量统计
    - 性能瓶颈分析
    """
    try:
        cache_manager = get_cache_manager()
        metrics_collector = get_metrics_collector()

        # 解析时间范围
        time_mapping = {
            "1h": 3600,
            "6h": 21600,
            "24h": 86400,
            "7d": 604800
        }

        seconds = time_mapping.get(time_range, 3600)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(seconds=seconds)

        # 获取策略数据
        strategies = cache_manager.list_strategies()
        if strategy:
            strategies = {strategy: strategies.get(strategy)} if strategy in strategies else {}

        performance_data = {}

        for strategy_name, strategy_config in strategies.items():
            metrics = cache_manager.get_metrics(strategy_name)

            # 计算性能指标
            total_operations = metrics.hits + metrics.misses + metrics.sets
            throughput = total_operations / seconds if seconds > 0 else 0

            performance_data[strategy_name] = {
                "throughput_ops_per_second": throughput,
                "hit_rate": metrics.hit_rate,
                "avg_response_time_ms": (metrics.avg_get_time + metrics.avg_set_time) * 1000,
                "error_rate": (metrics.get_errors + metrics.set_errors) / total_operations if total_operations > 0 else 0,
                "cache_level": strategy_config.cache_level.value,
                "operations": {
                    "hits": metrics.hits,
                    "misses": metrics.misses,
                    "sets": metrics.sets,
                    "deletes": metrics.deletes
                },
                "timing": {
                    "avg_get_time_ms": metrics.avg_get_time * 1000,
                    "avg_set_time_ms": metrics.avg_set_time * 1000,
                    "total_get_time_s": metrics.total_get_time,
                    "total_set_time_s": metrics.total_set_time
                }
            }

        # 生成性能分析
        analysis = {
            "overall_health": "good",
            "bottlenecks": [],
            "recommendations": []
        }

        # 分析性能瓶颈
        for strategy_name, data in performance_data.items():
            if data["hit_rate"] < 0.6:
                analysis["bottlenecks"].append(f"{strategy_name}: 命中率过低")
                analysis["recommendations"].append(f"检查{strategy_name}的缓存策略和数据访问模式")

            if data["avg_response_time_ms"] > 100:
                analysis["bottlenecks"].append(f"{strategy_name}: 响应时间过长")
                analysis["recommendations"].append(f"优化{strategy_name}的数据序列化或网络连接")

            if data["error_rate"] > 0.01:
                analysis["bottlenecks"].append(f"{strategy_name}: 错误率过高")
                analysis["recommendations"].append(f"检查{strategy_name}的缓存配置和网络稳定性")

        if analysis["bottlenecks"]:
            analysis["overall_health"] = "warning" if len(analysis["bottlenecks"]) <= 2 else "critical"

        return {
            "time_range": time_range,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_seconds": seconds
            },
            "performance": performance_data,
            "analysis": analysis,
            "summary": {
                "total_strategies": len(performance_data),
                "avg_hit_rate": sum(data["hit_rate"] for data in performance_data.values()) / len(performance_data) if performance_data else 0,
                "total_throughput": sum(data["throughput_ops_per_second"] for data in performance_data.values()),
                "avg_response_time_ms": sum(data["avg_response_time_ms"] for data in performance_data.values()) / len(performance_data) if performance_data else 0
            }
        }

    except Exception as e:
        logger.error(f"Failed to get cache performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取缓存性能分析失败: {str(e)}"
        )


# ============================================================================
# 缓存管理端点 (Cache Management Endpoints)
# ============================================================================

@router.post("/clear")
async def clear_cache(
    strategy: Optional[str] = Query(None, description="要清理的策略名称，不指定则清理所有"),
    pattern: Optional[str] = Query(None, description="要清理的键模式")
) -> Dict[str, Any]:
    """
    清理缓存

    Args:
        strategy: 可选的策略名称
        pattern: 可选的键模式（支持通配符）

    清理指定的缓存数据，支持策略级别和模式级别的清理
    """
    try:
        cache_manager = get_cache_manager()

        cleared_items = 0
        cleared_strategies = []

        if strategy:
            # 清理特定策略
            if pattern:
                cleared_items = cache_manager.clear_pattern(strategy, pattern)
                cleared_strategies.append(f"{strategy}:{pattern}")
            else:
                # 清理整个策略的缓存（需要获取所有键）
                # 这里简化处理，实际可能需要遍历所有键
                cleared_items = cache_manager.clear_pattern(strategy, "*")
                cleared_strategies.append(strategy)
        else:
            # 清理所有策略
            strategies = cache_manager.list_strategies()
            for strategy_name in strategies.keys():
                items_cleared = cache_manager.clear_pattern(strategy_name, "*")
                if items_cleared > 0:
                    cleared_items += items_cleared
                    cleared_strategies.append(strategy_name)

        return {
            "success": True,
            "cleared_items": cleared_items,
            "cleared_strategies": cleared_strategies,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"成功清理 {cleared_items} 个缓存项"
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"清理缓存失败: {str(e)}"
        )


@router.post("/warmup")
async def warmup_cache(
    strategy: str = Query(..., description="要预热的策略名称"),
    keys: list[str] = Query(..., description="要预热的键列表")
) -> Dict[str, Any]:
    """
    缓存预热

    Args:
        strategy: 策略名称
        keys: 要预热的键列表

    将指定的键预加载到缓存中，提高后续访问性能
    """
    try:
        cache_manager = get_cache_manager()

        # 这里需要实现数据加载逻辑
        # 简化实现，实际应该根据策略类型调用相应的数据加载函数
        def mock_data_loader(keys_to_load):
            """模拟数据加载函数"""
            return {key: f"preloaded_data_for_{key}" for key in keys_to_load}

        # 执行预热
        success_count = cache_manager.warm_up(strategy, mock_data_loader, keys)

        return {
            "success": True,
            "strategy": strategy,
            "requested_keys": len(keys),
            "success_count": success_count,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"成功预热 {success_count}/{len(keys)} 个键"
        }

    except Exception as e:
        logger.error(f"Failed to warmup cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"缓存预热失败: {str(e)}"
        )


@router.get("/export")
async def export_cache_data(
    strategy: str = Query(..., description="要导出的策略名称")
) -> Dict[str, Any]:
    """
    导出缓存数据

    Args:
        strategy: 策略名称

    导出指定策略的缓存数据，用于备份或迁移
    """
    try:
        cache_manager = get_cache_manager()

        # 生成导出文件名
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"cache_export_{strategy}_{timestamp}.pkl"

        # 导出缓存数据
        success = cache_manager.export_cache(strategy, filename)

        if success:
            return {
                "success": True,
                "strategy": strategy,
                "filename": filename,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"缓存数据已导出到 {filename}"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="导出缓存数据失败"
            )

    except Exception as e:
        logger.error(f"Failed to export cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"导出缓存数据失败: {str(e)}"
        )