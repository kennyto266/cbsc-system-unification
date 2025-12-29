"""
Basic E2E workflow tests
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from fastapi.testclient import TestClient


class TestBasicE2EWorkflows:
    """Test basic end-to-end workflows"""

    @pytest.fixture
    def test_client(self):
        """Create a test client with temporary workspace"""
        # Create temporary workspace
        workspace = Path(tempfile.mkdtemp())

        # Create required directories
        (workspace / "data").mkdir(exist_ok=True)
        (workspace / "storage").mkdir(exist_ok=True)
        (workspace / "search_index").mkdir(exist_ok=True)

        # Set environment variables
        os.environ["DATABASE_URL"] = str(workspace / "data" / "contexts.db")
        os.environ["STORAGE_PATH"] = str(workspace / "storage")
        os.environ["SEARCH_INDEX_PATH"] = str(workspace / "search_index")

        # Import and initialize app
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        sys.path.insert(0, parent_dir)

        # Initialize database first
        from config.database import init_sqlalchemy_database
        init_sqlalchemy_database()

        from main import app
        client = TestClient(app)

        yield client

        # Cleanup
        shutil.rmtree(workspace, ignore_errors=True)

    @pytest.mark.e2e
    def test_health_endpoint(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "persistent-context-storage"

    @pytest.mark.e2e
    def test_basic_context_workflow(self, test_client):
        """Test basic context creation and retrieval workflow"""
        # Create context
        context_data = {
            "title": "E2E Test Context",
            "content": {
                "messages": [
                    {"role": "user", "content": "Hello world"},
                    {"role": "assistant", "content": "Hello! How can I help you?"}
                ],
                "metadata": {"test": True, "workflow": "basic"}
            },
            "description": "Basic E2E test context",
            "user_id": "e2e-user",
            "tags": ["e2e", "test"]
        }

        response = test_client.post("/api/contexts", json=context_data)
        assert response.status_code in [200, 201]  # Both 200 and 201 are acceptable
        create_result = response.json()

        # Check if response has data wrapper
        if "data" in create_result:
            data = create_result["data"]
        else:
            data = create_result

        assert "id" in data
        context_id = data["id"]

        # Retrieve context
        response = test_client.get(f"/api/contexts/{context_id}")
        assert response.status_code == 200
        get_result = response.json()

        assert get_result["id"] == context_id
        assert get_result["title"] == "E2E Test Context"
        assert len(get_result["content"]["messages"]) == 2
        assert get_result["metadata"]["user_id"] == "e2e-user"
        assert "e2e" in get_result["metadata"]["tags"]

    @pytest.mark.e2e
    def test_context_search_workflow(self, test_client):
        """Test context search workflow"""
        # Create multiple contexts
        contexts = [
            {
                "title": "Python Context",
                "content": {"messages": [{"role": "user", "content": "Python programming"}]},
                "user_id": "search-user",
                "tags": ["python", "programming"]
            },
            {
                "title": "JavaScript Context",
                "content": {"messages": [{"role": "user", "content": "JavaScript development"}]},
                "user_id": "search-user",
                "tags": ["javascript", "development"]
            }
        ]

        created_ids = []
        for ctx_data in contexts:
            response = test_client.post("/api/contexts", json=ctx_data)
            assert response.status_code in [200, 201]
            result = response.json()
            data = result.get("data", result)
            created_ids.append(data["id"])

        # Search for Python context
        response = test_client.get("/api/contexts/search?query=python")
        assert response.status_code == 200
        search_result = response.json()

        assert len(search_result["contexts"]) >= 1
        python_contexts = [c for c in search_result["contexts"] if "Python" in c["title"]]
        assert len(python_contexts) >= 1

        # Search by tag
        response = test_client.get("/api/contexts/search/tags/python")
        assert response.status_code == 200
        tag_result = response.json()

        assert len(tag_result["contexts"]) >= 1
        for ctx in tag_result["contexts"]:
            assert "python" in ctx["tags"]

    @pytest.mark.e2e
    def test_session_persistence_workflow(self, test_client):
        """Test basic session persistence workflow"""
        # Create session with auto-save
        session_data = {
            "title": "E2E Session Test",
            "content": {
                "messages": [{"role": "user", "content": "Start session test"}],
                "metadata": {"session_type": "e2e_test"}
            },
            "user_id": "session-user",
            "interval_minutes": 1
        }

        response = test_client.post("/api/sessions/auto-save", json=session_data)
        assert response.status_code == 200
        session_result = response.json()

        assert "session_id" in session_result
        assert "context_id" in session_result
        session_id = session_result["session_id"]
        context_id = session_result["context_id"]

        # Update session
        update_data = {
            "content": {
                "messages": [
                    {"role": "user", "content": "Start session test"},
                    {"role": "assistant", "content": "Session updated"}
                ],
                "metadata": {"session_type": "e2e_test", "updated": True}
            }
        }

        response = test_client.put(f"/api/sessions/auto-save/{session_id}", json=update_data)
        assert response.status_code == 200

        # Resume session
        response = test_client.get(f"/api/sessions/resume/{session_id}")
        assert response.status_code == 200
        resume_result = response.json()

        assert resume_result["session_id"] == session_id
        assert resume_result["context_id"] == context_id
        assert len(resume_result["content"]["messages"]) == 2

        # Force save
        response = test_client.post(f"/api/sessions/{session_id}/force-save")
        assert response.status_code == 200

        # Cleanup
        response = test_client.delete(f"/api/sessions/{session_id}")
        assert response.status_code == 200

    @pytest.mark.e2e
    def test_team_sharing_workflow(self, test_client):
        """Test basic team sharing workflow"""
        # Create a context
        context_data = {
            "title": "Shared Test Context",
            "content": {"messages": [{"role": "user", "content": "Shared content"}]},
            "user_id": "owner-user",
            "visibility": "team"
        }

        response = test_client.post("/api/contexts", json=context_data)
        assert response.status_code in [200, 201]  # Both 200 and 201 are acceptable
        context_id = response.json()["id"]

        # Share with another user
        share_request = {
            "context_id": context_id,
            "shared_with_user_id": "viewer-user",
            "permission_level": "viewer",
            "expires_hours": 24
        }

        response = test_client.post("/api/team/share", json=share_request)
        assert response.status_code == 200
        share_result = response.json()

        assert "share_id" in share_result
        assert share_result["permission_level"] == "viewer"

        # Create public share link
        link_request = {
            "context_id": context_id,
            "permission_level": "viewer",
            "expires_hours": 48
        }

        response = test_client.post("/api/team/share/link", json=link_request)
        assert response.status_code == 200
        link_result = response.json()

        assert "share_token" in link_result

        # Check permission
        permission_check = {
            "context_id": context_id,
            "user_id": "viewer-user",
            "permission": "view"
        }

        response = test_client.post("/api/team/check-permission", json=permission_check)
        assert response.status_code == 200
        assert response.json()["has_permission"] == True

        # Get shares for context
        response = test_client.get(f"/api/team/contexts/{context_id}/shares")
        assert response.status_code == 200
        shares = response.json()
        assert len(shares) >= 2  # Owner share + viewer share + public link

    @pytest.mark.e2e
    def test_complete_workflow_integration(self, test_client):
        """Test complete integrated workflow"""
        # 1. Create session
        session_data = {
            "title": "Complete Workflow Test",
            "content": {
                "messages": [{"role": "user", "content": "Start integrated workflow"}],
                "metadata": {"workflow": "complete"}
            },
            "user_id": "integration-user",
            "tags": ["workflow", "integration"],
            "interval_minutes": 1
        }

        response = test_client.post("/api/sessions/auto-save", json=session_data)
        assert response.status_code == 200
        session_id = response.json()["session_id"]
        context_id = response.json()["context_id"]

        # 2. Update content
        update_data = {
            "content": {
                "messages": [
                    {"role": "user", "content": "Start integrated workflow"},
                    {"role": "assistant", "content": "Workflow progressing"}
                ]
            },
            "title": "Complete Workflow - Updated"
        }

        response = test_client.put(f"/api/sessions/auto-save/{session_id}", json=update_data)
        assert response.status_code == 200

        # 3. Share with team
        share_request = {
            "context_id": context_id,
            "shared_with_user_id": "team-user",
            "permission_level": "editor"
        }

        response = test_client.post("/api/team/share", json=share_request)
        assert response.status_code == 200

        # 4. Search for workflow contexts
        response = test_client.get("/api/contexts/search?query=workflow")
        assert response.status_code == 200
        search_results = response.json()

        workflow_contexts = [c for c in search_results["contexts"] if "workflow" in c["title"].lower()]
        assert len(workflow_contexts) >= 1

        # 5. Resume session
        response = test_client.get(f"/api/sessions/resume/{session_id}")
        assert response.status_code == 200
        resumed_data = response.json()

        assert "Updated" in resumed_data["title"]

        # 6. Cleanup
        response = test_client.delete(f"/api/sessions/{session_id}")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])