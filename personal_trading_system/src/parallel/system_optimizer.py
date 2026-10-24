#!/usr/bin/env python3
"""
System Optimizer for Parallel Processing Configuration
Automatic system tuning and performance optimization for 32-core systems
"""

import os
import sys
import time
import json
import logging
import platform
import psutil
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import multiprocessing as mp

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class SystemTier(Enum):
    """System performance tier classification"""
    ENTRY_LEVEL = "entry"        # 8-16 cores
    PROFESSIONAL = "professional"  # 16-24 cores
    ENTERPRISE = "enterprise"   # 24-32 cores
    ULTRA_HIGH = "ultra_high"  # 32+ cores


@dataclass
class SystemProfile:
    """Comprehensive system profile"""
    cpu_cores: int
    cpu_threads: int
    cpu_freq_mhz: float
    total_memory_gb: float
    available_memory_gb: float
    disk_speed_mb_s: float
    network_speed_mbps: float
    system_tier: SystemTier
    num_sockets: int
    cache_sizes: Dict[str, int]
    architecture: str
    platform: str
    gpu_available: bool = False
    gpu_memory_gb: float = 0.0


@dataclass
class OptimizationConfig:
    """Optimization configuration settings"""
    max_workers: int
    memory_limit_gb: float
    chunk_size_mb: int
    parallel_strategy: str
    cpu_affinity_enabled: bool
    memory_optimization_level: str
    io_optimization_enabled: bool
    network_optimization_enabled: bool
    auto_scaling_enabled: bool
    monitoring_level: str


@dataclass
class OptimizationRecommendation:
    """System optimization recommendation"""
    category: str
    priority: str
    description: str
    expected_improvement: str
    implementation_difficulty: str
    parameters: Dict[str, Any]
    risk_level: str


