#!/usr/bin/env python3
"""
测试Telegram量化交易系统Bot功能
"""

import os
import sys
import asyncio
import logging

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_quant_system():
    """测试量化交易系统功能"""
    print("🧪 测试量化交易系统...")
    
    try:
        from complete_project_system import (
            get_stock_data, 
            run_strategy_optimization,
            calculate_technical_indicators,
            calculate_risk_metrics,
            calculate_sentiment_analysis
        )
        print("✅ 量化交易系统导入成功")
        
        # 测试股票数据获取
        print("📊 测试股票数据获取...")
        data = get_stock_data("0700.HK")
        if data:
            print(f"✅ 成功获取股票数据: {len(data)} 条记录")
        else:
            print("❌ 股票数据获取失败")
            return False
        
        # 测试技术指标计算
        print("📈 测试技术指标计算...")
        df = pd.DataFrame(data)
        indicators = calculate_technical_indicators(df)
        print(f"✅ 技术指标计算成功: {len(indicators)} 个指标")
        
        # 测试策略优化（小规模测试）
        print("🚀 测试策略优化...")
        results = run_strategy_optimization(data, 'ma')
        if results:
            print(f"✅ 策略优化成功: 找到 {len(results)} 个策略")
        else:
            print("❌ 策略优化失败")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def test_telegram_bot():
    """测试Telegram Bot功能"""
    print("🤖 测试Telegram Bot...")
    
    try:
        from telegram_quant_bot import (
            format_strategy_results,
            format_technical_analysis,
            chunk_text
        )
        print("✅ Telegram Bot模块导入成功")
        
        # 测试文本格式化
        print("📝 测试文本格式化...")
        test_results = [
            {
                'strategy_name': 'MA(10,20)',
                'sharpe_ratio': 1.5,
                'annual_return': 12.5,
                'volatility': 8.2,
                'max_drawdown': -5.1,
                'win_rate': 65.0,
                'trade_count': 45,
                'final_value': 125000.0
            }
        ]
        
        formatted = format_strategy_results(test_results)
        print("✅ 策略结果格式化成功")
        
        # 测试文本分块
        print("📄 测试文本分块...")
        long_text = "测试文本 " * 1000
        chunks = chunk_text(long_text, 100)
        print(f"✅ 文本分块成功: {len(chunks)} 个块")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试Telegram量化交易系统Bot...\n")
    
    # 测试量化交易系统
    quant_ok = await test_quant_system()
    print()
    
    # 测试Telegram Bot
    bot_ok = await test_telegram_bot()
    print()
    
    # 总结
    if quant_ok and bot_ok:
        print("🎉 所有测试通过！系统准备就绪")
        print("\n📋 下一步:")
        print("1. 设置 TELEGRAM_BOT_TOKEN 环境变量")
        print("2. 运行: python telegram_quant_bot.py")
        print("3. 在Telegram中测试Bot功能")
    else:
        print("❌ 部分测试失败，请检查系统配置")
        if not quant_ok:
            print("  - 量化交易系统有问题")
        if not bot_ok:
            print("  - Telegram Bot模块有问题")

if __name__ == "__main__":
    asyncio.run(main())
