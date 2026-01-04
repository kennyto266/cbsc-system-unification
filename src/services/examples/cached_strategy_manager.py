"""
缓存的策略管理器示例
Cached Strategy Manager Example

展示如何在现有的策略管理器中集成新的缓存系统。
"""

import logging
from typing import Dict, List, Optional, Any

from ..cache_integration import StrategyManagerCacheMixin, cached_method, invalidate_cache_method
from ..cache_decorators import cached

logger = logging.getLogger(__name__)


class CachedStrategyManager(StrategyManagerCacheMixin):
    """
    带缓存的策略管理器示例

    继承自 StrategyManagerCacheMixin 以获得缓存功能。
    """

    def __init__(self):
        # 初始化缓存混入
        super().__init__()
        logger.info("CachedStrategyManager initialized with cache support")

    # 基础缓存操作示例
    @cached_method("strategy", ttl=300, key_prefix="get_strategy")
    def get_strategy(self, strategy_id: str) -> Optional[Dict]:
        """
        获取策略详情（带缓存）

        缓存键格式：get_strategy:{strategy_id}
        TTL: 300秒（5分钟）
        """
        logger.info(f"Loading strategy from database: {strategy_id}")
        # 模拟数据库查询
        return self._load_strategy_from_db(strategy_id)

    @invalidate_cache_method("strategy", "strategy_*")
    def update_strategy(self, strategy_id: str, strategy_data: Dict) -> bool:
        """
        更新策略（自动失效缓存）

        更新后自动清除所有与该策略相关的缓存。
        """
        logger.info(f"Updating strategy in database: {strategy_id}")
        # 模拟数据库更新
        success = self._update_strategy_in_db(strategy_id, strategy_data)

        if success:
            # 缓存会自动失效（通过装饰器）
            logger.info(f"Strategy updated and cache invalidated: {strategy_id}")

        return success

    # 使用缓存混入方法的示例
    def get_strategy_with_performance(self, strategy_id: str) -> Optional[Dict]:
        """
        获取策略及其性能数据（使用缓存混入）

        展示如何使用混入提供的专用缓存方法。
        """
        # 获取策略基础信息
        strategy = self.get_strategy_cache(strategy_id)
        if not strategy:
            # 如果缓存中没有，加载并缓存
            strategy = self._load_strategy_from_db(strategy_id)
            if strategy:
                self.set_strategy_cache(strategy_id, strategy, ttl=300)

        # 获取性能数据
        performance = self.get_strategy_performance_cache(strategy_id)
        if not performance:
            performance = self._calculate_performance(strategy_id)
            if performance:
                self.set_strategy_performance_cache(strategy_id, performance, ttl=60)

        # 合并数据
        if strategy and performance:
            result = strategy.copy()
            result["performance"] = performance
            return result

        return None

    # 用户相关缓存示例
    def get_user_strategies(self, user_id: int) -> List[Dict]:
        """
        获取用户的策略列表（带缓存）
        """
        # 尝试从缓存获取
        cached_list = self.get_user_strategy_list_cache(user_id)
        if cached_list:
            logger.info(f"User strategies cache hit: user_id={user_id}")
            return cached_list

        # 缓存未命中，从数据库加载
        logger.info(f"Loading user strategies from database: user_id={user_id}")
        strategies = self._load_user_strategies_from_db(user_id)

        # 缓存结果
        self.set_user_strategy_list_cache(user_id, strategies, ttl=120)

        return strategies

    # 批量操作示例
    def batch_get_strategies(self, strategy_ids: List[str]) -> Dict[str, Optional[Dict]]:
        """
        批量获取策略（优化缓存使用）

        先批量检查缓存，只加载缓存中没有的策略。
        """
        from ..cache_integration import BatchCacheHelper

        # 批量检查缓存
        cached_strategies = BatchCacheHelper.batch_get_strategies(strategy_ids)

        # 找出需要加载的策略
        to_load = [
            sid for sid, data in cached_strategies.items()
            if data is None
        ]

        # 批量加载缺失的策略
        if to_load:
            logger.info(f"Loading {len(to_load)} strategies from database")
            loaded_strategies = {}
            for sid in to_load:
                strategy = self._load_strategy_from_db(sid)
                loaded_strategies[sid] = strategy
                # 缓存加载的策略
                if strategy:
                    self.set_strategy_cache(sid, strategy, ttl=300)

            # 合并结果
            result = cached_strategies.copy()
            result.update(loaded_strategies)
            return result

        return cached_strategies

    # 市场数据缓存示例
    def get_market_data_for_strategy(self, strategy_id: str, symbol: str = None) -> Optional[Dict]:
        """
        获取策略相关的市场数据（带缓存）

        市场数据变化频繁，使用较短的TTL。
        """
        # 从策略获取需要的交易对
        strategy = self.get_strategy_cache(strategy_id)
        if not strategy:
            strategy = self.get_strategy(strategy_id)

        if not strategy or not strategy.get("symbols"):
            return None

        # 获取每个交易对的数据
        market_data = {}
        for s in strategy["symbols"]:
            data = self.get_market_data_cache(s, "1d")
            if not data:
                # 缓存未命中，从外部API加载
                data = self._fetch_market_data_from_api(s)
                # 缓存5秒
                if data:
                    self.set_market_data_cache(s, "1d", data, ttl=5)

            if data:
                market_data[s] = data

        return market_data if market_data else None

    # 用户仪表板缓存示例
    def get_user_dashboard(self, user_id: int) -> Optional[Dict]:
        """
        获取用户仪表板数据（聚合缓存）

        仪表板数据聚合自多个缓存源。
        """
        # 尝试从缓存获取完整的仪表板
        dashboard = self.get_user_dashboard_cache(user_id)
        if dashboard:
            return dashboard

        # 构建仪表板数据
        dashboard = {
            "user_id": user_id,
            "strategies": self.get_user_strategies(user_id),
            "performance_summary": self._get_user_performance_summary(user_id),
            "recent_activity": self._get_user_recent_activity(user_id),
            "market_overview": self._get_market_overview()
        }

        # 缓存30秒
        self.set_user_dashboard_cache(user_id, dashboard, ttl=30)

        return dashboard

    # 缓存清理示例
    def cleanup_user_data(self, user_id: int) -> int:
        """
        清理用户相关的所有缓存

        当用户删除或大量数据更新时调用。
        """
        logger.info(f"Cleaning up cache for user: {user_id}")

        # 清理用户策略缓存
        count = self.invalidate_user_cache(user_id)

        # 清理相关的仪表板缓存
        count += self.cache_clear_pattern("user", f"dashboard_{user_id}")

        # 清理用户偏好设置
        count += self.cache_delete("user", f"preferences_{user_id}")

        logger.info(f"Cleaned up {count} cache entries for user: {user_id}")
        return count

    # 以下是模拟的私有方法
    def _load_strategy_from_db(self, strategy_id: str) -> Optional[Dict]:
        """模拟从数据库加载策略"""
        # 实际实现会查询数据库
        return {
            "id": strategy_id,
            "name": f"Strategy {strategy_id}",
            "symbols": ["AAPL", "GOOGL"],
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z"
        }

    def _update_strategy_in_db(self, strategy_id: str, data: Dict) -> bool:
        """模拟更新数据库中的策略"""
        # 实际实现会更新数据库
        return True

    def _load_user_strategies_from_db(self, user_id: int) -> List[Dict]:
        """模拟从数据库加载用户策略列表"""
        # 实际实现会查询数据库
        return [
            {"id": "strategy1", "name": "Strategy 1"},
            {"id": "strategy2", "name": "Strategy 2"}
        ]

    def _calculate_performance(self, strategy_id: str) -> Optional[Dict]:
        """模拟计算策略性能"""
        # 实际实现会执行复杂的计算
        return {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.05
        }

    def _fetch_market_data_from_api(self, symbol: str) -> Optional[Dict]:
        """模拟从外部API获取市场数据"""
        # 实际实现会调用外部API
        return {
            "symbol": symbol,
            "price": 150.0,
            "change": 0.01
        }

    def _get_user_performance_summary(self, user_id: int) -> Dict:
        """获取用户性能摘要"""
        return {"total_return": 0.25, "active_strategies": 5}

    def _get_user_recent_activity(self, user_id: int) -> List[Dict]:
        """获取用户最近活动"""
        return [
            {"type": "strategy_created", "timestamp": "2024-01-01T10:00:00Z"},
            {"type": "strategy_updated", "timestamp": "2024-01-01T09:00:00Z"}
        ]

    def _get_market_overview(self) -> Dict:
        """获取市场概览"""
        return {"market_status": "open", "major_indices": {"SPY": "+0.5%"}}


