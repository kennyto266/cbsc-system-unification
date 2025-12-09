# 常见问题解决 - Enhanced Non-Price TA System

## 📖 概述

本文档收集了Enhanced Non-Price Technical Analysis System用户最常遇到的问题及其解决方案，涵盖安装、配置、使用等各个环节的常见故障。

## 🔍 问题分类

### 📋 问题快速导航
```
问题分类树
├── 安装部署问题 (Installation & Deployment)
│   ├── Python环境问题
│   ├── 依赖包问题
│   ├── 系统兼容性问题
│   └── 配置文件问题
├── 数据获取问题 (Data Acquisition)
│   ├── 股票数据问题
│   ├── 政府数据问题
│   ├── 网络连接问题
│   └── 数据质量问题
├── 算法计算问题 (Algorithm & Calculation)
│   ├── 指标计算错误
│   ├── 优化过程问题
│   ├── 内存溢出问题
│   └── 并发计算问题
├── 性能问题 (Performance Issues)
│   ├── 运行速度慢
│   ├── 内存占用高
│   ├── CPU使用率低
│   └── 缓存效率低
└── 结果分析问题 (Result Analysis)
    ├── 异常结果处理
    ├── 数据解读困惑
    ├── 策略验证失败
    └── 报告生成问题
```

## 🚀 安装部署问题

### 问题1: Python版本不兼容

#### 症状描述
```
ERROR: Package requires a different Python: 3.8.0 not in '>=3.9'
```

#### 原因分析
- 系统Python版本低于3.9
- 多个Python版本冲突
- 虚拟环境Python版本错误

#### 解决方案
```bash
# 1. 检查当前Python版本
python --version
python3 --version

# 2. 安装Python 3.9+
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv

# CentOS/RHEL
sudo yum install python311 python311-pip

# Windows
# 从 https://www.python.org/downloads/ 下载Python 3.11+

# macOS
brew install python@3.11

# 3. 创建指定版本的虚拟环境
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\Activate.ps1  # Windows

# 4. 验证虚拟环境Python版本
python --version  # 应该显示 3.11.x
```

#### 预防措施
- 始终在虚拟环境中开发
- 使用pyenv管理多个Python版本
- 在requirements.txt中指定Python版本要求

---

### 问题2: 依赖包安装失败

#### 症状描述
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

#### 原因分析
- 系统权限不足
- 网络连接问题
- 编译工具缺失
- 包版本冲突

#### 解决方案
```bash
# 1. 权限问题解决
# 方案A: 使用用户级安装
pip install --user package_name

# 方案B: 使用虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 方案C: 管理员权限安装 (不推荐)
sudo pip install package_name

# 2. 网络问题解决
# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package_name

# 配置永久镜像源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 编译工具问题
# Ubuntu/Debian
sudo apt update
sudo apt install build-essential python3-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel

# macOS
xcode-select --install
brew install gcc

# 4. 版本冲突解决
# 升级pip和setuptools
python -m pip install --upgrade pip setuptools wheel

# 清理缓存后重新安装
pip cache purge
pip install --no-cache-dir package_name
```

#### 专用包安装解决方案
```bash
# TA-Lib 安装 (常见问题包)
# Ubuntu/Debian
sudo apt install ta-lib-lib-dev

# CentOS/RHEL
sudo yum install ta-lib-devel

# macOS
brew install ta-lib

# Windows
# 从 https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib 下载预编译wheel

# 或使用conda
conda install -c conda-forge ta-lib

# 如果仍然失败，使用备选方案
pip install ta-lib-binary
```

---

### 问题3: 配置文件错误

#### 症状描述
```
FileNotFoundError: [Errno 2] No such file or directory: 'config/config.yml'
```

#### 原因分析
- 配置文件不存在
- 配置文件路径错误
- 配置文件格式错误
- 权限问题

#### 解决方案
```python
# 1. 检查配置文件是否存在
import os
config_path = "config/config.yml"
print(f"配置文件存在: {os.path.exists(config_path)}")
print(f"配置文件路径: {os.path.abspath(config_path)}")

# 2. 创建默认配置文件
import shutil

def create_default_config():
    """创建默认配置文件"""
    default_config = """# Enhanced Non-Price TA System Configuration
system:
  name: "Enhanced Non-Price TA System"
  version: "1.0.0"
  environment: "development"
  
data_sources:
  stock_api:
    base_url: "http://18.180.162.113:9191"
    timeout: 30
    retry_attempts: 3
    
  government_data:
    hibor_url: "https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ihb"
    cache_ttl_hours: 24
    
performance:
  parallel_cores: 8
  memory_limit_gb: 8
  cache_enabled: true
  
logging:
  level: "INFO"
  file: "logs/system.log"
  max_size_mb: 100
  backup_count: 5
  
paths:
  data_dir: "./data"
  cache_dir: "./cache"
  log_dir: "./logs"
  report_dir: "./reports"
"""
    
    # 确保目录存在
    os.makedirs("config", exist_ok=True)
    
    # 写入配置文件
    with open("config/config.yml", "w", encoding="utf-8") as f:
        f.write(default_config)
    
    print("✅ 默认配置文件已创建")

# 创建配置文件
create_default_config()
```

#### 配置文件验证
```python
import yaml

def validate_config():
    """验证配置文件"""
    try:
        with open("config/config.yml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # 检查必要配置项
        required_keys = ["system", "data_sources", "performance", "paths"]
        for key in required_keys:
            if key not in config:
                print(f"❌ 配置项缺失: {key}")
                return False
        
        print("✅ 配置文件验证通过")
        return True
        
    except FileNotFoundError:
        print("❌ 配置文件不存在")
        return False
    except yaml.YAMLError as e:
        print(f"❌ 配置文件格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 配置文件验证失败: {e}")
        return False

# 验证配置
validate_config()
```

---

## 📊 数据获取问题

### 问题4: 股票数据获取失败

