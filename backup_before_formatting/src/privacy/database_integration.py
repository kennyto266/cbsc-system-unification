"""
数据库集成模块

将加密和匿名化功能集成到SQLAlchemy ORM中。
提供加密列类型、自动加密 / 解密和数据验证。

用法示例:
    from src.privacy.database_integration import EncryptedString, EncryptedInteger

    class User(Base):
        __tablename__ = 'users'

        id = Column(Integer, primary_key=True)
        email = Column(EncryptedString(255), nullable=False)
        phone = Column(EncryptedString(20))
        name = Column(String(100))  # 假名化
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, Integer, String, Text, TypeDecorator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .anonymization import get_anonymizer
from .encryption import get_encryption
from .field_encryption import get_field_encryption

logger = logging.getLogger(__name__)

Base = declarative_base()


class EncryptedColumn(TypeDecorator):
    """
    加密列基类
    """

    impl = Text
    cache_ok = True

    def __init__(self, *args, field_name: str = None, encrypt: bool = True, **kwargs):
        """
        初始化加密列

        Args:
            field_name: 字段名（用于配置匹配）
            encrypt: 是否加密
        """
        super().__init__(*args, **kwargs)
        self.field_name = field_name
        self.encrypt = encrypt
        self.encryption = get_encryption()
        self.field_encryption = get_field_encryption()

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        """绑定参数时加密"""
        if value is None or not self.encrypt:
            return value

        if self.field_name:
            # 使用字段级加密
            return self.field_encryption.encrypt_field(self.field_name, value)
        else:
            # 使用全量加密
            return self.encryption.encrypt(str(value))

    def process_result_value(self, value: Any, dialect: Any) -> Optional[str]:
        """结果值时解密"""
        if value is None or not self.encrypt:
            return value

        if self.field_name:
            # 使用字段级加密
            try:
                return self.field_encryption.decrypt_field(self.field_name, value)
            except Exception:
                # 如果解密失败，返回原值
                return value
        else:
            # 使用全量加密
            try:
                return self.encryption.decrypt(str(value))
            except Exception:
                return value

    def copy(self, **kw):
        """复制列"""
        return self.__class__(
            field_name=self.field_name,
            encrypt=self.encrypt,
            length=self.length,
        )


class EncryptedString(EncryptedColumn):
    """加密字符串列"""

    def __init__(self, length: int = 255, **kwargs):
        super().__init__(length=length, **kwargs)


class EncryptedText(EncryptedColumn):
    """加密文本列"""

    impl = Text

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class EncryptedInteger(EncryptedColumn):
    """加密整数列"""

    impl = Integer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None or not self.encrypt:
            return value
        return super().process_bind_param(str(value), dialect)

    def process_result_value(self, value: Any, dialect: Any) -> Optional[int]:
        if value is None or not self.encrypt:
            return value
        decrypted = super().process_result_value(value, dialect)
        try:
            return int(decrypted) if decrypted else None
        except Exception:
            return value


class DatabaseEncryptionManager:
    """
    数据库加密管理器
    """

    def __init__(self, session_factory: sessionmaker):
        """
        初始化数据库加密管理器

        Args:
            session_factory: SQLAlchemy会话工厂
        """
        self.session_factory = session_factory
        self.encryption = get_encryption()
        self.field_encryption = get_field_encryption()
        self.anonymizer = get_anonymizer()

    def encrypt_existing_data(
        self, table_name: str, fields_to_encrypt: List[str]
    ) -> int:
        """
        加密现有数据

        Args:
            table_name: 表名
            fields_to_encrypt: 要加密的字段列表

        Returns:
            加密的记录数
        """
        session: Session = self.session_factory()
        encrypted_count = 0

        try:
            # 获取模型类
            from sqlalchemy import text

            result = session.execute(text(f"SELECT * FROM {table_name}"))

            for row in result:
                # 加密数据
                for field in fields_to_encrypt:
                    if field in row._mapping:
                        encrypted_value = self.field_encryption.encrypt_field(
                            field, row[field]
                        )
                        session.execute(
                            text(
                                f"UPDATE {table_name} SET {field} = :value WHERE id = :id"
                            ),
                            {"value": encrypted_value, "id": row.id},
                        )
                        encrypted_count += 1

            session.commit()
            logger.info(f"已加密 {encrypted_count} 条记录")
            return encrypted_count

        except Exception as e:
            session.rollback()
            logger.error(f"数据加密失败: {e}")
            raise
        finally:
            session.close()

    def create_encrypted_table(self, table_name: str, columns: Dict[str, str]) -> str:
        """
        创建加密表

        Args:
            table_name: 表名
            columns: 列定义 {字段名: 类型}

        Returns:
            SQL创建语句
        """
        from sqlalchemy import create_column

        sql_parts = [f"CREATE TABLE {table_name} ("]
        for field_name, field_type in columns.items():
            # 检查是否需要加密
            if self.field_encryption.field_configs.get(field_name):
                config = self.field_encryption.field_configs[field_name]
                if config.encryption_type.value != "remove":
                    encrypted_type = self.field_encryption.get_encrypted_sql_column(
                        field_name, field_type
                    )
                    sql_parts.append(f"  {encrypted_type},")
            else:
                sql_parts.append(f"  {field_name} {field_type},")

        sql_parts.append(");")
        return "\n".join(sql_parts)

    def validate_encrypted_data(self, table_name: str) -> Dict[str, Any]:
        """
        验证加密数据

        Args:
            table_name: 表名

        Returns:
            验证结果
        """
        from sqlalchemy import text

        session: Session = self.session_factory()
        validation_results = {
            "total_records": 0,
            "valid_encrypted": 0,
            "invalid_encrypted": 0,
            "errors": [],
        }

        try:
            result = session.execute(text(f"SELECT * FROM {table_name}"))
            validation_results["total_records"] = result.rowcount

            for row in result:
                row_dict = dict(row._mapping)
                field_validations = self.field_encryption.validate_encrypted_data(
                    row_dict
                )

                for field, is_valid in field_validations.items():
                    if is_valid:
                        validation_results["valid_encrypted"] += 1
                    else:
                        validation_results["invalid_encrypted"] += 1
                        validation_results["errors"].append(
                            f"字段 {field} 加密验证失败 (记录ID: {row.id})"
                        )

        except Exception as e:
            validation_results["errors"].append(f"验证过程错误: {e}")
        finally:
            session.close()

        return validation_results

    def pseudonymize_table_data(
        self, table_name: str, entity_id_field: str = "id"
    ) -> int:
        """
        假名化表数据

        Args:
            table_name: 表名
            entity_id_field: 实体ID字段

        Returns:
            假名化记录数
        """
        from sqlalchemy import text

        session: Session = self.session_factory()
        pseudonymized_count = 0

        try:
            result = session.execute(text(f"SELECT * FROM {table_name}"))

            for row in result:
                row_dict = dict(row._mapping)
                entity_id = str(row[entity_id_field])

                # 假名化
                pseudonymized = self.anonymizer.pseudonymize(row_dict, entity_id)

                # 更新数据库
                for field, value in pseudonymized.items():
                    if field != entity_id_field:
                        session.execute(
                            text(
                                f"UPDATE {table_name} SET {field} = :value WHERE {entity_id_field} = :id"
                            ),
                            {"value": value, "id": entity_id},
                        )
                        pseudonymized_count += 1

            session.commit()
            logger.info(f"已假名化 {pseudonymized_count} 个字段")
            return pseudonymized_count

        except Exception as e:
            session.rollback()
            logger.error(f"数据假名化失败: {e}")
            raise
        finally:
            session.close()

    def secure_delete_table_data(self, table_name: str, id_field: str = "id") -> int:
        """
        安全删除表数据

        Args:
            table_name: 表名
            id_field: ID字段

        Returns:
            删除记录数
        """
        from sqlalchemy import text

        session: Session = self.session_factory()
        deleted_count = 0

        try:
            # 获取所有记录
            result = session.execute(text(f"SELECT {id_field} FROM {table_name}"))

            for row in result:
                record_id = row[id_field]

                # 安全删除（这里简化为直接删除）
                session.execute(
                    text(f"DELETE FROM {table_name} WHERE {id_field} = :id"),
                    {"id": record_id},
                )
                deleted_count += 1

            session.commit()
            logger.info(f"已安全删除 {deleted_count} 条记录")
            return deleted_count

        except Exception as e:
            session.rollback()
            logger.error(f"安全删除数据失败: {e}")
            raise
        finally:
            session.close()

    def anonymize_for_analytics(self, table_name: str, output_table: str) -> int:
        """
        为分析匿名化数据

        Args:
            table_name: 源表名
            output_table: 输出表名

        Returns:
            匿名化记录数
        """
        from sqlalchemy import text

        session: Session = self.session_factory()
        anonymized_count = 0

        try:
            # 创建输出表
            session.execute(
                text(
                    f"CREATE TABLE {output_table} AS SELECT * FROM {table_name} WHERE 1=0"
                )
            )

            # 获取源数据
            result = session.execute(text(f"SELECT * FROM {table_name}"))

            for row in result:
                row_dict = dict(row._mapping)

                # 匿名化
                anonymized = self.anonymizer.anonymize_for_analytics(
                    row_dict, "analytics"
                )

                # 插入到输出表
                placeholders = ", ".join([f":{k}" for k in anonymized.keys()])
                fields = ", ".join(anonymized.keys())

                session.execute(
                    text(
                        f"INSERT INTO {output_table} ({fields}) VALUES ({placeholders})"
                    ),
                    anonymized,
                )
                anonymized_count += 1

            session.commit()
            logger.info(f"已匿名化 {anonymized_count} 条记录到表 {output_table}")
            return anonymized_count

        except Exception as e:
            session.rollback()
            logger.error(f"数据匿名化失败: {e}")
            raise
        finally:
            session.close()


# 预定义模型示例
class User(Base):
    """用户模型（使用加密列）"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(EncryptedString(255, field_name="email"), nullable=False)
    phone = Column(EncryptedString(20, field_name="phone"))
    name = Column(String(100), nullable=True)  # 假名化处理
    password_hash = Column(String(255), nullable=True)  # 单独处理
    created_at = Column(String(50))


class Trade(Base):
    """交易模型（使用加密列）"""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(EncryptedString(20, field_name="price"), nullable=False)
    transaction_details = Column(EncryptedText(field_name="transaction_details"))
    account_number = Column(EncryptedString(50, field_name="account_number"))
    created_at = Column(String(50))


class Strategy(Base):
    """策略模型（使用加密列）"""

    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parameters = Column(EncryptedText(field_name="secret_parameters"))
    api_keys = Column(EncryptedText(field_name="api_keys"))
    created_at = Column(String(50))


def setup_encrypted_database(engine, create_tables: bool = True):
    """
    设置加密数据库

    Args:
        engine: SQLAlchemy引擎
        create_tables: 是否创建表
    """
    if create_tables:
        Base.metadata.create_all(engine)

    # 创建会话工厂
    session_factory = sessionmaker(bind=engine)
    return session_factory


def get_encrypted_session(session_factory) -> Session:
    """
    获取加密会话

    Args:
        session_factory: 会话工厂

    Returns:
        数据库会话
    """
    return session_factory()
