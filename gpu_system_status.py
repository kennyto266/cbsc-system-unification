#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU系統狀態監控工具
提供實時的GPU、內存和系統性能狀態監控
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional

# 添加src路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def get_gpu_status() -> Dict[str, Any]:
    """獲取GPU狀態信息"""
    try:
        from utils.gpu_config import detect_gpu_environment, get_gpu_config

        gpu_info = detect_gpu_environment()
        config = get_gpu_config()

        return {
            'available': gpu_info.get('cuda_available', False),
            'gpu_count': gpu_info.get('gpu_count', 0),
            'gpu_memory_total': gpu_info.get('gpu_memory_total', 0),
            'gpu_memory_free': gpu_info.get('gpu_memory_free', 0),
            'gpu_memory_used': gpu_info.get('gpu_memory_used', 0),
            'gpu_utilization': gpu_info.get('gpu_utilization', 0),
            'gpu_temperature': gpu_info.get('gpu_temperature', 0),
            'compute_capability': gpu_info.get('compute_capability', 'N/A'),
            'driver_version': gpu_info.get('driver_version', 'N/A'),
            'cuda_version': gpu_info.get('cuda_version', 'N/A'),
            'gpu_enabled': config.use_gpu,
            'gpu_name': gpu_info.get('gpu_name', 'N/A')
        }
    except Exception as e:
        return {
            'available': False,
            'error': str(e),
            'gpu_enabled': False
        }

def get_memory_status() -> Dict[str, Any]:
    """獲取內存狀態信息"""
    try:
        import psutil

        memory = psutil.virtual_memory()

        return {
            'cpu_memory_total': memory.total,
            'cpu_memory_used': memory.used,
            'cpu_memory_free': memory.available,
            'cpu_memory_percent': memory.percent,
            'cpu_memory_available_gb': memory.available / (1024**3),
            'cpu_memory_used_gb': memory.used / (1024**3)
        }
    except ImportError:
        return {
            'error': 'psutil not installed'
        }

def get_data_sources_status() -> Dict[str, Any]:
    """獲取數據源狀態"""
    try:
        from adapters.adapter_manager import get_nonprice_adapter_manager

        adapter_manager = get_nonprice_adapter_manager()
        sources = adapter_manager.get_available_sources()
        validation_results = adapter_manager.validate_all_sources()

        healthy_count = sum(1 for is_healthy in validation_results.values() if is_healthy)

        return {
            'total_sources': len(sources),
            'healthy_sources': healthy_count,
            'unhealthy_sources': len(sources) - healthy_count,
            'health_rate': healthy_count / len(sources) * 100 if sources else 0,
            'sources_list': list(sources.keys()),
            'validation_details': validation_results
        }
    except Exception as e:
        return {
            'error': str(e),
            'total_sources': 0,
            'healthy_sources': 0
        }

def get_vectorbt_status() -> Dict[str, Any]:
    """獲取VectorBT狀態"""
    try:
        import vectorbt as vbt
        import pandas as pd
        import numpy as np

        return {
            'available': True,
            'version': vbt.__version__,
            'pandas_version': pd.__version__,
            'numpy_version': np.__version__,
            'gpu_acceleration_available': hasattr(vbt, 'GPU')
        }
    except ImportError as e:
        return {
            'available': False,
            'error': str(e)
        }

def get_system_performance() -> Dict[str, Any]:
    """獲取系統性能指標"""
    try:
        import psutil

        # CPU信息
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # 磁盤信息
        disk = psutil.disk_usage('/')

        return {
            'cpu_usage_percent': cpu_percent,
            'cpu_cores': cpu_count,
            'cpu_frequency_mhz': cpu_freq.current if cpu_freq else 0,
            'disk_usage_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3),
            'disk_total_gb': disk.total / (1024**3)
        }
    except ImportError:
        return {
            'error': 'psutil not installed'
        }