#### 症状描述
```
ConnectionError: Failed to establish connection to 18.180.162.113:9191
```

#### 原因分析
- 网络连接问题
- API端点变更
- 防火墙拦截
- 服务器维护

#### 解决方案
```python
import requests
import time
from urllib.parse import urljoin

class StockDataFetcher:
    """增强的数据获取器"""
    
    def __init__(self):
        self.base_urls = [
            "http://18.180.162.113:9191",  # 主数据源
            "http://backup-api.example.com:9191",  # 备用数据源1
            "http://alternative-api.example.com:9191"  # 备用数据源2
        ]
        self.timeout = 30
        self.max_retries = 3
    
    def fetch_with_fallback(self, symbol, days=365):
        """带回退机制的数据获取"""
        for attempt in range(self.max_retries):
            for url in self.base_urls:
                try:
                    print(f"尝试数据源 {url} (第 {attempt + 1} 次)")
                    
                    # 构建请求URL
                    endpoint = f"/inst/getInst?symbol={symbol.lower()}&duration={days}"
                    full_url = urljoin(url, endpoint)
                    
                    # 发送请求
                    response = requests.get(
                        full_url,
                        timeout=self.timeout,
                        headers={
                            'User-Agent': 'Enhanced-TA-System/1.0'
                        }
                    )
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    print(f"✅ 数据获取成功: {len(data.get('data', {}).get('close', {}))} 条记录")
                    return self._parse_data(data)
                    
                except requests.exceptions.ConnectionError as e:
                    print(f"❌ 连接失败 {url}: {e}")
                    continue
                except requests.exceptions.Timeout as e:
                    print(f"❌ 请求超时 {url}: {e}")
                    continue
                except requests.exceptions.RequestException as e:
                    print(f"❌ 请求错误 {url}: {e}")
                    continue
                except Exception as e:
                    print(f"❌ 未知错误 {url}: {e}")
                    continue
            
            # 如果所有URL都失败，等待后重试
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        # 所有尝试都失败，使用模拟数据
        print("⚠️ 所有数据源都失败，使用模拟数据")
        return self._generate_mock_data(symbol, days)
    
    def _parse_data(self, raw_data):
        """解析原始数据"""
        try:
            data = raw_data.get('data', {})
            close_data = data.get('close', {})
            
            if not close_data:
                raise ValueError("数据格式错误")
            
            # 转换为DataFrame
            dates = list(close_data.keys())
            prices = list(close_data.values())
            
            df = pd.DataFrame({
                'date': dates,
                'close': prices
            })
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            print(f"❌ 数据解析失败: {e}")
            raise
    
    def _generate_mock_data(self, symbol, days):
        """生成模拟数据"""
        import numpy as np
        import pandas as pd
        
        print(f"🔧 生成 {symbol} 模拟数据 ({days} 天)")
        
        # 生成日期范围
        end_date = pd.Timestamp.now()
        dates = pd.date_range(end=end_date, periods=days, freq='D')
        
        # 生成随机价格数据
        np.random.seed(42)  # 确保可重复性
        base_price = 300  # 基础价格
        
        # 生成价格走势（包含趋势和随机波动）
        returns = np.random.normal(0.001, 0.02, days)  # 日收益率
        prices = [base_price]
        
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 10))  # 确保价格为正
        
        # 生成其他OHLCV数据
        data = []
        for i, date in enumerate(dates):
            close_price = prices[i]
            
            # 生成开盘价（基于前一日收盘价）
            if i == 0:
                open_price = close_price
            else:
                open_price = prices[i-1] * (1 + np.random.normal(0, 0.005))
            
            # 生成高低价
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
            
            # 生成成交量
            volume = int(np.random.lognormal(15, 1))  # 对数正态分布
            
            data.append({
                'date': date,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        
        print(f"✅ 模拟数据生成完成: {len(df)} 条记录")
        return df

# 使用增强数据获取器
def fetch_stock_data_safely(symbol="0700.hk", days=365):
    """安全获取股票数据"""
    fetcher = StockDataFetcher()
    return fetcher.fetch_with_fallback(symbol, days)

# 测试数据获取
# stock_data = fetch_stock_data_safely()
```

#### 网络诊断工具
```python
def diagnose_network_connectivity():
    """网络连接诊断"""
    import socket
    import requests
    
    print("🔍 网络连接诊断:")
    
    # 1. 基础网络连通性
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        print("✅ 基础网络连接正常")
    except Exception as e:
        print(f"❌ 基础网络连接失败: {e}")
        return False
    
    # 2. DNS解析
    try:
        socket.gethostbyname("18.180.162.113")
        print("✅ DNS解析正常")
    except Exception as e:
        print(f"❌ DNS解析失败: {e}")
        return False
    
    # 3. HTTP连接测试
    test_urls = [
        "http://18.180.162.113:9191",
        "https://www.google.com",
        "https://api.hkma.gov.hk"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ {url}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {e}")
    
    # 4. 端口扫描
    target_host = "18.180.162.113"
    target_port = 9191
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((target_host, target_port))
        sock.close()
        
        if result == 0:
            print(f"✅ 端口 {target_port} 开放")
        else:
            print(f"❌ 端口 {target_port} 关闭或被阻断")
    except Exception as e:
        print(f"❌ 端口扫描失败: {e}")
    
    return True

# 运行网络诊断
# diagnose_network_connectivity()
```

---

### 问题5: 政府数据获取失败

#### 症状描述
```
HTTPError: 429 Client Error: Too Many Requests
```

#### 原因分析
- 请求频率过高
- API限制触发
- 数据源维护
- 认证问题

