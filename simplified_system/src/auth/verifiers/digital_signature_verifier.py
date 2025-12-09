#!/usr / bin / env python3
"""
Digital Signature Verifier
数字签名验证器

Task 5: Implement Digital Signature Verifier with RS256 / ES256 support
任务5：实现数字签名验证器，支持RS256 / ES256

Provides cryptographic signature verification for API responses and data
authenticity using industry - standard algorithms.
"""

import asyncio
import base64
import hashlib
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import jwt
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
    from cryptography.x509 import load_pem_x509_certificate

    CRYPTO_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Cryptography libraries not available: {e}")
    CRYPTO_AVAILABLE = False

from ..interfaces.auth_result import AuthResult, Verdict
from ..interfaces.verifier_interface import IVerifier

logger = logging.getLogger(__name__)


class DigitalSignatureVerifier(IVerifier):
    """
    Digital Signature Verifier for cryptographic data authentication
    数字签名验证器，用于密码学数据认证

    Supports:
    - RS256 (RSA Signature with SHA - 256)
    - ES256 (ECDSA using P - 256 and SHA - 256)
    - HS256 (HMAC using SHA - 256)
    """

    def __init__(
        self,
        name: str = "Digital Signature Verifier",
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name, config)

        if not CRYPTO_AVAILABLE:
            raise ImportError(
                "Required cryptography libraries not installed. Install with: pip install cryptography pyjwt"
            )

        self.supported_algorithms = ["RS256", "ES256", "HS256"]
        self.key_store_path = self.config.get("key_store_path", "config / keys/")
        self.trusted_issuers = self.config.get(
            "trusted_issuers",
            ["hkma.gov.hk", "api.hkma.gov.hk", "18.180.162.113"],  # Stock API server
        )

        # Performance settings
        self.max_signature_size = self.config.get("max_signature_size", 8192)  # 8KB max
        self.verification_timeout = self.config.get(
            "verification_timeout", 10.0
        )  # 10 seconds

        # Initialize key store
        self._init_key_store()

        logger.info(
            f"DigitalSignatureVerifier initialized with algorithms: {self.supported_algorithms}"
        )

    def _init_key_store(self):
        """Initialize key storage and load trusted keys"""
        self.trusted_keys = {}
        self.revoked_keys = set()

        try:
            key_store_dir = Path(self.key_store_path)
            key_store_dir.mkdir(parents = True, exist_ok = True)

            # Load trusted public keys
            for key_file in key_store_dir.glob("*.pem"):
                try:
                    key_data = key_file.read_text()
                    self._load_public_key(key_file.stem, key_data)
                    logger.info(f"Loaded trusted key: {key_file.stem}")
                except Exception as e:
                    logger.error(f"Failed to load key {key_file}: {e}")

            # Load revoked keys list
            revoked_file = key_store_dir / "revoked_keys.txt"
            if revoked_file.exists():
                self.revoked_keys = set(revoked_file.read_text().strip().split("\n"))

        except Exception as e:
            logger.error(f"Failed to initialize key store: {e}")

    def _load_public_key(self, key_id: str, key_data: str):
        """Load and parse public key"""
        try:
            # Try to load as PEM certificate first
            if "BEGIN CERTIFICATE" in key_data:
                cert = load_pem_x509_certificate(key_data.encode())
                public_key = cert.public_key()
            else:
                # Load as raw public key
                public_key = serialization.load_pem_public_key(key_data.encode())

            self.trusted_keys[key_id] = public_key

        except Exception as e:
            logger.error(f"Failed to parse public key {key_id}: {e}")
            raise

    async def verify(
        self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
    ) -> AuthResult:
        """
        Verify digital signature of data

        Args:
            data: Data to verify (should include signature)
            data_id: Unique data identifier
            context: Verification context (algorithm, key_id, etc.)

        Returns:
            AuthResult: Verification result
        """
        start_time = time.time()

        result = AuthResult(
            data_id = data_id,
            overall_verdict = Verdict.UNKNOWN,
            overall_confidence = 0.0,
            metadata={"algorithm": "digital_signature", "verifier": self.name},
        )

        try:
            # Extract data and signature
            data_content, signature_info = self._extract_signature_data(data)

            if not signature_info:
                result.overall_verdict = Verdict.SUSPICIOUS
                result.overall_confidence = 0.3
                result.error_message = "No digital signature found in data"
                result.metadata["signature_found"] = False
                return result

            # Get algorithm from context or signature
            algorithm = self._get_algorithm(signature_info, context)
            if not algorithm:
                result.overall_verdict = Verdict.SUSPICIOUS
                result.overall_confidence = 0.2
                result.error_message = "Unsupported or missing signature algorithm"
                return result

            # Verify based on algorithm type
            if algorithm.upper() in ["RS256", "ES256"]:
                verification_result = await self._verify_asymmetric_signature(
                    data_content, signature_info, algorithm, context
                )
            elif algorithm.upper() == "HS256":
                verification_result = await self._verify_hmac_signature(
                    data_content, signature_info, context
                )
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            # Update result with verification outcome
            result.overall_verdict = verification_result["verdict"]
            result.overall_confidence = verification_result["confidence"]
            result.metadata.update(verification_result["metadata"])

            # Log verification attempt for audit
            await self._log_verification_attempt(
                data_id, algorithm, result.overall_verdict
            )

            logger.info(
                f"Digital signature verification completed for {data_id}: {result.overall_verdict.value}"
            )

        except asyncio.TimeoutError:
            result.overall_verdict = Verdict.ERROR
            result.error_message = (
                f"Signature verification timeout after {self.verification_timeout}s"
            )

        except Exception as e:
            result.overall_verdict = Verdict.ERROR
            result.error_message = f"Signature verification failed: {str(e)}"
            logger.error(f"Digital signature verification error for {data_id}: {e}")

        finally:
            result.total_execution_time_ms = (time.time() - start_time) * 1000

        return result

    def _extract_signature_data(self, data: Any) -> Tuple[bytes, Dict[str, Any]]:
        """Extract data content and signature information"""
        if isinstance(data, dict):
            # Handle structured data with signature field
            if "signature" in data:
                data_copy = data.copy()
                signature_info = data_copy.pop("signature")
                data_content = json.dumps(data_copy, sort_keys = True).encode("utf - 8")
                return data_content, signature_info
            elif "digital_signature" in data:
                data_copy = data.copy()
                signature_info = data_copy.pop("digital_signature")
                data_content = json.dumps(data_copy, sort_keys = True).encode("utf - 8")
                return data_content, signature_info

        # Handle raw data
        if isinstance(data, (str, bytes)):
            if isinstance(data, str):
                data_bytes = data.encode("utf - 8")
            else:
                data_bytes = data

            # Look for signature in metadata
            return data_bytes, {}

        # Handle other data types (convert to JSON)
        data_json = json.dumps(data, sort_keys = True, default = str)
        return data_json.encode("utf - 8"), {}

    def _get_algorithm(
        self, signature_info: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Determine signature algorithm"""
        # Priority: signature_info -> context -> default
        if "algorithm" in signature_info:
            return signature_info["algorithm"]
        elif "alg" in signature_info:
            return signature_info["alg"]
        elif context and "algorithm" in context:
            return context["algorithm"]
        elif context and "signature_algorithm" in context:
            return context["signature_algorithm"]

        return None

    async def _verify_asymmetric_signature(
        self,
        data: bytes,
        signature_info: Dict[str, Any],
        algorithm: str,
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Verify RSA or ECDSA signature"""
        try:
            # Get signature value
            if "signature" in signature_info:
                signature_b64 = signature_info["signature"]
            elif "sig" in signature_info:
                signature_b64 = signature_info["sig"]
            else:
                raise ValueError("No signature value found")

            # Decode signature
            signature = base64.b64decode(signature_b64)

            if len(signature) > self.max_signature_size:
                raise ValueError(f"Signature too large: {len(signature)} bytes")

            # Get public key
            key_id = signature_info.get("key_id") or context.get("key_id")
            issuer = signature_info.get("issuer") or context.get("issuer")

            public_key = self._get_public_key(key_id, issuer)
            if not public_key:
                return {
                    "verdict": Verdict.SUSPICIOUS,
                    "confidence": 0.2,
                    "metadata": {
                        "algorithm": algorithm,
                        "error": "No trusted public key found",
                        "key_id": key_id,
                        "issuer": issuer,
                    },
                }

            # Check if key is revoked
            if key_id and key_id in self.revoked_keys:
                return {
                    "verdict": Verdict.FALSIFIED,
                    "confidence": 0.9,
                    "metadata": {
                        "algorithm": algorithm,
                        "error": "Public key has been revoked",
                        "key_id": key_id,
                    },
                }

            # Verify signature based on algorithm
            if algorithm.upper() == "RS256":
                verified = self._verify_rsa_signature(data, signature, public_key)
            elif algorithm.upper() == "ES256":
                verified = self._verify_ecdsa_signature(data, signature, public_key)
            else:
                raise ValueError(f"Unsupported asymmetric algorithm: {algorithm}")

            if verified:
                return {
                    "verdict": Verdict.AUTHENTIC,
                    "confidence": 0.95,
                    "metadata": {
                        "algorithm": algorithm,
                        "key_id": key_id,
                        "issuer": issuer,
                        "signature_size": len(signature),
                        "verification_method": "asymmetric",
                    },
                }
            else:
                return {
                    "verdict": Verdict.FALSIFIED,
                    "confidence": 0.9,
                    "metadata": {
                        "algorithm": algorithm,
                        "key_id": key_id,
                        "issuer": issuer,
                        "error": "Signature verification failed",
                    },
                }

        except Exception as e:
            return {
                "verdict": Verdict.ERROR,
                "confidence": 0.0,
                "metadata": {"algorithm": algorithm, "error": str(e)},
            }

    def _verify_rsa_signature(self, data: bytes, signature: bytes, public_key) -> bool:
        """Verify RSA signature (RS256)"""
        try:
            public_key.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            logger.error(f"RSA signature verification error: {e}")
            return False

    def _verify_ecdsa_signature(
        self, data: bytes, signature: bytes, public_key
    ) -> bool:
        """Verify ECDSA signature (ES256)"""
        try:
            public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            logger.error(f"ECDSA signature verification error: {e}")
            return False

    async def _verify_hmac_signature(
        self,
        data: bytes,
        signature_info: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Verify HMAC signature (HS256)"""
        try:
            # Get signature value
            if "signature" in signature_info:
                signature_b64 = signature_info["signature"]
            elif "sig" in signature_info:
                signature_b64 = signature_info["sig"]
            else:
                raise ValueError("No HMAC signature value found")

            # Get secret key
            key_id = signature_info.get("key_id") or context.get("key_id")
            secret_key = self._get_secret_key(key_id)

            if not secret_key:
                return {
                    "verdict": Verdict.SUSPICIOUS,
                    "confidence": 0.2,
                    "metadata": {
                        "algorithm": "HS256",
                        "error": "No secret key found for HMAC verification",
                        "key_id": key_id,
                    },
                }

            # Compute expected signature
            expected_signature = hashlib.sha256(data + secret_key.encode()).digest()
            provided_signature = base64.b64decode(signature_b64)

            # Constant - time comparison
            if hmac.compare_digest(expected_signature, provided_signature):
                return {
                    "verdict": Verdict.AUTHENTIC,
                    "confidence": 0.85,
                    "metadata": {
                        "algorithm": "HS256",
                        "key_id": key_id,
                        "verification_method": "hmac",
                    },
                }
            else:
                return {
                    "verdict": Verdict.FALSIFIED,
                    "confidence": 0.9,
                    "metadata": {
                        "algorithm": "HS256",
                        "key_id": key_id,
                        "error": "HMAC signature verification failed",
                    },
                }

        except Exception as e:
            return {
                "verdict": Verdict.ERROR,
                "confidence": 0.0,
                "metadata": {"algorithm": "HS256", "error": str(e)},
            }

    def _get_public_key(
        self, key_id: Optional[str], issuer: Optional[str]
    ) -> Optional[Any]:
        """Get trusted public key"""
        if key_id and key_id in self.trusted_keys:
            return self.trusted_keys[key_id]

        # Try to find key by issuer
        if issuer:
            for kid, key in self.trusted_keys.items():
                if issuer in kid or kid in issuer:
                    return key

        return None

    def _get_secret_key(self, key_id: Optional[str]) -> Optional[str]:
        """Get secret key for HMAC verification"""
        # In production, this should retrieve from secure key store
        # For now, use environment variables or config
        if key_id and f"HMAC_KEY_{key_id}" in self.config:
            return self.config[f"HMAC_KEY_{key_id}"]
        elif "default_hmac_key" in self.config:
            return self.config["default_hmac_key"]

        return None

    async def _log_verification_attempt(
        self, data_id: str, algorithm: str, verdict: Verdict
    ):
        """Log verification attempts for audit trail"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "data_id": data_id,
                "verifier": self.name,
                "algorithm": algorithm,
                "verdict": verdict.value,
                "user_agent": "DigitalSignatureVerifier",
            }

            # In production, send to secure audit system
            logger.info(f"Verification audit: {json.dumps(log_entry)}")

        except Exception as e:
            logger.error(f"Failed to log verification attempt: {e}")

    def get_verifier_type(self) -> str:
        """Get verifier type identifier"""
        return "digital_signature"

    def get_supported_data_types(self) -> List[str]:
        """Get supported data types"""
        return [
            "api_response",
            "json_data",
            "financial_data",
            "government_data",
            "stock_data",
            "authenticated_message",
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the verifier"""
        health_status = {
            "verifier": self.name,
            "type": self.get_verifier_type(),
            "enabled": self.enabled,
            "status": "healthy",
            "supported_algorithms": self.supported_algorithms,
            "trusted_keys_count": len(self.trusted_keys),
            "revoked_keys_count": len(self.revoked_keys),
            "crypto_available": CRYPTO_AVAILABLE,
        }

        # Test basic signature generation / verification
        try:
            if CRYPTO_AVAILABLE:
                # Simple self - test
                test_data = b"health_check_test"
                test_key = rsa.generate_private_key(
                    public_exponent = 65537, key_size = 2048
                )

                # Test signing and verification
                signature = test_key.sign(
                    test_data, padding.PKCS1v15(), hashes.SHA256()
                )

                test_key.public_key().verify(
                    signature, test_data, padding.PKCS1v15(), hashes.SHA256()
                )

                health_status["self_test"] = "passed"
            else:
                health_status["self_test"] = "skipped (crypto unavailable)"
                health_status["status"] = "degraded"

        except Exception as e:
            health_status["self_test"] = f"failed: {str(e)}"
            health_status["status"] = "unhealthy"

        return health_status

    async def cleanup(self):
        """Cleanup resources"""
        logger.info(f"Cleaning up {self.name}")
        self.trusted_keys.clear()
        self.revoked_keys.clear()


# Import for HMAC verification
import hmac
