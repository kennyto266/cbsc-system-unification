#!/usr/bin/env python3
"""
Portfolio Constraint System
投資組合約束系統

Advanced constraint management for portfolio optimization
專業投資組合優化約束管理系統

Features:
- Position constraints (weight bounds)
- Sector constraints (industry/sector limits)
- Turnover constraints (trading limits)
- Risk constraints (VaR, drawdown limits)
- Custom constraint framework
- Constraint validation and debugging
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class ConstraintConfig:
    """約束配置"""
    # 基本約束
    min_weight: float = 0.0  # 最小權重
    max_weight: float = 1.0  # 最大權重
    max_positions: int = 50  # 最大持倉數量

    # 交易約束
    max_turnover: float = 1.0  # 最大周轉率
    min_trade_size: float = 0.01  # 最小交易規模

    # 風險約束
    max_portfolio_volatility: float = 0.5  # 最大投資組合波動率
    max_concentration: float = 0.4  # 最大集中度

    # 驗證選項
    enable_debugging: bool = False  # 啟用調試模式
    tolerance: float = 1e-8  # 數值容差

@dataclass
class ConstraintResult:
    """約束檢查結果"""
    constraint_name: str
    constraint_type: str
    is_satisfied: bool
    current_value: float
    limit_value: float
    violation_amount: float
    violation_percentage: float
    affected_assets: List[str]
    timestamp: str

@dataclass
class ConstraintViolation:
    """約束違規"""
    constraint_name: str
    violation_type: str
    severity: str  # 'warning', 'error', 'critical'
    description: str
    current_value: float
    limit_value: float
    suggested_fix: str

class PortfolioConstraint(ABC):
    """投資組合約束抽象基類"""

    def __init__(self, name: str, constraint_type: str):
        self.name = name
        self.constraint_type = constraint_type
        self.is_active = True

    @abstractmethod
    def check(self, weights: np.ndarray, data: Optional[Dict[str, Any]] = None) -> ConstraintResult:
        """檢查約束是否滿足"""
        pass

    @abstractmethod
    def get_bounds(self, num_assets: int) -> List[Tuple[float, float]]:
        """獲取權重邊界"""
        pass

    @abstractmethod
    def get_scipy_constraints(self, asset_names: List[str]) -> List[Dict]:
        """獲取SciPy優化約束"""
        pass

class WeightBoundConstraint(PortfolioConstraint):
    """權重邊界約束"""

    def __init__(
        self,
        name: str = "WeightBound",
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        asset_bounds: Optional[Dict[str, Tuple[float, float]]] = None
    ):
        super().__init__(name, "weight_bound")
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.asset_bounds = asset_bounds or {}

    def check(self, weights: np.ndarray, data: Optional[Dict[str, Any]] = None) -> ConstraintResult:
        asset_names = data.get('asset_names', [f"Asset_{i}" for i in range(len(weights))])

        violations = []
        affected_assets = []
        max_violation = 0.0
        current_max = 0.0

        for i, (weight, asset) in enumerate(zip(weights, asset_names)):
            asset_min = self.asset_bounds.get(asset, (self.min_weight, self.max_weight))[0]
            asset_max = self.asset_bounds.get(asset, (self.min_weight, self.max_weight))[1]

            if weight < asset_min:
                violation_amount = asset_min - weight
                violations.append(violation_amount)
                affected_assets.append(asset)
                max_violation = max(max_violation, violation_amount)

            elif weight > asset_max:
                violation_amount = weight - asset_max
                violations.append(violation_amount)
                affected_assets.append(asset)
                max_violation = max(max_violation, violation_amount)

            current_max = max(current_max, abs(weight))

        is_satisfied = len(violations) == 0
        limit_value = self.max_weight if current_max > self.max_weight else self.min_weight

        return ConstraintResult(
            constraint_name=self.name,
            constraint_type=self.constraint_type,
            is_satisfied=is_satisfied,
            current_value=current_max,
            limit_value=limit_value,
            violation_amount=max_violation,
            violation_percentage=(max_violation / limit_value * 100) if limit_value != 0 else float('inf'),
            affected_assets=affected_assets,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def get_bounds(self, num_assets: int) -> List[Tuple[float, float]]:
        bounds = []
        for i in range(num_assets):
            if f"Asset_{i}" in self.asset_bounds:
                bounds.append(self.asset_bounds[f"Asset_{i}"])
            else:
                bounds.append((self.min_weight, self.max_weight))
        return bounds

    def get_scipy_constraints(self, asset_names: List[str]) -> List[Dict]:
        return []  # 權重邊界通過bounds參數處理，不需要額外約束

class PositionLimitConstraint(PortfolioConstraint):
    """持倉數量限制約束"""

    def __init__(self, name: str = "PositionLimit", max_positions: int = 50, min_weight_threshold: float = 0.01):
        super().__init__(name, "position_limit")
        self.max_positions = max_positions
        self.min_weight_threshold = min_weight_threshold

    def check(self, weights: np.ndarray, data: Optional[Dict[str, Any]] = None) -> ConstraintResult:
        active_positions = np.sum(weights >= self.min_weight_threshold)
        current_value = active_positions

        is_satisfied = active_positions <= self.max_positions
        violation_amount = max(0, active_positions - self.max_positions)
        violation_percentage = (violation_amount / self.max_positions * 100) if self.max_positions > 0 else float('inf')

        asset_names = data.get('asset_names', [f"Asset_{i}" for i in range(len(weights))])
        affected_assets = [asset for i, (weight, asset) in enumerate(zip(weights, asset_names))
                          if weight >= self.min_weight_threshold]

        return ConstraintResult(
            constraint_name=self.name,
            constraint_type=self.constraint_type,
            is_satisfied=is_satisfied,
            current_value=current_value,
            limit_value=self.max_positions,
            violation_amount=violation_amount,
            violation_percentage=violation_percentage,
            affected_assets=affected_assets,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def get_bounds(self, num_assets: int) -> List[Tuple[float, float]]:
        return [(0.0, 1.0)] * num_assets

    def get_scipy_constraints(self, asset_names: List[str]) -> List[Dict]:
        return []  # 這個約束很難用簡單的線性約束表示

class SectorConstraint(PortfolioConstraint):
    """行業約束"""

    def __init__(
        self,
        name: str = "Sector",
        sector_mapping: Dict[str, str] = None,
        sector_limits: Dict[str, Tuple[float, float]] = None
    ):
        super().__init__(name, "sector")
        self.sector_mapping = sector_mapping or {}
        self.sector_limits = sector_limits or {}

    def check(self, weights: np.ndarray, data: Optional[Dict[str, Any]] = None) -> ConstraintResult:
        asset_names = data.get('asset_names', [])
        if not asset_names or not self.sector_mapping:
            return ConstraintResult(
                constraint_name=self.name,
                constraint_type=self.constraint_type,
                is_satisfied=True,
                current_value=0.0,
                limit_value=0.0,
                violation_amount=0.0,
                violation_percentage=0.0,
                affected_assets=[],
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

        # 計算每個行業的權重
        sector_weights = {}
        for weight, asset in zip(weights, asset_names):
            sector = self.sector_mapping.get(asset, "Unknown")
            sector_weights[sector] = sector_weights.get(sector, 0) + weight

        # 檢查行業限制
        violations = []
        affected_assets = []
        max_violation = 0.0
        current_max = 0.0

        for sector, weight in sector_weights.items():
            if sector in self.sector_limits:
                min_limit, max_limit = self.sector_limits[sector]
                if weight < min_limit:
                    violation_amount = min_limit - weight
                    violations.append(violation_amount)
                    max_violation = max(max_violation, violation_amount)
                    # 找出這個行業的資產
                    sector_assets = [asset for asset in asset_names
                                   if self.sector_mapping.get(asset, "Unknown") == sector]
                    affected_assets.extend(sector_assets)

                elif weight > max_limit:
                    violation_amount = weight - max_limit
                    violations.append(violation_amount)
                    max_violation = max(max_violation, violation_amount)
                    # 找出這個行業的資產
                    sector_assets = [asset for asset in asset_names
                                   if self.sector_mapping.get(asset, "Unknown") == sector]
                    affected_assets.extend(sector_assets)

                current_max = max(current_max, weight)

        is_satisfied = len(violations) == 0
        max_sector_limit = max([max for _, max in self.sector_limits.values()]) if self.sector_limits else 1.0
        limit_value = max(current_max, max_sector_limit)

        return ConstraintResult(
            constraint_name=self.name,
            constraint_type=self.constraint_type,
            is_satisfied=is_satisfied,
            current_value=current_max,
            limit_value=limit_value,
            violation_amount=max_violation,
            violation_percentage=(max_violation / limit_value * 100) if limit_value != 0 else float('inf'),
            affected_assets=list(set(affected_assets)),
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def get_bounds(self, num_assets: int) -> List[Tuple[float, float]]:
        return [(0.0, 1.0)] * num_assets

    def get_scipy_constraints(self, asset_names: List[str]) -> List[Dict]:
        constraints = []

        for sector, (min_limit, max_limit) in self.sector_limits.items():
            # 獲取該行業的資產索引
            sector_indices = [i for i, asset in enumerate(asset_names)
                            if self.sector_mapping.get(asset, "Unknown") == sector]

            if sector_indices:
                # 最小權重約束
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda w, idx=sector_indices: np.sum(w[idx]) - min_limit
                })
                # 最大權重約束
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda w, idx=sector_indices, max_w=max_limit: max_w - np.sum(w[idx])
                })

        return constraints

class TurnoverConstraint(PortfolioConstraint):
    """周轉率約束"""

    def __init__(
        self,
        name: str = "Turnover",
        max_turnover: float = 1.0,
        previous_weights: Optional[np.ndarray] = None
    ):
        super().__init__(name, "turnover")
        self.max_turnover = max_turnover
        self.previous_weights = previous_weights

    def check(self, weights: np.ndarray, data: Optional[Dict[str, Any]] = None) -> ConstraintResult:
        if self.previous_weights is None:
            return ConstraintResult(
                constraint_name=self.name,
                constraint_type=self.constraint_type,
                is_satisfied=True,
                current_value=0.0,
                limit_value=self.max_turnover,
                violation_amount=0.0,
                violation_percentage=0.0,
                affected_assets=[],
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

        # 計算周轉率
        turnover = np.sum(np.abs(weights - self.previous_weights)) / 2

        is_satisfied = turnover <= self.max_turnover
        violation_amount = max(0, turnover - self.max_turnover)
        violation_percentage = (violation_amount / self.max_turnover * 100) if self.max_turnover > 0 else float('inf')

        # 找出變化最大的資產
        asset_names = data.get('asset_names', [f"Asset_{i}" for i in range(len(weights))])
        changes = np.abs(weights - self.previous_weights)
        threshold = np.max(changes) * 0.5  # 變化大於最大變化的50%
        affected_assets = [asset for i, (asset, change) in enumerate(zip(asset_names, changes))
                          if change >= threshold]

        return ConstraintResult(
            constraint_name=self.name,
            constraint_type=self.constraint_type,
            is_satisfied=is_satisfied,
            current_value=turnover,
            limit_value=self.max_turnover,
            violation_amount=violation_amount,
            violation_percentage=violation_percentage,
            affected_assets=affected_assets,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def get_bounds(self, num_assets: int) -> List[Tuple[float, float]]:
        return [(0.0, 1.0)] * num_assets

    def get_scipy_constraints(self, asset_names: List[str]) -> List[Dict]:
        return []  # 周轉率約束很難用線性約束表示

class RiskBudgetConstraint(PortfolioConstraint):
    """風險預算約束"""

    def __init__(
        self,
        name: str = "RiskBudget",
        risk_budgets: Optional[Dict[str, float]] = None,
        max_risk_contribution: float = 0.5
    ):
        super().__init__(name, "risk_budget")
        self.risk_budgets = risk_budgets or {}
        self.max_risk_contribution = max_risk_contribution

    def check(self, weights: np.ndarray, data: Optional[Dict[str, Any]] = None) -> ConstraintResult:
        cov_matrix = data.get('cov_matrix')
        asset_names = data.get('asset_names', [])

        if cov_matrix is None or len(asset_names) == 0:
            return ConstraintResult(
                constraint_name=self.name,
                constraint_type=self.constraint_type,
                is_satisfied=True,
                current_value=0.0,
                limit_value=0.0,
                violation_amount=0.0,
                violation_percentage=0.0,
                affected_assets=[],
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

        # 計算風險貢獻
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        if portfolio_variance <= 0:
            return ConstraintResult(
                constraint_name=self.name,
                constraint_type=self.constraint_type,
                is_satisfied=True,
                current_value=0.0,
                limit_value=self.max_risk_contribution,
                violation_amount=0.0,
                violation_percentage=0.0,
                affected_assets=[],
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

        marginal_contributions = np.dot(cov_matrix, weights) / portfolio_variance
        risk_contributions = weights * marginal_contributions

        # 檢查風險貢獻限制
        violations = []
        affected_assets = []
        max_violation = 0.0
        current_max = np.max(risk_contributions)

        for i, (risk_contrib, asset) in enumerate(zip(risk_contributions, asset_names)):
            budget = self.risk_budgets.get(asset, self.max_risk_contribution)
            if risk_contrib > budget:
                violation_amount = risk_contrib - budget
                violations.append(violation_amount)
                affected_assets.append(asset)
                max_violation = max(max_violation, violation_amount)

        is_satisfied = len(violations) == 0
        limit_value = self.max_risk_contribution

        return ConstraintResult(
            constraint_name=self.name,
            constraint_type=self.constraint_type,
            is_satisfied=is_satisfied,
            current_value=current_max,
            limit_value=limit_value,
            violation_amount=max_violation,
            violation_percentage=(max_violation / limit_value * 100) if limit_value > 0 else float('inf'),
            affected_assets=affected_assets,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

    def get_bounds(self, num_assets: int) -> List[Tuple[float, float]]:
        return [(0.0, 1.0)] * num_assets

    def get_scipy_constraints(self, asset_names: List[str]) -> List[Dict]:
        return []  # 風險預算約束需要二次規劃，不適合簡單的線性約束

class ConstraintSystem:
    """
    投資組合約束系統

    Professional constraint management system with:
    - Multiple constraint types
    - Constraint validation
    - SciPy constraint generation
    - Constraint debugging and reporting
    """

    def __init__(self, config: Optional[ConstraintConfig] = None):
        """初始化約束系統"""
        self.config = config or ConstraintConfig()
        self.constraints: List[PortfolioConstraint] = []
        self.violations: List[ConstraintViolation] = []

        logger.info("Constraint System initialized")

    def add_constraint(self, constraint: PortfolioConstraint) -> None:
        """添加約束"""
        self.constraints.append(constraint)
        logger.info(f"Added constraint: {constraint.name} ({constraint.constraint_type})")

    def remove_constraint(self, constraint_name: str) -> None:
        """移除約束"""
        self.constraints = [c for c in self.constraints if c.name != constraint_name]
        logger.info(f"Removed constraint: {constraint_name}")

    def get_constraint(self, constraint_name: str) -> Optional[PortfolioConstraint]:
        """獲取約束"""
        for constraint in self.constraints:
            if constraint.name == constraint_name:
                return constraint
        return None

    def validate_portfolio(
        self,
        weights: np.ndarray,
        data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[ConstraintResult]]:
        """驗證投資組合是否滿足所有約束"""
        results = []
        all_satisfied = True

        for constraint in self.constraints:
            if constraint.is_active:
                result = constraint.check(weights, data)
                results.append(result)

                if not result.is_satisfied:
                    all_satisfied = False

                    # 記錄違規
                    violation = ConstraintViolation(
                        constraint_name=constraint.name,
                        violation_type="CONSTRAINT_VIOLATION",
                        severity="error",
                        description=f"{constraint.name} constraint violated",
                        current_value=result.current_value,
                        limit_value=result.limit_value,
                        suggested_fix=f"Adjust {', '.join(result.affected_assets)} weights"
                    )
                    self.violations.append(violation)

        return all_satisfied, results

    def generate_scipy_constraints(
        self,
        asset_names: List[str]
    ) -> Tuple[List[Dict], List[Tuple[float, float]]]:
        """生成SciPy優化約束"""
        all_constraints = []
        bounds_list = []

        # 收集所有約束
        for constraint in self.constraints:
            if constraint.is_active:
                # 獲取約束
                scipy_constraints = constraint.get_scipy_constraints(asset_names)
                all_constraints.extend(scipy_constraints)

                # 獲取邊界 (使用最嚴格的邊界)
                constraint_bounds = constraint.get_bounds(len(asset_names))
                if not bounds_list:
                    bounds_list = constraint_bounds
                else:
                    # 取最嚴格的邊界
                    bounds_list = [
                        (max(b1[0], b2[0]), min(b1[1], b2[1]))
                        for b1, b2 in zip(bounds_list, constraint_bounds)
                    ]

        # 添加基本的權重總和約束
        all_constraints.append({
            'type': 'eq',
            'fun': lambda weights: np.sum(weights) - 1.0
        })

        # 如果沒有邊界，使用默認邊界
        if not bounds_list:
            bounds_list = [(self.config.min_weight, self.config.max_weight)] * len(asset_names)

        return all_constraints, bounds_list

    def generate_constraint_report(
        self,
        weights: np.ndarray,
        data: Optional[Dict[str, Any]] = None,
        save_path: Optional[str] = None
    ) -> str:
        """生成約束檢查報告"""
        try:
            report_lines = []

            # 報告標題
            report_lines.append("=" * 60)
            report_lines.append("PORTFOLIO CONSTRAINT VALIDATION REPORT")
            report_lines.append("=" * 60)
            report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"Number of Constraints: {len(self.constraints)}")
            report_lines.append("")

            # 驗證所有約束
            is_valid, results = self.validate_portfolio(weights, data)

            # 總體結果
            report_lines.append("OVERALL RESULT")
            report_lines.append("-" * 16)
            if is_valid:
                report_lines.append("✓ All constraints satisfied")
            else:
                report_lines.append("✗ Some constraints violated")
            report_lines.append(f"Portfolio weights sum to: {np.sum(weights):.6f}")
            report_lines.append("")

            # 詳細約束檢查
            report_lines.append("CONSTRAINT DETAILS")
            report_lines.append("-" * 20)

            for result in results:
                if result.is_satisfied:
                    status = "✓ SATISFIED"
                else:
                    status = "✗ VIOLATED"

                report_lines.append(f"Constraint: {result.constraint_name} ({result.constraint_type})")
                report_lines.append(f"  Status: {status}")
                report_lines.append(f"  Current Value: {result.current_value:.6f}")
                report_lines.append(f"  Limit Value: {result.limit_value:.6f}")

                if not result.is_satisfied:
                    report_lines.append(f"  Violation Amount: {result.violation_amount:.6f}")
                    report_lines.append(f"  Violation Percentage: {result.violation_percentage:.2f}%")
                    if result.affected_assets:
                        report_lines.append(f"  Affected Assets: {', '.join(result.affected_assets[:5])}")
                        if len(result.affected_assets) > 5:
                            report_lines.append(f"    ... and {len(result.affected_assets) - 5} more")

                report_lines.append("")

            # 權重分析
            asset_names = data.get('asset_names', [f"Asset_{i}" for i in range(len(weights))])
            report_lines.append("WEIGHT ANALYSIS")
            report_lines.append("-" * 16)

            # 排序權重
            weight_data = list(zip(asset_names, weights))
            weight_data.sort(key=lambda x: x[1], reverse=True)

            report_lines.append("Top 10 Holdings:")
            for i, (asset, weight) in enumerate(weight_data[:10]):
                report_lines.append(f"  {i+1:2d}. {asset}: {weight:.4f} ({weight*100:.2f}%)")

            zero_weights = [(asset, weight) for asset, weight in weight_data if weight < 1e-6]
            if zero_weights:
                report_lines.append(f"\nZero-weight assets: {len(zero_weights)}")
                if len(zero_weights) <= 5:
                    for asset, _ in zero_weights:
                        report_lines.append(f"  - {asset}")
                else:
                    report_lines.append(f"  - {zero_weights[0][0]}, {zero_weights[1][0]}, {zero_weights[2][0]}, ... ({len(zero_weights)-3} more)")

            # 建議修復
            if not is_valid:
                report_lines.append("\nRECOMMENDATIONS")
                report_lines.append("-" * 16)

                for violation in self.violations[-5:]:  # 最近5個違規
                    report_lines.append(f"• {violation.description}")
                    report_lines.append(f"  Suggested fix: {violation.suggested_fix}")

            # 報告結尾
            report_lines.append("=" * 60)
            report_lines.append("END OF REPORT")
            report_lines.append("=" * 60)

            report_text = "\n".join(report_lines)

            # 保存報告
            if save_path:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                logger.info(f"Constraint report saved to {save_path}")

            return report_text

        except Exception as e:
            logger.error(f"Failed to generate constraint report: {e}")
            raise

    def clear_violations(self) -> None:
        """清除違規記錄"""
        self.violations.clear()

    def get_active_constraints(self) -> List[PortfolioConstraint]:
        """獲取活動約束"""
        return [c for c in self.constraints if c.is_active]

    def deactivate_constraint(self, constraint_name: str) -> None:
        """停用約束"""
        constraint = self.get_constraint(constraint_name)
        if constraint:
            constraint.is_active = False
            logger.info(f"Deactivated constraint: {constraint_name}")

    def activate_constraint(self, constraint_name: str) -> None:
        """啟用約束"""
        constraint = self.get_constraint(constraint_name)
        if constraint:
            constraint.is_active = True
            logger.info(f"Activated constraint: {constraint_name}")

# 便利函數
def create_basic_constraint_system(
    max_weight: float = 1.0,
    min_weight: float = 0.0,
    max_positions: Optional[int] = None
) -> ConstraintSystem:
    """創建基本約束系統"""
    config = ConstraintConfig(max_weight=max_weight, min_weight=min_weight)
    system = ConstraintSystem(config)

    # 添加權重邊界約束
    system.add_constraint(WeightBoundConstraint(min_weight=min_weight, max_weight=max_weight))

    # 添加持倉數量限制
    if max_positions is not None:
        system.add_constraint(PositionLimitConstraint(max_positions=max_positions))

    return system

def create_sector_constraint_system(
    sector_mapping: Dict[str, str],
    sector_limits: Dict[str, Tuple[float, float]],
    max_weight: float = 1.0
) -> ConstraintSystem:
    """創建行業約束系統"""
    system = create_basic_constraint_system(max_weight=max_weight)
    system.add_constraint(SectorConstraint(sector_mapping=sector_mapping, sector_limits=sector_limits))

    return system

def create_turnover_constraint_system(
    previous_weights: np.ndarray,
    max_turnover: float = 1.0
) -> ConstraintSystem:
    """創建周轉率約束系統"""
    system = create_basic_constraint_system()
    system.add_constraint(TurnoverConstraint(max_turnover=max_turnover, previous_weights=previous_weights))

    return system