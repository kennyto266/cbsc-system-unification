#!/usr/bin/env python3
"""
Automated Parameter Application System
自動參數應用系統 (Selection 4.B)

支援無縫參數部署:
- Configuration Updates: Auto-update strategy config files
- Live Deployment: Hot-swappable parameters without system restart
- Version Control: Track parameter changes with rollback capability
- Validation Pipeline: Automated testing before production deployment
"""

import json
import yaml
import shutil
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import asyncio
import threading
import time
import copy
from functools import lru_cache
import watchdog.observers
import watchdog.events

logger = logging.getLogger(__name__)

class ApplicationStatus(Enum):
    """應用狀態"""
    PENDING = "pending"
    VALIDATING = "validating"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class ValidationLevel(Enum):
    """驗證級別"""
    BASIC = "basic"           # 基本參數驗證
    COMPREHENSIVE = "comprehensive"  # 綜合驗證
    PRODUCTION = "production"  # 生產級驗證

@dataclass
class ParameterVersion:
    """參數版本"""
    version_id: str
    timestamp: datetime
    strategy_name: str
    parameters: Dict[str, Any]
    source: str  # 'optimization', 'manual', 'rollback'
    parent_version: Optional[str] = None
    validation_results: Dict[str, Any] = field(default_factory=dict)
    deployment_status: ApplicationStatus = ApplicationStatus.PENDING
    rollback_available: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeploymentConfig:
    """部署配置"""
    strategy_name: str
    config_paths: List[str]
    backup_enabled: bool = True
    validation_level: ValidationLevel = ValidationLevel.COMPREHENSIVE
    hot_reload_enabled: bool = True
    rollback_timeout_minutes: int = 30
    monitoring_enabled: bool = True
    test_mode: bool = False

class ConfigManager:
    """配置管理器"""

    def __init__(self, config_root: str = "config/strategies"):
        self.config_root = Path(config_root)
        self.config_root.mkdir(parents=True, exist_ok=True)
        self.backup_root = self.config_root / "backups"
        self.backup_root.mkdir(exist_ok=True)

    def read_config(self, strategy_name: str) -> Dict[str, Any]:
        """讀取策略配置"""
        config_path = self.config_root / f"{strategy_name}.json"

        if not config_path.exists():
            # 嘗試YAML格式
            yaml_path = self.config_root / f"{strategy_name}.yaml"
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)

            # 返回默認配置
            return self._get_default_config(strategy_name)

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def write_config(self, strategy_name: str, config: Dict[str, Any],
                    create_backup: bool = True) -> str:
        """寫入策略配置"""
        config_path = self.config_root / f"{strategy_name}.json"

        # 創建備份
        if create_backup and config_path.exists():
            backup_path = self.backup_root / f"{strategy_name}_{int(time.time())}.json"
            shutil.copy2(config_path, backup_path)

        # 寫入新配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return str(config_path)

    def _get_default_config(self, strategy_name: str) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            "strategy_name": strategy_name,
            "parameters": {},
            "risk_management": {
                "max_position_size": 0.1,
                "stop_loss": 0.05,
                "take_profit": 0.1
            },
            "execution": {
                "execution_delay": 0,
                "slippage_tolerance": 0.001
            },
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        }

