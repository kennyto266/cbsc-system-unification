"""
Scheduler service module - 处理自动保存定时任务调度
"""

import threading
import time
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import schedule

from services.context_service import ContextService

logger = logging.getLogger(__name__)

class SchedulerService:
    """调度服务类，提供自动保存定时任务调度功能"""

    def __init__(self, context_service: Optional[ContextService] = None):
        """
        初始化调度服务

        Args:
            context_service: 上下文服务实例，如果为None则创建新实例
        """
        self.logger = logging.getLogger(__name__)
        self.context_service = context_service or ContextService()
        self.scheduler_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.auto_save_jobs: Dict[str, schedule.Job] = {}
        self.pending_saves: Dict[str, Dict[str, Any]] = {}

    def start(self) -> None:
        """启动调度服务"""
        try:
            if self.is_running:
                self.logger.warning("调度服务已在运行中")
                return

            self.is_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            self.logger.info("调度服务启动成功")

        except Exception as e:
            self.logger.error(f"启动调度服务失败: {e}")
            self.is_running = False
            raise

    def stop(self) -> None:
        """停止调度服务"""
        try:
            if not self.is_running:
                self.logger.warning("调度服务未在运行")
                return

            self.is_running = False
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)

            # 清理所有定时任务
            schedule.clear()
            self.auto_save_jobs.clear()
            self.logger.info("调度服务停止成功")

        except Exception as e:
            self.logger.error(f"停止调度服务失败: {e}")
            raise

    def schedule_auto_save(self, session_id: str, context_data: Dict[str, Any],
                          interval_minutes: int = 5) -> bool:
        """
        为指定会话安排自动保存任务

        Args:
            session_id: 会话ID
            context_data: 要保存的上下文数据
            interval_minutes: 保存间隔（分钟），默认为5分钟

        Returns:
            bool: 是否成功安排任务
        """
        try:
            if not session_id or not context_data:
                self.logger.error("会话ID和上下文数据不能为空")
                return False

            # 如果已有该会话的自动保存任务，先取消
            if session_id in self.auto_save_jobs:
                self.cancel_auto_save(session_id)

            # 存储待保存的数据
            self.pending_saves[session_id] = context_data

            # 安排定时任务
            job = schedule.every(interval_minutes).minutes.do(
                self._auto_save_job, session_id=session_id
            )

            self.auto_save_jobs[session_id] = job
            self.logger.info(f"为会话 {session_id} 安排了每 {interval_minutes} 分钟的自动保存任务")
            return True

        except Exception as e:
            self.logger.error(f"安排自动保存任务失败: {e}")
            return False

    def cancel_auto_save(self, session_id: str) -> bool:
        """
        取消指定会话的自动保存任务

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功取消任务
        """
        try:
            if session_id in self.auto_save_jobs:
                schedule.cancel_job(self.auto_save_jobs[session_id])
                del self.auto_save_jobs[session_id]

                # 清理待保存数据
                if session_id in self.pending_saves:
                    del self.pending_saves[session_id]

                self.logger.info(f"取消了会话 {session_id} 的自动保存任务")
                return True
            else:
                self.logger.warning(f"会话 {session_id} 没有安排自动保存任务")
                return False

        except Exception as e:
            self.logger.error(f"取消自动保存任务失败: {e}")
            return False

    def update_pending_context(self, session_id: str, context_data: Dict[str, Any]) -> bool:
        """
        更新待保存的上下文数据

        Args:
            session_id: 会话ID
            context_data: 新的上下文数据

        Returns:
            bool: 是否成功更新
        """
        try:
            if session_id in self.pending_saves:
                # 合并更新数据，保留原有元数据
                existing_data = self.pending_saves[session_id]
                existing_data.update(context_data)
                existing_data['updated_at'] = datetime.utcnow().isoformat()
                self.logger.debug(f"更新了会话 {session_id} 的待保存上下文数据")
                return True
            else:
                self.logger.warning(f"会话 {session_id} 没有待保存的数据")
                return False

        except Exception as e:
            self.logger.error(f"更新待保存上下文数据失败: {e}")
            return False

    def get_scheduled_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        获取当前所有已安排的任务信息

        Returns:
            Dict: 任务信息字典
        """
        try:
            jobs_info = {}
            for session_id, job in self.auto_save_jobs.items():
                next_run = job.next_run
                jobs_info[session_id] = {
                    'session_id': session_id,
                    'interval': f"{job.interval}分钟",
                    'next_run': next_run.isoformat() if next_run else None,
                    'has_pending_data': session_id in self.pending_saves
                }
            return jobs_info

        except Exception as e:
            self.logger.error(f"获取任务信息失败: {e}")
            return {}

    def force_save_now(self, session_id: str) -> bool:
        """
        立即执行指定会话的保存操作

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功保存
        """
        try:
            if session_id in self.pending_saves:
                return self._auto_save_job(session_id)
            else:
                self.logger.warning(f"会话 {session_id} 没有待保存的数据")
                return False

        except Exception as e:
            self.logger.error(f"强制保存失败: {e}")
            return False

    def _run_scheduler(self) -> None:
        """调度器运行线程"""
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)  # 每秒检查一次待执行任务

        except Exception as e:
            self.logger.error(f"调度器运行出错: {e}")
            self.is_running = False

    def _auto_save_job(self, session_id: str) -> bool:
        """
        自动保存任务执行函数

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功保存
        """
        try:
            if session_id not in self.pending_saves:
                self.logger.warning(f"会话 {session_id} 没有待保存数据，跳过自动保存")
                return False

            context_data = self.pending_saves[session_id]

            # 提取保存所需参数
            title = context_data.get('title', f'Auto-save Session {session_id}')
            content = context_data.get('content', {})
            user_id = context_data.get('user_id', 'system')
            description = context_data.get('description', f'Auto-saved at {datetime.utcnow().isoformat()}')
            tags = context_data.get('tags', ['auto-save'])
            project_path = context_data.get('project_path')

            # 标记为自动保存
            if not isinstance(tags, list):
                tags = [tags] if tags else []
            if 'auto-save' not in tags:
                tags.append('auto-save')

            # 执行保存
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self.context_service.save_context(
                        title=title,
                        content=content,
                        user_id=user_id,
                        description=description,
                        tags=tags,
                        session_id=session_id,
                        project_path=project_path,
                        auto_save_enabled=True
                    )
                )

                if result:
                    self.logger.info(f"会话 {session_id} 自动保存成功，上下文ID: {result}")
                    # 更新待保存数据中的上下文ID
                    context_data['context_id'] = result
                    context_data['last_saved_at'] = datetime.utcnow().isoformat()
                    return True
                else:
                    self.logger.error(f"会话 {session_id} 自动保存失败")
                    return False

            finally:
                loop.close()

        except Exception as e:
            self.logger.error(f"执行自动保存任务失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        获取调度服务状态

        Returns:
            Dict: 状态信息
        """
        return {
            'is_running': self.is_running,
            'total_jobs': len(self.auto_save_jobs),
            'pending_saves': len(self.pending_saves),
            'next_jobs': [
                {
                    'session_id': session_id,
                    'next_run': job.next_run.isoformat() if job.next_run else None
                }
                for session_id, job in self.auto_save_jobs.items()
            ]
        }

    def cleanup_expired_sessions(self, hours: int = 24) -> int:
        """
        清理超过指定时间的过期会话

        Args:
            hours: 过期时间（小时），默认24小时

        Returns:
            int: 清理的会话数量
        """
        try:
            expired_sessions = []
            current_time = datetime.utcnow()

            for session_id, data in self.pending_saves.items():
                last_updated = data.get('updated_at', data.get('created_at'))
                if last_updated:
                    try:
                        last_updated_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                        if (current_time - last_updated_time).total_seconds() > hours * 3600:
                            expired_sessions.append(session_id)
                    except:
                        # 如果时间解析失败，也视为过期
                        expired_sessions.append(session_id)

            # 清理过期会话
            cleaned_count = 0
            for session_id in expired_sessions:
                if self.cancel_auto_save(session_id):
                    cleaned_count += 1

            if cleaned_count > 0:
                self.logger.info(f"清理了 {cleaned_count} 个过期会话")

            return cleaned_count

        except Exception as e:
            self.logger.error(f"清理过期会话失败: {e}")
            return 0