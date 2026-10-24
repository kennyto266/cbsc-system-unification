#!/usr/bin/env python3
"""
安全和合規監控模塊
Security and Compliance Monitoring Module

監控API安全事件、數據訪問控制、配置變更審計、數據質量合規性、交易合規性
"""

import time
import json
import logging
import asyncio
import hashlib
import hmac
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, generate_latest
import ipaddress
from enum import Enum

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """安全事件類型"""
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_ERROR = "authorization_error"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    CONFIGURATION_CHANGE = "configuration_change"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_BREACH = "security_breach"
    COMPLIANCE_VIOLATION = "compliance_violation"

class ComplianceRule(Enum):
    """合規規則"""
    DATA_ENCRYPTION = "data_encryption"
    ACCESS_LOGGING = "access_logging"
    RETENTION_POLICY = "retention_policy"
    TRADING_LIMITS = "trading_limits"
    RISK_MANAGEMENT = "risk_management"
    AUDIT_TRAIL = "audit_trail"

@dataclass
class SecurityEvent:
    """安全事件記錄"""
    event_id: str
    timestamp: float
    event_type: SecurityEventType
    severity: str  # low, medium, high, critical
    source_ip: str
    user_id: Optional[str]
    service_name: str
    description: str
    details: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[float] = None
    false_positive: bool = False

@dataclass
class AuthenticationMetrics:
    """認證指標"""
    timestamp: float
    total_attempts: int
    successful_attempts: int
    failed_attempts: int
    failure_rate: float
    unique_users: int
    suspicious_ips: Set[str]
    brute_force_detected: bool

@dataclass
class DataAccessMetrics:
    """數據訪問指標"""
    timestamp: float
    service_name: str
    data_source: str
    access_type: str  # read, write, delete
    user_id: str
    access_count: int
    data_volume_mb: float
    encryption_used: bool
    access_authorized: bool
    risk_score: float

@dataclass
class ConfigurationAuditMetrics:
    """配置審計指標"""
    timestamp: float
    config_type: str  # system, service, security, trading
    service_name: str
    change_type: str  # create, update, delete
    user_id: str
    parameter_changed: str
    old_value: Any
    new_value: Any
    change_approved: bool
    compliance_check_passed: bool

@dataclass
class TradingComplianceMetrics:
    """交易合規指標"""
    timestamp: float
    strategy_name: str
    symbol: str
    trade_count: int
    position_size: float
    leverage_ratio: float
    risk_metrics: Dict[str, float]
    compliance_score: float
    violations_detected: List[str]
    regulatory_requirements_met: bool