class ParameterValidator:
    """參數驗證器"""

    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()

    def _initialize_validation_rules(self) -> Dict[str, Callable]:
        """初始化驗證規則"""
        return {
            'range_validation': self._validate_range,
            'type_validation': self._validate_type,
            'dependency_validation': self._validate_dependencies,
            'business_rules': self._validate_business_rules,
            'performance_validation': self._validate_performance_impact
        }

    def validate_parameters(self,
                          parameters: Dict[str, Any],
                          strategy_name: str,
                          validation_level: ValidationLevel = ValidationLevel.COMPREHENSIVE) -> Dict[str, Any]:
        """驗證參數"""

        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'validation_level': validation_level.value,
            'validation_time': datetime.now().isoformat(),
            'detailed_checks': {}
        }

        # 基本驗證
        if validation_level in [ValidationLevel.BASIC, ValidationLevel.COMPREHENSIVE, ValidationLevel.PRODUCTION]:
            self._run_basic_validation(parameters, strategy_name, validation_results)

        # 綜合驗證
        if validation_level in [ValidationLevel.COMPREHENSIVE, ValidationLevel.PRODUCTION]:
            self._run_comprehensive_validation(parameters, strategy_name, validation_results)

        # 生產級驗證
        if validation_level == ValidationLevel.PRODUCTION:
            self._run_production_validation(parameters, strategy_name, validation_results)

        validation_results['is_valid'] = len(validation_results['errors']) == 0

        return validation_results

    def _run_basic_validation(self, parameters: Dict[str, Any],
                           strategy_name: str, results: Dict[str, Any]) -> None:
        """運行基本驗證"""
        # 類型驗證
        type_errors = self.validation_rules['type_validation'](parameters)
        results['errors'].extend(type_errors)

        # 範圍驗證
        range_errors = self.validation_rules['range_validation'](parameters)
        results['errors'].extend(range_errors)

        results['detailed_checks']['basic'] = {
            'type_validation_passed': len(type_errors) == 0,
            'range_validation_passed': len(range_errors) == 0
        }

    def _run_comprehensive_validation(self, parameters: Dict[str, Any],
                                    strategy_name: str, results: Dict[str, Any]) -> None:
        """運行綜合驗證"""
        # 依賴關係驗證
        dependency_errors = self.validation_rules['dependency_validation'](parameters)
        results['errors'].extend(dependency_errors)

        # 業務規則驗證
        business_warnings = self.validation_rules['business_rules'](parameters, strategy_name)
        results['warnings'].extend(business_warnings)

        results['detailed_checks']['comprehensive'] = {
            'dependency_validation_passed': len(dependency_errors) == 0,
            'business_rules_warnings': len(business_warnings)
        }

    def _run_production_validation(self, parameters: Dict[str, Any],
                                 strategy_name: str, results: Dict[str, Any]) -> None:
        """運行生產級驗證"""
        # 性能影響驗證
        performance_warnings = self.validation_rules['performance_validation'](parameters, strategy_name)
        results['warnings'].extend(performance_warnings)

        # 生產環境特殊檢查
        production_warnings = self._validate_production_requirements(parameters, strategy_name)
        results['warnings'].extend(production_warnings)

        results['detailed_checks']['production'] = {
            'performance_validation_passed': len(performance_warnings) == 0,
            'production_requirements_passed': len(production_warnings) == 0
        }

    def _validate_type(self, parameters: Dict[str, Any]) -> List[str]:
        """驗證參數類型"""
        errors = []
        type_rules = {
            'rsi_period': int,
            'rsi_oversold': (int, float),
            'rsi_overbought': (int, float),
            'stop_loss_pct': (int, float),
            'take_profit_pct': (int, float),
            'leverage_ratio': (int, float),
            'max_position_size': (int, float)
        }

        for param_name, expected_type in type_rules.items():
            if param_name in parameters:
                value = parameters[param_name]
                if not isinstance(value, expected_type):
                    errors.append(f"Parameter {param_name} should be {expected_type}, got {type(value)}")

        return errors

    def _validate_range(self, parameters: Dict[str, Any]) -> List[str]:
        """驗證參數範圍"""
        errors = []
        range_rules = {
            'rsi_period': (5, 50),
            'rsi_oversold': (10, 40),
            'rsi_overbought': (60, 90),
            'stop_loss_pct': (0.5, 20.0),
            'take_profit_pct': (1.0, 50.0),
            'leverage_ratio': (1.0, 10.0),
            'max_position_size': (0.01, 1.0)
        }

        for param_name, (min_val, max_val) in range_rules.items():
            if param_name in parameters:
                value = parameters[param_name]
                if value < min_val or value > max_val:
                    errors.append(f"Parameter {param_name} value {value} outside range [{min_val}, {max_val}]")

        return errors

    def _validate_dependencies(self, parameters: Dict[str, Any]) -> List[str]:
        """驗證參數依賴關係"""
        errors = []

        # RSI相關依賴
        if 'rsi_period' in parameters:
            rsi_period = parameters['rsi_period']
            if rsi_period < 14 and 'rsi_oversold' in parameters and parameters['rsi_oversold'] > 25:
                errors.append("RSI period < 14 should have oversold level <= 25")
            if rsi_period < 14 and 'rsi_overbought' in parameters and parameters['rsi_overbought'] < 75:
                errors.append("RSI period < 14 should have overbought level >= 75")

        # 止損止盈依賴
        if 'stop_loss_pct' in parameters and 'take_profit_pct' in parameters:
            stop_loss = parameters['stop_loss_pct']
            take_profit = parameters['take_profit_pct']
            if take_profit <= stop_loss:
                errors.append("Take profit should be greater than stop loss")

        # 槓桿和倉位依賴
        if 'leverage_ratio' in parameters and 'max_position_size' in parameters:
            leverage = parameters['leverage_ratio']
            max_position = parameters['max_position_size']
            if leverage * max_position > 2.0:
                errors.append("Leverage * max_position_size should not exceed 2.0")

        return errors

    def _validate_business_rules(self, parameters: Dict[str, Any], strategy_name: str) -> List[str]:
        """驗證業務規則"""
        warnings = []

        # 保守性檢查
        if 'leverage_ratio' in parameters and parameters['leverage_ratio'] > 3.0:
            warnings.append("High leverage ratio (>3.0) increases risk")

        if 'stop_loss_pct' in parameters and parameters['stop_loss_pct'] > 10.0:
            warnings.append("Large stop loss (>10%) may result in significant losses")

        if 'rsi_period' in parameters and parameters['rsi_period'] > 30:
            warnings.append("Long RSI period (>30) may reduce signal frequency")

        return warnings

    def _validate_performance_impact(self, parameters: Dict[str, Any], strategy_name: str) -> List[str]:
        """驗證性能影響"""
        warnings = []

        # 複雜度評估
        complexity_score = self._calculate_parameter_complexity(parameters)
        if complexity_score > 10:
            warnings.append(f"High parameter complexity ({complexity_score}) may impact performance")

        return warnings

    def _validate_production_requirements(self, parameters: Dict[str, Any], strategy_name: str) -> List[str]:
        """驗證生產環境要求"""
        warnings = []

        # 生產環境安全性檢查
        if 'leverage_ratio' in parameters and parameters['leverage_ratio'] > 5.0:
            warnings.append("Leverage >5.0 not recommended for production")

        # 風險管理檢查
        required_risk_params = ['stop_loss_pct', 'max_position_size']
        missing_params = [p for p in required_risk_params if p not in parameters]
        if missing_params:
            warnings.append(f"Missing risk management parameters: {missing_params}")

        return warnings

    def _calculate_parameter_complexity(self, parameters: Dict[str, Any]) -> float:
        """計算參數複雜度"""
        complexity = 0.0
        for param_name, value in parameters.items():
            if isinstance(value, (int, float)):
                complexity += 1.0
            elif isinstance(value, bool):
                complexity += 0.5
            elif isinstance(value, str):
                complexity += 0.3
            elif isinstance(value, (list, dict)):
                complexity += 2.0
        return complexity

