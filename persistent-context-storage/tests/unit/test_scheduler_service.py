"""
Unit tests for SchedulerService
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from services.scheduler_service import SchedulerService


class TestSchedulerService:
    """Test cases for SchedulerService"""

    def test_init_default(self):
        """Test SchedulerService initialization with default parameters."""
        scheduler = SchedulerService()
        assert scheduler.context_service is not None
        assert scheduler.is_running is False
        assert scheduler.scheduler_thread is None
        assert scheduler.auto_save_jobs == {}
        assert scheduler.pending_saves == {}

    def test_init_with_context_service(self):
        """Test SchedulerService initialization with custom context service."""
        mock_context_service = Mock()
        scheduler = SchedulerService(context_service=mock_context_service)
        assert scheduler.context_service is mock_context_service

    def test_start_scheduler(self, scheduler_service):
        """Test starting the scheduler service."""
        scheduler_service.start()

        assert scheduler_service.is_running is True
        assert scheduler_service.scheduler_thread is not None
        assert scheduler_service.scheduler_thread.is_alive()

        # Clean up
        scheduler_service.stop()

    def test_start_already_running(self, scheduler_service):
        """Test starting scheduler when it's already running."""
        scheduler_service.start()

        # Try to start again
        scheduler_service.start()

        assert scheduler_service.is_running is True

        # Clean up
        scheduler_service.stop()

    def test_stop_scheduler(self, scheduler_service):
        """Test stopping the scheduler service."""
        # Start first
        scheduler_service.start()
        assert scheduler_service.is_running is True

        # Stop it
        scheduler_service.stop()

        assert scheduler_service.is_running is False

    def test_stop_not_running(self, scheduler_service):
        """Test stopping scheduler when it's not running."""
        # Should not raise an error
        scheduler_service.stop()
        assert scheduler_service.is_running is False

    def test_schedule_auto_save(self, scheduler_service, sample_context_data):
        """Test scheduling auto save for a session."""
        session_id = "test_session_123"
        interval_minutes = 1

        result = scheduler_service.schedule_auto_save(
            session_id=session_id,
            context_data=sample_context_data,
            interval_minutes=interval_minutes
        )

        assert result is True
        assert session_id in scheduler_service.auto_save_jobs
        assert session_id in scheduler_service.pending_saves
        assert scheduler_service.pending_saves[session_id] == sample_context_data

        # Clean up
        scheduler_service.cancel_auto_save(session_id)

    def test_schedule_auto_save_empty_session_id(self, scheduler_service):
        """Test scheduling auto save with empty session ID."""
        result = scheduler_service.schedule_auto_save(
            session_id="",
            context_data={"test": "data"}
        )

        assert result is False

    def test_schedule_auto_save_empty_context_data(self, scheduler_service):
        """Test scheduling auto save with empty context data."""
        result = scheduler_service.schedule_auto_save(
            session_id="test_session",
            context_data=None
        )

        assert result is False

    def test_schedule_auto_save_replace_existing(self, scheduler_service, sample_context_data):
        """Test that scheduling auto save replaces existing job for same session."""
        session_id = "test_session"

        # Schedule first job
        scheduler_service.schedule_auto_save(
            session_id=session_id,
            context_data={"initial": "data"},
            interval_minutes=5
        )

        first_job = scheduler_service.auto_save_jobs[session_id]

        # Schedule second job for same session
        new_data = {"updated": "data"}
        scheduler_service.schedule_auto_save(
            session_id=session_id,
            context_data=new_data,
            interval_minutes=2
        )

        # Should have replaced the job
        assert session_id in scheduler_service.auto_save_jobs
        assert scheduler_service.auto_save_jobs[session_id] != first_job
        assert scheduler_service.pending_saves[session_id] == new_data

        # Clean up
        scheduler_service.cancel_auto_save(session_id)

    def test_cancel_auto_save(self, scheduler_service, sample_context_data):
        """Test cancelling auto save for a session."""
        session_id = "test_session"

        # Schedule first
        scheduler_service.schedule_auto_save(
            session_id=session_id,
            context_data=sample_context_data
        )

        assert session_id in scheduler_service.auto_save_jobs

        # Cancel it
        result = scheduler_service.cancel_auto_save(session_id)

        assert result is True
        assert session_id not in scheduler_service.auto_save_jobs
        assert session_id not in scheduler_service.pending_saves

    def test_cancel_auto_save_nonexistent(self, scheduler_service):
        """Test cancelling auto save for non-existent session."""
        result = scheduler_service.cancel_auto_save("nonexistent_session")
        assert result is False

    def test_update_pending_context(self, scheduler_service):
        """Test updating pending context data."""
        session_id = "test_session"
        initial_data = {"title": "Initial", "content": {"test": "data"}}
        updated_data = {"content": {"updated": "content"}, "tags": ["test"]}

        # Schedule first
        scheduler_service.schedule_auto_save(
            session_id=session_id,
            context_data=initial_data
        )

        # Update the data
        result = scheduler_service.update_pending_context(session_id, updated_data)

        assert result is True

        # Check that data was merged
        pending = scheduler_service.pending_saves[session_id]
        assert pending["title"] == "Initial"  # Should remain
        assert pending["content"]["updated"] == "content"  # Should be updated
        assert pending["tags"] == ["test"]  # Should be added
        assert "updated_at" in pending  # Timestamp should be added

        # Clean up
        scheduler_service.cancel_auto_save(session_id)

    def test_update_pending_context_nonexistent(self, scheduler_service):
        """Test updating pending context for non-existent session."""
        result = scheduler_service.update_pending_context(
            "nonexistent_session",
            {"test": "data"}
        )

        assert result is False

    def test_get_scheduled_jobs(self, scheduler_service):
        """Test getting information about scheduled jobs."""
        session1 = "session1"
        session2 = "session2"

        # Schedule jobs
        scheduler_service.schedule_auto_save(
            session_id=session1,
            context_data={"test": "data1"},
            interval_minutes=5
        )
        scheduler_service.schedule_auto_save(
            session_id=session2,
            context_data={"test": "data2"},
            interval_minutes=10
        )

        # Get jobs info
        jobs_info = scheduler_service.get_scheduled_jobs()

        assert len(jobs_info) == 2
        assert session1 in jobs_info
        assert session2 in jobs_info

        # Check job info structure
        for session_id, info in jobs_info.items():
            assert 'session_id' in info
            assert 'interval' in info
            assert 'next_run' in info
            assert 'has_pending_data' in info
            assert info['session_id'] == session_id
            assert info['has_pending_data'] is True

        # Clean up
        scheduler_service.cancel_auto_save(session1)
        scheduler_service.cancel_auto_save(session2)

    def test_get_scheduled_jobs_empty(self, scheduler_service):
        """Test getting scheduled jobs when none exist."""
        jobs_info = scheduler_service.get_scheduled_jobs()
        assert jobs_info == {}

    @patch('services.scheduler_service.ContextService')
    def test_force_save_now(self, mock_context_service_class, scheduler_service):
        """Test forcing immediate save for a session."""
        # Setup mock
        mock_context_service = AsyncMock()
        mock_context_service_class.return_value = mock_context_service
        mock_context_service.save_context.return_value = "context_id_123"

        # Recreate scheduler with mocked context service
        scheduler = SchedulerService(context_service=mock_context_service)

        session_id = "test_session"
        context_data = {
            "title": "Test Context",
            "content": {"test": "data"},
            "user_id": "test_user",
            "description": "Test description"
        }

        # Schedule auto save
        scheduler.schedule_auto_save(session_id, context_data)

        # Force save now
        result = scheduler.force_save_now(session_id)

        assert result is True

        # Verify save was called with correct parameters
        mock_context_service.save_context.assert_called_once()
        call_args = mock_context_service.save_context.call_args[1]

        assert call_args['title'] == "Test Context"
        assert call_args['content'] == {"test": "data"}
        assert call_args['user_id'] == "test_user"
        assert call_args['session_id'] == session_id
        assert call_args['auto_save_enabled'] is True
        assert "auto-save" in call_args['tags']

        # Clean up
        scheduler.cancel_auto_save(session_id)

    def test_force_save_now_no_pending_data(self, scheduler_service):
        """Test forcing save when no pending data exists."""
        result = scheduler_service.force_save_now("nonexistent_session")
        assert result is False

    def test_get_status(self, scheduler_service):
        """Test getting scheduler service status."""
        # Initially stopped
        status = scheduler_service.get_status()
        assert status['is_running'] is False
        assert status['total_jobs'] == 0
        assert status['pending_saves'] == 0
        assert status['next_jobs'] == []

        # Start scheduler
        scheduler_service.start()
        status = scheduler_service.get_status()
        assert status['is_running'] is True

        # Schedule a job
        scheduler_service.schedule_auto_save(
            session_id="test_session",
            context_data={"test": "data"},
            interval_minutes=5
        )

        status = scheduler_service.get_status()
        assert status['is_running'] is True
        assert status['total_jobs'] == 1
        assert status['pending_saves'] == 1
        assert len(status['next_jobs']) == 1

        # Clean up
        scheduler_service.stop()

    def test_cleanup_expired_sessions(self, scheduler_service):
        """Test cleaning up expired sessions."""
        # Create sessions with different timestamps
        old_timestamp = (datetime.utcnow() - timedelta(hours=25)).isoformat()
        recent_timestamp = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        old_data = {"created_at": old_timestamp}
        recent_data = {"created_at": recent_timestamp}

        # Schedule sessions
        scheduler_service.schedule_auto_save("old_session", old_data)
        scheduler_service.schedule_auto_save("recent_session", recent_data)

        assert len(scheduler_service.auto_save_jobs) == 2
        assert len(scheduler_service.pending_saves) == 2

        # Clean up sessions older than 24 hours
        cleaned_count = scheduler_service.cleanup_expired_sessions(hours=24)

        assert cleaned_count == 1
        assert "old_session" not in scheduler_service.auto_save_jobs
        assert "old_session" not in scheduler_service.pending_saves
        assert "recent_session" in scheduler_service.auto_save_jobs
        assert "recent_session" in scheduler_service.pending_saves

        # Clean up
        scheduler_service.cancel_auto_save("recent_session")

    def test_cleanup_expired_sessions_none(self, scheduler_service):
        """Test cleaning up when no sessions exist."""
        cleaned_count = scheduler_service.cleanup_expired_sessions()
        assert cleaned_count == 0

    def test_cleanup_expired_sessions_all_recent(self, scheduler_service):
        """Test cleaning up when all sessions are recent."""
        recent_data = {"created_at": datetime.utcnow().isoformat()}
        scheduler_service.schedule_auto_save("session1", recent_data)
        scheduler_service.schedule_auto_save("session2", recent_data)

        cleaned_count = scheduler_service.cleanup_expired_sessions(hours=24)
        assert cleaned_count == 0

        # Sessions should still exist
        assert len(scheduler_service.auto_save_jobs) == 2

        # Clean up
        scheduler_service.cancel_auto_save("session1")
        scheduler_service.cancel_auto_save("session2")

    def test_auto_save_job_tags_handling(self, scheduler_service):
        """Test that auto-save job handles tags correctly."""
        session_id = "test_session"
        context_data = {
            "title": "Test",
            "content": {"test": "data"},
            "tags": ["existing", "tags"]
        }

        scheduler_service.schedule_auto_save(session_id, context_data)

        # The auto-save job should add 'auto-save' tag
        # We can't directly test this without running the job, but we can
        # verify the data structure is prepared correctly
        assert "tags" in scheduler_service.pending_saves[session_id]

        # Clean up
        scheduler_service.cancel_auto_save(session_id)

    def test_scheduler_thread_safety(self, scheduler_service):
        """Test that scheduler operations are thread-safe."""
        session_id = "concurrent_test"
        context_data = {"test": "data"}

        def schedule_and_cancel():
            """Schedule and cancel in a loop."""
            for i in range(10):
                scheduler_service.schedule_auto_save(
                    f"{session_id}_{i}",
                    {**context_data, "iteration": i}
                )
                time.sleep(0.01)  # Small delay
                scheduler_service.cancel_auto_save(f"{session_id}_{i}")

        def get_status():
            """Get status repeatedly."""
            for _ in range(50):
                scheduler_service.get_status()
                time.sleep(0.001)

        # Run operations in parallel
        schedule_thread = threading.Thread(target=schedule_and_cancel)
        status_thread = threading.Thread(target=get_status)

        schedule_thread.start()
        status_thread.start()

        schedule_thread.join(timeout=5)
        status_thread.join(timeout=5)

        # Should not have any jobs remaining
        assert len(scheduler_service.auto_save_jobs) == 0
        assert len(scheduler_service.pending_saves) == 0

    def test_scheduler_with_different_intervals(self, scheduler_service):
        """Test scheduling jobs with different intervals."""
        # Schedule jobs with different intervals
        scheduler_service.schedule_auto_save("session1", {"data": "1"}, interval_minutes=1)
        scheduler_service.schedule_auto_save("session2", {"data": "2"}, interval_minutes=5)
        scheduler_service.schedule_auto_save("session3", {"data": "3"}, interval_minutes=10)

        jobs_info = scheduler_service.get_scheduled_jobs()

        assert len(jobs_info) == 3
        assert "1分钟" in jobs_info["session1"]["interval"]
        assert "5分钟" in jobs_info["session2"]["interval"]
        assert "10分钟" in jobs_info["session3"]["interval"]

        # Clean up
        scheduler_service.cancel_auto_save("session1")
        scheduler_service.cancel_auto_save("session2")
        scheduler_service.cancel_auto_save("session3")