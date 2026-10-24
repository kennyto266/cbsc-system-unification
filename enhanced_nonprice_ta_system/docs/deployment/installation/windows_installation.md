# Windows安装指南 - Enhanced Non-Price TA System

## 📖 概述

本指南详细介绍在Windows环境下安装和配置Enhanced Non-Price Technical Analysis System的完整步骤，适用于Windows 10/11和Windows Server系统。

## 🎯 系统要求

### 最低硬件要求
- **CPU**: 4核心 2.0GHz+
- **内存**: 8GB RAM (推荐16GB+)
- **存储**: 50GB可用空间 (推荐SSD)
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: Windows 10 (Build 1903+), Windows 11, Windows Server 2019/2022
- **Python**: 3.9+ (推荐3.11)
- **权限**: 管理员权限 (用于安装软件和配置系统)

## 🚀 安装步骤

### 步骤1: 环境准备

#### 1.1 安装Python
```powershell
# 方法1: 从Microsoft Store安装 (推荐)
# 1. 打开Microsoft Store
# 2. 搜索"Python 3.11"
# 3. 点击安装

# 方法2: 从python.org下载安装
# 1. 访问 https://www.python.org/downloads/
# 2. 下载Python 3.11.x Windows installer
# 3. 运行安装程序，勾选"Add Python to PATH"

# 方法3: 使用winget (Windows 10/11)
winget install Python.Python.3.11
```

#### 1.2 验证Python安装
```powershell
# 打开PowerShell或Command Prompt
python --version
# 应该显示: Python 3.11.x

pip --version
# 应该显示: pip 23.x.x from python

# 验证环境变量
echo $env:PATH
# 应该包含Python路径
```

#### 1.3 安装Git
```powershell
# 方法1: 使用winget
winget install Git.Git

# 方法2: 从官网下载安装
# 1. 访问 https://git-scm.com/download/win
# 2. 下载Git for Windows
# 3. 运行安装程序，使用默认设置

# 验证安装
git --version
```

#### 1.4 安装Visual Studio Build Tools (可选但推荐)
```powershell
# 下载并安装Visual Studio Build Tools
winget install Microsoft.VisualStudio.2022.BuildTools

# 或者安装完整的Visual Studio Community
winget install Microsoft.VisualStudio.2022.Community
```

### 步骤2: 获取系统代码

#### 2.1 克隆项目仓库
```powershell
# 创建工作目录
mkdir C:\TA_System
cd C:\TA_System

# 克隆项目 (替换为实际的仓库地址)
git clone https://github.com/your-org/enhanced_nonprice_ta_system.git

# 进入项目目录
cd enhanced_nonprice_ta_system
```

#### 2.2 验证项目结构
```powershell
# 查看项目结构
dir

# 应该包含以下文件/目录:
# - README.md
# - requirements.txt
# - setup.py
# - enhanced_nonprice_ta_system/
# - config/
# - tests/
```

### 步骤3: 创建Python虚拟环境

```powershell
# 在项目根目录创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 验证激活 (命令行前面应该有(venv))
python -c "import sys; print(sys.prefix)"
# 应该显示虚拟环境路径
```

### 步骤4: 安装依赖包

#### 4.1 升级pip
```powershell
# 升级pip到最新版本
python -m pip install --upgrade pip
```

#### 4.2 安装系统依赖
```powershell
# 如果有Visual Studio Build Tools，可以直接安装
# 否则，可能需要预编译的wheel包

# 安装基础依赖
pip install wheel setuptools

# 安装核心依赖
pip install numpy pandas scipy
```

#### 4.3 安装项目依赖
```powershell
# 从requirements.txt安装所有依赖
pip install -r requirements.txt

# 如果某些包安装失败，尝试以下方法:

# 方法1: 使用预编译wheel
pip install --only-binary=all -r requirements.txt

# 方法2: 分步安装
pip install numpy
pip install pandas
pip install requests aiohttp
pip install scikit-learn
pip install vectorbt

# 方法3: 指定镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### 步骤5: 配置系统

#### 5.1 创建配置文件
```powershell
# 复制示例配置文件
copy config\config.example.yml config\config.yml

# 创建必要目录
mkdir data
mkdir logs
mkdir cache
mkdir reports
```

#### 5.2 编辑配置文件
```powershell
# 使用记事本或其他编辑器编辑配置
notepad config\config.yml
```

**基本配置示例**:
```yaml
# config/config.yml
system:
  name: "Enhanced Non-Price TA System"
  version: "1.0.0"
  environment: "production"
  
