# 系统要求 - Enhanced Non-Price TA System

## 📖 概述

本文档详细说明Enhanced Non-Price Technical Analysis System的软硬件系统要求，确保系统在各种环境下都能稳定高效运行。

## 💻 硬件要求

### 最低配置要求
**适用场景**: 开发测试、小规模使用

| 组件 | 最低要求 | 推荐配置 | 说明 |
|------|----------|----------|------|
| **CPU** | 4核 2.0GHz+ | 8核 3.0GHz+ | 支持多线程并行计算 |
| **内存** | 8GB RAM | 16GB+ RAM | 缓存和数据处理需要 |
| **存储** | 50GB 可用空间 | 100GB+ SSD | 系统安装和数据存储 |
| **网络** | 稳定互联网连接 | 100Mbps+ | 访问外部API数据源 |

### 生产环境推荐配置
**适用场景**: 中等规模、高负载使用

| 组件 | 推荐配置 | 高性能配置 | 说明 |
|------|----------|------------|------|
| **CPU** | 16核 3.0GHz+ | 32核 3.5GHz+ | 32核并行处理能力 |
| **内存** | 32GB+ RAM | 64GB+ RAM | 大量缓存和并发处理 |
| **存储** | 200GB+ SSD | 500GB+ NVMe SSD | 高速I/O，减少延迟 |
| **网络** | 1Gbps+ | 10Gbps+ | 高速数据传输 |
| **备份存储** | 500GB+ | 1TB+ | 数据备份和归档 |

### 云平台配置建议

#### AWS 配置
```
# 小规模部署
实例类型: t3.xlarge (4 vCPU, 16GB RAM)
存储类型: gp3 (100GB)
网络: 中等带宽

# 生产环境
实例类型: c6i.4xlarge (16 vCPU, 32GB RAM)
存储类型: io2 Block Express (500GB, 10,000 IOPS)
网络: 增强网络
```

#### Azure 配置
```
# 小规模部署
实例类型: Standard_D4s_v5 (4 vCPU, 16GB RAM)
存储类型: Premium SSD P10 (128GB)
网络: 标准带宽

# 生产环境
实例类型: Standard_D16s_v5 (16 vCPU, 64GB RAM)
存储类型: Premium SSD P30 (1TB)
网络: 加速网络
```

#### GCP 配置
```
# 小规模部署
实例类型: n2-highmem-4 (4 vCPU, 32GB RAM)
存储类型: pd-ssd (100GB)
网络: 标准网络层级

# 生产环境
实例类型: n2-highmem-16 (16 vCPU, 128GB RAM)
存储类型: pd-ssd (500GB)
网络: 高性能网络层级
```

## 🛠️ 软件要求

### 操作系统支持

#### Windows 系统
| 版本 | 支持状态 | 备注 |
|------|----------|------|
| Windows 10 | ✅ 完全支持 | Build 1903+ |
| Windows 11 | ✅ 完全支持 | 所有版本 |
| Windows Server 2019 | ✅ 完全支持 | Standard/Datacenter |
| Windows Server 2022 | ✅ 完全支持 | Standard/Datacenter |

#### Linux 系统
| 发行版 | 版本 | 支持状态 | 备注 |
|--------|------|----------|------|
| Ubuntu | 20.04 LTS | ✅ 完全支持 | 推荐版本 |
| Ubuntu | 22.04 LTS | ✅ 完全支持 | 最新LTS |
| Ubuntu | 24.04 LTS | ✅ 完全支持 | 最新版本 |
| CentOS | 7.x | ✅ 支持 | 需要额外依赖 |
| CentOS Stream | 8/9 | ✅ 完全支持 | 推荐Stream 9 |
| RHEL | 8.x | ✅ 支持 | 需要订阅 |
| RHEL | 9.x | ✅ 完全支持 | 企业级支持 |
| Debian | 11.x | ✅ 支持 | 需要额外配置 |
| Debian | 12.x | ✅ 完全支持 | 稳定版本 |

#### macOS 系统
| 版本 | 支持状态 | 备注 |
|------|----------|------|
| macOS 11 (Big Sur) | ✅ 支持 | Intel芯片 |
| macOS 12 (Monterey) | ✅ 支持 | Intel/Apple Silicon |
| macOS 13 (Ventura) | ✅ 完全支持 | Intel/Apple Silicon |
| macOS 14 (Sonoma) | ✅ 完全支持 | Intel/Apple Silicon |

### Python 环境
```
Python版本: 3.9, 3.10, 3.11, 3.12 (推荐 3.11)
包管理器: pip 21.0+
虚拟环境: venv, conda, poetry (推荐 venv)
```

### 核心依赖包

