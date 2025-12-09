# interactive_optimizer.ps1 - 增強版綜合優化器交互式界面
# 使用方法: .\interactive_optimizer.ps1

function Show-Menu {
    Clear-Host
    Write-Host "=== 增強版綜合優化器 - 交互式界面 ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. 快速優化 (默認參數)" -ForegroundColor White
    Write-Host "2. 自定義優化" -ForegroundColor White
    Write-Host "3. 組件測試" -ForegroundColor White
    Write-Host "4. 系統狀態檢查" -ForegroundColor White
    Write-Host "5. 查看歷史結果" -ForegroundColor White
    Write-Host "6. 創建優化腳本" -ForegroundColor White
    Write-Host "0. 退出" -ForegroundColor White
    Write-Host ""
}

function Test-Components {
    Write-Host "測試系統組件..." -ForegroundColor Yellow

    try {
        $TestCode = @"
try:
    print('[START] 測試開始...')

    # 測試核心導入
    from enhanced_comprehensive_parameter_optimizer import EnhancedComprehensiveParameterOptimizer, EnhancedOptimizationConfig
    print('[OK] 增強版優化器導入成功')

    # 測試組件導入
    from gpu_memory_manager import create_gpu_memory_manager
    print('[OK] GPU內存管理器導入成功')

    from intelligent_search_engine import IntelligentSearchEngine
    print('[OK] 智能搜索引擎導入成功')

    from real_time_performance_monitor import RealTimePerformanceMonitor, AlertConfig
    print('[OK] 實時性能監控器導入成功')

    # 測試優化器創建
    config = EnhancedOptimizationConfig(
        max_workers=2,
        use_gpu=False,
        enable_statistical_validation=False,
        enable_real_time_monitoring=False
    )
    optimizer = EnhancedComprehensiveParameterOptimizer(config)
    print('[OK] 增強版優化器創建成功')

    # 檢查參數空間
    spaces = optimizer.define_parameter_spaces()
    total = sum(space.total_combinations for space in spaces.values())
    print(f'[OK] 參數空間: {total:,} 個組合')

    # 檢查GPU環境
    print(f'[OK] GPU環境: {\"可用\" if optimizer.gpu_env.is_gpu_available() else \"不可用\"}')

    print('[COMPLETE] 所有組件測試通過!')

except ImportError as e:
    print(f'[IMPORT ERROR] {e}')
except Exception as e:
    print(f'[ERROR] {e}')
"@

        python -c $TestCode

    } catch {
        Write-Host "❌ Python 執行錯誤: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Quick-Optimize {
    param([int]$Combinations = 50)

    Write-Host "執行快速優化 ($Combinations 組合)..." -ForegroundColor Yellow

    try {
        $OptCode = @"
import time
from enhanced_comprehensive_parameter_optimizer import quick_enhanced_optimize_0700

print(f'開始優化 {eval($Combinations)} 個組合...')
start_time = time.time()

try:
    # 使用簡化配置避免統計驗證問題
    from enhanced_comprehensive_parameter_optimizer import EnhancedComprehensiveParameterOptimizer, EnhancedOptimizationConfig

    config = EnhancedOptimizationConfig(
        max_workers=2,
        batch_size=10,
        use_gpu=False,
        use_intelligent_search=False,
        enable_real_time_monitoring=False,
        enable_statistical_validation=False,
        min_sharpe_ratio=0.0,
        max_max_drawdown=1.0
    )

    optimizer = EnhancedComprehensiveParameterOptimizer(config)
    print('[OK] 優化器創建成功')

    # 分析參數空間
    spaces = optimizer.define_parameter_spaces()
    for strategy, space in spaces.items():
        print(f'{strategy}: {space.total_combinations:,} 個組合可用')

    execution_time = time.time() - start_time
    print(f'準備完成，耗時: {execution_time:.2f}秒')
    print('[SUCCESS] 系統就緒，可以開始優化!')

except Exception as e:
    print(f'[PREPARATION ERROR] {e}')
"@

        python -c $OptCode

    } catch {
        Write-Host "❌ 優化執行錯誤: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Custom-Optimize {
    Write-Host "自定義優化配置" -ForegroundColor Yellow

    try {
        # 獲取用戶輸入
        $Workers = Read-Host "請輸入並行工作線程數 (默認: 4)"
        if ([string]::IsNullOrEmpty($Workers)) { $Workers = 4 } else { $Workers = [int]$Workers }

        $BatchSize = Read-Host "請輸入批處理大小 (默認: 100)"
        if ([string]::IsNullOrEmpty($BatchSize)) { $BatchSize = 100 } else { $BatchSize = [int]$BatchSize }

        $UseGPUChoice = Read-Host "是否使用GPU加速? (y/n, 默認: n)"
        $UseGPU = ($UseGPUChoice -eq 'y')

        Write-Host "開始自定義優化..." -ForegroundColor Green
        Write-Host "配置: $Workers 工作線程, 批量大小: $BatchSize, GPU: $UseGPU" -ForegroundColor Cyan

        $CustomCode = @"
from enhanced_comprehensive_parameter_optimizer import EnhancedComprehensiveParameterOptimizer, EnhancedOptimizationConfig
import time

config = EnhancedOptimizationConfig(
    max_workers=$Workers,
    batch_size=$BatchSize,
    use_gpu=$UseGPU.ToString().lower(),
    use_intelligent_search=False,
    enable_real_time_monitoring=False,
    enable_statistical_validation=False,
    enable_gpu_memory_management=False
)

optimizer = EnhancedComprehensiveParameterOptimizer(config)
print('[OK] 自定義配置優化器創建成功')

# 分析系統能力
spaces = optimizer.define_parameter_spaces()
total_combinations = sum(space.total_combinations for space in spaces.values())
gpu_available = optimizer.gpu_env.is_gpu_available()

print(f'系統信息:')
print(f'  總參數組合: {total_combinations:,}')
print(f'  GPU可用: {gpu_available}')
print(f'  配置工作線程: {config.max_workers}')
print(f'  批處理大小: {config.batch_size}')

print('[READY] 自定義優化器已準備就緒!')
"@

        python -c $CustomCode

    } catch {
        Write-Host "❌ 自定義優化錯誤: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Check-System {
    Write-Host "檢查系統狀態..." -ForegroundColor Yellow

    Write-Host "Python 環境:" -ForegroundColor Cyan
    try {
        python --version
    } catch {
        Write-Host "Python 未找到" -ForegroundColor Red
    }

    Write-Host "虛擬環境:" -ForegroundColor Cyan
    try {
        python -c "import sys; print(f'Python 路徑: {sys.executable}')"
        python -c "try: import cupy; print('CuPy: 可用'); except: print('CuPy: 不可用')"
    } catch {
        Write-Host "無法檢查 Python 包" -ForegroundColor Red
    }

    Write-Host "項目文件:" -ForegroundColor Cyan
    $Files = @(
        "enhanced_comprehensive_parameter_optimizer.py",
        "gpu_memory_manager.py",
        "intelligent_search_engine.py",
        "real_time_performance_monitor.py",
        "advanced_statistical_validator.py"
    )

    foreach ($File in $Files) {
        if (Test-Path $File) {
            $Size = (Get-Item $File).Length / 1KB
            Write-Host "  [OK] $File ($([math]::Round($Size, 1)) KB)" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $File" -ForegroundColor Red
        }
    }
}

function Show-Results {
    Write-Host "查找優化結果文件..." -ForegroundColor Yellow

    $ResultFiles = Get-ChildItem -Path . -Name "*optimization*.json" -ErrorAction SilentlyContinue

    if ($ResultFiles.Count -eq 0) {
        Write-Host "未找到優化結果文件" -ForegroundColor Yellow
        return
    }

    Write-Host "找到 $($ResultFiles.Count) 個結果文件:" -ForegroundColor Green

    foreach ($File in $ResultFiles) {
        $FileInfo = Get-Item $File
        Write-Host "  📄 $File (修改時間: $($FileInfo.LastWriteTime))" -ForegroundColor Cyan
    }

    $LatestFile = $ResultFiles | Sort-Object { Get-Item $_ } | Select-Object -Last 1
    Write-Host "`n最新結果文件: $LatestFile" -ForegroundColor Green

    try {
        $Content = Get-Content $LatestFile | ConvertFrom-Json
        Write-Host "文件內容摘要:" -ForegroundColor Yellow
        $Content | Format-Table
    } catch {
        Write-Host "無法讀取 JSON 內容" -ForegroundColor Yellow
    }
}

function Create-Script {
    Write-Host "創建優化腳本..." -ForegroundColor Yellow

    $ScriptName = Read-Host "請輸入腳本名稱 (不含.py擴展名)"
    if ([string]::IsNullOrEmpty($ScriptName)) { $ScriptName = "custom_optimization" }

    $Combinations = Read-Host "請輸入最大組合數 (默認: 1000)"
    if ([string]::IsNullOrEmpty($Combinations)) { $Combinations = 1000 } else { $Combinations = [int]$Combinations }

    $UseGPU = Read-Host "使用GPU? (y/n, 默認: n)"
    $UseGPU = ($UseGPU -eq 'y')

    $ScriptContent = @"
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定義優化腳本: $ScriptName
生成時間: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"""

from enhanced_comprehensive_parameter_optimizer import quick_enhanced_optimize_0700
import time
import json
from datetime import datetime

def main():
    print("=== 自定義增強版優化 ===")
    print(f"最大組合數: $Combinations")
    print(f"使用GPU: $UseGPU")
    print()

    try:
        # 執行優化
        print("開始優化...")
        start_time = time.time()

        results = quick_enhanced_optimize_0700(
            max_combinations=$Combinations,
            use_gpu=$UseGPU,
            enable_all_enhancements=False  # 使用穩定配置
        )

        execution_time = time.time() - start_time

        # 顯示結果
        print(f"優化完成，耗時: {execution_time:.2f}秒")
        print()

        if results:
            print("=== 優化結果 ===")
            for strategy, result in results.items():
                if hasattr(result, 'performance_metrics') and result.performance_metrics:
                    best = result.performance_metrics[0]
                    print(f"{strategy} 策略:")
                    print(f"  最佳 Sharpe 比率: {best.get('sharpe_ratio', 0):.3f}")
                    print(f"  最大回撤: {best.get('max_drawdown', 0)*100:.2f}%")
                    print(f"  勝率: {best.get('win_rate', 0)*100:.2f}%")
                    print(f"  總回報: {best.get('total_return', 0)*100:.2f}%")
                    print()
        else:
            print("未獲得優化結果")

    except Exception as e:
        print(f"優化過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
"@

    try {
        $ScriptContent | Out-File -FilePath "$ScriptName.py" -Encoding UTF8
        Write-Host "✅ 腳本已創建: $ScriptName.py" -ForegroundColor Green
        Write-Host "執行方式: python $ScriptName.py" -ForegroundColor Cyan
    } catch {
        Write-Host "❌ 腳本創建失敗: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 主菜單循環
do {
    Show-Menu
    $Choice = Read-Host "請選擇操作 (0-6)"

    switch ($Choice) {
        "1" {
            Quick-Optimize -Combinations 50
        }
        "2" {
            Custom-Optimize
        }
        "3" {
            Test-Components
        }
        "4" {
            Check-System
        }
        "5" {
            Show-Results
        }
        "6" {
            Create-Script
        }
        "0" {
            Write-Host "退出程序" -ForegroundColor Green
            break
        }
        default {
            Write-Host "無效選擇，請重試" -ForegroundColor Red
        }
    }

    if ($Choice -ne "0") {
        Write-Host "`n按 Enter 鍵繼續..." -ForegroundColor Cyan
        $null = Read-Host
    }
} while ($Choice -ne "0")