#### 解决方案
```python
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta

class GovernmentDataFetcher:
    """政府数据获取器"""
    
    def __init__(self):
        self.session = None
        self.rate_limiter = RateLimiter(calls_per_minute=30)  # 限制调用频率
        self.cache = {}
        self.cache_ttl = 3600  # 1小时缓存
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300
        )
        
        timeout = aiohttp.ClientTimeout(
            total=30,
            connect=10,
            sock_read=10
        )
        
        headers = {
            'User-Agent': 'Enhanced-TA-System/1.0',
            'Accept': 'application/json'
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def fetch_with_rate_limit(self, url, cache_key=None):
        """带频率限制和缓存的数据获取"""
        # 检查缓存
        if cache_key and cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                print(f"✅ 使用缓存数据: {cache_key}")
                return cached_data
        
        # 应用频率限制
        await self.rate_limiter.acquire()
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 更新缓存
                    if cache_key:
                        self.cache[cache_key] = (data, time.time())
                    
                    print(f"✅ 数据获取成功: {cache_key or url}")
                    return data
                
                elif response.status == 429:
                    # 请求过于频繁，等待后重试
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"⏳ 请求过于频繁，等待 {retry_after} 秒...")
                    await asyncio.sleep(retry_after)
                    return await self.fetch_with_rate_limit(url, cache_key)
                
                elif response.status == 503:
                    # 服务不可用
                    print(f"⚠️ 服务不可用，使用备用数据")
                    return self._get_fallback_data(cache_key)
                
                else:
                    print(f"❌ HTTP错误 {response.status}: {await response.text()}")
                    return None
                    
        except asyncio.TimeoutError:
            print(f"❌ 请求超时: {url}")
            return self._get_fallback_data(cache_key)
        except Exception as e:
            print(f"❌ 请求异常: {url} - {e}")
            return self._get_fallback_data(cache_key)
    
    def _get_fallback_data(self, cache_key):
        """获取备用数据"""
        print(f"🔧 使用备用数据: {cache_key}")
        
        fallback_data = {
            'hibor': self._generate_fallback_hibor(),
            'monetary_base': self._generate_fallback_monetary_base(),
            'exchange_rate': self._generate_fallback_exchange_rate()
        }
        
        return fallback_data.get(cache_key, None)
    
    def _generate_fallback_hibor(self):
        """生成备用HIBOR数据"""
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(end=pd.Timestamp.now(), periods=365, freq='D')
        
        # 生成合理的HIBOR利率
        base_rate = 3.5
        rates = []
        
        for i, date in enumerate(dates):
            # 添加一些随机波动
            daily_change = np.random.normal(0, 0.05)
            rate = max(0.1, base_rate + daily_change)
            rates.append(rate)
        
        df = pd.DataFrame({
            'date': dates,
            'overnight': rates,
            'one_week': [r + np.random.normal(0.2, 0.1) for r in rates],
            'one_month': [r + np.random.normal(0.5, 0.2) for r in rates],
            'three_month': [r + np.random.normal(0.8, 0.3) for r in rates]
        })
        
        df.set_index('date', inplace=True)
        return df
    
    def _generate_fallback_monetary_base(self):
        """生成备用货币基础数据"""
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(end=pd.Timestamp.now(), periods=365, freq='D')
        
        # 模拟货币基础增长
        base_value = 2000000  # 20亿港币
        daily_growth_rate = 0.0002  # 0.02%日增长
        
        values = []
        for i, date in enumerate(dates):
            # 添加一些波动
            growth = daily_growth_rate + np.random.normal(0, 0.001)
            value = base_value * (1 + growth) ** i
            values.append(value)
        
        df = pd.DataFrame({
            'date': dates,
            'monetary_base': values
        })
        
        df.set_index('date', inplace=True)
        return df

class RateLimiter:
    """频率限制器"""
    
    def __init__(self, calls_per_minute=30):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    async def acquire(self):
        """获取调用许可"""
        now = time.time()
        
        # 清理过期的调用记录
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        # 检查是否超过限制
        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0])
            print(f"⏳ 达到频率限制，等待 {sleep_time:.1f} 秒...")
            await asyncio.sleep(sleep_time)
            return await self.acquire()
        
        # 记录本次调用
        self.calls.append(now)

# 使用示例
async def fetch_government_data_safely():
    """安全获取政府数据"""
    async with GovernmentDataFetcher() as fetcher:
        # HIBOR数据
        hibor_url = "https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ihb"
        hibor_data = await fetcher.fetch_with_rate_limit(hibor_url, "hibor")
        
        # 货币基础数据
        mb_url = "https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/mo/mo-dm-mb"
        mb_data = await fetcher.fetch_with_rate_limit(mb_url, "monetary_base")
        
        return {
            'hibor': hibor_data,
            'monetary_base': mb_data
        }

# 运行获取政府数据
# gov_data = asyncio.run(fetch_government_data_safely())
```

---

### 问题6: 数据质量问题

#### 症状描述
```
UserWarning: 数据中发现异常值: 价格跳跃超过50%
```

#### 原因分析
- 数据源错误
- 股票分割/合并
- 数据异常波动
- 缺失值处理不当

