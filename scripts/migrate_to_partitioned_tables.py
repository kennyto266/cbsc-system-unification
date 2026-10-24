#!/usr/bin/env python3
"""
数据迁移脚本
Data Migration Script

将现有数据迁移到新的分区表结构
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from contextlib import contextmanager
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'api', 'strategies'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('migration_script')

class DataMigrator:
    """数据迁移器"""

    def __init__(self, db_url: str):
        """初始化迁移器"""
        self.db_url = db_url
        self.batch_size = 5000

    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = None
        try:
            conn = psycopg2.connect(self.db_url)
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def check_migration_prerequisites(self) -> bool:
        """检查迁移前提条件"""
        logger.info("检查迁移前提条件...")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 检查是否已存在分区表
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_name LIKE '%_2024_%' OR table_name LIKE '%2024%'
                    AND table_schema = 'public';
                """)

                existing_partitions = cursor.fetchall()
                if existing_partitions:
                    logger.warning(f"发现现有分区表: {len(existing_partitions)} 个")
                    for table in existing_partitions:
                        logger.warning(f"  - {table[0]}")
                    logger.warning("请确认是否继续迁移，这可能导致数据冲突")
                    return False

                # 检查原始表是否存在
                required_tables = ['strategy_signals', 'stock_data', 'strategy_executions']
                for table in required_tables:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = %s AND table_schema = 'public'
                        );
                    """, (table,))

                    exists = cursor.fetchone()[0]
                    if not exists:
                        logger.error(f"必需的表不存在: {table}")
                        return False

                # 检查数据量
                total_records = 0
                for table in required_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    total_records += count
                    logger.info(f"表 {table}: {count:,} 条记录")

                logger.info(f"总计需要迁移 {total_records:,} 条记录")
                return True

        except Exception as e:
            logger.error(f"检查迁移前提条件失败: {e}")
            return False

    def backup_original_tables(self) -> bool:
        """备份原始表"""
        logger.info("备份原始表...")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                tables_to_backup = ['strategy_signals', 'stock_data', 'strategy_executions']

                for table in tables_to_backup:
                    backup_name = f"{table}_backup_{timestamp}"
                    cursor.execute(f"ALTER TABLE {table} RENAME TO {backup_name};")
                    logger.info(f"备份表 {table} -> {backup_name}")

                conn.commit()
                logger.info("原始表备份完成")
                return True

        except Exception as e:
            logger.error(f"备份原始表失败: {e}")
            return False

    def create_partitioned_tables(self) -> bool:
        """创建分区表结构"""
        logger.info("创建分区表结构...")

        try:
            # 导入分区管理器
            from database.partition_manager import partition_manager

            success = partition_manager.create_partitioned_tables()
            if success:
                logger.info("✅ 分区表结构创建成功")
                return True
            else:
                logger.error("❌ 分区表结构创建失败")
                return False

        except Exception as e:
            logger.error(f"创建分区表结构失败: {e}")
            return False

    def migrate_table_data(self, table_name: str, backup_table_name: str) -> bool:
        """迁移单个表的数据"""
        logger.info(f"开始迁移表 {table_name}...")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 获取总记录数
                cursor.execute(f"SELECT COUNT(*) FROM {backup_table_name}")
                total_records = cursor.fetchone()[0]
                logger.info(f"表 {backup_table_name} 共有 {total_records:,} 条记录")

                # 分批迁移数据
                offset = 0
                migrated_count = 0
                batch_num = 0

                while True:
                    start_time = time.time()

                    if table_name == 'strategy_signals':
                        cursor.execute(f"""
                            SELECT signal_id, strategy_id, strategy_type, signal_type,
                                   strength, confidence, symbol, timestamp,
                                   market_data, parameters, metadata, created_at
                            FROM {backup_table_name}
                            ORDER BY timestamp
                            LIMIT %s OFFSET %s
                        """, (self.batch_size, offset))
                    elif table_name == 'stock_data':
                        cursor.execute(f"""
                            SELECT id, symbol, timestamp, open_price, high_price,
                                   low_price, close_price, volume, source, created_at
                            FROM {backup_table_name}
                            ORDER BY timestamp
                            LIMIT %s OFFSET %s
                        """, (self.batch_size, offset))
                    elif table_name == 'strategy_executions':
                        cursor.execute(f"""
                            SELECT execution_id, strategy_id, status, start_time,
                                   end_time, execution_mode, data_source, signals_count,
                                   performance_data, error_message, execution_metadata, created_at
                            FROM {backup_table_name}
                            ORDER BY created_at
                            LIMIT %s OFFSET %s
                        """, (self.batch_size, offset))

                    batch = cursor.fetchall()
                    if not batch:
                        break

                    batch_num += 1
                    logger.info(f"处理批次 {batch_num}: {len(batch)} 条记录")

                    # 准备插入数据
                    if table_name == 'strategy_signals':
                        insert_query = """
                            INSERT INTO strategy_signals (
                                signal_id, strategy_id, strategy_type, signal_type,
                                strength, confidence, symbol, timestamp,
                                market_data, parameters, metadata, created_at
                            ) VALUES %s
                        """
                    elif table_name == 'stock_data':
                        insert_query = """
                            INSERT INTO stock_data (
                                id, symbol, timestamp, open_price, high_price,
                                low_price, close_price, volume, source, created_at
                            ) VALUES %s
                        """
                    elif table_name == 'strategy_executions':
                        insert_query = """
                            INSERT INTO strategy_executions (
                                execution_id, strategy_id, status, start_time,
                                end_time, execution_mode, data_source, signals_count,
                                performance_data, error_message, execution_metadata, created_at
                            ) VALUES %s
                        """

                    # 执行批量插入
                    execute_values(cursor, insert_query, batch)
                    conn.commit()

                    migrated_count += len(batch)
                    offset += self.batch_size

                    # 计算迁移速度
                    elapsed = time.time() - start_time
                    speed = len(batch) / elapsed if elapsed > 0 else 0
                    progress = (migrated_count / total_records) * 100 if total_records > 0 else 0

                    logger.info(f"批次 {batch_num} 完成: {len(batch)} 条记录, "
                               f"速度: {speed:.0f} 记录/秒, 进度: {progress:.1f}%")

                logger.info(f"✅ 表 {table_name} 迁移完成: {migrated_count:,} 条记录")
                return True

        except Exception as e:
            logger.error(f"迁移表 {table_name} 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def validate_migration(self, table_name: str, backup_table_name: str) -> bool:
        """验证迁移结果"""
        logger.info(f"验证表 {table_name} 的迁移结果...")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 比较记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                new_count = cursor.fetchone()[0]

                cursor.execute(f"SELECT COUNT(*) FROM {backup_table_name}")
                old_count = cursor.fetchone()[0]

                logger.info(f"原表记录数: {old_count:,}")
                logger.info(f"新表记录数: {new_count:,}")

                if new_count != old_count:
                    logger.error(f"❌ 记录数不匹配: {old_count} vs {new_count}")
                    return False

                # 比较数据采样
                if table_name == 'strategy_signals':
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table_name} ss
                        JOIN {backup_table_name} ss_old ON ss.signal_id = ss_old.signal_id
                    """)
                elif table_name == 'stock_data':
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table_name} sd
                        JOIN {backup_table_name} sd_old ON sd.id = sd_old.id
                    """)
                elif table_name == 'strategy_executions':
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {table_name} se
                        JOIN {backup_table_name} se_old ON se.execution_id = se_old.execution_id
                    """)

                matched_records = cursor.fetchone()[0]
                match_rate = (matched_records / new_count) * 100 if new_count > 0 else 0

                logger.info(f"数据匹配率: {match_rate:.2f}% ({matched_records:,}/{new_count:,})")

                if match_rate >= 99.9:
                    logger.info(f"✅ 表 {table_name} 验证通过")
                    return True
                else:
                    logger.error(f"❌ 表 {table_name} 验证失败: 数据匹配率过低")
                    return False

        except Exception as e:
            logger.error(f"验证表 {table_name} 失败: {e}")
            return False

    def cleanup_backup_tables(self) -> bool:
        """清理备份表"""
        logger.info("清理备份表...")

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 获取所有备份表
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_name LIKE '%_backup_%'
                    AND table_schema = 'public';
                """)

                backup_tables = cursor.fetchall()
                cleaned = 0

                for (table_name,) in backup_tables:
                    # 询问用户是否删除备份表
                    response = input(f"是否删除备份表 {table_name}? (y/N): ").strip().lower()
                    if response == 'y':
                        cursor.execute(f"DROP TABLE {table_name} CASCADE;")
                        logger.info(f"删除备份表: {table_name}")
                        cleaned += 1
                    else:
                        logger.info(f"保留备份表: {table_name}")

                conn.commit()
                logger.info(f"清理完成: 删除了 {cleaned} 个备份表")
                return True

        except Exception as e:
            logger.error(f"清理备份表失败: {e}")
            return False

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='数据迁移到分区表工具')
    parser.add_argument('--db-url', help='数据库URL (默认使用环境变量 DATABASE_URL)')
    parser.add_argument('--batch-size', type=int, default=5000, help='批处理大小')
    parser.add_argument('--skip-backup', action='store_true', help='跳过备份步骤')
    parser.add_argument('--cleanup', action='store_true', help='迁移后清理备份表')

    args = parser.parse_args()

    db_url = args.db_url or os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/quant_system')

    migrator = DataMigrator(db_url)
    migrator.batch_size = args.batch_size

    try:
        logger.info("=" * 60)
        logger.info("开始数据迁移到分区表")
        logger.info("=" * 60)

        # 1. 检查前提条件
        if not migrator.check_migration_prerequisites():
            logger.error("❌ 前提条件检查失败")
            sys.exit(1)

        # 2. 备份原始表
        if not args.skip_backup:
            if not migrator.backup_original_tables():
                logger.error("❌ 备份失败")
                sys.exit(1)

        # 3. 创建分区表结构
        if not migrator.create_partitioned_tables():
            logger.error("❌ 创建分区表失败")
            sys.exit(1)

        # 4. 迁移数据
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        tables_to_migrate = [
            ('strategy_signals', f'strategy_signals_backup_{timestamp}'),
            ('stock_data', f'stock_data_backup_{timestamp}'),
            ('strategy_executions', f'strategy_executions_backup_{timestamp}')
        ]

        if args.skip_backup:
            # 如果跳过备份，查找现有的备份表
            with migrator.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_name LIKE '%_backup_%'
                    AND table_schema = 'public'
                    ORDER BY table_name;
                """)
                backup_tables = cursor.fetchall()
                # 这里需要更复杂的逻辑来匹配表名和备份表
                # 为简化，假设使用特定的备份表名
                tables_to_migrate = [
                    ('strategy_signals', 'strategy_signals_backup'),
                    ('stock_data', 'stock_data_backup'),
                    ('strategy_executions', 'strategy_executions_backup')
                ]

        migration_success = True
        for table_name, backup_table_name in tables_to_migrate:
            # 检查备份表是否存在
            with migrator.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = %s AND table_schema = 'public'
                    );
                """, (backup_table_name,))
                exists = cursor.fetchone()[0]

                if not exists:
                    logger.warning(f"备份表 {backup_table_name} 不存在，跳过迁移 {table_name}")
                    continue

            # 迁移数据
            if not migrator.migrate_table_data(table_name, backup_table_name):
                logger.error(f"❌ 迁移表 {table_name} 失败")
                migration_success = False
                continue

            # 验证迁移
            if not migrator.validate_migration(table_name, backup_table_name):
                logger.error(f"❌ 验证表 {table_name} 失败")
                migration_success = False
                continue

        if migration_success:
            logger.info("✅ 所有表迁移成功")

            # 5. 清理备份表
            if args.cleanup:
                migrator.cleanup_backup_tables()

            logger.info("=" * 60)
            logger.info("数据迁移完成")
            logger.info("=" * 60)
        else:
            logger.error("❌ 部分迁移失败")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("用户中断迁移")
        sys.exit(1)
    except Exception as e:
        logger.error(f"迁移过程中发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()