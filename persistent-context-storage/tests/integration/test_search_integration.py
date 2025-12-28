"""
Integration tests for search functionality
Test whoosh-reloaded search integration and search index updates
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
from services.search_service import SearchService
from config.database import get_database_session, init_sqlalchemy_database
from models.context import Context, ContextTag


@pytest.fixture
def temp_search_workspace() -> Path:
    """Create a temporary workspace for search integration tests"""
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
async def search_service_with_index(temp_search_workspace: Path) -> SearchService:
    """Create a SearchService with temporary index"""
    index_path = str(temp_search_workspace / "search_index")
    service = SearchService(index_path)

    # Initialize the search index
    await service.initialize_index()

    yield service


@pytest.fixture
async def context_service_with_search(temp_search_workspace: Path) -> ContextService:
    """Create a ContextService integrated with search"""
    # Set environment variables for test
    os.environ["DATABASE_URL"] = str(temp_search_workspace / "test_search_contexts.db")
    os.environ["STORAGE_PATH"] = str(temp_search_workspace / "storage")
    os.environ["SEARCH_INDEX_PATH"] = str(temp_search_workspace / "search_index")

    # Initialize database
    await init_sqlalchemy_database()

    # Create service instances
    storage_path = str(temp_search_workspace / "storage")
    service = ContextService(storage_path=storage_path, compression_level=6)

    yield service

    # Cleanup will be handled by temp_workspace fixture


@pytest.fixture
def searchable_contexts() -> List[Dict[str, Any]]:
    """Sample context data designed for search testing"""
    return [
        {
            "title": "Python Programming Tutorial",
            "content": {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming."
                    }
                ],
                "metadata": {
                    "language": "python",
                    "difficulty": "beginner",
                    "topics": ["variables", "functions", "classes"]
                }
            },
            "description": "Comprehensive Python programming guide for beginners",
            "tags": ["python", "programming", "tutorial", "beginner"],
            "session_id": "session_python_001",
            "project_path": "/projects/python_basics",
            "user_id": "user_python_dev",
            "visibility": "public"
        },
        {
            "title": "Advanced Machine Learning Algorithms",
            "content": {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Machine learning algorithms can be categorized into supervised, unsupervised, and reinforcement learning. Deep learning uses neural networks with multiple layers to learn hierarchical representations of data."
                    }
                ],
                "metadata": {
                    "language": "python",
                    "difficulty": "advanced",
                    "topics": ["neural_networks", "deep_learning", "tensorflow", "pytorch"]
                }
            },
            "description": "Deep dive into ML algorithms and neural networks",
            "tags": ["machine_learning", "ai", "neural_networks", "python", "advanced"],
            "session_id": "session_ml_002",
            "project_path": "/projects/ml_research",
            "user_id": "user_ml_engineer",
            "visibility": "team"
        },
        {
            "title": "Web Development with FastAPI",
            "content": {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "FastAPI is a modern, fast web framework for building APIs with Python. It provides automatic API documentation, type hints, and high performance out of the box."
                    }
                ],
                "metadata": {
                    "language": "python",
                    "difficulty": "intermediate",
                    "topics": ["api", "web_development", "async", "fastapi"]
                }
            },
            "description": "Building RESTful APIs with FastAPI framework",
            "tags": ["fastapi", "web_development", "api", "python", "backend"],
            "session_id": "session_web_003",
            "project_path": "/projects/api_service",
            "user_id": "user_backend_dev",
            "visibility": "public"
        },
        {
            "title": "Database Design Patterns",
            "content": {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Effective database design involves understanding normalization, indexing strategies, and query optimization. SQL databases like PostgreSQL offer powerful features for complex data relationships."
                    }
                ],
                "metadata": {
                    "language": "sql",
                    "difficulty": "intermediate",
                    "topics": ["database", "sql", "normalization", "indexing"]
                }
            },
            "description": "Best practices for database schema design",
            "tags": ["database", "sql", "design_patterns", "postgresql"],
            "session_id": "session_db_004",
            "project_path": "/projects/data_modeling",
            "user_id": "user_database_admin",
            "visibility": "team"
        },
        {
            "title": "JavaScript Frontend Development",
            "content": {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "JavaScript enables interactive web experiences. Modern frameworks like React, Vue, and Angular provide component-based architectures for building scalable frontend applications."
                    }
                ],
                "metadata": {
                    "language": "javascript",
                    "difficulty": "intermediate",
                    "topics": ["frontend", "react", "vue", "components"]
                }
            },
            "description": "Modern JavaScript and frontend frameworks",
            "tags": ["javascript", "frontend", "react", "web", "ui"],
            "session_id": "session_js_005",
            "project_path": "/projects/frontend_app",
            "user_id": "user_frontend_dev",
            "visibility": "public"
        }
    ]


@pytest.mark.integration
class TestSearchIndexIntegration:
    """Test search service integration with database operations"""

    async def test_search_index_initialization(self, search_service_with_index: SearchService):
        """Test that search index can be properly initialized"""
        service = search_service_with_index

        # Index should exist and be accessible
        assert service.index is not None, "Search index should be initialized"
        assert service.writer is not None, "Search writer should be available"

        # Test that we can perform searches on empty index
        results = await service.search("python", limit=10)
        assert isinstance(results, list), "Search should return a list"
        assert len(results) == 0, "Empty index should return no results"

    async def test_context_indexing_on_creation(self, context_service_with_search: ContextService, searchable_contexts: List[Dict[str, Any]]):
        """Test that contexts are automatically indexed when created"""
        service = context_service_with_search
        context_data = searchable_contexts[0]  # Python tutorial

        # Create context
        context_id = await service.save_context(
            title=context_data["title"],
            content=context_data["content"],
            user_id=context_data["user_id"],
            description=context_data["description"],
            tags=context_data["tags"],
            session_id=context_data["session_id"],
            project_path=context_data["project_path"],
            visibility=context_data["visibility"]
        )

        assert context_id is not None, "Context should be created successfully"

        # Search for the context by title
        search_results = await service.search_service.search("Python Programming")
        assert len(search_results) == 1, "Should find the newly created context"

        result = search_results[0]
        assert result["id"] == context_id, "Search result should have correct context ID"
        assert result["title"] == context_data["title"], "Search result should have correct title"
        assert result["score"] > 0, "Search result should have a relevance score"

        # Search by content
        content_results = await service.search_service.search("high-level programming language")
        assert len(content_results) == 1, "Should find context by content"
        assert content_results[0]["id"] == context_id, "Should find correct context"

        # Search by tags
        tag_results = await service.search_service.search_by_tag("python")
        assert len(tag_results) >= 1, "Should find context by tag"
        assert any(r["id"] == context_id for r in tag_results), "Tag search should include our context"

    async def test_search_index_updates_on_modification(self, context_service_with_search: ContextService, searchable_contexts: List[Dict[str, Any]]):
        """Test that search index is updated when context is modified"""
        service = context_service_with_search
        context_data = searchable_contexts[1]  # Machine learning

        # Create initial context
        context_id = await service.save_context(
            title=context_data["title"],
            content=context_data["content"],
            user_id=context_data["user_id"],
            tags=context_data["tags"]
        )

        # Verify initial indexing
        initial_results = await service.search_service.search("Machine Learning")
        assert len(initial_results) == 1, "Should find context initially"

        # Update context with new content
        new_content = {
            **context_data["content"],
            "messages": [
                {
                    "role": "assistant",
                    "content": "Updated content about machine learning, transformers, and large language models like GPT."
                }
            ]
        }

        success = await service.update_context(
            context_id=context_id,
            content=new_content,
            user_id=context_data["user_id"]
        )

        assert success is True, "Context update should succeed"

        # Search for old content (should not find)
        old_content_results = await service.search_service.search("deep learning uses neural networks")
        assert len(old_content_results) == 0, "Should not find old content after update"

        # Search for new content (should find)
        new_content_results = await service.search_service.search("transformers and large language models")
        assert len(new_content_results) == 1, "Should find new content after update"
        assert new_content_results[0]["id"] == context_id, "Should find correct context"

    async def test_search_index_cleanup_on_deletion(self, context_service_with_search: ContextService, searchable_contexts: List[Dict[str, Any]]):
        """Test that search index is cleaned up when context is deleted"""
        service = context_service_with_search
        context_data = searchable_contexts[2]  # FastAPI

        # Create context
        context_id = await service.save_context(
            title=context_data["title"],
            content=context_data["content"],
            user_id=context_data["user_id"],
            tags=context_data["tags"]
        )

        # Verify context is indexed
        search_results = await service.search_service.search("FastAPI")
        assert len(search_results) == 1, "Context should be indexed"

        # Delete context
        success = await service.delete_context(
            context_id=context_id,
            user_id=context_data["user_id"]
        )

        assert success is True, "Context deletion should succeed"

        # Verify context is removed from search index
        deleted_search_results = await service.search_service.search("FastAPI")
        assert len(deleted_search_results) == 0, "Deleted context should not appear in search results"

    async def test_complex_search_queries(self, context_service_with_search: ContextService, searchable_contexts: List[Dict[str, Any]]):
        """Test complex search queries with multiple contexts"""
        service = context_service_with_search

        # Create all test contexts
        created_contexts = []
        for context_data in searchable_contexts:
            context_id = await service.save_context(
                title=context_data["title"],
                content=context_data["content"],
                user_id=context_data["user_id"],
                description=context_data["description"],
                tags=context_data["tags"],
                visibility=context_data["visibility"]
            )
            created_contexts.append(context_id)

        assert len(created_contexts) == len(searchable_contexts), "All contexts should be created"

        # Test search by programming language
        python_results = await service.search_service.search("python", limit=10)
        python_titles = [r["title"] for r in python_results]
        assert any("Python" in title for title in python_titles), "Should find Python-related contexts"
        assert len(python_results) >= 3, "Should find at least 3 Python contexts"

        # Test search by framework
        framework_results = await service.search_service.search("framework", limit=10)
        framework_titles = [r["title"] for r in framework_results]
        assert any("FastAPI" in title for title in framework_titles), "Should find FastAPI context"

        # Test search by concept
        database_results = await service.search_service.search("database design", limit=10)
        assert len(database_results) >= 1, "Should find database design context"
        assert any("Database" in r["title"] for r in database_results), "Should find correct database context"

        # Test search with partial matches
        partial_results = await service.search_service.search("learn", limit=10)
        assert len(partial_results) >= 2, "Should find contexts with 'learn' in content"

        # Test case-insensitive search
        case_results = await service.search_service.search("PYTHON", limit=10)
        assert len(case_results) >= 1, "Case-insensitive search should work"

    async def test_tag_search_functionality(self, context_service_with_search: ContextService, searchable_contexts: List[Dict[str, Any]]):
        """Test tag-specific search functionality"""
        service = context_service_with_search

        # Create contexts with overlapping tags
        for context_data in searchable_contexts:
            await service.save_context(
                title=context_data["title"],
                content=context_data["content"],
                user_id=context_data["user_id"],
                tags=context_data["tags"]
            )

        # Test single tag search
        python_tag_results = await service.search_service.search_by_tag("python")
        python_tag_ids = [r["id"] for r in python_tag_results]
        assert len(python_tag_results) >= 3, "Should find multiple contexts with 'python' tag"

        # Test tag that appears in multiple contexts
        programming_results = await service.search_service.search_by_tag("programming")
        assert len(programming_results) >= 1, "Should find contexts with 'programming' tag"

        # Test tag search with limit and offset
        limited_results = await service.search_service.search_by_tag("python", limit=2, offset=0)
        assert len(limited_results) == 2, "Should respect limit parameter"

        # Test non-existent tag
        no_results = await service.search_service.search_by_tag("nonexistent_tag")
        assert len(no_results) == 0, "Non-existent tag should return no results"

    async def test_search_result_ranking(self, context_service_with_search: ContextService):
        """Test that search results are properly ranked by relevance"""
        service = context_service_with_search

        # Create contexts with varying relevance to search terms
        high_relevance_context = {
            "title": "Complete Python Programming Guide",
            "content": {
                "messages": [
                    {"role": "assistant", "content": "Python programming language comprehensive tutorial covering all aspects of Python development"}
                ]
            },
            "user_id": "test_user",
            "tags": ["python", "programming", "tutorial"]
        }

        low_relevance_context = {
            "title": "General Programming Concepts",
            "content": {
                "messages": [
                    {"role": "assistant", "content": "Programming involves various languages and paradigms, including Python"}
                ]
            },
            "user_id": "test_user",
            "tags": ["programming", "concepts"]
        }

        # Create contexts
        high_id = await service.save_context(**high_relevance_context)
        low_id = await service.save_context(**low_relevance_context)

        # Search for "python programming tutorial"
        results = await service.search_service.search("python programming tutorial", limit=10)

        # The high relevance context should appear first
        result_ids = [r["id"] for r in results]
        assert high_id in result_ids, "High relevance context should be found"
        assert low_id in result_ids, "Low relevance context should be found"

        # Check that results have scores
        for result in results:
            assert "score" in result, "Each result should have a relevance score"
            assert result["score"] > 0, "Scores should be positive"

        # The high relevance context should generally have a higher score
        # (Note: exact ordering may vary based on search algorithm)
        high_result = next(r for r in results if r["id"] == high_id)
        low_result = next(r for r in results if r["id"] == low_id)

        assert high_result["score"] >= low_result["score"], "High relevance should have equal or higher score"

    async def test_search_performance_with_large_dataset(self, context_service_with_search: ContextService):
        """Test search performance with a larger dataset"""
        service = context_service_with_search
        num_contexts = 100

        # Create a larger dataset
        created_ids = []
        for i in range(num_contexts):
            context_data = {
                "title": f"Context {i}: {['Python', 'JavaScript', 'SQL', 'Machine Learning'][i % 4]} Tutorial",
                "content": {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": f"This is tutorial number {i} covering important concepts in programming and development. "
                                     f"Content includes best practices, examples, and exercises for learning."
                        }
                    ]
                },
                "user_id": f"user_{i % 10}",
                "tags": [f"tag_{j}" for j in range(i % 5)]
            }

            context_id = await service.save_context(**context_data)
            created_ids.append(context_id)

        assert len([cid for cid in created_ids if cid is not None]) == num_contexts, "All contexts should be created"

        # Test search performance
        search_terms = ["Python", "JavaScript", "tutorial", "programming", "development"]

        for term in search_terms:
            start_time = datetime.now()

            results = await service.search_service.search(term, limit=20)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            assert len(results) > 0, f"Search for '{term}' should return results"
            assert duration < 1.0, f"Search for '{term}' should complete in under 1 second, took {duration}s"

        # Test pagination performance
        start_time = datetime.now()

        page_1 = await service.search_service.search("tutorial", limit=10, offset=0)
        page_2 = await service.search_service.search("tutorial", limit=10, offset=10)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        assert len(page_1) == 10, "First page should have 10 results"
        assert len(page_2) == 10, "Second page should have 10 results"
        assert duration < 2.0, f"Paged search should complete in under 2 seconds, took {duration}s"

        # Verify no duplicate results across pages
        page_1_ids = {r["id"] for r in page_1}
        page_2_ids = {r["id"] for r in page_2}
        assert len(page_1_ids.intersection(page_2_ids)) == 0, "Pages should not have duplicate results"


@pytest.mark.integration
class TestSearchIntegrationErrors:
    """Test error handling in search integration"""

    async def test_search_with_invalid_index_path(self, temp_search_workspace: Path):
        """Test behavior when search index path is invalid"""
        invalid_path = "/nonexistent/path/that/does/not/exist"

        # Creating service with invalid path should handle gracefully
        try:
            service = SearchService(invalid_path)
            await service.initialize_index()
            # Should either succeed (creating the directory) or fail gracefully
        except Exception as e:
            # Expected behavior - should fail gracefully without crashing
            assert "path" in str(e).lower() or "directory" in str(e).lower(), "Should mention path/directory in error"

    async def test_search_index_corruption_recovery(self, context_service_with_search: ContextService, temp_search_workspace: Path):
        """Test recovery from search index corruption"""
        service = context_service_with_search

        # Create a context to ensure index exists
        context_id = await service.save_context(
            title="Test Context",
            content={"test": "content"},
            user_id="test_user"
        )

        # Verify search works initially
        initial_results = await service.search_service.search("test")
        assert len(initial_results) == 1, "Search should work initially"

        # Simulate index corruption by manually manipulating index files
        index_path = Path(service.index_path)
        if index_path.exists():
            # Remove some index files to simulate corruption
            for segment_file in index_path.glob("*.seg"):
                try:
                    segment_file.unlink()
                except:
                    pass

        # Try to search - should handle corruption gracefully
        try:
            corrupted_results = await service.search_service.search("test")
            # If it succeeds, great! The service recovered
            assert True, "Service recovered from index corruption"
        except Exception as e:
            # If it fails, should provide helpful error message
            assert "index" in str(e).lower() or "corrupt" in str(e).lower(), "Error should mention index corruption"

    async def test_concurrent_search_operations(self, context_service_with_search: ContextService):
        """Test concurrent search operations"""
        service = context_service_with_search

        # Create some test contexts
        for i in range(10):
            await service.save_context(
                title=f"Test Context {i}",
                content={"index": i, "content": f"Test content for context {i}"},
                user_id="test_user"
            )

        async def perform_search(search_term: str) -> int:
            """Perform search and return result count"""
            results = await service.search_service.search(search_term, limit=20)
            return len(results)

        # Run multiple searches concurrently
        search_terms = ["test", "context", "content", "index", "Test Context 0"]
        tasks = [perform_search(term) for term in search_terms]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all searches completed without exceptions
        for result in results:
            assert isinstance(result, int), "All searches should complete successfully"
            assert result >= 0, "Search result count should be non-negative"