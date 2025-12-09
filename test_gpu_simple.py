#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple GPU Performance Test
Test GPU optimization without complex imports
"""

import os
import sys
import time
import json
from pathlib import Path

def test_gpu_environment():
    """Test GPU environment directly"""

    print("=" * 60)
    print("GPU Environment Test")
    print("=" * 60)

    results = {}

    # Test CuPy availability
    print("\n1. Testing CuPy availability...")
    try:
        import cupy as cp
        results['cupy_available'] = True
        results['cupy_version'] = cp.__version__
        print(f"   CuPy Version: {cp.__version__}")

        # Test CUDA availability
        if cp.cuda.is_available():
            results['cuda_available'] = True
            results['gpu_count'] = cp.cuda.runtime.getDeviceCount()
            print(f"   CUDA Available: True")
            print(f"   GPU Count: {results['gpu_count']}")

            if results['gpu_count'] > 0:
                try:
                    device_props = cp.cuda.runtime.getDeviceProperties(0)
                    if hasattr(device_props, 'totalGlobalMem'):
                        results['gpu_memory_gb'] = device_props.totalGlobalMem // (1024**3)
                        results['gpu_name'] = device_props.name.decode('utf-8')
                    else:
                        # Fallback for dictionary-style device properties
                        results['gpu_memory_gb'] = device_props.get('totalGlobalMem', 0) // (1024**3)
                        results['gpu_name'] = device_props.get('name', 'Unknown GPU')
                    print(f"   GPU Name: {results['gpu_name']}")
                    print(f"   GPU Memory: {results['gpu_memory_gb']} GB")
                except Exception as e:
                    print(f"   GPU Properties: Unable to retrieve ({e})")
                    results['gpu_name'] = 'Unknown GPU'
                    results['gpu_memory_gb'] = 0

                # Test NVRTC availability
                try:
                    cp.cuda.Compiler()
                    results['nvrtc_available'] = True
                    print(f"   NVRTC Available: True")
                except Exception as e:
                    results['nvrtc_available'] = False
                    results['nvrtc_error'] = str(e)
                    print(f"   NVRTC Available: False ({e})")
        else:
            results['cuda_available'] = False
            print(f"   CUDA Available: False")

    except ImportError:
        results['cupy_available'] = False
        print(f"   CuPy Available: False")

    # Test simple GPU computation
    print("\n2. Testing GPU computation...")
    if results.get('cuda_available', False):
        try:
            import numpy as np

            # Create test data
            np.random.seed(42)
            test_data = np.random.randn(1000).astype(np.float32)

            # GPU computation test
            start_time = time.time()

            # Transfer to GPU
            gpu_data = cp.asarray(test_data)
            transfer_time = time.time() - start_time

            # Simple computation
            compute_start = time.time()
            gpu_result = cp.sum(gpu_data * 2.0)
            compute_time = time.time() - compute_start

            # Transfer back
            result = cp.asnumpy(gpu_result)
            total_time = time.time() - start_time

            print(f"   GPU Computation: Success")
            print(f"   Data Size: {len(test_data)} elements")
            print(f"   Transfer Time: {transfer_time:.4f}s")
            print(f"   Compute Time: {compute_time:.4f}s")
            print(f"   Total Time: {total_time:.4f}s")
            print(f"   Result: {result:.2f}")

            results['gpu_test'] = {
                'success': True,
                'data_size': len(test_data),
                'transfer_time': transfer_time,
                'compute_time': compute_time,
                'total_time': total_time,
                'result': float(result)
            }

        except Exception as e:
            results['gpu_test'] = {
                'success': False,
                'error': str(e)
            }
            print(f"   GPU Computation: Failed ({e})")
    else:
        results['gpu_test'] = {'success': False, 'reason': 'CUDA not available'}
        print(f"   GPU Computation: Skipped (CUDA not available)")

    # Test CPU performance for comparison
    print("\n3. Testing CPU performance...")
    try:
        import numpy as np

        # Create test data
        np.random.seed(42)
        test_data = np.random.randn(1000).astype(np.float32)

        # CPU computation test
        start_time = time.time()
        cpu_result = np.sum(test_data * 2.0)
        cpu_time = time.time() - start_time

        print(f"   CPU Computation: Success")
        print(f"   Data Size: {len(test_data)} elements")
        print(f"   Compute Time: {cpu_time:.4f}s")
        print(f"   Result: {cpu_result:.2f}")

        results['cpu_test'] = {
            'success': True,
            'data_size': len(test_data),
            'compute_time': cpu_time,
            'result': float(cpu_result)
        }

        # Calculate speedup if GPU test was successful
        if results.get('gpu_test', {}).get('success', False):
            gpu_time = results['gpu_test']['total_time']
            speedup = cpu_time / gpu_time
            results['speedup_ratio'] = speedup
            print(f"   Speedup Ratio: {speedup:.2f}x")

    except Exception as e:
        results['cpu_test'] = {
            'success': False,
            'error': str(e)
        }
        print(f"   CPU Computation: Failed ({e})")

    # Analyze bottlenecks
    print("\n4. Performance Bottleneck Analysis...")

    bottlenecks = []

    if not results.get('cupy_available', False):
        bottlenecks.append({
            'type': 'CUDA Runtime',
            'severity': 'CRITICAL',
            'issue': 'CuPy not installed',
            'solution': 'pip install cupy-cuda12x'
        })
    elif not results.get('cuda_available', False):
        bottlenecks.append({
            'type': 'CUDA Runtime',
            'severity': 'CRITICAL',
            'issue': 'CUDA not available',
            'solution': 'Install CUDA Toolkit or verify GPU drivers'
        })
    elif not results.get('nvrtc_available', False):
        bottlenecks.append({
            'type': 'CUDA Runtime',
            'severity': 'HIGH',
            'issue': 'NVRTC not available',
            'solution': 'Install CUDA Toolkit with NVRTC support',
            'details': results.get('nvrtc_error', 'Unknown error')
        })

    if results.get('gpu_test', {}).get('success', False):
        gpu_test = results['gpu_test']
        transfer_ratio = gpu_test['transfer_time'] / gpu_test['total_time']
        if transfer_ratio > 0.3:  # If transfer takes >30% of time
            bottlenecks.append({
                'type': 'Data Transfer Efficiency',
                'severity': 'HIGH',
                'issue': f'Data transfer takes {transfer_ratio:.1%} of total time',
                'solution': 'Implement batch transfers and pinned memory optimization'
            })

    # Memory management analysis
    if results.get('gpu_test', {}).get('success', False):
        if results.get('speedup_ratio', 0) < 2.0:
            bottlenecks.append({
                'type': 'Memory Management Strategy',
                'severity': 'MEDIUM',
                'issue': f'Low speedup ratio ({results.get("speedup_ratio", 0):.1f}x)',
                'solution': 'Optimize memory allocation and batch sizing strategies'
            })

    if bottlenecks:
        print(f"   Identified Bottlenecks ({len(bottlenecks)}):")
        for i, bottleneck in enumerate(bottlenecks, 1):
            print(f"   {i}. {bottleneck['type']} ({bottleneck['severity']}):")
            print(f"      Issue: {bottleneck['issue']}")
            print(f"      Solution: {bottleneck['solution']}")
            if 'details' in bottleneck:
                print(f"      Details: {bottleneck['details']}")
    else:
        print(f"   No critical bottlenecks identified")

    results['bottlenecks'] = bottlenecks

    # Save results
    print("\n5. Saving test results...")
    try:
        timestamp = int(time.time())
        report_file = f"gpu_test_results_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"   Results saved: {report_file}")

    except Exception as e:
        print(f"   Save failed: {e}")

    print("\n" + "=" * 60)
    print("GPU Environment Test: COMPLETE")
    print("=" * 60)

    return results

def show_optimization_recommendations(results):
    """Show specific optimization recommendations"""

    print("\n" + "=" * 60)
    print("Optimization Recommendations")
    print("=" * 60)

    if not results.get('cuda_available', False):
        print("\n[CUDA RUNTIME FIXES]")
        print("=" * 30)
        print("\n1. Install CUDA Toolkit:")
        print("   Download: https://developer.nvidia.com/cuda-downloads")
        print("   Select Windows 11, x86_64, exe (local)")
        print("   Install CUDA 12.x")
        print()
        print("2. Set Environment Variables:")
        print("   CUDA_PATH=C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.4")
        print("   PATH=%CUDA_PATH%\\bin;%PATH%")
        print()
        print("3. Install/Reinstall CuPy:")
        print("   pip uninstall cupy-cuda*")
        print("   pip install cupy-cuda12x")
        print()
        print("4. Alternative: Use Conda Environment:")
        print("   conda create -n gpu_env python=3.11")
        print("   conda activate gpu_env")
        print("   conda install -c conda-forge cupy-cuda12x")

    if results.get('gpu_test', {}).get('success', False):
        gpu_test = results['gpu_test']
        cpu_test = results.get('cpu_test', {})

        print("\n[DATA TRANSFER OPTIMIZATION]")
        print("=" * 30)
        print(f"\nCurrent Transfer Efficiency:")
        print(f"   Transfer Time: {gpu_test['transfer_time']:.4f}s")
        print(f"   Compute Time: {gpu_test['compute_time']:.4f}s")
        print(f"   Transfer Ratio: {gpu_test['transfer_time']/gpu_test['total_time']:.1%}")

        if gpu_test['transfer_time'] > gpu_test['compute_time'] * 0.5:
            print("\nRecommendations:")
            print("   1. Implement batch data transfers")
            print("   2. Use pinned memory (cp.cuda.PinnedMemoryAllocator)")
            print("   3. Cache frequently used data on GPU")
            print("   4. Use async CUDA streams for overlapping operations")

        print("\n[MEMORY MANAGEMENT OPTIMIZATION]")
        print("=" * 30)

        speedup = results.get('speedup_ratio', 0)
        if speedup < 5.0:
            print(f"\nCurrent Performance:")
            print(f"   GPU Time: {gpu_test['total_time']:.4f}s")
            print(f"   CPU Time: {cpu_test.get('compute_time', 0):.4f}s")
            print(f"   Speedup: {speedup:.2f}x")

            print("\nRecommendations:")
            print("   1. Increase batch sizes for better GPU utilization")
            print("   2. Use memory pools to reduce allocation overhead")
            print("   3. Implement adaptive batch sizing based on memory pressure")
            print("   4. Use vectorized operations to maximize parallelism")

if __name__ == "__main__":
    # Run GPU environment test
    results = test_gpu_environment()

    # Show optimization recommendations
    show_optimization_recommendations(results)

    print("\n" + "=" * 60)
    print("GPU Performance Analysis: COMPLETE")
    print("=" * 60)