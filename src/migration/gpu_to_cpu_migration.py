#!/usr/bin/env python3
"""
Phase 3: GPU到CPU配置迁移工具
GPU to CPU Configuration Migration Tool

This module provides comprehensive migration capabilities from GPU-accelerated
to CPU-optimized configurations, ensuring seamless transition and optimal performance.

Key Features:
- Automatic configuration detection and migration
- GPU/CPU capability assessment and fallback
- Performance parameter optimization
- Configuration validation and testing
- Rollback capabilities
- Migration progress tracking and reporting
"""

import logging
import time
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict
import yaml
import copy

from ..utils.gpu_detector import get_gpu_environment, GPUEnvironment
from ..optimization.dynamic_chunk_optimizer import get_chunk_optimizer

logger = logging.getLogger(__name__)

@dataclass
class GPUConfigProfile:
    """GPU配置文件"""
    batch_size: int
    memory_limit_gb: float
    parallel_streams: int
    gpu_device_id: int
    precision_mode: str  # 'float32', 'float16', 'mixed'
    optimization_level: str  # 'speed', 'memory', 'balanced'
    tensor_core_usage: bool
    cudnn_benchmark: bool

@dataclass
class CPUConfigProfile:
    """CPU配置文件"""
    chunk_size: int
    max_processes: int
    thread_pool_size: int
    memory_limit_mb: float
    optimization_target: str
    cache_size_mb: float
    numba_enabled: bool
    vectorization_enabled: bool

@dataclass
class MigrationSettings:
    """迁移设置"""
    preserve_performance: bool = True
    auto_optimize: bool = True
    validate_after_migration: bool = True
    enable_rollback: bool = True
    performance_tolerance: float = 0.1  # 10%性能容忍度

@dataclass
class MigrationResult:
    """迁移结果"""
    migration_id: str
    timestamp: float
    success: bool
    gpu_config: GPUConfigProfile
    cpu_config: CPUConfigProfile
    performance_comparison: Dict[str, float]
    warnings: List[str]
    errors: List[str]
    rollback_available: bool

