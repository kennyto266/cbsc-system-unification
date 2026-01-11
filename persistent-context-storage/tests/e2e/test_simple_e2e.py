"""
Simple E2E test to verify basic functionality works
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient


@pytest.mark.e2e
class BasicE2ETest:
    """Basic E2E test to verify service is working"""

    @pytest.fixture
    def client(self):
        """Create test client with temporary workspace"""
        workspace = Path(tempfile.mkdtemp())

        # Create required directories
        (workspace / "data").mkdir(exist_ok=True)
        (workspace / "storage").mkdir(exist_ok=True)
        (workspace / "search_index").mkdir(exist_ok=True)

        # Set environment variables for test
        os.environ["DATABASE_URL"] = str(workspace / "data" / "contexts.db")
        os.environ["STORAGE_PATH"] = str(workspace / "storage")
        os.environ["SEARCH_INDEX_PATH"] = str(workspace / "search_index")

        # Import app after setting environment
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        sys.path.insert(0, parent_dir)

        from main import app
        client = TestClient(app)

        yield client

        # Cleanup
        shutil.rmtree(workspace, ignore_errors=True)

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "persistent-context-storage"

    def test_basic_context_creation(self, client):
        """Test basic context creation"""
        context_data = {
            "title": "Test Context",
            "content": {
                "messages": [{"role": "user", "content": "Hello world"}],
                "metadata": {"test": True}
            },
            "description": "Basic test context",
            "user_id": "test-user",
            "tags": ["test"]
        }

        response = client.post("/api/contexts", json=context_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Context"

    def test_context_retrieval(self, client):
        """Test context retrieval"""
        # First create a context
        context_data = {
            "title": "Retrieval Test",
            "content": {"messages": [{"role": "user", "content": "Test message"}]},
            "user_id": "test-user"
        }

        create_response = client.post("/api/contexts", json=context_data)
        assert create_response.status_code == 200
        context_id = create_response.json()["id"]

        # Then retrieve it
        get_response = client.get(f"/api/contexts/{context_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == context_id
        assert data["title"] == "Retrieval Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])