data_sources:
  stock_api:
    base_url: "http://18.180.162.113:9191"
    timeout: 30
    retry_attempts: 3
    
  government_data:
    hibor_url: "https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ihb"
    cache_ttl_hours: 24
    
performance:
  parallel_cores: 8  # 根据CPU核心数调整
  memory_limit_gb: 8  # 根据可用内存调整
  cache_enabled: true
  
logging:
  level: "INFO"
  file: "logs/system.log"
  max_size_mb: 100
  backup_count: 5
  
paths:
  data_dir: "C:/TA_System/data"
  cache_dir: "C:/TA_System/cache"
  log_dir: "C:/TA_System/logs"
  report_dir: "C:/TA_System/reports"
```

### 步骤6: 系统测试

#### 6.1 运行基础测试
```powershell
# 激活虚拟环境 (如果未激活)
.\venv\Scripts\Activate.ps1

# 运行系统测试
python -m pytest tests/ -v

# 或运行简单的验证脚本
python -c "
from enhanced_nonprice_ta_system import CoreOptimizerEngine
print('✅ 系统导入成功')
engine = CoreOptimizerEngine()
print('✅ 核心引擎创建成功')
"
```

#### 6.2 运行集成测试
```powershell
# 运行完整的集成测试
python test_enhanced_system.py

# 或运行演示程序
python demo_enhanced_system.py
```

### 步骤7: 验证功能

#### 7.1 测试数据获取
```powershell
# 创建测试脚本 test_data_fetch.py
@"
from enhanced_nonprice_ta_system import EnhancedDataManager
import asyncio

async def test_data():
    dm = EnhancedDataManager()
    
    # 测试股票数据获取
    stock_data = dm.fetch_stock_data('0700.hk', 30)
    print(f'股票数据: {len(stock_data)} 条记录')
    
    # 测试政府数据获取
    gov_data = await dm.fetch_all_government_data(30)
    print(f'政府数据源: {len(gov_data)} 个')

asyncio.run(test_data())
"@ | Out-File -FilePath test_data_fetch.py -Encoding UTF8

# 运行测试
python test_data_fetch.py
```

#### 7.2 测试核心功能
```powershell
# 创建功能测试脚本
@"
from enhanced_nonprice_ta_system import CoreOptimizerEngine

def test_core_functionality():
    engine = CoreOptimizerEngine()
    
    # 测试快速优化
    results = engine.run_enhanced_optimization('0700.hk', parallel_cores=4)
    
    print(f'✅ 优化完成: {results.total_strategies_tested} 个策略')
    if results.top_strategies:
        best = results.top_strategies[0]
        print(f'✅ 最佳策略: {best.name}, Sharpe: {best.sharpe_ratio:.3f}')
    
    return True

test_core_functionality()
print('✅ 核心功能测试通过')
"@ | Out-File -FilePath test_core.py -Encoding UTF8

# 运行测试
python test_core.py
```

## 🔧 高级配置

### 配置Windows服务 (可选)

#### 1. 创建服务脚本
```powershell
# 创建 run_service.py
@"
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_nonprice_ta_system.main import main
import logging

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
"@ | Out-File -FilePath run_service.py -Encoding UTF8
```

#### 2. 使用NSSM安装为Windows服务
```powershell
# 下载NSSM (Non-Sucking Service Manager)
# https://nssm.cc/download

# 安装服务 (管理员权限)
nssm install "TA-System" "C:\TA_System\venv\Scripts\python.exe" "C:\TA_System\run_service.py"

# 设置服务参数
nssm set "TA-System" AppDirectory "C:\TA_System"
nssm set "TA-System" DisplayName "Enhanced Non-Price TA System"
nssm set "TA-System" Description "Technical Analysis System"
nssm set "TA-System" Start SERVICE_AUTO_START

# 启动服务
nssm start "TA-System"
```

### 配置计划任务

#### 创建定时任务
```powershell
# 创建备份脚本
@"
# backup_data.ps1
$backupDir = "C:\TA_System\backups"
$dataDir = "C:\TA_System\data"
$cacheDir = "C:\TA_System\cache"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$backupDir\backup_$timestamp.zip"

# 创建备份目录
New-Item -ItemType Directory -Force -Path $backupDir

# 压缩备份
Compress-Archive -Path $dataDir, $cacheDir -DestinationPath $backupFile

# 删除7天前的备份
Get-ChildItem $backupDir -Filter "backup_*.zip" | 
    Where-Object CreationTime -lt (Get-Date).AddDays(-7) | 
    Remove-Item -Force