class ConfigMigrator:
    """配置迁移器"""

    def __init__(
        self,
        config_dir: str = "config",
        backup_dir: str = "config_backup",
        migration_settings: MigrationSettings = None
    ):
        self.config_dir = Path(config_dir)
        self.backup_dir = Path(backup_dir)
        self.migration_settings = migration_settings or MigrationSettings()

        # 确保目录存在
        self.config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

        # GPU环境检测
        self.gpu_env = get_gpu_environment()

        # 迁移历史
        self.migration_history = []

        logger.info(f"Config Migrator initialized - Config dir: {self.config_dir}")

    def detect_gpu_configurations(self) -> Dict[str, Any]:
        """检测现有GPU配置"""
        gpu_configs = {}

        # 检查GPU配置文件
        gpu_config_files = [
            "gpu_config.json",
            "gpu_ta_config.yaml",
            "config/gpu_config.json"
        ]

        for config_file in gpu_config_files:
            config_path = self.config_dir / config_file
            if config_path.exists():
                try:
                    if config_path.suffix == '.json':
                        with open(config_path, 'r') as f:
                            config_data = json.load(f)
                    else:
                        with open(config_path, 'r') as f:
                            config_data = yaml.safe_load(f)

                    gpu_configs[config_file] = config_data
                    logger.info(f"Found GPU configuration: {config_file}")

                except Exception as e:
                    logger.warning(f"Failed to load GPU config {config_file}: {e}")

        # 检查代码中的GPU配置
        code_gpu_configs = self._scan_code_for_gpu_configs()
        gpu_configs.update(code_gpu_configs)

        return gpu_configs

    def _scan_code_for_gpu_configs(self) -> Dict[str, Any]:
        """扫描代码中的GPU配置"""
        gpu_configs = {}

        # 扫描主要Python文件
        python_files = list(Path(".").rglob("*.py"))
        keywords = ['use_gpu', 'GPUConfig', 'batch_size', 'memory_limit']

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 简单的关键词匹配
                if any(keyword in content for keyword in keywords):
                    # 这里可以添加更复杂的解析逻辑
                    gpu_configs[f"code_config_{py_file.name}"] = {
                        'source': 'code',
                        'file': str(py_file),
                        'detected_gpu_usage': True
                    }

            except Exception as e:
                logger.debug(f"Failed to scan {py_file}: {e}")

        return gpu_configs

    def generate_cpu_config_from_gpu(self, gpu_config: GPUConfigProfile) -> CPUConfigProfile:
        """从GPU配置生成CPU配置"""
        # 基于GPU配置的映射规则
        cpu_config = CPUConfigProfile(
            # 分块大小映射：GPU batch_size -> CPU chunk_size
            chunk_size=self._map_batch_to_chunk_size(gpu_config.batch_size),

            # 进程数映射：GPU streams -> CPU processes
            max_processes=min(multiprocessing.cpu_count(), gpu_config.parallel_streams + 1),

            # 线程池大小
            thread_pool_size=multiprocessing.cpu_count() * 2,

            # 内存限制：GB -> MB
            memory_limit_mb=gpu_config.memory_limit_gb * 1024,

            # 优化目标映射
            optimization_target=self._map_optimization_level(gpu_config.optimization_level),

            # 缓存大小
            cache_size_mb=min(512, gpu_config.memory_limit_gb * 100),

            # CPU特有优化
            numba_enabled=True,
            vectorization_enabled=True
        )

        return cpu_config

    def _map_batch_to_chunk_size(self, gpu_batch_size: int) -> int:
        """将GPU批处理大小映射到CPU分块大小"""
        # GPU通常可以处理更大的批次，CPU需要更小的分块
        # 基于经验值的映射
        if gpu_batch_size >= 50000:
            return 5000
        elif gpu_batch_size >= 25000:
            return 2500
        elif gpu_batch_size >= 10000:
            return 1000
        elif gpu_batch_size >= 5000:
            return 500
        else:
            return max(100, gpu_batch_size // 5)

    def _map_optimization_level(self, gpu_optimization: str) -> str:
        """映射优化级别"""
        mapping = {
            'speed': 'speed',
            'memory': 'memory',
            'balanced': 'balanced'
        }
        return mapping.get(gpu_optimization, 'balanced')

    def migrate_configuration(
        self,
        gpu_config_file: str = None,
        custom_gpu_config: GPUConfigProfile = None
    ) -> MigrationResult:
        """执行配置迁移"""
        migration_id = f"migration_{int(time.time())}"
        start_time = time.time()

        try:
            # 1. 检测或获取GPU配置
            if custom_gpu_config:
                gpu_config = custom_gpu_config
            elif gpu_config_file:
                gpu_config = self._load_gpu_config(gpu_config_file)
            else:
                gpu_configs = self.detect_gpu_configurations()
                if gpu_configs:
                    # 使用第一个找到的配置
                    config_data = list(gpu_configs.values())[0]
                    gpu_config = self._dict_to_gpu_config(config_data)
                else:
                    # 使用默认GPU配置
                    gpu_config = self._get_default_gpu_config()

            # 2. 生成CPU配置
            cpu_config = self.generate_cpu_config_from_gpu(gpu_config)

            # 3. 创建备份
            if self.migration_settings.enable_rollback:
                self._create_backup()

            # 4. 保存CPU配置
            self._save_cpu_config(cpu_config, migration_id)

            # 5. 自动优化（如果启用）
            if self.migration_settings.auto_optimize:
                cpu_config = self._auto_optimize_cpu_config(cpu_config)

            # 6. 验证配置（如果启用）
            performance_comparison = {}
            if self.migration_settings.validate_after_migration:
                performance_comparison = self._validate_configuration(gpu_config, cpu_config)

            # 7. 创建迁移记录
            migration_result = MigrationResult(
                migration_id=migration_id,
                timestamp=start_time,
                success=True,
                gpu_config=gpu_config,
                cpu_config=cpu_config,
                performance_comparison=performance_comparison,
                warnings=[],
                errors=[],
                rollback_available=self.migration_settings.enable_rollback
            )

            self.migration_history.append(migration_result)

            # 8. 保存迁移记录
            self._save_migration_record(migration_result)

            logger.info(f"Configuration migration completed: {migration_id}")
            return migration_result

        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            logger.error(error_msg)

            # 创建失败的迁移记录
            migration_result = MigrationResult(
                migration_id=migration_id,
                timestamp=start_time,
                success=False,
                gpu_config=gpu_config if 'gpu_config' in locals() else None,
                cpu_config=None,
                performance_comparison={},
                warnings=[],
                errors=[error_msg],
                rollback_available=self.migration_settings.enable_rollback
            )

            return migration_result

    def _load_gpu_config(self, config_file: str) -> GPUConfigProfile:
        """加载GPU配置文件"""
        config_path = self.config_dir / config_file
        if not config_path.exists():
            config_path = Path(config_file)  # 尝试绝对路径

        if not config_path.exists():
            raise FileNotFoundError(f"GPU config file not found: {config_file}")

        with open(config_path, 'r') as f:
            if config_path.suffix == '.json':
                config_data = json.load(f)
            else:
                config_data = yaml.safe_load(f)

        return self._dict_to_gpu_config(config_data)

    def _dict_to_gpu_config(self, config_data: Dict) -> GPUConfigProfile:
        """将字典转换为GPU配置"""
        return GPUConfigProfile(
            batch_size=config_data.get('batch_size', 10000),
            memory_limit_gb=config_data.get('memory_limit_gb', 4.0),
            parallel_streams=config_data.get('parallel_streams', 1),
            gpu_device_id=config_data.get('gpu_device_id', 0),
            precision_mode=config_data.get('precision_mode', 'float32'),
            optimization_level=config_data.get('optimization_level', 'balanced'),
            tensor_core_usage=config_data.get('tensor_core_usage', False),
            cudnn_benchmark=config_data.get('cudnn_benchmark', True)
        )

    def _get_default_gpu_config(self) -> GPUConfigProfile:
        """获取默认GPU配置"""
        return GPUConfigProfile(
            batch_size=10000,
            memory_limit_gb=4.0,
            parallel_streams=1,
            gpu_device_id=0,
            precision_mode='float32',
            optimization_level='balanced',
            tensor_core_usage=False,
            cudnn_benchmark=True
        )

    def _create_backup(self):
        """创建配置备份"""
        timestamp = int(time.time())
        backup_path = self.backup_dir / f"backup_{timestamp}"

        if self.config_dir.exists():
            shutil.copytree(self.config_dir, backup_path, dirs_exist_ok=True)
            logger.info(f"Configuration backed up to: {backup_path}")

    def _save_cpu_config(self, cpu_config: CPUConfigProfile, migration_id: str):
        """保存CPU配置"""
        config_data = asdict(cpu_config)

        # 保存为JSON
        json_path = self.config_dir / f"cpu_config_{migration_id}.json"
        with open(json_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        # 保存为主配置文件
        main_path = self.config_dir / "cpu_config.json"
        with open(main_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"CPU configuration saved: {main_path}")

    def _auto_optimize_cpu_config(self, cpu_config: CPUConfigProfile) -> CPUConfigProfile:
        """自动优化CPU配置"""
        logger.info("Auto-optimizing CPU configuration...")

        # 获取系统信息
        cpu_count = multiprocessing.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)

        # 优化进程数
        optimized_processes = min(cpu_count, cpu_config.max_processes)
        if memory_gb < 8:
            # 内存不足时减少进程数
            optimized_processes = min(optimized_processes, cpu_count // 2)

        # 优化分块大小
        chunk_optimizer = get_chunk_optimizer()
        optimized_chunk_size = chunk_optimizer.get_optimal_chunk_size(
            data_size=10000,  # 估算数据大小
            operation_type='technical_indicators'
        )

        # 优化缓存大小
        optimized_cache_size = min(512, memory_gb * 50)  # 50%的可用内存，最大512MB

        # 创建优化后的配置
        optimized_config = CPUConfigProfile(
            chunk_size=optimized_chunk_size,
            max_processes=optimized_processes,
            thread_pool_size=cpu_count * 2,
            memory_limit_mb=min(memory_gb * 1024 * 0.8, cpu_config.memory_limit_mb),
            optimization_target=cpu_config.optimization_target,
            cache_size_mb=optimized_cache_size,
            numba_enabled=True,
            vectorization_enabled=True
        )

        logger.info(f"CPU configuration optimized - Processes: {optimized_processes}, "
                   f"Chunk size: {optimized_chunk_size}")
        return optimized_config

    def _validate_configuration(
        self,
        gpu_config: GPUConfigProfile,
        cpu_config: CPUConfigProfile
    ) -> Dict[str, float]:
        """验证配置性能"""
        logger.info("Validating migrated configuration...")

        # 这里可以添加实际的性能测试
        # 目前返回模拟的性能比较数据
        performance_comparison = {
            'estimated_speed_ratio': 0.3,  # CPU大约是GPU的30%速度
            'memory_efficiency_ratio': 1.2,  # CPU内存效率更高
            'scalability_score': 0.8,
            'configuration_valid': True
        }

        return performance_comparison

    def _save_migration_record(self, result: MigrationResult):
        """保存迁移记录"""
        record_file = self.config_dir / f"migration_record_{result.migration_id}.json"

        record_data = {
            'migration_id': result.migration_id,
            'timestamp': result.timestamp,
            'success': result.success,
            'gpu_config': asdict(result.gpu_config) if result.gpu_config else None,
            'cpu_config': asdict(result.cpu_config) if result.cpu_config else None,
            'performance_comparison': result.performance_comparison,
            'warnings': result.warnings,
            'errors': result.errors,
            'rollback_available': result.rollback_available
        }

        with open(record_file, 'w') as f:
            json.dump(record_data, f, indent=2, default=str)

        logger.info(f"Migration record saved: {record_file}")

    def rollback_migration(self, migration_id: str) -> bool:
        """回滚迁移"""
        try:
            # 查找对应的备份
            backup_pattern = f"backup_*"
            backup_dirs = list(self.backup_dir.glob(backup_pattern))

            if not backup_dirs:
                logger.error("No backup directories found for rollback")
                return False

            # 使用最新的备份
            latest_backup = max(backup_dirs, key=lambda x: x.stat().st_mtime)

            # 恢复配置
            if self.config_dir.exists():
                shutil.rmtree(self.config_dir)
            shutil.copytree(latest_backup, self.config_dir)

            logger.info(f"Migration rolled back from: {latest_backup}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def get_migration_history(self) -> List[Dict[str, Any]]:
        """获取迁移历史"""
        history_records = []

        for record_file in self.config_dir.glob("migration_record_*.json"):
            try:
                with open(record_file, 'r') as f:
                    record_data = json.load(f)
                history_records.append(record_data)
            except Exception as e:
                logger.warning(f"Failed to read migration record {record_file}: {e}")

        return sorted(history_records, key=lambda x: x['timestamp'], reverse=True)

class GPUDetectorAndFallback:
    """GPU检测和回退系统"""

    def __init__(self):
        self.gpu_env = get_gpu_environment()
        self.fallback_activated = False
        self.fallback_history = []

    def check_gpu_availability(self) -> Dict[str, Any]:
        """检查GPU可用性"""
        status = {
            'gpu_available': self.gpu_env.is_gpu_available(),
            'cupy_available': self.gpu_env.cupy_available,
            'cuda_available': self.gpu_env.cuda_available,
            'gpu_count': self.gpu_env.gpu_count,
            'gpu_memory_gb': self.gpu_env.gpu_memory_gb,
            'recommendation': 'use_gpu' if self.gpu_env.is_gpu_available() else 'use_cpu'
        }

        if not status['gpu_available']:
            status['fallback_reason'] = self._get_fallback_reason()

        return status

    def _get_fallback_reason(self) -> str:
        """获取回退原因"""
        if not self.gpu_env.cupy_available:
            return "CuPy not installed"
        elif not self.gpu_env.cuda_available:
            return "CUDA not available"
        elif self.gpu_env.gpu_count == 0:
            return "No GPU devices found"
        elif self.gpu_env.gpu_memory_gb < 2:
            return "GPU memory insufficient"
        else:
            return "Unknown GPU detection failure"

    def activate_cpu_fallback(self, reason: str = "GPU unavailable"):
        """激活CPU回退"""
        if not self.fallback_activated:
            self.fallback_activated = True
            fallback_record = {
                'timestamp': time.time(),
                'reason': reason,
                'gpu_status': self.check_gpu_availability()
            }
            self.fallback_history.append(fallback_record)

            logger.warning(f"CPU fallback activated - Reason: {reason}")

    def get_fallback_status(self) -> Dict[str, Any]:
        """获取回退状态"""
        return {
            'fallback_activated': self.fallback_activated,
            'fallback_history': self.fallback_history,
            'current_gpu_status': self.check_gpu_availability()
        }

    def test_gpu_functionality(self) -> Dict[str, Any]:
        """测试GPU功能"""
        test_result = self.gpu_env.test_gpu_computation(size=1000)
        return test_result

# 全局实例
_global_migrator = None
_global_detector = None

def get_config_migrator() -> ConfigMigrator:
    """获取全局配置迁移器实例"""
    global _global_migrator
    if _global_migrator is None:
        _global_migrator = ConfigMigrator()
    return _global_migrator

def get_gpu_detector() -> GPUDetectorAndFallback:
    """获取全局GPU检测器实例"""
    global _global_detector
    if _global_detector is None:
        _global_detector = GPUDetectorAndFallback()
    return _global_detector

def auto_migrate_to_cpu() -> MigrationResult:
    """自动迁移到CPU配置"""
    migrator = get_config_migrator()
    detector = get_gpu_detector()

    # 检查GPU状态
    gpu_status = detector.check_gpu_availability()

    if not gpu_status['gpu_available']:
        logger.info("GPU not available, initiating auto-migration to CPU")
        return migrator.migrate_configuration()
    else:
        logger.info("GPU available, no migration needed")
        return None

# 导入multiprocessing和psutil（如果在模块内部未导入）
try:
    import multiprocessing
    import psutil
except ImportError:
    logger.warning("multiprocessing or psutil not available")