class SecurityMonitoringSystem:
    """安全監控系統"""

    def __init__(self):
        """初始化安全監控系統"""
        self.security_events = []
        self.active_threats = []
        self.blocked_ips = set()
        self.suspicious_patterns = {}

        # 安全配置
        self.max_failed_attempts = 5
        self.block_duration_seconds = 3600  # 1小時
        self.risk_thresholds = {
            'high_volume_access': 1000,  # MB
            'frequent_access': 100,  # requests per minute
            'unusual_access_pattern': 3  # std deviations from normal
        }

        # 初始化Prometheus指標
        self.registry = CollectorRegistry()

        # 安全事件指標
        self.security_events_total = Counter('security_events_total', 'Total security events', ['event_type', 'severity'], registry=self.registry)
        self.security_events_active = Gauge('security_events_active', 'Active security events', ['severity'], registry=self.registry)
        self.security_events_resolution_time = Histogram('security_event_resolution_time_seconds', 'Security event resolution time', registry=self.registry)

        # 認證指標
        self.authentication_attempts_total = Counter('authentication_attempts_total', 'Authentication attempts', ['result'], registry=self.registry)
        self.authentication_failure_rate = Gauge('authentication_failure_rate', 'Authentication failure rate', registry=self.registry)
        self.suspicious_ips_blocked = Gauge('suspicious_ips_blocked', 'Number of blocked suspicious IPs', registry=self.registry)

        # 數據訪問指標
        self.data_access_total = Counter('data_access_total', 'Data access attempts', ['service', 'access_type', 'authorized'], registry=self.registry)
        self.data_volume_accessed = Histogram('data_volume_accessed_mb', 'Data volume accessed', ['service', 'data_source'], registry=self.registry)
        self.encrypted_access_ratio = Gauge('encrypted_access_ratio', 'Encrypted access ratio', ['service'], registry=self.registry)

        # 配置變更指標
        self.configuration_changes_total = Counter('configuration_changes_total', 'Configuration changes', ['config_type', 'service', 'approved'], registry=self.registry)
        self.compliance_violations_total = Counter('compliance_violations_total', 'Compliance violations', ['rule_type', 'severity'], registry=self.registry)

        # 交易合規指標
        self.trading_compliance_score = Gauge('trading_compliance_score', 'Trading compliance score', ['strategy_name'], registry=self.registry)
        self.risk_limit_violations = Counter('risk_limit_violations_total', 'Risk limit violations', ['limit_type'], registry=self.registry)

        logger.info("Security monitoring system initialized")

    def record_security_event(self, event_type: SecurityEventType, severity: str,
                            source_ip: str, user_id: Optional[str], service_name: str,
                            description: str, details: Dict[str, Any] = None) -> str:
        """
        記錄安全事件

        Args:
            event_type: 事件類型
            severity: 嚴重程度
            source_ip: 源IP地址
            user_id: 用戶ID
            service_name: 服務名稱
            description: 事件描述
            details: 事件詳情

        Returns:
            str: 事件ID
        """
        event_id = str(time.time()) + "_" + hashlib.md5(description.encode()).hexdigest()[:8]

        event = SecurityEvent(
            event_id=event_id,
            timestamp=time.time(),
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            user_id=user_id,
            service_name=service_name,
            description=description,
            details=details or {}
        )

        self.security_events.append(event)

        # 更新Prometheus指標
        self.security_events_total.labels(
            event_type=event_type.value,
            severity=severity
        ).inc()

        # 自動處理高嚴重程度事件
        if severity in ['high', 'critical']:
            self._handle_critical_security_event(event)

        # 檢查威脅模式
        self._check_threat_patterns(event)

        logger.warning(f"Security event recorded: {event_type.value} - {description}")

        return event_id

    def record_authentication_attempt(self, success: bool, user_id: str,
                                    source_ip: str, auth_method: str = "password") -> AuthenticationMetrics:
        """
        記錄認證嘗試

        Args:
            success: 是否成功
            user_id: 用戶ID
            source_ip: 源IP地址
            auth_method: 認證方法

        Returns:
            AuthenticationMetrics: 認證指標
        """
        # 更新認證統計
        recent_events = [
            e for e in self.security_events
            if e.event_type == SecurityEventType.AUTHENTICATION_FAILURE
            and time.time() - e.timestamp < 300  # 5分鐘內
        ]

        total_recent_attempts = len(recent_events)
        failed_recent_attempts = len(recent_events)
        unique_users = len(set(e.user_id for e in recent_events if e.user_id))
        suspicious_ips = set(e.source_ip for e in recent_events)

        # 檢查暴力破解
        brute_force_detected = self._detect_brute_force_attack(source_ip, recent_events)

        # 計算失敗率
        failure_rate = (failed_recent_attempts / max(1, total_recent_attempts)) * 100

        # 記錄安全事件（如果失敗）
        if not success:
            self.record_security_event(
                SecurityEventType.AUTHENTICATION_FAILURE,
                severity="medium" if not brute_force_detected else "high",
                source_ip=source_ip,
                user_id=user_id,
                service_name="authentication_service",
                description=f"Authentication failure for user {user_id}",
                details={
                    "auth_method": auth_method,
                    "failure_count": failed_recent_attempts + 1
                }
            )

            # 如果檢測到暴力破解，封鎖IP
            if brute_force_detected:
                self.block_ip_address(source_ip, "Brute force attack detected")

        # 更新Prometheus指標
        self.authentication_attempts_total.labels(result="success" if success else "failure").inc()
        self.authentication_failure_rate.set(failure_rate)
        self.suspicious_ips_blocked.set(len(self.blocked_ips))

        metrics = AuthenticationMetrics(
            timestamp=time.time(),
            total_attempts=total_recent_attempts + 1,
            successful_attempts=(total_recent_attempts + 1) - failed_recent_attempts,
            failed_attempts=failed_recent_attempts + (0 if success else 1),
            failure_rate=failure_rate,
            unique_users=unique_users + (0 if success else 1),
            suspicious_ips=suspicious_ips,
            brute_force_detected=brute_force_detected
        )

        logger.info(f"Authentication attempt recorded: {user_id} from {source_ip}, "
                   f"success: {success}, failure_rate: {failure_rate:.1f}%")
        return metrics

    def record_data_access(self, service_name: str, data_source: str,
                         access_type: str, user_id: str, data_volume_mb: float,
                         encryption_used: bool = True, access_authorized: bool = True) -> DataAccessMetrics:
        """
        記錄數據訪問

        Args:
            service_name: 服務名稱
            data_source: 數據源
            access_type: 訪問類型
            user_id: 用戶ID
            data_volume_mb: 數據體量(MB)
            encryption_used: 是否使用加密
            access_authorized: 是否授權

        Returns:
            DataAccessMetrics: 數據訪問指標
        """
        # 計算風險評分
        risk_score = self._calculate_access_risk(
            data_volume_mb, access_type, service_name, user_id
        )

        # 檢查異常訪問模式
        if risk_score > 0.7:
            self.record_security_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                severity="medium",
                source_ip="",  # 數據訪問可能不在網絡層
                user_id=user_id,
                service_name=service_name,
                description=f"Suspicious data access pattern detected",
                details={
                    "data_source": data_source,
                    "access_type": access_type,
                    "data_volume_mb": data_volume_mb,
                    "risk_score": risk_score
                }
            )

        # 記錄未授權訪問
        if not access_authorized:
            self.record_security_event(
                SecurityEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
                severity="high",
                source_ip="",
                user_id=user_id,
                service_name=service_name,
                description=f"Unauthorized data access attempt",
                details={
                    "data_source": data_source,
                    "access_type": access_type
                }
            )

        # 更新Prometheus指標
        self.data_access_total.labels(
            service=service_name,
            access_type=access_type,
            authorized="yes" if access_authorized else "no"
        ).inc()

        self.data_volume_accessed.labels(
            service=service_name,
            data_source=data_source
        ).observe(data_volume_mb)

        # 計算加密訪問比率
        total_accesses = len([e for e in self.security_events
                            if e.event_type == SecurityEventType.DATA_ACCESS and
                            e.details.get('service_name') == service_name])
        if total_accesses > 0:
            encrypted_ratio = len([e for e in self.security_events
                                 if e.event_type == SecurityEventType.DATA_ACCESS and
                                 e.details.get('service_name') == service_name and
                                 e.details.get('encryption_used', True)]) / total_accesses
            self.encrypted_access_ratio.labels(service=service_name).set(encrypted_ratio)

        # 獲取訪問計數（簡化實現）
        access_count = len([e for e in self.security_events
                           if e.event_type == SecurityEventType.DATA_ACCESS and
                           e.details.get('user_id') == user_id and
                           time.time() - e.timestamp < 3600])  # 1小時內

        metrics = DataAccessMetrics(
            timestamp=time.time(),
            service_name=service_name,
            data_source=data_source,
            access_type=access_type,
            user_id=user_id,
            access_count=access_count + 1,
            data_volume_mb=data_volume_mb,
            encryption_used=encryption_used,
            access_authorized=access_authorized,
            risk_score=risk_score
        )

        logger.info(f"Data access recorded: {access_type} access to {data_source} by {user_id}, "
                   f"volume: {data_volume_mb:.1f}MB, authorized: {access_authorized}")
        return metrics

    def record_configuration_change(self, config_type: str, service_name: str,
                                  change_type: str, user_id: str, parameter_changed: str,
                                  old_value: Any, new_value: Any,
                                  change_approved: bool = False) -> ConfigurationAuditMetrics:
        """
        記錄配置變更

        Args:
            config_type: 配置類型
            service_name: 服務名稱
            change_type: 變更類型
            user_id: 用戶ID
            parameter_changed: 參數名稱
            old_value: 舊值
            new_value: 新值
            change_approved: 是否批准

        Returns:
            ConfigurationAuditMetrics: 配置審計指標
        """
        # 檢查合規性
        compliance_check_passed = self._check_configuration_compliance(
            config_type, parameter_changed, new_value, service_name
        )

        # 記錄安全事件
        severity = "low" if change_approved else "medium"
        if not compliance_check_passed:
            severity = "high"

        self.record_security_event(
            SecurityEventType.CONFIGURATION_CHANGE,
            severity=severity,
            source_ip="",
            user_id=user_id,
            service_name=service_name,
            description=f"Configuration change: {parameter_changed}",
            details={
                "config_type": config_type,
                "change_type": change_type,
                "parameter": parameter_changed,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "approved": change_approved,
                "compliance_check": compliance_check_passed
            }
        )

        # 如果合規檢查失敗，記錄合規違規
        if not compliance_check_passed:
            self.record_security_event(
                SecurityEventType.COMPLIANCE_VIOLATION,
                severity="high",
                source_ip="",
                user_id=user_id,
                service_name=service_name,
                description=f"Configuration compliance violation",
                details={
                    "config_type": config_type,
                    "parameter": parameter_changed,
                    "new_value": str(new_value),
                    "violation_type": "configuration_compliance"
                }
            )

        # 更新Prometheus指標
        self.configuration_changes_total.labels(
            config_type=config_type,
            service=service_name,
            approved="yes" if change_approved else "no"
        ).inc()

        if not compliance_check_passed:
            self.compliance_violations_total.labels(
                rule_type="configuration",
                severity="high"
            ).inc()

        metrics = ConfigurationAuditMetrics(
            timestamp=time.time(),
            config_type=config_type,
            service_name=service_name,
            change_type=change_type,
            user_id=user_id,
            parameter_changed=parameter_changed,
            old_value=old_value,
            new_value=new_value,
            change_approved=change_approved,
            compliance_check_passed=compliance_check_passed
        )

        logger.info(f"Configuration change recorded: {service_name}.{parameter_changed} "
                   f"from {old_value} to {new_value}, approved: {change_approved}")
        return metrics

    def record_trading_compliance_check(self, strategy_name: str, symbol: str,
                                      trade_count: int, position_size: float,
                                      leverage_ratio: float, risk_metrics: Dict[str, float]) -> TradingComplianceMetrics:
        """
        記錄交易合規檢查

        Args:
            strategy_name: 策略名稱
            symbol: 股票代碼
            trade_count: 交易次數
            position_size: 倉位大小
            leverage_ratio: 杠桿比率
            risk_metrics: 風險指標

        Returns:
            TradingComplianceMetrics: 交易合規指標
        """
        # 檢查合規規則
        violations_detected = []
        compliance_score = 100

        # 檢查交易頻率限制
        if trade_count > 1000:  # 假設每日1000筆交易上限
            violations_detected.append("excessive_trading_frequency")
            compliance_score -= 20

        # 檢查倉位大小限制
        if position_size > 1000000:  # 假設100萬倉位上限
            violations_detected.append("excessive_position_size")
            compliance_score -= 15

        # 檢查杠杆限制
        if leverage_ratio > 3.0:  # 假設3倍杠杆上限
            violations_detected.append("excessive_leverage")
            compliance_score -= 25

        # 檢查風險指標
        if risk_metrics.get('var', 0) > 0.05:  # VaR > 5%
            violations_detected.append("excessive_var")
            compliance_score -= 20

        if risk_metrics.get('max_drawdown', 0) > 0.2:  # 最大回撤 > 20%
            violations_detected.append("excessive_drawdown")
            compliance_score -= 15

        # 記錄違規
        for violation in violations_detected:
            self.record_security_event(
                SecurityEventType.COMPLIANCE_VIOLATION,
                severity="medium",
                source_ip="",
                user_id="",
                service_name="trading_engine",
                description=f"Trading compliance violation: {violation}",
                details={
                    "strategy_name": strategy_name,
                    "symbol": symbol,
                    "violation_type": violation,
                    "current_value": risk_metrics.get(violation.split('_')[-1], 0)
                }
            )

            self.risk_limit_violations.labels(limit_type=violation).inc()

        # 記錄合規評分
        regulatory_requirements_met = compliance_score >= 70
        self.trading_compliance_score.labels(strategy_name=strategy_name).set(compliance_score)

        metrics = TradingComplianceMetrics(
            timestamp=time.time(),
            strategy_name=strategy_name,
            symbol=symbol,
            trade_count=trade_count,
            position_size=position_size,
            leverage_ratio=leverage_ratio,
            risk_metrics=risk_metrics,
            compliance_score=compliance_score,
            violations_detected=violations_detected,
            regulatory_requirements_met=regulatory_requirements_met
        )

        logger.info(f"Trading compliance check recorded: {strategy_name} on {symbol}, "
                   f"score: {compliance_score:.1f}, violations: {len(violations_detected)}")
        return metrics

    def _detect_brute_force_attack(self, source_ip: str, recent_failures: List[SecurityEvent]) -> bool:
        """檢測暴力破解攻擊"""
        # 檢查來自同一IP的失敗次數
        ip_failures = [e for e in recent_failures if e.source_ip == source_ip]
        return len(ip_failures) >= self.max_failed_attempts

    def _calculate_access_risk(self, data_volume_mb: float, access_type: str,
                            service_name: str, user_id: str) -> float:
        """計算訪問風險評分"""
        risk_score = 0.0

        # 數據體量風險
        if data_volume_mb > self.risk_thresholds['high_volume_access']:
            risk_score += 0.3

        # 訪問類型風險
        if access_type == 'write':
            risk_score += 0.2
        elif access_type == 'delete':
            risk_score += 0.4

        # 訪問頻率風險
        recent_accesses = len([e for e in self.security_events
                              if e.event_type == SecurityEventType.DATA_ACCESS and
                              e.details.get('user_id') == user_id and
                              time.time() - e.timestamp < 60])  # 1分鐘內

        if recent_accesses > self.risk_thresholds['frequent_access']:
            risk_score += 0.3

        return min(1.0, risk_score)

    def _check_configuration_compliance(self, config_type: str, parameter: str,
                                     value: Any, service_name: str) -> bool:
        """檢查配置合規性"""
        # 定義合規規則
        compliance_rules = {
            'security': {
                'password_min_length': lambda v: len(str(v)) >= 8,
                'session_timeout': lambda v: int(v) <= 3600,
                'max_login_attempts': lambda v: int(v) <= 5
            },
            'trading': {
                'max_leverage': lambda v: float(v) <= 3.0,
                'risk_limit': lambda v: float(v) <= 0.05,
                'position_limit': lambda v: float(v) <= 1000000
            },
            'data': {
                'encryption_enabled': lambda v: bool(v) is True,
                'backup_frequency_hours': lambda v: int(v) <= 24,
                'retention_days': lambda v: int(v) <= 2555  # 7年
            }
        }

        try:
            if config_type in compliance_rules and parameter in compliance_rules[config_type]:
                rule_func = compliance_rules[config_type][parameter]
                return rule_func(value)
        except Exception as e:
            logger.warning(f"Compliance check error for {config_type}.{parameter}: {e}")
            return False

        return True  # 默認通過

    def _handle_critical_security_event(self, event: SecurityEvent):
        """處理關鍵安全事件"""
        # 添加到活躍威脅列表
        self.active_threats.append(event)

        # 更新活躍事件指標
        active_counts = {
            'low': 0, 'medium': 0, 'high': 0, 'critical': 0
        }
        for threat in self.active_threats:
            active_counts[threat.severity] += 1

        for severity, count in active_counts.items():
            self.security_events_active.labels(severity=severity).set(count)

        logger.critical(f"Critical security event detected: {event.description}")

    def _check_threat_patterns(self, event: SecurityEvent):
        """檢查威脅模式"""
        pattern_key = f"{event.event_type.value}_{event.service_name}"
        current_time = time.time()

        # 更新模式統計
        if pattern_key not in self.suspicious_patterns:
            self.suspicious_patterns[pattern_key] = {
                'count': 0,
                'first_seen': current_time,
                'last_seen': current_time
            }

        self.suspicious_patterns[pattern_key]['count'] += 1
        self.suspicious_patterns[pattern_key]['last_seen'] = current_time

        # 檢查是否構成威脅
        if self.suspicious_patterns[pattern_key]['count'] > 10:  # 10次以上相似事件
            time_window = current_time - self.suspicious_patterns[pattern_key]['first_seen']
            if time_window < 300:  # 5分鐘內
                logger.warning(f"Suspicious pattern detected: {pattern_key}, "
                            f"count: {self.suspicious_patterns[pattern_key]['count']}, "
                            f"time window: {time_window:.1f}s")

    def block_ip_address(self, ip_address: str, reason: str):
        """封鎖IP地址"""
        self.blocked_ips.add(ip_address)
        self.record_security_event(
            SecurityEventType.SECURITY_BREACH,
            severity="high",
            source_ip=ip_address,
            user_id=None,
            service_name="security_monitor",
            description=f"IP address blocked: {reason}",
            details={"reason": reason, "blocked_at": time.time()}
        )
        logger.warning(f"IP address {ip_address} blocked: {reason}")

    def is_ip_blocked(self, ip_address: str) -> bool:
        """檢查IP是否被封鎖"""
        return ip_address in self.blocked_ips

    def resolve_security_event(self, event_id: str, resolution_notes: str = "") -> bool:
        """解決安全事件"""
        for event in self.security_events:
            if event.event_id == event_id and not event.resolved:
                event.resolved = True
                event.resolution_time = time.time()

                # 更新解決時間指標
                resolution_time = event.resolution_time - event.timestamp
                self.security_events_resolution_time.observe(resolution_time)

                # 從活躍威脅中移除
                if event in self.active_threats:
                    self.active_threats.remove(event)

                logger.info(f"Security event resolved: {event_id}")
                return True

        logger.warning(f"Security event not found or already resolved: {event_id}")
        return False

    def get_security_summary(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        獲取安全摘要

        Args:
            time_window_hours: 時間窗口(小時)

        Returns:
            Dict[str, Any]: 安全摘要
        """
        cutoff_time = time.time() - (time_window_hours * 3600)
        recent_events = [e for e in self.security_events if e.timestamp > cutoff_time]

        # 統計各類事件
        event_counts = {}
        severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        resolved_count = 0

        for event in recent_events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            severity_counts[event.severity] += 1
            if event.resolved:
                resolved_count += 1

        # 計算趨勢
        previous_window_start = cutoff_time - (time_window_hours * 3600)
        previous_events = [e for e in self.security_events
                          if previous_window_start < e.timestamp < cutoff_time]

        trend = {
            'total_change': len(recent_events) - len(previous_events),
            'severity_trend': {
                sev: self._calculate_trend(sev, recent_events, previous_events)
                for sev in ['low', 'medium', 'high', 'critical']
            }
        }

        return {
            "time_window_hours": time_window_hours,
            "timestamp": time.time(),
            "total_events": len(recent_events),
            "resolved_events": resolved_count,
            "unresolved_events": len(recent_events) - resolved_count,
            "event_counts": event_counts,
            "severity_distribution": severity_counts,
            "active_threats": len(self.active_threats),
            "blocked_ips": len(self.blocked_ips),
            "suspicious_patterns": len(self.suspicious_patterns),
            "trends": trend,
            "security_score": max(0, 100 - severity_counts['high'] * 10 - severity_counts['critical'] * 25)
        }

    def _calculate_trend(self, severity: str, current_events: List[SecurityEvent],
                       previous_events: List[SecurityEvent]) -> str:
        """計算嚴重程度趨勢"""
        current_count = len([e for e in current_events if e.severity == severity])
        previous_count = len([e for e in previous_events if e.severity == severity])

        if current_count == previous_count:
            return "stable"
        elif current_count > previous_count:
            return "increasing"
        else:
            return "decreasing"

    def get_prometheus_metrics(self) -> str:
        """
        獲取Prometheus格式的指標

        Returns:
            str: Prometheus格式指標數據
        """
        return generate_latest(self.registry).decode('utf-8')

# 全局安全監控系統實例
security_monitoring_system = SecurityMonitoringSystem()

def get_security_monitoring_system() -> SecurityMonitoringSystem:
    """獲取安全監控系統實例"""
    return security_monitoring_system

# 裝飾器
def require_ip_whitelist(allowed_ips: List[str]):
    """IP白名單裝飾器"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # 這裡需要獲取請求的IP地址，簡化實現
            client_ip = "127.0.0.1"  # 應該從請求中獲取

            if client_ip not in allowed_ips:
                security_monitoring_system.record_security_event(
                    SecurityEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
                    severity="high",
                    source_ip=client_ip,
                    user_id=None,
                    service_name="api_gateway",
                    description=f"Unauthorized access attempt from non-whitelisted IP",
                    details={"allowed_ips": allowed_ips}
                )
                raise PermissionError(f"Access denied for IP: {client_ip}")

            return func(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == "__main__":
    def main():
        """測試安全監控功能"""
        monitor = SecurityMonitoringSystem()

        print("Testing security monitoring...")

        # 測試認證監控
        print("\n=== Authentication Monitoring ===")
        auth_metrics = monitor.record_authentication_attempt(
            success=False,
            user_id="test_user",
            source_ip="192.168.1.100"
        )
        print(f"Authentication metrics: failure_rate={auth_metrics.failure_rate:.1f}%")

        # 模擬多次失敗以觸發暴力破解檢測
        for i in range(6):
            monitor.record_authentication_attempt(
                success=False,
                user_id="test_user",
                source_ip="192.168.1.100"
            )

        print(f"Suspicious IPs blocked: {len(monitor.blocked_ips)}")

        # 測試數據訪問監控
        print("\n=== Data Access Monitoring ===")
        access_metrics = monitor.record_data_access(
            service_name="data_service",
            data_source="stock_prices",
            access_type="read",
            user_id="trader1",
            data_volume_mb=50.5,
            encryption_used=True,
            access_authorized=True
        )
        print(f"Access risk score: {access_metrics.risk_score:.2f}")

        # 測試配置變更監控
        print("\n=== Configuration Change Monitoring ===")
        config_metrics = monitor.record_configuration_change(
            config_type="security",
            service_name="authentication_service",
            change_type="update",
            user_id="admin1",
            parameter_changed="max_login_attempts",
            old_value=5,
            new_value=3,
            change_approved=True
        )
        print(f"Configuration compliance: {config_metrics.compliance_check_passed}")

        # 測試交易合規監控
        print("\n=== Trading Compliance Monitoring ===")
        trading_metrics = monitor.record_trading_compliance_check(
            strategy_name="RSI_STRATEGY",
            symbol="0700.HK",
            trade_count=500,
            position_size=500000,
            leverage_ratio=2.5,
            risk_metrics={
                "var": 0.03,
                "max_drawdown": 0.15,
                "sharpe_ratio": 1.2
            }
        )
        print(f"Trading compliance score: {trading_metrics.compliance_score:.1f}")

        # 獲取安全摘要
        print("\n=== Security Summary ===")
        summary = monitor.get_security_summary(24)  # 24小時窗口
        print(f"Total security events: {summary['total_events']}")
        print(f"Active threats: {summary['active_threats']}")
        print(f"Security score: {summary['security_score']}")

        # 獲取Prometheus指標
        prometheus_metrics = monitor.get_prometheus_metrics()
        print(f"\nPrometheus metrics generated: {len(prometheus_metrics)} bytes")

        print("\nSecurity monitoring test completed!")

    main()