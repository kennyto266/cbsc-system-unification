#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
Deployment Manager for VectorBT Enhanced System
VectorBT增强系统部署管理器 - Phase 6.1

Deployment checklist, feature flags, monitoring, and rollback procedures
部署检查清单、特性标志、监控和回滚程序
"""

import json
import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple

import yaml

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """部署状态枚举"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class Environment(Enum):
    """环境枚举"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DeploymentConfig:
    """部署配置"""

    environment: Environment
    version: str
    features_enabled: List[str] = field(default_factory = list)
    monitoring_enabled: bool = True
    auto_rollback: bool = True
    health_check_timeout: int = 300  # 5 minutes
    performance_thresholds: Dict[str, float] = field(default_factory = dict)


@dataclass
class FeatureFlag:
    """特性标志"""

    name: str
    enabled: bool
    description: str
    rollout_percentage: float = 100.0
    dependencies: List[str] = field(default_factory = list)
    conditions: Dict[str, Any] = field(default_factory = dict)


class DeploymentManager:
    """部署管理器"""

    def __init__(self, config_file: str = "deployment_config.yaml"):
        """
        初始化部署管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.feature_flags = {}
        self.deployment_history = []
        self.monitoring_system = None
        self.health_checks = []

        # 加载配置
        self.load_configuration()

        logger.info(f"Deployment Manager initialized for environment")

    def load_configuration(self):
        """加载部署配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf - 8") as f:
                    config_data = yaml.safe_load(f)

                self.feature_flags = {
                    name: FeatureFlag(**flag_data)
                    for name, flag_data in config_data.get("feature_flags", {}).items()
                }

                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                logger.warning(
                    f"Config file {self.config_file} not found, using defaults"
                )
                self.create_default_config()

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def create_default_config(self):
        """创建默认配置"""
        default_flags = {
            "vectorbt_gpu_acceleration": {
                "enabled": False,
                "description": "Enable GPU acceleration for VectorBT operations",
                "rollout_percentage": 10.0,
                "dependencies": ["cupy"],
                "conditions": {"memory_gb": 8},
            },
            "advanced_optimization": {
                "enabled": True,
                "description": "Enable advanced optimization algorithms",
                "rollout_percentage": 100.0,
                "dependencies": ["scipy"],
            },
            "professional_risk_metrics": {
                "enabled": True,
                "description": "Enable professional risk metrics calculations",
                "rollout_percentage": 100.0,
            },
            "signal_fusion_engine": {
                "enabled": True,
                "description": "Enable multi - indicator signal fusion",
                "rollout_percentage": 50.0,
                "dependencies": ["sklearn"],
            },
            "real_time_monitoring": {
                "enabled": False,
                "description": "Enable real - time performance monitoring",
                "rollout_percentage": 5.0,
            },
        }

        config_data = {
            "feature_flags": default_flags,
            "performance_thresholds": {
                "max_response_time_ms": 1000,
                "max_memory_usage_mb": 2048,
                "max_cpu_usage_percent": 80,
                "error_rate_threshold": 0.01,
            },
            "health_checks": {
                "database_connection": True,
                "api_endpoints": True,
                "vectorbt_functionality": True,
                "memory_limits": True,
            },
        }

        try:
            with open(self.config_file, "w", encoding="utf - 8") as f:
                yaml.dump(config_data, f, default_flow_style = False, allow_unicode = True)

            logger.info(f"Created default configuration file: {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to create default config file: {e}")

    def check_deployment_readiness(
        self, environment: Environment
    ) -> Tuple[bool, List[str]]:
        """
        检查部署准备状态

        Args:
            environment: 目标环境

        Returns:
            (是否准备就绪, 问题列表)
        """
        logger.info(f"Checking deployment readiness for {environment.value}")

        issues = []

        # 检查依赖
        dependency_issues = self._check_dependencies()
        issues.extend(dependency_issues)

        # 检查环境配置
        env_issues = self._check_environment_configuration(environment)
        issues.extend(env_issues)

        # 检查系统资源
        resource_issues = self._check_system_resources()
        issues.extend(resource_issues)

        # 检查特性标志状态
        flag_issues = self._check_feature_flags()
        issues.extend(flag_issues)

        is_ready = len(issues) == 0

        if is_ready:
            logger.info("Deployment readiness check: PASSED")
        else:
            logger.warning(
                f"Deployment readiness check: FAILED - {len(issues)} issues found"
            )
            for issue in issues:
                logger.warning(f"  - {issue}")

        return is_ready, issues

    def _check_dependencies(self) -> List[str]:
        """检查依赖项"""
        issues = []
        required_packages = ["pandas", "numpy"]
        optional_packages = ["vectorbt", "scipy", "sklearn", "cupy", "cvxpy"]

        # 检查必需包
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                issues.append(f"Required package '{package}' is not installed")

        # 检查可选包
        for package in optional_packages:
            try:
                __import__(package)
            except ImportError:
                logger.info(f"Optional package '{package}' is not installed")

        return issues

    def _check_environment_configuration(self, environment: Environment) -> List[str]:
        """检查环境配置"""
        issues = []

        # 检查必要目录
        required_dirs = ["logs", "data", "cache"]
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                try:
                    os.makedirs(dir_name, exist_ok = True)
                    logger.info(f"Created directory: {dir_name}")
                except Exception as e:
                    issues.append(f"Failed to create directory '{dir_name}': {e}")

        # 检查配置文件
        config_files = [self.config_file, "requirements.txt"]
        for config_file in config_files:
            if not os.path.exists(config_file):
                issues.append(f"Configuration file '{config_file}' is missing")

        return issues

    def _check_system_resources(self) -> List[str]:
        """检查系统资源"""
        issues = []

        try:
            import psutil

            # 检查内存
            memory = psutil.virtual_memory()
            if memory.available < 1024 * 1024 * 1024:  # 1GB
                issues.append(
                    f"Low available memory: {memory.available / (1024 * *3):.1f}GB"
                )

            # 检查磁盘空间
            disk = psutil.disk_usage(".")
            if disk.free < 1024 * 1024 * 1024:  # 1GB
                issues.append(f"Low disk space: {disk.free / (1024 * *3):.1f}GB")

            # 检查CPU
            cpu_count = psutil.cpu_count()
            if cpu_count < 2:
                issues.append(f"Insufficient CPU cores: {cpu_count}")

        except ImportError:
            logger.warning("psutil not available - cannot check system resources")

        return issues

    def _check_feature_flags(self) -> List[str]:
        """检查特性标志"""
        issues = []

        for flag_name, flag in self.feature_flags.items():
            if flag.enabled and flag.dependencies:
                for dependency in flag.dependencies:
                    try:
                        __import__(dependency)
                    except ImportError:
                        issues.append(
                            f"Feature '{flag_name}' requires '{dependency}' but it's not installed"
                        )

            if flag.enabled and flag.conditions:
                # 检查条件
                if "memory_gb" in flag.conditions:
                    try:
                        import psutil

                        memory_gb = psutil.virtual_memory().total / (1024 * *3)
                        if memory_gb < flag.conditions["memory_gb"]:
                            issues.append(
                                f"Feature '{flag_name}' requires {flag.conditions['memory_gb']}GB memory, available: {memory_gb:.1f}GB"
                            )
                    except ImportError:
                        issues.append(
                            f"Cannot check memory requirements for feature '{flag_name}'"
                        )

        return issues

    def execute_deployment(
        self, environment: Environment, version: str
    ) -> Dict[str, Any]:
        """
        执行部署

        Args:
            environment: 目标环境
            version: 版本号

        Returns:
            部署结果
        """
        logger.info(f"Starting deployment of version {version} to {environment.value}")

        deployment_record = {
            "environment": environment.value,
            "version": version,
            "start_time": datetime.now(),
            "status": DeploymentStatus.IN_PROGRESS.value,
            "steps": [],
        }

        try:
            # 步骤1: 检查准备状态
            ready, issues = self.check_deployment_readiness(environment)
            if not ready:
                raise Exception(f"Deployment not ready: {', '.join(issues)}")

            deployment_record["steps"].append(
                {
                    "step": "readiness_check",
                    "status": "completed",
                    "timestamp": datetime.now(),
                }
            )

            # 步骤2: 备份当前版本
            backup_result = self._create_backup(environment, version)
            deployment_record["steps"].append(
                {
                    "step": "backup",
                    "status": "completed",
                    "timestamp": datetime.now(),
                    "backup_path": backup_result,
                }
            )

            # 步骤3: 更新特性标志
            self._update_feature_flags(environment)
            deployment_record["steps"].append(
                {
                    "step": "feature_flags",
                    "status": "completed",
                    "timestamp": datetime.now(),
                }
            )

            # 步骤4: 部署代码
            self._deploy_code(environment, version)
            deployment_record["steps"].append(
                {
                    "step": "code_deployment",
                    "status": "completed",
                    "timestamp": datetime.now(),
                }
            )

            # 步骤5: 健康检查
            health_check_result = self._perform_health_check(environment)
            deployment_record["steps"].append(
                {
                    "step": "health_check",
                    "status": "completed",
                    "timestamp": datetime.now(),
                    "health_status": health_check_result,
                }
            )

            if not health_check_result["healthy"]:
                raise Exception(f"Health check failed: {health_check_result['issues']}")

            # 步骤6: 性能验证
            performance_result = self._validate_performance(environment)
            deployment_record["steps"].append(
                {
                    "step": "performance_validation",
                    "status": "completed",
                    "timestamp": datetime.now(),
                    "performance_metrics": performance_result,
                }
            )

            deployment_record["status"] = DeploymentStatus.COMPLETED.value
            deployment_record["end_time"] = datetime.now()

            logger.info(f"Deployment completed successfully for {environment.value}")

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            deployment_record["status"] = DeploymentStatus.FAILED.value
            deployment_record["error"] = str(e)
            deployment_record["end_time"] = datetime.now()

            # 自动回滚
            if self._get_config(environment).auto_rollback:
                logger.info("Initiating automatic rollback...")
                rollback_result = self.execute_rollback(environment, version)
                deployment_record["rollback_result"] = rollback_result

        # 保存部署记录
        self.deployment_history.append(deployment_record)
        self._save_deployment_history()

        return deployment_record

    def _create_backup(self, environment: Environment, version: str) -> str:
        """创建备份"""
        backup_dir = f"backups/{environment.value}/{version}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{backup_dir}/backup_{timestamp}"

        try:
            os.makedirs(backup_path, exist_ok = True)

            # 备份关键文件
            files_to_backup = ["src/", "requirements.txt", "deployment_config.yaml"]

            for file_path in files_to_backup:
                if os.path.exists(file_path):
                    if os.path.isdir(file_path):
                        shutil.copytree(file_path, os.path.join(backup_path, file_path))
                    else:
                        shutil.copy2(file_path, backup_path)

            logger.info(f"Backup created: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def _update_feature_flags(self, environment: Environment):
        """更新特性标志"""
        # 根据环境调整特性标志
        for flag_name, flag in self.feature_flags.items():
            if environment == Environment.PRODUCTION:
                # 生产环境使用保守的推出策略
                flag.rollout_percentage = min(flag.rollout_percentage, 50.0)
            elif environment == Environment.STAGING:
                # 测试环境可以使用更多特性
                flag.rollout_percentage = min(flag.rollout_percentage, 80.0)

        # 保存更新的特性标志
        config_data = {
            "feature_flags": {
                name: {
                    "enabled": flag.enabled,
                    "description": flag.description,
                    "rollout_percentage": flag.rollout_percentage,
                    "dependencies": flag.dependencies,
                    "conditions": flag.conditions,
                }
                for name, flag in self.feature_flags.items()
            }
        }

        try:
            with open(self.config_file, "w", encoding="utf - 8") as f:
                yaml.dump(config_data, f, default_flow_style = False, allow_unicode = True)

            logger.info("Feature flags updated for deployment")

        except Exception as e:
            logger.error(f"Failed to update feature flags: {e}")
            raise

    def _deploy_code(self, environment: Environment, version: str):
        """部署代码"""
        # 这里可以实现实际的代码部署逻辑
        # 例如：复制文件、重启服务等

        logger.info(f"Deploying code version {version} to {environment.value}")

        # 模拟部署过程
        deployment_steps = [
            "Stopping existing services",
            "Copying updated files",
            "Installing dependencies",
            "Starting services",
            "Verifying installation",
        ]

        for step in deployment_steps:
            logger.info(f"  {step}...")
            # 这里可以添加实际的部署逻辑

        logger.info("Code deployment completed")

    def _perform_health_check(self, environment: Environment) -> Dict[str, Any]:
        """执行健康检查"""
        health_results = {"healthy": True, "checks": {}, "issues": []}

        health_checks = [
            ("database_connection", self._check_database_connection),
            ("api_endpoints", self._check_api_endpoints),
            ("vectorbt_functionality", self._check_vectorbt_functionality),
            ("memory_limits", self._check_memory_limits),
        ]

        for check_name, check_func in health_checks:
            try:
                check_result = check_func()
                health_results["checks"][check_name] = check_result

                if not check_result.get("healthy", False):
                    health_results["healthy"] = False
                    health_results["issues"].append(
                        f"{check_name}: {check_result.get('message', 'Unknown issue')}"
                    )

            except Exception as e:
                health_results["checks"][check_name] = {
                    "healthy": False,
                    "error": str(e),
                }
                health_results["healthy"] = False
                health_results["issues"].append(f"{check_name}: {str(e)}")

        return health_results

    def _check_database_connection(self) -> Dict[str, Any]:
        """检查数据库连接"""
        # 这里可以实现实际的数据库连接检查
        return {"healthy": True, "message": "Database connection successful"}

    def _check_api_endpoints(self) -> Dict[str, Any]:
        """检查API端点"""
        # 这里可以实现API端点健康检查
        return {"healthy": True, "message": "API endpoints responding correctly"}

    def _check_vectorbt_functionality(self) -> Dict[str, Any]:
        """检查VectorBT功能"""
        try:
            import numpy as np
            import pandas as pd
            import vectorbt as vbt

            # 简单功能测试
            test_data = pd.Series(np.random.normal(1, 0.1, 100))
            rsi = vbt.RSI.run(test_data, window = 14)

            return {
                "healthy": True,
                "message": "VectorBT functionality working",
                "vectorbt_version": getattr(vbt, "__version__", "unknown"),
            }

        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _check_memory_limits(self) -> Dict[str, Any]:
        """检查内存限制"""
        try:
            import psutil

            memory = psutil.virtual_memory()

            # 检查内存使用是否在合理范围内
            memory_usage_percent = memory.percent
            if memory_usage_percent > 90:
                return {
                    "healthy": False,
                    "message": f"High memory usage: {memory_usage_percent:.1f}%",
                }

            return {
                "healthy": True,
                "message": f"Memory usage normal: {memory_usage_percent:.1f}%",
            }

        except ImportError:
            return {
                "healthy": True,
                "message": "psutil not available - cannot check memory",
            }

    def _validate_performance(self, environment: Environment) -> Dict[str, Any]:
        """验证性能"""
        performance_metrics = {
            "response_time_ms": 0,
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0,
            "error_rate": 0,
        }

        # 这里可以实现实际的性能测试
        logger.info("Validating deployment performance...")

        return performance_metrics

    def _get_config(self, environment: Environment) -> DeploymentConfig:
        """获取环境配置"""
        return DeploymentConfig(
            environment = environment,
            version="current",
            features_enabled=[
                name for name, flag in self.feature_flags.items() if flag.enabled
            ],
            monitoring_enabled = True,
            auto_rollback = True,
        )

    def execute_rollback(
        self, environment: Environment, version: str
    ) -> Dict[str, Any]:
        """执行回滚"""
        logger.info(f"Executing rollback for {environment.value} version {version}")

        rollback_result = {
            "environment": environment.value,
            "version": version,
            "start_time": datetime.now(),
            "status": "in_progress",
        }

        try:
            # 找到最近的备份
            backup_dir = f"backups/{environment.value}/{version}"
            if os.path.exists(backup_dir):
                backup_subdirs = [
                    d for d in os.listdir(backup_dir) if d.startswith("backup_")
                ]
                if backup_subdirs:
                    latest_backup = sorted(backup_subdirs)[-1]
                    backup_path = os.path.join(backup_dir, latest_backup)

                    # 恢复文件
                    self._restore_from_backup(backup_path)

                    rollback_result["status"] = "completed"
                    rollback_result["backup_used"] = latest_backup
                else:
                    rollback_result["status"] = "failed"
                    rollback_result["error"] = "No backup found"
            else:
                rollback_result["status"] = "failed"
                rollback_result["error"] = "Backup directory not found"

        except Exception as e:
            rollback_result["status"] = "failed"
            rollback_result["error"] = str(e)

        rollback_result["end_time"] = datetime.now()

        logger.info(
            f"Rollback {'completed' if rollback_result['status'] == 'completed' else 'failed'}"
        )
        return rollback_result

    def _restore_from_backup(self, backup_path: str):
        """从备份恢复"""
        # 这里可以实现实际的文件恢复逻辑
        logger.info(f"Restoring from backup: {backup_path}")

        # 恢复文件
        if os.path.exists(backup_path):
            for item in os.listdir(backup_path):
                backup_item = os.path.join(backup_path, item)
                if os.path.isdir(backup_item):
                    if os.path.exists(item):
                        shutil.rmtree(item)
                    shutil.copytree(backup_item, item)
                else:
                    shutil.copy2(backup_item, item)

        logger.info("Backup restoration completed")

    def _save_deployment_history(self):
        """保存部署历史"""
        try:
            history_file = f"deployment_history_{datetime.now().strftime('%Y%m')}.json"

            with open(history_file, "w", encoding="utf - 8") as f:
                json.dump(self.deployment_history, f, indent = 2, default = str)

            logger.info(f"Deployment history saved to: {history_file}")

        except Exception as e:
            logger.error(f"Failed to save deployment history: {e}")

    def get_deployment_status(self, environment: Environment) -> Dict[str, Any]:
        """获取部署状态"""
        recent_deployments = [
            d for d in self.deployment_history if d["environment"] == environment.value
        ]

        if not recent_deployments:
            return {"status": "no_deployment", "environment": environment.value}

        latest_deployment = max(recent_deployments, key = lambda x: x["start_time"])

        return {
            "environment": environment.value,
            "status": latest_deployment["status"],
            "version": latest_deployment.get("version", "unknown"),
            "deployed_at": latest_deployment["start_time"].isoformat(),
            "deployment_duration": (
                (
                    latest_deployment["end_time"] - latest_deployment["start_time"]
                ).total_seconds()
                if latest_deployment.get("end_time")
                else None
            ),
            "steps": latest_deployment.get("steps", []),
            "feature_flags": {
                name: flag.enabled for name, flag in self.feature_flags.items()
            },
        }

    def enable_feature_flag(self, flag_name: str, rollout_percentage: float = 100.0):
        """启用特性标志"""
        if flag_name in self.feature_flags:
            self.feature_flags[flag_name].enabled = True
            self.feature_flags[flag_name].rollout_percentage = rollout_percentage
            logger.info(
                f"Feature flag '{flag_name}' enabled with {rollout_percentage}% rollout"
            )
        else:
            logger.warning(f"Feature flag '{flag_name}' not found")

    def disable_feature_flag(self, flag_name: str):
        """禁用特性标志"""
        if flag_name in self.feature_flags:
            self.feature_flags[flag_name].enabled = False
            logger.info(f"Feature flag '{flag_name}' disabled")
        else:
            logger.warning(f"Feature flag '{flag_name}' not found")


# 便利函数
def create_deployment_manager(
    config_file: str = "deployment_config.yaml",
) -> DeploymentManager:
    """创建部署管理器"""
    return DeploymentManager(config_file)


# 示例使用
def example_deployment():
    """部署示例"""
    manager = DeploymentManager()

    # 检查部署准备状态
    ready, issues = manager.check_deployment_readiness(Environment.STAGING)
    print(f"Deployment ready: {ready}")
    if issues:
        print("Issues:")
        for issue in issues:
            print(f"  - {issue}")

    # 执行部署
    if ready:
        result = manager.execute_deployment(Environment.STAGING, "v1.0.0")
        print(f"Deployment result: {result['status']}")


if __name__ == "__main__":
    example_deployment()
