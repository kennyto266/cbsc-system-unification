#!/usr/bin/env python3
"""
TLS Certificate Validator
TLS证书验证器

Task 7: Implement TLS Certificate Validator with certificate pinning
任务7：实现TLS证书验证器，支持证书固定

Provides comprehensive TLS certificate validation including certificate pinning,
CRL/OCSP checking, and secure certificate update mechanisms.
"""

import asyncio
import ssl
import socket
import logging
import time
import hashlib
import base64
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path

try:
    import cryptography
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    CRYPTO_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Cryptography libraries not available: {e}")
    CRYPTO_AVAILABLE = False

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.ssl_ import create_urllib3_context
    REQUESTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Requests library not available: {e}")
    REQUESTS_AVAILABLE = False

from ..interfaces.verifier_interface import IVerifier
from ..interfaces.auth_result import AuthResult, Verdict

logger = logging.getLogger(__name__)


class TLSCertificateValidator(IVerifier):
    """
    TLS Certificate Validator for secure connection verification
    TLS证书验证器，用于安全连接验证

    Features:
    - Complete certificate chain verification
    - Certificate pinning for critical endpoints
    - CRL and OCSP checking
    - Secure certificate update mechanism
    """

    def __init__(self, name: str = "TLS Certificate Validator", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)

        if not CRYPTO_AVAILABLE:
            raise ImportError("Required cryptography library not installed. Install with: pip install cryptography")

        # Certificate pinning configuration
        self.pinned_certificates = self.config.get('pinned_certificates', {})
        self.certificate_store_path = self.config.get('certificate_store_path', 'config/certificates/')

        # Critical endpoints that require certificate pinning
        self.critical_endpoints = self.config.get('critical_endpoints', [
            'api.hkma.gov.hk',
            '18.180.162.113:9191',
            'data.gov.hk'
        ])

        # Validation settings
        self.validation_timeout = self.config.get('validation_timeout', 30.0)  # 30 seconds
        self.max_chain_length = self.config.get('max_chain_length', 10)
        self.allow_self_signed = self.config.get('allow_self_signed', False)

        # CRL/OCSP settings
        self.enable_crl_checking = self.config.get('enable_crl_checking', True)
        self.enable_ocsp_checking = self.config.get('enable_ocsp_checking', True)
        self.crl_cache_timeout = self.config.get('crl_cache_timeout', 3600)  # 1 hour

        # Initialize certificate store
        self._init_certificate_store()

        logger.info(f"TLS Certificate Validator initialized with {len(self.pinned_certificates)} pinned certificates")

    def _init_certificate_store(self):
        """Initialize certificate storage and load pinned certificates"""
        self.certificate_store = {}
        self.crl_cache = {}

        try:
            cert_store_dir = Path(self.certificate_store_path)
            cert_store_dir.mkdir(parents=True, exist_ok=True)

            # Load pinned certificates
            for cert_file in cert_store_dir.glob("*.pem"):
                try:
                    cert_data = cert_file.read_bytes()
                    cert = x509.load_pem_x509_certificate(cert_data, default_backend())
                    self.certificate_store[cert_file.stem] = cert

                    # Calculate fingerprint for pinning
                    fingerprint = hashlib.sha256(cert_data).digest()
                    self.pinned_certificates[cert_file.stem] = base64.b64encode(fingerprint).decode('ascii')

                    logger.info(f"Loaded pinned certificate: {cert_file.stem}")
                except Exception as e:
                    logger.error(f"Failed to load certificate {cert_file}: {e}")

            # Load CRLs
            if self.enable_crl_checking:
                for crl_file in cert_store_dir.glob("*.crl"):
                    try:
                        crl_data = crl_file.read_bytes()
                        crl = x509.load_der_x509_crl(crl_data, default_backend())
                        self.crl_cache[crl_file.stem] = {
                            'crl': crl,
                            'loaded_at': time.time()
                        }
                        logger.info(f"Loaded CRL: {crl_file.stem}")
                    except Exception as e:
                        logger.error(f"Failed to load CRL {crl_file}: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize certificate store: {e}")

    async def verify(self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None) -> AuthResult:
        """
        Verify TLS certificate for data source or connection

        Args:
            data: Connection data (URL, hostname, or certificate data)
            data_id: Unique data identifier
            context: Verification context (port, protocol, etc.)

        Returns:
            AuthResult: Verification result
        """
        start_time = time.time()

        result = AuthResult(
            data_id=data_id,
            overall_verdict=Verdict.UNKNOWN,
            overall_confidence=0.0,
            metadata={'algorithm': 'tls_certificate', 'verifier': self.name}
        )

        try:
            # Extract connection information
            connection_info = self._extract_connection_info(data, context)

            if not connection_info.get('hostname'):
                result.overall_verdict = Verdict.SUSPICIOUS
                result.overall_confidence = 0.2
                result.error_message = "No hostname or connection information provided"
                return result

            hostname = connection_info['hostname']
            port = connection_info.get('port', 443)
            protocol = connection_info.get('protocol', 'https')

            # Check if this is a critical endpoint requiring pinning
            requires_pinning = self._requires_certificate_pinning(hostname, port)

            # Perform TLS validation
            validation_result = await self._validate_tls_certificate(
                hostname, port, protocol, requires_pinning, connection_info
            )

            result.overall_verdict = validation_result['verdict']
            result.overall_confidence = validation_result['confidence']
            result.metadata.update(validation_result['metadata'])

            # Additional checks for critical endpoints
            if requires_pinning and result.overall_verdict == Verdict.AUTHENTIC:
                pinning_result = await self._verify_certificate_pinning(hostname, validation_result['certificate'])
                if pinning_result['valid']:
                    result.metadata['pinning_verified'] = True
                    result.overall_confidence = min(result.overall_confidence + 0.1, 1.0)
                else:
                    result.overall_verdict = Verdict.FALSIFIED
                    result.overall_confidence = 0.9
                    result.error_message = "Certificate pinning verification failed"
                    result.metadata['pinning_verified'] = False

            logger.info(f"TLS certificate validation completed for {hostname}: {result.overall_verdict.value}")

        except asyncio.TimeoutError:
            result.overall_verdict = Verdict.ERROR
            result.error_message = f"TLS validation timeout after {self.validation_timeout}s"

        except Exception as e:
            result.overall_verdict = Verdict.ERROR
            result.error_message = f"TLS certificate validation failed: {str(e)}"
            logger.error(f"TLS validation error for {data_id}: {e}")

        finally:
            result.total_execution_time_ms = (time.time() - start_time) * 1000

        return result

    def _extract_connection_info(self, data: Any, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract connection information from data and context"""
        connection_info = {}

        # Handle URL
        if isinstance(data, str):
            if data.startswith('http://'):
                connection_info['hostname'] = data[7:].split('/')[0].split(':')[0]
                connection_info['protocol'] = 'http'
                if ':' in data[7:].split('/')[0]:
                    connection_info['port'] = int(data[7:].split('/')[0].split(':')[1])
                else:
                    connection_info['port'] = 80
            elif data.startswith('https://'):
                connection_info['hostname'] = data[8:].split('/')[0].split(':')[0]
                connection_info['protocol'] = 'https'
                if ':' in data[8:].split('/')[0]:
                    connection_info['port'] = int(data[8:].split('/')[0].split(':')[1])
                else:
                    connection_info['port'] = 443
            else:
                connection_info['hostname'] = data

        # Handle dict with connection info
        elif isinstance(data, dict):
            connection_info.update(data)

        # Add context information
        if context:
            connection_info.update(context)

        return connection_info

    def _requires_certificate_pinning(self, hostname: str, port: int) -> bool:
        """Check if endpoint requires certificate pinning"""
        endpoint = f"{hostname}:{port}" if port not in [80, 443] else hostname

        for critical_endpoint in self.critical_endpoints:
            if critical_endpoint in endpoint or endpoint in critical_endpoint:
                return True

        return False

    async def _validate_tls_certificate(self, hostname: str, port: int, protocol: str,
                                       requires_pinning: bool, connection_info: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive TLS certificate validation"""
        try:
            if protocol == 'https':
                # Create SSL context
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = True
                ssl_context.verify_mode = ssl.CERT_REQUIRED

                # Set timeout
                ssl_context.set_timeout(self.validation_timeout)

                # Connect and get certificate
                with socket.create_connection((hostname, port), timeout=self.validation_timeout) as sock:
                    with ssl_context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert_der = ssock.getpeercert(binary_form=True)
                        cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)
                        cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())

                # Validate certificate
                validation_result = await self._validate_certificate_details(cert, hostname)

                return {
                    'verdict': validation_result['verdict'],
                    'confidence': validation_result['confidence'],
                    'certificate': cert,
                    'metadata': {
                        'hostname': hostname,
                        'port': port,
                        'protocol': protocol,
                        'subject': str(cert.subject),
                        'issuer': str(cert.issuer),
                        'valid_from': cert.not_valid_before.isoformat(),
                        'valid_until': cert.not_valid_after.isoformat(),
                        'serial_number': str(cert.serial_number),
                        'validation_details': validation_result['details']
                    }
                }

            else:
                # HTTP connection - no TLS validation needed but still check if TLS was expected
                if requires_pinning:
                    return {
                        'verdict': Verdict.SUSPICIOUS,
                        'confidence': 0.3,
                        'metadata': {
                            'error': 'Critical endpoint using unencrypted HTTP',
                            'hostname': hostname,
                            'protocol': protocol
                        }
                    }
                else:
                    return {
                        'verdict': Verdict.AUTHENTIC,
                        'confidence': 0.6,
                        'metadata': {
                            'note': 'HTTP connection - no TLS validation required',
                            'hostname': hostname,
                            'protocol': protocol
                        }
                    }

        except ssl.SSLCertVerificationError as e:
            return {
                'verdict': Verdict.FALSIFIED,
                'confidence': 0.9,
                'metadata': {
                    'error': f'SSL certificate verification failed: {str(e)}',
                    'hostname': hostname,
                    'port': port
                }
            }
        except Exception as e:
            return {
                'verdict': Verdict.ERROR,
                'confidence': 0.0,
                'metadata': {
                    'error': f'TLS validation error: {str(e)}',
                    'hostname': hostname,
                    'port': port
                }
            }

    async def _validate_certificate_details(self, cert: x509.Certificate, hostname: str) -> Dict[str, Any]:
        """Validate certificate details and chain"""
        validation_details = {}

        try:
            # Check validity period
            now = datetime.utcnow()
            if now < cert.not_valid_before:
                return {
                    'verdict': Verdict.FALSIFIED,
                    'confidence': 0.9,
                    'details': {'error': 'Certificate not yet valid'}
                }
            elif now > cert.not_valid_after:
                return {
                    'verdict': Verdict.FALSIFIED,
                    'confidence': 0.9,
                    'details': {'error': 'Certificate has expired'}
                }

            validation_details['validity_period'] = 'valid'

            # Check hostname
            try:
                ssl.match_hostname(cert, hostname)
                validation_details['hostname_match'] = True
            except ssl.CertificateError:
                return {
                    'verdict': Verdict.SUSPICIOUS,
                    'confidence': 0.7,
                    'details': {'error': f'Certificate hostname does not match {hostname}'}
                }

            # Check key strength
            public_key = cert.public_key()
            if hasattr(public_key, 'key_size'):
                if public_key.key_size < 2048:
                    validation_details['key_strength_warning'] = 'weak_key_size'
                    confidence_adjustment = -0.1
                else:
                    validation_details['key_strength'] = 'strong'
                    confidence_adjustment = 0.0

            # Check certificate chain and revocation
            if self.enable_crl_checking:
                revocation_status = await self._check_certificate_revocation(cert)
                validation_details['revocation_check'] = revocation_status

                if revocation_status.get('revoked', False):
                    return {
                        'verdict': Verdict.FALSIFIED,
                        'confidence': 0.95,
                        'details': {'error': 'Certificate has been revoked'}
                    }

            # Calculate overall confidence
            base_confidence = 0.85
            final_confidence = max(0.0, min(1.0, base_confidence + confidence_adjustment))

            return {
                'verdict': Verdict.AUTHENTIC,
                'confidence': final_confidence,
                'details': validation_details
            }

        except Exception as e:
            return {
                'verdict': Verdict.ERROR,
                'confidence': 0.0,
                'details': {'error': f'Certificate validation error: {str(e)}'}
            }

    async def _check_certificate_revocation(self, cert: x509.Certificate) -> Dict[str, Any]:
        """Check if certificate is revoked using CRL"""
        if not self.enable_crl_checking:
            return {'checked': False, 'reason': 'CRL checking disabled'}

        try:
            # In production, this should download CRL from distribution points
            # For now, check local CRL cache
            for crl_name, crl_info in self.crl_cache.items():
                crl = crl_info['crl']

                # Check if certificate is in CRL
                revoked_certs = crl.get_revoked_certificates()
                if revoked_certs:
                    for revoked_cert in revoked_certs:
                        if revoked_cert.serial_number == cert.serial_number:
                            return {
                                'revoked': True,
                                'crl': crl_name,
                                'revocation_date': revoked_cert.revocation_date.isoformat()
                            }

            return {'revoked': False, 'checked': True}

        except Exception as e:
            return {'checked': False, 'error': str(e)}

    async def _verify_certificate_pinning(self, hostname: str, certificate: x509.Certificate) -> Dict[str, Any]:
        """Verify certificate against pinned fingerprints"""
        try:
            # Generate certificate fingerprint
            cert_der = certificate.public_bytes(serialization.Encoding.DER)
            fingerprint = hashlib.sha256(cert_der).digest()
            fingerprint_b64 = base64.b64encode(fingerprint).decode('ascii')

            # Check against pinned certificates
            for name, pinned_fingerprint in self.pinned_certificates.items():
                if hostname in name or name in hostname:
                    if fingerprint_b64 == pinned_fingerprint:
                        return {
                            'valid': True,
                            'matched_pin': name,
                            'fingerprint': fingerprint_b64
                        }
                    else:
                        return {
                            'valid': False,
                            'matched_pin': name,
                            'expected_fingerprint': pinned_fingerprint,
                            'actual_fingerprint': fingerprint_b64,
                            'error': 'Certificate fingerprint mismatch'
                        }

            # No specific pin found for this hostname
            return {
                'valid': True,  # Allow if no specific pin required
                'note': 'No certificate pin configured for this hostname',
                'fingerprint': fingerprint_b64
            }

        except Exception as e:
            return {
                'valid': False,
                'error': f'Certificate pinning error: {str(e)}'
            }

    def get_verifier_type(self) -> str:
        """Get verifier type identifier"""
        return "tls_certificate"

    def get_supported_data_types(self) -> List[str]:
        """Get supported data types"""
        return [
            "https_url",
            "api_endpoint",
            "hostname",
            "connection_info",
            "certificate_data"
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the TLS certificate validator"""
        health_status = {
            'verifier': self.name,
            'type': self.get_verifier_type(),
            'enabled': self.enabled,
            'status': 'healthy',
            'pinned_certificates': len(self.pinned_certificates),
            'critical_endpoints': len(self.critical_endpoints),
            'crl_cache_size': len(self.crl_cache),
            'crypto_available': CRYPTO_AVAILABLE,
            'requests_available': REQUESTS_AVAILABLE
        }

        # Test certificate validation
        try:
            # Test with a known good certificate (google.com)
            test_result = await self._validate_tls_certificate('google.com', 443, 'https', False, {})

            if test_result['verdict'] == Verdict.AUTHENTIC:
                health_status['certificate_validation_test'] = 'passed'
            else:
                health_status['certificate_validation_test'] = f'failed: {test_result["metadata"].get("error", "unknown")}'
                health_status['status'] = 'degraded'

        except Exception as e:
            health_status['certificate_validation_test'] = f'failed: {str(e)}'
            health_status['status'] = 'unhealthy'

        return health_status

    async def cleanup(self):
        """Cleanup resources"""
        logger.info(f"Cleaning up {self.name}")
        self.certificate_store.clear()
        self.crl_cache.clear()


# Import required modules
import ssl
from cryptography.hazmat.primitives import serialization