#### 数据处理
```
pandas >= 2.0.0          # 数据分析
numpy >= 1.24.0          # 数值计算
scipy >= 1.10.0          # 科学计算
```

#### 网络请求
```
requests >= 2.31.0       # HTTP请求
aiohttp >= 3.8.0         # 异步HTTP
urllib3 >= 2.0.0         # URL处理
```

#### 技术分析
```
vectorbt >= 0.25.0       # 向量回测
TA-Lib >= 0.4.28         # 技术分析库
scikit-learn >= 1.3.0    # 机器学习
```

#### 性能优化
```
numba >= 0.57.0          # JIT编译
cython >= 3.0.0          # C扩展
multiprocessing-logging  # 多进程日志
```

#### 数据存储
```
sqlite3 >= 3.40.0        # 内置
redis >= 4.5.0           # 缓存 (可选)
postgresql-adapter       # 数据库适配器 (可选)
```

## 🌐 网络要求

### 带宽要求
- **最低带宽**: 10Mbps (稳定连接)
- **推荐带宽**: 100Mbps+ (生产环境)
- **高性能**: 1Gbps+ (大规模部署)

### 端口要求
| 端口 | 用途 | 必需性 | 说明 |
|------|------|--------|------|
| 80/443 | HTTP/HTTPS | 可选 | Web界面访问 |
| 8001 | 数据API服务 | 推荐 | 本地数据服务 |
| 9000 | 业务逻辑服务 | 推荐 | 核心分析服务 |
| 3005 | 表现层接口 | 可选 | 前端数据接口 |
| 6379 | Redis缓存 | 可选 | 缓存服务 |
| 5432 | PostgreSQL | 可选 | 数据库服务 |

### 外部数据源访问
系统需要访问以下外部数据源，确保网络连接畅通：

#### 股票数据API
```
主数据源: http://18.180.162.113:9191
协议: HTTP
端口: 9191
用途: 获取港股实时和历史数据
```

#### 香港政府数据API
```
HKMA API: https://api.hkma.gov.hk
协议: HTTPS
端口: 443
用途: 获取政府经济数据
访问频率: 建议限制在合理范围内
```

### 防火墙配置
```bash
# Ubuntu/Debian
sudo ufw allow 8001/tcp
sudo ufw allow 9000/tcp
sudo ufw allow 3005/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8001/tcp
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --permanent --add-port=3005/tcp
sudo firewall-cmd --reload

# Windows (管理员权限)
netsh advfirewall firewall add rule name="TA System" dir=in action=allow protocol=TCP localport=8001,9000,3005
```

## 📁 存储要求

### 磁盘空间分配
```
系统安装: 2-5GB
Python环境: 1-3GB
依赖包: 500MB-1GB
缓存数据: 1-10GB (可配置)
日志文件: 100MB-1GB (可配置)
备份数据: 10-100GB (取决于数据量)
临时文件: 1-5GB
```

### 存储类型建议
- **系统盘**: SSD (推荐) 或 高速HDD
- **数据盘**: SSD (强烈推荐) 或 NVMe SSD
- **备份盘**: HDD (成本效益) 或 云存储

### 文件系统建议
- **Windows**: NTFS (支持大文件和权限控制)
- **Linux**: ext4 或 XFS (高性能)
- **macOS**: APFS (现代文件系统)

## 🔧 系统配置

### 操作系统优化

#### Linux 系统优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化网络参数
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p

# 禁用swap (推荐用于高性能)
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
```

#### Windows 系统优化
```powershell
# 设置虚拟内存 (PowerShell管理员权限)
$cs = Get-WmiObject -Class Win32_ComputerSystem
$cs.AutomaticManagedPagefile = $false
$cs.Put()

$pagefile = Get-WmiObject -Class Win32_PageFileSetting
$pagefile.InitialSize = 16384  # 16GB
$pagefile.MaximumSize = 32768  # 32GB
$pagefile.Put()
```

### 环境变量配置
```bash
# Linux/macOS (添加到 ~/.bashrc 或 ~/.zshrc)
export PYTHONPATH="${PYTHONPATH}:/path/to/enhanced_nonprice_ta_system"
export TA_SYSTEM_CONFIG="/path/to/config"
export TA_SYSTEM_CACHE_DIR="/path/to/cache"
export TA_SYSTEM_LOG_DIR="/path/to/logs"

# Windows (系统环境变量)
set PYTHONPATH=%PYTHONPATH%;C:\path\to\enhanced_nonprice_ta_system
set TA_SYSTEM_CONFIG=C:\path\to\config
set TA_SYSTEM_CACHE_DIR=C:\path\to\cache
set TA_SYSTEM_LOG_DIR=C:\path\to\logs
```

## 🔍 系统兼容性检查

### 自动检查脚本
```python
#!/usr/bin/env python3
"""
系统兼容性检查脚本
运行方式: python check_system_compatibility.py
"""

