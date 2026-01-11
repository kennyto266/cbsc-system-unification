"""
Unit tests for StorageService
"""

import pytest
import aiofiles
import asyncio
from pathlib import Path
from services.storage_service import StorageService


class TestStorageService:
    """Test cases for StorageService"""

    @pytest.mark.asyncio
    async def test_init_default(self):
        """Test StorageService initialization with default parameters."""
        service = StorageService()
        assert service.base_path.name == "data"
        assert service.logger is not None

    @pytest.mark.asyncio
    async def test_init_custom_path(self, temp_dir):
        """Test StorageService initialization with custom path."""
        custom_path = str(temp_dir / "test_storage")
        service = StorageService(custom_path)
        assert str(service.base_path) == custom_path
        # Directory should be created automatically
        assert service.base_path.exists()

    @pytest.mark.asyncio
    async def test_save_compressed_data(self, storage_service, temp_dir):
        """Test saving compressed data to file."""
        test_data = b"Test compressed data content"
        filename = "test_file.bin"

        result = await storage_service.save_compressed_data(test_data, filename)

        assert result is True

        # Verify file exists in compressed subdirectory
        file_path = storage_service.base_path / "compressed" / filename
        assert file_path.exists()

        # Verify content
        async with aiofiles.open(file_path, 'rb') as f:
            saved_data = await f.read()
        assert saved_data == test_data

    @pytest.mark.asyncio
    async def test_save_compressed_data_with_subdirectory(self, storage_service):
        """Test saving compressed data with custom subdirectory."""
        test_data = b"Test data"
        filename = "test.bin"
        subdirectory = "custom_dir"

        result = await storage_service.save_compressed_data(test_data, filename, subdirectory)

        assert result is True

        # Verify file exists in custom subdirectory
        file_path = storage_service.base_path / subdirectory / filename
        assert file_path.exists()

    @pytest.mark.asyncio
    async def test_save_compressed_data_empty(self, storage_service):
        """Test saving empty compressed data."""
        result = await storage_service.save_compressed_data(b"", "empty.bin")

        assert result is False  # Service returns False for empty data

    @pytest.mark.asyncio
    async def test_load_compressed_data(self, storage_service):
        """Test loading compressed data from file."""
        # First save some data
        test_data = b"Test data for loading"
        filename = "load_test.bin"
        await storage_service.save_compressed_data(test_data, filename)

        # Now load it
        loaded_data = await storage_service.load_compressed_data(filename)

        assert loaded_data == test_data

    @pytest.mark.asyncio
    async def test_load_compressed_data_with_subdirectory(self, storage_service):
        """Test loading compressed data from custom subdirectory."""
        test_data = b"Test data"
        filename = "test.bin"
        subdirectory = "custom_dir"
        await storage_service.save_compressed_data(test_data, filename, subdirectory)

        # Load it from the same subdirectory
        loaded_data = await storage_service.load_compressed_data(filename, subdirectory)

        assert loaded_data == test_data

    @pytest.mark.asyncio
    async def test_load_compressed_data_nonexistent(self, storage_service):
        """Test loading a file that doesn't exist."""
        loaded_data = await storage_service.load_compressed_data("nonexistent.bin")

        assert loaded_data is None

    @pytest.mark.asyncio
    async def test_save_text_data(self, storage_service):
        """Test saving text data to file."""
        test_text = "This is test text content"
        filename = "test_text.txt"

        result = await storage_service.save_text_data(test_text, filename)

        assert result is True

        # Verify file exists in text subdirectory
        file_path = storage_service.base_path / "text" / filename
        assert file_path.exists()

        # Verify content
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            saved_text = await f.read()
        assert saved_text == test_text

    @pytest.mark.asyncio
    async def test_save_text_data_with_encoding(self, storage_service):
        """Test saving text data with custom encoding."""
        test_text = "Hello 世界! 🌍"
        filename = "unicode.txt"

        result = await storage_service.save_text_data(test_text, filename, encoding='utf-8')

        assert result is True

    @pytest.mark.asyncio
    async def test_load_text_data(self, storage_service):
        """Test loading text data from file."""
        # First save some text
        test_text = "Test text for loading"
        filename = "load_text.txt"
        await storage_service.save_text_data(test_text, filename)

        # Now load it
        loaded_text = await storage_service.load_text_data(filename)

        assert loaded_text == test_text

    @pytest.mark.asyncio
    async def test_load_text_data_with_encoding(self, storage_service):
        """Test loading text data with custom encoding."""
        test_text = "Hello 世界! 🌍"
        filename = "unicode_encoding.txt"
        await storage_service.save_text_data(test_text, filename, encoding='utf-8')

        # Load it with the same encoding
        loaded_text = await storage_service.load_text_data(filename, encoding='utf-8')

        assert loaded_text == test_text

    @pytest.mark.asyncio
    async def test_file_exists(self, storage_service):
        """Test checking if file exists."""
        # Save a file first
        await storage_service.save_compressed_data(b"test", "exists_test.bin")

        # Check if it exists in compressed subdirectory
        exists = await storage_service.file_exists("exists_test.bin", "compressed")

        assert exists is True

        # Check non-existent file
        exists = await storage_service.file_exists("nonexistent.bin")

        assert exists is False

    @pytest.mark.asyncio
    async def test_file_exists_root(self, storage_service):
        """Test checking if file exists in root directory."""
        # Create a file directly in the base path
        test_file = storage_service.base_path / "root_test.txt"
        test_file.write_text("test")

        # Check if it exists
        exists = await storage_service.file_exists("root_test.txt", "")

        assert exists is True

    @pytest.mark.asyncio
    async def test_delete_file(self, storage_service):
        """Test deleting a file."""
        # Save a file first
        await storage_service.save_compressed_data(b"Data to delete", "delete_test.bin")

        # Verify file exists
        file_path = storage_service.base_path / "compressed" / "delete_test.bin"
        assert file_path.exists()

        # Delete it
        result = await storage_service.delete_file("delete_test.bin", "compressed")

        assert result is True
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_file_nonexistent(self, storage_service):
        """Test deleting a file that doesn't exist."""
        result = await storage_service.delete_file("nonexistent.bin")

        assert result is False

    @pytest.mark.asyncio
    async def test_list_files(self, storage_service):
        """Test listing files in storage directory."""
        # Save multiple files in compressed subdirectory
        files_data = [
            ("file1.bin", b"data1"),
            ("file2.bin", b"data2"),
            ("file3.txt", b"data3"),
        ]

        for filename, data in files_data:
            await storage_service.save_compressed_data(data, filename)

        # List files in compressed subdirectory
        file_list = await storage_service.list_files("compressed")

        assert len(file_list) >= 3
        for filename, _ in files_data:
            assert filename in file_list

    @pytest.mark.asyncio
    async def test_list_files_with_pattern(self, storage_service):
        """Test listing files with pattern matching."""
        # Save files with different extensions
        files_data = [
            ("test1.bin", b"data1"),
            ("test2.bin", b"data2"),
            ("test3.txt", b"data3"),
            ("other.bin", b"data4"),
        ]

        for filename, data in files_data:
            await storage_service.save_compressed_data(data, filename)

        # List only .bin files
        bin_files = await storage_service.list_files("compressed", "*.bin")

        assert len(bin_files) == 3
        assert "test1.bin" in bin_files
        assert "test2.bin" in bin_files
        assert "other.bin" in bin_files
        assert "test3.txt" not in bin_files

    @pytest.mark.asyncio
    async def test_list_files_empty_directory(self, storage_service):
        """Test listing files in empty directory."""
        file_list = await storage_service.list_files("nonexistent")

        assert file_list == []

    @pytest.mark.asyncio
    async def test_get_file_info(self, storage_service):
        """Test getting file information."""
        # Save a file first
        await storage_service.save_compressed_data(b"test data", "info_test.bin")

        # Get file info
        file_info = await storage_service.get_file_info("info_test.bin", "compressed")

        assert file_info is not None
        assert file_info['filename'] == "info_test.bin"
        assert file_info['size'] == len(b"test data")
        assert file_info['is_file'] is True
        assert file_info['is_readable'] is True
        assert file_info['is_writable'] is True
        assert 'created_time' in file_info
        assert 'modified_time' in file_info

    @pytest.mark.asyncio
    async def test_get_file_info_nonexistent(self, storage_service):
        """Test getting info for non-existent file."""
        file_info = await storage_service.get_file_info("nonexistent.bin")

        assert file_info is None

    @pytest.mark.asyncio
    async def test_get_storage_stats(self, storage_service):
        """Test getting storage statistics."""
        # Save some files
        await storage_service.save_compressed_data(b"data1" * 100, "file1.bin")
        await storage_service.save_compressed_data(b"data2" * 200, "file2.bin")
        await storage_service.save_text_data("text content", "text_file.txt")

        # Get storage info
        stats = await storage_service.get_storage_stats()

        assert 'base_path' in stats
        assert 'exists' in stats
        assert 'total_files' in stats
        assert 'total_size' in stats
        assert 'subdirectories' in stats

        assert stats['exists'] is True
        assert stats['total_files'] >= 3
        assert stats['total_size'] > 0
        assert len(stats['subdirectories']) >= 2  # compressed and text subdirectories

    @pytest.mark.asyncio
    async def test_get_storage_stats_empty(self, storage_service):
        """Test getting storage info for empty directory."""
        stats = await storage_service.get_storage_stats()

        assert stats['total_files'] == 0
        assert stats['total_size'] == 0
        assert len(stats['subdirectories']) == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_files(self, storage_service):
        """Test cleaning up old files."""
        import time

        # Save a file
        await storage_service.save_compressed_data(b"old data", "old_file.bin")

        # Get file path and modify its modification time
        file_path = storage_service.base_path / "compressed" / "old_file.bin"
        old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
        import os
        os.utime(file_path, (old_time, old_time))

        # Save a recent file
        await storage_service.save_compressed_data(b"new data", "new_file.bin")

        # Clean up files older than 7 days
        deleted_count = await storage_service.cleanup_old_files("compressed", 7)

        assert deleted_count == 1
        assert not file_path.exists()

        # New file should still exist
        new_file_path = storage_service.base_path / "compressed" / "new_file.bin"
        assert new_file_path.exists()

    @pytest.mark.asyncio
    async def test_cleanup_old_files_no_matches(self, storage_service):
        """Test cleanup when no files match the age criteria."""
        # Save recent files
        await storage_service.save_compressed_data(b"recent1", "recent1.bin")
        await storage_service.save_compressed_data(b"recent2", "recent2.bin")

        # Try to clean up files older than 30 days
        deleted_count = await storage_service.cleanup_old_files("compressed", 30)

        assert deleted_count == 0

        # Files should still exist
        assert (storage_service.base_path / "compressed" / "recent1.bin").exists()
        assert (storage_service.base_path / "compressed" / "recent2.bin").exists()

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, storage_service):
        """Test concurrent save/load operations."""
        async def save_and_load(i):
            filename = f"concurrent_{i}.bin"
            data = f"Concurrent data {i}".encode()

            # Save
            save_result = await storage_service.save_compressed_data(data, filename)
            assert save_result is True

            # Load
            loaded_data = await storage_service.load_compressed_data(filename)
            assert loaded_data == data

        # Run multiple operations concurrently
        tasks = [save_and_load(i) for i in range(10)]
        await asyncio.gather(*tasks)

        # Verify all files exist
        file_list = await storage_service.list_files("compressed")
        assert len(file_list) >= 10

    @pytest.mark.asyncio
    async def test_large_file_handling(self, storage_service):
        """Test handling of large files."""
        # Create large data (1MB)
        large_data = b"x" * (1024 * 1024)
        filename = "large_file.bin"

        # Save large file
        result = await storage_service.save_compressed_data(large_data, filename)
        assert result is True

        # Load large file
        loaded_data = await storage_service.load_compressed_data(filename)
        assert loaded_data == large_data

        # Check file info
        file_info = await storage_service.get_file_info(filename, "compressed")
        assert file_info is not None
        assert file_info['size'] == len(large_data)

    @pytest.mark.asyncio
    async def test_binary_data_handling(self, storage_service):
        """Test handling of binary data with null bytes and special values."""
        # Create binary data with various byte values
        binary_data = bytes(range(256)) * 4  # All byte values repeated
        filename = "binary_test.bin"

        # Save and load binary data
        result = await storage_service.save_compressed_data(binary_data, filename)
        assert result is True

        loaded_data = await storage_service.load_compressed_data(filename)
        assert loaded_data == binary_data

    @pytest.mark.asyncio
    async def test_unicode_filename(self, storage_service):
        """Test handling of unicode filenames."""
        unicode_filename = "测试_文件.bin"
        test_data = b"Test data with unicode filename"

        result = await storage_service.save_compressed_data(test_data, unicode_filename)
        assert result is True

        loaded_data = await storage_service.load_compressed_data(unicode_filename)
        assert loaded_data == test_data

        # Check if file exists
        exists = await storage_service.file_exists(unicode_filename, "compressed")
        assert exists is True

    @pytest.mark.asyncio
    async def test_ensure_directory(self, storage_service, temp_dir):
        """Test _ensure_directory method."""
        new_dir = temp_dir / "new_test_dir"

        # Directory doesn't exist initially
        assert not new_dir.exists()

        # Call _ensure_directory
        result = await storage_service._ensure_directory(new_dir)

        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()