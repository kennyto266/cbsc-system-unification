"""
Permission service module - 处理用户角色、访问级别和共享链接管理
"""

import uuid
import secrets
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from models.context import Context, ContextShare, ContextAccess
from config.database import get_database_session

logger = logging.getLogger(__name__)


class PermissionService:
    """权限服务类，提供用户角色、访问级别和共享链接管理功能"""

    def __init__(self):
        """初始化权限服务"""
        self.logger = logging.getLogger(__name__)

        # 定义权限级别
        self.PERMISSION_LEVELS = {
            "viewer": {
                "can_view": True,
                "can_edit": False,
                "can_share": False,
                "can_delete": False,
                "description": "Can only view the context"
            },
            "editor": {
                "can_view": True,
                "can_edit": True,
                "can_share": False,
                "can_delete": False,
                "description": "Can view and edit the context"
            },
            "owner": {
                "can_view": True,
                "can_edit": True,
                "can_share": True,
                "can_delete": True,
                "description": "Full access to the context"
            }
        }

        # 定义角色层次结构
        self.ROLE_HIERARCHY = {
            "viewer": 1,
            "editor": 2,
            "owner": 3
        }

    def _generate_share_token(self) -> str:
        """生成安全的共享令牌"""
        return secrets.token_urlsafe(32)

    def _hash_share_token(self, token: str) -> str:
        """对共享令牌进行哈希处理"""
        return hashlib.sha256(token.encode()).hexdigest()

    async def check_permission(self, context_id: str, user_id: str,
                             required_permission: str = "view") -> Tuple[bool, Optional[str]]:
        """
        检查用户对上下文的权限

        Args:
            context_id: 上下文ID
            user_id: 用户ID
            required_permission: 所需权限类型 (view, edit, share, delete)

        Returns:
            (是否有权限, 权限级别) 元组
        """
        try:
            with get_database_session() as db:
                # 查询上下文
                context = db.query(Context).filter(Context.id == context_id).first()
                if not context:
                    return False, None

                # 上下文所有者拥有所有权限
                if context.user_id == user_id:
                    return True, "owner"

                # 检查上下文可见性
                if context.visibility == "private":
                    return False, None
                elif context.visibility == "public" and required_permission == "view":
                    return True, "viewer"

                # 检查显式权限
                share = db.query(ContextShare).filter(
                    and_(
                        ContextShare.context_id == context_id,
                        ContextShare.shared_with_user_id == user_id,
                        ContextShare.is_active == True
                    )
                ).first()

                if share:
                    # 检查共享是否过期
                    if share.is_expired():
                        share.is_active = False
                        db.commit()
                        return False, None

                    # 检查具体权限
                    permission_map = {
                        "view": True,  # 所有共享都有查看权限
                        "edit": share.can_edit,
                        "share": share.can_share,
                        "delete": share.can_delete
                    }

                    if required_permission in permission_map and permission_map[required_permission]:
                        return True, share.permission_level

                return False, None

        except Exception as e:
            self.logger.error(f"检查权限失败: {e}")
            return False, None

    async def share_context(self, context_id: str, shared_by_user_id: str,
                          shared_with_user_id: str = None, permission_level: str = "viewer",
                          expires_at: datetime = None, message: str = None) -> Optional[str]:
        """
        共享上下文给其他用户

        Args:
            context_id: 上下文ID
            shared_by_user_id: 共享者用户ID
            shared_with_user_id: 被共享者用户ID（None表示创建公开链接）
            permission_level: 权限级别 (viewer, editor, owner)
            expires_at: 过期时间
            message: 共享消息

        Returns:
            共享ID，失败返回None
        """
        try:
            # 验证权限级别
            if permission_level not in self.PERMISSION_LEVELS:
                self.logger.error(f"无效的权限级别: {permission_level}")
                return None

            with get_database_session() as db:
                # 检查上下文是否存在
                context = db.query(Context).filter(Context.id == context_id).first()
                if not context:
                    self.logger.warning(f"上下文不存在: {context_id}")
                    return None

                # 检查共享者是否有权限
                has_permission, _ = await self.check_permission(context_id, shared_by_user_id, "share")
                if not has_permission:
                    self.logger.warning(f"用户无权共享上下文: {shared_by_user_id}")
                    return None

                # 检查是否已经共享给该用户
                existing_share = db.query(ContextShare).filter(
                    and_(
                        ContextShare.context_id == context_id,
                        ContextShare.shared_with_user_id == shared_with_user_id,
                        ContextShare.is_active == True
                    )
                ).first()

                if existing_share:
                    # 更新现有共享
                    existing_share.permission_level = permission_level
                    existing_share.can_edit = self.PERMISSION_LEVELS[permission_level]["can_edit"]
                    existing_share.can_share = self.PERMISSION_LEVELS[permission_level]["can_share"]
                    existing_share.can_delete = self.PERMISSION_LEVELS[permission_level]["can_delete"]
                    existing_share.expires_at = expires_at
                    existing_share.updated_at = datetime.utcnow()
                    existing_share.is_active = True

                    share_id = existing_share.id
                else:
                    # 创建新共享
                    share_id = str(uuid.uuid4())

                    # 如果是公开分享，生成共享令牌
                    share_token = self._generate_share_token() if shared_with_user_id is None else None

                    share = ContextShare(
                        id=share_id,
                        context_id=context_id,
                        shared_by_user_id=shared_by_user_id,
                        shared_with_user_id=shared_with_user_id,
                        share_token=share_token,
                        permission_level=permission_level,
                        can_edit=self.PERMISSION_LEVELS[permission_level]["can_edit"],
                        can_share=self.PERMISSION_LEVELS[permission_level]["can_share"],
                        can_delete=self.PERMISSION_LEVELS[permission_level]["can_delete"],
                        expires_at=expires_at,
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )

                    db.add(share)

                # 记录访问日志
                access_record = ContextAccess(
                    context_id=context_id,
                    user_id=shared_by_user_id,
                    access_type="share",
                    accessed_at=datetime.utcnow()
                )
                db.add(access_record)

                db.commit()

                self.logger.info(f"成功共享上下文: {context_id} 给 {shared_with_user_id or '公开链接'}")
                return share_id

        except Exception as e:
            self.logger.error(f"共享上下文失败: {e}")
            return None

    async def create_share_link(self, context_id: str, shared_by_user_id: str,
                              permission_level: str = "viewer", expires_hours: int = 24,
                              max_accesses: int = None) -> Optional[str]:
        """
        创建匿名共享链接

        Args:
            context_id: 上下文ID
            shared_by_user_id: 共享者用户ID
            permission_level: 权限级别
            expires_hours: 过期小时数
            max_accesses: 最大访问次数（可选）

        Returns:
            共享令牌，失败返回None
        """
        try:
            # 检查权限
            has_permission, _ = await self.check_permission(context_id, shared_by_user_id, "share")
            if not has_permission:
                self.logger.warning(f"用户无权创建共享链接: {shared_by_user_id}")
                return None

            # 计算过期时间
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours) if expires_hours > 0 else None

            # 创建共享
            share_id = await self.share_context(
                context_id=context_id,
                shared_by_user_id=shared_by_user_id,
                shared_with_user_id=None,  # None 表示公开共享
                permission_level=permission_level,
                expires_at=expires_at
            )

            if share_id:
                # 获取生成的共享令牌
                with get_database_session() as db:
                    share = db.query(ContextShare).filter(ContextShare.id == share_id).first()
                    if share and share.share_token:
                        return share.share_token

            return None

        except Exception as e:
            self.logger.error(f"创建共享链接失败: {e}")
            return None

    async def access_by_share_token(self, share_token: str, user_id: str = None,
                                  ip_address: str = None, user_agent: str = None) -> Optional[Dict[str, Any]]:
        """
        通过共享令牌访问上下文

        Args:
            share_token: 共享令牌
            user_id: 访问者用户ID（可选）
            ip_address: 访问者IP地址
            user_agent: 用户代理

        Returns:
            上下文信息，失败返回None
        """
        try:
            with get_database_session() as db:
                # 查找共享记录
                share = db.query(ContextShare).filter(
                    and_(
                        ContextShare.share_token == share_token,
                        ContextShare.is_active == True
                    )
                ).first()

                if not share:
                    self.logger.warning(f"无效的共享令牌: {share_token}")
                    return None

                # 检查是否过期
                if share.is_expired():
                    share.is_active = False
                    db.commit()
                    self.logger.warning(f"共享链接已过期: {share_token}")
                    return None

                # 获取上下文
                context = db.query(Context).filter(Context.id == share.context_id).first()
                if not context:
                    self.logger.warning(f"上下文不存在: {share.context_id}")
                    return None

                # 更新访问时间
                share.last_accessed_at = datetime.utcnow()

                # 记录访问日志
                access_record = ContextAccess(
                    context_id=share.context_id,
                    user_id=user_id or "anonymous",
                    access_type="view",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    accessed_at=datetime.utcnow()
                )
                db.add(access_record)

                db.commit()

                # 返回上下文信息（不包含内容）
                result = {
                    "context_id": context.id,
                    "title": context.title,
                    "description": context.description,
                    "permission_level": share.permission_level,
                    "can_edit": share.can_edit,
                    "can_share": share.can_share,
                    "can_delete": share.can_delete,
                    "expires_at": share.expires_at.isoformat() if share.expires_at else None,
                    "shared_by": share.shared_by_user_id,
                    "metadata": {
                        "user_id": context.user_id,
                        "visibility": context.visibility,
                        "created_at": context.created_at.isoformat() if context.created_at else None,
                        "updated_at": context.updated_at.isoformat() if context.updated_at else None,
                        "tags": [tag.tag_name for tag in context.tags] if context.tags else []
                    }
                }

                self.logger.info(f"通过共享令牌成功访问上下文: {share.context_id}")
                return result

        except Exception as e:
            self.logger.error(f"通过共享令牌访问失败: {e}")
            return None

    async def revoke_share(self, share_id: str, user_id: str) -> bool:
        """
        撤销共享

        Args:
            share_id: 共享ID
            user_id: 操作用户ID

        Returns:
            操作成功返回True，失败返回False
        """
        try:
            with get_database_session() as db:
                share = db.query(ContextShare).filter(ContextShare.id == share_id).first()
                if not share:
                    self.logger.warning(f"共享不存在: {share_id}")
                    return False

                # 检查权限（只有上下文所有者或共享者可以撤销）
                if share.shared_by_user_id != user_id:
                    # 检查是否是上下文所有者
                    context = db.query(Context).filter(Context.id == share.context_id).first()
                    if not context or context.user_id != user_id:
                        self.logger.warning(f"用户无权撤销共享: {user_id}")
                        return False

                # 撤销共享
                share.is_active = False
                share.updated_at = datetime.utcnow()

                # 记录访问日志
                access_record = ContextAccess(
                    context_id=share.context_id,
                    user_id=user_id,
                    access_type="revoke_share",
                    accessed_at=datetime.utcnow()
                )
                db.add(access_record)

                db.commit()

                self.logger.info(f"成功撤销共享: {share_id}")
                return True

        except Exception as e:
            self.logger.error(f"撤销共享失败: {e}")
            return False

    async def list_shares(self, context_id: str = None, user_id: str = None,
                         include_expired: bool = False, limit: int = 50,
                         offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出共享

        Args:
            context_id: 上下文ID过滤（可选）
            user_id: 用户ID过滤（可选）
            include_expired: 是否包含已过期的共享
            limit: 结果数量限制
            offset: 结果偏移量

        Returns:
            共享列表
        """
        try:
            with get_database_session() as db:
                query = db.query(ContextShare)

                # 应用过滤条件
                if context_id:
                    query = query.filter(ContextShare.context_id == context_id)

                if user_id:
                    # 查询用户共享的或被共享的上下文
                    query = query.filter(
                        or_(
                            ContextShare.shared_by_user_id == user_id,
                            ContextShare.shared_with_user_id == user_id
                        )
                    )

                if not include_expired:
                    query = query.filter(ContextShare.is_active == True)

                # 排序和分页
                shares = query.order_by(desc(ContextShare.created_at)).offset(offset).limit(limit).all()

                # 转换为字典列表
                result = []
                for share in shares:
                    share_dict = share.to_dict()

                    # 添加上下文信息
                    context = db.query(Context).filter(Context.id == share.context_id).first()
                    if context:
                        share_dict["context_title"] = context.title
                        share_dict["context_description"] = context.description

                    result.append(share_dict)

                self.logger.debug(f"列出共享，找到 {len(result)} 个结果")
                return result

        except Exception as e:
            self.logger.error(f"列出共享失败: {e}")
            return []

    async def get_user_permissions(self, user_id: str, context_id: str = None) -> Dict[str, Any]:
        """
        获取用户权限信息

        Args:
            user_id: 用户ID
            context_id: 上下文ID（可选）

        Returns:
            用户权限信息
        """
        try:
            with get_database_session() as db:
                result = {
                    "user_id": user_id,
                    "permissions": {},
                    "shares_received": [],
                    "shares_given": [],
                    "total_accessible_contexts": 0
                }

                # 如果指定了上下文ID，获取特定权限
                if context_id:
                    has_permission, permission_level = await self.check_permission(context_id, user_id, "view")
                    result["permissions"][context_id] = {
                        "has_access": has_permission,
                        "permission_level": permission_level,
                        "can_edit": await self.check_permission(context_id, user_id, "edit")[0],
                        "can_share": await self.check_permission(context_id, user_id, "share")[0],
                        "can_delete": await self.check_permission(context_id, user_id, "delete")[0]
                    }
                else:
                    # 获取所有可访问的上下文
                    # 1. 用户拥有的上下文
                    owned_contexts = db.query(Context).filter(Context.user_id == user_id).all()

                    # 2. 公开的上下文
                    public_contexts = db.query(Context).filter(Context.visibility == "public").all()

                    # 3. 明确共享给用户的上下文
                    shared_contexts = db.query(Context).join(ContextShare).filter(
                        and_(
                            ContextShare.shared_with_user_id == user_id,
                            ContextShare.is_active == True
                        )
                    ).all()

                    # 合并所有可访问的上下文
                    all_contexts = set(owned_contexts + public_contexts + shared_contexts)
                    result["total_accessible_contexts"] = len(all_contexts)

                    # 为每个上下文添加权限信息
                    for context in all_contexts:
                        result["permissions"][context.id] = {
                            "title": context.title,
                            "is_owner": context.user_id == user_id,
                            "visibility": context.visibility,
                            "permission_level": "owner" if context.user_id == user_id else "viewer"
                        }

                # 获取收到的共享
                shares_received = db.query(ContextShare).filter(
                    and_(
                        ContextShare.shared_with_user_id == user_id,
                        ContextShare.is_active == True
                    )
                ).all()

                for share in shares_received:
                    share_dict = share.to_dict()
                    context = db.query(Context).filter(Context.id == share.context_id).first()
                    if context:
                        share_dict["context_title"] = context.title
                    result["shares_received"].append(share_dict)

                # 获取发出的共享
                shares_given = db.query(ContextShare).filter(
                    ContextShare.shared_by_user_id == user_id
                ).all()

                for share in shares_given:
                    share_dict = share.to_dict()
                    context = db.query(Context).filter(Context.id == share.context_id).first()
                    if context:
                        share_dict["context_title"] = context.title
                    result["shares_given"].append(share_dict)

                return result

        except Exception as e:
            self.logger.error(f"获取用户权限失败: {e}")
            return {"error": str(e)}

    async def update_share_permission(self, share_id: str, user_id: str,
                                    new_permission_level: str) -> bool:
        """
        更新共享权限级别

        Args:
            share_id: 共享ID
            user_id: 操作用户ID
            new_permission_level: 新的权限级别

        Returns:
            更新成功返回True，失败返回False
        """
        try:
            if new_permission_level not in self.PERMISSION_LEVELS:
                self.logger.error(f"无效的权限级别: {new_permission_level}")
                return False

            with get_database_session() as db:
                share = db.query(ContextShare).filter(ContextShare.id == share_id).first()
                if not share:
                    self.logger.warning(f"共享不存在: {share_id}")
                    return False

                # 检查权限（只有上下文所有者或共享者可以更新）
                if share.shared_by_user_id != user_id:
                    # 检查是否是上下文所有者
                    context = db.query(Context).filter(Context.id == share.context_id).first()
                    if not context or context.user_id != user_id:
                        self.logger.warning(f"用户无权更新共享权限: {user_id}")
                        return False

                # 更新权限
                old_permission = share.permission_level
                share.permission_level = new_permission_level
                share.can_edit = self.PERMISSION_LEVELS[new_permission_level]["can_edit"]
                share.can_share = self.PERMISSION_LEVELS[new_permission_level]["can_share"]
                share.can_delete = self.PERMISSION_LEVELS[new_permission_level]["can_delete"]
                share.updated_at = datetime.utcnow()

                # 记录访问日志
                access_record = ContextAccess(
                    context_id=share.context_id,
                    user_id=user_id,
                    access_type="update_permission",
                    accessed_at=datetime.utcnow()
                )
                db.add(access_record)

                db.commit()

                self.logger.info(f"成功更新共享权限: {share_id} 从 {old_permission} 到 {new_permission_level}")
                return True

        except Exception as e:
            self.logger.error(f"更新共享权限失败: {e}")
            return False

    async def get_access_logs(self, context_id: str = None, user_id: str = None,
                            access_type: str = None, limit: int = 100,
                            offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取访问日志

        Args:
            context_id: 上下文ID过滤（可选）
            user_id: 用户ID过滤（可选）
            access_type: 访问类型过滤（可选）
            limit: 结果数量限制
            offset: 结果偏移量

        Returns:
            访问日志列表
        """
        try:
            with get_database_session() as db:
                query = db.query(ContextAccess)

                # 应用过滤条件
                if context_id:
                    query = query.filter(ContextAccess.context_id == context_id)

                if user_id:
                    query = query.filter(ContextAccess.user_id == user_id)

                if access_type:
                    query = query.filter(ContextAccess.access_type == access_type)

                # 排序和分页
                logs = query.order_by(desc(ContextAccess.accessed_at)).offset(offset).limit(limit).all()

                # 转换为字典列表
                result = []
                for log in logs:
                    log_dict = log.to_dict()

                    # 添加上下文信息
                    context = db.query(Context).filter(Context.id == log.context_id).first()
                    if context:
                        log_dict["context_title"] = context.title

                    result.append(log_dict)

                self.logger.debug(f"获取访问日志，找到 {len(result)} 条记录")
                return result

        except Exception as e:
            self.logger.error(f"获取访问日志失败: {e}")
            return []

    def get_permission_levels(self) -> Dict[str, Any]:
        """
        获取所有可用的权限级别

        Returns:
            权限级别定义
        """
        return self.PERMISSION_LEVELS.copy()

    async def cleanup_expired_shares(self) -> int:
        """
        清理过期的共享

        Returns:
            清理的共享数量
        """
        try:
            with get_database_session() as db:
                # 查找过期但仍激活的共享
                expired_shares = db.query(ContextShare).filter(
                    and_(
                        ContextShare.is_active == True,
                        ContextShare.expires_at < datetime.utcnow()
                    )
                ).all()

                cleaned_count = 0
                for share in expired_shares:
                    share.is_active = False
                    share.updated_at = datetime.utcnow()
                    cleaned_count += 1

                db.commit()

                self.logger.info(f"清理了 {cleaned_count} 个过期共享")
                return cleaned_count

        except Exception as e:
            self.logger.error(f"清理过期共享失败: {e}")
            return 0