def display_status():
    """顯示系統狀態"""
    print("="*80)
    print("GPU加速非價格TA回測系統狀態監控")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # GPU狀態
    print("\n📊 GPU狀態:")
    print("-" * 40)
    gpu_status = get_gpu_status()

    if gpu_status.get('available', False):
        print(f"✅ GPU可用: {gpu_status['gpu_count']} 個設備")
        print(f"🏷️  GPU名稱: {gpu_status.get('gpu_name', 'N/A')}")
        print(f"💾 GPU內存: {gpu_status.get('gpu_memory_used', 0):.0f} MB / {gpu_status.get('gpu_memory_total', 0):.0f} MB")
        print(f"⚡ GPU利用率: {gpu_status.get('gpu_utilization', 0):.1f}%")
        print(f"🌡️  GPU溫度: {gpu_status.get('gpu_temperature', 0):.0f}°C")
        print(f"🔧 CUDA版本: {gpu_status.get('cuda_version', 'N/A')}")
        print(f"🎯 計算能力: {gpu_status.get('compute_capability', 'N/A')}")
        print(f"🚀 GPU加速: {'啟用' if gpu_status.get('gpu_enabled') else '禁用'}")
    else:
        print("❌ GPU不可用")
        if 'error' in gpu_status:
            print(f"錯誤: {gpu_status['error']}")

    # 內存狀態
    print("\n💾 內存狀態:")
    print("-" * 40)
    memory_status = get_memory_status()

    if 'error' not in memory_status:
        print(f"📊 CPU內存: {memory_status['cpu_memory_used_gb']:.2f} GB / {memory_status['cpu_memory_total']/(1024**3):.2f} GB")
        print(f"📈 內存使用率: {memory_status['cpu_memory_percent']:.1f}%")
        print(f"💡 可用內存: {memory_status['cpu_memory_available_gb']:.2f} GB")
    else:
        print(f"❌ 內存信息獲取失敗: {memory_status['error']}")

    # 數據源狀態
    print("\n📡 數據源狀態:")
    print("-" * 40)
    data_sources = get_data_sources_status()

    if 'error' not in data_sources:
        print(f"📊 總數據源: {data_sources['total_sources']} 個")
        print(f"✅ 健康數據源: {data_sources['healthy_sources']} 個")
        print(f"❌ 不健康數據源: {data_sources['unhealthy_sources']} 個")
        print(f"📈 健康率: {data_sources['health_rate']:.1f}%")

        if data_sources['sources_list']:
            print(f"📋 可用數據源: {', '.join(data_sources['sources_list'][:5])}")
            if len(data_sources['sources_list']) > 5:
                print(f"    ... 還有 {len(data_sources['sources_list']) - 5} 個數據源")
    else:
        print(f"❌ 數據源檢查失敗: {data_sources['error']}")

    # VectorBT狀態
    print("\n📈 VectorBT狀態:")
    print("-" * 40)
    vbt_status = get_vectorbt_status()

    if vbt_status.get('available', False):
        print(f"✅ VectorBT可用: 版本 {vbt_status['version']}")
        print(f"🐼 Pandas版本: {vbt_status['pandas_version']}")
        print(f"🔢 NumPy版本: {vbt_status['numpy_version']}")
        print(f"🚀 GPU加速: {'可用' if vbt_status.get('gpu_acceleration_available') else '不可用'}")
    else:
        print("❌ VectorBT不可用")
        if 'error' in vbt_status:
            print(f"錯誤: {vbt_status['error']}")

    # 系統性能
    print("\n⚙️  系統性能:")
    print("-" * 40)
    perf_status = get_system_performance()

    if 'error' not in perf_status:
        print(f"💻 CPU使用率: {perf_status['cpu_usage_percent']:.1f}%")
        print(f"🔧 CPU核心數: {perf_status['cpu_cores']}")
        print(f"⚡ CPU頻率: {perf_status['cpu_frequency_mhz']:.0f} MHz")
        print(f"💿 磁盤使用率: {perf_status['disk_usage_percent']:.1f}%")
        print(f"💾 可用磁盤空間: {perf_status['disk_free_gb']:.2f} GB")
    else:
        print(f"❌ 系統性能信息獲取失敗: {perf_status['error']}")

    print("\n" + "="*80)
    print("狀態檢查完成")
    print("="*80)

def export_status_json(output_path: str = None):
    """導出狀態為JSON格式"""
    if output_path is None:
        output_path = f"gpu_system_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    status_data = {
        'timestamp': datetime.now().isoformat(),
        'gpu_status': get_gpu_status(),
        'memory_status': get_memory_status(),
        'data_sources_status': get_data_sources_status(),
        'vectorbt_status': get_vectorbt_status(),
        'system_performance': get_system_performance()
    }

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
        print(f"狀態數據已導出到: {output_path}")
    except Exception as e:
        print(f"導出狀態數據失敗: {e}")

def watch_mode(interval: int = 30):
    """監控模式，定時刷新狀態"""
    print("🔍 進入監控模式 (Ctrl+C 退出)")
    print(f"🔄 刷新間隔: {interval} 秒")

    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            display_status()
            print(f"\n⏰ 下次更新: {interval} 秒後...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n👋 監控模式已停止")

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="GPU系統狀態監控工具")
    parser.add_argument(
        '--watch', '-w',
        action='store_true',
        help='監控模式，定時刷新狀態'
    )
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=30,
        help='監控模式刷新間隔（秒，默認30）'
    )
    parser.add_argument(
        '--export', '-e',
        help='導出狀態到JSON文件'
    )
    parser.add_argument(
        '--json-only',
        action='store_true',
        help='僅輸出JSON格式，不顯示美化界面'
    )

    args = parser.parse_args()

    if args.json_only:
        export_status_json(args.export if args.export else None)
    elif args.watch:
        watch_mode(args.interval)
    else:
        display_status()
        if args.export:
            export_status_json(args.export)

if __name__ == "__main__":
    main()