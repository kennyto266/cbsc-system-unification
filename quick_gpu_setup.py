#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速GPU設置檢查和配置工具
Quick GPU Setup Check and Configuration Tool
"""

import subprocess
import sys
import os
import importlib.util

def check_gpu_status():
    """檢查GPU狀態"""
    print("=== GPU狀態檢查 ===")

    # 檢查NVIDIA驅動
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA驅動：正常")
            # 解析GPU信息
            lines = result.stdout.split('\n')
            for line in lines:
                if 'GeForce' in line or 'RTX' in line:
                    print(f"   GPU型號: {line.strip()}")
                if 'CUDA Version:' in line:
                    cuda_version = line.split('CUDA Version:')[1].strip()
                    print(f"   CUDA版本: {cuda_version}")
        else:
            print("❌ NVIDIA驅動：未檢測到")
            return False
    except FileNotFoundError:
        print("❌ nvidia-smi：未找到")
        return False

    # 檢查CuPy
    try:
        import cupy as cp
        print(f"✅ CuPy版本: {cp.__version__}")
        print(f"   CUDA可用: {cp.cuda.is_available()}")
        if cp.cuda.is_available():
            print(f"   GPU設備數: {cp.cuda.runtime.getDeviceCount()}")
        return True
    except ImportError:
        print("❌ CuPy：未安裝")
        return False
    except Exception as e:
        print(f"❌ CuPy錯誤: {e}")
        return False

def test_gpu_computation():
    """測試GPU計算"""
    print("\n=== GPU計算測試 ===")

    try:
        import cupy as cp
        import numpy as np
        import time

        print("測試GPU向量化計算...")

        # 創建測試數據
        size = 1000000
        np.random.seed(42)

        # CPU測試
        cpu_data = np.random.random(size)
        start_time = time.time()
        cpu_result = np.sum(cpu_data * 2.0)
        cpu_time = time.time() - start_time

        # GPU測試
        gpu_data = cp.array(cpu_data)
        start_time = time.time()
        gpu_result = cp.sum(gpu_data * 2.0)
        cp.cuda.Stream.null.synchronize()
        gpu_time = time.time() - start_time

        # 檢查結果
        cpu_final = float(cpu_result)
        gpu_final = float(gpu_result)

        print(f"CPU時間: {cpu_time:.6f}s")
        print(f"GPU時間: {gpu_time:.6f}s")
        print(f"加速比: {cpu_time/gpu_time:.2f}x")
        print(f"結果一致: {abs(cpu_final - gpu_final) < 1e-10}")

        return gpu_time < cpu_time

    except Exception as e:
        print(f"GPU計算測試失敗: {e}")
        return False

def install_cupy_conda():
    """使用Conda安裝CuPy"""
    print("\n=== Conda CuPy安裝 ===")

    try:
        # 檢查conda是否可用
        subprocess.run(['conda', '--version'], capture_output=True, check=True)
        print("✅ Conda可用")

        # 創建新的GPU環境
        print("正在創建GPU環境...")
        subprocess.run([
            'conda', 'create', '-n', 'vectorbt_gpu',
            'python=3.11', '-y'
        ], check=True)

        print("正在安裝CuPy...")
        subprocess.run([
            'conda', 'install', '-n', 'vectorbt_gpu',
            'cupy', 'vectorbt', '-c', 'conda-forge', '-y'
        ], check=True)

        print("✅ GPU環境安裝完成")
        print("\n使用方法:")
        print("conda activate vectorbt_gpu")
        print("cd simplified_system")
        print("python simple_gpu_test.py")

        return True

    except subprocess.CalledProcessError as e:
        print(f"Conda安裝失敗: {e}")
        return False
    except FileNotFoundError:
        print("❌ Conda未找到，請先安裝Anaconda或Miniconda")
        return False

def install_cupy_pip():
    """使用pip安裝CuPy"""
    print("\n=== Pip CuPy安裝 ===")

    try:
        # 卸載現有CuPy
        subprocess.run([sys.executable, '-m', 'pip', 'uninstall', 'cupy-cuda11x', '-y'],
                      capture_output=True)

        # 安裝CUDA 12版本（推薦）
        print("正在安裝CuPy CUDA 12...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'cupy-cuda12x'],
                      check=True)

        print("✅ CuPy安裝完成")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Pip安裝失敗: {e}")
        # 嘗試CPU版本作為備選
        print("正在安裝CPU版本...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'cupy-cuda11x'],
                          check=True)
            print("✅ CuPy CPU版本安裝完成")
            return True
        except:
            print("❌ CuPy安裝完全失敗")
            return False

def main():
    """主函數"""
    print("=" * 60)
    print("VectorBT GPU快速設置工具")
    print("=" * 60)

    # 檢查當前狀態
    gpu_available = check_gpu_status()

    if gpu_available:
        # 測試計算
        computation_ok = test_gpu_computation()

        if computation_ok:
            print("\n🎉 GPU加速已完全配置！")
            print("可以開始使用GPU加速的VectorBT功能。")
            return True
        else:
            print("\n⚠️ GPU檢測到但計算失敗")
            print("需要重新配置CUDA環境")

    # 提供配置選項
    print("\n=== 配置選項 ===")
    print("1. 使用Conda安裝（推薦）")
    print("2. 使用pip重新安裝")
    print("3. 手動安裝CUDA Toolkit")
    print("4. 跳過，繼續使用CPU版本")

    choice = input("\n請選擇 (1-4): ").strip()

    if choice == "1":
        return install_cupy_conda()
    elif choice == "2":
        return install_cupy_pip()
    elif choice == "3":
        print("\n請參考CUDA_SETUP_GUIDE.md進行手動配置")
        return False
    elif choice == "4":
        print("\n繼續使用CPU版本（已完美工作）")
        return True
    else:
        print("無效選擇")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)