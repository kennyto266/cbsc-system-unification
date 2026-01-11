"""
Integration tests for API endpoints
Test API transactions and data consistency across frontend and backend services
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import shutil
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from fastapi.testclient import TestClient
from fastapi import FastAPI
import httpx

from main import app
from services.context_service import ContextService
from services.scheduler_service import SchedulerService
from services.permission_service import PermissionService
from config.database import get_database_session, init_sqlalchemy_database
from models.context import Context, ContextTag
from models.user import User, Team, Permission


@pytest.fixture
def temp_api_workspace() -> Path:
    """Create a temporary workspace for API integration tests"""
    workspace = Path(tempfile.mkdtemp())

    # Create required directories
    (workspace / "data").mkdir(exist_ok=True)
    (workspace / "storage").mkdir(exist_ok=True)
    (workspace / "search_index").mkdir(exist_ok=True)
    (workspace / "logs").mkdir(exist_ok=True)

    yield workspace

    # Cleanup
    shutil.rmtree(workspace, ignore_errors=True)


@pytest.fixture
async def test_app_with_db(temp_api_workspace: Path):
    """Create a test FastAPI app with temporary database"""
    # Set environment variables for test
    os.environ["DATABASE_URL"] = str(temp_api_workspace / "test_api_contexts.db")
    os.environ["STORAGE_PATH"] = str(temp_api_workspace / "storage")
    os.environ["SEARCH_INDEX_PATH"] = str(temp_api_workspace / "search_index")
    os.environ["AUTO_SAVE_INTERVAL"] = "60"  # 1 minute for tests
    os.environ["COMPRESSION_LEVEL"] = "6"

    # Initialize database
    await init_sqlalchemy_database()

    # Create a test app instance
    from main import app as main_app
    yield main_app


@pytest.fixture
def test_client(test_app_with_db):
    """Create a test client for the FastAPI app"""
    return TestClient(test_app_with_db)


@pytest.fixture
def sample_api_contexts() -> List[Dict[str, Any]]:
    """Sample context data for API testing"""
    return [
        {
            "title": "API Test Context 1",
            "content": {
                "messages": [
                    {"role": "user", "content": "Test message 1"},
                    {"role": "assistant", "content": "Test response 1"}
                ],
                "metadata": {"test": True, "api": True}
            },
            "description": "First test context for API",
            "tags": ["test", "api", "first"],
            "session_id": "api_session_001",
            "project_path": "/projects/api_test",
            "user_id": "api_user_001"
        },
        {
            "title": "API Test Context 2",
            "content": {
                "messages": [
                    {"role": "user", "content": "Test message 2"},
                    {"role": "assistant", "content": "Test response 2"}
                ],
                "metadata": {"test": True, "api": True, "batch": "2"}
            },
            "description": "Second test context for API",
            "tags": ["test", "api", "second"],
            "session_id": "api_session_002",
            "project_path": "/projects/api_test",
            "user_id": "api_user_002"
        }
    ]


@pytest.mark.integration
class TestContextAPIEndpoints:
    """Test context management API endpoints"""

    def test_health_check_endpoint(self, test_client):
        """Test that health check endpoint works"""
        response = test_client.get("/health")
        assert response.status_code == 200, "Health check should return 200"

        data = response.json()
        assert data["status"] == "healthy", "Status should be healthy"
        assert data["service"] == "persistent-context-storage", "Service name should match"
        assert "version" in data, "Version should be included"

    def test_root_endpoint(self, test_client):
        """Test root endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200, "Root endpoint should return 200"

        data = response.json()
        assert "message" in data, "Should include message"
        assert "description" in data, "Should include description"
        assert data["docs"] == "/docs", "Should point to docs"

    def test_create_context_endpoint(self, test_client, sample_api_contexts):
        """Test context creation endpoint"""
        context_data = sample_api_contexts[0]

        response = test_client.post(
            "/api/contexts",
            json={
                "title": context_data["title"],
                "content": context_data["content"],
                "description": context_data["description"],
                "tags": context_data["tags"],
                "session_id": context_data["session_id"],
                "project_path": context_data["project_path"],
                "user_id": context_data["user_id"],
                "visibility": "private",
                "auto_save_enabled": True
            }
        )

        assert response.status_code == 201, "Context creation should return 201"

        data = response.json()
        assert data["success"] is True, "Success flag should be True"
        assert "data" in data, "Should include data"
        assert "id" in data["data"], "Should include context ID"
        assert data["data"]["title"] == context_data["title"], "Title should match"
        assert data["data"]["message"] == "上下文创建成功", "Should include success message"

        # Store context ID for subsequent tests
        return data["data"]["id"]

    def test_create_context_validation_errors(self, test_client):
        """Test context creation with invalid data"""
        # Missing required fields
        response = test_client.post(
            "/api/contexts",
            json={
                "title": "Test",  # Missing content and user_id
                "description": "Test description"
            }
        )
        assert response.status_code == 422, "Should return validation error"

        # Invalid visibility value
        response = test_client.post(
            "/api/contexts",
            json={
                "title": "Test",
                "content": {"test": "data"},
                "user_id": "test_user",
                "visibility": "invalid_visibility"  # Invalid value
            }
        )
        assert response.status_code == 422, "Should return validation error for invalid visibility"

        # Title too long
        response = test_client.post(
            "/api/contexts",
            json={
                "title": "x" * 300,  # Exceeds max length of 255
                "content": {"test": "data"},
                "user_id": "test_user"
            }
        )
        assert response.status_code == 422, "Should return validation error for long title"

    def test_get_context_endpoint(self, test_client, sample_api_contexts):
        """Test context retrieval endpoint"""
        # First create a context
        create_response = test_client.post(
            "/api/contexts",
            json={
                "title": sample_api_contexts[0]["title"],
                "content": sample_api_contexts[0]["content"],
                "user_id": sample_api_contexts[0]["user_id"]
            }
        )
        context_id = create_response.json()["data"]["id"]

        # Retrieve the context
        response = test_client.get(f"/api/contexts/{context_id}")
        assert response.status_code == 200, "Context retrieval should succeed"

        data = response.json()
        assert data["id"] == context_id, "Context ID should match"
        assert data["title"] == sample_api_contexts[0]["title"], "Title should match"
        assert data["content"] == sample_api_contexts[0]["content"], "Content should match"

    def test_get_nonexistent_context(self, test_client):
        """Test retrieving non-existent context"""
        fake_id = "non-existent-context-id"
        response = test_client.get(f"/api/contexts/{fake_id}")
        assert response.status_code == 404, "Should return 404 for non-existent context"

        data = response.json()
        assert "detail" in data, "Should include error detail"
        assert "上下文不存在或无权访问" in data["detail"], "Error message should be descriptive"

    def test_update_context_endpoint(self, test_client, sample_api_contexts):
        """Test context update endpoint"""
        # Create context first
        create_response = test_client.post(
            "/api/contexts",
            json={
                "title": sample_api_contexts[0]["title"],
                "content": sample_api_contexts[0]["content"],
                "user_id": sample_api_contexts[0]["user_id"]
            }
        )
        context_id = create_response.json()["data"]["id"]

        # Update the context
        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "tags": ["updated", "test"]
        }
        response = test_client.put(
            f"/api/contexts/{context_id}",
            json=update_data
        )
        assert response.status_code == 200, "Context update should succeed"

        data = response.json()
        assert data["success"] is True, "Success flag should be True"
        assert data["data"]["id"] == context_id, "Context ID should match"

        # Verify the update
        get_response = test_client.get(f"/api/contexts/{context_id}")
        updated_context = get_response.json()
        assert updated_context["title"] == "Updated Title", "Title should be updated"
        assert updated_context["description"] == "Updated description", "Description should be updated"

    def test_update_context_no_fields(self, test_client, sample_api_contexts):
        """Test context update with no fields provided"""
        # Create context first
        create_response = test_client.post(
            "/api/contexts",
            json={
                "title": sample_api_contexts[0]["title"],
                "content": sample_api_contexts[0]["content"],
                "user_id": sample_api_contexts[0]["user_id"]
            }
        )
        context_id = create_response.json()["data"]["id"]

        # Try to update with no fields
        response = test_client.put(
            f"/api/contexts/{context_id}",
            json={}
        )
        assert response.status_code == 400, "Should return 400 when no fields provided"

        data = response.json()
        assert "没有提供要更新的字段" in data["detail"], "Error message should be descriptive"

    def test_delete_context_endpoint(self, test_client, sample_api_contexts):
        """Test context deletion endpoint"""
        # Create context first
        create_response = test_client.post(
            "/api/contexts",
            json={
                "title": sample_api_contexts[0]["title"],
                "content": sample_api_contexts[0]["content"],
                "user_id": sample_api_contexts[0]["user_id"]
            }
        )
        context_id = create_response.json()["data"]["id"]

        # Delete the context
        response = test_client.delete(f"/api/contexts/{context_id}?user_id={sample_api_contexts[0]['user_id']}")
        assert response.status_code == 200, "Context deletion should succeed"

        data = response.json()
        assert data["success"] is True, "Success flag should be True"
        assert data["data"]["id"] == context_id, "Context ID should match"

        # Verify deletion
        get_response = test_client.get(f"/api/contexts/{context_id}")
        assert get_response.status_code == 404, "Deleted context should not be found"

    def test_list_contexts_endpoint(self, test_client, sample_api_contexts):
        """Test context listing endpoint"""
        # Create multiple contexts
        created_ids = []
        for context_data in sample_api_contexts:
            response = test_client.post(
                "/api/contexts",
                json={
                    "title": context_data["title"],
                    "content": context_data["content"],
                    "user_id": context_data["user_id"],
                    "tags": context_data["tags"],
                    "session_id": context_data["session_id"]
                }
            )
            created_ids.append(response.json()["data"]["id"])

        # List all contexts
        response = test_client.get("/api/contexts")
        assert response.status_code == 200, "Context listing should succeed"

        data = response.json()
        assert isinstance(data, list), "Should return a list"
        assert len(data) >= len(sample_api_contexts), "Should include created contexts"

        # List contexts for specific user
        response = test_client.get("/api/contexts?user_id=api_user_001")
        data = response.json()
        user_contexts = [ctx for ctx in data if ctx.get("metadata", {}).get("user_id") == "api_user_001"]
        assert len(user_contexts) >= 1, "Should find contexts for user"

        # List contexts with limit and offset
        response = test_client.get("/api/contexts?limit=1&offset=0")
        data = response.json()
        assert len(data) <= 1, "Should respect limit parameter"

    def test_context_search_endpoints(self, test_client, sample_api_contexts):
        """Test context search endpoints"""
        # Create contexts for searching
        for context_data in sample_api_contexts:
            test_client.post(
                "/api/contexts",
                json={
                    "title": context_data["title"],
                    "content": context_data["content"],
                    "user_id": context_data["user_id"],
                    "tags": context_data["tags"],
                    "description": context_data["description"]
                }
            )

        # Test basic search
        response = test_client.get("/api/contexts/search?q=Test")
        assert response.status_code == 200, "Search should succeed"

        data = response.json()
        assert isinstance(data, list), "Should return a list"

        # Test advanced search
        search_request = {
            "query": "API",
            "tags": ["test", "api"],
            "limit": 10,
            "sort_by": "created_at",
            "sort_order": "desc"
        }
        response = test_client.post("/api/contexts/search/advanced", json=search_request)
        assert response.status_code == 200, "Advanced search should succeed"

        data = response.json()
        assert isinstance(data, list), "Should return a list"

        # Test tag search
        response = test_client.get("/api/contexts/search/tags/test")
        assert response.status_code == 200, "Tag search should succeed"

        data = response.json()
        assert isinstance(data, list), "Should return a list"

        # Test search suggestions
        response = test_client.get("/api/contexts/search/suggestions?q=API")
        assert response.status_code == 200, "Search suggestions should succeed"

        data = response.json()
        assert isinstance(data, list), "Should return a list"

        # Test filters endpoints
        response = test_client.get("/api/contexts/filters/tags")
        assert response.status_code == 200, "Tags filter should succeed"

        response = test_client.get("/api/contexts/filters/projects")
        assert response.status_code == 200, "Projects filter should succeed"

        response = test_client.get("/api/contexts/filters/sessions")
        assert response.status_code == 200, "Sessions filter should succeed"

    def test_context_stats_endpoint(self, test_client, sample_api_contexts):
        """Test context statistics endpoint"""
        # Create some contexts
        for context_data in sample_api_contexts:
            test_client.post(
                "/api/contexts",
                json={
                    "title": context_data["title"],
                    "content": context_data["content"],
                    "user_id": context_data["user_id"]
                }
            )

        # Get statistics
        response = test_client.get("/api/contexts/stats")
        assert response.status_code == 200, "Stats endpoint should succeed"

        data = response.json()
        assert data["success"] is True, "Success flag should be True"
        assert "data" in data, "Should include stats data"
        assert "total_contexts" in data["data"], "Should include total count"
        assert data["data"]["total_contexts"] >= len(sample_api_contexts), "Should count created contexts"


@pytest.mark.integration
class TestSessionAPIEndpoints:
    """Test session management API endpoints"""

    def test_session_management_endpoints(self, test_client):
        """Test session creation, retrieval, and management"""
        # Create a new session
        session_data = {
            "user_id": "session_test_user",
            "session_metadata": {
                "client_type": "test_client",
                "version": "1.0.0"
            }
        }
        response = test_client.post("/api/sessions", json=session_data)
        assert response.status_code == 201, "Session creation should succeed"

        session_info = response.json()
        assert "session_id" in session_info, "Should include session ID"

        session_id = session_info["session_id"]

        # Get session info
        response = test_client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200, "Session retrieval should succeed"

        # List user sessions
        response = test_client.get(f"/api/sessions?user_id=session_test_user")
        assert response.status_code == 200, "Session listing should succeed"

        # Resume session
        response = test_client.post(f"/api/sessions/{session_id}/resume")
        assert response.status_code == 200, "Session resume should succeed"

        # Force save session
        response = test_client.post(f"/api/sessions/{session_id}/force-save")
        assert response.status_code == 200, "Force save should succeed"

    def test_scheduler_management_endpoints(self, test_client):
        """Test scheduler management endpoints"""
        # Create a session first
        session_response = test_client.post(
            "/api/sessions",
            json={"user_id": "scheduler_test_user"}
        )
        session_id = session_response.json()["session_id"]

        # Start auto-save
        response = test_client.post(
            f"/api/sessions/{session_id}/auto-save/start",
            json={"interval": 60}
        )
        assert response.status_code == 200, "Auto-save start should succeed"

        # Get auto-save status
        response = test_client.get(f"/api/sessions/{session_id}/auto-save/status")
        assert response.status_code == 200, "Status check should succeed"

        # Stop auto-save
        response = test_client.post(f"/api/sessions/{session_id}/auto-save/stop")
        assert response.status_code == 200, "Auto-save stop should succeed"

        # Get global scheduler status
        response = test_client.get("/api/scheduler/status")
        assert response.status_code == 200, "Global scheduler status should succeed"


