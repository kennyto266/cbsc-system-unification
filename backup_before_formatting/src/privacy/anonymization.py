"""
数据匿名化模块 - T094: 数据匿名化和假名化

实现数据脱敏、假名化、k - 匿名性和差分隐私功能。
支持GDPR、PDPA合规性要求。

功能:
- 数据掩码 (姓名、电话、邮箱、ID等)
- 假名化处理
- 数据泛化 (年龄范围、收入区间)
- k - 匿名性实现
- 差分隐私
- 合成数据生成

用法示例:
    anonymizer = DataAnonymizer()

    # 掩码个人信息
    user = {'name': 'John Doe', 'phone': '1234567890', 'email': 'john@example.com'}
    masked = anonymizer.mask_pii(user)

    # 假名化
    pseudonymized = anonymizer.pseudonymize(user, 'user_id_123')

    # 泛化年龄
    generalized = anonymizer.generalize_age({'age': 35}, k=10)
"""

import hashlib
import logging
import random
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


class AnonymizationType(Enum):
    """匿名化类型"""

    MASK = "mask"  # 掩码
    PSEUDONYM = "pseudonym"  # 假名
    GENERALIZE = "generalize"  # 泛化
    REMOVE = "remove"  # 删除
    SHUFFLE = "shuffle"  # 洗牌
    NOISE = "noise"  # 添加噪声


@dataclass
class PIIField:
    """PII字段配置"""

    field_name: str
    field_type: str  # name, email, phone, id, address, etc.
    anonymization_type: AnonymizationType
    keep_pattern: str = ""  # 保留模式（如邮箱的域名部分）
    generalization_bins: Optional[int] = None  # 泛化区间数


