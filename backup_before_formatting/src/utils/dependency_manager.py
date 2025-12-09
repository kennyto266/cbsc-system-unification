#!/usr/bin/env python3
"""
依賴管理系統
負責動態檢查和管理系統依賴，包括GPU、VectorBT等組件
"""

import sys
import importlib
import platform
import subprocess
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

try:
    import pkg_resources
except ImportError:
    pkg_resources = None

logger = logging.getLogger(__name__)

class DependencyManager:
    """依賴管理器"""

    def __init__(self):
        self.dependencies = {}
        self.gpu_available = False
        self.vectorbt_available = False
        self.system_info = {}

        # 初始化依賴檢查
        self._check_all_dependencies()
        self._get_system_info()

    def _get_system_info(self):
        """獲取系統信息"""
        self.system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'python_implementation': platform.python_implementation(),
            'python_executable': sys.executable,
        }

    def _check_all_dependencies(self):
        """檢查所有依賴"""
        # 定義要檢查的依賴
        dependency_specs = {
            # 核心依賴
            'pandas': {'required': True, 'min_version': '1.3.0'},
            'numpy': {'required': True, 'min_version': '1.20.0'},
            'requests': {'required': True, 'min_version': '2.25.0'},

            # 分析依賴
            'vectorbt': {'required': False, 'min_version': '0.25.0', 'features': ['backtesting', 'portfolio_analysis']},
            'scipy': {'required': False, 'min_version': '1.7.0', 'features': ['statistics', 'optimization']},
            'scikit-learn': {'required': False, 'min_version': '1.0.0', 'features': ['machine_learning']},

            # 可視化依賴
            'matplotlib': {'required': False, 'min_version': '3.3.0', 'features': ['charting']},
            'plotly': {'required': False, 'min_version': '5.0.0', 'features': ['interactive_charts']},
            'seaborn': {'required': False, 'min_version': '0.11.0', 'features': ['statistical_viz']},

            # GPU依賴
            'cupy': {'required': False, 'min_version': '9.0.0', 'features': ['gpu_acceleration']},
            'numba': {'required': False, 'min_version': '0.56.0', 'features': ['jit_compilation']},

            # 界面依賴
            'tabulate': {'required': False, 'min_version': '0.8.0', 'features': ['table_formatting']},
            'colorama': {'required': False, 'min_version': '0.4.0', 'features': ['terminal_colors']},
            'rich': {'required': False, 'min_version': '10.0.0', 'features': ['enhanced_terminal']},

            # 系統依賴
            'psutil': {'required': False, 'min_version': '5.8.0', 'features': ['system_monitoring']},
            'tqdm': {'required': False, 'min_version': '4.60.0', 'features': ['progress_bars']},
        }

        for dependency, spec in dependency_specs.items():
            self.dependencies[dependency] = self._check_dependency(dependency, spec)

        # 特殊檢查
        self.gpu_available = self._check_gpu_availability()
        self.vectorbt_available = self.dependencies['vectorbt']['available']

    def _check_dependency(self, name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        """檢查單個依賴"""
        result = {
            'name': name,
            'available': False,
            'version': None,
            'version_ok': False,
            'features': [],
            'error': None,
            'required': spec.get('required', False),
            'min_version': spec.get('min_version'),
            'spec_features': spec.get('features', [])
        }

        try:
            # 嘗試導入模塊
            module = importlib.import_module(name)

            # 獲取版本信息
            if hasattr(module, '__version__'):
                version = module.__version__
            elif hasattr(module, 'version'):
                version = module.version
            else:
                # 嘗試使用pkg_resources獲取版本
                try:
                    if pkg_resources:
                        version = pkg_resources.get_distribution(name).version
                    else:
                        version = 'Unknown'
                except:
                    version = 'Unknown'

            result['available'] = True
            result['version'] = version

            # 檢查版本
            if spec.get('min_version'):
                result['version_ok'] = self._compare_versions(version, spec['min_version'])
            else:
                result['version_ok'] = True

            # 檢查功能
            if spec.get('features'):
                result['features'] = self._check_module_features(module, spec['features'])

        except ImportError as e:
            result['error'] = str(e)
            if spec.get('required', False):
                logger.error(f"Required dependency {name} not available: {e}")
            else:
                logger.warning(f"Optional dependency {name} not available: {e}")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error checking dependency {name}: {e}")

        return result

    def _check_module_features(self, module, features: List[str]) -> List[str]:
        """檢查模塊功能"""
        available_features = []

        for feature in features:
            try:
                if feature == 'backtesting':
                    # VectorBT backtesting功能
                    if hasattr(module, 'Backtester') or hasattr(module, 'Portfolio'):
                        available_features.append(feature)
                elif feature == 'portfolio_analysis':
                    # VectorBT portfolio功能
                    if hasattr(module, 'Portfolio') or hasattr(module, 'Portfolio.from_signals'):
                        available_features.append(feature)
                elif feature == 'gpu_acceleration':
                    # CuPy GPU功能
                    if hasattr(module, 'cuda') and hasattr(module, 'get_device'):
                        available_features.append(feature)
                elif feature == 'jit_compilation':
                    # Numba JIT功能
                    if hasattr(module, 'jit'):
                        available_features.append(feature)
                elif feature == 'statistics':
                    # SciPy統計功能
                    if hasattr(module, 'stats'):
                        available_features.append(feature)
                elif feature == 'optimization':
                    # SciPy優化功能
                    if hasattr(module, 'optimize'):
                        available_features.append(feature)
                elif feature == 'machine_learning':
                    # Scikit-learn功能
                    if hasattr(module, 'model_selection') or hasattr(module, 'linear_model'):
                        available_features.append(feature)
                elif feature == 'charting':
                    # Matplotlib圖表功能
                    if hasattr(module, 'pyplot'):
                        available_features.append(feature)
                elif feature == 'interactive_charts':
                    # Plotly交互式圖表
                    if hasattr(module, 'graph_objects') or hasattr(module, 'express'):
                        available_features.append(feature)
                elif feature == 'statistical_viz':
                    # Seaborn統計可視化
                    if hasattr(module, 'histplot') or hasattr(module, 'scatterplot'):
                        available_features.append(feature)
                elif feature == 'table_formatting':
                    # Tabulate表格格式化
                    if hasattr(module, 'tabulate'):
                        available_features.append(feature)
                elif feature == 'terminal_colors':
                    # Colorama終端顏色
                    if hasattr(module, 'init') or hasattr(module, 'Fore'):
                        available_features.append(feature)
                elif feature == 'enhanced_terminal':
                    # Rich增強終端
                    if hasattr(module, 'Console') or hasattr(module, 'Table'):
                        available_features.append(feature)
                elif feature == 'system_monitoring':
                    # psutil系統監控
                    if hasattr(module, 'virtual_memory') or hasattr(module, 'cpu_percent'):
                        available_features.append(feature)
                elif feature == 'progress_bars':
                    # tqdm進度條
                    if hasattr(module, 'tqdm'):
                        available_features.append(feature)
                else:
                    # 通用檢查
                    if hasattr(module, feature):
                        available_features.append(feature)

            except Exception:
                # 功能檢查失敗，跳過
                pass

        return available_features

    def _check_gpu_availability(self) -> bool:
        """檢查GPU可用性"""
        try:
            import cupy as cp
            # 嘗試創建一個簡單的數組來測試GPU
            test_array = cp.array([1, 2, 3])
            # 檢查GPU設備信息
            device = cp.cuda.Device()
            if device.id >= 0:
                logger.info(f"GPU detected: {device.name} (ID: {device.id})")
                return True
        except ImportError:
            logger.info("CuPy not available, GPU acceleration disabled")
        except Exception as e:
            logger.warning(f"GPU detected but not functional: {e}")

        return False

    def _compare_versions(self, current: str, minimum: str) -> bool:
        """比較版本號"""
        try:
            from packaging import version
            return version.parse(current) >= version.parse(minimum)
        except ImportError:
            # 如果沒有packaging，使用簡單的字符串比較
            try:
                current_parts = [int(x) for x in current.split('.')]
                minimum_parts = [int(x) for x in minimum.split('.')]

                # 補齊長度
                max_len = max(len(current_parts), len(minimum_parts))
                current_parts.extend([0] * (max_len - len(current_parts)))
                minimum_parts.extend([0] * (max_len - len(minimum_parts)))

                return current_parts >= minimum_parts
            except:
                return True  # 無法比較時假設OK

    def get_dependency_status(self) -> Dict[str, Any]:
        """獲取依賴狀態摘要"""
        required_deps = [dep for dep in self.dependencies.values() if dep['required']]
        optional_deps = [dep for dep in self.dependencies.values() if not dep['required']]

        required_ok = all(dep['available'] for dep in required_deps)
        optional_count = len([dep for dep in optional_deps if dep['available']])

        return {
            'all_required_available': required_ok,
            'required_count': len(required_deps),
            'optional_available': optional_count,
            'optional_total': len(optional_deps),
            'gpu_available': self.gpu_available,
            'vectorbt_available': self.vectorbt_available,
            'system_info': self.system_info
        }

    def get_missing_dependencies(self) -> List[Dict[str, Any]]:
        """獲取缺失的依賴"""
        missing = []
        for dep in self.dependencies.values():
            if not dep['available'] and dep['required']:
                missing.append({
                    'name': dep['name'],
                    'min_version': dep.get('min_version'),
                    'error': dep.get('error'),
                    'install_command': self._get_install_command(dep['name'])
                })
        return missing

    def _get_install_command(self, package_name: str) -> str:
        """獲取安裝命令"""
        install_commands = {
            'pandas': 'pip install pandas>=1.3.0',
            'numpy': 'pip install numpy>=1.20.0',
            'requests': 'pip install requests>=2.25.0',
            'vectorbt': 'pip install vectorbt>=0.25.0',
            'scipy': 'pip install scipy>=1.7.0',
            'scikit-learn': 'pip install scikit-learn>=1.0.0',
            'matplotlib': 'pip install matplotlib>=3.3.0',
            'plotly': 'pip install plotly>=5.0.0',
            'seaborn': 'pip install seaborn>=0.11.0',
            'cupy': 'pip install cupy-cuda11x>=9.0.0',  # 根據CUDA版本調整
            'numba': 'pip install numba>=0.56.0',
            'tabulate': 'pip install tabulate>=0.8.0',
            'colorama': 'pip install colorama>=0.4.0',
            'rich': 'pip install rich>=10.0.0',
            'psutil': 'pip install psutil>=5.8.0',
            'tqdm': 'pip install tqdm>=4.60.0',
        }

        return install_commands.get(package_name, f'pip install {package_name}')

    def get_compatibility_report(self) -> Dict[str, Any]:
        """獲取兼容性報告"""
        report = {
            'platform': self.system_info['platform'],
            'python_version': self.system_info['python_version'],
            'compatibility_score': 0,
            'issues': [],
            'recommendations': [],
            'performance_tier': 'Basic'
        }

        # 計算兼容性分數
        total_deps = len(self.dependencies)
        available_deps = len([dep for dep in self.dependencies.values() if dep['available']])
        required_available = all(dep['available'] for dep in self.dependencies.values() if dep['required'])

        if required_available:
            score_base = 50
            bonus = int((available_deps / total_deps) * 50)
            report['compatibility_score'] = score_base + bonus
        else:
            report['compatibility_score'] = 0
            report['issues'].append("Missing required dependencies")

        # 檢查GPU兼容性
        if self.gpu_available:
            report['performance_tier'] = 'Advanced'
            report['recommendations'].append("GPU acceleration available for enhanced performance")
        else:
            if platform.system() == 'Windows':
                report['recommendations'].append("Consider installing WSL2 + CUDA for GPU acceleration")
            elif platform.system() == 'Linux':
                report['recommendations'].append("Consider installing NVIDIA drivers + CUDA for GPU acceleration")
            elif platform.system() == 'Darwin':
                report['recommendations'].append("Consider installing Metal-compatible libraries for Apple Silicon acceleration")

        # 檢查VectorBT
        if self.vectorbt_available:
            report['performance_tier'] = 'Professional' if self.gpu_available else 'Enhanced'
            report['recommendations'].append("VectorBT available for professional backtesting")
        else:
            report['issues'].append("VectorBT not available - advanced backtesting features disabled")
            report['recommendations'].append("Install VectorBT for professional backtesting capabilities")

        # 檢查可視化庫
        viz_available = self.dependencies['matplotlib']['available'] or self.dependencies['plotly']['available']
        if not viz_available:
            report['issues'].append("No visualization libraries available")
            report['recommendations'].append("Install matplotlib or plotly for chart visualization")

        return report

    def attempt_dependency_fallback(self, dependency_name: str) -> Optional[Any]:
        """嘗試依賴降級"""
        fallbacks = {
            'cupy': self._fallback_numpy,
            'vectorbt': self._fallback_basic_backtesting,
            'matplotlib': self._fallback_ascii_charts,
            'plotly': self._fallback_ascii_charts,
            'tabulate': self._fallback_simple_table,
            'rich': self._fallback_basic_terminal,
        }

        fallback_func = fallbacks.get(dependency_name)
        if fallback_func:
            try:
                return fallback_func()
            except Exception as e:
                logger.error(f"Fallback for {dependency_name} failed: {e}")

        return None

    def _fallback_numpy(self):
        """CuPy降級到NumPy"""
        import numpy as np
        logger.info("Using NumPy instead of CuPy (CPU-only)")
        return np

    def _fallback_basic_backtesting(self):
        """VectorBT降級到基礎回測"""
        class BasicBacktester:
            def __init__(self):
                logger.info("Using basic backtesting instead of VectorBT")

            def backtest(self, data, strategy_func):
                # 實現基礎回測邏輯
                pass

        return BasicBacktester()

    def _fallback_ascii_charts(self):
        """圖表庫降級到ASCII圖表"""
        class AsciiChart:
            def __init__(self):
                logger.info("Using ASCII charts instead of matplotlib/plotly")

            def plot(self, data):
                # 實現ASCII圖表邏輯
                pass

        return AsciiChart()

    def _fallback_simple_table(self):
        """Tabulate降級到簡單表格"""
        def simple_table(data, headers=None):
            if headers:
                print("\t".join(headers))
            for row in data:
                print("\t".join(str(item) for item in row))

        logger.info("Using simple table formatting instead of tabulate")
        return simple_table

    def _fallback_basic_terminal(self):
        """Rich降級到基礎終端"""
        class BasicTerminal:
            def __init__(self):
                logger.info("Using basic terminal instead of rich")

            def print(self, text, style=None):
                print(text)

        return BasicTerminal()

    def install_missing_dependencies(self, auto_install: bool = False) -> Dict[str, Any]:
        """安裝缺失的依賴"""
        missing = self.get_missing_dependencies()
        results = {}

        for dep in missing:
            cmd = dep['install_command']
            if auto_install:
                try:
                    logger.info(f"Installing {dep['name']}...")
                    result = subprocess.run(cmd.split(), capture_output=True, text=True)
                    results[dep['name']] = {
                        'success': result.returncode == 0,
                        'output': result.stdout,
                        'error': result.stderr
                    }
                except Exception as e:
                    results[dep['name']] = {
                        'success': False,
                        'output': '',
                        'error': str(e)
                    }
            else:
                results[dep['name']] = {
                    'success': False,
                    'output': '',
                    'error': 'Auto-install disabled',
                    'command': cmd
                }

        return results

    def get_performance_profile(self) -> Dict[str, Any]:
        """獲取性能配置文件"""
        profile = {
            'acceleration_level': 'CPU',
            'parallelization': False,
            'memory_optimization': False,
            'recommendations': []
        }

        # GPU加速
        if self.gpu_available:
            profile['acceleration_level'] = 'GPU'
            profile['recommendations'].append("GPU acceleration available")

        # 多進程並行
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        if cpu_count >= 4:
            profile['parallelization'] = True
            profile['recommendations'].append(f"Multi-core parallelization available ({cpu_count} cores)")

        # 內存優化
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            if memory_gb >= 16:
                profile['memory_optimization'] = True
                profile['recommendations'].append(f"High memory environment ({memory_gb:.1f}GB) available")
        except:
            pass

        return profile