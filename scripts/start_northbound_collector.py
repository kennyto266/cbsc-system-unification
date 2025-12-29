#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
北向资金数据收集器启动脚本
支持命令行参数和配置文件
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.services.northbound_flow_collector import (
    NorthboundConfig,
    NorthboundDataManager,
    NorthboundScheduler
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/northbound_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> dict:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
        return {}

async def collect_historical_data(manager: NorthboundDataManager, days: int = 30):
    """收集历史数据"""
    logger.info(f"开始收集最近 {days} 天的历史数据...")

    success_count = 0
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

        # 跳过周末
        if datetime.strptime(date, '%Y-%m-%d').weekday() >= 5:
            logger.info(f"跳过周末: {date}")
            continue

        try:
            success = await manager.collect_daily_data(date)
            if success:
                success_count += 1
                logger.info(f"✅ {date}: 数据收集成功")
            else:
                logger.warning(f"❌ {date}: 数据收集失败")
        except Exception as e:
            logger.error(f"❌ {date}: 收集出错 - {e}")

        # 避免请求过快
        await asyncio.sleep(1)

    logger.info(f"历史数据收集完成: {success_count}/{days} 天成功")

async def collect_today_data(manager: NorthboundDataManager):
    """收集今日数据"""
    today = datetime.now().strftime('%Y-%m-%d')
    logger.info(f"开始收集今日数据: {today}")

    success = await manager.collect_daily_data(today)
    if success:
        logger.info(f"✅ {today}: 数据收集成功")
    else:
        logger.error(f"❌ {today}: 数据收集失败")

    return success

async def start_scheduler(manager: NorthboundDataManager, update_frequency: str = "daily"):
    """启动定时调度器"""
    logger.info(f"启动定时调度器，更新频率: {update_frequency}")

    scheduler = NorthboundScheduler(manager)
    await scheduler.start_scheduler()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="北向资金数据收集器")
    parser.add_argument("--config", "-c", default="config/northbound_config.json",
                       help="配置文件路径")
    parser.add_argument("--mode", "-m", choices=["historical", "today", "scheduler"],
                       default="today", help="运行模式")
    parser.add_argument("--days", "-d", type=int, default=30,
                       help="历史数据天数（仅在historical模式下使用）")
    parser.add_argument("--db-path", default="data/northbound_flow.db",
                       help="数据库路径")

    args = parser.parse_args()

    # 确保必要的目录存在
    os.makedirs(os.path.dirname(args.db_path), exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # 加载配置
    config_data = load_config(args.config)

    # 创建配置对象
    config = NorthboundConfig(
        db_path=args.db_path,
        update_frequency=config_data.get("schedule", {}).get("update_frequency", "daily")
    )

    # 创建管理器
    manager = NorthboundDataManager(config)

    # 根据模式执行不同的操作
    if args.mode == "historical":
        # 收集历史数据
        asyncio.run(collect_historical_data(manager, args.days))

    elif args.mode == "today":
        # 收集今日数据
        asyncio.run(collect_today_data(manager))

    elif args.mode == "scheduler":
        # 启动定时调度器
        try:
            asyncio.run(start_scheduler(manager, config.update_frequency))
        except KeyboardInterrupt:
            logger.info("定时调度器已停止")

if __name__ == "__main__":
    main()