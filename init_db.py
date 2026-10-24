"""
数据库初始化脚本
"""

import sqlite3
import os

def init_database():
    """初始化数据库"""
    # 创建数据库
    DB_PATH = 'data/quant_system.db'
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 创建股票表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sector TEXT,
                industry TEXT,
                market_cap REAL,
                pe_ratio REAL,
                dividend_yield REAL,
                currency TEXT DEFAULT 'HKD',
                exchange TEXT DEFAULT 'HKEX',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建市场数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                UNIQUE(symbol, timestamp)
            )
        """)
        
        # 创建技术指标表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                sma_20 REAL,
                sma_50 REAL,
                ema_12 REAL,
                ema_26 REAL,
                rsi REAL,
                macd REAL,
                macd_signal REAL,
                macd_histogram REAL,
                bollinger_upper REAL,
                bollinger_middle REAL,
                bollinger_lower REAL,
                atr REAL,
                volume_sma REAL,
                volume_ratio REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                UNIQUE(symbol, timestamp)
            )
        """)
        
        # 创建投资组合表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                total_value REAL DEFAULT 0,
                total_return REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建投资组合持仓表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                average_price REAL NOT NULL,
                current_price REAL,
                value REAL,
                return_pct REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
                FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                UNIQUE(portfolio_id, symbol)
            )
        """)
        
        # 创建策略表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                strategy_type TEXT NOT NULL,
                parameters TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建回测结果表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                total_return REAL,
                annual_return REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                win_rate REAL,
                total_trades INTEGER,
                profit_trades INTEGER,
                loss_trades INTEGER,
                avg_profit REAL,
                avg_loss REAL,
                profit_factor REAL,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id),
                FOREIGN KEY (symbol) REFERENCES stocks(symbol)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol_timestamp ON technical_indicators(symbol, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_portfolio_id ON portfolio_holdings(portfolio_id)")
        
        conn.commit()
        print("✅ 数据库初始化完成")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def insert_sample_data():
    """插入示例数据"""
    conn = sqlite3.connect('data/quant_system.db')
    cursor = conn.cursor()
    
    try:
        # 插入示例股票数据
        sample_stocks = [
            ("0700.HK", "腾讯控股", "科技", "互联网", 3000000000000, 25.5, 0.5),
            ("2800.HK", "盈富基金", "金融", "ETF", 100000000000, 15.2, 3.2),
            ("1299.HK", "友邦保险", "保险", "人寿保险", 800000000000, 18.8, 2.1),
            ("0941.HK", "中国移动", "电信", "移动通信", 1200000000000, 12.5, 4.8),
            ("0388.HK", "香港交易所", "金融", "交易所", 400000000000, 22.3, 2.9)
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO stocks (symbol, name, sector, industry, market_cap, pe_ratio, dividend_yield)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_stocks)
        
        # 插入示例投资组合
        sample_portfolios = [
            ("portfolio_1", "港股核心组合", "以腾讯、友邦等港股蓝筹股为核心的投资组合", 1000000, 8.5),
            ("portfolio_2", "科技成长组合", "专注于科技股的成长型投资组合", 500000, 12.3)
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO portfolios (id, name, description, total_value, total_return)
            VALUES (?, ?, ?, ?, ?)
        """, sample_portfolios)
        
        # 插入示例策略
        sample_strategies = [
            ("ma_cross", "移动平均交叉策略", "基于短期和长期移动平均线交叉的交易策略", "technical", '{"short_period": 20, "long_period": 50}'),
            ("rsi_oversold", "RSI超卖策略", "基于RSI指标的超买超卖交易策略", "technical", '{"rsi_period": 14, "oversold_level": 30, "overbought_level": 70}'),
            ("bollinger_bands", "布林带策略", "基于布林带的价格突破交易策略", "technical", '{"period": 20, "std_dev": 2}')
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO strategies (id, name, description, strategy_type, parameters)
            VALUES (?, ?, ?, ?, ?)
        """, sample_strategies)
        
        conn.commit()
        print("✅ 示例数据插入完成")
        
    except Exception as e:
        print(f"❌ 插入示例数据失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
    insert_sample_data()
