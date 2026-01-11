"""
pytest configuration and fixtures
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import AsyncGenerator, Generator
import sys
import os

# Add the current directory to the path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from services.compression_service import CompressionService
from services.search_service import SearchService
from services.storage_service import StorageService
from services.context_service import ContextService
from services.scheduler_service import SchedulerService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def compression_service() -> CompressionService:
    """Create a CompressionService instance for testing."""
    return CompressionService(compression_level=6)


@pytest_asyncio.fixture
async def search_service(temp_dir: Path) -> SearchService:
    """Create a SearchService instance with temporary index directory."""
    index_path = temp_dir / "search_index"
    service = SearchService(str(index_path))
    await service.initialize_index()
    return service


@pytest.fixture
def storage_service(temp_dir: Path) -> StorageService:
    """Create a StorageService instance with temporary storage directory."""
    return StorageService(str(temp_dir / "storage"))


@pytest.fixture
async def context_service(temp_dir: Path) -> AsyncGenerator[ContextService, None]:
    """Create a ContextService instance with temporary directories."""
    # For now, we'll mock the database parts
    storage_path = str(temp_dir / "storage")
    service = ContextService(storage_path=storage_path, compression_level=6)
    yield service
    # Cleanup is handled by temp_dir fixture


@pytest.fixture
def scheduler_service() -> SchedulerService:
    """Create a SchedulerService instance for testing."""
    return SchedulerService()


@pytest.fixture
def sample_text_data() -> str:
    """Sample text data for testing compression."""
    return """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
    incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
    exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure
    dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
    Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt
    mollit anim id est laborum. Sed ut perspiciatis unde omnis iste natus error sit
    voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae
    ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.
    """ * 10  # Repeat for more substantial data


@pytest.fixture
def sample_binary_data() -> bytes:
    """Sample binary data for testing compression."""
    return bytes(range(256)) * 100  # Create patterned binary data


@pytest.fixture
def sample_context_data() -> dict:
    """Sample context data for testing."""
    return {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you for asking!"}
        ],
        "metadata": {
            "session_id": "test-session-123",
            "user_id": "test-user-456",
            "timestamp": "2024-01-01T00:00:00Z",
            "model": "claude-3-opus",
            "tokens": 150
        },
        "context": {
            "project": "test-project",
            "files": ["file1.py", "file2.py"],
            "tags": ["testing", "example"]
        }
    }


@pytest.fixture
def sample_documents() -> list:
    """Sample documents for search testing."""
    return [
        {
            "id": "doc1",
            "title": "Python Programming Guide",
            "content": "Python is a high-level programming language with dynamic semantics.",
            "file_path": "/docs/python.md",
            "file_type": "markdown",
            "tags": ["python", "programming", "guide"]
        },
        {
            "id": "doc2",
            "title": "FastAPI Documentation",
            "content": "FastAPI is a modern, fast web framework for building APIs with Python.",
            "file_path": "/docs/fastapi.md",
            "file_type": "markdown",
            "tags": ["python", "api", "web"]
        },
        {
            "id": "doc3",
            "title": "Database Design Patterns",
            "content": "Understanding database design patterns is crucial for scalable applications.",
            "file_path": "/docs/database.md",
            "file_type": "markdown",
            "tags": ["database", "design", "patterns"]
        }
    ]


# Test markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )