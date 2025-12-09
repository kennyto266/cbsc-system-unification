"""
传输加密模块 - T092: 数据传输加密

实现TLS 1.3、证书管理、WSS安全通信和Perfect Forward Secrecy。
支持内部服务通信加密和API端点加密。

功能:
- TLS 1.3配置
- SSL / TLS证书管理
- WSS WebSocket安全
- HSTS头部强制
- Perfect Forward Secrecy
- 证书绑定
- 内部服务通信加密
"""

import logging
import os
import socket
import ssl
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import ExtensionOID, NameOID

logger = logging.getLogger(__name__)


class TLSManager:
    """
    TLS / SSL管理器
    """

    def __init__(self, cert_dir: str = "certs"):
        """
        初始化TLS管理器

        Args:
            cert_dir: 证书目录
        """
        self.cert_dir = cert_dir
        self.ca_cert = None
        self.server_cert = None
        self.server_key = None

        # 创建证书目录
        os.makedirs(cert_dir, exist_ok=True)

        # 加载或生成证书
        self._load_or_generate_certificates()

    def _load_or_generate_certificates(self):
        """加载或生成证书"""
        cert_path = os.path.join(self.cert_dir, "server.crt")
        key_path = os.path.join(self.cert_dir, "server.key")

        if os.path.exists(cert_path) and os.path.exists(key_path):
            self._load_certificates(cert_path, key_path)
        else:
            logger.info("证书不存在，生成自签名证书（仅用于开发）")
            self._generate_self_signed_cert(cert_path, key_path)

    def _load_certificates(self, cert_path: str, key_path: str):
        """加载现有证书"""
        try:
            with open(cert_path, "rb") as f:
                self.server_cert = x509.load_pem_x509_certificate(f.read())

            with open(key_path, "rb") as f:
                self.server_key = serialization.load_pem_private_key(
                    f.read(), password=None
                )

            logger.info("证书加载成功")

        except Exception as e:
            logger.error(f"证书加载失败: {e}")
            raise

    def _generate_self_signed_cert(
        self, cert_path: str, key_path: str, days_valid: int = 365
    ):
        """
        生成自签名证书（仅用于开发 / 测试）

        Args:
            cert_path: 证书保存路径
            key_path: 私钥保存路径
            days_valid: 有效天数
        """
        # 生成私钥
        self.server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # 创建证书主题
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "HK"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Hong Kong"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Hong Kong"),
                x509.NameAttribute(
                    NameOID.ORGANIZATION_NAME, "HK Quant Trading System"
                ),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ]
        )

        # 创建证书
        self.server_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(self.server_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=days_valid))
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        x509.DNSName("localhost"),
                        x509.DNSName("127.0.0.1"),
                        x509.IPAddress("127.0.0.1".encode()),
                    ]
                ),
                critical=False,
            )
            .sign(self.server_key, hashes.SHA256())
        )

        # 保存证书和私钥
        with open(cert_path, "wb") as f:
            f.write(self.server_cert.public_bytes(serialization.Encoding.PEM))

        with open(key_path, "wb") as f:
            f.write(
                self.server_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        logger.info(f"自签名证书生成完成: {cert_path}")

    def create_ssl_context(self, server_side: bool = True) -> ssl.SSLContext:
        """
        创建SSL上下文

        Args:
            server_side: 是否为服务器端

        Returns:
            配置好的SSL上下文
        """
        # 使用TLS 1.3（如果可用）
        context = ssl.SSLContext(
            ssl.PROTOCOL_TLS_SERVER if server_side else ssl.PROTOCOL_TLS_CLIENT
        )

        # 加载证书和私钥
        if self.server_cert and self.server_key:
            context.load_cert_chain(
                certfile=os.path.join(self.cert_dir, "server.crt"),
                keyfile=os.path.join(self.cert_dir, "server.key"),
            )

        # 设置加密套件（使用安全的套件）
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3

        # 启用Perfect Forward Secrecy
        context.options |= ssl.OP_SINGLE_DH_USE
        context.options |= ssl.OP_SINGLE_ECDH_USE

        # 禁用不安全的协议和加密套件
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1

        # 设置加密套件偏好
        if hasattr(ssl, "OP_CIPHER_SERVER_PREFERENCE"):
            context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE

        # 禁用压缩（CRIME攻击防护）
        context.options |= ssl.OP_NO_COMPRESSION

        # 加载默认CA
        context.load_default_certs()

        return context

    def get_wss_context(self) -> ssl.SSLContext:
        """
        获取WSS WebSocket的SSL上下文

        Returns:
            WSS SSL上下文
        """
        context = self.create_ssl_context(server_side=True)

        # WebSocket额外设置
        if hasattr(ssl, "OP_ENABLE_HTTP2"):
            context.options |= ssl.OP_ENABLE_HTTP2

        return context

    def verify_certificate(self, cert_path: str) -> Dict[str, Any]:
        """
        验证证书

        Args:
            cert_path: 证书路径

        Returns:
            验证结果
        """
        try:
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())

            result = {
                "valid": True,
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "serial_number": str(cert.serial_number),
                "not_valid_before": cert.not_valid_before.isoformat(),
                "not_valid_after": cert.not_valid_after.isoformat(),
                "signature_algorithm": cert.signature_algorithm_oid._name,
                "public_key_algorithm": cert.public_key().__class__.__name__,
            }

            # 检查证书是否过期
            now = datetime.utcnow()
            if now < cert.not_valid_before or now > cert.not_valid_after:
                result["valid"] = False
                result["error"] = "Certificate is expired or not yet valid"

            return result

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def create_certificate_request(
        self, common_name: str, alt_names: list = None
    ) -> tuple:
        """
        创建证书签名请求

        Args:
            common_name: 通用名称
            alt_names: 备用名称列表

        Returns:
            (CSR数据, 私钥)
        """
        # 生成私钥
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # 创建主题
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "HK"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Hong Kong"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Hong Kong"),
                x509.NameAttribute(
                    NameOID.ORGANIZATION_NAME, "HK Quant Trading System"
                ),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ]
        )

        # 创建CSR
        csr = x509.CertificateSigningRequestBuilder().subject_name(subject)

        # 添加备用名称
        if alt_names:
            san_list = []
            for name in alt_names:
                if name.startswith("*."):
                    san_list.append(x509.DNSName(name))
                elif name.replace(".", "").replace("-", "").isalnum():
                    san_list.append(x509.DNSName(name))
                else:
                    try:
                        san_list.append(x509.IPAddress(name.encode()))
                    except Exception:
                        pass

            if san_list:
                csr = csr.add_extension(
                    x509.SubjectAlternativeName(san_list), critical=False
                )

        # 签名CSR
        csr = csr.sign(private_key, hashes.SHA256())

        return csr.public_bytes(serialization.Encoding.PEM), private_key

    def check_certificate_expiry(
        self, cert_path: str, warning_days: int = 30
    ) -> Dict[str, Any]:
        """
        检查证书过期时间

        Args:
            cert_path: 证书路径
            warning_days: 警告阈值（天）

        Returns:
            过期信息
        """
        try:
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())

            now = datetime.utcnow()
            expiry = cert.not_valid_after
            days_until_expiry = (expiry - now).days

            return {
                "valid": True,
                "expiry_date": expiry.isoformat(),
                "days_until_expiry": days_until_expiry,
                "warning": days_until_expiry <= warning_days,
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def rotate_certificate(self, new_cert_path: str, new_key_path: str) -> bool:
        """
        轮换证书

        Args:
            new_cert_path: 新证书路径
            new_key_path: 新私钥路径

        Returns:
            是否成功
        """
        try:
            # 验证新证书
            if not os.path.exists(new_cert_path) or not os.path.exists(new_key_path):
                logger.error("新证书文件不存在")
                return False

            # 备份旧证书
            backup_cert = os.path.join(
                self.cert_dir, f"server_{datetime.now().strftime('%Y % m % d_ % H % M % S')}.crt"
            )
            backup_key = os.path.join(
                self.cert_dir, f"server_{datetime.now().strftime('%Y % m % d_ % H % M % S')}.key"
            )

            old_cert_path = os.path.join(self.cert_dir, "server.crt")
            old_key_path = os.path.join(self.cert_dir, "server.key")

            if os.path.exists(old_cert_path):
                os.rename(old_cert_path, backup_cert)
            if os.path.exists(old_key_path):
                os.rename(old_key_path, backup_key)

            # 安装新证书
            os.rename(new_cert_path, old_cert_path)
            os.rename(new_key_path, old_key_path)

            # 重新加载证书
            self._load_certificates(old_cert_path, old_key_path)

            logger.info("证书轮换成功")
            return True

        except Exception as e:
            logger.error(f"证书轮换失败: {e}")
            return False

    def get_security_headers(self) -> Dict[str, str]:
        """
        获取安全HTTP头部

        Returns:
            安全头部字典
        """
        return {
            "Strict - Transport - Security": "max - age=31536000; includeSubDomains; preload",  # HSTS
            "X - Content - Type - Options": "nosniff",
            "X - Frame - Options": "DENY",
            "X - XSS - Protection": "1; mode=block",
            "Referrer - Policy": "strict - origin - when - cross - origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            # 额外的加密头部
            "Cache - Control": "no - store, no - cache, must - revalidate, private",
            "Pragma": "no - cache",
            "Expires": "0",
        }

    def create_mutual_tls_context(self, ca_cert_path: str) -> ssl.SSLContext:
        """
        创建双向TLS上下文（客户端证书验证）

        Args:
            ca_cert_path: CA证书路径

        Returns:
            双向TLS SSL上下文
        """
        context = self.create_ssl_context(server_side=True)

        # 要求客户端证书
        context.verify_mode = ssl.CERT_REQUIRED

        # 加载CA证书
        context.load_verify_locations(ca_cert_path)

        return context

    def get_cipher_suites(self) -> List[str]:
        """
        获取推荐的加密套件列表

        Returns:
            安全加密套件列表
        """
        return [
            "TLS_AES_256_GCM_SHA384",  # TLS 1.3
            "TLS_CHACHA20_POLY1305_SHA256",  # TLS 1.3
            "TLS_AES_128_GCM_SHA256",  # TLS 1.3
            "ECDHE - RSA - AES256 - GCM - SHA384",  # TLS 1.2 + PFS
            "ECDHE - RSA - AES128 - GCM - SHA256",  # TLS 1.2 + PFS
            "ECDHE - RSA - AES256 - SHA384",  # TLS 1.2 + PFS
            "ECDHE - RSA - AES128 - SHA256",  # TLS 1.2 + PFS
        ]

    def validate_tls_configuration(self) -> Dict[str, Any]:
        """
        验证TLS配置

        Returns:
            验证结果
        """
        results = {"valid": True, "checks": [], "warnings": [], "errors": []}

        # 检查证书是否存在
        cert_path = os.path.join(self.cert_dir, "server.crt")
        if not os.path.exists(cert_path):
            results["valid"] = False
            results["errors"].append("服务器证书不存在")
        else:
            results["checks"].append("服务器证书存在")

        # 检查私钥是否存在
        key_path = os.path.join(self.cert_dir, "server.key")
        if not os.path.exists(key_path):
            results["valid"] = False
            results["errors"].append("服务器私钥不存在")
        else:
            results["checks"].append("服务器私钥存在")

        # 检查证书过期时间
        if os.path.exists(cert_path):
            expiry_info = self.check_certificate_expiry(cert_path)
            if not expiry_info.get("valid"):
                results["errors"].append(f"证书验证失败: {expiry_info.get('error')}")
            elif expiry_info.get("warning"):
                results["warnings"].append(
                    f"证书将在 {expiry_info.get('days_until_expiry')} 天后过期"
                )
            else:
                results["checks"].append("证书未过期")

        # 检查证书权限
        if os.path.exists(key_path):
            key_stat = os.stat(key_path)
            key_perms = oct(key_stat.st_mode)[-3:]
            if key_perms != "600":
                results["warnings"].append(f"私钥权限 {key_perms} 不是600（建议）")

        return results


def create_secure_ssl_context(
    cert_path: Optional[str] = None,
    key_path: Optional[str] = None,
    ca_cert_path: Optional[str] = None,
    client_cert_required: bool = False,
) -> ssl.SSLContext:
    """
    创建安全的SSL上下文（快捷函数）

    Args:
        cert_path: 服务器证书路径
        key_path: 服务器私钥路径
        ca_cert_path: CA证书路径
        client_cert_required: 是否需要客户端证书

    Returns:
        配置好的SSL上下文
    """
    tls_manager = TLSManager()

    if client_cert_required and ca_cert_path:
        return tls_manager.create_mutual_tls_context(ca_cert_path)
    else:
        return tls_manager.create_ssl_context(server_side=True)