# 使用示例装饰器的独立函数
@cached("config", ttl=600)  # 缓存10分钟
def get_global_config() -> Dict:
    """
    获取全局配置（带缓存）

    全局配置相对稳定，可以长时间缓存。
    """
    # 模拟加载配置
    return {
        "max_strategies_per_user": 10,
        "default_strategy_params": {...},
        "supported_exchanges": ["NYSE", "NASDAQ"]
    }


@cached("api_stats", ttl=3600)  # 缓存1小时
def get_api_statistics() -> Dict:
    """
    获取API统计信息（带缓存）

    统计信息不需要实时性，可以长时间缓存。
    """
    # 模拟获取统计信息
    return {
        "total_requests": 1000000,
        "active_users": 5000,
        "error_rate": 0.001
    }


# 使用示例
if __name__ == "__main__":
    # 初始化缓存管理器
    from ..cache_manager import initialize_cache_manager
    initialize_cache_manager(redis_host="localhost", redis_port=6379)

    # 创建缓存的策略管理器
    manager = CachedStrategyManager()

    # 使用缓存功能
    strategy = manager.get_strategy("strategy123")
    print(f"Strategy: {strategy}")

    # 获取用户策略列表
    user_strategies = manager.get_user_strategies(1001)
    print(f"User strategies: {len(user_strategies)} strategies")

    # 批量获取策略
    batch_strategies = manager.batch_get_strategies(["s1", "s2", "s3"])
    print(f"Batch retrieved: {len(batch_strategies)} strategies")