import sys
import platform
import subprocess
import psutil

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro} (兼容)")
        return True
    else:
        print(f"❌ Python版本: {version.major}.{version.minor}.{version.micro} (需要3.9+)")
        return False

def check_system_resources():
    """检查系统资源"""
    # CPU检查
    cpu_count = psutil.cpu_count()
    if cpu_count >= 4:
        print(f"✅ CPU核心数: {cpu_count} (满足最低要求)")
    else:
        print(f"⚠️ CPU核心数: {cpu_count} (推荐8核+)")
    
    # 内存检查
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024**3)
    if memory_gb >= 8:
        print(f"✅ 内存: {memory_gb:.1f}GB (满足最低要求)")
    else:
        print(f"❌ 内存: {memory_gb:.1f}GB (需要8GB+)")
        return False
    
    # 磁盘空间检查
    disk = psutil.disk_usage('/')
    disk_gb = disk.free / (1024**3)
    if disk_gb >= 50:
        print(f"✅ 可用磁盘空间: {disk_gb:.1f}GB (满足要求)")
    else:
        print(f"❌ 可用磁盘空间: {disk_gb:.1f}GB (需要50GB+)")
        return False
    
    return True

def check_network_connectivity():
    """检查网络连接"""
    import urllib.request
    import socket
    
    try:
        # 检查主数据源连接
        response = urllib.request.urlopen("http://18.180.162.113:9191", timeout=10)
        print("✅ 主数据源连接正常")
    except Exception as e:
        print(f"⚠️ 主数据源连接异常: {e}")
    
    try:
        # 检查HKMA连接
        response = urllib.request.urlopen("https://api.hkma.gov.hk", timeout=10)
        print("✅ HKMA数据源连接正常")
    except Exception as e:
        print(f"⚠️ HKMA数据源连接异常: {e}")

def main():
    """主检查函数"""
    print("🔍 Enhanced Non-Price TA System - 系统兼容性检查")
    print("=" * 60)
    
    # 检查操作系统
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    
    # 检查Python环境
    python_ok = check_python_version()
    
    # 检查系统资源
    resources_ok = check_system_resources()
    
    # 检查网络连接
    check_network_connectivity()
    
    print("\n" + "=" * 60)
    if python_ok and resources_ok:
        print("✅ 系统兼容性检查通过，可以安装系统")
    else:
        print("❌ 系统不满足要求，请升级硬件或软件")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 运行兼容性检查
```bash
# 下载并运行检查脚本
python check_system_compatibility.py

# 或使用curl直接运行
curl -s https://raw.githubusercontent.com/your-org/ta-system/main/check_system_compatibility.py | python
```

## 📋 部署前检查清单

### 硬件检查
- [ ] CPU: 4核+ (推荐8核+)
- [ ] 内存: 8GB+ (推荐16GB+)
- [ ] 存储: 50GB+ 可用空间 (推荐SSD)
- [ ] 网络: 稳定互联网连接

### 软件检查
- [ ] 操作系统: Windows 10+/Linux/macOS
- [ ] Python: 3.9+ (推荐3.11)
- [ ] 包管理器: pip 21.0+
- [ ] 必要的开发工具: git, make, gcc (Linux)

### 网络检查
- [ ] 可访问主数据源 (http://18.180.162.113:9191)
- [ ] 可访问HKMA数据源 (https://api.hkma.gov.hk)
- [ ] 防火墙配置正确
- [ ] 代理设置正确 (如需要)

### 权限检查
- [ ] 安装软件权限
- [ ] 创建目录权限
- [ ] 网络访问权限
- [ ] 系统配置权限

## 🚨 常见兼容性问题

### Python版本问题
**问题**: Python版本过低
**解决**: 升级到Python 3.9+
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv

# CentOS/RHEL
sudo yum install python311 python311-pip

# Windows
# 从python.org下载最新版本
```

### 依赖包安装失败
**问题**: 某些依赖包安装失败
**解决**: 安装系统依赖
```bash
# Ubuntu/Debian
sudo apt install build-essential python3-dev libpq-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel postgresql-devel

# macOS
xcode-select --install
brew install postgresql
```

### 网络连接问题
**问题**: 无法访问外部数据源
**解决**: 检查网络和防火墙设置
```bash
# 测试连接
curl -I http://18.180.162.113:9191
curl -I https://api.hkma.gov.hk

# 检查防火墙
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS
```

---

**🎯 确保系统满足所有要求后，继续下一步安装过程！**