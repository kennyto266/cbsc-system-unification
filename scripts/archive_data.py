#!/usr/bin/env python3
"""
数据归档脚本
Data Archive Script

用于归档历史数据到长期存储
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

logger = logging.getLogger('archive_script')

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据归档工具')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 归档表命令
    archive_parser = subparsers.add_parser('archive', help='归档表数据')
    archive_parser.add_argument('--table', choices=['strategy_signals', 'stock_data', 'strategy_executions', 'performance_metrics'],
                               help='表名 (不指定则归档所有表)')
    archive_parser.add_argument('--cutoff-date', type=str, help='截止日期 (YYYY-MM-DD)')
    archive_parser.add_argument('--dry-run', action='store_true', help='仅检查，不执行归档')

    # 清理文件命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理本地归档文件')
    cleanup_parser.add_argument('--days-old', type=int, default=30, help='删除N天前的文件')

    # 统计信息命令
    stats_parser = subparsers.add_parser('stats', help='显示归档统计信息')

    # 验证归档命令
    validate_parser = subparsers.add_parser('validate', help='验证归档数据完整性')
    validate_parser.add_argument('--table', choices=['strategy_signals', 'stock_data', 'strategy_executions', 'performance_metrics'],
                                required=True, help='表名')
    validate_parser.add_argument('--archive-file', required=True, help='归档文件路径')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        # 导入归档管理器
        from database.archive_manager import archive_manager

        if args.command == 'archive':
            cutoff_date = None
            if args.cutoff_date:
                cutoff_date = datetime.strptime(args.cutoff_date, '%Y-%m-%d')

            if args.dry_run:
                logger.info("DRY RUN: 仅检查需要归档的数据...")
                if args.table:
                    data = archive_manager.get_archive_candidates(args.table, cutoff_date or datetime.now() - timedelta(days=90))
                    logger.info(f"表 {args.table} 需要归档 {len(data)} 条记录")
                else:
                    total = 0
                    for table_name in archive_manager.archive_config.keys():
                        data = archive_manager.get_archive_candidates(table_name, cutoff_date or datetime.now() - timedelta(days=90))
                        total += len(data)
                        logger.info(f"表 {table_name}: {len(data)} 条记录")
                    logger.info(f"总计需要归档 {total} 条记录")
            else:
                if args.table:
                    logger.info(f"归档表 {args.table}...")
                    result = archive_manager.archive_table(args.table, cutoff_date)
                    if result['success']:
                        logger.info(f"✅ 归档成功: {result['archived_records']} 条记录")
                    else:
                        logger.error(f"❌ 归档失败: {result['error']}")
                else:
                    logger.info("归档所有表...")
                    results = archive_manager.archive_all_tables()
                    for result in results:
                        if result['success']:
                            logger.info(f"✅ 表 {result['table']}: {result['archived_records']} 条记录")
                        else:
                            logger.error(f"❌ 表 {result['table']}: {result['error']}")

        elif args.command == 'cleanup':
            logger.info(f"清理 {args.days_old} 天前的归档文件...")
            cleaned = archive_manager.cleanup_archive_files(args.days_old)
            logger.info(f"✅ 清理了 {cleaned} 个文件")

        elif args.command == 'stats':
            stats = archive_manager.get_archive_statistics()
            logger.info("归档统计信息:")
            logger.info(f"  本地文件数: {stats.get('local_files', 0)}")
            logger.info(f"  本地文件大小: {stats.get('local_size', 0):,} bytes")

            logger.info("\n各表当前记录数:")
            for table_name, table_stats in stats.get('tables', {}).items():
                logger.info(f"  {table_name}: {table_stats['current_records']:,} 条记录 "
                           f"(保留期: {table_stats['retention_days']} 天)")

        elif args.command == 'validate':
            logger.info(f"验证归档文件 {args.archive_file}...")
            if not os.path.exists(args.archive_file):
                logger.error("❌ 归档文件不存在")
                sys.exit(1)

            # 这里可以添加文件完整性验证逻辑
            import gzip
            import json

            try:
                if args.archive_file.endswith('.gz'):
                    with gzip.open(args.archive_file, 'rt') as f:
                        data = json.load(f)
                else:
                    with open(args.archive_file, 'r') as f:
                        data = json.load(f)

                logger.info(f"✅ 验证成功: 文件包含 {len(data)} 条记录")

                # 可以添加更详细的验证逻辑
                if data:
                    sample_record = data[0]
                    logger.info(f"  样本记录字段: {list(sample_record.keys())}")

            except Exception as e:
                logger.error(f"❌ 验证失败: {e}")
                sys.exit(1)

    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        logger.error("请确保已安装所需依赖: pip install psycopg2-binary boto3")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行命令失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()