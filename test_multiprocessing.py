#!/usr/bin/env python3
"""
测试multiprocessing功能
"""

import multiprocessing as mp
import os
import time
from multiprocessing import Pool, cpu_count

def test_task(x):
    """测试任务"""
    print(f"进程 {os.getpid()} 处理任务 {x}")
    time.sleep(0.1)  # 模拟计算
    return x * x

def main():
    print(f"CPU核心数: {cpu_count()}")
    print(f"操作系统: {os.name}")
    
    # Windows multiprocessing 需要特殊处理
    if os.name == 'nt':  # Windows
        mp.set_start_method('spawn', force=True)
    
    # 准备测试任务
    tasks = list(range(20))
    print(f"准备 {len(tasks)} 个测试任务")
    
    # 使用multiprocessing
    max_workers = min(cpu_count(), 8)
    print(f"使用 {max_workers} 个进程")
    
    try:
        with Pool(processes=max_workers) as pool:
            results = pool.map(test_task, tasks)
            print(f"结果: {results}")
            print("multiprocessing 测试成功!")
    except Exception as e:
        print(f"multiprocessing 失败: {e}")
        print("回退到单线程")
        results = [test_task(x) for x in tasks]
        print(f"单线程结果: {results}")

if __name__ == "__main__":
    main()
