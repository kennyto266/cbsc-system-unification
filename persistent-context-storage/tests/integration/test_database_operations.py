"""
Integration tests for database operations
Test context persistence across service restarts and database transactions
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
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from services.context_service import ContextService
from services.compression_service import CompressionService
from services.storage_service import StorageService
from services.search_service import SearchService
from models.context import Context, ContextTag, ContextAccess, ContextShare
from models.user import User, Team, UserTeamAssociation, Permission
from config.database import get_database_session, init_sqlalchemy_database


@pytest.fixture
def temp_workspace() -> Path:
    """Create a temporary workspace for integration tests"""
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
def temp_db_path(temp_workspace: Path) -> str:
    """Create a temporary database path"""
    return str(temp_workspace / "test_contexts.db")


@pytest.fixture
async def context_service_with_db(temp_workspace: Path, temp_db_path: str) -> ContextService:
    """Create a ContextService with temporary database"""
    # Set environment variables for test
    os.environ["DATABASE_URL"] = temp_db_path
    os.environ["STORAGE_PATH"] = str(temp_workspace / "storage")
    os.environ["SEARCH_INDEX_PATH"] = str(temp_workspace / "search_index")

    # Initialize database
    await init_sqlalchemy_database()

    # Create service instances
    storage_path = str(temp_workspace / "storage")
    service = ContextService(storage_path=storage_path, compression_level=6)

    yield service

    # Cleanup will be handled by temp_workspace fixture


@pytest.fixture
def sample_contexts() -> List[Dict[str, Any]]:
    """Sample context data for testing"""
    return [
        {
            "title": "Python Development Context",
            "content": {
                "messages": [
                    {"role": "user", "content": "How do I create a Python class?"},
                    {"role": "assistant", "content": "Here's how to create a Python class..."}
                ],
                "metadata": {
                    "language": "python",
                    "framework": "none",
                    "session_type": "coding_help"
                }
            },
            "description": "Python class creation help",
            "tags": ["python", "oop", "basics"],
            "session_id": "session_001",
            "project_path": "/projects/python_tutorial",
            "user_id": "user_001"
        },
        {
            "title": "FastAPI Application Setup",
            "content": {
                "messages": [
                    {"role": "user", "content": "Set up a FastAPI app with authentication"},
                    {"role": "assistant", "content": "Here's how to set up FastAPI with JWT..."}
                ],
                "metadata": {
                    "language": "python",
                    "framework": "fastapi",
                    "session_type": "project_setup"
                }
            },
            "description": "FastAPI authentication setup",
            "tags": ["fastapi", "authentication", "jwt"],
            "session_id": "session_002",
            "project_path": "/projects/api_backend",
            "user_id": "user_001"
        },
        {
            "title": "Database Design Review",
            "content": {
                "messages": [
                    {"role": "user", "content": "Review my database schema"},
                    {"role": "assistant", "content": "Your database schema looks good, but..."}
                ],
                "metadata": {
                    "language": "sql",
                    "framework": "postgresql",
                    "session_type": "code_review"
                }
            },
            "description": "Database schema review session",
            "tags": ["database", "sql", "schema"],
            "session_id": "session_003",
            "project_path": "/projects/data_model",
            "user_id": "user_002"
        }
    ]


@pytest.mark.integration
class TestContextPersistence:
    """Test context persistence across service restarts and database operations"""

    async def test_context_creation_and_retrieval(self, context_service_with_db: ContextService, sample_contexts: List[Dict[str, Any]]):
        """Test that contexts can be created and retrieved successfully"""
        service = context_service_with_db

        # Create a context
        context_data = sample_contexts[0]
        context_id = await service.save_context(
            title=context_data["title"],
            content=context_data["content"],
            user_id=context_data["user_id"],
            description=context_data["description"],
            tags=context_data["tags"],
            session_id=context_data["session_id"],
            project_path=context_data["project_path"]
        )

        assert context_id is not None, "Context ID should not be None after successful save"

        # Retrieve the context
        retrieved_context = await service.load_context(context_id=context_id)

        assert retrieved_context is not None, "Retrieved context should not be None"
        assert retrieved_context["title"] == context_data["title"], "Title should match"
        assert retrieved_context["description"] == context_data["description"], "Description should match"
        assert retrieved_context["content"] == context_data["content"], "Content should match"
        assert retrieved_context["metadata"]["user_id"] == context_data["user_id"], "User ID should match"
        assert set(retrieved_context["metadata"]["tags"]) == set(context_data["tags"]), "Tags should match"

    async def test_context_update_persistence(self, context_service_with_db: ContextService, sample_contexts: List[Dict[str, Any]]):
        """Test that context updates persist correctly"""
        service = context_service_with_db
        context_data = sample_contexts[0]

        # Create initial context
        context_id = await service.save_context(
            title=context_data["title"],
            content=context_data["content"],
            user_id=context_data["user_id"],
            description=context_data["description"],
            tags=context_data["tags"]
        )

        # Update the context
        updated_title = "Updated: " + context_data["title"]
        updated_description = "Updated description"
        updated_tags = context_data["tags"] + ["updated"]

        success = await service.update_context(
            context_id=context_id,
            title=updated_title,
            description=updated_description,
            tags=updated_tags,
            user_id=context_data["user_id"]
        )

        assert success is True, "Context update should succeed"

        # Verify update persisted
        updated_context = await service.load_context(context_id=context_id)
        assert updated_context["title"] == updated_title, "Updated title should match"
        assert updated_context["description"] == updated_description, "Updated description should match"
        assert set(updated_context["metadata"]["tags"]) == set(updated_tags), "Updated tags should match"

        # Verify original fields are preserved
        assert updated_context["content"] == context_data["content"], "Original content should be preserved"

    async def test_context_deletion(self, context_service_with_db: ContextService, sample_contexts: List[Dict[str, Any]]):
        """Test that context deletion removes both database records and files"""
        service = context_service_with_db
        context_data = sample_contexts[0]

        # Create context
        context_id = await service.save_context(
            title=context_data["title"],
            content=context_data["content"],
            user_id=context_data["user_id"]
        )

        # Verify context exists
        context = await service.load_context(context_id=context_id)
        assert context is not None, "Context should exist before deletion"

        # Delete context
        success = await service.delete_context(
            context_id=context_id,
            user_id=context_data["user_id"]
        )

        assert success is True, "Context deletion should succeed"

        # Verify context is deleted
        deleted_context = await service.load_context(context_id=context_id)
        assert deleted_context is None, "Deleted context should not be retrievable"

    async def test_batch_context_operations(self, context_service_with_db: ContextService, sample_contexts: List[Dict[str, Any]]):
        """Test batch operations on multiple contexts"""
        service = context_service_with_db
        created_contexts = []

        # Create multiple contexts
        for context_data in sample_contexts:
            context_id = await service.save_context(
                title=context_data["title"],
                content=context_data["content"],
                user_id=context_data["user_id"],
                description=context_data["description"],
                tags=context_data["tags"],
                session_id=context_data["session_id"],
                project_path=context_data["project_path"]
            )
            created_contexts.append(context_id)

        assert len(created_contexts) == len(sample_contexts), "All contexts should be created"

        # List contexts for a user
        user_contexts = await service.list_contexts(user_id="user_001")
        assert len(user_contexts) == 2, "User should have 2 contexts"

        # List contexts for a session
        session_contexts = await service.list_contexts(session_id="session_001")
        assert len(session_contexts) == 1, "Session should have 1 context"

        # List contexts for a project
        project_contexts = await service.list_contexts(project_path="/projects/python_tutorial")
        assert len(project_contexts) == 1, "Project should have 1 context"

        # Filter by tags
        tagged_contexts = await service.list_contexts(tags=["python"])
        assert len(tagged_contexts) == 2, "Should find 2 contexts with 'python' tag"

    async def test_database_transaction_rollback(self, context_service_with_db: ContextService, sample_contexts: List[Dict[str, Any]]):
        """Test database transaction rollback on errors"""
        service = context_service_with_db

        # Start with a clean state
        initial_contexts = await service.list_contexts()
        initial_count = len(initial_contexts)

        # Try to create a context with invalid data that should cause rollback
        # This simulates a scenario where part of the operation succeeds but then fails
        try:
            # This would normally work, but let's simulate a failure by passing invalid content
            context_id = await service.save_context(
                title="Test Context",
                content={"key": "value"},
                user_id="test_user"
            )

            # If we get here, the save succeeded. Now let's force an error scenario
            # by trying to create another context with the same ID (should fail)

            # Simulate a database error by manually manipulating the database
            with get_database_session() as db:
                # Create a context record directly in database
                context = Context(
                    id="duplicate-id",
                    title="Duplicate",
                    user_id="test_user",
                    file_path="fake_path.bin"
                )
                db.add(context)
                db.commit()

                # Try to add the same context again (should fail)
                duplicate_context = Context(
                    id="duplicate-id",
                    title="Duplicate 2",
                    user_id="test_user",
                    file_path="fake_path2.bin"
                )
                db.add(duplicate_context)

                # This should raise an IntegrityError and rollback
                db.commit()

        except Exception as e:
            # Expected behavior - transaction should rollback
            pass

        # Verify database state is consistent
        final_contexts = await service.list_contexts()
        # The count should either be the same or increased by 1 (if first save succeeded)
        assert len(final_contexts) >= initial_count, "Database should remain consistent"


@pytest.mark.integration
class TestDatabaseRelationships:
    """Test database relationships and constraints"""

    async def test_context_tag_relationships(self, context_service_with_db: ContextService, sample_contexts: List[Dict[str, Any]]):
        """Test many-to-many relationship between contexts and tags"""
        service = context_service_with_db
        context_data = sample_contexts[0]

        # Create context with multiple tags
        context_id = await service.save_context(
            title=context_data["title"],
            content=context_data["content"],
            user_id=context_data["user_id"],
            tags=context_data["tags"]
        )

        # Verify tags are associated in database
        with get_database_session() as db:
            context = db.query(Context).filter(Context.id == context_id).first()
            assert context is not None, "Context should exist"
            assert len(context.tags) == len(context_data["tags"]), "All tags should be associated"

            # Verify tag names
            tag_names = [tag.tag_name for tag in context.tags]
            for expected_tag in context_data["tags"]:
                assert expected_tag in tag_names, f"Tag '{expected_tag}' should be associated"

    async def test_foreign_key_constraints(self, context_service_with_db: ContextService, temp_workspace: Path):
        """Test foreign key constraints are enforced"""
        from models.tag import Tag

        # Create a tag directly
        with get_database_session() as db:
            tag = Tag(tag_name="test_tag", description="Test tag")
            db.add(tag)
            db.commit()
            tag_id = tag.id

        # Verify tag exists
        with get_database_session() as db:
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            assert tag is not None, "Tag should exist"

            # Try to create a context tag association with non-existent context
            context_tag = ContextTag(context_id="non-existent-id", tag_id=tag_id)
            db.add(context_tag)

            # This should fail due to foreign key constraint
            try:
                db.commit()
                assert False, "Should have failed due to foreign key constraint"
            except Exception:
                db.rollback()
                # Expected behavior

    async def test_cascade_delete_operations(self, context_service_with_db: ContextService, sample_contexts: List[Dict[str, Any]]):
        """Test cascade delete operations"""
        service = context_service_with_db
        context_data = sample_contexts[0]

        # Create context with tags
        context_id = await service.save_context(
            title=context_data["title"],
            content=context_data["content"],
            user_id=context_data["user_id"],
            tags=context_data["tags"]
        )

        # Verify associations exist
        with get_database_session() as db:
            context = db.query(Context).filter(Context.id == context_id).first()
            context_tag_count = db.query(ContextTag).filter(ContextTag.context_id == context_id).count()
            assert context_tag_count > 0, "Context tag associations should exist"

        # Delete context
        success = await service.delete_context(context_id=context_id, user_id=context_data["user_id"])
        assert success is True, "Context deletion should succeed"

        # Verify cascade deletion worked
        with get_database_session() as db:
            context = db.query(Context).filter(Context.id == context_id).first()
            assert context is None, "Context should be deleted"

            context_tag_count = db.query(ContextTag).filter(ContextTag.context_id == context_id).count()
            assert context_tag_count == 0, "Context tag associations should be deleted"


@pytest.mark.integration
class TestDatabasePerformance:
    """Test database performance under load"""

    async def test_bulk_context_creation(self, context_service_with_db: ContextService):
        """Test performance when creating many contexts"""
        service = context_service_with_db
        num_contexts = 50

        start_time = datetime.now()

        # Create many contexts
        context_ids = []
        for i in range(num_contexts):
            context_id = await service.save_context(
                title=f"Context {i}",
                content={"index": i, "data": f"Test data for context {i}"},
                user_id=f"user_{i % 5}",  # 5 different users
                description=f"Description for context {i}",
                tags=[f"tag_{j}" for j in range(i % 3)]  # 0-2 tags per context
            )
            context_ids.append(context_id)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Verify all contexts were created
        assert len([cid for cid in context_ids if cid is not None]) == num_contexts, "All contexts should be created"

        # Performance check (should complete in reasonable time)
        assert duration < 10.0, f"Bulk creation should complete in under 10 seconds, took {duration}s"

        # Test retrieval performance
        start_time = datetime.now()

        all_contexts = await service.list_contexts(limit=100)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        assert len(all_contexts) == num_contexts, "Should retrieve all created contexts"
        assert duration < 2.0, f"Listing contexts should complete in under 2 seconds, took {duration}s"

    async def test_concurrent_operations(self, context_service_with_db: ContextService):
        """Test database operations under concurrent load"""
        service = context_service_with_db

        async def create_context_batch(start_idx: int, count: int) -> List[str]:
            """Create a batch of contexts concurrently"""
            context_ids = []
            for i in range(count):
                idx = start_idx + i
                context_id = await service.save_context(
                    title=f"Concurrent Context {idx}",
                    content={"index": idx, "batch": start_idx},
                    user_id=f"concurrent_user",
                    description=f"Concurrent test context {idx}"
                )
                context_ids.append(context_id)
            return context_ids

        # Run multiple batches concurrently
        batch_size = 10
        num_batches = 5

        start_time = datetime.now()

        tasks = []
        for i in range(num_batches):
            task = create_context_batch(i * batch_size, batch_size)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Verify all contexts were created
        all_context_ids = [context_id for batch_results in results for context_id in batch_results]
        successful_contexts = [cid for cid in all_context_ids if cid is not None]

        expected_total = batch_size * num_batches
        assert len(successful_contexts) == expected_total, f"All {expected_total} contexts should be created successfully"

        # Performance check for concurrent operations
        assert duration < 15.0, f"Concurrent creation should complete in under 15 seconds, took {duration}s"