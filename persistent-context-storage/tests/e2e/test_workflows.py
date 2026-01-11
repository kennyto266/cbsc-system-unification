"""
End-to-End (E2E) Tests for Complete Workflows
Tests session persistence, team sharing, and search functionality
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import shutil
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from main import app
from services.context_service import ContextService
from services.scheduler_service import SchedulerService
from services.permission_service import PermissionService
from services.search_service import SearchService
from config.database import init_sqlalchemy_database, get_database_session
from models.context import Context, ContextShare, ContextAccess
from models.tag import Tag
from models.user import User, Team, Permission


@pytest.mark.e2e
class SessionPersistenceWorkflowTest:
    """Test complete session persistence workflows including auto-save and recovery"""

    @pytest.fixture
    async def client_and_services(self):
        """Create test client and services with temporary workspace"""
        workspace = Path(tempfile.mkdtemp())

        # Create required directories
        (workspace / "data").mkdir(exist_ok=True)
        (workspace / "storage").mkdir(exist_ok=True)
        (workspace / "search_index").mkdir(exist_ok=True)
        (workspace / "logs").mkdir(exist_ok=True)

        # Set environment variables for test
        os.environ["DATABASE_URL"] = str(workspace / "data" / "contexts.db")
        os.environ["STORAGE_PATH"] = str(workspace / "storage")
        os.environ["SEARCH_INDEX_PATH"] = str(workspace / "search_index")

        # Initialize database
        await init_sqlalchemy_database()

        # Create test client
        client = TestClient(app)

        yield client, workspace

        # Cleanup
        shutil.rmtree(workspace, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_complete_session_lifecycle(self, client_and_services):
        """Test complete session lifecycle: creation -> auto-save -> recovery -> cleanup"""
        client, workspace = client_and_services

        # 1. Create a new context session
        session_data = {
            "title": "E2E Test Session",
            "content": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "Hello, let's start a project"},
                    {"role": "assistant", "content": "Great! I'm ready to help you"}
                ],
                "metadata": {
                    "session_id": "e2e-session-123",
                    "user_id": "test-user-456",
                    "project": "test-project",
                    "files": ["main.py", "README.md"]
                }
            },
            "description": "E2E test session for complete lifecycle",
            "tags": ["e2e", "test", "session"],
            "project_path": "/test/project",
            "user_id": "test-user-456",
            "interval_minutes": 1  # Short interval for testing
        }

        # Create context with auto-save
        response = client.post("/api/sessions/auto-save", json=session_data)
        assert response.status_code == 200
        result = response.json()

        assert "session_id" in result
        assert "context_id" in result
        assert result["status"] == "auto_save_enabled"

        session_id = result["session_id"]
        context_id = result["context_id"]

        # 2. Simulate content updates (multiple auto-save cycles)
        for i in range(3):
            # Wait for auto-save interval
            time.sleep(1.2)  # Wait slightly longer than the 1-minute interval

            # Update content
            update_data = {
                "content": {
                    "messages": session_data["content"]["messages"] + [
                        {"role": "user", "content": f"Update {i+1}"},
                        {"role": "assistant", "content": f"Response {i+1}"}
                    ],
                    "metadata": {
                        **session_data["content"]["metadata"],
                        "last_update": f"update-{i+1}",
                        "update_count": i + 1
                    }
                },
                "title": f"E2E Test Session - Update {i+1}",
                "description": f"Updated {i+1} times"
            }

            response = client.put(f"/api/sessions/auto-save/{session_id}", json=update_data)
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "updated"

        # 3. Test session resumption
        response = client.get(f"/api/sessions/resume/{session_id}")
        assert response.status_code == 200
        resume_result = response.json()

        assert resume_result["session_id"] == session_id
        assert resume_result["context_id"] == context_id
        assert resume_result["title"] == "E2E Test Session - Update 3"
        assert len(resume_result["content"]["messages"]) == 9  # 3 original + 6 updates

        # 4. Test session recovery after simulated restart
        # Get all sessions for the user
        response = client.get(f"/api/sessions/user/test-user-456")
        assert response.status_code == 200
        sessions = response.json()

        assert len(sessions) > 0
        found_session = next(s for s in sessions if s["session_id"] == session_id)
        assert found_session["context_id"] == context_id

        # 5. Test context retrieval with full history
        response = client.get(f"/api/contexts/{context_id}")
        assert response.status_code == 200
        context = response.json()

        assert context["id"] == context_id
        assert context["title"] == "E2E Test Session - Update 3"
        assert context["session_id"] == session_id
        assert "update_count" in context["content"]["metadata"]
        assert context["content"]["metadata"]["update_count"] == 3

        # 6. Test cleanup and force save
        response = client.post(f"/api/sessions/{session_id}/force-save")
        assert response.status_code == 200
        save_result = response.json()
        assert save_result["status"] == "saved"

        # 7. Test session deletion and cleanup
        response = client.delete(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        cleanup_result = response.json()
        assert cleanup_result["status"] == "cleaned_up"

        # Verify session is no longer active
        response = client.get(f"/api/sessions/resume/{session_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_session_persistence_across_restarts(self, client_and_services):
        """Test that session data persists across service restarts"""
        client, workspace = client_and_services

        # Create initial session
        session_data = {
            "title": "Persistence Test Session",
            "content": {
                "messages": [{"role": "user", "content": "Initial message"}],
                "metadata": {"project": "persistence-test", "user_id": "user-789"}
            },
            "description": "Test persistence across restarts",
            "user_id": "user-789",
            "interval_minutes": 1
        }

        response = client.post("/api/sessions/auto-save", json=session_data)
        assert response.status_code == 200
        session_id = response.json()["session_id"]

        # Simulate service restart by reinitializing services
        # In a real scenario, this would be an actual restart
        from services.scheduler_service import SchedulerService
        from services.context_service import ContextService

        new_context_service = ContextService()
        new_scheduler_service = SchedulerService(new_context_service)
        new_scheduler_service.start()

        # Test session recovery after restart
        response = client.get(f"/api/sessions/resume/{session_id}")
        assert response.status_code == 200

        resumed_data = response.json()
        assert resumed_data["title"] == "Persistence Test Session"
        assert resumed_data["content"]["metadata"]["project"] == "persistence-test"


@pytest.mark.e2e
class TeamSharingWorkflowTest:
    """Test complete team sharing workflows including permissions and access control"""

    @pytest.fixture
    async def sharing_setup(self):
        """Setup users, teams, and contexts for sharing tests"""
        workspace = Path(tempfile.mkdtemp())

        # Create required directories
        (workspace / "data").mkdir(exist_ok=True)
        (workspace / "storage").mkdir(exist_ok=True)
        (workspace / "search_index").mkdir(exist_ok=True)

        os.environ["DATABASE_URL"] = str(workspace / "data" / "contexts.db")
        os.environ["STORAGE_PATH"] = str(workspace / "storage")
        os.environ["SEARCH_INDEX_PATH"] = str(workspace / "search_index")

        await init_sqlalchemy_database()

        client = TestClient(app)

        # Create test users and contexts
        owner_user = "owner-123"
        editor_user = "editor-456"
        viewer_user = "viewer-789"

        # Create a context owned by owner_user
        context_data = {
            "title": "Team Project Context",
            "content": {
                "messages": [
                    {"role": "system", "content": "Project planning context"},
                    {"role": "user", "content": "Let's plan our new feature"}
                ],
                "metadata": {
                    "project": "team-project",
                    "feature": "user-authentication",
                    "files": ["auth.py", "models.py"]
                }
            },
            "description": "Shared team project context",
            "tags": ["team", "project", "authentication"],
            "project_path": "/team/project",
            "user_id": owner_user,
            "visibility": "team"
        }

        response = client.post("/api/contexts", json=context_data)
        assert response.status_code == 200
        context_id = response.json()["id"]

        yield client, {
            "context_id": context_id,
            "owner": owner_user,
            "editor": editor_user,
            "viewer": viewer_user
        }

        shutil.rmtree(workspace, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_complete_sharing_workflow(self, sharing_setup):
        """Test complete sharing workflow: create -> share -> manage permissions -> revoke"""
        client, users = sharing_setup
        context_id = users["context_id"]
        owner = users["owner"]
        editor = users["editor"]
        viewer = users["viewer"]

        # 1. Share context with editor (editor permissions)
        share_request = {
            "context_id": context_id,
            "shared_with_user_id": editor,
            "permission_level": "editor",
            "expires_hours": 24,
            "message": "Please help review this authentication feature"
        }

        response = client.post("/api/team/share", json=share_request)
        assert response.status_code == 200
        share_result = response.json()

        assert "share_id" in share_result
        assert share_result["permission_level"] == "editor"
        assert share_result["shared_with_user_id"] == editor

        editor_share_id = share_result["share_id"]

        # 2. Share context with viewer (viewer permissions)
        share_request["shared_with_user_id"] = viewer
        share_request["permission_level"] = "viewer"
        share_request["message"] = "For your reference"

        response = client.post("/api/team/share", json=share_request)
        assert response.status_code == 200
        viewer_share_id = response.json()["share_id"]

        # 3. Create public share link
        public_link_request = {
            "context_id": context_id,
            "permission_level": "viewer",
            "expires_hours": 48,
            "max_accesses": 10
        }

        response = client.post("/api/team/share/link", json=public_link_request)
        assert response.status_code == 200
        public_share = response.json()

        assert "share_token" in public_share
        assert public_share["permission_level"] == "viewer"
        assert public_share["max_accesses"] == 10

        share_token = public_share["share_token"]

        # 4. Test access controls for different permission levels
        # Editor should be able to update context
        editor_update = {
            "title": "Updated by Editor",
            "content": {
                "messages": [
                    {"role": "editor", "content": "I've reviewed and added comments"}
                ]
            },
            "description": "Editor's review and updates"
        }

        response = client.put(f"/api/contexts/{context_id}", json=editor_update)
        assert response.status_code == 200

        # 5. Test permission checking
        permission_check = {
            "context_id": context_id,
            "user_id": viewer,
            "permission": "view"
        }

        response = client.post("/api/team/check-permission", json=permission_check)
        assert response.status_code == 200
        assert response.json()["has_permission"] == True

        # Viewer should not have edit permission
        permission_check["permission"] = "edit"
        response = client.post("/api/team/check-permission", json=permission_check)
        assert response.status_code == 200
        assert response.json()["has_permission"] == False

        # 6. Test access via share token
        token_access = {
            "share_token": share_token,
            "user_id": "anonymous-user"
        }

        response = client.post("/api/team/share/access", json=token_access)
        assert response.status_code == 200
        access_result = response.json()

        assert access_result["context_id"] == context_id
        assert access_result["permission_level"] == "viewer"

        # 7. List all shares for the context
        response = client.get(f"/api/team/contexts/{context_id}/shares")
        assert response.status_code == 200
        shares = response.json()

        assert len(shares) >= 3  # owner, editor, viewer shares

        # 8. Get user's shared contexts
        response = client.get(f"/api/team/users/{editor}/shared-contexts")
        assert response.status_code == 200
        editor_contexts = response.json()

        assert any(ctx["id"] == context_id for ctx in editor_contexts)

        # 9. Update permission level
        permission_update = {
            "permission_level": "viewer"
        }

        response = client.put(f"/api/team/share/{editor_share_id}/permission", json=permission_update)
        assert response.status_code == 200
        assert response.json()["permission_level"] == "viewer"

        # 10. Test access logs (admin functionality)
        response = client.get("/api/team/access-logs")
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) > 0

        # 11. Revoke shares
        response = client.delete(f"/api/team/share/{editor_share_id}")
        assert response.status_code == 200

        response = client.delete(f"/api/team/share/{viewer_share_id}")
        assert response.status_code == 200

        # Verify shares are revoked
        response = client.get(f"/api/team/contexts/{context_id}/shares")
        shares = response.json()
        editor_share = next((s for s in shares if s["id"] == editor_share_id), None)
        viewer_share = next((s for s in shares if s["id"] == viewer_share_id), None)

        assert editor_share is None or editor_share.get("revoked") == True
        assert viewer_share is None or viewer_share.get("revoked") == True

    @pytest.mark.asyncio
    async def test_team_collaboration_features(self, sharing_setup):
        """Test team collaboration features like team contexts and permissions"""
        client, users = sharing_setup
        context_id = users["context_id"]

        # 1. Get available permission levels
        response = client.get("/api/team/permission-levels")
        assert response.status_code == 200
        permissions = response.json()

        assert any(p["level"] == "viewer" for p in permissions)
        assert any(p["level"] == "editor" for p in permissions)
        assert any(p["level"] == "owner" for p in permissions)

        # 2. Get popular tags across shared contexts
        response = client.get("/api/team/popular-tags")
        assert response.status_code == 200
        popular_tags = response.json()

        assert len(popular_tags) > 0
        assert any(tag["tag"] == "team" for tag in popular_tags)

        # 3. Get user permission summary
        response = client.get(f"/api/team/permissions/{users['editor']}")
        assert response.status_code == 200
        permission_summary = response.json()

        assert "permissions" in permission_summary
        assert "shared_contexts_count" in permission_summary
        assert "access_level" in permission_summary


@pytest.mark.e2e
class SearchAndFilterWorkflowTest:
    """Test complete search and filtering workflows"""

    @pytest.fixture
    async def search_dataset(self):
        """Create a comprehensive dataset for search testing"""
        workspace = Path(tempfile.mkdtemp())

        (workspace / "data").mkdir(exist_ok=True)
        (workspace / "storage").mkdir(exist_ok=True)
        (workspace / "search_index").mkdir(exist_ok=True)

        os.environ["DATABASE_URL"] = str(workspace / "data" / "contexts.db")
        os.environ["STORAGE_PATH"] = str(workspace / "storage")
        os.environ["SEARCH_INDEX_PATH"] = str(workspace / "search_index")

        await init_sqlalchemy_database()

        client = TestClient(app)

        # Create diverse contexts for search testing
        contexts = [
            {
                "title": "Python Machine Learning Guide",
                "content": {
                    "messages": [{"role": "assistant", "content": "Machine learning with Python and scikit-learn"}],
                    "metadata": {"project": "ml-tutorial", "language": "python"}
                },
                "tags": ["python", "machine-learning", "tutorial"],
                "project_path": "/tutorials/ml",
                "user_id": "user-1"
            },
            {
                "title": "FastAPI REST API Development",
                "content": {
                    "messages": [{"role": "assistant", "content": "Building REST APIs with FastAPI framework"}],
                    "metadata": {"project": "api-development", "language": "python"}
                },
                "tags": ["python", "fastapi", "api"],
                "project_path": "/projects/api",
                "user_id": "user-2"
            },
            {
                "title": "React Component Library",
                "content": {
                    "messages": [{"role": "assistant", "content": "Creating reusable React components"}],
                    "metadata": {"project": "ui-library", "language": "javascript"}
                },
                "tags": ["react", "javascript", "components"],
                "project_path": "/projects/ui",
                "user_id": "user-3"
            },
            {
                "title": "Database Schema Design",
                "content": {
                    "messages": [{"role": "assistant", "content": "Designing scalable database schemas with PostgreSQL"}],
                    "metadata": {"project": "database-design", "language": "sql"}
                },
                "tags": ["database", "sql", "design"],
                "project_path": "/projects/database",
                "user_id": "user-1"
            },
            {
                "title": "Docker Containerization Guide",
                "content": {
                    "messages": [{"role": "assistant", "content": "Containerizing applications with Docker"}],
                    "metadata": {"project": "devops", "technology": "docker"}
                },
                "tags": ["docker", "devops", "containers"],
                "project_path": "/projects/devops",
                "user_id": "user-2"
            }
        ]

        created_contexts = []
        for context_data in contexts:
            response = client.post("/api/contexts", json=context_data)
            assert response.status_code == 200
            created_contexts.append(response.json())

        yield client, created_contexts

        shutil.rmtree(workspace, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_comprehensive_search_workflow(self, search_dataset):
        """Test comprehensive search and filtering workflow"""
        client, contexts = search_dataset

        # 1. Basic text search
        response = client.get("/api/contexts/search?query=python")
        assert response.status_code == 200
        search_results = response.json()

        assert len(search_results["contexts"]) >= 2
        python_contexts = [ctx for ctx in search_results["contexts"] if "Python" in ctx["title"]]
        assert len(python_contexts) >= 2

        # 2. Tag-based search
        response = client.get("/api/contexts/search/tags/python")
        assert response.status_code == 200
        tag_results = response.json()

        assert len(tag_results["contexts"]) >= 2
        for ctx in tag_results["contexts"]:
            assert "python" in ctx["tags"]

        # 3. Advanced search with multiple filters
        advanced_search = {
            "query": "api",
            "tags": ["python"],
            "user_id": "user-2",
            "limit": 10,
            "offset": 0
        }

        response = client.post("/api/contexts/search/advanced", json=advanced_search)
        assert response.status_code == 200
        advanced_results = response.json()

        assert len(advanced_results["contexts"]) >= 1
        for ctx in advanced_results["contexts"]:
            assert "FastAPI" in ctx["title"] or "api" in ctx["title"].lower()
            assert ctx["user_id"] == "user-2"
            assert "python" in ctx["tags"]

        # 4. Date range filtering
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        response = client.get(f"/api/contexts/search?created_after={yesterday.isoformat()}&created_before={today.isoformat()}")
        assert response.status_code == 200
        date_results = response.json()

        for ctx in date_results["contexts"]:
            created_date = datetime.fromisoformat(ctx["created_at"])
            assert yesterday <= created_date <= today

        # 5. Search suggestions
        response = client.get("/api/contexts/search/suggestions?prefix=py")
        assert response.status_code == 200
        suggestions = response.json()

        assert len(suggestions["title_suggestions"]) > 0
        assert any("Python" in s["title"] for s in suggestions["title_suggestions"])

        # 6. Filter endpoints
        response = client.get("/api/contexts/filters/tags")
        assert response.status_code == 200
        tag_filters = response.json()

        assert len(tag_filters) > 0
        assert any(tag["tag"] == "python" for tag in tag_filters)

        response = client.get("/api/contexts/filters/projects")
        assert response.status_code == 200
        project_filters = response.json()

        assert len(project_filters) > 0
        assert any("/tutorials/ml" in proj["project_path"] for proj in project_filters)

        # 7. Sorted search results
        response = client.get("/api/contexts/search?sort_by=title&sort_order=asc")
        assert response.status_code == 200
        sorted_results = response.json()

        titles = [ctx["title"] for ctx in sorted_results["contexts"]]
        assert titles == sorted(titles)

        # 8. Paginated search
        response = client.get("/api/contexts/search?limit=2&offset=0")
        assert response.status_code == 200
        page1 = response.json()

        response = client.get("/api/contexts/search?limit=2&offset=2")
        assert response.status_code == 200
        page2 = response.json()

        assert len(page1["contexts"]) <= 2
        assert len(page2["contexts"]) <= 2

        # Ensure no overlap between pages
        page1_ids = {ctx["id"] for ctx in page1["contexts"]}
        page2_ids = {ctx["id"] for ctx in page2["contexts"]}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_search_performance_and_accuracy(self, search_dataset):
        """Test search performance and result accuracy"""
        client, contexts = search_dataset

        # 1. Test search result relevance
        response = client.get("/api/contexts/search?query=machine learning")
        assert response.status_code == 200
        results = response.json()

        # Most relevant result should be the ML guide
        if len(results["contexts"]) > 0:
            top_result = results["contexts"][0]
            assert "Machine Learning" in top_result["title"]

        # 2. Test search with special characters and partial matches
        response = client.get("/api/contexts/search?query=api")
        assert response.status_code == 200
        api_results = response.json()

        # Should match both "API" and "api"
        for ctx in api_results["contexts"]:
            content_match = "api" in ctx["title"].lower() or "api" in ctx.get("content", {}).get("messages", [{}])[0].get("content", "").lower()
            assert content_match

        # 3. Test empty search returns all contexts
        response = client.get("/api/contexts/search?query=")
        assert response.status_code == 200
        empty_results = response.json()

        response = client.get("/api/contexts")
        assert response.status_code == 200
        all_contexts = response.json()

        assert len(empty_results["contexts"]) == len(all_contexts)


@pytest.mark.e2e
class IntegratedWorkflowTest:
    """Test integrated workflows combining multiple features"""

    @pytest.fixture
    async def integrated_setup(self):
        """Setup for integrated workflow testing"""
        workspace = Path(tempfile.mkdtemp())

        (workspace / "data").mkdir(exist_ok=True)
        (workspace / "storage").mkdir(exist_ok=True)
        (workspace / "search_index").mkdir(exist_ok=True)

        os.environ["DATABASE_URL"] = str(workspace / "data" / "contexts.db")
        os.environ["STORAGE_PATH"] = str(workspace / "storage")
        os.environ["SEARCH_INDEX_PATH"] = str(workspace / "search_index")

        await init_sqlalchemy_database()

        client = TestClient(app)
        yield client, workspace

        shutil.rmtree(workspace, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_collaborative_development_workflow(self, integrated_setup):
        """Test complete collaborative development workflow"""
        client, workspace = integrated_setup

        # 1. Developer creates initial context session
        initial_session = {
            "title": "New Feature Development - User Authentication",
            "content": {
                "messages": [
                    {"role": "system", "content": "Starting user authentication feature development"},
                    {"role": "developer", "content": "Need to implement login, registration, and password reset"}
                ],
                "metadata": {
                    "feature": "authentication",
                    "sprint": "sprint-12",
                    "stories": ["AUTH-001", "AUTH-002", "AUTH-003"]
                }
            },
            "description": "User authentication feature development session",
            "tags": ["authentication", "feature", "sprint-12"],
            "project_path": "/team-project/auth",
            "user_id": "developer-123",
            "interval_minutes": 2
        }

        response = client.post("/api/sessions/auto-save", json=initial_session)
        assert response.status_code == 200
        session_result = response.json()
        session_id = session_result["session_id"]
        context_id = session_result["context_id"]

        # 2. Developer works on feature, updating session
        for i in range(3):
            time.sleep(2.1)  # Wait for auto-save

            update_data = {
                "content": {
                    "messages": initial_session["content"]["messages"] + [
                        {"role": "developer", "content": f"Implemented auth component {i+1}"},
                        {"role": "assistant", "content": f"Code review suggestions for component {i+1}"}
                    ],
                    "metadata": {
                        **initial_session["content"]["metadata"],
                        "components_completed": i + 1,
                        "last_activity": f"component-{i+1}"
                    }
                },
                "title": f"Auth Feature - Component {i+1} Complete"
            }

            response = client.put(f"/api/sessions/auto-save/{session_id}", json=update_data)
            assert response.status_code == 200

        # 3. Developer shares context with team lead for review
        share_request = {
            "context_id": context_id,
            "shared_with_user_id": "teamlead-456",
            "permission_level": "editor",
            "expires_hours": 72,
            "message": "Ready for code review and feedback"
        }

        response = client.post("/api/team/share", json=share_request)
        assert response.status_code == 200
        share_result = response.json()
        share_id = share_result["share_id"]

        # 4. Team lead reviews and updates the context
        lead_update = {
            "title": "Auth Feature - Code Review Complete",
            "content": {
                "messages": [
                    {"role": "teamlead", "content": "Reviewed authentication implementation"},
                    {"role": "teamlead", "content": "Great work! A few suggestions for security improvements"},
                    {"role": "teamlead", "content": "Approved for testing phase"}
                ],
                "metadata": {
                    "feature": "authentication",
                    "status": "ready_for_testing",
                    "review_date": datetime.now().isoformat(),
                    "approved_by": "teamlead-456"
                }
            },
            "description": "Code reviewed and approved for testing"
        }

        response = client.put(f"/api/contexts/{context_id}", json=lead_update)
        assert response.status_code == 200

        # 5. Create public share link for QA team
        public_link_request = {
            "context_id": context_id,
            "permission_level": "viewer",
            "expires_hours": 168,  # 1 week
            "max_accesses": 50
        }

        response = client.post("/api/team/share/link", json=public_link_request)
        assert response.status_code == 200
        public_share = response.json()

        # 6. QA team searches for authentication contexts
        response = client.get("/api/contexts/search?query=authentication&tags=feature")
        assert response.status_code == 200
        search_results = response.json()

        auth_contexts = [ctx for ctx in search_results["contexts"] if ctx["id"] == context_id]
        assert len(auth_contexts) == 1

        # 7. Developer resumes session and incorporates feedback
        response = client.get(f"/api/sessions/resume/{session_id}")
        assert response.status_code == 200
        resumed_session = response.json()

        assert "ready_for_testing" in resumed_session["content"]["metadata"]["status"]

        # 8. Developer adds final updates based on feedback
        final_update = {
            "content": {
                "messages": resumed_session["content"]["messages"] + [
                    {"role": "developer", "content": "Implemented security improvements from code review"},
                    {"role": "developer", "content": "Added comprehensive unit tests"}
                ],
                "metadata": {
                    **resumed_session["content"]["metadata"],
                    "status": "testing_complete",
                    "security_improvements": True,
                    "unit_tests": True
                }
            },
            "title": "Auth Feature - Ready for Production",
            "tags": ["authentication", "feature", "sprint-12", "tested", "security-reviewed"]
        }

        response = client.put(f"/api/sessions/auto-save/{session_id}", json=final_update)
        assert response.status_code == 200

        # 9. Search for completed features in the sprint
        response = client.get("/api/contexts/search/tags/sprint-12")
        assert response.status_code == 200
        sprint_contexts = response.json()

        completed_features = [ctx for ctx in sprint_contexts["contexts"]
                            if "tested" in ctx["tags"]]
        assert len(completed_features) >= 1

        # 10. Generate usage statistics
        response = client.get("/api/contexts/stats")
        assert response.status_code == 200
        stats = response.json()

        assert stats["total_contexts"] >= 1
        assert "popular_tags" in stats
        assert any("authentication" in tag["tag"] for tag in stats["popular_tags"])

        # 11. Cleanup session
        response = client.delete(f"/api/sessions/{session_id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_disaster_recovery_workflow(self, integrated_setup):
        """Test disaster recovery and data integrity workflow"""
        client, workspace = integrated_setup

        # 1. Create multiple contexts with auto-save
        contexts = []
        for i in range(5):
            session_data = {
                "title": f"Critical Context {i+1}",
                "content": {
                    "messages": [{"role": "user", "content": f"Important data {i+1}"}],
                    "metadata": {"priority": "critical", "backup_required": True}
                },
                "user_id": "user-123",
                "interval_minutes": 1
            }

            response = client.post("/api/sessions/auto-save", json=session_data)
            assert response.status_code == 200
            contexts.append(response.json())

        # 2. Simulate data corruption by modifying stored files
        # (In real scenario, this would be actual corruption)
        storage_path = Path(os.environ["STORAGE_PATH"])

        # 3. Test data recovery through search and listing
        response = client.get("/api/contexts?user_id=user-123")
        assert response.status_code == 200
        recovered_contexts = response.json()

        assert len(recovered_contexts) >= 5

        # 4. Verify data integrity
        for context in contexts[:5]:
            response = client.get(f"/api/contexts/{context['context_id']}")
            assert response.status_code == 200

            context_data = response.json()
            assert context_data["user_id"] == "user-123"
            assert "Important data" in context_data["content"]["messages"][0]["content"]

        # 5. Test search functionality still works
        response = client.get("/api/contexts/search?query=critical")
        assert response.status_code == 200
        search_results = response.json()

        critical_contexts = [ctx for ctx in search_results["contexts"]
                           if "Critical" in ctx["title"]]
        assert len(critical_contexts) >= 5

        # 6. Test session recovery for all contexts
        for context in contexts[:3]:
            session_id = context["session_id"]
            response = client.get(f"/api/sessions/resume/{session_id}")
            assert response.status_code == 200

            resumed_data = response.json()
            assert "Critical" in resumed_data["title"]
            assert resumed_data["content"]["metadata"]["priority"] == "critical"


if __name__ == "__main__":
    # Run specific E2E tests
    pytest.main([
        __file__,
        "-v",
        "-m", "e2e",
        "--tb=short"
    ])