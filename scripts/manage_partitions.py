#!/usr/bin/env python3
"""
分区管理脚本
Partition Management Script

用于手动管理数据库分区
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'api', 'strategies'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('partition_manager')

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库分区管理工具')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 创建分区命令
    create_parser = subparsers.add_parser('create', help='创建分区')
    create_parser.add_argument('--table', required=True, choices=['strategy_signals', 'stock_data', 'strategy_executions', 'performance_metrics'],
                              help='表名')
    create_parser.add_argument('--period', required=True, help='时间段 (格式: YYYY_MM for monthly, YYYYMMDD for daily)')

    # 清理分区命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧分区')
    cleanup_parser.add_argument('--table', choices=['strategy_signals', 'stock_data', 'strategy_executions', 'performance_metrics'],
                               help='表名 (不指定则清理所有表)')
    cleanup_parser.add_argument('--retention-days', type=int, help='保留天数 (覆盖默认值)')

    # 列出分区命令
    list_parser = subparsers.add_parser('list', help='列出分区信息')
    list_parser.add_argument('--table', choices=['strategy_signals', 'stock_data', 'strategy_executions', 'performance_metrics'],
                            help='表名 (不指定则显示所有表)')

    # 检查分区命令
    check_parser = subparsers.add_parser('check', help='检查分区状态')
    check_parser.add_argument('--table', choices=['strategy_signals', 'stock_data', 'strategy_executions', 'performance_metrics'],
                             help='表名 (不指定则检查所有表)')

    # 初始化命令
    init_parser = subparsers.add_parser('init', help='初始化分区表结构')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        # 导入分区管理器
        from database.partition_manager import partition_manager
        from database.partition_scheduler import partition_scheduler

        if args.command == 'init':
            logger.info("初始化分区表结构...")
            success = partition_manager.create_partitioned_tables()
            if success:
                logger.info("✅ 初始化成功")
            else:
                logger.error("❌ 初始化失败")
                sys.exit(1)

        elif args.command == 'create':
            logger.info(f"为表 {args.table} 创建 {args.period} 分区...")
            success = partition_manager.create_monthly_partitions(args.table, args.period)
            if success:
                logger.info("✅ 分区创建成功")
            else:
                logger.error("❌ 分区创建失败")
                sys.exit(1)

        elif args.command == 'cleanup':
            if args.table:
                table_name = args.table
                retention_days = args.retention_days or partition_manager.partitions_config[table_name].retention_period
                logger.info(f"清理表 {table_name} 超过 {retention_days} 天的分区...")
                dropped = partition_manager.drop_old_partitions(table_name, retention_days)
            else:
                logger.info("清理所有表的旧分区...")
                dropped = 0
                for table_name, config in partition_manager.partitions_config.items():
                    retention_days = args.retention_days or config.retention_period
                    table_dropped = partition_manager.drop_old_partitions(table_name, retention_days)
                    dropped += table_dropped
                    logger.info(f"表 {table_name}: 清理了 {table_dropped} 个分区")

            logger.info(f"✅ 总计清理 {dropped} 个分区")

        elif args.command == 'list':
            partitions = partition_manager.get_partition_info(args.table)
            if partitions:
                logger.info(f"找到 {len(partitions)} 个分区:")
                for partition in partitions:
                    logger.info(f"  - {partition['name']} ({partition['size']})")
            else:
                logger.info("没有找到分区")

        elif args.command == 'check':
            if args.table:
                partition_scheduler._check_table_partition_health(args.table)
            else:
                logger.info("检查所有表的分区健康状态...")
                for table_name in partition_manager.partitions_config.keys():
                    partition_scheduler._check_table_partition_health(table_name)

    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        logger.error("请确保已安装所需依赖: pip install psycopg2-binary schedule")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行命令失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()