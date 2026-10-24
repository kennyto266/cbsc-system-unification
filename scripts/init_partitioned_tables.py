#!/usr/bin/env python3
"""
初始化分区表脚本
Initialize Partitioned Tables Script

用于创建和初始化数据库分区表结构
"""

import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'api', 'strategies'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('partition_setup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('partition_setup')

def main():
    """主函数"""
    try:
        logger.info("=" * 60)
        logger.info("开始初始化分区表结构")
        logger.info("=" * 60)

        # 导入分区管理器
        from database.partition_manager import partition_manager

        # 创建分区表结构
        logger.info("正在创建分区表结构...")
        success = partition_manager.create_partitioned_tables()

        if success:
            logger.info("✅ 分区表结构创建成功")

            # 显示分区信息
            logger.info("\n当前分区信息:")
            partitions = partition_manager.get_partition_info()
            for partition in partitions:
                logger.info(f"  - {partition['name']} ({partition['size']})")

        else:
            logger.error("❌ 分区表结构创建失败")
            sys.exit(1)

        # 测试分区创建
        logger.info("\n测试未来分区创建...")
        current_date = datetime.now()
        next_month = (current_date.replace(day=1) + timedelta(days=32)).strftime('%Y_%m')

        for table_name in ['strategy_signals', 'stock_data']:
            success = partition_manager.create_monthly_partitions(table_name, next_month)
            if success:
                logger.info(f"✅ 成功创建 {table_name} 下个月分区")
            else:
                logger.error(f"❌ 创建 {table_name} 下个月分区失败")

        logger.info("\n" + "=" * 60)
        logger.info("分区表初始化完成")
        logger.info("=" * 60)

    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        logger.error("请确保已安装所需依赖: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        logger.error(f"初始化过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()