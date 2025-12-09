"""
任務自動化工作流服務
港股量化交易系統 - 項目管理模組

提供Git集成、狀態通知、依賴檢查、自動化驗收等功能
"""

import json
import logging
import re
import smtplib
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from email.mime.multipart import MimeMultipart
from email.mime.text import MimeText
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GitCommit:
    """Git提交信息"""

    commit_id: str
    author: str
    message: str
    timestamp: datetime
    files_changed: List[str]
    task_ids: List[str]


@dataclass
class NotificationEvent:
    """通知事件"""

    event_type: str  # TASK_CREATED, STATUS_CHANGED, COMPLETED, BLOCKED
    task_id: str
    title: str
    description: str
    assignee: Optional[str]
    priority: str
    status: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class TaskAutomationService:
    """
    任務自動化工作流服務

    功能包括:
    - Git提交自動關聯任務
    - 依賴關係檢查
    - 狀態變更通知
    - 自動驗收機制
    - 進度報告生成
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化自動化服務

        Args:
            config: 配置字典，包含SMTP、Git等配置
        """
        self.config = config or {}
        self.notification_listeners = []

        # 任務ID模式 (匹配格式: TASK - XXX 或 #XXX)
        self.task_id_pattern = re.compile(r"(?:TASK-|#)(\d{3})")

        # Git配置
        self.git_config = {
            "auto_link": self.config.get("auto_link_commits", True),
            "branch_pattern": self.config.get(
                "branch_pattern", r"^(feature|bugfix|hotfix)/"
            ),
            "max_commits_per_task": self.config.get("max_commits_per_task", 50),
        }

        # 通知配置
        self.notification_config = {
            "email_enabled": self.config.get("email_enabled", False),
            "smtp_server": self.config.get("smtp_server"),
            "smtp_port": self.config.get("smtp_port", 587),
            "smtp_user": self.config.get("smtp_user"),
            "smtp_password": self.config.get("smtp_password"),
            "notification_email": self.config.get("notification_email"),
            "slack_webhook": self.config.get("slack_webhook"),
        }

    # ==================== Git集成 ====================

    def extract_task_ids_from_commit_message(self, message: str) -> List[str]:
        """
        從Git提交信息中提取任務ID

        Args:
            message: Git提交信息

        Returns:
            匹配的任務ID列表
        """
        matches = self.task_id_pattern.findall(message)
        return [f"TASK-{match}" for match in matches]

    def parse_git_log(self, since: Optional[datetime] = None) -> List[GitCommit]:
        """
        解析Git提交日誌

        Args:
            since: 起始時間，如果為None則獲取所有提交

        Returns:
            Git提交列表
        """
        try:
            # 構建git log命令
            cmd = ["git", "log", "--pretty=format:%H|%an|%ai|%s", "--name - status"]

            if since:
                cmd.append(f"--since={since.isoformat()}")

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commits = []

            # 解析輸出
            current_commit = None
            for line in result.stdout.split("\n"):
                if "|" in line and len(line.split("|")) == 4:
                    parts = line.split("|")
                    current_commit = GitCommit(
                        commit_id=parts[0],
                        author=parts[1],
                        timestamp=datetime.fromisoformat(parts[2]),
                        message=parts[3],
                        files_changed=[],
                        task_ids=self.extract_task_ids_from_commit_message(parts[3]),
                    )
                    commits.append(current_commit)
                elif line and line.startswith(("A\t", "M\t", "D\t")) and current_commit:
                    current_commit.files_changed.append(line.split("\t", 1)[1])

            logger.info(f"解析到 {len(commits)} 個Git提交")
            return commits

        except subprocess.CalledProcessError as e:
            logger.error(f"Git命令執行失敗: {e}")
            return []
        except Exception as e:
            logger.error(f"解析Git日誌失敗: {e}")
            return []

    def link_commits_to_tasks(self, commits: List[GitCommit]) -> Dict[str, List[str]]:
        """
        將Git提交關聯到任務

        Args:
            commits: Git提交列表

        Returns:
            任務ID到提交ID的映射
        """
        task_commits = {}

        for commit in commits:
            for task_id in commit.task_ids:
                if task_id not in task_commits:
                    task_commits[task_id] = []

                # 檢查是否已存在
                if commit.commit_id not in task_commits[task_id]:
                    task_commits[task_id].append(commit.commit_id)

                    # 記錄到任務元數據
                    self._update_task_metadata(task_id, "git_commits", commit.commit_id)

        logger.info(f"關聯了 {len(task_commits)} 個任務到Git提交")
        return task_commits

    def _update_task_metadata(self, task_id: str, key: str, value: Any):
        """
        更新任務元數據

        Args:
            task_id: 任務ID
            key: 元數據鍵
            value: 元數據值
        """
        # TODO: 實現數據庫更新邏輯
        # 這裡應該更新任務的metadata字段
        pass

    # ==================== 依賴檢查 ====================

    def check_task_dependencies(
        self, task_id: str, dependencies: List[str]
    ) -> Dict[str, Any]:
        """
        檢查任務依賴關係

        Args:
            task_id: 任務ID
            dependencies: 依賴任務ID列表

        Returns:
            依賴檢查結果
        """
        result = {
            "task_id": task_id,
            "all_resolved": True,
            "resolved_dependencies": [],
            "unresolved_dependencies": [],
            "blocked_dependencies": [],
        }

        for dep_id in dependencies:
            dep_status = self._get_task_status(dep_id)

            if dep_status == "DONE":
                result["resolved_dependencies"].append(dep_id)
            elif dep_status in ["BLOCKED", "TODO"]:
                result["unresolved_dependencies"].append(dep_id)
                result["all_resolved"] = False
            elif dep_status in ["IN_PROGRESS", "REVIEW"]:
                result["blocked_dependencies"].append(dep_id)
                result["all_resolved"] = False

        # 如果有未解決的依賴，發送通知
        if not result["all_resolved"]:
            self._notify_dependency_blocked(task_id, result)

        return result

    def _get_task_status(self, task_id: str) -> str:
        """
        獲取任務狀態

        Args:
            task_id: 任務ID

        Returns:
            任務狀態字符串
        """
        # TODO: 從數據庫查詢任務狀態
        # 這裡應該從數據庫獲取任務的實際狀態
        return "TODO"

    def _notify_dependency_blocked(self, task_id: str, check_result: Dict[str, Any]):
        """
        發送依賴阻塞通知

        Args:
            task_id: 任務ID
            check_result: 依賴檢查結果
        """
        # TODO: 實現通知邏輯
        logger.warning(f"任務 {task_id} 因依賴未完成而被阻塞")

    # ==================== 狀態通知 ====================

    def add_notification_listener(self, listener):
        """
        添加通知監聽器

        Args:
            listener: 回調函數，接收NotificationEvent參數
        """
        self.notification_listeners.append(listener)

    def send_notification(self, event: NotificationEvent):
        """
        發送通知

        Args:
            event: 通知事件
        """
        logger.info(f"發送通知: {event.event_type} - {event.task_id}")

        # 調用所有監聽器
        for listener in self.notification_listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"通知監聽器執行失敗: {e}")

        # 發送郵件通知
        if self.notification_config["email_enabled"]:
            self._send_email_notification(event)

    def _send_email_notification(self, event: NotificationEvent):
        """
        發送郵件通知

        Args:
            event: 通知事件
        """
        try:
            if not all(
                [
                    self.notification_config["smtp_server"],
                    self.notification_config["smtp_user"],
                    self.notification_config["notification_email"],
                ]
            ):
                logger.warning("郵件配置不完整，跳過郵件通知")
                return

            msg = MimeMultipart()
            msg["From"] = self.notification_config["smtp_user"]
            msg["To"] = self.notification_config["notification_email"]
            msg["Subject"] = f"[任務通知] {event.task_id} - {event.title}"

            body = """
任務狀態變更通知

任務ID: {event.task_id}
標題: {event.title}
狀態: {event.status}
優先級: {event.priority}
分配給: {event.assignee or '未分配'}

時間: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{description}
            """

            msg.attach(MimeText(body, "plain", "utf - 8"))

            server = smtplib.SMTP(
                self.notification_config["smtp_server"],
                self.notification_config["smtp_port"],
            )
            server.starttls()
            server.login(
                self.notification_config["smtp_user"],
                self.notification_config["smtp_password"],
            )
            server.send_message(msg)
            server.quit()

            logger.info("郵件通知發送成功")

        except Exception as e:
            logger.error(f"發送郵件通知失敗: {e}")

    # ==================== 自動驗收 ====================

    def validate_task_completion(
        self, task_id: str, acceptance_criteria: List[str]
    ) -> Dict[str, Any]:
        """
        驗證任務完成情況

        Args:
            task_id: 任務ID
            acceptance_criteria: 驗收標準列表

        Returns:
            驗證結果
        """
        result = {
            "task_id": task_id,
            "all_passed": True,
            "passed_criteria": [],
            "failed_criteria": [],
        }

        for criterion in acceptance_criteria:
            # 這裡實現具體的驗證邏輯
            # 例如：檢查文件是否存在、測試是否通過等
            is_valid = self._check_single_criterion(task_id, criterion)

            if is_valid:
                result["passed_criteria"].append(criterion)
            else:
                result["failed_criteria"].append(criterion)
                result["all_passed"] = False

        # 如果所有驗收標準都通過，自動完成任務
        if result["all_passed"]:
            self._auto_complete_task(task_id)

        return result

    def _check_single_criterion(self, task_id: str, criterion: str) -> bool:
        """
        檢查單個驗收標準

        Args:
            task_id: 任務ID
            criterion: 驗收標準

        Returns:
            是否通過
        """
        # TODO: 實現具體的驗收邏輯
        # 例如：
        # - 檢查特定文件是否存在
        # - 運行測試用例
        # - 檢查代碼覆蓋率
        # - 驗證API端點
        return True

    def _auto_complete_task(self, task_id: str):
        """
        自動完成任務

        Args:
            task_id: 任務ID
        """
        # TODO: 實現自動完成邏輯
        # 更新數據庫中任務狀態為DONE
        logger.info(f"自動完成任務: {task_id}")

    # ==================== 進度報告 ====================

    def generate_daily_progress_report(
        self, date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        生成每日進度報告

        Args:
            date: 報告日期，默認為今天

        Returns:
            報告數據
        """
        if date is None:
            date = datetime.now()

        # TODO: 從數據庫查詢任務統計
        report = {
            "date": date.strftime("%Y-%m-%d"),
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "blocked_tasks": 0,
            "new_tasks": 0,
            "completion_rate": 0.0,
            "top_performers": [],
            "blockers": [],
        }

        return report

    def generate_sprint_report(self, sprint_id: str) -> Dict[str, Any]:
        """
        生成Sprint報告

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint報告數據
        """
        # TODO: 實現Sprint報告生成
        report = {
            "sprint_id": sprint_id,
            "planned_hours": 0,
            "completed_hours": 0,
            "velocity": 0.0,
            "burndown_data": [],
            "completion_rate": 0.0,
            "issues": [],
        }

        return report

    # ==================== Webhook支持 ====================

    def handle_git_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理Git webhook

        Args:
            payload: Webhook payload

        Returns:
            處理結果
        """
        result = {"processed": False, "linked_tasks": [], "errors": []}

        try:
            commits = payload.get("commits", [])
            for commit in commits:
                message = commit.get("message", "")
                task_ids = self.extract_task_ids_from_commit_message(message)

                if task_ids:
                    result["linked_tasks"].extend(task_ids)

                    # 更新任務元數據
                    for task_id in task_ids:
                        self._update_task_metadata(
                            task_id, "last_commit", commit.get("id", "")
                        )

            result["processed"] = True

        except Exception as e:
            result["errors"].append(str(e))
            logger.error(f"處理Git webhook失敗: {e}")

        return result

    def handle_ci_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理CI webhook (如Jenkins, GitHub Actions等)

        Args:
            payload: Webhook payload

        Returns:
            處理結果
        """
        result = {"processed": False, "affected_tasks": [], "actions": []}

        try:
            # 提取任務ID
            task_ids = []
            if "head_commit" in payload:
                message = payload["head_commit"].get("message", "")
                task_ids = self.extract_task_ids_from_commit_message(message)

            # 檢查測試結果
            test_result = payload.get("test_result", {})

            if test_result.get("status") == "passed":
                # 測試通過，嘗試自動驗收
                for task_id in task_ids:
                    result["actions"].append(f"Auto - completed: {task_id}")
            elif test_result.get("status") == "failed":
                # 測試失敗，標記任務為失敗
                for task_id in task_ids:
                    result["actions"].append(f"Marked as failed: {task_id}")

            result["affected_tasks"] = task_ids
            result["processed"] = True

        except Exception as e:
            logger.error(f"處理CI webhook失敗: {e}")

        return result