Write-Host "备份完成: $backupFile"
"@ | Out-File -FilePath backup_data.ps1 -Encoding UTF8

# 创建计划任务 (管理员权限)
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\TA_System\backup_data.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

Register-ScheduledTask -TaskName "TA-System-Backup" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest
```

## 🔍 故障排除

### 常见安装问题

#### 问题1: Python环境变量问题
**症状**: `python` 命令未找到
```powershell
# 解决方案: 手动添加环境变量
$pythonPath = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\"
$pythonPath += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\Scripts\"

[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";" + $pythonPath, "User")

# 重新启动PowerShell
```

#### 问题2: 依赖包安装失败
**症状**: pip install 报错
```powershell
# 解决方案1: 使用预编译包
pip install --only-binary=all package_name

# 解决方案2: 更换pip源
pip install -i https://pypi.douban.com/simple/ package_name

# 解决方案3: 升级pip和setuptools
python -m pip install --upgrade pip setuptools wheel

# 解决方案4: 安装Visual C++ Build Tools
# 下载并安装 Microsoft C++ Build Tools
```

#### 问题3: 权限问题
**症状**: 无法创建文件或目录
```powershell
# 解决方案: 以管理员身份运行PowerShell
# 右键点击PowerShell -> "以管理员身份运行"

# 或者修改目录权限
icacls "C:\TA_System" /grant "$env:USERNAME:(OI)(CI)F"
```

#### 问题4: 网络连接问题
**症状**: 无法访问外部数据源
```powershell
# 测试网络连接
Test-NetConnection -ComputerName "18.180.162.113" -Port 9191
Test-NetConnection -ComputerName "api.hkma.gov.hk" -Port 443

# 如果使用代理，设置环境变量
$env:HTTP_PROXY = "http://proxy.company.com:8080"
$env:HTTPS_PROXY = "http://proxy.company.com:8080"
```

### 性能优化建议

#### 1. Windows性能设置
```powershell
# 设置为高性能电源计划
powercfg -setactive scheme_min

# 禁用Windows Defender实时保护 (仅限开发环境)
Set-MpPreference -DisableRealtimeMonitoring $true

# 优化虚拟内存
$cs = Get-WmiObject -Class Win32_ComputerSystem
$cs.AutomaticManagedPagefile = $false
$cs.Put()

$pagefile = Get-WmiObject -Class Win32_PageFileSetting
$pagefile.InitialSize = 16384  # 16GB
$pagefile.MaximumSize = 32768  # 32GB
$pagefile.Put()
```

#### 2. Python性能优化
```powershell
# 设置Python优化标志
$env:PYTHONOPTIMIZE = "2"
$env:PYTHONUTF8 = "1"

# 启用JIT编译 (如果使用PyPy)
# 安装PyPy并替换Python解释器
```

## 📋 安装验证清单

### 基础环境检查
- [ ] Python 3.9+ 已安装并可访问
- [ ] pip 已安装并更新到最新版本
- [ ] Git 已安装
- [ ] 虚拟环境已创建并激活
- [ ] 项目代码已成功克隆

### 依赖安装检查
- [ ] 所有requirements.txt中的包已安装
- [ ] 核心模块可正常导入
- [ ] 无版本冲突或兼容性问题

### 功能验证检查
- [ ] 数据获取功能正常
- [ ] 指标计算功能正常
- [ ] 优化引擎功能正常
- [ ] 缓存系统功能正常
- [ ] 错误处理功能正常

### 配置检查
- [ ] 配置文件已创建并编辑
- [ ] 目录结构正确
- [ ] 环境变量设置正确
- [ ] 网络连接正常

## 🚀 下一步

安装完成后，您可以：

1. **查看用户指南**: 阅读详细的用户使用文档
2. **运行演示**: 执行 `python demo_enhanced_system.py`
3. **开始优化**: 使用QuickOptimizer进行策略优化
4. **配置监控**: 设置系统监控和警报
5. **定期维护**: 配置自动备份和更新

## 📞 技术支持

如果在安装过程中遇到问题：

1. **查看日志**: 检查 `logs/` 目录下的日志文件
2. **运行诊断**: 使用兼容性检查脚本
3. **查阅文档**: 参考故障排除指南
4. **社区支持**: 访问项目GitHub Issues
5. **专业支持**: 联系技术支持团队

---

**🎉 恭喜！您已成功在Windows上安装Enhanced Non-Price TA System！**