@pytest.mark.integration
class TestTeamAPIEndpoints:
    """Test team collaboration and sharing API endpoints"""

    def test_team_sharing_endpoints(self, test_client, sample_api_contexts):
        """Test context sharing and team collaboration endpoints"""
        # Create a context to share
        create_response = test_client.post(
            "/api/contexts",
            json={
                "title": sample_api_contexts[0]["title"],
                "content": sample_api_contexts[0]["content"],
                "user_id": "sharing_user",
                "visibility": "team"
            }
        )
        context_id = create_response.json()["data"]["id"]

        # Share context with a user
        share_data = {
            "context_id": context_id,
            "target_user_id": "target_user",
            "permission_level": "editor",
            "expires_at": None
        }
        response = test_client.post("/api/team/share", json=share_data)
        assert response.status_code == 201, "Context sharing should succeed"

        share_info = response.json()
        assert "share_id" in share_info, "Should include share ID"

        # Create anonymous share link
        link_data = {
            "context_id": context_id,
            "permission_level": "viewer",
            "expires_in_days": 7
        }
        response = test_client.post("/api/team/share/link", json=link_data)
        assert response.status_code == 201, "Share link creation should succeed"

        link_info = response.json()
        assert "share_token" in link_info, "Should include share token"

        # Get user permissions
        response = test_client.get("/api/team/permissions/sharing_user")
        assert response.status_code == 200, "Permission check should succeed"

        # List shares
        response = test_client.get("/api/team/shares")
        assert response.status_code == 200, "Share listing should succeed"

        # Get context shares
        response = test_client.get(f"/api/team/contexts/{context_id}/shares")
        assert response.status_code == 200, "Context shares listing should succeed"

    def test_permission_management_endpoints(self, test_client):
        """Test permission management endpoints"""
        # Get available permission levels
        response = test_client.get("/api/team/permission-levels")
        assert response.status_code == 200, "Permission levels should succeed"

        data = response.json()
        assert isinstance(data, list), "Should return a list"
        assert any(level["level"] == "owner" for level in data), "Should include owner level"
        assert any(level["level"] == "editor" for level in data), "Should include editor level"
        assert any(level["level"] == "viewer" for level in data), "Should include viewer level"

        # Check specific permission
        permission_check = {
            "user_id": "test_user",
            "resource_type": "context",
            "resource_id": "test_context_id",
            "permission": "view"
        }
        response = test_client.post("/api/team/check-permission", json=permission_check)
        assert response.status_code == 200, "Permission check should succeed"

    def test_team_management_endpoints(self, test_client):
        """Test team management endpoints"""
        # List teams
        response = test_client.get("/api/team/teams")
        assert response.status_code == 200, "Team listing should succeed"

        data = response.json()
        assert isinstance(data, list), "Should return a list"

        # Get team contexts (if team exists)
        if data:  # Only test if teams exist
            team_id = data[0]["id"]
            response = test_client.get(f"/api/team/teams/{team_id}/contexts")
            assert response.status_code == 200, "Team contexts listing should succeed"


