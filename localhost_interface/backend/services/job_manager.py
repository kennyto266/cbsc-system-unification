#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
異步任務管理系統
Phase 4: Redis/Celery基礎的參數優化任務隊列管理
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import pickle
import redis.asyncio as redis
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)

class JobStatus(str, Enum):
    """任務狀態"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class JobPriority(str, Enum):
    """任務優先級"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Job:
    """任務數據結構"""
    job_id: str
    job_type: str
    priority: JobPriority
    payload: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    worker_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        data = asdict(self)
        # 轉換datetime為ISO字符串
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat() if value else None
            elif isinstance(value, (JobStatus, JobPriority)):
                data[key] = value.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """從字典創建Job"""
        # 轉換ISO字符串為datetime
        for key in ['created_at', 'started_at', 'completed_at', 'timeout_at']:
            if data.get(key):
                data[key] = datetime.fromisoformat(data[key])

        # 轉換枚舉
        if 'status' in data:
            data['status'] = JobStatus(data['status'])
        if 'priority' in data:
            data['priority'] = JobPriority(data['priority'])

        return cls(**data)

    def to_json(self) -> str:
        """轉換為JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'Job':
        """從JSON字符串創建Job"""
        data = json.loads(json_str)
        return cls.from_dict(data)

class JobManager:
    """異步任務管理器"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False

        # Redis鍵前綴
        self.job_queue_prefix = "job_queue:"
        self.job_data_prefix = "job_data:"
        self.job_status_prefix = "job_status:"
        self.worker_prefix = "worker:"

        # 任務處理器註冊
        self.job_processors: Dict[str, Callable] = {}

        # 統計信息
        self.stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "active_workers": 0
        }

    async def initialize(self):
        """初始化Redis連接"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self.is_connected = True
            logger.info(f"任務管理器已連接到Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Redis連接失敗: {e}")
            self.is_connected = False
            raise

    async def shutdown(self):
        """關閉任務管理器"""
        try:
            if self.redis_client:
                await self.redis_client.close()
                self.is_connected = False
                logger.info("任務管理器已關閉")
        except Exception as e:
            logger.error(f"關閉任務管理器失敗: {e}")

    def register_processor(self, job_type: str, processor: Callable):
        """註冊任務處理器"""
        self.job_processors[job_type] = processor
        logger.info(f"註冊任務處理器: {job_type}")

    async def submit_job(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        timeout_minutes: int = 60,
        max_retries: int = 3,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """提交新任務"""
        try:
            if not self.is_connected:
                raise RuntimeError("Redis未連接")

            if job_type not in self.job_processors:
                raise ValueError(f"未知的任務類型: {job_type}")

            # 創建任務
            job = Job(
                job_id=str(uuid.uuid4()),
                job_type=job_type,
                priority=priority,
                payload=payload,
                created_at=datetime.now(),
                timeout_at=datetime.now() + timedelta(minutes=timeout_minutes),
                max_retries=max_retries,
                user_id=user_id,
                metadata=metadata or {}
            )

            # 存儲任務數據
            await self._store_job(job)

            # 添加到隊列
            await self._enqueue_job(job)

            self.stats["total_jobs"] += 1

            logger.info(f"任務已提交: {job.job_id}, 類型: {job_type}, 優先級: {priority}")
            return job.job_id

        except Exception as e:
            logger.error(f"提交任務失敗: {e}")
            raise

    async def get_job_status(self, job_id: str) -> Optional[Job]:
        """獲取任務狀態"""
        try:
            if not self.is_connected:
                return None

            job_data = await self.redis_client.get(f"{self.job_data_prefix}{job_id}")
            if job_data:
                return Job.from_json(job_data)
            return None

        except Exception as e:
            logger.error(f"獲取任務狀態失敗: {e}")
            return None

    async def cancel_job(self, job_id: str) -> bool:
        """取消任務"""
        try:
            if not self.is_connected:
                return False

            job = await self.get_job_status(job_id)
            if not job:
                return False

            # 只能取消未開始或正在運行的任務
            if job.status in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING]:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()

                await self._store_job(job)
                await self._remove_from_queue(job_id)

                logger.info(f"任務已取消: {job_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"取消任務失敗: {e}")
            return False

    async def retry_job(self, job_id: str) -> bool:
        """重試任務"""
        try:
            if not self.is_connected:
                return False

            job = await self.get_job_status(job_id)
            if not job:
                return False

            if job.status != JobStatus.FAILED or job.retry_count >= job.max_retries:
                return False

            # 重置任務狀態
            job.status = JobStatus.PENDING
            job.progress = 0.0
            job.error = None
            job.retry_count += 1
            job.started_at = None
            job.completed_at = None

            await self._store_job(job)
            await self._enqueue_job(job)

            logger.info(f"任務重試: {job_id}, 重試次數: {job.retry_count}")
            return True

        except Exception as e:
            logger.error(f"重試任務失敗: {e}")
            return False

    async def get_user_jobs(
        self,
        user_id: str,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[Job]:
        """獲取用戶的任務列表"""
        try:
            if not self.is_connected:
                return []

            # 獲取所有任務ID
            all_job_ids = await self.redis_client.keys(f"{self.job_data_prefix}*")
            user_jobs = []

            for job_key in all_job_ids[:limit * 2]:  # 限制搜索範圍
                job_data = await self.redis_client.get(job_key)
                if job_data:
                    job = Job.from_json(job_data)
                    if job.user_id == user_id:
                        if status is None or job.status == status:
                            user_jobs.append(job)
                            if len(user_jobs) >= limit:
                                break

            # 按創建時間排序
            user_jobs.sort(key=lambda x: x.created_at, reverse=True)
            return user_jobs

        except Exception as e:
            logger.error(f"獲取用戶任務失敗: {e}")
            return []

    async def get_queue_stats(self) -> Dict[str, Any]:
        """獲取隊列統計信息"""
        try:
            if not self.is_connected:
                return {}

            stats = {}

            # 各優先級隊列長度
            for priority in JobPriority:
                queue_key = f"{self.job_queue_prefix}{priority.value}"
                queue_length = await self.redis_client.llen(queue_key)
                stats[f"{priority.value}_queue_length"] = queue_length

            # 任務狀態統計
            all_job_keys = await self.redis_client.keys(f"{self.job_data_prefix}*")
            status_counts = {status.value: 0 for status in JobStatus}

            for job_key in all_job_keys[:1000]:  # 限制統計範圍
                job_data = await self.redis_client.get(job_key)
                if job_data:
                    job = Job.from_json(job_data)
                    status_counts[job.status.value] += 1

            stats.update(status_counts)
            stats.update(self.stats)

            return stats

        except Exception as e:
            logger.error(f"獲取隊列統計失敗: {e}")
            return {}

    async def cleanup_old_jobs(self, days: int = 7):
        """清理舊任務"""
        try:
            if not self.is_connected:
                return

            cutoff_date = datetime.now() - timedelta(days=days)
            all_job_keys = await self.redis_client.keys(f"{self.job_data_prefix}*")

            deleted_count = 0
            for job_key in all_job_keys:
                job_data = await self.redis_client.get(job_key)
                if job_data:
                    job = Job.from_json(job_data)
                    if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and
                        job.created_at < cutoff_date):
                        # 刪除任務數據
                        await self.redis_client.delete(job_key)
                        # 從隊列中移除
                        await self._remove_from_queue(job.job_id)
                        deleted_count += 1

            logger.info(f"清理了 {deleted_count} 個舊任務")

        except Exception as e:
            logger.error(f"清理舊任務失敗: {e}")

    async def _store_job(self, job: Job):
        """存儲任務數據"""
        job_key = f"{self.job_data_prefix}{job.job_id}"
        await self.redis_client.set(job_key, job.to_json(), ex=86400 * 30)  # 30天過期

    async def _enqueue_job(self, job: Job):
        """將任務加入隊列"""
        queue_key = f"{self.job_queue_prefix}{job.priority.value}"
        await self.redis_client.lpush(queue_key, job.job_id)

    async def _remove_from_queue(self, job_id: str):
        """從所有隊列中移除任務"""
        for priority in JobPriority:
            queue_key = f"{self.job_queue_prefix}{priority.value}"
            await self.redis_client.lrem(queue_key, 0, job_id)

    async def _get_next_job(self, worker_id: str) -> Optional[Job]:
        """獲取下一個待處理任務"""
        try:
            if not self.is_connected:
                return None

            # 按優先級順序檢查隊列
            priority_order = [JobPriority.CRITICAL, JobPriority.HIGH, JobPriority.NORMAL, JobPriority.LOW]

            for priority in priority_order:
                queue_key = f"{self.job_queue_prefix}{priority.value}"
                job_id = await self.redis_client.brpop(queue_key, timeout=1)

                if job_id:
                    job_id = job_id[1].decode('utf-8') if isinstance(job_id[1], bytes) else job_id[1]
                    job = await self.get_job_status(job_id)

                    if job and job.status == JobStatus.QUEUED:
                        # 更新任務狀態
                        job.status = JobStatus.RUNNING
                        job.started_at = datetime.now()
                        job.worker_id = worker_id
                        await self._store_job(job)

                        logger.info(f"分配任務給工作者 {worker_id}: {job_id}")
                        return job

            return None

        except Exception as e:
            logger.error(f"獲取下一個任務失敗: {e}")
            return None

    async def update_job_progress(self, job_id: str, progress: float, message: Optional[str] = None):
        """更新任務進度"""
        try:
            if not self.is_connected:
                return

            job = await self.get_job_status(job_id)
            if job and job.status == JobStatus.RUNNING:
                job.progress = min(100.0, max(0.0, progress))
                if message:
                    if not job.metadata:
                        job.metadata = {}
                    job.metadata["progress_message"] = message
                await self._store_job(job)

        except Exception as e:
            logger.error(f"更新任務進度失敗: {e}")

    async def complete_job(self, job_id: str, result: Dict[str, Any]):
        """標記任務完成"""
        try:
            if not self.is_connected:
                return

            job = await self.get_job_status(job_id)
            if job:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                job.progress = 100.0
                job.result = result
                await self._store_job(job)

                self.stats["completed_jobs"] += 1
                logger.info(f"任務完成: {job_id}")

        except Exception as e:
            logger.error(f"標記任務完成失敗: {e}")

    async def fail_job(self, job_id: str, error: str):
        """標記任務失敗"""
        try:
            if not self.is_connected:
                return

            job = await self.get_job_status(job_id)
            if job:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
                job.error = error

                # 檢查是否需要重試
                if job.retry_count < job.max_retries:
                    await self.retry_job(job_id)
                else:
                    await self._store_job(job)
                    self.stats["failed_jobs"] += 1

                logger.error(f"任務失敗: {job_id}, 錯誤: {error}")

        except Exception as e:
            logger.error(f"標記任務失敗失敗: {e}")

class JobWorker:
    """任務工作者"""

    def __init__(self, worker_id: str, job_manager: JobManager):
        self.worker_id = worker_id
        self.job_manager = job_manager
        self.is_running = False
        self.current_job: Optional[Job] = None
        self.processed_jobs = 0

    async def start(self):
        """啟動工作者"""
        self.is_running = True
        logger.info(f"工作者啟動: {self.worker_id}")

        while self.is_running:
            try:
                # 獲取下一個任務
                job = await self.job_manager._get_next_job(self.worker_id)
                if job:
                    self.current_job = job
                    await self._process_job(job)
                    self.processed_jobs += 1
                else:
                    # 沒有任務時等待
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"工作者處理錯誤: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        """停止工作者"""
        self.is_running = False
        logger.info(f"工作者停止: {self.worker_id}, 處理任務數: {self.processed_jobs}")

    async def _process_job(self, job: Job):
        """處理任務"""
        try:
            logger.info(f"開始處理任務: {job.job_id}")

            # 檢查超時
            if job.timeout_at and datetime.now() > job.timeout_at:
                await self.job_manager.fail_job(job.job_id, "任務超時")
                return

            # 獲取處理器
            processor = self.job_manager.job_processors.get(job.job_type)
            if not processor:
                await self.job_manager.fail_job(job.job_id, f"未知的任務類型: {job.job_type}")
                return

            # 執行任務
            result = await processor(job.payload, self.worker_id)

            # 標記完成
            await self.job_manager.complete_job(job.job_id, result)
            logger.info(f"任務處理完成: {job.job_id}")

        except Exception as e:
            logger.error(f"任務處理失敗: {job.job_id}, 錯誤: {e}")
            await self.job_manager.fail_job(job.job_id, str(e))

        finally:
            self.current_job = None

# 全局任務管理器實例
job_manager = JobManager()

async def get_job_manager():
    """獲取任務管理器實例"""
    return job_manager

async def create_worker(worker_id: str) -> JobWorker:
    """創建工作者"""
    return JobWorker(worker_id, job_manager)