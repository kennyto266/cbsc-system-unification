"""
Security Anomaly Detection Service
安全異常檢測服務

檢測用戶行為異常、安全威脅和潛在的攻擊模式
"""

import asyncio
import json
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as redis

from security.audit_logger import AuditEventType, EventSeverity
from core.config import settings

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of security anomalies"""
    UNUSUAL_LOGIN_PATTERN = "unusual_login_pattern"
    MULTIPLE_FAILED_ATTEMPTS = "multiple_failed_attempts"
    SUSPICIOUS_ACCESS_PATTERN = "suspicious_access_pattern"
    DATA_ACCESS_ANOMALY = "data_access_anomaly"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    BRUTE_FORCE_ATTACK = "brute_force_attack"
    UNAUTHORIZED_DATA_ACCESS = "unauthorized_data_access"
    ABNORMAL_API_USAGE = "abnormal_api_usage"
    CONCURRENT_SESSIONS = "concurrent_sessions"
    GEOLOCATION_ANOMALY = "geolocation_anomaly"


@dataclass
class Anomaly:
    """Security anomaly data structure"""
    anomaly_type: AnomalyType
    user_id: Optional[str]
    ip_address: Optional[str]
    severity: EventSeverity
    risk_score: float
    confidence: float
    description: str
    details: Dict[str, Any]
    detected_at: datetime
    requires_action: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'anomaly_type': self.anomaly_type.value,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'severity': self.severity.value,
            'risk_score': self.risk_score,
            'confidence': self.confidence,
            'description': self.description,
            'details': self.details,
            'detected_at': self.detected_at.isoformat(),
            'requires_action': self.requires_action
        }


class UserBehaviorProfile:
    """User behavior profile for anomaly detection"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.login_patterns = []
        self.access_patterns = []
        self.data_access_patterns = []
        self.api_usage_patterns = []
        self.ip_addresses = set()
        self.user_agents = set()
        self.active_hours = set()
        self.last_updated = datetime.utcnow()

    def update_pattern(self, event_data: Dict[str, Any]):
        """Update user behavior patterns"""
        timestamp = datetime.fromisoformat(event_data['timestamp'])

        # Track active hours
        self.active_hours.add(timestamp.hour)

        # Track IP addresses and user agents
        if event_data.get('ip_address'):
            self.ip_addresses.add(event_data['ip_address'])
        if event_data.get('user_agent'):
            self.user_agents.add(event_data['user_agent'])

        # Update specific patterns based on event type
        event_type = event_data.get('event_type')

        if 'login' in event_type:
            self._update_login_pattern(event_data)
        elif 'data' in event_type or 'api' in event_type:
            self._update_access_pattern(event_data)

        self.last_updated = datetime.utcnow()

    def _update_login_pattern(self, event_data: Dict[str, Any]):
        """Update login pattern"""
        self.login_patterns.append({
            'timestamp': event_data['timestamp'],
            'ip_address': event_data.get('ip_address'),
            'success': event_data.get('success', True)
        })

        # Keep only recent patterns (last 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)
        self.login_patterns = [
            p for p in self.login_patterns
            if datetime.fromisoformat(p['timestamp']) > cutoff
        ]

    def _update_access_pattern(self, event_data: Dict[str, Any]):
        """Update access pattern"""
        self.access_patterns.append({
            'timestamp': event_data['timestamp'],
            'resource': event_data.get('resource'),
            'action': event_data.get('action'),
            'ip_address': event_data.get('ip_address')
        })

        # Keep only recent patterns
        cutoff = datetime.utcnow() - timedelta(days=7)
        self.access_patterns = [
            p for p in self.access_patterns
            if datetime.fromisoformat(p['timestamp']) > cutoff
        ]

    def get_baseline_stats(self) -> Dict[str, Any]:
        """Get baseline statistics for anomaly detection"""
        if not self.login_patterns and not self.access_patterns:
            return {}

        login_hours = [datetime.fromisoformat(p['timestamp']).hour for p in self.login_patterns]
        access_hours = [datetime.fromisoformat(p['timestamp']).hour for p in self.access_patterns]
        all_hours = login_hours + access_hours

        return {
            'typical_hours': list(set(all_hours)) if all_hours else [],
            'known_ips': list(self.ip_addresses),
            'known_user_agents': list(self.user_agents),
            'login_success_rate': self._calculate_login_success_rate(),
            'avg_daily_requests': len(self.access_patterns) / 7 if self.access_patterns else 0
        }

    def _calculate_login_success_rate(self) -> float:
        """Calculate login success rate"""
        if not self.login_patterns:
            return 1.0

        successful = sum(1 for p in self.login_patterns if p.get('success', True))
        return successful / len(self.login_patterns)