class DataAnonymizer:
    """
    数据匿名化核心类
    """

    def __init__(self, seed: Optional[int] = None):
        """
        初始化数据匿名化器

        Args:
            seed: 随机种子（确保结果可重现）
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.pii_fields = self._init_pii_fields()
        self.pseudonym_map: Dict[str, str] = {}
        self._init_pseudonym_map()

    def _init_pii_fields(self) -> List[PIIField]:
        """初始化PII字段配置"""
        return [
            PIIField("name", "name", AnonymizationType.MASK),
            PIIField("full_name", "name", AnonymizationType.MASK),
            PIIField("first_name", "name", AnonymizationType.MASK),
            PIIField("last_name", "name", AnonymizationType.MASK),
            PIIField("email", "email", AnonymizationType.PSEUDONYM, keep_pattern="@"),
            PIIField(
                "email_address", "email", AnonymizationType.PSEUDONYM, keep_pattern="@"
            ),
            PIIField("phone", "phone", AnonymizationType.MASK),
            PIIField("phone_number", "phone", AnonymizationType.MASK),
            PIIField("mobile", "phone", AnonymizationType.MASK),
            PIIField("id_number", "id", AnonymizationType.MASK),
            PIIField("passport_number", "id", AnonymizationType.MASK),
            PIIField("id_card", "id", AnonymizationType.MASK),
            PIIField("ssn", "id", AnonymizationType.MASK),
            PIIField("address", "address", AnonymizationType.GENERALIZE),
            PIIField("street_address", "address", AnonymizationType.GENERALIZE),
            PIIField("city", "address", AnonymizationType.GENERALIZE),
            PIIField("postal_code", "address", AnonymizationType.GENERALIZE),
            PIIField(
                "age", "numeric", AnonymizationType.GENERALIZE, generalization_bins=10
            ),
            PIIField(
                "birth_date",
                "date",
                AnonymizationType.GENERALIZE,
                generalization_bins=12,
            ),
            PIIField(
                "income", "numeric", AnonymizationType.GENERALIZE, generalization_bins=5
            ),
            PIIField("account_number", "financial", AnonymizationType.MASK),
            PIIField("credit_card", "financial", AnonymizationType.MASK),
            PIIField("bank_account", "financial", AnonymizationType.MASK),
        ]

    def _init_pseudonym_map(self):
        """初始化假名映射"""
        # 常用姓名列表
        self.first_names = [
            "John",
            "Jane",
            "Michael",
            "Emily",
            "David",
            "Sarah",
            "Robert",
            "Lisa",
            "William",
            "Jennifer",
            "James",
            "Jessica",
            "Richard",
            "Ashley",
            "Joseph",
            "Amanda",
            "Thomas",
            "Melissa",
            "Charles",
            "Dorothy",
        ]

        self.last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
            "Rodriguez",
            "Martinez",
            "Hernandez",
            "Lopez",
            "Gonzalez",
            "Wilson",
            "Anderson",
            "Thomas",
            "Taylor",
            "Moore",
            "Jackson",
            "Martin",
        ]

    def mask_pii(
        self, data: Dict[str, Any], fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        掩码PII数据

        Args:
            data: 原始数据字典
            fields: 指定要掩码的字段（None表示使用所有PII字段）

        Returns:
            掩码后的数据字典
        """
        result = data.copy()

        # 如果没有指定字段，使用默认PII字段
        if fields is None:
            fields = [field.field_name for field in self.pii_fields]

        for field_name in fields:
            if field_name in result and result[field_name] is not None:
                result[field_name] = self._mask_field(field_name, result[field_name])

        return result

    def _mask_field(self, field_name: str, value: Any) -> str:
        """
        掩码单个字段

        Args:
            field_name: 字段名
            value: 原始值

        Returns:
            掩码后的值
        """
        if value is None:
            return value

        str_value = str(value)

        # 查找匹配的PII字段配置
        pii_config = next(
            (f for f in self.pii_fields if f.field_name == field_name), None
        )

        if not pii_config:
            return str_value

        if pii_config.field_type == "name":
            return self._mask_name(str_value)
        elif pii_config.field_type == "email":
            return self._mask_email(str_value)
        elif pii_config.field_type == "phone":
            return self._mask_phone(str_value)
        elif pii_config.field_type == "id":
            return self._mask_id(str_value)
        elif pii_config.field_type == "address":
            return self._mask_address(str_value)
        elif pii_config.field_type == "financial":
            return self._mask_financial(str_value)
        elif pii_config.field_type == "numeric":
            return self._mask_numeric(str_value, pii_config)
        else:
            return self._general_mask(str_value)

    def _mask_name(self, name: str) -> str:
        """掩码姓名"""
        parts = name.split()
        if len(parts) >= 2:
            # 保留首字母，其他用点替代
            masked = []
            for part in parts:
                if part:
                    masked.append(part[0] + ".")
            return " ".join(masked)
        elif len(name) > 0:
            return name[0] + "."
        return name

    def _mask_email(self, email: str) -> str:
        """掩码邮箱"""
        if "@" not in email:
            return self._general_mask(email)

        username, domain = email.split("@", 1)
        if len(username) <= 1:
            username_masked = "*"
        else:
            username_masked = username[0] + "*" * (len(username) - 1)

        return f"{username_masked}@{domain}"

    def _mask_phone(self, phone: str) -> str:
        """掩码电话号码"""
        # 提取所有数字
        digits = re.sub(r"\D", "", phone)

        if len(digits) <= 4:
            return "*" * len(digits)

        # 保留最后4位，前面全部掩码
        masked = "*" * (len(digits) - 4) + digits[-4:]

        # 尝试保持原始格式
        result = ""
        digit_idx = 0
        for char in phone:
            if char.isdigit():
                if digit_idx < len(masked):
                    result += masked[digit_idx]
                    digit_idx += 1
                else:
                    result += char
            else:
                result += char

        return result

    def _mask_id(self, id_number: str) -> str:
        """掩码ID号"""
        if len(id_number) <= 4:
            return "*" * len(id_number)
        return "****-****-" + id_number[-4:]

    def _mask_address(self, address: str) -> str:
        """掩码地址"""
        # 简化处理，只保留城市信息
        parts = address.split(",")
        if len(parts) >= 2:
            # 保留最后两部分（通常是城市和邮编）
            return ", ".join(parts[-2:])
        return "****"

    def _mask_financial(self, value: str) -> str:
        """掩码金融信息"""
        if len(value) <= 4:
            return "*" * len(value)
        return "*" * (len(value) - 4) + value[-4:]

    def _mask_numeric(self, value: str, config: PIIField) -> str:
        """掩码数值"""
        try:
            num = float(value)
            # 泛化为区间
            return self.generalize_numeric(num, config)
        except Exception:
            return self._general_mask(value)

    def _general_mask(self, value: str) -> str:
        """通用掩码"""
        if len(value) <= 2:
            return "*" * len(value)
        return value[:2] + "*" * (len(value) - 2)

    def pseudonymize(self, data: Dict[str, Any], entity_id: str) -> Dict[str, Any]:
        """
        假名化数据

        Args:
            data: 原始数据字典
            entity_id: 实体ID（用于一致性假名化）

        Returns:
            假名化后的数据字典
        """
        result = data.copy()

        # 生成确定性假名
        entity_hash = hashlib.sha256(entity_id.encode()).hexdigest()

        for field_name, value in data.items():
            if value is not None and field_name != "id":
                result[field_name] = self._pseudonymize_field(
                    field_name, str(value), entity_hash
                )

        return result

    def _pseudonymize_field(self, field_name: str, value: str, entity_hash: str) -> str:
        """
        假名化单个字段

        Args:
            field_name: 字段名
            value: 原始值
            entity_hash: 实体哈希

        Returns:
            假名化后的值
        """
        # 查找PII字段配置
        pii_config = next(
            (f for f in self.pii_fields if f.field_name == field_name), None
        )

        if not pii_config:
            return value

        if pii_config.field_type == "name":
            return self._pseudonymize_name(value, entity_hash)
        elif pii_config.field_type == "email":
            return self._pseudonymize_email(value, entity_hash)
        elif pii_config.field_type == "phone":
            return self._pseudonymize_phone(value, entity_hash)
        else:
            # 其他字段使用哈希伪名
            return f"pseudo_{entity_hash[:8]}"

    def _pseudonymize_name(self, name: str, entity_hash: str) -> str:
        """假名化姓名"""
        # 基于哈希选择姓名
        idx = int(entity_hash[:8], 16) % len(self.first_names)
        first_name = self.first_names[idx]

        idx = int(entity_hash[8:16], 16) % len(self.last_names)
        last_name = self.last_names[idx]

        return f"{first_name} {last_name}"

    def _pseudonymize_email(self, email: str, entity_hash: str) -> str:
        """假名化邮箱"""
        # 保留域名，替换用户名
        if "@" in email:
            domain = email.split("@")[1]
            return f"user_{entity_hash[:8]}@{domain}"
        return f"user_{entity_hash[:8]}@example.com"

    def _pseudonymize_phone(self, phone: str, entity_hash: str) -> str:
        """假名化电话号码"""
        # 保留区号，替换号码
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 10:
            # 使用哈希生成新号码（保留格式）
            pseudo_digits = str(int(entity_hash[:8], 16) % 100000000).zfill(8)
            return phone[:-8] + pseudo_digits if len(phone) > 8 else pseudo_digits
        return f"+****{entity_hash[:4]}"

    def generalize_age(self, data: Dict[str, Any], k: int = 10) -> Dict[str, Any]:
        """
        泛化年龄数据

        Args:
            data: 包含年龄的数据字典
            k: k - 匿名性参数

        Returns:
            泛化后的数据
        """
        result = data.copy()

        if "age" in result and result["age"] is not None:
            try:
                age = int(result["age"])
                # 将年龄泛化为区间
                bin_size = max(1, 100 // k)
                lower_bound = (age // bin_size) * bin_size
                upper_bound = lower_bound + bin_size - 1
                result["age"] = f"{lower_bound}-{upper_bound}"
            except (ValueError, TypeError):
                pass

        return result

    def generalize_numeric(self, value: float, bins: int = 5) -> str:
        """
        泛化数值数据

        Args:
            value: 数值
            bins: 区间数

        Returns:
            泛化后的区间字符串
        """
        # 简化实现，根据区间数量划分范围
        bin_size = 100 / bins
        bin_idx = min(int(value / bin_size), bins - 1)
        lower = bin_idx * bin_size
        upper = (bin_idx + 1) * bin_size

        return f"{lower:.0f}-{upper:.0f}"

    def add_differential_privacy(
        self, numeric_data: List[float], epsilon: float = 1.0
    ) -> List[float]:
        """
        添加差分隐私噪声

        Args:
            numeric_data: 数值数据列表
            epsilon: 隐私预算（越小越隐私）

        Returns:
            添加噪声后的数据
        """
        # 使用拉普拉斯机制添加噪声
        noise_data = []

        for value in numeric_data:
            # 计算敏感度（简化：使用最大值）
            sensitivity = max(numeric_data) if numeric_data else 1.0

            # 拉普拉斯噪声参数
            scale = sensitivity / epsilon

            # 生成拉普拉斯噪声
            u = random.random() - 0.5
            noise = -scale * np.sign(u) * np.log(1 - 2 * abs(u))

            noise_data.append(value + noise)

        return noise_data

    def remove_direct_identifiers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        移除直接标识符

        Args:
            data: 原始数据字典

        Returns:
            移除直接标识符后的数据
        """
        direct_identifiers = [
            "name",
            "full_name",
            "email",
            "phone",
            "phone_number",
            "id_number",
            "passport_number",
            "ssn",
            "address",
            "account_number",
        ]

        result = {k: v for k, v in data.items() if k not in direct_identifiers}
        return result

    def generate_synthetic_data(
        self, schema: Dict[str, str], count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        生成合成数据

        Args:
            schema: 数据模式定义 {字段名: 类型}
            count: 生成数量

        Returns:
            合成数据列表
        """
        synthetic_data = []

        for _ in range(count):
            record = {}
            for field_name, field_type in schema.items():
                if field_type == "name":
                    first = random.choice(self.first_names)
                    last = random.choice(self.last_names)
                    record[field_name] = f"{first} {last}"
                elif field_type == "email":
                    first = random.choice(self.first_names).lower()
                    last = random.choice(self.last_names).lower()
                    domain = random.choice(["example.com", "test.com", "demo.org"])
                    record[field_name] = f"{first}.{last}@{domain}"
                elif field_type == "phone":
                    record[field_name] = f"+852{random.randint(10000000, 99999999)}"
                elif field_type == "age":
                    record[field_name] = random.randint(18, 80)
                elif field_type == "numeric":
                    record[field_name] = random.uniform(0, 1000)
                else:
                    record[field_name] = f"{field_type}_{random.randint(1000, 9999)}"

            synthetic_data.append(record)

        return synthetic_data

    def validate_k_anonymity(
        self, data: List[Dict[str, Any]], quasi_identifiers: List[str], k: int = 5
    ) -> Dict[str, Any]:
        """
        验证k - 匿名性

        Args:
            data: 数据列表
            quasi_identifiers: 准标识符列表
            k: k值

        Returns:
            k - 匿名性验证结果
        """
        if not data or not quasi_identifiers:
            return {"valid": False, "min_group_size": 0, "violations": []}

        # 计算准标识符组合的频率
        groups = {}
        for record in data:
            key = tuple(record.get(qi, "NULL") for qi in quasi_identifiers)
            groups[key] = groups.get(key, 0) + 1

        min_group_size = min(groups.values()) if groups else 0
        violations = [key for key, count in groups.items() if count < k]

        return {
            "valid": min_group_size >= k,
            "min_group_size": min_group_size,
            "violations": violations,
            "total_groups": len(groups),
        }

    def anonymize_for_analytics(
        self, data: Dict[str, Any], purpose: str = "analytics"
    ) -> Dict[str, Any]:
        """
        为分析目的匿名化数据

        Args:
            data: 原始数据
            purpose: 分析目的

        Returns:
            匿名化后的数据
        """
        result = data.copy()

        if purpose == "analytics":
            # 移除直接标识符
            result = self.remove_direct_identifiers(result)

            # 泛化敏感数值
            if "age" in result:
                result = self.generalize_age(result)

            # 泛化收入
            if "income" in result:
                result["income"] = self.generalize_numeric(result.get("income", 0))

        elif purpose == "research":
            # 研究用途：更严格的匿名化
            result = self.mask_pii(result)
            result = self.remove_direct_identifiers(result)

        elif purpose == "marketing":
            # 营销用途：部分匿名化
            result = self.pseudonymize(result, str(data.get("id", "unknown")))

        return result


# 全局匿名化实例
_global_anonymizer = None


def get_anonymizer() -> DataAnonymizer:
    """
    获取全局匿名化实例

    Returns:
        数据匿名化器实例
    """
    global _global_anonymizer
    if _global_anonymizer is None:
        _global_anonymizer = DataAnonymizer()
    return _global_anonymizer