@pytest.mark.integration
class TestAPIErrorHandling:
    """Test API error handling and edge cases"""

    def test_invalid_context_id_format(self, test_client):
        """Test API with invalid context ID format"""
        invalid_ids = [
            "",
            "too-short",
            "invalid-id-format!",
            "x" * 1000  # Too long
        ]

        for invalid_id in invalid_ids:
            response = test_client.get(f"/api/contexts/{invalid_id}")
            # Should handle gracefully (either 404 or 422)
            assert response.status_code in [404, 422], f"Should handle invalid ID: {invalid_id}"

    def test_malformed_json_requests(self, test_client):
        """Test API with malformed JSON"""
        # Test with invalid JSON in POST request
        response = test_client.post(
            "/api/contexts",
            data="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422, "Should handle malformed JSON"

    def test_large_payload_handling(self, test_client):
        """Test API with large payloads"""
        # Create a very large content payload
        large_content = {
            "messages": [
                {"role": "user", "content": "x" * 1000000},  # 1MB of content
                {"role": "assistant", "content": "x" * 1000000}
            ],
            "metadata": {"large": True}
        }

        response = test_client.post(
            "/api/contexts",
            json={
                "title": "Large Content Test",
                "content": large_content,
                "user_id": "large_payload_user"
            },
            timeout=30.0  # Allow more time for large payload
        )

        # Should either succeed or fail gracefully
        assert response.status_code in [201, 413, 422], "Should handle large payload gracefully"

    def test_concurrent_api_requests(self, test_client, sample_api_contexts):
        """Test concurrent API requests"""
        import threading
        import queue

        results = queue.Queue()

        def make_request(request_data):
            try:
                response = test_client.post("/api/contexts", json=request_data)
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")

        # Create multiple concurrent requests
        threads = []
        for i in range(10):
            request_data = {
                "title": f"Concurrent Context {i}",
                "content": {"index": i},
                "user_id": f"concurrent_user_{i % 3}"
            }
            thread = threading.Thread(target=make_request, args=(request_data,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 201:
                success_count += 1

        assert success_count >= 7, "Most concurrent requests should succeed (at least 70%)"


@pytest.mark.integration
class TestAPIPerformance:
    """Test API performance under load"""

    def test_api_response_times(self, test_client, sample_api_contexts):
        """Test API response times"""
        import time

        # Test creation performance
        start_time = time.time()
        response = test_client.post(
            "/api/contexts",
            json={
                "title": sample_api_contexts[0]["title"],
                "content": sample_api_contexts[0]["content"],
                "user_id": sample_api_contexts[0]["user_id"]
            }
        )
        creation_time = time.time() - start_time

        assert response.status_code == 201, "Context creation should succeed"
        assert creation_time < 5.0, f"Creation should complete in under 5 seconds, took {creation_time:.2f}s"

        context_id = response.json()["data"]["id"]

        # Test retrieval performance
        start_time = time.time()
        response = test_client.get(f"/api/contexts/{context_id}")
        retrieval_time = time.time() - start_time

        assert response.status_code == 200, "Context retrieval should succeed"
        assert retrieval_time < 2.0, f"Retrieval should complete in under 2 seconds, took {retrieval_time:.2f}s"

        # Test listing performance
        start_time = time.time()
        response = test_client.get("/api/contexts?limit=50")
        listing_time = time.time() - start_time

        assert response.status_code == 200, "Context listing should succeed"
        assert listing_time < 3.0, f"Listing should complete in under 3 seconds, took {listing_time:.2f}s"

    def test_batch_operations_performance(self, test_client):
        """Test performance of batch operations"""
        import time

        num_contexts = 20
        created_ids = []

        # Test batch creation performance
        start_time = time.time()
        for i in range(num_contexts):
            response = test_client.post(
                "/api/contexts",
                json={
                    "title": f"Batch Context {i}",
                    "content": {"batch": i, "data": f"test data {i}"},
                    "user_id": "batch_user"
                }
            )
            if response.status_code == 201:
                created_ids.append(response.json()["data"]["id"])
        batch_creation_time = time.time() - start_time

        assert len(created_ids) == num_contexts, "All batch contexts should be created"
        assert batch_creation_time < 30.0, f"Batch creation should complete in under 30 seconds, took {batch_creation_time:.2f}s"

        # Test batch listing performance
        start_time = time.time()
        response = test_client.get(f"/api/contexts?user_id=batch_user&limit={num_contexts}")
        batch_listing_time = time.time() - start_time

        assert response.status_code == 200, "Batch listing should succeed"
        assert len(response.json()) == num_contexts, "Should list all batch contexts"
        assert batch_listing_time < 5.0, f"Batch listing should complete in under 5 seconds, took {batch_listing_time:.2f}s"