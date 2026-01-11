"""
存储服务模块 - 处理文件存储和异步操作
"""

import os
import aiofiles
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class StorageService:
    """文件存储服务类，提供异步文件操作功能"""

    def __init__(self, base_path: str = "data"):
        """
        初始化存储服务

        Args:
            base_path: 基础存储路径，默认为"data"
        """
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(__name__)

        # 确保基础目录存在
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def _ensure_directory(self, path: Path) -> bool:
        """
        确保目录存在

        Args:
            path: 目录路径

        Returns:
            目录创建成功返回True，失败返回False
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"确保目录存在: {path}")
            return True
        except Exception as e:
            self.logger.error(f"创建目录失败 {path}: {e}")
            return False

    async def save_compressed_data(self, data: bytes, filename: str, subdirectory: str = "compressed") -> bool:
        """
        保存压缩数据到文件

        Args:
            data: 要保存的数据
            filename: 文件名
            subdirectory: 子目录名，默认为"compressed"

        Returns:
            保存成功返回True，失败返回False
        """
        try:
            if not data:
                self.logger.warning(f"保存数据为空，文件名: {filename}")
                return False

            # 构建完整的文件路径
            file_path = self.base_path / subdirectory

            # 确保目录存在
            if not await self._ensure_directory(file_path):
                return False

            full_path = file_path / filename

            # 异步写入文件
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(data)

            self.logger.debug(f"成功保存压缩数据: {filename}, 大小: {len(data)} 字节")
            return True

        except Exception as e:
            self.logger.error(f"保存压缩数据失败 {filename}: {e}")
            return False

    async def load_compressed_data(self, filename: str, subdirectory: str = "compressed") -> Optional[bytes]:
        """
        从文件加载压缩数据

        Args:
            filename: 文件名
            subdirectory: 子目录名，默认为"compressed"

        Returns:
            文件数据，加载失败返回None
        """
        try:
            # 构建完整的文件路径
            file_path = self.base_path / subdirectory / filename

            # 检查文件是否存在
            if not file_path.exists():
                self.logger.warning(f"文件不存在: {file_path}")
                return None

            # 异步读取文件
            async with aiofiles.open(file_path, 'rb') as f:
                data = await f.read()

            self.logger.debug(f"成功加载压缩数据: {filename}, 大小: {len(data)} 字节")
            return data

        except Exception as e:
            self.logger.error(f"加载压缩数据失败 {filename}: {e}")
            return None

    async def save_text_data(self, text: str, filename: str, subdirectory: str = "text",
                           encoding: str = 'utf-8') -> bool:
        """
        保存文本数据到文件

        Args:
            text: 要保存的文本
            filename: 文件名
            subdirectory: 子目录名，默认为"text"
            encoding: 文件编码，默认为utf-8

        Returns:
            保存成功返回True，失败返回False
        """
        try:
            if not text:
                self.logger.warning(f"保存文本为空，文件名: {filename}")
                return False

            # 构建完整的文件路径
            file_path = self.base_path / subdirectory

            # 确保目录存在
            if not await self._ensure_directory(file_path):
                return False

            full_path = file_path / filename

            # 异步写入文件
            async with aiofiles.open(full_path, 'w', encoding=encoding) as f:
                await f.write(text)

            self.logger.debug(f"成功保存文本数据: {filename}, 长度: {len(text)} 字符")
            return True

        except Exception as e:
            self.logger.error(f"保存文本数据失败 {filename}: {e}")
            return False

    async def load_text_data(self, filename: str, subdirectory: str = "text",
                           encoding: str = 'utf-8') -> Optional[str]:
        """
        从文件加载文本数据

        Args:
            filename: 文件名
            subdirectory: 子目录名，默认为"text"
            encoding: 文件编码，默认为utf-8

        Returns:
            文件文本内容，加载失败返回None
        """
        try:
            # 构建完整的文件路径
            file_path = self.base_path / subdirectory / filename

            # 检查文件是否存在
            if not file_path.exists():
                self.logger.warning(f"文件不存在: {file_path}")
                return None

            # 异步读取文件
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                text = await f.read()

            self.logger.debug(f"成功加载文本数据: {filename}, 长度: {len(text)} 字符")
            return text

        except Exception as e:
            self.logger.error(f"加载文本数据失败 {filename}: {e}")
            return None

    async def file_exists(self, filename: str, subdirectory: str = "") -> bool:
        """
        检查文件是否存在

        Args:
            filename: 文件名
            subdirectory: 子目录名，默认为空

        Returns:
            文件存在返回True，不存在返回False
        """
        try:
            file_path = self.base_path
            if subdirectory:
                file_path = file_path / subdirectory
            file_path = file_path / filename

            exists = file_path.exists()
            self.logger.debug(f"检查文件存在: {filename}, 结果: {exists}")
            return exists

        except Exception as e:
            self.logger.error(f"检查文件存在失败 {filename}: {e}")
            return False

    async def delete_file(self, filename: str, subdirectory: str = "") -> bool:
        """
        删除文件

        Args:
            filename: 文件名
            subdirectory: 子目录名，默认为空

        Returns:
            删除成功返回True，失败返回False
        """
        try:
            file_path = self.base_path
            if subdirectory:
                file_path = file_path / subdirectory
            file_path = file_path / filename

            # 检查文件是否存在
            if not file_path.exists():
                self.logger.warning(f"要删除的文件不存在: {file_path}")
                return False

            # 删除文件
            file_path.unlink()

            self.logger.debug(f"成功删除文件: {filename}")
            return True

        except Exception as e:
            self.logger.error(f"删除文件失败 {filename}: {e}")
            return False

    async def list_files(self, subdirectory: str = "", pattern: str = "*") -> List[str]:
        """
        列出目录中的文件

        Args:
            subdirectory: 子目录名，默认为空
            pattern: 文件匹配模式，默认为"*"

        Returns:
            文件名列表
        """
        try:
            directory = self.base_path
            if subdirectory:
                directory = directory / subdirectory

            # 检查目录是否存在
            if not directory.exists():
                self.logger.warning(f"目录不存在: {directory}")
                return []

            # 列出文件
            files = []
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    files.append(file_path.name)

            self.logger.debug(f"列出文件: {subdirectory}, 找到 {len(files)} 个文件")
            return files

        except Exception as e:
            self.logger.error(f"列出文件失败 {subdirectory}: {e}")
            return []

    async def get_file_info(self, filename: str, subdirectory: str = "") -> Optional[Dict[str, Any]]:
        """
        获取文件信息

        Args:
            filename: 文件名
            subdirectory: 子目录名，默认为空

        Returns:
            文件信息字典，失败返回None
        """
        try:
            file_path = self.base_path
            if subdirectory:
                file_path = file_path / subdirectory
            file_path = file_path / filename

            # 检查文件是否存在
            if not file_path.exists():
                return None

            # 获取文件统计信息
            stat = file_path.stat()

            file_info = {
                'filename': filename,
                'path': str(file_path),
                'size': stat.st_size,
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'is_file': file_path.is_file(),
                'is_readable': os.access(file_path, os.R_OK),
                'is_writable': os.access(file_path, os.W_OK)
            }

            self.logger.debug(f"获取文件信息: {filename}")
            return file_info

        except Exception as e:
            self.logger.error(f"获取文件信息失败 {filename}: {e}")
            return None

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息

        Returns:
            存储统计信息字典
        """
        try:
            stats = {
                'base_path': str(self.base_path),
                'exists': self.base_path.exists(),
                'total_files': 0,
                'total_size': 0,
                'subdirectories': []
            }

            if not self.base_path.exists():
                return stats

            # 遍历所有子目录和文件
            for item in self.base_path.rglob('*'):
                if item.is_file():
                    stats['total_files'] += 1
                    try:
                        stats['total_size'] += item.stat().st_size
                    except (OSError, PermissionError):
                        pass

            # 获取子目录列表
            for item in self.base_path.iterdir():
                if item.is_dir():
                    sub_stats = await self._get_subdirectory_stats(item)
                    stats['subdirectories'].append(sub_stats)

            self.logger.debug(f"获取存储统计信息: {stats['total_files']} 个文件, {stats['total_size']} 字节")
            return stats

        except Exception as e:
            self.logger.error(f"获取存储统计信息失败: {e}")
            return {
                'base_path': str(self.base_path),
                'exists': False,
                'total_files': 0,
                'total_size': 0,
                'subdirectories': [],
                'error': str(e)
            }

    async def _get_subdirectory_stats(self, directory: Path) -> Dict[str, Any]:
        """
        获取子目录统计信息

        Args:
            directory: 目录路径

        Returns:
            子目录统计信息字典
        """
        try:
            file_count = 0
            total_size = 0

            for item in directory.iterdir():
                if item.is_file():
                    file_count += 1
                    try:
                        total_size += item.stat().st_size
                    except (OSError, PermissionError):
                        pass

            return {
                'name': directory.name,
                'path': str(directory),
                'file_count': file_count,
                'total_size': total_size
            }

        except Exception as e:
            self.logger.error(f"获取子目录统计信息失败 {directory}: {e}")
            return {
                'name': directory.name,
                'path': str(directory),
                'file_count': 0,
                'total_size': 0,
                'error': str(e)
            }

    async def cleanup_old_files(self, subdirectory: str = "", days_old: int = 30) -> int:
        """
        清理旧文件

        Args:
            subdirectory: 子目录名，默认为空
            days_old: 文件年龄天数，默认为30天

        Returns:
            删除的文件数量
        """
        try:
            directory = self.base_path
            if subdirectory:
                directory = directory / subdirectory

            if not directory.exists():
                self.logger.warning(f"清理目录不存在: {directory}")
                return 0

            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            deleted_count = 0

            # 清理旧文件
            for file_path in directory.iterdir():
                if file_path.is_file():
                    try:
                        if file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            deleted_count += 1
                            self.logger.debug(f"删除旧文件: {file_path.name}")
                    except (OSError, PermissionError) as e:
                        self.logger.warning(f"无法删除文件 {file_path.name}: {e}")

            self.logger.info(f"清理完成，删除了 {deleted_count} 个旧文件")
            return deleted_count

        except Exception as e:
            self.logger.error(f"清理旧文件失败: {e}")
            return 0