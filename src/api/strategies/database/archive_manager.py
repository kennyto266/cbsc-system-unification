"""
数据归档管理器
Data Archive Manager

负责将历史数据从主数据库迁移到归档存储
"""

import logging
import os
import gzip
import json
import csv
import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from contextlib import contextmanager
import tempfile
import shutil

logger = logging.getLogger('archive_manager')

class DataArchiveManager:
    """数据归档管理器"""

    def __init__(self):
        """初始化归档管理器"""
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/quant_system')
        self.archive_config = {
            'strategy_signals': {
                'retention_days': 90,
                'batch_size': 10000,
                'archive_format': 'json',
                'compress': True
            },
            'stock_data': {
                'retention_days': 365,
                'batch_size': 20000,
                'archive_format': 'csv',
                'compress': True
            },
            'strategy_executions': {
                'retention_days': 180,
                'batch_size': 5000,
                'archive_format': 'json',
                'compress': True
            },
            'performance_metrics': {
                'retention_days': 30,
                'batch_size': 50000,
                'archive_format': 'csv',
                'compress': True
            }
        }

        # S3配置 (可选)
        self.s3_enabled = os.getenv('ARCHIVE_S3_ENABLED', 'false').lower() == 'true'
        if self.s3_enabled:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            )
            self.s3_bucket = os.getenv('ARCHIVE_S3_BUCKET')
        else:
            self.s3_client = None
            self.s3_bucket = None

        # 本地归档目录
        self.local_archive_dir = os.getenv('ARCHIVE_LOCAL_DIR', '/tmp/data_archive')
        os.makedirs(self.local_archive_dir, exist_ok=True)

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

    def get_archive_candidates(self, table_name: str, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """获取需要归档的数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)

                if table_name == 'strategy_signals':
                    query = """
                        SELECT signal_id, strategy_id, strategy_type, signal_type,
                               strength, confidence, symbol, timestamp,
                               market_data, parameters, metadata, created_at
                        FROM strategy_signals
                        WHERE timestamp < %s
                        ORDER BY timestamp
                    """
                elif table_name == 'stock_data':
                    query = """
                        SELECT id, symbol, timestamp, open_price, high_price,
                               low_price, close_price, volume, source, created_at
                        FROM stock_data
                        WHERE timestamp < %s
                        ORDER BY timestamp
                    """
                elif table_name == 'strategy_executions':
                    query = """
                        SELECT execution_id, strategy_id, status, start_time,
                               end_time, execution_mode, data_source, signals_count,
                               performance_data, error_message, execution_metadata, created_at
                        FROM strategy_executions
                        WHERE created_at < %s
                        ORDER BY created_at
                    """
                elif table_name == 'performance_metrics':
                    query = """
                        SELECT id, strategy_id, metric_type, metric_value,
                               recorded_at, additional_data
                        FROM performance_metrics
                        WHERE recorded_at < %s
                        ORDER BY recorded_at
                    """
                else:
                    raise ValueError(f"Unsupported table: {table_name}")

                cursor.execute(query, (cutoff_date,))
                data = cursor.fetchall()

                return [dict(row) for row in data]

        except Exception as e:
            logger.error(f"获取归档候选数据失败 ({table_name}): {e}")
            return []

    def archive_data_to_file(self, table_name: str, data: List[Dict[str, Any]]) -> Optional[str]:
        """将数据归档到文件"""
        if not data:
            return None

        try:
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_format = self.archive_config[table_name]['archive_format']
            compress = self.archive_config[table_name]['compress']

            if compress:
                filename = f"{table_name}_{timestamp}.{archive_format}.gz"
            else:
                filename = f"{table_name}_{timestamp}.{archive_format}"

            file_path = os.path.join(self.local_archive_dir, filename)

            # 写入数据
            if compress:
                with gzip.open(file_path, 'wt', encoding='utf-8') as f:
                    self._write_data(f, data, archive_format)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    self._write_data(f, data, archive_format)

            file_size = os.path.getsize(file_path)
            logger.info(f"归档数据到文件: {filename} ({file_size:,} bytes)")

            return file_path

        except Exception as e:
            logger.error(f"归档数据到文件失败 ({table_name}): {e}")
            return None

    def _write_data(self, file_handle, data: List[Dict[str, Any]], format_type: str):
        """写入数据到文件"""
        if format_type == 'json':
            json.dump(data, file_handle, indent=2, default=str, ensure_ascii=False)
        elif format_type == 'csv':
            if not data:
                return

            fieldnames = data[0].keys()
            writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def upload_to_s3(self, file_path: str, table_name: str) -> bool:
        """上传文件到S3"""
        if not self.s3_client or not self.s3_bucket:
            logger.warning("S3未配置，跳过上传")
            return False

        try:
            filename = os.path.basename(file_path)
            s3_key = f"archive/{table_name}/{filename}"

            self.s3_client.upload_file(file_path, self.s3_bucket, s3_key)

            logger.info(f"上传到S3: s3://{self.s3_bucket}/{s3_key}")
            return True

        except Exception as e:
            logger.error(f"上传到S3失败: {e}")
            return False

    def remove_archived_data(self, table_name: str, cutoff_date: datetime, batch_size: int = 1000) -> int:
        """删除已归档的数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                total_deleted = 0

            while True:
                with self.get_connection() as conn:
                    cursor = conn.cursor()

                    if table_name == 'strategy_signals':
                        query = """
                            DELETE FROM strategy_signals
                            WHERE ctid IN (
                                SELECT ctid FROM strategy_signals
                                WHERE timestamp < %s
                                LIMIT %s
                            )
                        """
                        cursor.execute(query, (cutoff_date, batch_size))
                    elif table_name == 'stock_data':
                        query = """
                            DELETE FROM stock_data
                            WHERE ctid IN (
                                SELECT ctid FROM stock_data
                                WHERE timestamp < %s
                                LIMIT %s
                            )
                        """
                        cursor.execute(query, (cutoff_date, batch_size))
                    elif table_name == 'strategy_executions':
                        query = """
                            DELETE FROM strategy_executions
                            WHERE ctid IN (
                                SELECT ctid FROM strategy_executions
                                WHERE created_at < %s
                                LIMIT %s
                            )
                        """
                        cursor.execute(query, (cutoff_date, batch_size))
                    elif table_name == 'performance_metrics':
                        query = """
                            DELETE FROM performance_metrics
                            WHERE ctid IN (
                                SELECT ctid FROM performance_metrics
                                WHERE recorded_at < %s
                                LIMIT %s
                            )
                        """
                        cursor.execute(query, (cutoff_date, batch_size))
                    else:
                        raise ValueError(f"Unsupported table: {table_name}")

                    deleted = cursor.rowcount
                    total_deleted += deleted

                    conn.commit()

                    if deleted < batch_size:
                        break

                logger.info(f"删除 {table_name} 归档数据: {deleted} 条")

            logger.info(f"总计删除 {table_name} 归档数据: {total_deleted:,} 条")
            return total_deleted

        except Exception as e:
            logger.error(f"删除归档数据失败 ({table_name}): {e}")
            return 0

    def archive_table(self, table_name: str, cutoff_date: Optional[datetime] = None) -> Dict[str, Any]:
        """归档单个表的数据"""
        if cutoff_date is None:
            retention_days = self.archive_config[table_name]['retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)

        logger.info(f"开始归档表 {table_name} (截止日期: {cutoff_date})")

        result = {
            'table': table_name,
            'cutoff_date': cutoff_date,
            'archived_records': 0,
            'deleted_records': 0,
            'archive_files': [],
            'success': False,
            'error': None
        }

        try:
            # 获取需要归档的数据
            data = self.get_archive_candidates(table_name, cutoff_date)

            if not data:
                logger.info(f"表 {table_name} 没有需要归档的数据")
                result['success'] = True
                return result

            # 分批处理数据
            batch_size = self.archive_config[table_name]['batch_size']
            total_batches = (len(data) + batch_size - 1) // batch_size

            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                batch_num = i // batch_size + 1

                logger.info(f"处理批次 {batch_num}/{total_batches} ({len(batch)} 条记录)")

                # 归档到文件
                archive_file = self.archive_data_to_file(table_name, batch)
                if archive_file:
                    result['archive_files'].append(archive_file)

                    # 上传到S3 (如果配置)
                    if self.s3_enabled:
                        self.upload_to_s3(archive_file, table_name)

                    # 删除已归档的数据
                    deleted = self.remove_archived_data(table_name, cutoff_date, batch_size)
                    result['deleted_records'] += deleted

            result['archived_records'] = len(data)
            result['success'] = True

            logger.info(f"表 {table_name} 归档完成: {len(data)} 条记录")

        except Exception as e:
            logger.error(f"归档表 {table_name} 失败: {e}")
            result['error'] = str(e)

        return result

    def archive_all_tables(self) -> List[Dict[str, Any]]:
        """归档所有表的数据"""
        logger.info("开始归档所有表的数据")

        results = []

        for table_name in self.archive_config.keys():
            result = self.archive_table(table_name)
            results.append(result)

        # 统计结果
        total_archived = sum(r['archived_records'] for r in results if r['success'])
        total_deleted = sum(r['deleted_records'] for r in results if r['success'])

        logger.info(f"归档完成: 总计归档 {total_archived:,} 条记录，删除 {total_deleted:,} 条记录")

        return results

    def cleanup_archive_files(self, days_old: int = 30) -> int:
        """清理本地归档文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleaned = 0

            for filename in os.listdir(self.local_archive_dir):
                file_path = os.path.join(self.local_archive_dir, filename)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                if file_mtime < cutoff_date:
                    os.remove(file_path)
                    cleaned += 1
                    logger.info(f"删除旧归档文件: {filename}")

            logger.info(f"清理完成: 删除了 {cleaned} 个旧归档文件")
            return cleaned

        except Exception as e:
            logger.error(f"清理归档文件失败: {e}")
            return 0

    def get_archive_statistics(self) -> Dict[str, Any]:
        """获取归档统计信息"""
        try:
            stats = {
                'local_files': 0,
                'local_size': 0,
                'tables': {}
            }

            # 统计本地文件
            for filename in os.listdir(self.local_archive_dir):
                file_path = os.path.join(self.local_archive_dir, filename)
                if os.path.isfile(file_path):
                    stats['local_files'] += 1
                    stats['local_size'] += os.path.getsize(file_path)

            # 统计各表的归档数据量
            with self.get_connection() as conn:
                cursor = conn.cursor()

                for table_name in self.archive_config.keys():
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    current_records = cursor.fetchone()[0]

                    stats['tables'][table_name] = {
                        'current_records': current_records,
                        'retention_days': self.archive_config[table_name]['retention_days']
                    }

            return stats

        except Exception as e:
            logger.error(f"获取归档统计信息失败: {e}")
            return {}

# 创建全局归档管理器实例
archive_manager = DataArchiveManager()