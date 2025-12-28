"""
Unit tests for SearchService
"""

import pytest
import asyncio
from datetime import datetime
from services.search_service import SearchService


class TestSearchService:
    """Test cases for SearchService"""

    @pytest.mark.asyncio
    async def test_init_default(self):
        """Test SearchService initialization with default parameters."""
        service = SearchService()
        assert service.index_path.name == "search_index"
        assert service.index_path.parent.name == "data"
        assert service.schema is not None
        assert 'id' in service.schema
        assert 'title' in service.schema
        assert 'content' in service.schema

    @pytest.mark.asyncio
    async def test_init_custom_path(self):
        """Test SearchService initialization with custom path."""
        custom_path = "/tmp/test_index"
        service = SearchService(custom_path)
        assert str(service.index_path) == custom_path

    @pytest.mark.asyncio
    async def test_initialize_index_new(self, temp_dir):
        """Test creating a new index."""
        index_path = temp_dir / "new_index"
        service = SearchService(str(index_path))

        result = await service.initialize_index()

        assert result is True
        assert service.index is not None
        assert index_path.exists()
        assert any(index_path.iterdir())  # Index files should be created

    @pytest.mark.asyncio
    async def test_initialize_index_existing(self, search_service):
        """Test opening an existing index."""
        # Index should already be initialized by fixture
        result = await search_service.initialize_index()

        assert result is True
        assert search_service.index is not None

    @pytest.mark.asyncio
    async def test_add_document(self, search_service):
        """Test adding a document to the index."""
        result = await search_service.add_document(
            doc_id="test_doc_1",
            title="Test Document",
            content="This is a test document for search indexing.",
            file_path="/test/path.txt",
            file_type="text",
            tags=["test", "document"],
            metadata={"author": "test_user", "version": 1}
        )

        assert result is True

        # Verify document was added
        doc_count = await search_service.get_document_count()
        assert doc_count == 1

    @pytest.mark.asyncio
    async def test_add_document_minimal(self, search_service):
        """Test adding a document with minimal required fields."""
        result = await search_service.add_document(
            doc_id="test_doc_minimal",
            title="Minimal Document",
            content="Minimal content",
            file_path="/test/minimal.txt"
        )

        assert result is True

        # Verify document was added
        doc_count = await search_service.get_document_count()
        assert doc_count == 1

    @pytest.mark.asyncio
    async def test_add_document_no_index(self, temp_dir):
        """Test adding document when index is not initialized."""
        service = SearchService(str(temp_dir / "no_init"))
        # Don't initialize the index

        result = await service.add_document(
            doc_id="test_doc",
            title="Test",
            content="Test content"
        )

        # Should auto-initialize and succeed
        assert result is True

    @pytest.mark.asyncio
    async def test_update_document(self, search_service):
        """Test updating an existing document."""
        # First add a document
        await search_service.add_document(
            doc_id="test_update",
            title="Original Title",
            content="Original content",
            file_path="/test/original.txt",
            tags=["original"]
        )

        # Update the document
        result = await search_service.update_document(
            doc_id="test_update",
            title="Updated Title",
            content="Updated content with more information",
            tags=["updated", "modified"]
        )

        assert result is True

        # Verify the update by retrieving the document
        doc = await search_service.get_document_by_id("test_update")
        assert doc is not None
        assert doc['title'] == "Updated Title"
        assert "Updated content" in doc['content']
        assert "updated" in doc['tags']

    @pytest.mark.asyncio
    async def test_update_nonexistent_document(self, search_service):
        """Test updating a document that doesn't exist."""
        result = await search_service.update_document(
            doc_id="nonexistent",
            title="New Title"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_document(self, search_service):
        """Test deleting a document."""
        # First add a document
        await search_service.add_document(
            doc_id="test_delete",
            title="To Delete",
            content="This will be deleted",
            file_path="/test/delete.txt"
        )

        # Verify it was added
        doc_count = await search_service.get_document_count()
        assert doc_count == 1

        # Delete the document
        result = await search_service.delete_document("test_delete")

        assert result is True

        # Verify it was deleted
        doc_count = await search_service.get_document_count()
        assert doc_count == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, search_service):
        """Test deleting a document that doesn't exist."""
        result = await search_service.delete_document("nonexistent")
        assert result is True  # Whoosh doesn't error on deleting non-existent docs

    @pytest.mark.asyncio
    async def test_search_basic(self, search_service, sample_documents):
        """Test basic text search."""
        # Add sample documents
        for doc in sample_documents:
            await search_service.add_document(**doc)

        # Search for "Python"
        results = await search_service.search("Python")

        assert len(results) == 2  # Should find doc1 and doc2
        for result in results:
            assert "python" in result['title'].lower() or "python" in result['content'].lower()

    @pytest.mark.asyncio
    async def test_search_empty_query(self, search_service):
        """Test search with empty query."""
        results = await search_service.search("")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_whitespace_query(self, search_service):
        """Test search with whitespace-only query."""
        results = await search_service.search("   ")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_specific_fields(self, search_service, sample_documents):
        """Test searching in specific fields."""
        for doc in sample_documents:
            await search_service.add_document(**doc)

        # Search only in title field
        results = await search_service.search("FastAPI", fields=['title'])

        assert len(results) == 1
        assert results[0]['title'] == "FastAPI Documentation"

    @pytest.mark.asyncio
    async def test_search_pagination(self, search_service, sample_documents):
        """Test search with pagination."""
        for doc in sample_documents:
            await search_service.add_document(**doc)

        # Get first page
        page1 = await search_service.search("python", limit=1, offset=0)

        # Get second page
        page2 = await search_service.search("python", limit=1, offset=1)

        # Should get different results
        assert len(page1) == 1
        assert len(page2) == 1
        assert page1[0]['id'] != page2[0]['id']

    @pytest.mark.asyncio
    async def test_search_by_tag(self, search_service, sample_documents):
        """Test searching by tag."""
        for doc in sample_documents:
            await search_service.add_document(**doc)

        # Search for "database" tag
        results = await search_service.search_by_tag("database")

        assert len(results) == 1
        assert results[0]['id'] == "doc3"

    @pytest.mark.asyncio
    async def test_search_by_file_type(self, search_service, sample_documents):
        """Test searching by file type."""
        for doc in sample_documents:
            await search_service.add_document(**doc)

        # Search for markdown files
        results = await search_service.search_by_file_type("markdown")

        assert len(results) == 3  # All docs are markdown

    @pytest.mark.asyncio
    async def test_get_document_by_id(self, search_service):
        """Test retrieving a document by ID."""
        # Add a document
        await search_service.add_document(
            doc_id="test_get",
            title="Retrieve Me",
            content="Content to retrieve",
            file_path="/test/retrieve.txt",
            file_type="text",
            tags=["test"],
            metadata={"key": "value"}
        )

        # Retrieve the document
        doc = await search_service.get_document_by_id("test_get")

        assert doc is not None
        assert doc['id'] == "test_get"
        assert doc['title'] == "Retrieve Me"
        assert doc['content'] == "Content to retrieve"
        assert doc['file_path'] == "/test/retrieve.txt"
        assert doc['file_type'] == "text"
        assert doc['tags'] == ["test"]
        assert doc['metadata'] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_nonexistent_document_by_id(self, search_service):
        """Test retrieving a non-existent document by ID."""
        doc = await search_service.get_document_by_id("nonexistent")
        assert doc is None

    @pytest.mark.asyncio
    async def test_get_document_count(self, search_service, sample_documents):
        """Test getting document count."""
        # Initially should be 0
        count = await search_service.get_document_count()
        assert count == 0

        # Add documents
        for doc in sample_documents:
            await search_service.add_document(**doc)

        # Should have 3 documents
        count = await search_service.get_document_count()
        assert count == 3

    @pytest.mark.asyncio
    async def test_optimize_index(self, search_service, sample_documents):
        """Test index optimization."""
        # Add some documents
        for doc in sample_documents:
            await search_service.add_document(**doc)

        # Optimize the index
        result = await search_service.optimize_index()

        assert result is True

        # Verify we can still search
        results = await search_service.search("Python")
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_get_index_stats(self, search_service):
        """Test getting index statistics."""
        # Get stats for empty index
        stats = await search_service.get_index_stats()

        assert 'doc_count' in stats
        assert 'index_path' in stats
        assert 'index_exists' in stats
        assert 'field_names' in stats
        assert 'schema_size' in stats

        assert stats['doc_count'] == 0
        assert stats['index_exists'] is True
        assert isinstance(stats['field_names'], list)

    @pytest.mark.asyncio
    async def test_get_index_stats_with_documents(self, search_service, sample_documents):
        """Test getting index statistics with documents."""
        # Add documents
        for doc in sample_documents:
            await search_service.add_document(**doc)

        stats = await search_service.get_index_stats()

        assert stats['doc_count'] == 3
        assert stats['schema_size'] > 0

    @pytest.mark.asyncio
    async def test_rebuild_index(self, search_service, sample_documents):
        """Test rebuilding the index."""
        # Add documents
        for doc in sample_documents:
            await search_service.add_document(**doc)

        # Verify documents exist
        count = await search_service.get_document_count()
        assert count == 3

        # Rebuild index
        result = await search_service.rebuild_index()

        assert result is True
        assert search_service.index is not None

        # Verify count is reset (index is empty after rebuild)
        count = await search_service.get_document_count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_search_unicode_content(self, search_service):
        """Test searching with unicode content."""
        unicode_content = "Hello 世界! Testing unicode: αβγδε"

        await search_service.add_document(
            doc_id="unicode_doc",
            title="Unicode Document",
            content=unicode_content,
            file_path="/test/unicode.txt"
        )

        # Search for unicode text
        results = await search_service.search("世界")

        assert len(results) == 1
        assert results[0]['id'] == "unicode_doc"

    @pytest.mark.asyncio
    async def test_search_special_characters(self, search_service):
        """Test searching with special characters."""
        content = "Testing special chars: .+-*/&|^$()[]{}"

        await search_service.add_document(
            doc_id="special_doc",
            title="Special Characters",
            content=content,
            file_path="/test/special.txt"
        )

        # Search for special characters
        results = await search_service.search("special")

        assert len(results) == 1
        assert results[0]['id'] == "special_doc"

    @pytest.mark.asyncio
    async def test_large_document(self, search_service):
        """Test handling of large documents."""
        large_content = "This is a test. " * 10000  # Repeat many times

        await search_service.add_document(
            doc_id="large_doc",
            title="Large Document",
            content=large_content,
            file_path="/test/large.txt"
        )

        # Should be able to add and search
        results = await search_service.search("test")

        assert len(results) == 1
        assert results[0]['id'] == "large_doc"
        # Content should be truncated in results
        assert len(results[0]['content']) <= 503  # 500 chars + "..."

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, search_service):
        """Test concurrent add/update/delete operations."""
        async def add_doc(i):
            await search_service.add_document(
                doc_id=f"concurrent_{i}",
                title=f"Concurrent Document {i}",
                content=f"Content for document {i}",
                file_path=f"/test/concurrent_{i}.txt"
            )

        # Add multiple documents concurrently
        tasks = [add_doc(i) for i in range(10)]
        await asyncio.gather(*tasks)

        # Verify all documents were added
        count = await search_service.get_document_count()
        assert count == 10

        # Search should find all of them
        results = await search_service.search("Concurrent", limit=20)
        assert len(results) == 10