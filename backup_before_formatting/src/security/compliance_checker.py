"""
合規性檢查器 - 金融合規性和監管要求

包含交易合規性、風險合規性、數據合規性等檢查
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class ComplianceLevel(str, Enum):
    """合規性級別"""

    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


class ComplianceCategory(str, Enum):
    """合規性類別"""

    TRADING_LIMITS = "trading_limits"
    RISK_MANAGEMENT = "risk_management"
    DATA_PROTECTION = "data_protection"
    REPORTING = "reporting"
    MARKET_MANIPULATION = "market_manipulation"
    INSIDER_TRADING = "insider_trading"
    AML_KYC = "aml_kyc"
    REGULATORY = "regulatory"


class ComplianceRule(BaseModel):
    """合規性規則"""

    rule_id: str = Field(..., description="規則ID")
    name: str = Field(..., description="規則名稱")
    category: ComplianceCategory = Field(..., description="規則類別")
    description: str = Field(..., description="規則描述")
    condition: str = Field(..., description="檢查條件")
    threshold: Optional[float] = Field(None, description="閾值")
    level: ComplianceLevel = Field(..., description="合規性級別")
    enabled: bool = Field(default=True, description="是否啟用")
    applicable_markets: List[str] = Field(default_factory=list, description="適用市場")
    applicable_products: List[str] = Field(default_factory=list, description="適用產品")
    regulatory_framework: str = Field(..., description="監管框架")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="最後更新時間"
    )


class ComplianceViolation(BaseModel):
    """合規性違規"""

    violation_id: str = Field(..., description="違規ID")
    rule_id: str = Field(..., description="規則ID")
    rule_name: str = Field(..., description="規則名稱")
    category: ComplianceCategory = Field(..., description="違規類別")
    level: ComplianceLevel = Field(..., description="違規級別")
    description: str = Field(..., description="違規描述")
    detected_at: datetime = Field(default_factory=datetime.now, description="檢測時間")
    entity_id: str = Field(..., description="實體ID")
    entity_type: str = Field(..., description="實體類型")
    violation_data: Dict[str, Any] = Field(default_factory=dict, description="違規數據")
    remediation_required: bool = Field(default=True, description="是否需要補救")
    remediation_status: str = Field(default="pending", description="補救狀態")
    regulatory_report_required: bool = Field(
        default=False, description="是否需要監管報告"
    )


class ComplianceReport(BaseModel):
    """合規性報告"""

    report_id: str = Field(..., description="報告ID")
    report_type: str = Field(..., description="報告類型")
    period_start: datetime = Field(..., description="報告期開始")
    period_end: datetime = Field(..., description="報告期結束")
    total_violations: int = Field(..., description="總違規數")
    violations_by_category: Dict[str, int] = Field(
        default_factory=dict, description="按類別違規數"
    )
    violations_by_level: Dict[str, int] = Field(
        default_factory=dict, description="按級別違規數"
    )
    remediation_rate: float = Field(..., description="補救率")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成時間")
    generated_by: str = Field(..., description="生成者")


class ComplianceChecker:
    """合規性檢查器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.compliance_checker")

        # 合規性規則
        self.compliance_rules: List[ComplianceRule] = []
        self.violations: List[ComplianceViolation] = []

        # 監管框架配置
        self.regulatory_frameworks = {
            "SEC": "美國證券交易委員會",
            "FINRA": "美國金融業監管局",
            "CFTC": "美國商品期貨交易委員會",
            "FCA": "英國金融行為監管局",
            "ESMA": "歐洲證券和市場管理局",
            "SFC": "香港證券及期貨事務監察委員會",
            "MAS": "新加坡金融管理局",
        }

    async def initialize(self) -> bool:
        """初始化合規性檢查器"""
        try:
            self.logger.info("Initializing compliance checker...")

            # 加載合規性規則
            await self._load_compliance_rules()

            self.logger.info("Compliance checker initialized successfully")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize compliance checker: {e}")
            return False

    async def _load_compliance_rules(self) -> None:
        """加載合規性規則"""
        try:
            # 默認合規性規則
            default_rules = [
                # 交易限制規則
                ComplianceRule(
                    rule_id="max_position_size",
                    name="最大持倉限制",
                    category=ComplianceCategory.TRADING_LIMITS,
                    description="單一持倉不得超過組合總值的20%",
                    condition="position_value / portfolio_value > 0.2",
                    threshold=0.2,
                    level=ComplianceLevel.VIOLATION,
                    applicable_markets=["US", "HK", "SG"],
                    applicable_products=["EQUITY", "BOND", "DERIVATIVE"],
                    regulatory_framework="SEC",
                ),
                ComplianceRule(
                    rule_id="max_daily_trading_volume",
                    name="最大日交易量限制",
                    category=ComplianceCategory.TRADING_LIMITS,
                    description="單日交易量不得超過平均日交易量的50%",
                    condition="daily_volume / avg_daily_volume > 0.5",
                    threshold=0.5,
                    level=ComplianceLevel.WARNING,
                    applicable_markets=["US", "HK"],
                    applicable_products=["EQUITY"],
                    regulatory_framework="SEC",
                ),
                # 風險管理規則
                ComplianceRule(
                    rule_id="max_portfolio_var",
                    name="最大組合VaR限制",
                    category=ComplianceCategory.RISK_MANAGEMENT,
                    description="組合95% VaR不得超過資本的5%",
                    condition="portfolio_var_95 / capital > 0.05",
                    threshold=0.05,
                    level=ComplianceLevel.CRITICAL,
                    applicable_markets=["US", "HK", "SG", "EU"],
                    applicable_products=["EQUITY", "BOND", "DERIVATIVE"],
                    regulatory_framework="SEC",
                ),
                ComplianceRule(
                    rule_id="max_drawdown_limit",
                    name="最大回撤限制",
                    category=ComplianceCategory.RISK_MANAGEMENT,
                    description="最大回撤不得超過15%",
                    condition="max_drawdown > 0.15",
                    threshold=0.15,
                    level=ComplianceLevel.VIOLATION,
                    applicable_markets=["US", "HK", "SG", "EU"],
                    applicable_products=["EQUITY", "BOND"],
                    regulatory_framework="SEC",
                ),
                # 市場操縱規則
                ComplianceRule(
                    rule_id="wash_trading_detection",
                    name="洗售交易檢測",
                    category=ComplianceCategory.MARKET_MANIPULATION,
                    description="檢測可能的洗售交易行為",
                    condition="same_symbol_buy_sell_within_short_time",
                    threshold=None,
                    level=ComplianceLevel.CRITICAL,
                    applicable_markets=["US", "HK", "SG", "EU"],
                    applicable_products=["EQUITY", "DERIVATIVE"],
                    regulatory_framework="SEC",
                ),
                ComplianceRule(
                    rule_id="price_manipulation_detection",
                    name="價格操縱檢測",
                    category=ComplianceCategory.MARKET_MANIPULATION,
                    description="檢測異常價格變動",
                    condition="price_change_percent > 20 and volume_spike",
                    threshold=20.0,
                    level=ComplianceLevel.WARNING,
                    applicable_markets=["US", "HK", "SG", "EU"],
                    applicable_products=["EQUITY"],
                    regulatory_framework="SEC",
                ),
                # 內幕交易規則
                ComplianceRule(
                    rule_id="insider_trading_detection",
                    name="內幕交易檢測",
                    category=ComplianceCategory.INSIDER_TRADING,
                    description="檢測可能的內幕交易行為",
                    condition="large_trade_before_news_announcement",
                    threshold=None,
                    level=ComplianceLevel.CRITICAL,
                    applicable_markets=["US", "HK", "SG", "EU"],
                    applicable_products=["EQUITY"],
                    regulatory_framework="SEC",
                ),
                # AML / KYC規則
                ComplianceRule(
                    rule_id="suspicious_transaction_detection",
                    name="可疑交易檢測",
                    category=ComplianceCategory.AML_KYC,
                    description="檢測可疑交易模式",
                    condition="unusual_trading_pattern_detected",
                    threshold=None,
                    level=ComplianceLevel.WARNING,
                    applicable_markets=["US", "HK", "SG", "EU"],
                    applicable_products=["EQUITY", "BOND", "DERIVATIVE"],
                    regulatory_framework="SEC",
                ),
                # 數據保護規則
                ComplianceRule(
                    rule_id="data_retention_compliance",
                    name="數據保留合規性",
                    category=ComplianceCategory.DATA_PROTECTION,
                    description="確保交易數據保留符合監管要求",
                    condition="data_retention_period < regulatory_requirement",
                    threshold=7,  # 7年
                    level=ComplianceLevel.VIOLATION,
                    applicable_markets=["US", "HK", "SG", "EU"],
                    applicable_products=["EQUITY", "BOND", "DERIVATIVE"],
                    regulatory_framework="SEC",
                ),
                # 報告規則
                ComplianceRule(
                    rule_id="regulatory_reporting_timeliness",
                    name="監管報告及時性",
                    category=ComplianceCategory.REPORTING,
                    description="確保監管報告按時提交",
                    condition="report_submission_delay > allowed_delay",
                    threshold=1,  # 1天
                    level=ComplianceLevel.VIOLATION,
                    applicable_markets=["US", "HK", "SG", "EU"],
                    applicable_products=["EQUITY", "BOND", "DERIVATIVE"],
                    regulatory_framework="SEC",
                ),
            ]

            self.compliance_rules = default_rules
            self.logger.info(f"Loaded {len(self.compliance_rules)} compliance rules")

        except Exception as e:
            self.logger.error(f"Error loading compliance rules: {e}")

    async def check_trading_compliance(
        self,
        trades: List[Dict[str, Any]],
        portfolio_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> List[ComplianceViolation]:
        """檢查交易合規性"""
        try:
            violations = []

            # 檢查交易限制規則
            trading_rules = [
                rule
                for rule in self.compliance_rules
                if rule.category == ComplianceCategory.TRADING_LIMITS and rule.enabled
            ]

            for rule in trading_rules:
                violation = await self._check_trading_rule(
                    rule, trades, portfolio_data, market_data
                )
                if violation:
                    violations.append(violation)

            # 檢查市場操縱規則
            manipulation_rules = [
                rule
                for rule in self.compliance_rules
                if rule.category == ComplianceCategory.MARKET_MANIPULATION
                and rule.enabled
            ]

            for rule in manipulation_rules:
                violation = await self._check_manipulation_rule(
                    rule, trades, market_data
                )
                if violation:
                    violations.append(violation)

            # 檢查內幕交易規則
            insider_rules = [
                rule
                for rule in self.compliance_rules
                if rule.category == ComplianceCategory.INSIDER_TRADING and rule.enabled
            ]

            for rule in insider_rules:
                violation = await self._check_insider_trading_rule(
                    rule, trades, market_data
                )
                if violation:
                    violations.append(violation)

            # 記錄違規
            for violation in violations:
                self.violations.append(violation)
                self.logger.warning(
                    f"Compliance violation detected: {violation.rule_name}"
                )

            return violations

        except Exception as e:
            self.logger.error(f"Error checking trading compliance: {e}")
            return []

    async def check_risk_compliance(
        self, risk_metrics: Dict[str, Any], portfolio_data: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """檢查風險合規性"""
        try:
            violations = []

            risk_rules = [
                rule
                for rule in self.compliance_rules
                if rule.category == ComplianceCategory.RISK_MANAGEMENT and rule.enabled
            ]

            for rule in risk_rules:
                violation = await self._check_risk_rule(
                    rule, risk_metrics, portfolio_data
                )
                if violation:
                    violations.append(violation)

            # 記錄違規
            for violation in violations:
                self.violations.append(violation)
                self.logger.warning(
                    f"Risk compliance violation detected: {violation.rule_name}"
                )

            return violations

        except Exception as e:
            self.logger.error(f"Error checking risk compliance: {e}")
            return []

    async def check_data_compliance(
        self, data_usage: Dict[str, Any], data_retention: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """檢查數據合規性"""
        try:
            violations = []

            data_rules = [
                rule
                for rule in self.compliance_rules
                if rule.category == ComplianceCategory.DATA_PROTECTION and rule.enabled
            ]

            for rule in data_rules:
                violation = await self._check_data_rule(
                    rule, data_usage, data_retention
                )
                if violation:
                    violations.append(violation)

            # 記錄違規
            for violation in violations:
                self.violations.append(violation)
                self.logger.warning(
                    f"Data compliance violation detected: {violation.rule_name}"
                )

            return violations

        except Exception as e:
            self.logger.error(f"Error checking data compliance: {e}")
            return []

    async def _check_trading_rule(
        self,
        rule: ComplianceRule,
        trades: List[Dict[str, Any]],
        portfolio_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> Optional[ComplianceViolation]:
        """檢查交易規則"""
        try:
            if rule.rule_id == "max_position_size":
                # 檢查最大持倉限制
                portfolio_value = portfolio_data.get("total_value", 0)

                for trade in trades:
                    symbol = trade.get("symbol")
                    quantity = trade.get("quantity", 0)
                    price = trade.get("price", 0)
                    position_value = quantity * price

                    if (
                        portfolio_value > 0
                        and position_value / portfolio_value > rule.threshold
                    ):
                        return ComplianceViolation(
                            violation_id=f"{rule.rule_id}_{datetime.now().timestamp()}",
                            rule_id=rule.rule_id,
                            rule_name=rule.name,
                            category=rule.category,
                            level=rule.level,
                            description=f"Position in {symbol} exceeds maximum size limit",
                            entity_id=symbol,
                            entity_type="position",
                            violation_data={
                                "position_value": position_value,
                                "portfolio_value": portfolio_value,
                                "position_ratio": position_value / portfolio_value,
                                "threshold": rule.threshold,
                            },
                        )

            elif rule.rule_id == "max_daily_trading_volume":
                # 檢查最大日交易量限制
                for trade in trades:
                    symbol = trade.get("symbol")
                    quantity = trade.get("quantity", 0)

                    if symbol in market_data:
                        avg_volume = market_data[symbol].get("avg_daily_volume", 0)
                        if avg_volume > 0 and quantity / avg_volume > rule.threshold:
                            return ComplianceViolation(
                                violation_id=f"{rule.rule_id}_{datetime.now().timestamp()}",
                                rule_id=rule.rule_id,
                                rule_name=rule.name,
                                category=rule.category,
                                level=rule.level,
                                description=f"Daily trading volume for {symbol} exceeds limit",
                                entity_id=symbol,
                                entity_type="trade",
                                violation_data={
                                    "trading_volume": quantity,
                                    "avg_daily_volume": avg_volume,
                                    "volume_ratio": quantity / avg_volume,
                                    "threshold": rule.threshold,
                                },
                            )

            return None

        except Exception as e:
            self.logger.error(f"Error checking trading rule {rule.rule_id}: {e}")
            return None

    async def _check_risk_rule(
        self,
        rule: ComplianceRule,
        risk_metrics: Dict[str, Any],
        portfolio_data: Dict[str, Any],
    ) -> Optional[ComplianceViolation]:
        """檢查風險規則"""
        try:
            if rule.rule_id == "max_portfolio_var":
                # 檢查最大組合VaR限制
                portfolio_var_95 = risk_metrics.get("var_95", 0)
                capital = portfolio_data.get("total_value", 0)

                if capital > 0 and abs(portfolio_var_95) / capital > rule.threshold:
                    return ComplianceViolation(
                        violation_id=f"{rule.rule_id}_{datetime.now().timestamp()}",
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        category=rule.category,
                        level=rule.level,
                        description="Portfolio VaR exceeds maximum limit",
                        entity_id="portfolio",
                        entity_type="portfolio",
                        violation_data={
                            "portfolio_var_95": portfolio_var_95,
                            "capital": capital,
                            "var_ratio": abs(portfolio_var_95) / capital,
                            "threshold": rule.threshold,
                        },
                    )

            elif rule.rule_id == "max_drawdown_limit":
                # 檢查最大回撤限制
                max_drawdown = risk_metrics.get("max_drawdown", 0)

                if max_drawdown > rule.threshold:
                    return ComplianceViolation(
                        violation_id=f"{rule.rule_id}_{datetime.now().timestamp()}",
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        category=rule.category,
                        level=rule.level,
                        description="Maximum drawdown exceeds limit",
                        entity_id="portfolio",
                        entity_type="portfolio",
                        violation_data={
                            "max_drawdown": max_drawdown,
                            "threshold": rule.threshold,
                        },
                    )

            return None

        except Exception as e:
            self.logger.error(f"Error checking risk rule {rule.rule_id}: {e}")
            return None

    async def _check_manipulation_rule(
        self,
        rule: ComplianceRule,
        trades: List[Dict[str, Any]],
        market_data: Dict[str, Any],
    ) -> Optional[ComplianceViolation]:
        """檢查市場操縱規則"""
        try:
            if rule.rule_id == "wash_trading_detection":
                # 檢測洗售交易
                symbol_trades = {}
                for trade in trades:
                    symbol = trade.get("symbol")
                    if symbol not in symbol_trades:
                        symbol_trades[symbol] = []
                    symbol_trades[symbol].append(trade)

                for symbol, symbol_trade_list in symbol_trades.items():
                    if len(symbol_trade_list) >= 2:
                        # 檢查是否有短時間內的買賣交易
                        for i, trade1 in enumerate(symbol_trade_list):
                            for trade2 in symbol_trade_list[i + 1 :]:
                                if (
                                    trade1.get("side") != trade2.get("side")
                                    and abs(
                                        (
                                            trade1.get("timestamp", datetime.now())
                                            - trade2.get("timestamp", datetime.now())
                                        ).total_seconds()
                                    )
                                    < 300
                                ):  # 5分鐘內

                                    return ComplianceViolation(
                                        violation_id=f"{rule.rule_id}_{datetime.now().timestamp()}",
                                        rule_id=rule.rule_id,
                                        rule_name=rule.name,
                                        category=rule.category,
                                        level=rule.level,
                                        description=f"Potential wash trading detected for {symbol}",
                                        entity_id=symbol,
                                        entity_type="trade",
                                        violation_data={
                                            "symbol": symbol,
                                            "trade1": trade1,
                                            "trade2": trade2,
                                            "time_diff_seconds": abs(
                                                (
                                                    trade1.get(
                                                        "timestamp", datetime.now()
                                                    )
                                                    - trade2.get(
                                                        "timestamp", datetime.now()
                                                    )
                                                ).total_seconds()
                                            ),
                                        },
                                    )

            elif rule.rule_id == "price_manipulation_detection":
                # 檢測價格操縱
                for trade in trades:
                    symbol = trade.get("symbol")
                    if symbol in market_data:
                        price_change_percent = market_data[symbol].get(
                            "price_change_percent", 0
                        )
                        volume_spike = market_data[symbol].get("volume_spike", False)

                        if abs(price_change_percent) > rule.threshold and volume_spike:
                            return ComplianceViolation(
                                violation_id=f"{rule.rule_id}_{datetime.now().timestamp()}",
                                rule_id=rule.rule_id,
                                rule_name=rule.name,
                                category=rule.category,
                                level=rule.level,
                                description=f"Potential price manipulation detected for {symbol}",
                                entity_id=symbol,
                                entity_type="trade",
                                violation_data={
                                    "symbol": symbol,
                                    "price_change_percent": price_change_percent,
                                    "volume_spike": volume_spike,
                                    "threshold": rule.threshold,
                                },
                            )

            return None

        except Exception as e:
            self.logger.error(f"Error checking manipulation rule {rule.rule_id}: {e}")
            return None

    async def _check_insider_trading_rule(
        self,
        rule: ComplianceRule,
        trades: List[Dict[str, Any]],
        market_data: Dict[str, Any],
    ) -> Optional[ComplianceViolation]:
        """檢查內幕交易規則"""
        try:
            if rule.rule_id == "insider_trading_detection":
                # 檢測內幕交易（簡化實現）
                for trade in trades:
                    symbol = trade.get("symbol")
                    quantity = trade.get("quantity", 0)
                    timestamp = trade.get("timestamp", datetime.now())

                    # 檢查是否有大額交易在新聞發布前
                    if symbol in market_data:
                        news_announcement_time = market_data[symbol].get(
                            "news_announcement_time"
                        )
                        if news_announcement_time:
                            time_diff = (
                                news_announcement_time - timestamp
                            ).total_seconds()
                            if 0 < time_diff < 3600:  # 1小時內
                                avg_volume = market_data[symbol].get(
                                    "avg_daily_volume", 0
                                )
                                if (
                                    avg_volume > 0 and quantity / avg_volume > 0.1
                                ):  # 超過平均日交易量的10%
                                    return ComplianceViolation(
                                        violation_id=f"{rule.rule_id}_{datetime.now().timestamp()}",
                                        rule_id=rule.rule_id,
                                        rule_name=rule.name,
                                        category=rule.category,
                                        level=rule.level,
                                        description=f"Potential insider trading detected for {symbol}",
                                        entity_id=symbol,
                                        entity_type="trade",
                                        violation_data={
                                            "symbol": symbol,
                                            "quantity": quantity,
                                            "trade_time": timestamp,
                                            "news_time": news_announcement_time,
                                            "time_diff_seconds": time_diff,
                                            "volume_ratio": quantity / avg_volume,
                                        },
                                    )

            return None

        except Exception as e:
            self.logger.error(
                f"Error checking insider trading rule {rule.rule_id}: {e}"
            )
            return None

    async def _check_data_rule(
        self,
        rule: ComplianceRule,
        data_usage: Dict[str, Any],
        data_retention: Dict[str, Any],
    ) -> Optional[ComplianceViolation]:
        """檢查數據規則"""
        try:
            if rule.rule_id == "data_retention_compliance":
                # 檢查數據保留合規性
                retention_period_years = data_retention.get("retention_period_years", 0)
                regulatory_requirement_years = rule.threshold

                if retention_period_years < regulatory_requirement_years:
                    return ComplianceViolation(
                        violation_id=f"{rule.rule_id}_{datetime.now().timestamp()}",
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        category=rule.category,
                        level=rule.level,
                        description="Data retention period does not meet regulatory requirements",
                        entity_id="data_system",
                        entity_type="data",
                        violation_data={
                            "retention_period_years": retention_period_years,
                            "regulatory_requirement_years": regulatory_requirement_years,
                            "shortfall_years": regulatory_requirement_years
                            - retention_period_years,
                        },
                    )

            return None

        except Exception as e:
            self.logger.error(f"Error checking data rule {rule.rule_id}: {e}")
            return None

    async def generate_compliance_report(
        self, start_date: datetime, end_date: datetime
    ) -> ComplianceReport:
        """生成合規性報告"""
        try:
            # 篩選期間內的違規
            period_violations = [
                v for v in self.violations if start_date <= v.detected_at <= end_date
            ]

            # 統計違規
            violations_by_category = {}
            violations_by_level = {}

            for violation in period_violations:
                category = violation.category.value
                level = violation.level.value

                violations_by_category[category] = (
                    violations_by_category.get(category, 0) + 1
                )
                violations_by_level[level] = violations_by_level.get(level, 0) + 1

            # 計算補救率
            remediated_violations = len(
                [v for v in period_violations if v.remediation_status == "completed"]
            )
            remediation_rate = (
                remediated_violations / len(period_violations)
                if period_violations
                else 0
            )

            report = ComplianceReport(
                report_id=f"compliance_report_{datetime.now().timestamp()}",
                report_type="periodic_compliance_report",
                period_start=start_date,
                period_end=end_date,
                total_violations=len(period_violations),
                violations_by_category=violations_by_category,
                violations_by_level=violations_by_level,
                remediation_rate=remediation_rate,
                generated_by="compliance_checker",
            )

            self.logger.info(f"Generated compliance report: {report.report_id}")
            return report

        except Exception as e:
            self.logger.error(f"Error generating compliance report: {e}")
            raise

    async def get_violation_summary(self) -> Dict[str, Any]:
        """獲取違規摘要"""
        try:
            total_violations = len(self.violations)
            unresolved_violations = len(
                [v for v in self.violations if v.remediation_status != "completed"]
            )

            violations_by_category = {}
            violations_by_level = {}

            for violation in self.violations:
                category = violation.category.value
                level = violation.level.value

                violations_by_category[category] = (
                    violations_by_category.get(category, 0) + 1
                )
                violations_by_level[level] = violations_by_level.get(level, 0) + 1

            return {
                "total_violations": total_violations,
                "unresolved_violations": unresolved_violations,
                "violations_by_category": violations_by_category,
                "violations_by_level": violations_by_level,
                "compliance_rules_count": len(self.compliance_rules),
                "active_rules_count": len(
                    [r for r in self.compliance_rules if r.enabled]
                ),
            }

        except Exception as e:
            self.logger.error(f"Error getting violation summary: {e}")
            return {}

    async def add_compliance_rule(self, rule: ComplianceRule) -> bool:
        """添加合規性規則"""
        try:
            self.compliance_rules.append(rule)
            self.logger.info(f"Added compliance rule: {rule.rule_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error adding compliance rule: {e}")
            return False

    async def update_compliance_rule(
        self, rule_id: str, updates: Dict[str, Any]
    ) -> bool:
        """更新合規性規則"""
        try:
            for rule in self.compliance_rules:
                if rule.rule_id == rule_id:
                    for key, value in updates.items():
                        if hasattr(rule, key):
                            setattr(rule, key, value)

                    rule.last_updated = datetime.now()
                    self.logger.info(f"Updated compliance rule: {rule_id}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error updating compliance rule: {e}")
            return False

    async def delete_compliance_rule(self, rule_id: str) -> bool:
        """刪除合規性規則"""
        try:
            for i, rule in enumerate(self.compliance_rules):
                if rule.rule_id == rule_id:
                    del self.compliance_rules[i]
                    self.logger.info(f"Deleted compliance rule: {rule_id}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error deleting compliance rule: {e}")
            return False