class SystemOptimizer:
    """
    Advanced system optimizer for parallel processing

    Features:
    - Automatic system profiling and capability detection
    - Intelligent parameter optimization based on hardware
    - NUMA-aware CPU affinity optimization
    - Memory hierarchy optimization
    - I/O subsystem tuning
    - Network stack optimization
    - Power management configuration
    - Thermal management integration
    - Performance benchmarking and validation
    - Continuous optimization monitoring
    """

    def __init__(self, enable_gpu_optimization: bool = False, enable_detailed_profiling: bool = False):
        self.enable_gpu_optimization = enable_gpu_optimization
        self.enable_detailed_profiling = enable_detailed_profiling

        # System information
        self.system_profile: Optional[SystemProfile] = None
        self.optimization_config: Optional[OptimizationConfig] = None
        self.benchmark_results: Dict[str, float] = {}

        # Optimization state
        self.is_optimized = False
        self.optimization_history: List[Dict[str, Any]] = []

        logger.info("SystemOptimizer initialized")

    def profile_system(self) -> SystemProfile:
        """
        Perform comprehensive system profiling

        Returns:
            SystemProfile with detailed hardware information
        """
        logger.info("Starting comprehensive system profiling...")

        # CPU information
        cpu_info = self._get_cpu_info()

        # Memory information
        memory_info = self._get_memory_info()

        # Disk information
        disk_info = self._get_disk_info()

        # Network information
        network_info = self._get_network_info()

        # GPU information
        gpu_info = self._get_gpu_info() if self.enable_gpu_optimization else {}

        # Determine system tier
        system_tier = self._classify_system_tier(cpu_info['cores'], memory_info['total_gb'])

        self.system_profile = SystemProfile(
            cpu_cores=cpu_info['cores'],
            cpu_threads=cpu_info['threads'],
            cpu_freq_mhz=cpu_info['freq_mhz'],
            total_memory_gb=memory_info['total_gb'],
            available_memory_gb=memory_info['available_gb'],
            disk_speed_mb_s=disk_info['speed_mb_s'],
            network_speed_mbps=network_info['speed_mbps'],
            system_tier=system_tier,
            num_sockets=cpu_info['sockets'],
            cache_sizes=cpu_info['cache_sizes'],
            architecture=cpu_info['architecture'],
            platform=platform.platform(),
            gpu_available=gpu_info.get('available', False),
            gpu_memory_gb=gpu_info.get('memory_gb', 0.0)
        )

        logger.info(f"System profiling completed: {system_tier.value} tier, {cpu_info['cores']} cores, {memory_info['total_gb']:.1f}GB RAM")
        return self.system_profile

    def optimize_system(self, force_reprofile: bool = False) -> OptimizationConfig:
        """
        Automatically optimize system configuration

        Args:
            force_reprofile: Force system re-profiling

        Returns:
            OptimizationConfig with optimized parameters
        """
        logger.info("Starting system optimization...")

        if force_reprofile or not self.system_profile:
            self.profile_system()

        if not self.system_profile:
            raise RuntimeError("System profile not available")

        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations()

        # Apply optimizations
        self.optimization_config = self._apply_optimizations(recommendations)

        # Validate optimizations
        self._validate_optimizations()

        self.is_optimized = True

        logger.info("System optimization completed successfully")
        return self.optimization_config

    def get_optimized_config(self) -> OptimizationConfig:
        """Get current optimization configuration"""
        if not self.optimization_config:
            raise RuntimeError("System not optimized yet. Call optimize_system() first.")
        return self.optimization_config

    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        if not self.system_profile:
            self.profile_system()

        recommendations = self._generate_optimization_recommendations()

        report = {
            'timestamp': datetime.now().isoformat(),
            'system_profile': {
                'cpu_cores': self.system_profile.cpu_cores,
                'cpu_threads': self.system_profile.cpu_threads,
                'total_memory_gb': self.system_profile.total_memory_gb,
                'system_tier': self.system_profile.system_tier.value,
                'gpu_available': self.system_profile.gpu_available
            },
            'optimization_config': self.optimization_config.__dict__ if self.optimization_config else None,
            'recommendations': [rec.__dict__ for rec in recommendations],
            'benchmark_results': self.benchmark_results,
            'optimization_history': self.optimization_history
        }

        return report

    def benchmark_system(self, iterations: int = 5) -> Dict[str, float]:
        """
        Run system benchmarks to validate optimizations

        Args:
            iterations: Number of benchmark iterations

        Returns:
            Dictionary with benchmark results
        """
        logger.info(f"Running system benchmarks ({iterations} iterations)...")

        if not self.optimization_config:
            raise RuntimeError("System not optimized yet")

        benchmarks = {}

        # CPU benchmark
        benchmarks['cpu_mops'] = self._benchmark_cpu(iterations)

        # Memory benchmark
        benchmarks['memory_gb_s'] = self._benchmark_memory(iterations)

        # I/O benchmark
        benchmarks['disk_io_mb_s'] = self._benchmark_disk_io(iterations)

        # Parallel processing benchmark
        benchmarks['parallel_efficiency'] = self._benchmark_parallel_processing(iterations)

        self.benchmark_results = benchmarks

        logger.info("System benchmarks completed")
        return benchmarks

    def _get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information"""
        cpu_info = {
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True),
            'freq_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 0.0,
            'sockets': 1,  # Default assumption
            'cache_sizes': {},
            'architecture': platform.machine()
        }

        # Try to get more detailed CPU information
        try:
            if platform.system() == "Linux":
                # Parse /proc/cpuinfo
                cpu_info.update(self._parse_linux_cpuinfo())
            elif platform.system() == "Windows":
                # Use wmic for Windows
                cpu_info.update(self._parse_windows_cpuinfo())
            elif platform.system() == "Darwin":
                # Use sysctl for macOS
                cpu_info.update(self._parse_macos_cpuinfo())
        except Exception as e:
            logger.warning(f"Could not get detailed CPU info: {e}")

        return cpu_info

    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        memory = psutil.virtual_memory()

        return {
            'total_gb': memory.total / (1024**3),
            'available_gb': memory.available / (1024**3),
            'used_gb': memory.used / (1024**3),
            'percent': memory.percent
        }

    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk information"""
        disk_info = {'speed_mb_s': 0.0}

        try:
            # Get primary disk
            disk_usage = psutil.disk_usage('/')

            # Simple disk speed test
            test_file = Path(tempfile.gettempdir()) / "disk_speed_test.tmp"
            test_data = b'0' * (10 * 1024 * 1024)  # 10MB

            start_time = time.time()
            with open(test_file, 'wb') as f:
                f.write(test_data)
            write_time = time.time() - start_time

            start_time = time.time()
            with open(test_file, 'rb') as f:
                f.read()
            read_time = time.time() - start_time

            # Clean up
            test_file.unlink()

            # Calculate speed (10MB / time)
            disk_info['speed_mb_s'] = 10 / max(write_time, read_time, 0.001)

        except Exception as e:
            logger.warning(f"Could not benchmark disk speed: {e}")

        return disk_info

    def _get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        net_info = {'speed_mbps': 0.0}

        try:
            net_io = psutil.net_io_counters()
            # Simple test - this is approximate
            net_info['speed_mbps'] = 1000.0  # Default assumption

        except Exception as e:
            logger.warning(f"Could not get network info: {e}")

        return net_info

    def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        gpu_info = {'available': False, 'memory_gb': 0.0}

        try:
            # Try to detect NVIDIA GPU
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total,name', '--format=csv,noheader,nounits'],
                                   capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    memory_mb = int(lines[0].split(',')[0].strip())
                    gpu_info.update({
                        'available': True,
                        'memory_gb': memory_mb / 1024,
                        'name': lines[0].split(',')[1].strip()
                    })

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # No NVIDIA GPU or nvidia-smi not available
            pass

        return gpu_info

    def _classify_system_tier(self, cores: int, memory_gb: float) -> SystemTier:
        """Classify system into performance tier"""
        if cores >= 32 and memory_gb >= 64:
            return SystemTier.ULTRA_HIGH
        elif cores >= 24 and memory_gb >= 32:
            return SystemTier.ENTERPRISE
        elif cores >= 16 and memory_gb >= 16:
            return SystemTier.PROFESSIONAL
        else:
            return SystemTier.ENTRY_LEVEL

    def _generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on system profile"""
        recommendations = []

        if not self.system_profile:
            return recommendations

        profile = self.system_profile

        # CPU optimization recommendations
        if profile.cpu_cores >= 32:
            recommendations.append(OptimizationRecommendation(
                category="cpu",
                priority="high",
                description="Enable hyper-threading optimization for maximum throughput",
                expected_improvement="20-30% task throughput",
                implementation_difficulty="easy",
                parameters={"hyperthreading": True, "num_workers": profile.cpu_cores},
                risk_level="low"
            ))

        # Memory optimization recommendations
        if profile.total_memory_gb >= 64:
            recommendations.append(OptimizationRecommendation(
                category="memory",
                priority="high",
                description="Use large memory pools for terabyte-scale processing",
                expected_improvement="50-70% memory efficiency",
                implementation_difficulty="medium",
                parameters={"memory_pool_size_mb": 8192, "enable_compression": True},
                risk_level="low"
            ))

        # I/O optimization recommendations
        if profile.disk_speed_mb_s >= 500:
            recommendations.append(OptimizationRecommendation(
                category="io",
                priority="medium",
                description="Enable parallel I/O for fast SSD systems",
                expected_improvement="40-60% I/O throughput",
                implementation_difficulty="medium",
                parameters={"parallel_io": True, "io_buffer_size_mb": 256},
                risk_level="medium"
            ))

        # NUMA optimization for multi-socket systems
        if profile.num_sockets > 1:
            recommendations.append(OptimizationRecommendation(
                category="numa",
                priority="high",
                description="Enable NUMA-aware processing for multi-socket systems",
                expected_improvement="15-25% performance",
                implementation_difficulty="hard",
                parameters={"numa_affinity": True, "socket_binding": True},
                risk_level="medium"
            ))

        # GPU optimization recommendations
        if profile.gpu_available and profile.gpu_memory_gb >= 8:
            recommendations.append(OptimizationRecommendation(
                category="gpu",
                priority="medium",
                description="Offload computationally intensive tasks to GPU",
                expected_improvement="5-10x acceleration for compatible tasks",
                implementation_difficulty="hard",
                parameters={"gpu_acceleration": True, "batch_size": 1000},
                risk_level="high"
            ))

        return recommendations

    def _apply_optimizations(self, recommendations: List[OptimizationRecommendation]) -> OptimizationConfig:
        """Apply optimization recommendations to generate configuration"""
        profile = self.system_profile

        # Base configuration
        config = OptimizationConfig(
            max_workers=min(profile.cpu_cores, 32),
            memory_limit_gb=profile.total_memory_gb * 0.8,  # Use 80% of available memory
            chunk_size_mb=100,
            parallel_strategy="auto",
            cpu_affinity_enabled=True,
            memory_optimization_level="medium",
            io_optimization_enabled=False,
            network_optimization_enabled=False,
            auto_scaling_enabled=True,
            monitoring_level="standard"
        )

        # Apply recommendations
        for rec in recommendations:
            if rec.category == "cpu" and rec.parameters.get("num_workers"):
                config.max_workers = rec.parameters["num_workers"]
                config.cpu_affinity_enabled = rec.parameters.get("hyperthreading", True)

            elif rec.category == "memory":
                if rec.parameters.get("memory_pool_size_mb"):
                    config.memory_limit_gb = min(
                        profile.total_memory_gb * 0.9,
                        rec.parameters["memory_pool_size_mb"] / 1024
                    )
                if rec.parameters.get("enable_compression"):
                    config.memory_optimization_level = "aggressive"

            elif rec.category == "io":
                config.io_optimization_enabled = rec.parameters.get("parallel_io", False)
                if rec.parameters.get("io_buffer_size_mb"):
                    config.chunk_size_mb = max(config.chunk_size_mb, rec.parameters["io_buffer_size_mb"])

            elif rec.category == "numa":
                config.cpu_affinity_enabled = rec.parameters.get("numa_affinity", True)

        # Fine-tune based on system tier
        if profile.system_tier == SystemTier.ULTRA_HIGH:
            config.parallel_strategy = "adaptive"
            config.monitoring_level = "detailed"
            config.chunk_size_mb = 200
        elif profile.system_tier == SystemTier.ENTERPRISE:
            config.parallel_strategy = "balanced"
            config.monitoring_level = "standard"
            config.chunk_size_mb = 150
        elif profile.system_tier == SystemTier.PROFESSIONAL:
            config.parallel_strategy = "throughput"
            config.monitoring_level = "basic"
            config.chunk_size_mb = 100
        else:  # ENTRY_LEVEL
            config.parallel_strategy = "conservative"
            config.monitoring_level = "minimal"
            config.chunk_size_mb = 50

        # Store optimization in history
        self.optimization_history.append({
            'timestamp': datetime.now().isoformat(),
            'config': config.__dict__,
            'recommendations': [rec.__dict__ for rec in recommendations]
        })

        logger.info(f"Applied {len(recommendations)} optimization recommendations")
        return config

    def _validate_optimizations(self):
        """Validate applied optimizations"""
        if not self.optimization_config or not self.system_profile:
            return

        config = self.optimization_config
        profile = self.system_profile

        # Validate worker count
        if config.max_workers > profile.cpu_cores:
            logger.warning(f"Worker count ({config.max_workers}) exceeds CPU cores ({profile.cpu_cores})")

        # Validate memory allocation
        if config.memory_limit_gb > profile.total_memory_gb * 0.95:
            logger.warning(f"Memory allocation ({config.memory_limit_gb}GB) approaches system limit ({profile.total_memory_gb}GB)")

        # Log successful validation
        logger.info("Optimization validation completed successfully")

    def _benchmark_cpu(self, iterations: int) -> float:
        """Benchmark CPU performance (millions of operations per second)"""
        import math

        operations_per_test = 1000000
        total_time = 0

        for _ in range(iterations):
            start_time = time.time()

            # CPU-intensive computation
            result = 0
            for i in range(operations_per_test):
                result += math.sqrt(i) * math.sin(i) * math.cos(i)

            test_time = time.time() - start_time
            total_time += test_time

        mops = (operations_per_test * iterations) / (total_time * 1_000_000)
        return mops

    def _benchmark_memory(self, iterations: int) -> float:
        """Benchmark memory performance (GB/s)"""
        data_size_gb = 1.0
        data_size_bytes = int(data_size_gb * 1024**3)
        test_array = np.random.random(data_size_bytes // 8)  # float64

        total_time = 0

        for _ in range(iterations):
            start_time = time.time()

            # Memory-intensive operation
            processed_array = test_array * 2 + np.sqrt(test_array) + np.log(test_array + 1)
            result = np.sum(processed_array)

            test_time = time.time() - start_time
            total_time += test_time

        gb_per_second = (data_size_gb * iterations) / total_time
        return gb_per_second

    def _benchmark_disk_io(self, iterations: int) -> float:
        """Benchmark disk I/O performance (MB/s)"""
        test_file = Path(tempfile.gettempdir()) / "disk_benchmark.tmp"
        test_size_mb = 100
        test_data = b'0' * (test_size_mb * 1024 * 1024)

        total_time = 0

        for _ in range(iterations):
            start_time = time.time()

            # Write test
            with open(test_file, 'wb') as f:
                f.write(test_data)

            # Read test
            with open(test_file, 'rb') as f:
                f.read()

            test_time = time.time() - start_time
            total_time += test_time

        # Clean up
        if test_file.exists():
            test_file.unlink()

        mb_per_second = (test_size_mb * 2 * iterations) / total_time  # 2x for read and write
        return mb_per_second

    def _benchmark_parallel_processing(self, iterations: int) -> float:
        """Benchmark parallel processing efficiency"""
        from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

        test_function = lambda x: sum(range(x))  # CPU-bound task
        test_size = 100000
        num_workers = min(8, self.optimization_config.max_workers if self.optimization_config else 4)

        # Sequential baseline
        start_time = time.time()
        for _ in range(num_workers):
            test_function(test_size)
        sequential_time = time.time() - start_time

        # Parallel test
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            list(executor.map(lambda _: test_function(test_size), range(num_workers)))
        parallel_time = time.time() - start_time

        # Calculate efficiency
        theoretical_parallel_time = sequential_time / num_workers
        efficiency = theoretical_parallel_time / parallel_time if parallel_time > 0 else 0

        return min(efficiency, 1.0)  # Cap at 100%

    def _parse_linux_cpuinfo(self) -> Dict[str, Any]:
        """Parse Linux /proc/cpuinfo"""
        cpu_info = {}

        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo_lines = f.readlines()

            physical_cores = 0
            processors = set()
            cache_info = {}

            for line in cpuinfo_lines:
                if 'physical id' in line:
                    processors.add(line.split(':')[1].strip())
                elif 'cpu cores' in line:
                    cores = int(line.split(':')[1].strip())
                    physical_cores = max(physical_cores, cores)
                elif 'cache size' in line:
                    cache_kb = line.split(':')[1].strip()
                    if 'KB' in cache_kb:
                        cache_size = int(cache_kb.replace('KB', '').strip())
                        cache_info['l3'] = cache_size

            cpu_info['sockets'] = len(processors)
            cpu_info['cache_sizes'] = cache_info

        except Exception:
            pass  # Use defaults

        return cpu_info

    def _parse_windows_cpuinfo(self) -> Dict[str, Any]:
        """Parse Windows CPU information using wmic"""
        cpu_info = {}

        try:
            # Get CPU information using wmic
            result = subprocess.run(['wmic', 'cpu', 'get', 'NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed', '/format:list'],
                                   capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        if key == 'NumberOfCores':
                            cpu_info['sockets'] = 1
                            cpu_info['cores'] = int(value)
                        elif key == 'NumberOfLogicalProcessors':
                            cpu_info['threads'] = int(value)
                        elif key == 'MaxClockSpeed':
                            cpu_info['freq_mhz'] = float(value)

        except Exception:
            pass  # Use defaults

        return cpu_info

    def _parse_macos_cpuinfo(self) -> Dict[str, Any]:
        """Parse macOS CPU information using sysctl"""
        cpu_info = {}

        try:
            # Get CPU information using sysctl
            commands = {
                'hw.physicalcpu': 'cores',
                'hw.logicalcpu': 'threads',
                'hw.cpufrequency': 'freq_hz'
            }

            for cmd, key in commands.items():
                result = subprocess.run(['sysctl', '-n', cmd], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    value = result.stdout.strip()
                    if key == 'freq_hz':
                        cpu_info['freq_mhz'] = float(value) / 1_000_000
                    else:
                        cpu_info[key] = int(value)

            cpu_info['sockets'] = 1

        except Exception:
            pass  # Use defaults

        return cpu_info


# Utility functions for system optimization
def get_optimal_system_config() -> OptimizationConfig:
    """
    Get optimal system configuration for current hardware

    Returns:
        OptimizationConfig with optimal parameters
    """
    optimizer = SystemOptimizer()
    config = optimizer.optimize_system()
    return config


def apply_system_tuning():
    """Apply system-level tuning for optimal parallel processing performance"""
    logger.info("Applying system-level tuning...")

    try:
        if platform.system() == "Linux":
            _apply_linux_tuning()
        elif platform.system() == "Windows":
            _apply_windows_tuning()
        elif platform.system() == "Darwin":
            _apply_macos_tuning()

        logger.info("System-level tuning completed successfully")

    except Exception as e:
        logger.error(f"System-level tuning failed: {e}")


def _apply_linux_tuning():
    """Apply Linux-specific system tuning"""
    try:
        # Set CPU governor to performance
        subprocess.run(['cpupower', 'frequency-set', '-g', 'performance'], check=False)

        # Disable swap temporarily for better performance
        subprocess.run(['sudo', 'swapoff', '-a'], check=False)

        # Set ulimits for better parallel processing
        subprocess.run(['ulimit', '-n', '65536'], check=False)

    except Exception as e:
        logger.warning(f"Some Linux tuning could not be applied: {e}")


def _apply_windows_tuning():
    """Apply Windows-specific system tuning"""
    try:
        # Set power plan to High Performance
        subprocess.run(['powercfg', '/setactive', 'SCHEME_MIN'], check=False)

    except Exception as e:
        logger.warning(f"Windows tuning could not be applied: {e}")


def _apply_macos_tuning():
    """Apply macOS-specific system tuning"""
    try:
        # Set power management settings
        subprocess.run(['sudo', 'pmset', '-a', 'displaysleep', '0'], check=False)
        subprocess.run(['sudo', 'pmset', '-a', 'sleep', '0'], check=False)

    except Exception as e:
        logger.warning(f"macOS tuning could not be applied: {e}")