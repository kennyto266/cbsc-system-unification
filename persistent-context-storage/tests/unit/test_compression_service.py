"""
Unit tests for CompressionService
"""

import pytest
import zlib
import gzip
from services.compression_service import CompressionService


class TestCompressionService:
    """Test cases for CompressionService"""

    def test_init_default(self):
        """Test CompressionService initialization with default parameters."""
        service = CompressionService()
        assert service.compression_level == 6
        assert service.logger is not None

    def test_init_custom_level(self):
        """Test CompressionService initialization with custom compression level."""
        service = CompressionService(compression_level=9)
        assert service.compression_level == 9

    def test_init_clamp_level(self):
        """Test that compression level is clamped to valid range."""
        service_low = CompressionService(compression_level=0)
        assert service_low.compression_level == 1

        service_high = CompressionService(compression_level=15)
        assert service_high.compression_level == 9

    @pytest.mark.asyncio
    async def test_compress_zlib(self, compression_service, sample_binary_data):
        """Test zlib compression."""
        compressed = compression_service.compress(sample_binary_data, method='zlib')
        assert compressed is not None
        assert isinstance(compressed, bytes)
        assert len(compressed) > 0
        # Verify it's actually compressed (should be smaller for repetitive data)
        assert len(compressed) < len(sample_binary_data) * 0.9

        # Verify decompression works
        decompressed = zlib.decompress(compressed)
        assert decompressed == sample_binary_data

    @pytest.mark.asyncio
    async def test_compress_gzip(self, compression_service, sample_binary_data):
        """Test gzip compression."""
        compressed = compression_service.compress(sample_binary_data, method='gzip')
        assert compressed is not None
        assert isinstance(compressed, bytes)
        assert len(compressed) > 0
        # Verify it's actually gzip data (starts with magic number)
        assert compressed.startswith(b'\x1f\x8b')

        # Verify decompression works
        decompressed = gzip.decompress(compressed)
        assert decompressed == sample_binary_data

    def test_compress_empty_data(self, compression_service):
        """Test compression of empty data."""
        compressed = compression_service.compress(b'')
        assert compressed == b''

    def test_compress_none_data(self, compression_service):
        """Test compression of None data."""
        compressed = compression_service.compress(None)
        assert compressed == b''  # Service returns empty bytes for falsy data

    def test_compress_invalid_method(self, compression_service, sample_binary_data):
        """Test compression with invalid method (should default to zlib)."""
        compressed = compression_service.compress(sample_binary_data, method='invalid')
        assert compressed is not None
        # Should work with zlib decompression
        decompressed = zlib.decompress(compressed)
        assert decompressed == sample_binary_data

    @pytest.mark.asyncio
    async def test_decompress_zlib(self, compression_service, sample_binary_data):
        """Test zlib decompression."""
        compressed = zlib.compress(sample_binary_data)
        decompressed = compression_service.decompress(compressed, method='zlib')
        assert decompressed == sample_binary_data

    @pytest.mark.asyncio
    async def test_decompress_gzip(self, compression_service, sample_binary_data):
        """Test gzip decompression."""
        compressed = gzip.compress(sample_binary_data)
        decompressed = compression_service.decompress(compressed, method='gzip')
        assert decompressed == sample_binary_data

    def test_decompress_empty_data(self, compression_service):
        """Test decompression of empty data."""
        decompressed = compression_service.decompress(b'')
        assert decompressed == b''

    def test_decompress_none_data(self, compression_service):
        """Test decompression of None data."""
        decompressed = compression_service.decompress(None)
        assert decompressed == b''  # Service returns empty bytes for falsy data

    def test_decompress_invalid_data(self, compression_service):
        """Test decompression of invalid data."""
        invalid_data = b'invalid compressed data'
        decompressed = compression_service.decompress(invalid_data)
        assert decompressed is None

    @pytest.mark.asyncio
    async def test_compress_text(self, compression_service, sample_text_data):
        """Test text compression."""
        compressed = compression_service.compress_text(sample_text_data)
        assert compressed is not None
        assert isinstance(compressed, bytes)

        # Verify round-trip
        decompressed_text = compression_service.decompress_to_text(compressed)
        assert decompressed_text == sample_text_data

    def test_compress_text_empty(self, compression_service):
        """Test compression of empty text."""
        compressed = compression_service.compress_text('')
        assert compressed == b''

    def test_compress_text_none(self, compression_service):
        """Test compression of None text."""
        compressed = compression_service.compress_text(None)
        assert compressed == b''  # Service returns empty bytes for falsy data

    @pytest.mark.asyncio
    async def test_compress_text_with_encoding(self, compression_service):
        """Test text compression with specific encoding."""
        # Use text with special characters
        text = "Hello 世界! 🌍 Testing unicode: αβγδε"
        compressed = compression_service.compress_text(text, encoding='utf-8')
        assert compressed is not None

        decompressed = compression_service.decompress_to_text(compressed, encoding='utf-8')
        assert decompressed == text

    @pytest.mark.asyncio
    async def test_decompress_to_text(self, compression_service, sample_text_data):
        """Test decompression to text."""
        compressed = compression_service.compress_text(sample_text_data)
        decompressed_text = compression_service.decompress_to_text(compressed)
        assert decompressed_text == sample_text_data

    def test_decompress_to_text_invalid_encoding(self, compression_service):
        """Test decompression to text with invalid encoding."""
        # Create valid compressed data but try to decode with wrong encoding
        compressed = compression_service.compress_text("Hello 世界", encoding='utf-8')
        decompressed = compression_service.decompress_to_text(compressed, encoding='ascii')
        # Should handle encoding error gracefully - returns None on exception
        assert decompressed is None

    def test_get_compression_info(self, compression_service):
        """Test compression info calculation."""
        original_size = 1000
        compressed_size = 300

        info = compression_service.get_compression_info(original_size, compressed_size)

        assert info['original_size'] == original_size
        assert info['compressed_size'] == compressed_size
        assert info['compression_ratio'] == 0.3
        assert info['space_saved'] == 700
        assert info['space_saved_percent'] == 70.0

    def test_get_compression_info_zero_original(self, compression_service):
        """Test compression info with zero original size."""
        info = compression_service.get_compression_info(0, 100)

        assert info['original_size'] == 0
        assert info['compressed_size'] == 100
        assert info['compression_ratio'] == 0
        assert info['space_saved'] == 0
        assert info['space_saved_percent'] == 0

    def test_is_compressed_zlib(self, compression_service, sample_binary_data):
        """Test checking if data is zlib compressed."""
        uncompressed = b"Hello, world!"
        compressed = zlib.compress(uncompressed)

        assert not compression_service.is_compressed(uncompressed, 'zlib')
        assert compression_service.is_compressed(compressed, 'zlib')

    def test_is_compressed_gzip(self, compression_service, sample_binary_data):
        """Test checking if data is gzip compressed."""
        uncompressed = b"Hello, world!"
        compressed = gzip.compress(uncompressed)

        assert not compression_service.is_compressed(uncompressed, 'gzip')
        assert compression_service.is_compressed(compressed, 'gzip')

    def test_is_compressed_empty(self, compression_service):
        """Test checking if empty data is compressed."""
        assert not compression_service.is_compressed(b'', 'zlib')
        assert not compression_service.is_compressed(None, 'zlib')

    def test_benchmark_compression(self, compression_service, sample_binary_data):
        """Test compression benchmarking."""
        results = compression_service.benchmark_compression(sample_binary_data)

        assert isinstance(results, dict)
        assert 'original_size' in results
        assert 'zlib' in results or 'gzip' in results
        assert results['original_size'] == len(sample_binary_data)

        if 'zlib' in results:
            zlib_result = results['zlib']
            assert 'avg_time' in zlib_result
            assert 'avg_size' in zlib_result
            assert 'compression_ratio' in zlib_result
            assert isinstance(zlib_result['avg_time'], float)
            assert isinstance(zlib_result['avg_size'], (int, float))
            assert isinstance(zlib_result['compression_ratio'], float)

    def test_benchmark_compression_empty(self, compression_service):
        """Test benchmarking with empty data."""
        results = compression_service.benchmark_compression(b'')
        assert 'error' in results

    @pytest.mark.asyncio
    async def test_compression_roundtrip(self, compression_service, sample_context_data):
        """Test that compression and decompression preserves data exactly."""
        import json

        # Convert to JSON string and then to bytes
        json_str = json.dumps(sample_context_data, ensure_ascii=False)
        original_bytes = json_str.encode('utf-8')

        # Test both methods
        for method in ['zlib', 'gzip']:
            compressed = compression_service.compress(original_bytes, method=method)
            assert compressed is not None

            decompressed = compression_service.decompress(compressed, method=method)
            assert decompressed == original_bytes

            # Verify JSON can be decoded back
            decoded_json = json.loads(decompressed.decode('utf-8'))
            assert decoded_json == sample_context_data

    @pytest.mark.asyncio
    async def test_compression_performance(self, compression_service):
        """Test compression performance with different data sizes."""
        import time

        # Test with different data sizes
        data_sizes = [100, 1000, 10000, 100000]

        for size in data_sizes:
            data = b'x' * size

            start_time = time.time()
            compressed = compression_service.compress(data)
            compress_time = time.time() - start_time

            start_time = time.time()
            decompressed = compression_service.decompress(compressed)
            decompress_time = time.time() - start_time

            assert decompressed == data
            assert compress_time < 1.0  # Should complete within 1 second
            assert decompress_time < 1.0  # Should complete within 1 second

            # Compression should achieve some reduction for repetitive data
            if size > 1000:
                assert len(compressed) < size * 0.1  # At least 90% compression

    def test_compression_level_effect(self):
        """Test that different compression levels produce different results."""
        data = b"x" * 10000  # Repetitive data compresses well

        service_low = CompressionService(compression_level=1)
        service_high = CompressionService(compression_level=9)

        compressed_low = service_low.compress(data)
        compressed_high = service_high.compress(data)

        assert compressed_low is not None
        assert compressed_high is not None

        # Higher compression level should produce smaller (or equal) result
        assert len(compressed_high) <= len(compressed_low)

        # Both should decompress to original
        assert service_low.decompress(compressed_low) == data
        assert service_high.decompress(compressed_high) == data