class DeploymentEngine:
    """部署引擎"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.active_deployments = {}
        self.rollback_timers = {}

    async def deploy_parameters(self,
                              strategy_name: str,
                              parameters: Dict[str, Any],
                              deployment_config: DeploymentConfig,
                              version_id: str) -> bool:
        """部署參數"""

        logger.info(f"Deploying parameters for strategy {strategy_name}")

        try:
            # 1. 驗證參數
            validator = ParameterValidator()
            validation_results = validator.validate_parameters(
                parameters, strategy_name, deployment_config.validation_level
            )

            if not validation_results['is_valid']:
                logger.error(f"Parameter validation failed: {validation_results['errors']}")
                return False

            # 2. 讀取現有配置
            current_config = self.config_manager.read_config(strategy_name)

            # 3. 創建新配置
            new_config = self._merge_parameters(current_config, parameters)
            new_config['metadata'] = {
                'last_updated': datetime.now().isoformat(),
                'updated_by': 'auto_applicator',
                'version_id': version_id,
                'validation_results': validation_results
            }

            # 4. 備份當前配置
            if deployment_config.backup_enabled:
                backup_path = self._create_deployment_backup(strategy_name, current_config, version_id)
                logger.info(f"Created backup at {backup_path}")

            # 5. 寫入新配置
            config_path = self.config_manager.write_config(strategy_name, new_config)

            # 6. 熱部署 (如果啟用)
            if deployment_config.hot_reload_enabled:
                hot_reload_success = await self._perform_hot_reload(strategy_name, new_config)
                if not hot_reload_success:
                    logger.warning("Hot reload failed, but config was updated")
            else:
                logger.info("Hot reload disabled, restart required to apply changes")

            # 7. 設置回滾定時器
            if deployment_config.rollback_timeout_minutes > 0:
                self._set_rollback_timer(strategy_name, version_id, deployment_config.rollback_timeout_minutes)

            # 8. 記錄部署
            self.active_deployments[strategy_name] = {
                'version_id': version_id,
                'deployed_at': datetime.now(),
                'config_path': config_path,
                'validation_results': validation_results,
                'deployment_config': deployment_config
            }

            logger.info(f"Successfully deployed parameters for strategy {strategy_name}")
            return True

        except Exception as e:
            logger.error(f"Deployment failed for strategy {strategy_name}: {e}")
            return False

    async def rollback_parameters(self, strategy_name: str, target_version_id: str) -> bool:
        """回滾參數"""

        logger.info(f"Rolling back strategy {strategy_name} to version {target_version_id}")

        try:
            # 查找備份配置
            backup_config = self._find_backup_config(strategy_name, target_version_id)
            if not backup_config:
                logger.error(f"Backup config not found for version {target_version_id}")
                return False

            # 讀取當前配置並創建回滾前的備份
            current_config = self.config_manager.read_config(strategy_name)
            rollback_backup_id = f"rollback_{int(time.time())}"
            self._create_deployment_backup(strategy_name, current_config, rollback_backup_id)

            # 還原配置
            config_path = self.config_manager.write_config(strategy_name, backup_config, create_backup=False)

            # 熱部署回滾
            hot_reload_success = await self._perform_hot_reload(strategy_name, backup_config)

            # 清除回滾定時器
            if strategy_name in self.rollback_timers:
                self.rollback_timers[strategy_name].cancel()
                del self.rollback_timers[strategy_name]

            logger.info(f"Successfully rolled back strategy {strategy_name} to version {target_version_id}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed for strategy {strategy_name}: {e}")
            return False

    def _merge_parameters(self, current_config: Dict[str, Any], new_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """合併參數到現有配置"""
        merged_config = copy.deepcopy(current_config)

        # 更新參數
        if 'parameters' not in merged_config:
            merged_config['parameters'] = {}

        merged_config['parameters'].update(new_parameters)

        # 確保必要欄位存在
        if 'risk_management' not in merged_config:
            merged_config['risk_management'] = {}

        if 'execution' not in merged_config:
            merged_config['execution'] = {}

        return merged_config

    def _create_deployment_backup(self, strategy_name: str, config: Dict[str, Any], version_id: str) -> str:
        """創建部署備份"""
        backup_dir = self.config_manager.backup_root / strategy_name
        backup_dir.mkdir(exist_ok=True)

        backup_filename = f"{version_id}.json"
        backup_path = backup_dir / backup_filename

        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return str(backup_path)

    def _find_backup_config(self, strategy_name: str, version_id: str) -> Optional[Dict[str, Any]]:
        """查找備份配置"""
        backup_path = self.config_manager.backup_root / strategy_name / f"{version_id}.json"

        if backup_path.exists():
            with open(backup_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        return None

    async def _perform_hot_reload(self, strategy_name: str, config: Dict[str, Any]) -> bool:
        """執行熱重載"""
        try:
            # 這裡應該實現實際的熱重載邏輯
            # 例如：發送信號到運行中的策略進程，調用重載API等

            # 模擬熱重載
            logger.info(f"Performing hot reload for strategy {strategy_name}")
            await asyncio.sleep(0.1)  # 模擬重載時間

            # 這裡應該檢查重載是否成功
            return True

        except Exception as e:
            logger.error(f"Hot reload failed for strategy {strategy_name}: {e}")
            return False

    def _set_rollback_timer(self, strategy_name: str, version_id: str, timeout_minutes: int):
        """設置回滾定時器"""
        if strategy_name in self.rollback_timers:
            self.rollback_timers[strategy_name].cancel()

        async def rollback_callback():
            await asyncio.sleep(timeout_minutes * 60)
            logger.warning(f"Automatic rollback triggered for {strategy_name} (version {version_id})")
            await self.rollback_parameters(strategy_name, version_id)

        self.rollback_timers[strategy_name] = asyncio.create_task(rollback_callback())

class ParameterAutoApplication:
    """自動參數應用系統主類"""

    def __init__(self, config_root: str = "config/strategies"):
        self.config_manager = ConfigManager(config_root)
        self.validator = ParameterValidator()
        self.deployment_engine = DeploymentEngine(self.config_manager)
        self.parameter_versions = {}  # version_id -> ParameterVersion

    async def apply_optimal_parameters(self,
                                     strategy_name: str,
                                     optimal_parameters: Dict[str, Any],
                                     source: str = "optimization",
                                     validation_level: ValidationLevel = ValidationLevel.COMPREHENSIVE,
                                     auto_deploy: bool = True) -> Tuple[bool, str]:
        """應用最佳參數"""

        # 1. 驗證參數
        validation_results = self.validator.validate_parameters(
            optimal_parameters, strategy_name, validation_level
        )

        if not validation_results['is_valid']:
            logger.error(f"Parameter validation failed: {validation_results['errors']}")
            return False, f"Validation failed: {validation_results['errors']}"

        # 2. 創建版本
        version_id = self._create_version_id(strategy_name, optimal_parameters)
        parameter_version = ParameterVersion(
            version_id=version_id,
            timestamp=datetime.now(),
            strategy_name=strategy_name,
            parameters=optimal_parameters,
            source=source,
            validation_results=validation_results,
            metadata={'auto_deploy': auto_deploy}
        )

        self.parameter_versions[version_id] = parameter_version

        # 3. 自動部署
        if auto_deploy:
            deployment_config = DeploymentConfig(
                strategy_name=strategy_name,
                config_paths=[],
                validation_level=validation_level,
                hot_reload_enabled=True,
                monitoring_enabled=True
            )

            deployment_success = await self.deployment_engine.deploy_parameters(
                strategy_name, optimal_parameters, deployment_config, version_id
            )

            if deployment_success:
                parameter_version.deployment_status = ApplicationStatus.DEPLOYED
                parameter_version.rollback_available = True
            else:
                parameter_version.deployment_status = ApplicationStatus.FAILED

            return deployment_success, version_id

        return True, version_id

    async def rollback_parameters(self, strategy_name: str, version_id: str) -> bool:
        """回滾參數到指定版本"""
        if version_id not in self.parameter_versions:
            logger.error(f"Version {version_id} not found")
            return False

        rollback_success = await self.deployment_engine.rollback_parameters(strategy_name, version_id)

        if rollback_success:
            # 更新版本狀態
            current_version = self._get_current_version(strategy_name)
            if current_version:
                current_version.deployment_status = ApplicationStatus.ROLLED_BACK

            logger.info(f"Successfully rolled back {strategy_name} to version {version_id}")

        return rollback_success

    def _create_version_id(self, strategy_name: str, parameters: Dict[str, Any]) -> str:
        """創建版本ID"""
        content = f"{strategy_name}_{json.dumps(parameters, sort_keys=True)}_{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_current_version(self, strategy_name: str) -> Optional[ParameterVersion]:
        """獲取當前版本"""
        for version in self.parameter_versions.values():
            if (version.strategy_name == strategy_name and
                version.deployment_status == ApplicationStatus.DEPLOYED):
                return version
        return None

    def get_parameter_history(self, strategy_name: str) -> List[ParameterVersion]:
        """獲取參數歷史"""
        versions = [
            version for version in self.parameter_versions.values()
            if version.strategy_name == strategy_name
        ]
        versions.sort(key=lambda v: v.timestamp, reverse=True)
        return versions

    def get_deployment_status(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """獲取部署狀態"""
        current_version = self._get_current_version(strategy_name)
        if current_version:
            return {
                'version_id': current_version.version_id,
                'deployment_status': current_version.deployment_status.value,
                'deployed_at': current_version.timestamp.isoformat(),
                'rollback_available': current_version.rollback_available,
                'validation_results': current_version.validation_results
            }
        return None

# 全局實例
_auto_applicator = None

def get_parameter_applicator(config_root: str = "config/strategies") -> ParameterAutoApplication:
    """獲取參數應用器實例"""
    global _auto_applicator
    if _auto_applicator is None:
        _auto_applicator = ParameterAutoApplication(config_root)
    return _auto_applicator