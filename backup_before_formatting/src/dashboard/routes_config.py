"""
API路由配置
港股量化交易系統 - 路由管理

集中管理所有API路由的註冊、配置和版本控制。

使用示例:
    from routes_config import register_all_routes
    manager = UnifiedAPIManager()
    manager.create_app()
    register_all_routes(manager.app)
"""

from typing import Any, Dict

from fastapi import APIRouter, FastAPI


# 路由將在註冊時動態導入
def get_router(name: str):
    """獲取路由器實例"""
    if name == "tasks":
        from src.dashboard.api_tasks import router as tasks_router

        return tasks_router
    elif name == "sprints":
        from src.dashboard.api_sprints import router as sprints_router

        return sprints_router
    else:
        raise ValueError(f"未知的路由: {name}")


# 路由配置映射
ROUTES_CONFIG = {
    "tasks": {
        "router_name": "tasks",
        "prefix": "/api / v1 / tasks",
        "tags": ["Tasks"],
        "description": "任務管理相關API",
    },
    "sprints": {
        "router_name": "sprints",
        "prefix": "/api / v1 / sprints",
        "tags": ["Sprints"],
        "description": "Sprint管理相關API",
    },
    # 可以繼續添加其他路由...
    # "agents": {
    #     "router": agents_router,
    #     "prefix": "/api / v1 / agents",
    #     "tags": ["Agents"],
    #     "description": "智能體管理相關API"
    # },
    # "strategies": {
    #     "router": strategies_router,
    #     "prefix": "/api / v1 / strategies",
    #     "tags": ["Strategies"],
    #     "description": "策略管理相關API"
    # },
    # "trading": {
    #     "router": trading_router,
    #     "prefix": "/api / v1 / trading",
    #     "tags": ["Trading"],
    #     "description": "交易相關API"
    # },
    # "risk": {
    #     "router": risk_router,
    #     "prefix": "/api / v1 / risk",
    #     "tags": ["Risk"],
    #     "description": "風險管理相關API"
    # },
    # "backtest": {
    #     "router": backtest_router,
    #     "prefix": "/api / v1 / backtest",
    #     "tags": ["Backtest"],
    #     "description": "回測相關API"
    # },
}

# 版本配置
API_VERSIONS = {
    "v1": {"prefix": "/api / v1", "description": "API版本1"},
    # 可以添加更多版本...
    # "v2": {
    #     "prefix": "/api / v2",
    #     "description": "API版本2"
    # }
}


def register_all_routes(app: FastAPI, version: str = "v1"):
    """
    註冊所有API路由

    Args:
        app: FastAPI應用實例
        version: API版本
    """
    if version not in API_VERSIONS:
        raise ValueError(f"不支持的API版本: {version}")

    version_config = API_VERSIONS[version]
    version_prefix = version_config["prefix"]

    # 註冊版本標籤
    app.openapi_tags = app.openapi_tags or []
    app.openapi_tags.append(
        {"name": version, "description": version_config["description"]}
    )

    # 註冊所有路由
    registered_count = 0
    for route_name, config in ROUTES_CONFIG.items():
        try:
            # 動態獲取路由器
            router = get_router(config["router_name"])
            app.include_router(
                router,
                prefix=f"{version_prefix}{config.get('prefix', '')}",
                tags=config.get("tags", []),
            )
            registered_count += 1
            print(f"✅ 成功註冊路由: {route_name}")
        except Exception as e:
            print(f"❌ 註冊路由失敗: {route_name} - {e}")

    print("\n📊 路由註冊完成:")
    print(f"   總計: {len(ROUTES_CONFIG)} 個路由")
    print(f"   成功: {registered_count} 個")
    print(f"   失敗: {len(ROUTES_CONFIG) - registered_count} 個")


def register_specific_routes(app: FastAPI, route_names: list, version: str = "v1"):
    """
    註冊指定路由

    Args:
        app: FastAPI應用實例
        route_names: 要註冊的路由名稱列表
        version: API版本
    """
    if version not in API_VERSIONS:
        raise ValueError(f"不支持的API版本: {version}")

    version_config = API_VERSIONS[version]
    version_prefix = version_config["prefix"]

    registered_count = 0
    for route_name in route_names:
        if route_name not in ROUTES_CONFIG:
            print(f"⚠️  路由不存在: {route_name}")
            continue

        try:
            config = ROUTES_CONFIG[route_name]
            router = get_router(config["router_name"])
            app.include_router(
                router,
                prefix=f"{version_prefix}{config.get('prefix', '')}",
                tags=config.get("tags", []),
            )
            registered_count += 1
            print(f"✅ 成功註冊路由: {route_name}")
        except Exception as e:
            print(f"❌ 註冊路由失敗: {route_name} - {e}")

    print("\n📊 指定路由註冊完成:")
    print(f"   請求: {len(route_names)} 個路由")
    print(f"   成功: {registered_count} 個")


def get_routes_info() -> Dict[str, Any]:
    """
    獲取所有路由信息

    Returns:
        路由信息字典
    """
    return {
        "total_routes": len(ROUTES_CONFIG),
        "available_routes": list(ROUTES_CONFIG.keys()),
        "route_details": ROUTES_CONFIG,
        "api_versions": list(API_VERSIONS.keys()),
    }


def validate_route_config() -> bool:
    """
    驗證路由配置的有效性

    Returns:
        配置是否有效
    """
    is_valid = True

    for route_name, config in ROUTES_CONFIG.items():
        # 檢查必需的字段
        required_fields = ["router_name", "prefix", "tags"]
        for field in required_fields:
            if field not in config:
                print(f"❌ 路由 {route_name} 缺少必需字段: {field}")
                is_valid = False

        # 嘗試獲取路由器
        try:
            router = get_router(config["router_name"])
            if not isinstance(router, APIRouter):
                print(f"❌ 路由 {route_name} 的router不是有效的APIRouter實例")
                is_valid = False
        except Exception as e:
            print(f"❌ 路由 {route_name} 無法獲取路由器: {e}")
            is_valid = False

    if is_valid:
        print("✅ 路由配置驗證通過")

    return is_valid


if __name__ == "__main__":
    # 測試配置
    print("=" * 60)
    print("路由配置驗證")
    print("=" * 60)

    if validate_route_config():
        print("\n📋 路由信息:")
        info = get_routes_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
    else:
        print("❌ 路由配置驗證失敗!")
