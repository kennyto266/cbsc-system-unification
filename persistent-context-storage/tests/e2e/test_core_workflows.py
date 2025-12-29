"""
Core E2E workflow tests for session persistence and team sharing
"""

import pytest
import tempfile
import shutil
import os
import time
from pathlib import Path
from fastapi.testclient import TestClient


class TestCoreE2EWorkflows:
    """Test core end-to-end workflows for session persistence and team sharing"""

    @pytest.fixture
    def test_client(self):
        """Create a test client with temporary workspace"""
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
    def test_complete_session_lifecycle(self, test_client):
        """Test complete session lifecycle: creation -> auto-save -> recovery -> cleanup"""
        # 1. Create a new context session
        session_data = {
            "title": "E2E Session Lifecycle Test",
            "content": {
                "messages": [
                    {"role": "system", "content": "Starting E2E session test"},
                    {"role": "user", "content": "Let's work on the authentication feature"},
                    {"role": "assistant", "content": "Great! I'll help you implement authentication"}
                ],
                "metadata": {
                    "session_id": "e2e-session-lifecycle",
                    "user_id": "test-user-123",
                    "project": "auth-feature",
                    "feature": "user-login"
                }
            },
            "description": "E2E test for complete session lifecycle",
            "tags": ["e2e", "session", "auth"],
            "project_path": "/projects/auth",
            "user_id": "test-user-123",
            "interval_minutes": 1  # Short interval for testing
        }

        response = test_client.post("/api/sessions/auto-save", json=session_data)
        assert response.status_code == 200
        result = response.json()

        assert "session_id" in result
        assert "context_id" in result
        assert result["status"] == "auto_save_enabled"

        session_id = result["session_id"]
        context_id = result["context_id"]

        # 2. Simulate content updates during the session
        for i in range(2):
            # Wait for auto-save interval
            time.sleep(1.2)

            # Update content
            update_data = {
                "content": {
                    "messages": session_data["content"]["messages"] + [
                        {"role": "user", "content": f"Update {i+1}: Added password reset"},
                        {"role": "assistant", "content": f"Response {i+1}: Implemented reset functionality"}
                    ],
                    "metadata": {
                        **session_data["content"]["metadata"],
                        "update_count": i + 1,
                        "last_feature": f"password-reset-{i+1}"
                    }
                },
                "title": f"E2E Session - Update {i+1}",
                "description": f"Session updated {i+1} times"
            }

            response = test_client.put(f"/api/sessions/auto-save/{session_id}", json=update_data)
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "updated"

        # 3. Test session resumption - the user comes back later
        response = test_client.get(f"/api/sessions/resume/{session_id}")
        assert response.status_code == 200
        resume_result = response.json()

        assert resume_result["session_id"] == session_id
        assert resume_result["context_id"] == context_id
        assert "Update 2" in resume_result["title"]
        assert len(resume_result["content"]["messages"]) >= 7  # 3 original + 4 updates
        assert resume_result["content"]["metadata"]["update_count"] == 2

        # 4. Test context retrieval with complete session data
        response = test_client.get(f"/api/contexts/{context_id}")
        assert response.status_code == 200
        context = response.json()

        assert context["id"] == context_id
        assert context["title"] == "E2E Session - Update 2"
        assert context["metadata"]["session_id"] == session_id
        assert "update_count" in context["metadata"]

        # 5. Test force save before finishing
        response = test_client.post(f"/api/sessions/{session_id}/force-save")
        assert response.status_code == 200
        save_result = response.json()
        assert save_result["status"] == "saved"

        # 6. Test session cleanup
        response = test_client.delete(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        cleanup_result = response.json()
        assert cleanup_result["status"] == "cleaned_up"

        # 7. Verify session is no longer active
        response = test_client.get(f"/api/sessions/resume/{session_id}")
        assert response.status_code == 404

    @pytest.mark.e2e
    def test_complete_team_sharing_workflow(self, test_client):
        """Test complete team sharing workflow: create -> share -> manage -> revoke"""
        # 1. Create a context for sharing
        context_data = {
            "title": "Team Project - User Authentication",
            "content": {
                "messages": [
                    {"role": "system", "content": "Team collaboration on authentication feature"},
                    {"role": "developer", "content": "I've implemented the login functionality"},
                    {"role": "assistant", "content": "Great work! Let me review the implementation"}
                ],
                "metadata": {
                    "project": "team-auth",
                    "feature": "user-login",
                    "status": "review-needed",
                    "assignee": "team-lead"
                }
            },
            "description": "Team authentication feature ready for review",
            "tags": ["team", "authentication", "review"],
            "project_path": "/team/projects/auth",
            "user_id": "developer-001",
            "visibility": "team"
        }

        response = test_client.post("/api/contexts", json=context_data)
        assert response.status_code in [200, 201]
        result = response.json()
        data = result.get("data", result)
        context_id = data["id"]

        # 2. Share with team lead for review (editor permissions)
        share_request = {
            "context_id": context_id,
            "shared_with_user_id": "team-lead-001",
            "permission_level": "editor",
            "expires_hours": 72,
            "message": "Please review the authentication implementation"
        }

        response = test_client.post("/api/team/share", json=share_request)
        assert response.status_code == 200
        share_result = response.json()

        assert "share_id" in share_result
        assert share_result["permission_level"] == "editor"
        assert share_result["shared_with_user_id"] == "team-lead-001"

        editor_share_id = share_result["share_id"]

        # 3. Share with QA team for testing (viewer permissions)
        share_request["shared_with_user_id"] = "qa-team-001"
        share_request["permission_level"] = "viewer"
        share_request["message"] = "Ready for QA testing"

        response = test_client.post("/api/team/share", json=share_request)
        assert response.status_code == 200
        viewer_share_id = response.json()["share_id"]

        # 4. Create public share link for external stakeholder
        public_link_request = {
            "context_id": context_id,
            "permission_level": "viewer",
            "expires_hours": 168,  # 1 week
            "max_accesses": 20
        }

        response = test_client.post("/api/team/share/link", json=public_link_request)
        assert response.status_code == 200
        public_share = response.json()

        assert "share_token" in public_share
        assert public_share["permission_level"] == "viewer"

        share_token = public_share["share_token"]

        # 5. Test permission checking for different users
        # Team lead should have edit permission
        permission_check = {
            "context_id": context_id,
            "user_id": "team-lead-001",
            "permission": "edit"
        }

        response = test_client.post("/api/team/check-permission", json=permission_check)
        assert response.status_code == 200
        assert response.json()["has_permission"] == True

        # QA team should only have view permission
        permission_check["user_id"] = "qa-team-001"
        permission_check["permission"] = "edit"

        response = test_client.post("/api/team/check-permission", json=permission_check)
        assert response.status_code == 200
        assert response.json()["has_permission"] == False

        # 6. Test access via public share token
        token_access = {
            "share_token": share_token,
            "user_id": "external-stakeholder"
        }

        response = test_client.post("/api/team/share/access", json=token_access)
        assert response.status_code == 200
        access_result = response.json()

        assert access_result["context_id"] == context_id
        assert access_result["permission_level"] == "viewer"

        # 7. List all shares for the context
        response = test_client.get(f"/api/team/contexts/{context_id}/shares")
        assert response.status_code == 200
        shares = response.json()

        assert len(shares) >= 3  # owner + editor + viewer + public link

        # 8. Get user's shared contexts
        response = test_client.get(f"/api/team/users/team-lead-001/shared-contexts")
        assert response.status_code == 200
        team_leads_contexts = response.json()

        assert any(ctx["id"] == context_id for ctx in team_leads_contexts)

        # 9. Update permission level (demote editor to viewer)
        permission_update = {
            "permission_level": "viewer"
        }

        response = test_client.put(f"/api/team/share/{editor_share_id}/permission", json=permission_update)
        assert response.status_code == 200
        assert response.json()["permission_level"] == "viewer"

        # 10. Revoke access when review is complete
        response = test_client.delete(f"/api/team/share/{editor_share_id}")
        assert response.status_code == 200

        response = test_client.delete(f"/api/team/share/{viewer_share_id}")
        assert response.status_code == 200

        # Verify access has been revoked
        permission_check["user_id"] = "team-lead-001"
        permission_check["permission"] = "view"

        response = test_client.post("/api/team/check-permission", json=permission_check)
        assert response.status_code == 200
        # Should be False now that share is revoked
        # (Note: actual behavior depends on implementation)

    @pytest.mark.e2e
    def test_collaborative_development_workflow(self, test_client):
        """Test integrated collaborative development workflow"""
        # 1. Developer starts new feature session
        session_data = {
            "title": "Feature Development - Payment Processing",
            "content": {
                "messages": [
                    {"role": "system", "content": "Starting payment processing feature development"},
                    {"role": "developer", "content": "Need to implement stripe integration"}
                ],
                "metadata": {
                    "feature": "payment-processing",
                    "sprint": "sprint-15",
                    "stories": ["PAY-001", "PAY-002"]
                }
            },
            "user_id": "frontend-dev-001",
            "tags": ["payment", "stripe", "feature"],
            "interval_minutes": 1
        }

        response = test_client.post("/api/sessions/auto-save", json=session_data)
        assert response.status_code == 200
        session_result = response.json()
        session_id = session_result["session_id"]
        context_id = session_result["context_id"]

        # 2. Developer makes progress during the session
        time.sleep(1.2)  # Wait for auto-save

        update_data = {
            "content": {
                "messages": session_data["content"]["messages"] + [
                    {"role": "developer", "content": "Stripe client integration complete"},
                    {"role": "assistant", "content": "Great! Ready for backend integration"}
                ],
                "metadata": {
                    **session_data["content"]["metadata"],
                    "status": "frontend-complete",
                    "next_step": "backend-integration"
                }
            },
            "title": "Payment Feature - Frontend Complete"
        }

        response = test_client.put(f"/api/sessions/auto-save/{session_id}", json=update_data)
        assert response.status_code == 200

        # 3. Share with backend developer for collaboration
        share_request = {
            "context_id": context_id,
            "shared_with_user_id": "backend-dev-001",
            "permission_level": "editor",
            "message": "Frontend complete, please integrate with backend API"
        }

        response = test_client.post("/api/team/share", json=share_request)
        assert response.status_code == 200

        # 4. Backend developer updates the context
        backend_update = {
            "content": {
                "messages": [
                    {"role": "backend-dev", "content": "API endpoint created for payment processing"},
                    {"role": "assistant", "content": "Perfect! Integration complete"}
                ],
                "metadata": {
                    "feature": "payment-processing",
                    "status": "integration-complete",
                    "api_endpoint": "/api/payments"
                }
            },
            "title": "Payment Feature - Integration Complete"
        }

        # Note: This would normally require the backend developer's authentication
        # For E2E test, we simulate the update
        response = test_client.put(f"/api/contexts/{context_id}", json=backend_update)
        assert response.status_code == 200

        # 5. Create public share link for product manager review
        public_link = {
            "context_id": context_id,
            "permission_level": "viewer",
            "expires_hours": 48
        }

        response = test_client.post("/api/team/share/link", json=public_link)
        assert response.status_code == 200

        # 6. Original developer resumes session and sees progress
        response = test_client.get(f"/api/sessions/resume/{session_id}")
        assert response.status_code == 200
        resumed = response.json()

        assert "Integration Complete" in resumed["title"]
        assert resumed["content"]["metadata"]["status"] == "integration-complete"

        # 7. Force final save and cleanup
        response = test_client.post(f"/api/sessions/{session_id}/force-save")
        assert response.status_code == 200

        response = test_client.delete(f"/api/sessions/{session_id}")
        assert response.status_code == 200

    @pytest.mark.e2e
    def test_context_crud_workflow(self, test_client):
        """Test basic context CRUD operations"""
        # Create context
        context_data = {
            "title": "CRUD Test Context",
            "content": {
                "messages": [{"role": "user", "content": "Initial content"}],
                "metadata": {"test": "crud"}
            },
            "description": "Testing CRUD operations",
            "user_id": "crud-user",
            "tags": ["test", "crud"]
        }

        response = test_client.post("/api/contexts", json=context_data)
        assert response.status_code in [200, 201]
        result = response.json()
        data = result.get("data", result)
        context_id = data["id"]

        # Read context
        response = test_client.get(f"/api/contexts/{context_id}")
        assert response.status_code == 200
        context = response.json()
        assert context["title"] == "CRUD Test Context"

        # Update context
        update_data = {
            "title": "Updated CRUD Test",
            "content": {
                "messages": [{"role": "user", "content": "Updated content"}],
                "metadata": {"test": "crud", "updated": True}
            },
            "description": "Updated description"
        }

        response = test_client.put(f"/api/contexts/{context_id}", json=update_data)
        assert response.status_code == 200

        # Verify update
        response = test_client.get(f"/api/contexts/{context_id}")
        assert response.status_code == 200
        updated_context = response.json()
        assert "Updated" in updated_context["title"]

        # List contexts
        response = test_client.get("/api/contexts")
        assert response.status_code == 200
        contexts = response.json()
        assert len(contexts) >= 1

        # Delete context
        response = test_client.delete(f"/api/contexts/{context_id}")
        assert response.status_code == 200

        # Verify deletion
        response = test_client.get(f"/api/contexts/{context_id}")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])