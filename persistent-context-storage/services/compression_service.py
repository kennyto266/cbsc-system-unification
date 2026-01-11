"""
压缩服务模块 - 处理数据的压缩和解压缩操作
"""

import zlib
import gzip
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class CompressionService:
    """压缩服务类，提供基于zlib/gzip的数据压缩功能"""

    def __init__(self, compression_level: int = 6):
        """
        初始化压缩服务

        Args:
            compression_level: 压缩级别，范围1-9，默认为6
        """
        self.compression_level = max(1, min(9, compression_level))
        self.logger = logging.getLogger(__name__)

    def compress(self, data: bytes, method: str = 'zlib') -> Optional[bytes]:
        """
        压缩数据

        Args:
            data: 要压缩的原始数据
            method: 压缩方法，'zlib' 或 'gzip'，默认为 'zlib'

        Returns:
            压缩后的数据，如果压缩失败返回None
        """
        try:
            if not data:
                self.logger.warning("压缩数据为空")
                return b''

            if method.lower() == 'gzip':
                compressed = gzip.compress(data, compresslevel=self.compression_level)
            else:
                # 默认使用zlib
                compressed = zlib.compress(data, level=self.compression_level)

            # 记录压缩统计信息
            compression_ratio = len(compressed) / len(data) if len(data) > 0 else 0
            self.logger.debug(f"数据压缩完成: {len(data)} -> {len(compressed)} 字节, "
                            f"压缩率: {compression_ratio:.2%}")

            return compressed

        except Exception as e:
            self.logger.error(f"压缩数据失败: {e}")
            return None

    def decompress(self, compressed_data: bytes, method: str = 'zlib') -> Optional[bytes]:
        """
        解压缩数据

        Args:
            compressed_data: 压缩的数据
            method: 压缩方法，'zlib' 或 'gzip'，默认为 'zlib'

        Returns:
            解压缩后的原始数据，如果解压失败返回None
        """
        try:
            if not compressed_data:
                self.logger.warning("解压数据为空")
                return b''

            if method.lower() == 'gzip':
                decompressed = gzip.decompress(compressed_data)
            else:
                # 默认使用zlib
                decompressed = zlib.decompress(compressed_data)

            self.logger.debug(f"数据解压完成: {len(compressed_data)} -> {len(decompressed)} 字节")

            return decompressed

        except Exception as e:
            self.logger.error(f"解压数据失败: {e}")
            return None

    def compress_text(self, text: str, encoding: str = 'utf-8', method: str = 'zlib') -> Optional[bytes]:
        """
        压缩文本数据

        Args:
            text: 要压缩的文本
            encoding: 文本编码，默认为utf-8
            method: 压缩方法，'zlib' 或 'gzip'，默认为 'zlib'

        Returns:
            压缩后的数据
        """
        try:
            if not text:
                self.logger.warning("压缩文本为空")
                return b''

            text_bytes = text.encode(encoding)
            return self.compress(text_bytes, method)

        except Exception as e:
            self.logger.error(f"压缩文本失败: {e}")
            return None

    def decompress_to_text(self, compressed_data: bytes, encoding: str = 'utf-8',
                          method: str = 'zlib') -> Optional[str]:
        """
        解压缩数据到文本

        Args:
            compressed_data: 压缩的数据
            encoding: 文本编码，默认为utf-8
            method: 压缩方法，'zlib' 或 'gzip'，默认为 'zlib'

        Returns:
            解压缩后的文本
        """
        try:
            decompressed_bytes = self.decompress(compressed_data, method)
            if decompressed_bytes is None:
                return None

            return decompressed_bytes.decode(encoding)

        except Exception as e:
            self.logger.error(f"解压到文本失败: {e}")
            return None

    def get_compression_info(self, original_size: int, compressed_size: int) -> dict:
        """
        获取压缩信息统计

        Args:
            original_size: 原始数据大小（字节）
            compressed_size: 压缩后数据大小（字节）

        Returns:
            包含压缩统计信息的字典
        """
        try:
            if original_size <= 0:
                return {
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'compression_ratio': 0,
                    'space_saved': 0,
                    'space_saved_percent': 0
                }

            compression_ratio = compressed_size / original_size
            space_saved = original_size - compressed_size
            space_saved_percent = (space_saved / original_size) * 100

            return {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': round(compression_ratio, 4),
                'space_saved': space_saved,
                'space_saved_percent': round(space_saved_percent, 2)
            }

        except Exception as e:
            self.logger.error(f"计算压缩信息失败: {e}")
            return {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': 0,
                'space_saved': 0,
                'space_saved_percent': 0
            }

    def is_compressed(self, data: bytes, method: str = 'zlib') -> bool:
        """
        检查数据是否已被压缩

        Args:
            data: 要检查的数据
            method: 压缩方法，'zlib' 或 'gzip'，默认为 'zlib'

        Returns:
            如果数据已被压缩返回True，否则返回False
        """
        try:
            if not data:
                return False

            if method.lower() == 'gzip':
                # GZIP文件以魔数开头
                return data.startswith(b'\x1f\x8b')
            else:
                # 尝试解压来验证是否为zlib压缩数据
                try:
                    zlib.decompress(data)
                    return True
                except zlib.error:
                    return False

        except Exception as e:
            self.logger.error(f"检查压缩状态失败: {e}")
            return False

    def benchmark_compression(self, data: bytes) -> dict:
        """
        压缩性能基准测试

        Args:
            data: 要测试的数据

        Returns:
            包含基准测试结果的字典
        """
        try:
            import time

            if not data:
                return {'error': '测试数据为空'}

            results = {}
            original_size = len(data)

            # 测试zlib压缩
            zlib_times = []
            zlib_sizes = []
            for _ in range(5):  # 运行5次取平均值
                start_time = time.time()
                zlib_compressed = self.compress(data, 'zlib')
                end_time = time.time()

                if zlib_compressed is not None:
                    zlib_times.append(end_time - start_time)
                    zlib_sizes.append(len(zlib_compressed))

            if zlib_times:
                results['zlib'] = {
                    'avg_time': sum(zlib_times) / len(zlib_times),
                    'avg_size': sum(zlib_sizes) / len(zlib_sizes),
                    'compression_ratio': sum(zlib_sizes) / len(zlib_sizes) / original_size
                }

            # 测试gzip压缩
            gzip_times = []
            gzip_sizes = []
            for _ in range(5):  # 运行5次取平均值
                start_time = time.time()
                gzip_compressed = self.compress(data, 'gzip')
                end_time = time.time()

                if gzip_compressed is not None:
                    gzip_times.append(end_time - start_time)
                    gzip_sizes.append(len(gzip_compressed))

            if gzip_times:
                results['gzip'] = {
                    'avg_time': sum(gzip_times) / len(gzip_times),
                    'avg_size': sum(gzip_sizes) / len(gzip_sizes),
                    'compression_ratio': sum(gzip_sizes) / len(gzip_sizes) / original_size
                }

            results['original_size'] = original_size

            return results

        except Exception as e:
            self.logger.error(f"压缩基准测试失败: {e}")
            return {'error': str(e)}