#### 解决方案
```python
import pandas as pd
import numpy as np
from scipy import stats

class DataQualityChecker:
    """数据质量检查器"""
    
    def __init__(self):
        self.quality_report = {}
        self.cleaning_actions = []
    
    def check_stock_data(self, data):
        """检查股票数据质量"""
        print("🔍 检查股票数据质量...")
        
        issues = []
        
        # 1. 检查缺失值
        missing_data = data.isnull().sum()
        if missing_data.any():
            issues.append(f"发现缺失值: {missing_data.to_dict()}")
        
        # 2. 检查异常价格跳跃
        price_jumps = self._detect_price_jumps(data)
        if price_jumps:
            issues.extend([f"价格跳跃: {jump}" for jump in price_jumps])
        
        # 3. 检查异常成交量
        volume_anomalies = self._detect_volume_anomalies(data)
        if volume_anomalies:
            issues.extend([f"成交量异常: {anomaly}" for anomaly in volume_anomalies])
        
        # 4. 检查数据连续性
        date_gaps = self._detect_date_gaps(data)
        if date_gaps:
            issues.extend([f"日期间隔: {gap}" for gap in date_gaps])
        
        # 5. 检查价格合理性
        price_reasonability = self._check_price_reasonability(data)
        if not price_reasonability['is_reasonable']:
            issues.append(f"价格不合理: {price_reasonability['reason']}")
        
        self.quality_report = {
            'total_records': len(data),
            'issues': issues,
            'quality_score': self._calculate_quality_score(len(issues), len(data)),
            'cleaning_recommended': len(issues) > 0
        }
        
        return self.quality_report
    
    def _detect_price_jumps(self, data, threshold=0.5):
        """检测价格异常跳跃"""
        jumps = []
        
        if 'close' not in data.columns:
            return jumps
        
        close_prices = data['close']
        returns = close_prices.pct_change().dropna()
        
        # 检测异常收益率
        z_scores = np.abs(stats.zscore(returns))
        anomaly_indices = np.where(z_scores > threshold)[0]
        
        for idx in anomaly_indices:
            if idx > 0 and idx < len(data):
                date = data.index[idx]
                price_change = returns.iloc[idx]
                prev_price = close_prices.iloc[idx-1]
                curr_price = close_prices.iloc[idx]
                
                jumps.append({
                    'date': date,
                    'price_change': f"{price_change:.2%}",
                    'previous_price': prev_price,
                    'current_price': curr_price,
                    'z_score': z_scores[idx]
                })
        
        return jumps
    
    def _detect_volume_anomalies(self, data):
        """检测成交量异常"""
        anomalies = []
        
        if 'volume' not in data.columns:
            return anomalies
        
        volumes = data['volume'].replace(0, np.nan).dropna()
        
        if len(volumes) == 0:
            return anomalies
        
        # 使用IQR方法检测异常值
        Q1 = volumes.quantile(0.25)
        Q3 = volumes.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 3 * IQR
        upper_bound = Q3 + 3 * IQR
        
        anomaly_mask = (volumes < lower_bound) | (volumes > upper_bound)
        anomaly_dates = data.index[anomaly_mask]
        
        for date in anomaly_dates:
            volume = data.loc[date, 'volume']
            anomalies.append({
                'date': date,
                'volume': volume,
                'reason': '超出正常范围' if volume > upper_bound else '异常低成交量'
            })
        
        return anomalies
    
    def _detect_date_gaps(self, data):
        """检测日期间隔"""
        gaps = []
        
        if len(data) < 2:
            return gaps
        
        # 计算日期间隔
        date_diffs = data.index.to_series().diff().dropna()
        
        # 正常情况下，交易日间隔最多为3天（考虑周末）
        large_gaps = date_diffs[date_diffs > pd.Timedelta(days=3)]
        
        for date, gap in large_gaps.items():
            gaps.append({
                'date': date,
                'gap_days': gap.days,
                'reason': f'{gap.days}天间隔，可能存在数据缺失'
            })
        
        return gaps
    
    def _check_price_reasonability(self, data):
        """检查价格合理性"""
        if 'close' not in data.columns:
            return {'is_reasonable': False, 'reason': '缺少价格数据'}
        
        prices = data['close']
        
        # 检查价格范围
        min_price = prices.min()
        max_price = prices.max()
        price_range = max_price / min_price - 1
        
        # 价格变化过大可能不合理
        if price_range > 10:  # 10倍变化
            return {
                'is_reasonable': False,
                'reason': f'价格范围过大: {price_range:.1f}倍'
            }
        
        # 检查价格是否为负或零
        if (prices <= 0).any():
            return {
                'is_reasonable': False,
                'reason': '发现非正价格'
            }
        
        # 检查价格是否过于集中（可能是模拟数据）
        price_std = prices.std()
        price_mean = prices.mean()
        cv = price_std / price_mean  # 变异系数
        
        if cv < 0.01:  # 变异系数过小
            return {
                'is_reasonable': False,
                'reason': f'价格变化过小，变异系数: {cv:.4f}'
            }
        
        return {'is_reasonable': True, 'reason': '价格数据正常'}
    
    def _calculate_quality_score(self, num_issues, num_records):
        """计算数据质量分数"""
        if num_issues == 0:
            return 10.0
        
        # 基础分数
        base_score = 10.0
        
        # 根据问题数量扣分
        issue_penalty = min(num_issues * 1.0, 8.0)
        
        # 根据数据量调整
        if num_records < 100:
            quantity_penalty = 2.0
        elif num_records < 252:  # 一年交易日
            quantity_penalty = 1.0
        else:
            quantity_penalty = 0.0
        
        final_score = max(0, base_score - issue_penalty - quantity_penalty)
        
        return round(final_score, 1)
    
    def clean_data(self, data):
        """数据清洗"""
        print("🧹 开始数据清洗...")
        
        cleaned_data = data.copy()
        original_len = len(cleaned_data)
        
        # 1. 处理缺失值
        if cleaned_data.isnull().any().any():
            print("  处理缺失值...")
            
            # 数值列使用前向填充
            numeric_columns = cleaned_data.select_dtypes(include=[np.number]).columns
            cleaned_data[numeric_columns] = cleaned_data[numeric_columns].fillna(method='ffill')
            
            # 如果仍然有缺失值，使用后向填充
            cleaned_data[numeric_columns] = cleaned_data[numeric_columns].fillna(method='bfill')
        
        # 2. 处理价格跳跃
        if 'close' in cleaned_data.columns:
            print("  处理价格跳跃...")
            
            # 计算日收益率
            returns = cleaned_data['close'].pct_change()
            
            # 标记异常值
            z_scores = np.abs(stats.zscore(returns.dropna()))
            anomaly_mask = z_scores > 3
            
            # 平滑异常值
            for i in range(1, len(cleaned_data)):
                if anomaly_mask.iloc[i] and not anomaly_mask.iloc[i-1]:
                    # 使用前一日的价格变化率
                    if i > 1:
                        prev_return = returns.iloc[i-1]
                        cleaned_data.loc[cleaned_data.index[i], 'close'] = (
                            cleaned_data.loc[cleaned_data.index[i-1], 'close'] * (1 + prev_return)
                    )
        
        # 3. 重新计算OHLC基于close价格
        if all(col in cleaned_data.columns for col in ['open', 'high', 'low', 'close']):
            print("  重新计算OHLC...")
            
            # 确保价格逻辑合理
            for i in range(len(cleaned_data)):
                row = cleaned_data.iloc[i]
                
                # 最高价不能低于最低价
                if row['high'] < row['low']:
                    cleaned_data.loc[cleaned_data.index[i], 'high'] = row['low']
                
                # 开盘价和收盘价应在高低价范围内
                cleaned_data.loc[cleaned_data.index[i], 'high'] = max(
                    row['high'], row['open'], row['close']
                )
                cleaned_data.loc[cleaned_data.index[i], 'low'] = min(
                    row['low'], row['open'], row['close']
                )
        
        # 4. 处理异常成交量
        if 'volume' in cleaned_data.columns:
            print("  处理异常成交量...")
            
            # 将零成交量替换为前一日成交量的中位数
            median_volume = cleaned_data[cleaned_data['volume'] > 0]['volume'].median()
            cleaned_data.loc[cleaned_data['volume'] == 0, 'volume'] = median_volume
            
            # 使用IQR方法处理极端异常值
            Q1 = cleaned_data['volume'].quantile(0.25)
            Q3 = cleaned_data['volume'].quantile(0.75)
            IQR = Q3 - Q1
            
            upper_bound = Q3 + 3 * IQR
            cleaned_data.loc[cleaned_data['volume'] > upper_bound, 'volume'] = upper_bound
        
        # 5. 移除重复的日期
        if cleaned_data.index.duplicated().any():
            print("  移除重复日期...")
            cleaned_data = cleaned_data[~cleaned_data.index.duplicated(keep='first')]
        
        final_len = len(cleaned_data)
        removed_records = original_len - final_len
        
        print(f"✅ 数据清洗完成:")
        print(f"  原始记录数: {original_len}")
        print(f"  清洗后记录数: {final_len}")
        print(f"  移除记录数: {removed_records}")
        
        # 重新检查清洗后的数据质量
        post_clean_report = self.check_stock_data(cleaned_data)
        
        print(f"  清洗后质量分数: {post_clean_report['quality_score']:.1f}/10")
        
        self.cleaning_actions = [
            "处理缺失值",
            "平滑价格跳跃", 
            "重新计算OHLC",
            "处理异常成交量",
            "移除重复日期"
        ]
        
        return cleaned_data

# 使用数据质量检查器
def ensure_data_quality(stock_data):
    """确保数据质量"""
    checker = DataQualityChecker()
    
    # 检查数据质量
    quality_report = checker.check_stock_data(stock_data)
    
    print(f"📊 数据质量报告:")
    print(f"  总记录数: {quality_report['total_records']}")
    print(f"  质量分数: {quality_report['quality_score']:.1f}/10")
    
    if quality_report['issues']:
        print(f"  发现问题: {len(quality_report['issues'])}")
        for issue in quality_report['issues']:
            print(f"    - {issue}")
    
    # 如果需要清洗
    if quality_report['cleaning_recommended']:
        print("\n🧹 推荐进行数据清洗...")
        cleaned_data = checker.clean_data(stock_data)
        return cleaned_data
    
    return stock_data

# 使用示例
# clean_stock_data = ensure_data_quality(tencent_data)
```

