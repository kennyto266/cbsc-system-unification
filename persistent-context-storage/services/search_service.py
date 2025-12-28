"""
搜索服务模块 - 处理全文搜索和索引功能
"""

import os
import asyncio
from typing import Optional, Dict, Any, List, Tuple
import logging
from pathlib import Path
from datetime import datetime
import json
from whoosh import fields, index
from whoosh.analysis import StandardAnalyzer, StemmingAnalyzer, CompositeAnalyzer
from whoosh.query import Query, And, Or, Term, Phrase
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.filedb.filestore import FileStorage
from whoosh.writing import IndexWriter
from whoosh.searching import Results

logger = logging.getLogger(__name__)

class SearchService:
    """搜索服务类，提供全文搜索和索引功能"""

    def __init__(self, index_path: str = "data/search_index"):
        """
        初始化搜索服务

        Args:
            index_path: 索引存储路径，默认为"data/search_index"
        """
        self.index_path = Path(index_path)
        self.logger = logging.getLogger(__name__)
        self.index = None
        # Create a composite analyzer properly
        self.analyzer = StandardAnalyzer()
        self.stemming_analyzer = StemmingAnalyzer()

        # 定义索引字段模式
        self.schema = fields.Schema(
            id=fields.ID(stored=True, unique=True),
            title=fields.TEXT(analyzer=self.analyzer, stored=True),
            content=fields.TEXT(analyzer=self.analyzer, stored=True),
            file_path=fields.ID(stored=True),
            file_type=fields.ID(stored=True),
            created_at=fields.DATETIME(stored=True),
            updated_at=fields.DATETIME(stored=True),
            tags=fields.KEYWORD(stored=True, commas=True),
            metadata=fields.TEXT(stored=True)  # Use TEXT instead of JSON for compatibility
        )

    async def initialize_index(self) -> bool:
        """
        初始化搜索索引

        Returns:
            初始化成功返回True，失败返回False
        """
        try:
            # 确保索引目录存在
            self.index_path.mkdir(parents=True, exist_ok=True)

            # 检查是否已有索引
            if index.exists_in(str(self.index_path)):
                self.index = index.open_dir(str(self.index_path))
                self.logger.info(f"打开现有搜索索引: {self.index_path}")
            else:
                # 创建新索引
                storage = FileStorage(str(self.index_path))
                self.index = storage.create_index(self.schema)
                self.logger.info(f"创建新搜索索引: {self.index_path}")

            return True

        except Exception as e:
            self.logger.error(f"初始化搜索索引失败: {e}")
            return False

    async def add_document(self, doc_id: str, title: str, content: str,
                          file_path: str, file_type: str = None,
                          tags: List[str] = None, metadata: Dict[str, Any] = None) -> bool:
        """
        添加文档到索引

        Args:
            doc_id: 文档唯一标识
            title: 文档标题
            content: 文档内容
            file_path: 文件路径
            file_type: 文件类型
            tags: 标签列表
            metadata: 元数据字典

        Returns:
            添加成功返回True，失败返回False
        """
        try:
            if not self.index:
                if not await self.initialize_index():
                    return False

            # 准备文档数据
            doc_data = {
                'id': doc_id,
                'title': title or '',
                'content': content or '',
                'file_path': file_path or '',
                'file_type': file_type or '',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'tags': ','.join(tags) if tags else '',
                'metadata': json.dumps(metadata or {}) if metadata else ''
            }

            # 获取写入器并添加文档
            writer: IndexWriter = self.index.writer()
            writer.add_document(**doc_data)
            writer.commit()

            self.logger.debug(f"成功添加文档到索引: {doc_id}")
            return True

        except Exception as e:
            self.logger.error(f"添加文档到索引失败 {doc_id}: {e}")
            return False

    async def update_document(self, doc_id: str, title: str = None,
                            content: str = None, tags: List[str] = None,
                            metadata: Dict[str, Any] = None) -> bool:
        """
        更新索引中的文档

        Args:
            doc_id: 文档唯一标识
            title: 新标题
            content: 新内容
            tags: 新标签列表
            metadata: 新元数据

        Returns:
            更新成功返回True，失败返回False
        """
        try:
            if not self.index:
                if not await self.initialize_index():
                    return False

            # 搜索现有文档
            writer: IndexWriter = self.index.writer()

            # 删除旧文档
            writer.delete_by_term('id', doc_id)

            # 重新添加文档
            with self.index.searcher() as searcher:
                doc = searcher.document(id=doc_id)
                if doc:
                    updated_doc = {
                        'id': doc_id,
                        'title': title if title is not None else doc.get('title', ''),
                        'content': content if content is not None else doc.get('content', ''),
                        'file_path': doc.get('file_path', ''),
                        'file_type': doc.get('file_type', ''),
                        'created_at': doc.get('created_at', datetime.now()),
                        'updated_at': datetime.now(),
                        'tags': ','.join(tags) if tags is not None else doc.get('tags', ''),
                        'metadata': json.dumps(metadata) if metadata is not None else doc.get('metadata', '')
                    }

                    writer.add_document(**updated_doc)
                    writer.commit()

                    self.logger.debug(f"成功更新文档: {doc_id}")
                    return True
                else:
                    self.logger.warning(f"要更新的文档不存在: {doc_id}")
                    return False

        except Exception as e:
            self.logger.error(f"更新文档失败 {doc_id}: {e}")
            return False

    async def delete_document(self, doc_id: str) -> bool:
        """
        从索引中删除文档

        Args:
            doc_id: 文档唯一标识

        Returns:
            删除成功返回True，失败返回False
        """
        try:
            if not self.index:
                if not await self.initialize_index():
                    return False

            writer: IndexWriter = self.index.writer()
            writer.delete_by_term('id', doc_id)
            writer.commit()

            self.logger.debug(f"成功删除文档: {doc_id}")
            return True

        except Exception as e:
            self.logger.error(f"删除文档失败 {doc_id}: {e}")
            return False

    async def search(self, query_str: str, limit: int = 10,
                    fields: List[str] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        执行全文搜索

        Args:
            query_str: 搜索查询字符串
            limit: 返回结果数量限制，默认为10
            fields: 搜索字段列表，默认为['title', 'content']
            offset: 结果偏移量，用于分页

        Returns:
            搜索结果列表
        """
        try:
            if not self.index:
                if not await self.initialize_index():
                    return []

            if not query_str.strip():
                self.logger.warning("搜索查询为空")
                return []

            # 默认搜索字段
            search_fields = fields or ['title', 'content']

            with self.index.searcher() as searcher:
                # 创建查询解析器
                parser = MultifieldParser(search_fields, self.index.schema)
                query = parser.parse(query_str)

                # 执行搜索
                results: Results = searcher.search(query, limit=limit + offset)

                # 转换结果为字典列表
                search_results = []
                for hit in results[offset:limit + offset]:
                    # Parse metadata JSON if it exists
                    metadata_str = hit.get('metadata', '')
                    metadata = {}
                    try:
                        metadata = json.loads(metadata_str) if metadata_str else {}
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}

                    result = {
                        'id': hit['id'],
                        'title': hit['title'],
                        'content': hit['content'][:500] + '...' if len(hit.get('content', '')) > 500 else hit.get('content', ''),
                        'file_path': hit.get('file_path', ''),
                        'file_type': hit.get('file_type', ''),
                        'score': hit.score,
                        'created_at': hit.get('created_at'),
                        'updated_at': hit.get('updated_at'),
                        'tags': hit.get('tags', '').split(',') if hit.get('tags') else [],
                        'metadata': metadata
                    }
                    search_results.append(result)

                self.logger.debug(f"搜索完成，找到 {len(search_results)} 个结果")
                return search_results

        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            return []

    async def search_by_tag(self, tag: str, limit: int = 10,
                           offset: int = 0) -> List[Dict[str, Any]]:
        """
        按标签搜索文档

        Args:
            tag: 标签名称
            limit: 返回结果数量限制
            offset: 结果偏移量

        Returns:
            搜索结果列表
        """
        try:
            if not self.index:
                if not await self.initialize_index():
                    return []

            with self.index.searcher() as searcher:
                query = Term('tags', tag)
                results = searcher.search(query, limit=limit + offset)

                search_results = []
                for hit in results[offset:limit + offset]:
                    # Parse metadata JSON if it exists
                    metadata_str = hit.get('metadata', '')
                    metadata = {}
                    try:
                        metadata = json.loads(metadata_str) if metadata_str else {}
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}

                    result = {
                        'id': hit['id'],
                        'title': hit['title'],
                        'file_path': hit.get('file_path', ''),
                        'file_type': hit.get('file_type', ''),
                        'score': hit.score,
                        'created_at': hit.get('created_at'),
                        'updated_at': hit.get('updated_at'),
                        'tags': hit.get('tags', '').split(',') if hit.get('tags') else [],
                        'metadata': metadata
                    }
                    search_results.append(result)

                self.logger.debug(f"标签搜索完成，找到 {len(search_results)} 个结果")
                return search_results

        except Exception as e:
            self.logger.error(f"标签搜索失败: {e}")
            return []

    async def search_by_file_type(self, file_type: str, limit: int = 10,
                                 offset: int = 0) -> List[Dict[str, Any]]:
        """
        按文件类型搜索文档

        Args:
            file_type: 文件类型
            limit: 返回结果数量限制
            offset: 结果偏移量

        Returns:
            搜索结果列表
        """
        try:
            if not self.index:
                if not await self.initialize_index():
                    return []

            with self.index.searcher() as searcher:
                query = Term('file_type', file_type)
                results = searcher.search(query, limit=limit + offset)

                search_results = []
                for hit in results[offset:limit + offset]:
                    # Parse metadata JSON if it exists
                    metadata_str = hit.get('metadata', '')
                    metadata = {}
                    try:
                        metadata = json.loads(metadata_str) if metadata_str else {}
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}

                    result = {
                        'id': hit['id'],
                        'title': hit['title'],
                        'file_path': hit.get('file_path', ''),
                        'file_type': hit.get('file_type', ''),
                        'score': hit.score,
                        'created_at': hit.get('created_at'),
                        'updated_at': hit.get('updated_at'),
                        'tags': hit.get('tags', '').split(',') if hit.get('tags') else [],
                        'metadata': metadata
                    }
                    search_results.append(result)

                self.logger.debug(f"文件类型搜索完成，找到 {len(search_results)} 个结果")
                return search_results

        except Exception as e:
            self.logger.error(f"文件类型搜索失败: {e}")
            return []

    async def get_document_count(self) -> int:
        """
        获取索引中的文档总数

        Returns:
            文档总数
        """
        try:
            if not self.index:
                if not await self.initialize_index():
                    return 0

            with self.index.searcher() as searcher:
                count = searcher.doc_count()
                self.logger.debug(f"索引文档总数: {count}")
                return count

        except Exception as e:
            self.logger.error(f"获取文档总数失败: {e}")
            return 0

    async def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文档

        Args:
            doc_id: 文档唯一标识

        Returns:
            文档字典，不存在返回None
        """
        try:
            if not self.index:
                if not await self.initialize_index():
                    return None

            with self.index.searcher() as searcher:
                doc = searcher.document(id=doc_id)
                if doc:
                    # Parse metadata JSON if it exists
                    metadata_str = doc.get('metadata', '')
                    metadata = {}
                    try:
                        metadata = json.loads(metadata_str) if metadata_str else {}
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}

                    result = {
                        'id': doc['id'],
                        'title': doc['title'],
                        'content': doc['content'],
                        'file_path': doc.get('file_path', ''),
                        'file_type': doc.get('file_type', ''),
                        'created_at': doc.get('created_at'),
                        'updated_at': doc.get('updated_at'),
                        'tags': doc.get('tags', '').split(',') if doc.get('tags') else [],
                        'metadata': metadata
                    }
                    return result
                else:
                    return None

        except Exception as e:
            self.logger.error(f"获取文档失败 {doc_id}: {e}")
            return None

    async def optimize_index(self) -> bool:
        """
        优化索引以提升搜索性能

        Returns:
            优化成功返回True，失败返回False
        """
        try:
            if not self.index:
                if not await self.initialize_index():
                    return False

            writer: IndexWriter = self.index.writer()
            writer.commit(optimize=True)

            self.logger.info("索引优化完成")
            return True

        except Exception as e:
            self.logger.error(f"索引优化失败: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """
        获取索引统计信息

        Returns:
            索引统计信息字典
        """
        try:
            if not self.index:
                if not await self.initialize_index():
                    return {}

            with self.index.searcher() as searcher:
                stats = {
                    'doc_count': searcher.doc_count(),
                    'index_path': str(self.index_path),
                    'index_exists': True,
                    'field_names': list(self.index.schema.names()),
                    'schema_size': len(self.index.schema),
                    'last_modified': None
                }

                # 获取索引文件的最后修改时间
                try:
                    index_files = list(self.index_path.glob("*"))
                    if index_files:
                        stats['last_modified'] = max(
                            f.stat().st_mtime for f in index_files
                        )
                except Exception:
                    pass

                return stats

        except Exception as e:
            self.logger.error(f"获取索引统计信息失败: {e}")
            return {
                'doc_count': 0,
                'index_path': str(self.index_path),
                'index_exists': False,
                'error': str(e)
            }

    async def rebuild_index(self) -> bool:
        """
        重建整个索引

        Returns:
            重建成功返回True，失败返回False
        """
        try:
            # 删除现有索引
            if self.index_path.exists():
                import shutil
                shutil.rmtree(self.index_path)

            # 重新初始化索引
            self.index = None
            return await self.initialize_index()

        except Exception as e:
            self.logger.error(f"重建索引失败: {e}")
            return False