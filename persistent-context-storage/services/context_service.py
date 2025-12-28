"""
Context service module - 处理上下文保存、加载和管理
"""

import json
import uuid
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from models.context import Context, ContextTag, ContextAccess, ContextShare
from services.compression_service import CompressionService
from services.storage_service import StorageService
from services.search_service import SearchService
from config.database import get_database_session

logger = logging.getLogger(__name__)

class ContextService:
    """上下文服务类，提供上下文保存、加载和管理功能"""

    def __init__(self, storage_path: str = "data", compression_level: int = 6):
        """
        初始化上下文服务

        Args:
            storage_path: 存储路径，默认为"data"
            compression_level: 压缩级别，范围1-9，默认为6
        """
        self.logger = logging.getLogger(__name__)
        self.compression_service = CompressionService(compression_level)
        self.storage_service = StorageService(storage_path)
        self.search_service = SearchService()

    async def save_context(self, title: str, content: Dict[str, Any], user_id: str,
                          description: str = None, tags: List[str] = None,
                          session_id: str = None, project_path: str = None,
                          visibility: str = "private", auto_save_enabled: bool = True) -> Optional[str]:
        """
        保存上下文数据

        Args:
            title: 上下文标题
            content: 上下文内容字典
            user_id: 用户ID
            description: 上下文描述
            tags: 标签列表
            session_id: 会话ID
            project_path: 项目路径
            visibility: 可见性 (private, team, public)
            auto_save_enabled: 是否启用自动保存

        Returns:
            上下文ID，保存失败返回None
        """
        try:
            # 生成唯一ID
            context_id = str(uuid.uuid4())

            # 序列化内容
            content_json = json.dumps(content, ensure_ascii=False, indent=2)
            content_bytes = content_json.encode('utf-8')
            original_size = len(content_bytes)

            # 压缩内容
            compressed_data = self.compression_service.compress(content_bytes)
            if not compressed_data:
                self.logger.error("压缩内容失败")
                return None

            # 计算内容哈希
            content_hash = hashlib.sha256(compressed_data).hexdigest()
            file_size = len(compressed_data)
            compression_ratio = file_size / original_size if original_size > 0 else 0

            # 生成文件名
            filename = f"context_{context_id}.bin"

            # 保存压缩数据到文件
            if not await self.storage_service.save_compressed_data(compressed_data, filename):
                self.logger.error("保存压缩数据到文件失败")
                return None

            # 获取数据库会话
            with get_database_session() as db:
                try:
                    # 创建上下文记录
                    context = Context(
                        id=context_id,
                        title=title,
                        description=description,
                        content_hash=content_hash,
                        file_path=filename,
                        file_size=file_size,
                        original_size=original_size,
                        compression_ratio=compression_ratio,
                        user_id=user_id,
                        session_id=session_id,
                        project_path=project_path,
                        visibility=visibility,
                        auto_save_enabled=auto_save_enabled,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        last_accessed_at=datetime.utcnow()
                    )

                    db.add(context)
                    db.flush()  # 获取context.id

                    # 添加标签
                    if tags:
                        for tag_name in tags:
                            tag = ContextTag(
                                context_id=context_id,
                                tag_name=tag_name.strip().lower(),
                                created_at=datetime.utcnow()
                            )
                            db.add(tag)

                    # 添加访问记录
                    access_record = ContextAccess(
                        context_id=context_id,
                        user_id=user_id,
                        access_type="create",
                        accessed_at=datetime.utcnow()
                    )
                    db.add(access_record)

                    db.commit()

                    # 添加到搜索索引
                    await self.search_service.add_document(
                        doc_id=context_id,
                        title=title,
                        content=content_json,
                        file_path=filename,
                        file_type="context",
                        tags=tags,
                        metadata={
                            "user_id": user_id,
                            "session_id": session_id,
                            "project_path": project_path,
                            "visibility": visibility,
                            "description": description
                        }
                    )

                    self.logger.info(f"成功保存上下文: {context_id}")
                    return context_id

                except Exception as e:
                    db.rollback()
                    self.logger.error(f"保存上下文到数据库失败: {e}")
                    # 清理已保存的文件
                    await self.storage_service.delete_file(filename)
                    return None

        except Exception as e:
            self.logger.error(f"保存上下文失败: {e}")
            return None

    async def load_context(self, context_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """
        加载上下文数据

        Args:
            context_id: 上下文ID
            user_id: 用户ID（用于权限检查）

        Returns:
            上下文内容字典，加载失败返回None
        """
        try:
            with get_database_session() as db:
                # 查询上下文记录
                context = db.query(Context).filter(Context.id == context_id).first()
                if not context:
                    self.logger.warning(f"上下文不存在: {context_id}")
                    return None

                # 权限检查（如果提供了user_id）
                if user_id and context.user_id != user_id and context.visibility == "private":
                    self.logger.warning(f"用户无权访问上下文: {context_id}")
                    return None

                # 从文件加载压缩数据
                compressed_data = await self.storage_service.load_compressed_data(context.file_path)
                if not compressed_data:
                    self.logger.error(f"加载压缩数据失败: {context.file_path}")
                    return None

                # 验证内容哈希
                current_hash = hashlib.sha256(compressed_data).hexdigest()
                if current_hash != context.content_hash:
                    self.logger.error(f"内容哈希验证失败: {context_id}")
                    return None

                # 解压缩数据
                content_bytes = self.compression_service.decompress(compressed_data)
                if not content_bytes:
                    self.logger.error(f"解压缩数据失败: {context_id}")
                    return None

                # 解析JSON内容
                try:
                    content = json.loads(content_bytes.decode('utf-8'))
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析JSON内容失败: {e}")
                    return None

                # 更新访问时间和记录
                context.last_accessed_at = datetime.utcnow()

                # 添加访问记录
                if user_id:
                    access_record = ContextAccess(
                        context_id=context_id,
                        user_id=user_id,
                        access_type="view",
                        accessed_at=datetime.utcnow()
                    )
                    db.add(access_record)

                db.commit()

                # 构建返回数据
                result = {
                    "id": context.id,
                    "title": context.title,
                    "description": context.description,
                    "content": content,
                    "metadata": {
                        "user_id": context.user_id,
                        "session_id": context.session_id,
                        "project_path": context.project_path,
                        "visibility": context.visibility,
                        "auto_save_enabled": context.auto_save_enabled,
                        "file_size": context.file_size,
                        "original_size": context.original_size,
                        "compression_ratio": context.compression_ratio,
                        "created_at": context.created_at.isoformat() if context.created_at else None,
                        "updated_at": context.updated_at.isoformat() if context.updated_at else None,
                        "last_accessed_at": context.last_accessed_at.isoformat() if context.last_accessed_at else None,
                        "tags": [tag.tag_name for tag in context.tags] if context.tags else []
                    }
                }

                self.logger.info(f"成功加载上下文: {context_id}")
                return result

        except Exception as e:
            self.logger.error(f"加载上下文失败 {context_id}: {e}")
            return None

    async def update_context(self, context_id: str, content: Dict[str, Any] = None,
                           title: str = None, description: str = None,
                           tags: List[str] = None, user_id: str = None) -> bool:
        """
        更新上下文数据

        Args:
            context_id: 上下文ID
            content: 新的上下文内容
            title: 新标题
            description: 新描述
            tags: 新标签列表
            user_id: 用户ID

        Returns:
            更新成功返回True，失败返回False
        """
        try:
            with get_database_session() as db:
                # 查询上下文记录
                context = db.query(Context).filter(Context.id == context_id).first()
                if not context:
                    self.logger.warning(f"上下文不存在: {context_id}")
                    return False

                # 权限检查
                if user_id and context.user_id != user_id:
                    self.logger.warning(f"用户无权更新上下文: {context_id}")
                    return False

                # 更新内容
                if content is not None:
                    # 序列化新内容
                    content_json = json.dumps(content, ensure_ascii=False, indent=2)
                    content_bytes = content_json.encode('utf-8')
                    original_size = len(content_bytes)

                    # 压缩新内容
                    compressed_data = self.compression_service.compress(content_bytes)
                    if not compressed_data:
                        self.logger.error("压缩新内容失败")
                        return False

                    # 计算新哈希
                    new_hash = hashlib.sha256(compressed_data).hexdigest()

                    # 保存新的压缩数据
                    new_filename = f"context_{context_id}_updated_{int(datetime.utcnow().timestamp())}.bin"
                    if not await self.storage_service.save_compressed_data(compressed_data, new_filename):
                        self.logger.error("保存新压缩数据失败")
                        return False

                    # 删除旧文件
                    await self.storage_service.delete_file(context.file_path)

                    # 更新数据库记录
                    context.content_hash = new_hash
                    context.file_path = new_filename
                    context.file_size = len(compressed_data)
                    context.original_size = original_size
                    context.compression_ratio = len(compressed_data) / original_size if original_size > 0 else 0

                    # 更新搜索索引
                    await self.search_service.update_document(
                        doc_id=context_id,
                        title=title if title is not None else context.title,
                        content=content_json,
                        tags=tags if tags is not None else [tag.tag_name for tag in context.tags]
                    )

                # 更新其他字段
                if title is not None:
                    context.title = title
                if description is not None:
                    context.description = description

                # 更新标签
                if tags is not None:
                    # 删除现有标签
                    db.query(ContextTag).filter(ContextTag.context_id == context_id).delete()

                    # 添加新标签
                    for tag_name in tags:
                        tag = ContextTag(
                            context_id=context_id,
                            tag_name=tag_name.strip().lower(),
                            created_at=datetime.utcnow()
                        )
                        db.add(tag)

                context.updated_at = datetime.utcnow()

                # 添加访问记录
                if user_id:
                    access_record = ContextAccess(
                        context_id=context_id,
                        user_id=user_id,
                        access_type="edit",
                        accessed_at=datetime.utcnow()
                    )
                    db.add(access_record)

                db.commit()

                self.logger.info(f"成功更新上下文: {context_id}")
                return True

        except Exception as e:
            self.logger.error(f"更新上下文失败 {context_id}: {e}")
            return False

    async def delete_context(self, context_id: str, user_id: str = None) -> bool:
        """
        删除上下文

        Args:
            context_id: 上下文ID
            user_id: 用户ID

        Returns:
            删除成功返回True，失败返回False
        """
        try:
            with get_database_session() as db:
                # 查询上下文记录
                context = db.query(Context).filter(Context.id == context_id).first()
                if not context:
                    self.logger.warning(f"上下文不存在: {context_id}")
                    return False

                # 权限检查
                if user_id and context.user_id != user_id:
                    self.logger.warning(f"用户无权删除上下文: {context_id}")
                    return False

                # 删除压缩文件
                await self.storage_service.delete_file(context.file_path)

                # 从搜索索引删除
                await self.search_service.delete_document(context_id)

                # 删除数据库记录（级联删除相关记录）
                db.delete(context)
                db.commit()

                self.logger.info(f"成功删除上下文: {context_id}")
                return True

        except Exception as e:
            self.logger.error(f"删除上下文失败 {context_id}: {e}")
            return False

    async def list_contexts(self, user_id: str = None, session_id: str = None,
                           project_path: str = None, tags: List[str] = None,
                           limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出上下文

        Args:
            user_id: 用户ID
            session_id: 会话ID
            project_path: 项目路径
            tags: 标签过滤
            limit: 结果数量限制
            offset: 结果偏移量

        Returns:
            上下文列表
        """
        try:
            with get_database_session() as db:
                query = db.query(Context)

                # 应用过滤条件
                if user_id:
                    query = query.filter(Context.user_id == user_id)
                if session_id:
                    query = query.filter(Context.session_id == session_id)
                if project_path:
                    query = query.filter(Context.project_path == project_path)

                # 标签过滤
                if tags:
                    for tag in tags:
                        query = query.join(ContextTag).filter(ContextTag.tag_name == tag.lower())

                # 排序和分页
                contexts = query.order_by(desc(Context.updated_at)).offset(offset).limit(limit).all()

                # 转换为字典列表
                result = []
                for context in contexts:
                    context_dict = {
                        "id": context.id,
                        "title": context.title,
                        "description": context.description,
                        "metadata": {
                            "user_id": context.user_id,
                            "session_id": context.session_id,
                            "project_path": context.project_path,
                            "visibility": context.visibility,
                            "auto_save_enabled": context.auto_save_enabled,
                            "file_size": context.file_size,
                            "original_size": context.original_size,
                            "compression_ratio": context.compression_ratio,
                            "created_at": context.created_at.isoformat() if context.created_at else None,
                            "updated_at": context.updated_at.isoformat() if context.updated_at else None,
                            "last_accessed_at": context.last_accessed_at.isoformat() if context.last_accessed_at else None,
                            "tags": [tag.tag_name for tag in context.tags] if context.tags else []
                        }
                    }
                    result.append(context_dict)

                self.logger.debug(f"列出上下文，找到 {len(result)} 个结果")
                return result

        except Exception as e:
            self.logger.error(f"列出上下文失败: {e}")
            return []

    async def get_context_stats(self, user_id: str = None) -> Dict[str, Any]:
        """
        获取上下文统计信息

        Args:
            user_id: 用户ID（可选）

        Returns:
            统计信息字典
        """
        try:
            with get_database_session() as db:
                query = db.query(Context)

                if user_id:
                    query = query.filter(Context.user_id == user_id)

                # 统计查询
                total_contexts = query.count()
                auto_save_enabled = query.filter(Context.auto_save_enabled == True).count()

                # 计算总大小和压缩信息
                contexts = query.all()
                total_original_size = sum(c.original_size for c in contexts)
                total_compressed_size = sum(c.file_size for c in contexts)
                overall_compression_ratio = total_compressed_size / total_original_size if total_original_size > 0 else 0

                # 获取最近的上下文
                recent_context = query.order_by(desc(Context.updated_at)).first()

                # 获取所有唯一标签
                tags_query = db.query(ContextTag.tag_name).distinct()
                if user_id:
                    tags_query = tags_query.join(Context).filter(Context.user_id == user_id)
                total_tags = tags_query.count()

                stats = {
                    "total_contexts": total_contexts,
                    "auto_save_enabled": auto_save_enabled,
                    "total_original_size": total_original_size,
                    "total_compressed_size": total_compressed_size,
                    "space_saved": total_original_size - total_compressed_size,
                    "compression_ratio": round(overall_compression_ratio, 4),
                    "space_saved_percent": round((1 - overall_compression_ratio) * 100, 2) if overall_compression_ratio > 0 else 0,
                    "total_tags": total_tags,
                    "most_recent_context": {
                        "id": recent_context.id,
                        "title": recent_context.title,
                        "updated_at": recent_context.updated_at.isoformat() if recent_context.updated_at else None
                    } if recent_context else None,
                    "storage_stats": await self.storage_service.get_storage_stats(),
                    "search_stats": await self.search_service.get_index_stats()
                }

                self.logger.debug(f"获取上下文统计信息完成")
                return stats

        except Exception as e:
            self.logger.error(f"获取上下文统计信息失败: {e}")
            return {
                "total_contexts": 0,
                "error": str(e)
            }

    async def search_contexts(self, query_str: str, user_id: str = None,
                             limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        搜索上下文

        Args:
            query_str: 搜索查询字符串
            user_id: 用户ID（用于权限过滤）
            limit: 结果数量限制
            offset: 结果偏移量

        Returns:
            搜索结果列表
        """
        try:
            # 使用搜索服务进行全文搜索
            search_results = await self.search_service.search(
                query_str=query_str,
                limit=limit,
                offset=offset
            )

            # 过滤结果（权限检查）
            filtered_results = []
            with get_database_session() as db:
                for result in search_results:
                    context_id = result['id']
                    context = db.query(Context).filter(Context.id == context_id).first()

                    if context:
                        # 权限检查
                        if not user_id or context.user_id == user_id or context.visibility != "private":
                            filtered_result = {
                                "id": context.id,
                                "title": context.title,
                                "description": context.description,
                                "content_preview": result['content'],
                                "score": result['score'],
                                "metadata": {
                                    "user_id": context.user_id,
                                    "session_id": context.session_id,
                                    "project_path": context.project_path,
                                    "visibility": context.visibility,
                                    "file_size": context.file_size,
                                    "original_size": context.original_size,
                                    "compression_ratio": context.compression_ratio,
                                    "created_at": context.created_at.isoformat() if context.created_at else None,
                                    "updated_at": context.updated_at.isoformat() if context.updated_at else None,
                                    "tags": [tag.tag_name for tag in context.tags] if context.tags else []
                                }
                            }
                            filtered_results.append(filtered_result)

            self.logger.debug(f"搜索上下文完成，找到 {len(filtered_results)} 个结果")
            return filtered_results

        except Exception as e:
            self.logger.error(f"搜索上下文失败: {e}")
            return []

    async def search_contexts_advanced(self, query: str = None, user_id: str = None,
                                     tags: List[str] = None, session_id: str = None,
                                     project_path: str = None, visibility: str = None,
                                     date_from: str = None, date_to: str = None,
                                     content_type: str = None, file_size_min: int = None,
                                     file_size_max: int = None, sort_by: str = "created_at",
                                     sort_order: str = "desc", limit: int = 10,
                                     offset: int = 0) -> List[Dict[str, Any]]:
        """
        高级搜索上下文，支持多种过滤条件

        Args:
            query: 全文搜索查询字符串
            user_id: 用户ID过滤
            tags: 标签过滤
            session_id: 会话ID过滤
            project_path: 项目路径过滤
            visibility: 可见性过滤
            date_from: 开始日期过滤 (ISO格式)
            date_to: 结束日期过滤 (ISO格式)
            content_type: 内容类型过滤
            file_size_min: 最小文件大小过滤
            file_size_max: 最大文件大小过滤
            sort_by: 排序字段
            sort_order: 排序方向 (asc/desc)
            limit: 结果数量限制
            offset: 结果偏移量

        Returns:
            搜索结果列表
        """
        try:
            with get_database_session() as db:
                # 构建基础查询
                db_query = db.query(Context)

                # 应用过滤条件
                if user_id:
                    db_query = db_query.filter(Context.user_id == user_id)
                elif visibility != "public":
                    # 如果没有指定用户ID，只显示公开和团队可见的上下文
                    db_query = db_query.filter(Context.visibility != "private")

                if session_id:
                    db_query = db_query.filter(Context.session_id == session_id)

                if project_path:
                    db_query = db_query.filter(Context.project_path.like(f"%{project_path}%"))

                if visibility:
                    db_query = db_query.filter(Context.visibility == visibility)

                if file_size_min is not None:
                    db_query = db_query.filter(Context.file_size >= file_size_min)

                if file_size_max is not None:
                    db_query = db_query.filter(Context.file_size <= file_size_max)

                # 日期过滤
                if date_from:
                    try:
                        date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                        db_query = db_query.filter(Context.created_at >= date_from_obj)
                    except ValueError:
                        self.logger.warning(f"无效的开始日期格式: {date_from}")

                if date_to:
                    try:
                        date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                        db_query = db_query.filter(Context.created_at <= date_to_obj)
                    except ValueError:
                        self.logger.warning(f"无效的结束日期格式: {date_to}")

                # 标签过滤
                if tags:
                    from sqlalchemy import or_
                    tag_conditions = []
                    for tag in tags:
                        # 关联查询，通过中间表过滤
                        tag_conditions.append(
                            Context.tags.any(tag_name=tag)
                        )
                    if tag_conditions:
                        db_query = db_query.filter(or_(*tag_conditions))

                # 排序
                sort_column = getattr(Context, sort_by, Context.created_at)
                if sort_order.lower() == "desc":
                    db_query = db_query.order_by(sort_column.desc())
                else:
                    db_query = db_query.order_by(sort_column.asc())

                # 应用分页
                contexts = db_query.offset(offset).limit(limit).all()

                # 如果有全文搜索查询，使用搜索服务进行进一步过滤
                if query:
                    search_results = await self.search_service.search(
                        query_str=query,
                        limit=limit * 2,  # 获取更多结果用于过滤
                        offset=0
                    )

                    # 获取搜索结果的ID集合
                    search_ids = {result['id'] for result in search_results}

                    # 过滤数据库查询结果，只保留在搜索结果中的
                    filtered_contexts = [ctx for ctx in contexts if ctx.id in search_ids]
                else:
                    filtered_contexts = contexts

                # 转换为响应格式
                results = []
                for context in filtered_contexts:
                    # 获取标签列表
                    tag_list = [tag.tag_name for tag in context.tags] if context.tags else []

                    result = {
                        "id": context.id,
                        "title": context.title,
                        "description": context.description,
                        "content_preview": "",  # 可以根据需要添加内容预览
                        "metadata": {
                            "user_id": context.user_id,
                            "session_id": context.session_id,
                            "project_path": context.project_path,
                            "visibility": context.visibility,
                            "file_size": context.file_size,
                            "original_size": context.original_size,
                            "compression_ratio": context.compression_ratio,
                            "created_at": context.created_at.isoformat() if context.created_at else None,
                            "updated_at": context.updated_at.isoformat() if context.updated_at else None,
                            "tags": tag_list
                        },
                        "score": 1.0 if not query else 0.0  # 如果没有搜索查询，默认分数
                    }

                    # 如果有搜索查询，计算匹配分数
                    if query:
                        for search_result in search_results:
                            if search_result['id'] == context.id:
                                result['score'] = search_result['score']
                                result['content_preview'] = search_result.get('content', '')[:200] + '...' if len(search_result.get('content', '')) > 200 else search_result.get('content', '')
                                break

                    results.append(result)

                # 如果有搜索查询，按分数重新排序
                if query:
                    results.sort(key=lambda x: x['score'], reverse=True)

                self.logger.debug(f"高级搜索完成，找到 {len(results)} 个结果")
                return results

        except Exception as e:
            self.logger.error(f"高级搜索上下文失败: {e}")
            return []

    async def get_search_suggestions(self, query_prefix: str, user_id: str = None,
                                   limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取搜索建议（基于标题和标签）

        Args:
            query_prefix: 查询前缀
            user_id: 用户ID（用于权限过滤）
            limit: 建议数量限制

        Returns:
            搜索建议列表
        """
        try:
            suggestions = []

            with get_database_session() as db:
                # 搜索标题匹配的建议
                title_matches = db.query(Context).filter(
                    Context.title.like(f"%{query_prefix}%")
                )

                if user_id:
                    title_matches = title_matches.filter(
                        (Context.user_id == user_id) | (Context.visibility != "private")
                    )
                else:
                    title_matches = title_matches.filter(Context.visibility == "public")

                title_matches = title_matches.limit(limit).all()

                for context in title_matches:
                    # 突出显示匹配的部分
                    title_lower = context.title.lower()
                    prefix_lower = query_prefix.lower()

                    if prefix_lower in title_lower:
                        start_idx = title_lower.find(prefix_lower)
                        end_idx = start_idx + len(prefix_lower)
                        highlighted_title = (
                            context.title[:start_idx] +
                            f"**{context.title[start_idx:end_idx]}**" +
                            context.title[end_idx:]
                        )
                    else:
                        highlighted_title = context.title

                    suggestions.append({
                        "type": "title",
                        "text": context.title,
                        "highlighted": highlighted_title,
                        "context_id": context.id,
                        "description": context.description
                    })

                # 搜索标签匹配的建议
                from models.tag import Tag
                tag_matches = db.query(Tag).filter(
                    Tag.tag_name.like(f"%{query_prefix}%")
                ).limit(limit).all()

                for tag in tag_matches:
                    # 计算使用次数
                    usage_count = db.query(Context).filter(
                        Context.tags.any(tag_name=tag.tag_name)
                    ).count()

                    if user_id:
                        usage_count = db.query(Context).filter(
                            Context.tags.any(tag_name=tag.tag_name),
                            (Context.user_id == user_id) | (Context.visibility != "private")
                        ).count()

                    if usage_count > 0:
                        suggestions.append({
                            "type": "tag",
                            "text": tag.tag_name,
                            "highlighted": f"**{tag.tag_name}**",
                            "usage_count": usage_count,
                            "description": f"Used in {usage_count} contexts"
                        })

            # 限制建议数量并按类型和相关性排序
            suggestions = suggestions[:limit]

            # 标题建议优先，然后是标签建议
            suggestions.sort(key=lambda x: (x['type'] != 'title', -len(x['text'])))

            return suggestions

        except Exception as e:
            self.logger.error(f"获取搜索建议失败: {e}")
            return []

    async def get_popular_tags(self, user_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取热门标签列表（按使用频率排序）

        Args:
            user_id: 用户ID（用于权限过滤）
            limit: 标签数量限制

        Returns:
            热门标签列表
        """
        try:
            with get_database_session() as db:
                from models.tag import Tag
                from sqlalchemy import func

                # 构建查询，统计每个标签的使用次数
                query = db.query(
                    Tag.tag_name,
                    func.count(Context.id).label('usage_count')
                ).join(
                    Context.tags
                )

                # 应用用户权限过滤
                if user_id:
                    query = query.filter(
                        (Context.user_id == user_id) | (Context.visibility != "private")
                    )
                else:
                    query = query.filter(Context.visibility == "public")

                # 按使用次数排序
                tags = query.group_by(Tag.tag_name).order_by(
                    func.count(Context.id).desc()
                ).limit(limit).all()

                # 转换为响应格式
                result = []
                for tag_name, usage_count in tags:
                    result.append({
                        "tag_name": tag_name,
                        "usage_count": usage_count,
                        "description": f"Used in {usage_count} contexts"
                    })

                return result

        except Exception as e:
            self.logger.error(f"获取热门标签失败: {e}")
            return []

    async def get_available_projects(self, user_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取可用的项目路径列表

        Args:
            user_id: 用户ID（用于权限过滤）
            limit: 项目数量限制

        Returns:
            项目路径列表
        """
        try:
            with get_database_session() as db:
                from sqlalchemy import func

                # 构建查询，统计每个项目的使用次数
                query = db.query(
                    Context.project_path,
                    func.count(Context.id).label('context_count')
                ).filter(
                    Context.project_path.isnot(None),
                    Context.project_path != ""
                )

                # 应用用户权限过滤
                if user_id:
                    query = query.filter(
                        (Context.user_id == user_id) | (Context.visibility != "private")
                    )
                else:
                    query = query.filter(Context.visibility == "public")

                # 按使用次数排序
                projects = query.group_by(Context.project_path).order_by(
                    func.count(Context.id).desc()
                ).limit(limit).all()

                # 转换为响应格式
                result = []
                for project_path, context_count in projects:
                    result.append({
                        "project_path": project_path,
                        "context_count": context_count,
                        "description": f"Contains {context_count} contexts"
                    })

                return result

        except Exception as e:
            self.logger.error(f"获取项目列表失败: {e}")
            return []

    async def get_available_sessions(self, user_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取可用的会话ID列表

        Args:
            user_id: 用户ID（用于权限过滤）
            limit: 会话数量限制

        Returns:
            会话ID列表
        """
        try:
            with get_database_session() as db:
                from sqlalchemy import func

                # 构建查询，统计每个会话的上下文数量
                query = db.query(
                    Context.session_id,
                    func.count(Context.id).label('context_count'),
                    func.max(Context.created_at).label('last_activity')
                ).filter(
                    Context.session_id.isnot(None),
                    Context.session_id != ""
                )

                # 应用用户权限过滤
                if user_id:
                    query = query.filter(
                        (Context.user_id == user_id) | (Context.visibility != "private")
                    )
                else:
                    query = query.filter(Context.visibility == "public")

                # 按最后活动时间排序
                sessions = query.group_by(Context.session_id).order_by(
                    func.max(Context.created_at).desc()
                ).limit(limit).all()

                # 转换为响应格式
                result = []
                for session_id, context_count, last_activity in sessions:
                    result.append({
                        "session_id": session_id,
                        "context_count": context_count,
                        "last_activity": last_activity.isoformat() if last_activity else None,
                        "description": f"Contains {context_count} contexts"
                    })

                return result

        except Exception as e:
            self.logger.error(f"获取会话列表失败: {e}")
            return []