---

## ⚡ 性能问题

### 问题7: 系统运行速度慢

#### 症状描述
```
策略优化耗时超过预期: 600秒 (期望: 60秒)
```

#### 原因分析
- 并行处理未启用
- 缓存未启用
- 数据量大且未优化
- 算法实现效率低

#### 解决方案
```python
import time
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.baseline_time = None
        self.optimization_results = {}
    
    def profile_function(self, func, *args, **kwargs):
        """性能分析"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        self.baseline_time = execution_time
        
        print(f"⏱️ 函数 {func.__name__} 执行时间: {execution_time:.2f}秒")
        
        return result
    
    def optimize_parallel_processing(self, tasks, worker_func, max_workers=None):
        """优化并行处理"""
        if max_workers is None:
            max_workers = min(mp.cpu_count(), len(tasks))
        
        print(f"🚀 开始并行优化: {len(tasks)} 个任务, {max_workers} 个进程")
        
        # 基准测试 (单进程)
        start_time = time.time()
        for task in tasks[:min(10, len(tasks))]:  # 只测试前10个任务
            worker_func(task)
        baseline_time = time.time() - start_time
        
        # 并行处理
        start_time = time.time()
        results = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_task = {
                executor.submit(worker_func, task): task for task in tasks
            }
            
            # 收集结果
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"❌ 任务 {task} 执行失败: {e}")
        
        parallel_time = time.time() - start_time
        
        # 计算性能提升
        speedup = baseline_time / parallel_time if parallel_time > 0 else 0
        efficiency = speedup / max_workers if max_workers > 0 else 0
        
        print(f"📊 性能对比:")
        print(f"  单进程时间: {baseline_time:.2f}秒 (10个任务)")
        print(f"  并行时间: {parallel_time:.2f}秒 ({len(tasks)} 个任务)")
        print(f"  加速比: {speedup:.2f}x")
        print(f"  并行效率: {efficiency:.2%}")
        
        self.optimization_results['parallel_processing'] = {
            'baseline_time': baseline_time,
            'parallel_time': parallel_time,
            'speedup': speedup,
            'efficiency': efficiency
        }
        
        return results
    
    def optimize_numpy_operations(self, data):
        """优化NumPy操作"""
        print("🔧 优化NumPy操作...")
        
        # 测试原始方法
        def original_method(data):
            # 使用循环的原始方法
            result = []
            for i in range(len(data) - 1):
                result.append(data[i+1] - data[i])
            return np.array(result)
        
        # 测试向量化方法
        def vectorized_method(data):
            # 使用向量化操作
            return np.diff(data)
        
        # 性能对比
        test_data = np.random.random(100000)
        
        # 基准测试
        original_time = time.time()
        original_result = original_method(test_data)
        original_time = time.time() - original_time
        
        # 向量化测试
        vectorized_time = time.time()
        vectorized_result = vectorized_method(test_data)
        vectorized_time = time.time() - vectorized_time
        
        # 验证结果一致性
        if np.allclose(original_result, vectorized_result, rtol=1e-10):
            speedup = original_time / vectorized_time
            print(f"✅ 向量化优化成功，加速比: {speedup:.2f}x")
            print(f"  原始方法: {original_time:.4f}秒")
            print(f"  向量化方法: {vectorized_time:.4f}秒")
            
            self.optimization_results['vectorization'] = {
                'speedup': speedup,
                'original_time': original_time,
                'vectorized_time': vectorized_time
            }
        else:
            print("❌ 向量化结果不一致")
    
    def optimize_memory_usage(self, large_dataset):
        """优化内存使用"""
        print("💾 优化内存使用...")
        
        import psutil
        import gc
        
        # 记录初始内存使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 测试原始方法（加载所有数据到内存）
        def original_memory_usage():
            data_in_memory = []
            for chunk in large_dataset:
                data_in_memory.append(chunk.copy())
            return data_in_memory
        
        # 测试优化方法（分块处理）
        def optimized_memory_usage():
            for chunk in large_dataset:
                # 处理数据块，不保存在内存中
                processed_chunk = chunk * 2  # 示例处理
                del processed_chunk  # 显式释放内存
                if len(data_in_memory) % 100 == 0:  # 每100次清理一次
                    gc.collect()
        
        # 内存使用测试
        data_in_memory = []
        
        # 原始方法内存测试
        original_time = time.time()
        original_memory_usage()
        original_memory_time = time.time() - original_time
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 清理内存
        del data_in_memory
        gc.collect()
        
        # 优化方法内存测试
        optimized_time = time.time()
        optimized_memory_usage()
        optimized_memory_time = time.time() - optimized_time
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_savings = (peak_memory - final_memory) / peak_memory * 100
        
        print(f"📊 内存优化结果:")
        print(f"  初始内存: {initial_memory:.1f}MB")
        print(f"  原始方法峰值: {peak_memory:.1f}MB")
        print(f"  优化后内存: {final_memory:.1f}MB")
        print(f"  内存节省: {memory_savings:.1f}%")
        print(f"  时间对比: {original_memory_time:.2f}s vs {optimized_memory_time:.2f}s")
    
    def enable_cache_optimization(self):
        """启用缓存优化"""
        print("🗄️ 启用缓存优化...")
        
        from functools import lru_cache
        import pickle
        import hashlib
        import os
        
        class CacheManager:
            def __init__(self, cache_dir="./cache"):
                self.cache_dir = cache_dir
                os.makedirs(cache_dir, exist_ok=True)
            
            def _get_cache_key(self, func_name, args, kwargs):
                """生成缓存键"""
                key_data = f"{func_name}:{str(args)}:{str(kwargs)}"
                return hashlib.md5(key_data.encode()).hexdigest()
            
            def _get_cache_path(self, cache_key):
                """获取缓存文件路径"""
                return os.path.join(self.cache_dir, f"{cache_key}.cache")
            
            def cached(self, ttl_seconds=3600):
                """缓存装饰器"""
                def decorator(func):
                    def wrapper(*args, **kwargs):
                        cache_key = self._get_cache_key(func.__name__, args, kwargs)
                        cache_path = self._get_cache_path(cache_key)
                        
                        # 检查缓存是否存在且未过期
                        if os.path.exists(cache_path):
                            try:
                                with open(cache_path, 'rb') as f:
                                    cached_data = pickle.load(f)
                                    cache_time = cached_data['timestamp']
                                    result = cached_data['result']
                                    
                                    current_time = time.time()
                                    if current_time - cache_time < ttl_seconds:
                                        return result
                            except Exception:
                                pass  # 缓存损坏，重新计算
                        
                        # 计算结果
                        result = func(*args, **kwargs)
                        
                        # 保存到缓存
                        try:
                            with open(cache_path, 'wb') as f:
                                pickle.dump({
                                    'timestamp': time.time(),
                                    'result': result
                                }, f)
                        except Exception as e:
                            print(f"⚠️ 缓存保存失败: {e}")
                        
                        return result
                    
                    return wrapper
                return decorator
        
        # 创建缓存管理器
        cache_manager = CacheManager()
        
        # 示例：缓存RSI计算
        @cache_manager.cached(ttl_seconds=1800)  # 30分钟缓存
        def cached_rsi_calculation(prices, period=14):
            """缓存RSI计算"""
            delta = np.diff(prices)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            
            avg_gain = pd.Series(gain).rolling(window=period).mean()
            avg_loss = pd.Series(loss).rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        
        print("✅ 缓存系统已启用")
        return cache_manager

# 使用性能优化器
def optimize_system_performance():
    """优化系统性能"""
    optimizer = PerformanceOptimizer()
    
    # 1. 优化并行处理
    sample_tasks = list(range(100))
    
    def dummy_worker_task(x):
        return x * x
    
    parallel_results = optimizer.optimize_parallel_processing(
        sample_tasks, dummy_worker_task, max_workers=8
    )
    
    # 2. 优化NumPy操作
    test_data = np.random.random(10000)
    optimizer.optimize_numpy_operations(test_data)
    
    # 3. 优化内存使用
    large_dataset = [np.random.random(1000) for _ in range(100)]
    optimizer.optimize_memory_usage(large_dataset)
    
    # 4. 启用缓存优化
    cache_manager = optimizer.enable_cache_optimization()
    
    print("\n🎯 性能优化总结:")
    for optimization, results in optimizer.optimization_results.items():
        print(f"  {optimization}: {results}")

# 运行性能优化
# optimize_system_performance()
```

