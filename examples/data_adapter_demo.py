#!/usr/bin/env python3
"""
数据适配器演示脚本

展示黑人RAW DATA数据适配器的各种功能，包括：
- 数据读取和转换
- 数据质量验证
- 缓存机制
- 健康检查
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import date

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_adapters.raw_data_adapter import RawDataAdapter, RawDataAdapterConfig
from src.data_adapters.data_service import DataService
from src.data_adapters.config_manager import DataAdapterConfigManager


async def demo_basic_adapter():
    """演示基础适配器功能"""
    print("=" * 60)
    print("演示1: 基础数据适配器功能")
    print("=" * 60)
    
    # 创建配置（使用示例数据）
    config = RawDataAdapterConfig(
        source_path=str(project_root / "examples"),
        data_directory=str(project_root / "examples"),
        file_pattern="raw_data_sample.csv",
        encoding="utf-8",
        delimiter=",",
        date_column="date",
        symbol_column="symbol",
        price_columns={
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume"
        },
        market_cap_column="market_cap",
        pe_ratio_column="pe_ratio",
        update_frequency=60,
        max_retries=3,
        timeout=30,
        cache_enabled=True,
        cache_ttl=300,
        quality_threshold=0.8
    )
    
    # 创建适配器
    adapter = RawDataAdapter(config)
    
    try:
        # 连接数据源
        print("正在连接数据源...")
        connected = await adapter.connect()
        if not connected:
            print("❌ 连接失败")
            return
        
        print("✅ 连接成功")
        
        # 获取可用股票代码
        print("\n获取可用股票代码...")
        symbols = await adapter.get_available_symbols()
        print(f"找到股票代码: {symbols}")
        
        # 获取市场数据
        if symbols:
            symbol = symbols[0]
            print(f"\n获取 {symbol} 的市场数据...")
            data = await adapter.get_market_data(symbol)
            
            if data:
                print(f"✅ 成功获取 {len(data)} 条记录")
                
                # 显示第一条数据
                first_record = data[0]
                print(f"\n第一条数据详情:")
                print(f"  股票代码: {first_record.symbol}")
                print(f"  日期: {first_record.timestamp}")
                print(f"  开盘价: {first_record.open_price}")
                print(f"  最高价: {first_record.high_price}")
                print(f"  最低价: {first_record.low_price}")
                print(f"  收盘价: {first_record.close_price}")
                print(f"  成交量: {first_record.volume:,}")
                print(f"  市值: {first_record.market_cap:,}")
                print(f"  市盈率: {first_record.pe_ratio}")
                print(f"  数据质量评分: {first_record.quality_score:.2f}")
                
                # 数据验证
                print(f"\n进行数据质量验证...")
                validation_result = await adapter.validate_data(data)
                
                print(f"验证结果:")
                print(f"  数据有效性: {'✅ 有效' if validation_result.is_valid else '❌ 无效'}")
                print(f"  质量评分: {validation_result.quality_score:.2f}")
                print(f"  质量等级: {validation_result.quality_level}")
                print(f"  错误数量: {len(validation_result.errors)}")
                print(f"  警告数量: {len(validation_result.warnings)}")
                
                if validation_result.errors:
                    print("  错误详情:")
                    for error in validation_result.errors:
                        print(f"    - {error}")
                
                if validation_result.warnings:
                    print("  警告详情:")
                    for warning in validation_result.warnings:
                        print(f"    - {warning}")
            else:
                print("❌ 未获取到数据")
        
        # 健康检查
        print(f"\n进行健康检查...")
        health_status = await adapter.health_check()
        print(f"健康状态: {health_status['status']}")
        print(f"数据源类型: {health_status['source_type']}")
        print(f"缓存大小: {health_status['cache_size']}")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
    
    finally:
        # 断开连接
        await adapter.disconnect()
        print(f"\n✅ 已断开数据源连接")


async def demo_data_service():
    """演示数据服务管理器"""
    print("\n" + "=" * 60)
    print("演示2: 数据服务管理器功能")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = DataAdapterConfigManager()
    
    # 创建数据服务
    data_service = DataService(config_manager)
    
    try:
        # 初始化服务
        print("正在初始化数据服务...")
        initialized = await data_service.initialize()
        if not initialized:
            print("❌ 初始化失败")
            return
        
        print("✅ 数据服务初始化成功")
        
        # 获取服务统计信息
        print(f"\n获取服务统计信息...")
        stats = await data_service.get_data_statistics()
        print(f"总适配器数量: {stats['total_adapters']}")
        print(f"启用的适配器: {stats['enabled_adapters']}")
        
        if stats['adapters']:
            for name, adapter_stats in stats['adapters'].items():
                print(f"\n适配器 {name}:")
                print(f"  数据源类型: {adapter_stats['source_type']}")
                print(f"  更新频率: {adapter_stats['config']['update_frequency']}秒")
                print(f"  缓存启用: {adapter_stats['config']['cache_enabled']}")
                print(f"  质量阈值: {adapter_stats['config']['quality_threshold']}")
        
        # 健康检查
        print(f"\n进行服务健康检查...")
        health_status = await data_service.health_check()
        print(f"服务状态: {health_status['service_status']}")
        print(f"已初始化: {health_status['initialized']}")
        print(f"适配器总数: {health_status['total_adapters']}")
        
        if health_status['adapters']:
            for name, adapter_health in health_status['adapters'].items():
                print(f"  适配器 {name}: {adapter_health['status']}")
        
        # 获取可用股票代码
        print(f"\n获取所有可用股票代码...")
        all_symbols = await data_service.get_available_symbols()
        print(f"找到股票代码: {all_symbols}")
        
        # 尝试获取数据（如果有股票代码）
        if all_symbols:
            symbol = all_symbols[0]
            print(f"\n尝试获取 {symbol} 的数据...")
            data = await data_service.get_market_data(symbol)
            
            if data:
                print(f"✅ 成功获取 {len(data)} 条记录")
                
                # 验证数据质量
                validation_result = await data_service.validate_data_quality(data)
                print(f"数据质量验证:")
                print(f"  有效性: {'✅ 有效' if validation_result.is_valid else '❌ 无效'}")
                print(f"  质量评分: {validation_result.quality_score:.2f}")
            else:
                print("❌ 未获取到数据")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
    
    finally:
        # 清理资源
        await data_service.cleanup()
        print(f"\n✅ 数据服务已清理")


async def demo_configuration():
    """演示配置管理"""
    print("\n" + "=" * 60)
    print("演示3: 配置管理功能")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = DataAdapterConfigManager()
    
    try:
        # 显示配置摘要
        print("获取配置摘要...")
        summary = config_manager.get_config_summary()
        print(f"总适配器数量: {summary['total_adapters']}")
        print(f"启用的适配器: {summary['enabled_adapters']}")
        print(f"禁用的适配器: {summary['disabled_adapters']}")
        print(f"数据源类型: {summary['source_types']}")
        
        # 显示适配器详情
        if summary['adapters']:
            print(f"\n适配器详情:")
            for adapter_info in summary['adapters']:
                print(f"  名称: {adapter_info['name']}")
                print(f"  启用状态: {adapter_info['enabled']}")
                print(f"  优先级: {adapter_info['priority']}")
                print(f"  数据源类型: {adapter_info['source_type']}")
                print(f"  更新频率: {adapter_info['update_frequency']}秒")
                print(f"  缓存启用: {adapter_info['cache_enabled']}")
                print()
        
        # 配置验证
        print("进行配置验证...")
        validation_results = config_manager.validate_all_configs()
        
        for adapter_name, errors in validation_results.items():
            if errors:
                print(f"❌ 适配器 {adapter_name} 配置错误:")
                for error in errors:
                    print(f"    - {error}")
            else:
                print(f"✅ 适配器 {adapter_name} 配置正确")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")


async def main():
    """主演示函数"""
    print("🚀 黑人RAW DATA数据适配器演示")
    print("本演示将展示数据适配器的各种功能")
    
    try:
        # 演示1: 基础适配器功能
        await demo_basic_adapter()
        
        # 演示2: 数据服务管理器
        await demo_data_service()
        
        # 演示3: 配置管理
        await demo_configuration()
        
        print("\n" + "=" * 60)
        print("🎉 演示完成！")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 演示被用户中断")
    except Exception as e:
        print(f"\n\n❌ 演示过程中出现未处理的错误: {e}")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())
