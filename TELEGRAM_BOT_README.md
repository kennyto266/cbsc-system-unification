# Telegram量化交易系统Bot

## 🤖 功能概述

这是一个集成完整量化交易分析功能的Telegram Bot，提供以下功能：

### 📊 股票分析功能
- **技术分析** (`/analyze`) - 计算SMA、EMA、RSI、MACD、布林带等技术指标
- **策略优化** (`/optimize`) - 运行高计算量策略参数优化，测试数千个策略组合
- **风险评估** (`/risk`) - 计算VaR、最大回撤、波动率等风险指标
- **市场情绪** (`/sentiment`) - 分析市场情绪和趋势强度

### 🔧 系统功能
- **系统状态** (`/status`) - 查看系统运行状态和版本信息
- **帮助信息** (`/help`) - 显示所有可用指令
- **ID信息** (`/id`) - 显示对话ID信息

## 🚀 安装与配置

### 1. 安装依赖
```bash
pip install python-telegram-bot[rate-limiter,http2]==21.6
pip install python-dotenv==1.0.1
pip install pandas numpy requests
```

### 2. 配置环境变量
创建 `.env` 文件或设置环境变量：
```bash
# 必需配置
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here"

# 可选配置
export TG_ALLOWED_USER_IDS="123456789,987654321"
export TG_ALLOWED_CHAT_IDS="-1001234567890"
```

### 3. 获取Telegram Bot Token
1. 在Telegram中搜索 `@BotFather`
2. 发送 `/newbot` 创建新Bot
3. 按提示设置Bot名称和用户名
4. 获取Bot Token并设置到环境变量

## 📱 使用方法

### 基本指令
```
/start - 问候与简介
/help - 显示帮助信息
/status - 查看系统状态
/id - 显示对话ID信息
```

### 股票分析指令
```
/analyze 0700.HK - 分析腾讯控股技术指标
/optimize 2800.HK - 运行恒生指数ETF策略优化
/risk 0700.HK - 计算腾讯控股风险评估
/sentiment 2800.HK - 分析恒生指数ETF市场情绪
```

## 🎯 高计算量策略优化

### 优化特性
- **策略数量**: 测试2,728个策略组合（相比基础版本增加105倍）
- **参数范围**: 
  - MA策略: 3-50 × 10-100 = 1,200个组合
  - RSI策略: 10-40 × 50-80 = 930个组合
  - MACD策略: 5×6×5 = 150个组合
  - 布林带策略: 8×3 = 24个组合
- **CPU利用**: 充分利用9950X3D的16核心32线程性能

### 优化结果示例
```
🎯 0700.HK 策略优化完成

📊 测试策略数量: 2728
🏆 最佳Sharpe比率: 1.52
⏰ 优化时间: 2025-09-29 13:01:21

📊 策略优化结果 (前10名)

1. MA交叉(13,18)
   Sharpe比率: 1.520
   年化收益率: 11.95%
   波动率: 7.86%
   最大回撤: -5.41%
   胜率: 60.78%
   交易次数: 52
   最终价值: ¥145,990.05
```

## 🔧 技术架构

### 核心组件
- **Telegram Bot**: 基于python-telegram-bot v21
- **量化系统**: 集成complete_project_system.py
- **数据处理**: Pandas + NumPy
- **API集成**: 外部股票数据API

### 系统要求
- Python 3.8+
- 内存: 建议4GB+
- CPU: 支持多核处理（推荐16核心+）
- 网络: 稳定的互联网连接

## 🛡️ 安全特性

### 权限控制
- 支持用户白名单 (`TG_ALLOWED_USER_IDS`)
- 支持群组白名单 (`TG_ALLOWED_CHAT_IDS`)
- 命令执行超时保护
- 输出长度限制

### 错误处理
- 完善的异常捕获和日志记录
- 用户友好的错误提示
- 自动重试机制

## 📊 性能监控

### 系统状态
使用 `/status` 命令查看：
- 量化交易系统状态
- Python和依赖库版本
- 当前系统时间

### 日志记录
- 详细的执行日志
- 错误追踪和调试信息
- 性能指标记录

## 🚀 启动方式

### 方式1: 直接启动
```bash
python telegram_quant_bot.py
```

### 方式2: 使用启动脚本
```bash
python start_telegram_bot.py
```

### 方式3: 后台运行
```bash
nohup python telegram_quant_bot.py > bot.log 2>&1 &
```

## 📝 注意事项

1. **API限制**: 外部股票API可能有请求频率限制
2. **计算时间**: 策略优化可能需要几分钟时间
3. **数据质量**: 确保股票代码格式正确（如：0700.HK）
4. **权限设置**: 建议设置用户白名单以提高安全性

## 🔄 更新日志

### v1.0.0
- 集成完整量化交易系统
- 支持高计算量策略优化
- 添加技术分析、风险评估、情绪分析功能
- 完善的错误处理和权限控制

## 📞 支持

如有问题或建议，请通过以下方式联系：
- 检查系统日志
- 使用 `/status` 命令诊断
- 查看错误消息和提示