---

## 🔧 快速诊断工具

### 系统诊断脚本
```python
#!/usr/bin/env python3
"""
Enhanced Non-Price TA System 系统诊断脚本
运行方式: python system_diagnostic.py
"""

import sys
import os
import platform
import psutil
import requests
import json
from datetime import datetime

class SystemDiagnostic:
    """系统诊断工具"""
    
    def __init__(self):
        self.diagnostic_results = {}
        self.issues = []
        self.recommendations = []
    
    def run_full_diagnostic(self):
        """运行完整诊断"""
        print("🔍 Enhanced Non-Price TA System 系统诊断")
        print("=" * 60)
        
        # 系统环境诊断
        self.diagnose_system_environment()
        
        # Python环境诊断
        self.diagnose_python_environment()
        
        # 网络连接诊断
        self.diagnose_network_connectivity()
        
        # 数据源诊断
        self.diagnose_data_sources()
        
        # 性能诊断
        self.diagnose_performance()
        
        # 生成诊断报告
        self.generate_diagnostic_report()
    
    def diagnose_system_environment(self):
        """诊断系统环境"""
        print("\n🖥️  系统环境诊断:")
        
        # 基本信息
        system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
        
        print(f"  操作系统: {system_info['platform']} {system_info['platform_release']}")
        print(f"  架构: {system_info['architecture']}")
        print(f"  处理器: {system_info['processor']}")
        print(f"  Python版本: {system_info['python_version']}")
        
        # 硬件信息
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        print(f"\n  硬件配置:")
        print(f"    CPU核心数: {cpu_count}")
        print(f"    总内存: {memory.total / 1024**3:.1f}GB")
        print(f"    可用内存: {memory.available / 1024**3:.1f}GB ({memory.percent:.1f}%使用)")
        print(f"    总磁盘: {disk.total / 1024**3:.1f}GB")
        print(f"    可用磁盘: {disk.free / 1024**3:.1f}GB")
        
        # 系统要求检查
        print(f"\n  系统要求检查:")
        
        # CPU检查
        if cpu_count >= 8:
            print(f"    ✅ CPU核心数: {cpu_count} (满足推荐要求)")
        elif cpu_count >= 4:
            print(f"    ⚠️ CPU核心数: {cpu_count} (满足最低要求)")
        else:
            print(f"    ❌ CPU核心数: {cpu_count} (不满足要求)")
            self.issues.append("CPU核心数不足")
        
        # 内存检查
        if memory.total >= 16 * 1024**3:  # 16GB
            print(f"    ✅ 内存: {memory.total / 1024**3:.1f}GB (满足推荐要求)")
        elif memory.total >= 8 * 1024**3:  # 8GB
            print(f"    ⚠️ 内存: {memory.total / 1024**3:.1f}GB (满足最低要求)")
        else:
            print(f"    ❌ 内存: {memory.total / 1024**3:.1f}GB (不满足要求)")
            self.issues.append("内存不足")
        
        # 磁盘空间检查
        if disk.free >= 50 * 1024**3:  # 50GB
            print(f"    ✅ 可用磁盘: {disk.free / 1024**3:.1f}GB (满足要求)")
        else:
            print(f"    ❌ 可用磁盘: {disk.free / 1024**3:.1f}GB (不满足要求)")
            self.issues.append("磁盘空间不足")
        
        self.diagnostic_results['system_environment'] = system_info
    
    def diagnose_python_environment(self):
        """诊断Python环境"""
        print(f"\n🐍 Python环境诊断:")
        
        try:
            # 检查Python版本
            version_info = sys.version_info
            if version_info.major >= 3 and version_info.minor >= 9:
                print(f"    ✅ Python版本: {version_info.major}.{version_info.minor}.{version_info.micro} (满足要求)")
            else:
                print(f"    ❌ Python版本: {version_info.major}.{version_info.minor}.{version_info.micro} (需要3.9+)")
                self.issues.append("Python版本过低")
            
            # 检查pip
            try:
                import pip
                print(f"    ✅ pip版本: {pip.__version__}")
            except ImportError:
                print("    ❌ pip未安装")
                self.issues.append("pip未安装")
            
            # 检查关键包
            key_packages = [
                'pandas', 'numpy', 'requests', 'aiohttp', 
                'scipy', 'scikit-learn', 'matplotlib'
            ]
            
            for package in key_packages:
                try:
                    __import__(package)
                    print(f"    ✅ {package}: 已安装")
                except ImportError:
                    print(f"    ❌ {package}: 未安装")
                    self.issues.append(f"{package}未安装")
            
        except Exception as e:
            print(f"    ❌ Python环境诊断失败: {e}")
            self.issues.append("Python环境异常")
    
    def diagnose_network_connectivity(self):
        """诊断网络连接"""
        print(f"\n🌐 网络连接诊断:")
        
        test_urls = [
            ("主数据源", "http://18.180.162.113:9191"),
            ("Google DNS", "8.8.8.8:53"),
            ("HKMA官网", "https://api.hkma.gov.hk")
        ]
        
        network_status = {}
        
        for name, url in test_urls:
            try:
                if url.startswith("http"):
                    response = requests.get(url, timeout=10)
                    status = response.status_code
                    if 200 <= status < 300:
                        print(f"    ✅ {name}: HTTP {status}")
                        network_status[name] = "正常"
                    else:
                        print(f"    ⚠️ {name}: HTTP {status}")
                        network_status[name] = f"HTTP {status}"
                else:
                    # DNS测试
                    host, port = url.split(":")
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, int(port)))
                    sock.close()
                    
                    if result == 0:
                        print(f"    ✅ {name}: 连接正常")
                        network_status[name] = "正常"
                    else:
                        print(f"    ❌ {name}: 连接失败")
                        network_status[name] = "连接失败"
                        self.issues.append(f"{name}连接失败")
                        
            except requests.exceptions.ConnectionError:
                print(f"    ❌ {name}: 连接失败")
                network_status[name] = "连接失败"
                self.issues.append(f"{name}连接失败")
            except requests.exceptions.Timeout:
                print(f"    ❌ {name}: 超时")
                network_status[name] = "超时"
                self.issues.append(f"{name}超时")
            except Exception as e:
                print(f"    ❌ {name}: {e}")
                network_status[name] = f"错误: {e}"
        
        self.diagnostic_results['network_connectivity'] = network_status
    
    def diagnose_data_sources(self):
        """诊断数据源"""
        print(f"\n📊 数据源诊断:")
        
        # 检查配置文件
        config_files = [
            "config/config.yml",
            "config/config.example.yml"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"    ✅ {config_file}: 存在")
            else:
                print(f"    ❌ {config_file}: 不存在")
                if config_file == "config/config.yml":
                    self.issues.append("主配置文件不存在")
        
        # 检查数据目录
        data_dirs = ["data", "cache", "logs", "reports"]
        
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                print(f"    ✅ {data_dir}目录: 存在")
            else:
                print(f"    ⚠️ {data_dir}目录: 不存在 (创建中...)")
                try:
                    os.makedirs(data_dir, exist_ok=True)
                    print(f"    ✅ {data_dir}目录: 已创建")
                except Exception as e:
                    print(f"    ❌ {data_dir}目录: 创建失败 - {e}")
                    self.issues.append(f"{data_dir}目录创建失败")
    
    def diagnose_performance(self):
        """诊断性能"""
        print(f"\n⚡ 性能诊断:")
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"    CPU使用率: {cpu_percent:.1f}%")
        
        if cpu_percent > 80:
            print(f"    ⚠️ CPU使用率较高，可能影响性能")
        elif cpu_percent > 95:
            print(f"    ❌ CPU使用率过高，系统负载过重")
            self.issues.append("CPU使用率过高")
        
        # 内存使用率
        memory = psutil.virtual_memory()
        print(f"    内存使用率: {memory.percent:.1f}%")
        
        if memory.percent > 80:
            print(f"    ⚠️ 内存使用率较高，可能影响性能")
        elif memory.percent > 90:
            print(f"    ❌ 内存使用率过高，可能导致系统不稳定")
            self.issues.append("内存使用率过高")
        
        # 磁盘I/O
        disk_io = psutil.disk_io_counters()
        if disk_io:
            print(f"    磁盘读取: {disk_io.read_bytes / 1024**2:.1f}MB")
            print(f"    磁盘写入: {disk_io.write_bytes / 1024**2:.1f}MB")
        else:
            print(f"    磁盘I/O: 暂无数据")
    
    def generate_diagnostic_report(self):
        """生成诊断报告"""
        print(f"\n📋 诊断报告")
        print("=" * 60)
        
        # 总体状态
        if not self.issues:
            print("🎉 系统诊断通过！所有检查项都正常。")
        else:
            print(f"⚠️ 发现 {len(self.issues)} 个问题:")
            
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
            
            print(f"\n💡 建议:")
            recommendations = self._generate_recommendations()
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        # 保存诊断结果
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.diagnostic_results,
            'issues': self.issues,
            'recommendations': self._generate_recommendations()
        }
        
        try:
            with open('diagnostic_report.json', 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 详细报告已保存到: diagnostic_report.json")
        except Exception as e:
            print(f"\n❌ 保存报告失败: {e}")
    
    def _generate_recommendations(self):
        """生成建议"""
        recommendations = []
        
        for issue in self.issues:
            if "CPU核心数" in issue:
                recommendations.append("升级CPU或使用云计算资源以提高并行处理能力")
            elif "内存不足" in issue:
                recommendations.append("增加内存或优化内存使用策略")
            elif "磁盘空间" in issue:
                recommendations.append("清理磁盘空间或使用更大的存储设备")
            elif "Python版本" in issue:
                recommendations.append("升级Python到3.9+版本")
            elif "pip未安装" in issue:
                recommendations.append("安装pip包管理器")
            elif "未安装" in issue and "package" in issue.lower():
                recommendations.append("安装缺少的Python包：pip install package_name")
            elif "连接失败" in issue:
                recommendations.append("检查网络连接和防火墙设置")
            elif "超时" in issue:
                recommendations.append("检查网络延迟或增加请求超时时间")
            elif "CPU使用率过高" in issue:
                recommendations.append("优化算法或增加CPU资源")
            elif "内存使用率过高" in issue:
                recommendations.append("优化内存使用或增加内存")
            elif "配置文件不存在" in issue:
                recommendations.append("从config.example.yml复制并修改config.yml")
            elif "目录创建失败" in issue:
                recommendations.append("检查目录权限或手动创建目录")
        
        # 通用建议
        if not recommendations:
            recommendations.append("系统运行良好，继续保持当前配置")
        
        return recommendations

def main():
    """主函数"""
    diagnostic = SystemDiagnostic()
    diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    main()
```

---

## 📞 支持和反馈

### 获取更多帮助

1. **查看详细日志**: 检查 `logs/` 目录下的日志文件
2. **运行诊断脚本**: 使用上面的系统诊断工具
3. **查阅完整文档**: 参考[故障排除指南](./)
4. **社区支持**: 访问GitHub Issues或社区论坛

### 提交问题报告

如果您遇到本指南未涵盖的问题，请提交详细的问题报告：

```markdown
## 问题描述

**系统信息:**
- 操作系统: 
- Python版本:
- 系统版本: 

**问题详情:**
1. 重现步骤:
2. 期望结果:
3. 实际结果:
4. 错误信息:
5. 相关日志:

**已尝试的解决方案:**
1. 
2. 
3. 
```

---

**🚀 通过系统化的故障排除，让您的Enhanced Non-Price TA系统运行更稳定！**