class SecurityAnomalyDetector:
    """Advanced security anomaly detection system"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.user_profiles: Dict[str, UserBehaviorProfile] = {}
        self.anomaly_thresholds = {
            'failed_login_threshold': 5,  # 5 failed logins in 5 minutes
            'unusual_hour_score': 0.7,   # Score threshold for unusual hours
            'new_ip_penalty': 0.3,       # Penalty for new IP address
            'concurrent_sessions_max': 3, # Max concurrent sessions
            'data_access_spike': 5.0,    # 5x normal data access
            'api_usage_spike': 3.0       # 3x normal API usage
        }
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize anomaly detector"""
        if not self.redis_client:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    retry_on_timeout=True
                )
                await self.redis_client.ping()
                logger.info("Anomaly detector connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect Redis for anomaly detection: {e}")
                self.redis_client = None

    async def detect_anomalies(self, event_id: str, event_data: Dict[str, Any]) -> List[Anomaly]:
        """Main anomaly detection method"""
        anomalies = []

        # Update user profile
        user_id = event_data.get('user_id')
        if user_id:
            await self._update_user_profile(user_id, event_data)

        # Run various anomaly detectors
        anomalies.extend(await self._detect_login_anomalies(event_data))
        anomalies.extend(await self._detect_access_anomalies(event_data))
        anomalies.extend(await self._detect_data_anomalies(event_data))
        anomalies.extend(await self._detect_behavioral_anomalies(event_data))
        anomalies.extend(await self._detect_attack_patterns(event_data))

        # Log and handle detected anomalies
        for anomaly in anomalies:
            await self._handle_detected_anomaly(anomaly, event_id)

        return anomalies

    async def _update_user_profile(self, user_id: str, event_data: Dict[str, Any]):
        """Update user behavior profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserBehaviorProfile(user_id)

        self.user_profiles[user_id].update_pattern(event_data)

        # Periodically save profiles to Redis
        if self.redis_client:
            try:
                profile_key = f"security:profile:{user_id}"
                profile_data = {
                    'last_updated': self.user_profiles[user_id].last_updated.isoformat(),
                    'login_patterns': self.user_profiles[user_id].login_patterns[-10:],  # Keep last 10
                    'ip_addresses': list(self.user_profiles[user_id].ip_addresses),
                    'active_hours': list(self.user_profiles[user_id].active_hours)
                }
                await self.redis_client.setex(
                    profile_key,
                    7 * 24 * 3600,  # Keep for 7 days
                    json.dumps(profile_data)
                )
            except Exception as e:
                logger.error(f"Error saving user profile: {e}")

    async def _detect_login_anomalies(self, event_data: Dict[str, Any]) -> List[Anomaly]:
        """Detect login-related anomalies"""
        anomalies = []
        event_type = event_data.get('event_type')

        if 'login' not in event_type:
            return anomalies

        user_id = event_data.get('user_id')
        ip_address = event_data.get('ip_address')

        # Check for multiple failed login attempts
        if event_type == 'login_failed':
            failed_count = await self._count_recent_failed_logins(user_id, ip_address)

            if failed_count >= self.anomaly_thresholds['failed_login_threshold']:
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.MULTIPLE_FAILED_ATTEMPTS,
                    user_id=user_id,
                    ip_address=ip_address,
                    severity=EventSeverity.HIGH,
                    risk_score=0.8,
                    confidence=0.9,
                    description=f"Multiple failed login attempts detected: {failed_count} attempts",
                    details={
                        'failed_attempts': failed_count,
                        'time_window': '5 minutes',
                        'ip_address': ip_address
                    }
                ))

        # Check for unusual login patterns
        if user_id and user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            current_hour = datetime.fromisoformat(event_data['timestamp']).hour

            # Check if login is at unusual hour
            if profile.active_hours and current_hour not in profile.active_hours:
                # Calculate business hours overlap
                business_hours = set(range(9, 18))
                is_business_hour = current_hour in business_hours
                user_business_hours = len(profile.active_hours & business_hours)

                if not is_business_hour and user_business_hours > 0:
                    anomalies.append(Anomaly(
                        anomaly_type=AnomalyType.UNUSUAL_LOGIN_PATTERN,
                        user_id=user_id,
                        ip_address=ip_address,
                        severity=EventSeverity.MEDIUM,
                        risk_score=0.6,
                        confidence=0.7,
                        description=f"Login at unusual hour: {current_hour}:00",
                        details={
                            'login_hour': current_hour,
                            'typical_hours': list(profile.active_hours),
                            'is_business_hour': is_business_hour
                        }
                    ))

            # Check for new IP address
            if ip_address and ip_address not in profile.ip_addresses:
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.UNUSUAL_LOGIN_PATTERN,
                    user_id=user_id,
                    ip_address=ip_address,
                    severity=EventSeverity.MEDIUM,
                    risk_score=0.5,
                    confidence=0.8,
                    description=f"Login from new IP address: {ip_address}",
                    details={
                        'new_ip': ip_address,
                        'known_ips': list(profile.ip_addresses),
                        'ip_reputation': await self._check_ip_reputation(ip_address)
                    }
                ))

        return anomalies

    async def _detect_access_anomalies(self, event_data: Dict[str, Any]) -> List[Anomaly]:
        """Detect access pattern anomalies"""
        anomalies = []
        user_id = event_data.get('user_id')

        if not user_id:
            return anomalies

        # Check for data access anomalies
        if 'data' in event_data.get('event_type', ''):
            access_count = await self._count_recent_data_access(user_id)
            baseline = self.user_profiles.get(user_id, UserBehaviorProfile('')).get_baseline_stats()
            avg_daily = baseline.get('avg_daily_requests', 1)

            if access_count > avg_daily * self.anomaly_thresholds['data_access_spike']:
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.DATA_ACCESS_ANOMALY,
                    user_id=user_id,
                    ip_address=event_data.get('ip_address'),
                    severity=EventSeverity.HIGH,
                    risk_score=0.7,
                    confidence=0.8,
                    description=f"Unusual data access pattern: {access_count} requests",
                    details={
                        'access_count': access_count,
                        'baseline_daily': avg_daily,
                        'spike_factor': access_count / max(avg_daily, 1)
                    }
                ))

        return anomalies

    async def _detect_data_anomalies(self, event_data: Dict[str, Any]) -> List[Anomaly]:
        """Detect data-related security anomalies"""
        anomalies = []

        # Check for suspicious data export
        if event_data.get('event_type') == 'data_export':
            user_id = event_data.get('user_id')
            export_count = await self._count_recent_exports(user_id)

            if export_count > 10:  # More than 10 exports in 24 hours
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.UNAUTHORIZED_DATA_ACCESS,
                    user_id=user_id,
                    ip_address=event_data.get('ip_address'),
                    severity=EventSeverity.HIGH,
                    risk_score=0.8,
                    confidence=0.9,
                    description=f"Suspicious data export activity: {export_count} exports",
                    details={
                        'export_count': export_count,
                        'time_window': '24 hours',
                        'export_details': event_data.get('details', {})
                    }
                ))

        return anomalies

    async def _detect_behavioral_anomalies(self, event_data: Dict[str, Any]) -> List[Anomaly]:
        """Detect behavioral anomalies"""
        anomalies = []
        user_id = event_data.get('user_id')

        if not user_id:
            return anomalies

        # Check for concurrent sessions
        if self.redis_client:
            try:
                sessions_key = f"security:sessions:{user_id}"
                sessions = await self.redis_client.hgetall(sessions_key)

                if len(sessions) > self.anomaly_thresholds['concurrent_sessions_max']:
                    anomalies.append(Anomaly(
                        anomaly_type=AnomalyType.CONCURRENT_SESSIONS,
                        user_id=user_id,
                        severity=EventSeverity.MEDIUM,
                        risk_score=0.6,
                        confidence=0.8,
                        description=f"Multiple concurrent sessions detected: {len(sessions)} sessions",
                        details={
                            'active_sessions': len(sessions),
                            'session_details': sessions
                        }
                    ))
            except Exception as e:
                logger.error(f"Error checking concurrent sessions: {e}")

        return anomalies

    async def _detect_attack_patterns(self, event_data: Dict[str, Any]) -> List[Anomaly]:
        """Detect attack patterns"""
        anomalies = []
        ip_address = event_data.get('ip_address')

        if not ip_address:
            return anomalies

        # Check for brute force patterns
        attack_indicators = await self._check_attack_indicators(ip_address)

        if attack_indicators.get('brute_force_score', 0) > 0.7:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.BRUTE_FORCE_ATTACK,
                ip_address=ip_address,
                user_id=event_data.get('user_id'),
                severity=EventSeverity.CRITICAL,
                risk_score=0.9,
                confidence=0.8,
                description="Brute force attack pattern detected",
                details=attack_indicators
            ))

        return anomalies

    async def _count_recent_failed_logins(self, user_id: Optional[str], ip_address: Optional[str]) -> int:
        """Count recent failed login attempts"""
        if not self.redis_client:
            return 0

        try:
            current_time = int(time.time())
            window_start = current_time - 300  # 5 minutes ago

            if user_id:
                pattern = f"*login_failed*{user_id}*"
            else:
                pattern = f"*login_failed*{ip_address}*"

            # This would need to be implemented based on your audit log storage
            # For now, return a placeholder
            return 0
        except Exception as e:
            logger.error(f"Error counting failed logins: {e}")
            return 0

    async def _count_recent_data_access(self, user_id: str) -> int:
        """Count recent data access attempts"""
        if not self.redis_client:
            return 0

        try:
            # Implementation depends on your metric tracking
            # Placeholder for now
            return 1
        except Exception as e:
            logger.error(f"Error counting data access: {e}")
            return 0

    async def _count_recent_exports(self, user_id: str) -> int:
        """Count recent data export attempts"""
        if not self.redis_client:
            return 0

        try:
            # Implementation depends on your export tracking
            # Placeholder for now
            return 1
        except Exception as e:
            logger.error(f"Error counting exports: {e}")
            return 0

    async def _check_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Check IP address reputation"""
        # This would integrate with IP reputation services
        # Placeholder implementation
        return {
            'reputation': 'unknown',
            'malicious': False,
            'proxy': False,
            'tor': False
        }

    async def _check_attack_indicators(self, ip_address: str) -> Dict[str, Any]:
        """Check for attack indicators from IP"""
        if not self.redis_client:
            return {}

        try:
            # Check various attack patterns
            indicators = {}

            # Check request rate
            rate_key = f"security:rate:{ip_address}:minute"
            request_count = await self.redis_client.zcard(rate_key)
            indicators['requests_per_minute'] = request_count
            indicators['brute_force_score'] = min(request_count / 100, 1.0)

            # Check failed login attempts
            failed_key = f"security:failed:{ip_address}"
            failed_count = await self.redis_client.get(failed_key)
            indicators['failed_attempts'] = int(failed_count) if failed_count else 0

            # Check suspicious patterns
            suspicious_key = f"security:suspicious:{ip_address}"
            suspicious_count = await self.redis_client.get(suspicious_key)
            indicators['suspicious_activities'] = int(suspicious_count) if suspicious_count else 0

            return indicators
        except Exception as e:
            logger.error(f"Error checking attack indicators: {e}")
            return {}

    async def _handle_detected_anomaly(self, anomaly: Anomaly, event_id: str):
        """Handle detected anomaly"""
        logger.warning(
            f"Security anomaly detected: {anomaly.anomaly_type.value}",
            extra={'anomaly': anomaly.to_dict()}
        )

        # Store anomaly for review
        if self.redis_client:
            try:
                anomaly_key = f"security:anomalies:{datetime.now().strftime('%Y-%m-%d')}"
                await self.redis_client.lpush(
                    anomaly_key,
                    json.dumps(anomaly.to_dict())
                )
                await self.redis_client.expire(anomaly_key, 30 * 24 * 3600)  # Keep for 30 days
            except Exception as e:
                logger.error(f"Error storing anomaly: {e}")

        # Trigger automatic responses for critical anomalies
        if anomaly.severity == EventSeverity.CRITICAL and anomaly.requires_action:
            await self._trigger_auto_response(anomaly)

    async def _trigger_auto_response(self, anomaly: Anomaly):
        """Trigger automatic security response"""
        if anomaly.anomaly_type == AnomalyType.BRUTE_FORCE_ATTACK and anomaly.ip_address:
            # Block IP temporarily
            if self.redis_client:
                try:
                    block_key = f"security:blocked:{anomaly.ip_address}"
                    await self.redis_client.setex(
                        block_key,
                        3600,  # 1 hour
                        json.dumps({
                            'reason': 'Brute force attack detected',
                            'anomaly_id': anomaly.detected_at.isoformat()
                        })
                    )
                    logger.critical(f"Auto-blocked IP due to brute force: {anomaly.ip_address}")
                except Exception as e:
                    logger.error(f"Error auto-blocking IP: {e}")

    async def get_user_risk_score(self, user_id: str) -> Dict[str, Any]:
        """Calculate comprehensive risk score for user"""
        profile = self.user_profiles.get(user_id)
        if not profile:
            return {'risk_score': 0.0, 'risk_factors': []}

        risk_factors = []
        risk_score = 0.0

        # Check failed login rate
        baseline = profile.get_baseline_stats()
        success_rate = baseline.get('login_success_rate', 1.0)
        if success_rate < 0.8:
            risk_factors.append('low_login_success_rate')
            risk_score += 0.3

        # Check IP diversity
        unique_ips = len(profile.ip_addresses)
        if unique_ips > 5:
            risk_factors.append('high_ip_diversity')
            risk_score += 0.2

        # Check access patterns
        avg_daily = baseline.get('avg_daily_requests', 0)
        if avg_daily > 1000:
            risk_factors.append('high_access_volume')
            risk_score += 0.2

        return {
            'risk_score': min(risk_score, 1.0),
            'risk_factors': risk_factors,
            'baseline_stats': baseline,
            'profile_updated': profile.last_updated.isoformat()
        }


# Global instance
anomaly_detector = SecurityAnomalyDetector()


def get_anomaly_detector() -> SecurityAnomalyDetector:
    """Get anomaly detector instance"""
    return anomaly_detector


async def initialize_anomaly_detection():
    """Initialize anomaly detection system"""
    await anomaly_detector.initialize()
    logger.info("Security anomaly detection system initialized")