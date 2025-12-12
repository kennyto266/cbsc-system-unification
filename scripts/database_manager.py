#!/usr/bin/env python3
"""
数据库管理器
Database Manager

统一的数据库管理工具 - 分区、归档、视图管理
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

logger = logging.getLogger('database_manager')

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库管理工具')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 初始化命令
    init_parser = subparsers.add_parser('init', help='初始化数据库')
    init_parser.add_argument('--create-partitions', action='store_true', default=True,
                            help='创建分区表结构')
    init_parser.add_argument('--create-views', action='store_true', default=True,
                            help='创建聚合视图')
    init_parser.add_argument('--create-indexes', action='store_true', default=True,
                            help='创建性能索引')

    # 迁移命令
    migrate_parser = subparsers.add_parser('migrate', help='数据迁移')
    migrate_parser.add_argument('--batch-size', type=int, default=5000,
                               help='批处理大小')
    migrate_parser.add_argument('--skip-backup', action='store_true',
                               help='跳过备份步骤')
    migrate_parser.add_argument('--cleanup', action='store_true',
                               help='迁移后清理备份表')

    # 分区管理命令
    partition_parser = subparsers.add_parser('partition', help='分区管理')
    partition_subparsers = partition_parser.add_subparsers(dest='partition_action', help='分区操作')

    create_part_parser = partition_subparsers.add_parser('create', help='创建分区')
    create_part_parser.add_argument('--table', required=True,
                                   choices=['strategy_signals', 'stock_data', 'strategy_executions', 'performance_metrics'],
                                   help='表名')
    create_part_parser.add_argument('--period', required=True, help='时间段 (格式: YYYY_MM)')

    cleanup_part_parser = partition_subparsers.add_parser('cleanup', help='清理旧分区')
    cleanup_part_parser.add_argument('--table',
                                    choices=['strategy_signals', 'stock_data', 'strategy_executions', 'performance_metrics'],
                                    help='表名 (不指定则清理所有表)')
    cleanup_part_parser.add_argument('--retention-days', type=int, help='保留天数 (覆盖默认值)')

    list_part_parser = partition_subparsers.add_parser('list', help='列出分区信息')
    list_part_parser.add_argument('--table',
                                 choices=['strategy_signals', 'stock_data', 'strategy_executions', 'performance_metrics'],
                                 help='表名 (不指定则显示所有表)')

    # 归档管理命令
    archive_parser = subparsers.add_parser('archive', help='数据归档')
    archive_parser.add_argument('--table',
                               choices=['strategy_signals', 'stock_data', 'strategy_executions', 'performance_metrics'],
                               help='表名 (不指定则归档所有表)')
    archive_parser.add_argument('--cutoff-date', type=str, help='截止日期 (YYYY-MM-DD)')
    archive_parser.add_argument('--dry-run', action='store_true', help='仅检查，不执行归档')

    # 视图管理命令
    view_parser = subparsers.add_parser('view', help='视图管理')
    view_parser.add_argument('--action', choices=['create', 'refresh', 'stats'], required=True,
                            help='视图操作')

    # 性能测试命令
    perf_parser = subparsers.add_parser('perf-test', help='性能测试')
    perf_parser.add_argument('--test-data-count', type=int, default=10000,
                            help='测试数据数量')
    perf_parser.add_argument('--report-file', help='性能报告文件路径')
    perf_parser.add_argument('--skip-data-gen', action='store_true',
                            help='跳过测试数据生成')

    # 状态检查命令
    status_parser = subparsers.add_parser('status', help='数据库状态检查')
    status_parser.add_argument('--detailed', action='store_true', help='详细状态信息')

    # 调度器命令
    scheduler_parser = subparsers.add_parser('scheduler', help='分区调度器')
    scheduler_parser.add_argument('--action', choices=['start', 'stop', 'status'], required=True,
                                help='调度器操作')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'init':
            handle_init_command(args)
        elif args.command == 'migrate':
            handle_migrate_command(args)
        elif args.command == 'partition':
            handle_partition_command(args)
        elif args.command == 'archive':
            handle_archive_command(args)
        elif args.command == 'view':
            handle_view_command(args)
        elif args.command == 'perf-test':
            handle_perf_test_command(args)
        elif args.command == 'status':
            handle_status_command(args)
        elif args.command == 'scheduler':
            handle_scheduler_command(args)

    except Exception as e:
        logger.error(f"执行命令失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def handle_init_command(args):
    """处理初始化命令"""
    logger.info("初始化数据库...")

    from database.partition_manager import partition_manager
    from database.view_manager import AggregateViewManager

    # 创建分区表结构
    if args.create_partitions:
        logger.info("创建分区表结构...")
        success = partition_manager.create_partitioned_tables()
        if success:
            logger.info("✅ 分区表结构创建成功")
        else:
            logger.error("❌ 分区表结构创建失败")
            sys.exit(1)

    # 创建聚合视图
    if args.create_views:
        logger.info("创建聚合视图...")
        view_manager = AggregateViewManager(partition_manager.db_url)
        success = view_manager.create_all_views()
        if success:
            logger.info("✅ 聚合视图创建成功")
        else:
            logger.error("❌ 聚合视图创建失败")

    # 创建性能索引
    if args.create_indexes:
        logger.info("创建性能索引...")
        view_manager = AggregateViewManager(partition_manager.db_url)
        success = view_manager.create_performance_indexes()
        if success:
            logger.info("✅ 性能索引创建成功")
        else:
            logger.error("❌ 性能索引创建失败")

    logger.info("数据库初始化完成")

def handle_migrate_command(args):
    """处理迁移命令"""
    logger.info("开始数据迁移...")

    # 构建迁移命令参数
    migrate_args = [
        '--batch-size', str(args.batch_size)
    ]

    if args.skip_backup:
        migrate_args.append('--skip-backup')

    if args.cleanup:
        migrate_args.append('--cleanup')

    # 调用迁移脚本
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), 'migrate_to_partitioned_tables.py')
    result = subprocess.run([sys.executable, script_path] + migrate_args)

    if result.returncode == 0:
        logger.info("✅ 数据迁移完成")
    else:
        logger.error("❌ 数据迁移失败")
        sys.exit(result.returncode)

def handle_partition_command(args):
    """处理分区管理命令"""
    from scripts.manage_partitions import main as partition_main

    # 构建参数
    if args.partition_action == 'create':
        partition_args = ['create', '--table', args.table, '--period', args.period]
    elif args.partition_action == 'cleanup':
        partition_args = ['cleanup']
        if args.table:
            partition_args.extend(['--table', args.table])
        if args.retention_days:
            partition_args.extend(['--retention-days', str(args.retention_days)])
    elif args.partition_action == 'list':
        partition_args = ['list']
        if args.table:
            partition_args.extend(['--table', args.table])
    else:
        logger.error(f"未知的分区操作: {args.partition_action}")
        sys.exit(1)

    # 调用分区管理脚本
    sys.argv = ['manage_partitions.py'] + partition_args
    partition_main()

def handle_archive_command(args):
    """处理归档命令"""
    from scripts.archive_data import main as archive_main

    # 构建参数
    archive_args = ['archive']
    if args.table:
        archive_args.extend(['--table', args.table])
    if args.cutoff_date:
        archive_args.extend(['--cutoff-date', args.cutoff_date])
    if args.dry_run:
        archive_args.append('--dry-run')

    # 调用归档脚本
    sys.argv = ['archive_data.py'] + archive_args
    archive_main()

def handle_view_command(args):
    """处理视图管理命令"""
    from database.view_manager import AggregateViewManager
    import os

    view_manager = AggregateViewManager(os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/quant_system'))

    if args.action == 'create':
        logger.info("创建聚合视图...")
        success = view_manager.create_all_views()
        if success:
            logger.info("✅ 聚合视图创建成功")
        else:
            logger.error("❌ 聚合视图创建失败")

    elif args.action == 'refresh':
        logger.info("刷新物化视图...")
        success = view_manager.refresh_materialized_views()
        if success:
            logger.info("✅ 物化视图刷新成功")
        else:
            logger.error("❌ 物化视图刷新失败")

    elif args.action == 'stats':
        logger.info("获取视图使用统计...")
        stats = view_manager.get_view_usage_stats()
        if stats:
            logger.info("视图使用统计:")
            for stat in stats:
                logger.info(f"  {stat['name']}: {stat['size']}")
        else:
            logger.info("没有找到视图统计信息")

def handle_perf_test_command(args):
    """处理性能测试命令"""
    # 构建性能测试参数
    test_args = [
        '--test-data-count', str(args.test_data_count)
    ]

    if args.report_file:
        test_args.extend(['--report-file', args.report_file])

    if args.skip_data_gen:
        test_args.append('--skip-data-gen')

    # 调用性能测试脚本
    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), 'test_partition_performance.py')
    result = subprocess.run([sys.executable, script_path] + test_args)

    if result.returncode != 0:
        logger.error("性能测试失败")
        sys.exit(result.returncode)

def handle_status_command(args):
    """处理状态检查命令"""
    logger.info("检查数据库状态...")

    from database.partition_manager import partition_manager
    from database.archive_manager import archive_manager

    # 检查分区状态
    logger.info("\n分区状态:")
    partitions = partition_manager.get_partition_info()
    if partitions:
        table_counts = {}
        total_size = 0

        for partition in partitions:
            table_name = partition['name'].split('_')[0]
            if table_name not in table_counts:
                table_counts[table_name] = 0
            table_counts[table_name] += 1

            # 简单解析大小
            size_str = partition['size']
            if 'MB' in size_str:
                size_value = float(size_str.replace('MB', ''))
                total_size += size_value
            elif 'GB' in size_str:
                size_value = float(size_str.replace('GB', '')) * 1024
                total_size += size_value

        for table_name, count in table_counts.items():
            logger.info(f"  {table_name}: {count} 个分区")

        logger.info(f"总大小: {total_size:.1f} MB")
    else:
        logger.info("  没有找到分区")

    # 检查归档状态
    if args.detailed:
        logger.info("\n归档状态:")
        archive_stats = archive_manager.get_archive_statistics()
        if archive_stats:
            logger.info(f"  本地归档文件: {archive_stats.get('local_files', 0)}")
            logger.info(f"  本地文件大小: {archive_stats.get('local_size', 0):,} bytes")

            for table_name, table_stats in archive_stats.get('tables', {}).items():
                logger.info(f"  {table_name}: {table_stats.get('current_records', 0):,} 条当前记录")
        else:
            logger.info("  无法获取归档统计信息")

def handle_scheduler_command(args):
    """处理调度器命令"""
    from database.partition_scheduler import partition_scheduler

    if args.action == 'start':
        logger.info("启动分区调度器...")
        partition_scheduler.start()
    elif args.action == 'stop':
        logger.info("停止分区调度器...")
        partition_scheduler.stop()
    elif args.action == 'status':
        logger.info(f"调度器状态: {'运行中' if partition_scheduler.running else '已停止'}")

if __name__ == "__main__":
    main()