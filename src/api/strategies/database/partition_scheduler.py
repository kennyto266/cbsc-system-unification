"""
分区调度器
Partition Scheduler

负责自动创建和管理数据库分区
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import schedule
import time
from .partition_manager import partition_manager, PartitionConfig

logger = logging.getLogger('partition_scheduler')

class PartitionScheduler:
    """分区调度器"""

    def __init__(self):
        """初始化分区调度器"""
        self.running = False
        self.scheduler_tasks = []

    def setup_schedules(self):
        """设置调度任务"""
        # 每天凌晨2点检查并创建新分区
        schedule.every().day.at("02:00").do(self.check_and_create_partitions)

        # 每周日凌晨3点清理旧分区
        schedule.every().sunday.at("03:00").do(self.cleanup_old_partitions)

        # 每小时检查分区状态
        schedule.every().hour.do(self.monitor_partition_health)

        logger.info("分区调度任务已设置")

    def check_and_create_partitions(self):
        """检查并创建需要的分区"""
        logger.info("开始检查分区需求...")

        try:
            current_date = datetime.now()

            # 检查每个表的分区需求
            for table_name, config in partition_manager.partitions_config.items():
                self._ensure_table_partitions(table_name, config, current_date)

            logger.info("分区检查完成")

        except Exception as e:
            logger.error(f"检查分区失败: {e}")

    def _ensure_table_partitions(self, table_name: str, config: PartitionConfig, current_date: datetime):
        """确保表有足够的分区"""
        try:
            # 获取现有分区
            existing_partitions = self._get_existing_partitions(table_name)

            # 计算需要创建的分区
            needed_partitions = self._calculate_needed_partitions(
                config, current_date, existing_partitions
            )

            # 创建缺失的分区
            for partition_info in needed_partitions:
                success = self._create_partition(table_name, partition_info)
                if success:
                    logger.info(f"✅ 创建分区: {partition_info['name']}")
                else:
                    logger.error(f"❌ 创建分区失败: {partition_info['name']}")

        except Exception as e:
            logger.error(f"确保表 {table_name} 分区失败: {e}")

    def _get_existing_partitions(self, table_name: str) -> List[str]:
        """获取现有分区列表"""
        try:
            partitions = partition_manager.get_partition_info(table_name)
            return [p['name'] for p in partitions if p['name'].startswith(f"{table_name}_")]
        except Exception as e:
            logger.error(f"获取现有分区失败: {e}")
            return []

    def _calculate_needed_partitions(self, config: PartitionConfig,
                                   current_date: datetime,
                                   existing_partitions: List[str]) -> List[Dict]:
        """计算需要创建的分区"""
        needed_partitions = []

        # 计算未来需要创建的分区
        for i in range(config.create_future_partitions):
            if config.partition_interval == 'monthly':
                partition_date = current_date.replace(day=1) + timedelta(days=32*i)
                partition_start = partition_date.replace(day=1)
                partition_name = f"{config.table_name}_{partition_start.strftime('%Y_%m')}"
            elif config.partition_interval == 'daily':
                partition_date = current_date + timedelta(days=i)
                partition_start = partition_date.replace(hour=0, minute=0, second=0, microsecond=0)
                partition_name = f"{config.table_name}_{partition_start.strftime('%Y%m%d')}"
            else:
                continue

            # 检查分区是否已存在
            if partition_name not in existing_partitions:
                needed_partitions.append({
                    'name': partition_name,
                    'start_date': partition_start,
                    'interval': config.partition_interval
                })

        return needed_partitions

    def _create_partition(self, table_name: str, partition_info: Dict) -> bool:
        """创建单个分区"""
        try:
            start_date = partition_info['start_date']
            interval = partition_info['interval']

            # 计算结束日期
            if interval == 'monthly':
                if start_date.month == 12:
                    end_date = datetime(start_date.year + 1, 1, 1)
                else:
                    end_date = datetime(start_date.year, start_date.month + 1, 1)
            elif interval == 'daily':
                end_date = start_date + timedelta(days=1)
            else:
                logger.error(f"不支持的分区间隔: {interval}")
                return False

            partition_name = partition_info['name']

            with partition_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF {table_name}
                    FOR VALUES FROM ('{start_date}') TO ('{end_date}');
                """)

                conn.commit()
                logger.info(f"成功创建分区: {partition_name}")
                return True

        except Exception as e:
            logger.error(f"创建分区 {partition_info['name']} 失败: {e}")
            return False

    def cleanup_old_partitions(self):
        """清理旧分区"""
        logger.info("开始清理旧分区...")

        try:
            total_dropped = 0

            for table_name, config in partition_manager.partitions_config.items():
                dropped = partition_manager.drop_old_partitions(
                    table_name, config.retention_period
                )
                total_dropped += dropped

                if dropped > 0:
                    logger.info(f"✅ 表 {table_name}: 清理了 {dropped} 个旧分区")

            logger.info(f"旧分区清理完成，总计清理 {total_dropped} 个分区")

        except Exception as e:
            logger.error(f"清理旧分区失败: {e}")

    def monitor_partition_health(self):
        """监控分区健康状态"""
        try:
            # 检查分区大小和使用情况
            for table_name in partition_manager.partitions_config.keys():
                self._check_table_partition_health(table_name)

        except Exception as e:
            logger.error(f"监控分区健康状态失败: {e}")

    def _check_table_partition_health(self, table_name: str):
        """检查单个表的分区健康状态"""
        try:
            partitions = partition_manager.get_partition_info(table_name)

            if not partitions:
                logger.warning(f"表 {table_name} 没有找到分区")
                return

            # 检查分区数量
            current_month = datetime.now().strftime('%Y_%m')
            current_partitions = [p for p in partitions if current_month in p['name']]

            if not current_partitions:
                logger.warning(f"表 {table_name} 缺少当前月份分区: {current_month}")

            # 检查分区大小（这里可以添加更复杂的健康检查逻辑）
            total_size = 0
            for partition in partitions:
                # 简单的大小检查，可以扩展
                if 'MB' in partition['size'] or 'GB' in partition['size']:
                    size_str = partition['size'].replace('MB', '').replace('GB', '')
                    size_value = float(size_str)
                    if 'GB' in partition['size']:
                        size_value *= 1024
                    total_size += size_value

            if total_size > 1024:  # 超过1GB
                logger.info(f"表 {table_name} 总大小: {total_size:.1f}MB")

        except Exception as e:
            logger.error(f"检查表 {table_name} 分区健康状态失败: {e}")

    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("分区调度器已经在运行")
            return

        self.running = True
        self.setup_schedules()

        logger.info("分区调度器已启动")

        # 立即执行一次检查
        self.check_and_create_partitions()

        # 运行调度循环
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在停止调度器...")
            self.stop()

    def stop(self):
        """停止调度器"""
        self.running = False
        schedule.clear()
        logger.info("分区调度器已停止")

    async def start_async(self):
        """异步启动调度器"""
        import asyncio

        if self.running:
            logger.warning("分区调度器已经在运行")
            return

        self.running = True

        # 在后台任务中运行调度器
        async def scheduler_loop():
            while self.running:
                self.check_and_create_partitions()
                await asyncio.sleep(3600)  # 每小时检查一次

        # 启动后台任务
        task = asyncio.create_task(scheduler_loop())
        self.scheduler_tasks.append(task)

        logger.info("异步分区调度器已启动")

        # 立即执行一次检查
        self.check_and_create_partitions()

    async def stop_async(self):
        """异步停止调度器"""
        self.running = False

        # 取消所有后台任务
        for task in self.scheduler_tasks:
            task.cancel()

        # 等待任务完成
        if self.scheduler_tasks:
            await asyncio.gather(*self.scheduler_tasks, return_exceptions=True)

        self.scheduler_tasks.clear()
        logger.info("异步分区调度器已停止")

# 创建全局分区调度器实例
partition_scheduler = PartitionScheduler()