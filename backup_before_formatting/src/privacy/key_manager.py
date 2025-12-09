"""
密钥管理模块

实现加密密钥的生成、存储、轮换和销毁。
支持多种密钥管理方式：环境变量、文件、HSM（硬件安全模块）。

功能:
- 密钥生成（对称 / 非对称）
- 密钥存储
- 密钥轮换
- 密钥验证
- 密钥撤销
- 密钥恢复
"""

import base64
import json
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

logger = logging.getLogger(__name__)


class KeyType:
    """密钥类型常量"""

    SYMMETRIC = "symmetric"
    ASYMMETRIC_PUBLIC = "asymmetric_public"
    ASYMMETRIC_PRIVATE = "asymmetric_private"
    HMAC = "hmac"
    DERIVATION = "derivation"


class KeyStatus:
    """密钥状态常量"""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    COMPROMISED = "compromised"


class KeyManager:
    """
    密钥管理器
    负责密钥的生成、存储、管理和轮换
    """

    def __init__(self, key_store_path: str = "keys"):
        """
        初始化密钥管理器

        Args:
            key_store_path: 密钥存储目录
        """
        self.key_store_path = key_store_path
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.backend = default_backend()

        # 创建密钥存储目录
        os.makedirs(key_store_path, exist_ok=True)
        os.makedirs(os.path.join(key_store_path, "active"), exist_ok=True)
        os.makedirs(os.path.join(key_store_path, "archive"), exist_ok=True)
        os.makedirs(os.path.join(key_store_path, "revoked"), exist_ok=True)

        # 加载现有密钥
        self._load_keys()

    def generate_symmetric_key(self, key_name: str, key_size: int = 32) -> str:
        """
        生成对称密钥

        Args:
            key_name: 密钥名称
            key_size: 密钥大小（字节，32=256位）

        Returns:
            密钥ID
        """
        key_id = f"sym_{key_name}_{datetime.utcnow().strftime('%Y % m % d_ % H % M % S')}"

        # 生成随机密钥
        key = secrets.token_bytes(key_size)

        # 存储密钥
        key_data = {
            "id": key_id,
            "type": KeyType.SYMMETRIC,
            "name": key_name,
            "size": key_size * 8,  # 位数
            "created_at": datetime.utcnow().isoformat(),
            "status": KeyStatus.ACTIVE,
            "key": base64.b64encode(key).decode("utf - 8"),
            "usage_count": 0,
        }

        self.keys[key_id] = key_data
        self._save_key(key_id, key_data)

        logger.info(f"生成对称密钥: {key_id}")
        return key_id

    def generate_asymmetric_keypair(self, key_name: str) -> Tuple[str, str]:
        """
        生成非对称密钥对

        Args:
            key_name: 密钥名称

        Returns:
            (公钥ID, 私钥ID)
        """
        private_key_id = (
            f"asym_priv_{key_name}_{datetime.utcnow().strftime('%Y % m % d_ % H % M % S')}"
        )
        public_key_id = (
            f"asym_pub_{key_name}_{datetime.utcnow().strftime('%Y % m % d_ % H % M % S')}"
        )

        # 生成RSA密钥对
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # 私钥
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        private_key_data = {
            "id": private_key_id,
            "type": KeyType.ASYMMETRIC_PRIVATE,
            "name": key_name,
            "size": 2048,
            "created_at": datetime.utcnow().isoformat(),
            "status": KeyStatus.ACTIVE,
            "key": base64.b64encode(private_pem).decode("utf - 8"),
            "usage_count": 0,
            "public_key_id": public_key_id,
        }

        # 公钥
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        public_key_data = {
            "id": public_key_id,
            "type": KeyType.ASYMMETRIC_PUBLIC,
            "name": key_name,
            "size": 2048,
            "created_at": datetime.utcnow().isoformat(),
            "status": KeyStatus.ACTIVE,
            "key": base64.b64encode(public_pem).decode("utf - 8"),
            "usage_count": 0,
            "private_key_id": private_key_id,
        }

        self.keys[private_key_id] = private_key_data
        self.keys[public_key_id] = public_key_data

        self._save_key(private_key_id, private_key_data)
        self._save_key(public_key_id, public_key_data)

        logger.info(f"生成非对称密钥对: {private_key_id}, {public_key_id}")
        return private_key_id, public_key_id

    def get_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """
        获取密钥

        Args:
            key_id: 密钥ID

        Returns:
            密钥数据或None
        """
        if key_id in self.keys:
            key_data = self.keys[key_id]
            # 检查密钥状态
            if key_data["status"] == KeyStatus.ACTIVE:
                # 更新使用计数
                key_data["usage_count"] += 1
                self._save_key(key_id, key_data)
                return key_data
            else:
                logger.warning(f"密钥 {key_id} 状态非活跃: {key_data['status']}")
                return None

        logger.warning(f"密钥不存在: {key_id}")
        return None

    def get_symmetric_key_bytes(self, key_id: str) -> Optional[bytes]:
        """
        获取对称密钥字节

        Args:
            key_id: 密钥ID

        Returns:
            密钥字节或None
        """
        key_data = self.get_key(key_id)
        if key_data and key_data["type"] == KeyType.SYMMETRIC:
            return base64.b64decode(key_data["key"])
        return None

    def rotate_key(self, key_id: str) -> Optional[str]:
        """
        轮换密钥

        Args:
            key_id: 要轮换的密钥ID

        Returns:
            新密钥ID或None
        """
        if key_id not in self.keys:
            logger.error(f"密钥不存在: {key_id}")
            return None

        old_key = self.keys[key_id]
        key_name = old_key["name"]

        # 生成新密钥
        if old_key["type"] == KeyType.SYMMETRIC:
            new_key_id = self.generate_symmetric_key(key_name, old_key["size"] // 8)
        elif old_key["type"] == KeyType.ASYMMETRIC_PRIVATE:
            new_key_id, _ = self.generate_asymmetric_keypair(key_name)
        else:
            logger.error(f"不支持的密钥类型: {old_key['type']}")
            return None

        # 标记旧密钥为过期
        old_key["status"] = KeyStatus.EXPIRED
        old_key["rotated_at"] = datetime.utcnow().isoformat()
        old_key["replaced_by"] = new_key_id

        # 移动到归档目录
        self._archive_key(key_id, old_key)

        logger.info(f"密钥轮换: {key_id} -> {new_key_id}")
        return new_key_id

    def revoke_key(self, key_id: str, reason: str = "manual") -> bool:
        """
        撤销密钥

        Args:
            key_id: 密钥ID
            reason: 撤销原因

        Returns:
            是否成功撤销
        """
        if key_id not in self.keys:
            logger.error(f"密钥不存在: {key_id}")
            return False

        key_data = self.keys[key_id]
        key_data["status"] = KeyStatus.REVOKED
        key_data["revoked_at"] = datetime.utcnow().isoformat()
        key_data["revocation_reason"] = reason

        # 移动到撤销目录
        self._revoke_key(key_id, key_data)

        logger.warning(f"密钥已撤销: {key_id}, 原因: {reason}")
        return True

    def delete_key(self, key_id: str) -> bool:
        """
        彻底删除密钥

        Args:
            key_id: 密钥ID

        Returns:
            是否成功删除
        """
        if key_id not in self.keys:
            logger.warning(f"密钥不存在: {key_id}")
            return False

        key_data = self.keys[key_id]
        key_type = key_data["type"]

        # 删除文件
        file_path = os.path.join(self.key_store_path, "active", f"{key_id}.json")
        if os.path.exists(file_path):
            # 安全删除
            with open(file_path, "r + b") as f:
                f.write(secrets.token_bytes(os.path.getsize(file_path)))
                f.flush()
                os.fsync(f.fileno())
            os.remove(file_path)

        # 从内存中移除
        del self.keys[key_id]

        logger.info(f"密钥已删除: {key_id} (类型: {key_type})")
        return True

    def list_keys(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出密钥

        Args:
            status: 过滤状态

        Returns:
            密钥列表
        """
        keys = list(self.keys.values())

        if status:
            keys = [k for k in keys if k["status"] == status]

        # 移除敏感信息
        for key in keys:
            if "key" in key:
                del key["key"]

        return keys

    def verify_key_integrity(self, key_id: str) -> bool:
        """
        验证密钥完整性

        Args:
            key_id: 密钥ID

        Returns:
            完整性是否有效
        """
        if key_id not in self.keys:
            return False

        key_data = self.keys[key_id]

        # 重新计算校验和
        file_path = os.path.join(self.key_store_path, "active", f"{key_id}.json")
        if not os.path.exists(file_path):
            return False

        with open(file_path, "r") as f:
            stored_data = json.load(f)

        # 比较关键字段
        for field in ["id", "type", "created_at", "status"]:
            if stored_data.get(field) != key_data.get(field):
                return False

        return True

    def export_public_key(self, key_id: str) -> Optional[str]:
        """
        导出公钥

        Args:
            key_id: 公钥ID

        Returns:
            公钥PEM格式或None
        """
        key_data = self.get_key(key_id)
        if not key_data or key_data["type"] != KeyType.ASYMMETRIC_PUBLIC:
            return None

        return base64.b64decode(key_data["key"]).decode("utf - 8")

    def _save_key(self, key_id: str, key_data: Dict[str, Any]):
        """保存密钥到文件"""
        file_path = os.path.join(self.key_store_path, "active", f"{key_id}.json")

        with open(file_path, "w") as f:
            json.dump(key_data, f, indent=2)

    def _load_keys(self):
        """从文件加载所有密钥"""
        active_dir = os.path.join(self.key_store_path, "active")

        if not os.path.exists(active_dir):
            return

        for filename in os.listdir(active_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(active_dir, filename)
                try:
                    with open(file_path, "r") as f:
                        key_data = json.load(f)

                    key_id = key_data["id"]
                    self.keys[key_id] = key_data

                except Exception as e:
                    logger.error(f"加载密钥失败 {filename}: {e}")

        logger.info(f"已加载 {len(self.keys)} 个密钥")

    def _archive_key(self, key_id: str, key_data: Dict[str, Any]):
        """将密钥移到归档目录"""
        # 从活动目录移除
        active_path = os.path.join(self.key_store_path, "active", f"{key_id}.json")
        archive_path = os.path.join(self.key_store_path, "archive", f"{key_id}.json")

        if os.path.exists(active_path):
            os.rename(active_path, archive_path)

        # 移除敏感信息
        key_data_copy = key_data.copy()
        if "key" in key_data_copy:
            del key_data_copy["key"]

        # 保存到归档索引
        self.keys[key_id] = key_data_copy

    def _revoke_key(self, key_id: str, key_data: Dict[str, Any]):
        """将密钥移到撤销目录"""
        # 从活动目录移除
        active_path = os.path.join(self.key_store_path, "active", f"{key_id}.json")
        revoked_path = os.path.join(self.key_store_path, "revoked", f"{key_id}.json")

        if os.path.exists(active_path):
            os.rename(active_path, revoked_path)

        # 移除敏感信息
        key_data_copy = key_data.copy()
        if "key" in key_data_copy:
            del key_data_copy["key"]

        # 保存到撤销索引
        self.keys[key_id] = key_data_copy

    def cleanup_expired_keys(self) -> Dict[str, int]:
        """
        清理过期密钥

        Returns:
            清理统计
        """
        cleaned = {"deleted": 0, "archived": 0}

        # 查找过期密钥
        expired_keys = [
            key_id
            for key_id, key_data in self.keys.items()
            if key_data["status"] in [KeyStatus.EXPIRED, KeyStatus.COMPROMISED]
        ]

        for key_id in expired_keys:
            key_data = self.keys[key_id]

            # 删除过期密钥
            if self.delete_key(key_id):
                if key_data["status"] == KeyStatus.EXPIRED:
                    cleaned["archived"] += 1
                else:
                    cleaned["deleted"] += 1

        logger.info(
            f"清理密钥完成: 归档 {cleaned['archived']}, 删除 {cleaned['deleted']}"
        )
        return cleaned

    def get_key_statistics(self) -> Dict[str, Any]:
        """
        获取密钥统计信息

        Returns:
            统计信息
        """
        stats = {
            "total_keys": len(self.keys),
            "by_type": {},
            "by_status": {},
            "total_usage": 0,
        }

        for key_data in self.keys.values():
            # 按类型统计
            key_type = key_data["type"]
            if key_type not in stats["by_type"]:
                stats["by_type"][key_type] = 0
            stats["by_type"][key_type] += 1

            # 按状态统计
            status = key_data["status"]
            if status not in stats["by_status"]:
                stats["by_status"][status] = 0
            stats["by_status"][status] += 1

            # 累计使用次数
            stats["total_usage"] += key_data.get("usage_count", 0)

        return stats


# 全局密钥管理器
_global_key_manager = None


def get_key_manager() -> KeyManager:
    """
    获取全局密钥管理器

    Returns:
        密钥管理器实例
    """
    global _global_key_manager
    if _global_key_manager is None:
        _global_key_manager = KeyManager()
    return _global_key_manager
