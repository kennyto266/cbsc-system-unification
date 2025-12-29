#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港交所北向资金数据整合架构设计
实现真正的港交所北向资金爬虫和数据管理系统
"""

import requests
import sqlite3
import pandas as pd
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import asyncio
import aiohttp
from urllib.parse import urljoin
import hashlib
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/northbound_flow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class NorthboundConfig:
    """北向资金爬虫配置"""
    # 数据库配置
    db_path: str = "data/northbound_flow.db"

    # API配置
    hkex_base_url: str = "https://www.hkex.com.hk"
    hkex_api_base: str = "https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices"
    sse_base_url: str = "http://query.sse.com.cn"
    szse_base_url: str = "http://www.szse.cn"

    # 请求配置
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    # 数据更新配置
    update_frequency: str = "daily"  # daily, hourly, real-time
    batch_size: int = 100

    # 合规配置
    respect_robots_txt: bool = True
    rate_limit_delay: float = 1.0  # 秒
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

class NorthboundDataSchema:
    """北向资金数据模式定义"""

    # 北向资金流向表
    CREATE_NORTHBOUND_FLOW_TABLE = """
        CREATE TABLE IF NOT EXISTS northbound_flow (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date DATE NOT NULL,
            market TEXT NOT NULL CHECK (market IN ('SH', 'SZ')),
            total_turnover REAL NOT NULL,
            net_inflow REAL,
            turnover_change REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(trade_date, market)
        )
    """

    # 个股北向资金流向表
    CREATE_STOCK_NORTHBOUND_TABLE = """
        CREATE TABLE IF NOT EXISTS stock_northbound_flow (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date DATE NOT NULL,
            stock_code TEXT NOT NULL,
            stock_name TEXT,
            market TEXT NOT NULL CHECK (market IN ('SH', 'SZ')),
            buy_volume REAL DEFAULT 0,
            sell_volume REAL DEFAULT 0,
            net_volume REAL DEFAULT 0,
            turnover REAL DEFAULT 0,
            holding_ratio REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(trade_date, stock_code, market)
        )
    """

    # 数据源日志表
    CREATE_DATA_SOURCE_LOG_TABLE = """
        CREATE TABLE IF NOT EXISTS data_source_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_time REAL,
            status_code INTEGER,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            records_count INTEGER DEFAULT 0
        )
    """

    # 创建索引
    CREATE_INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_northbound_flow_date ON northbound_flow(trade_date)",
        "CREATE INDEX IF NOT EXISTS idx_northbound_flow_market ON northbound_flow(market)",
        "CREATE INDEX IF NOT EXISTS idx_stock_northbound_date ON stock_northbound_flow(trade_date)",
        "CREATE INDEX IF NOT EXISTS idx_stock_northbound_code ON stock_northbound_flow(stock_code)",
        "CREATE INDEX IF NOT EXISTS idx_data_source_time ON data_source_log(request_time)"
    ]

class NorthboundFlowAPI:
    """北向资金数据获取API"""

    def __init__(self, config: NorthboundConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br'
        })

    def get_hkex_northbound_data(self, date: Union[str, None] = None) -> Optional[Dict]:
        """
        从港交所获取北向资金数据
        注意：此方法需要根据港交所实际API调整
        """
        try:
            # 港交所信息披露API（示例URL，需要实际验证）
            url = f"{self.config.hkex_base_url}/eng/services/somc/securitydaystat.htm"

            # 港交所通常使用JavaScript渲染，可能需要使用Selenium或解析JavaScript
            params = {
                'date': date or datetime.now().strftime('%Y-%m-%d'),
                'market': 'northbound'
            }

            response = self.session.get(
                url,
                params=params,
                timeout=self.config.request_timeout
            )
            response.raise_for_status()

            # 解析响应（需要根据实际响应格式调整）
            return self._parse_hkex_response(response.text)

        except Exception as e:
            logger.error(f"获取港交所数据失败: {e}")
            return None

    def get_sse_northbound_data(self, date: Union[str, None] = None) -> Optional[Dict]:
        """
        从上交所获取沪股通数据
        """
        try:
            # 上交所信息披露API
            url = f"{self.config.sse_base_url}/commonQuery.do"

            params = {
                'jsonCallBack': 'jsonpCallback',
                'isPagination': 'false',
                'sqlId': 'COMMON_SSE_SCGS_NORTHBOUND',
                'pageHelp.pageSize': '100',
                'tradeDate': date or datetime.now().strftime('%Y%m%d')
            }

            response = self.session.get(
                url,
                params=params,
                timeout=self.config.request_timeout
            )
            response.raise_for_status()

            # 解析JSONP响应
            return self._parse_jsonp_response(response.text)

        except Exception as e:
            logger.error(f"获取上交所数据失败: {e}")
            return None

    def get_szse_northbound_data(self, date: Union[str, None] = None) -> Optional[Dict]:
        """
        从深交所获取深股通数据
        """
        try:
            # 深交所信息披露API
            url = f"{self.config.szse_base_url}/api/report/ShowReport"

            params = {
                'SHOWTYPE': 'JSON',
                'CATALOGID': '1110',
                'TABKEY': 'tab1',
                'PAGENO': '1',
                'TXT_DATE': date or datetime.now().strftime('%Y-%m-%d')
            }

            response = self.session.get(
                url,
                params=params,
                timeout=self.config.request_timeout
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"获取深交所数据失败: {e}")
            return None

    def _parse_hkex_response(self, html: str) -> Optional[Dict]:
        """解析港交所HTML响应"""
        # 实际实现需要根据HTML结构进行解析
        # 可能需要使用BeautifulSoup或类似工具
        return {"data": [], "source": "HKEX"}

    def _parse_jsonp_response(self, jsonp: str) -> Optional[Dict]:
        """解析JSONP响应"""
        try:
            # 移除JSONP包装
            json_start = jsonp.find('(') + 1
            json_end = jsonp.rfind(')')
            json_str = jsonp[json_start:json_end]
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"解析JSONP失败: {e}")
            return None

class AlternativeDataSource:
    """备用数据源"""

    @staticmethod
    def get_eastmoney_northbound_data() -> Optional[Dict]:
        """
        从东方财富网获取北向资金数据
        这是一个公开的数据源，通常更稳定
        """
        try:
            url = "http://push2.eastmoney.com/api/qt/kamt.rt.get"
            params = {
                'fields1': 'f1,f2,f3,f4',
                'fields2': 'f51,f52,f53,f54,f55',
                'ut': 'b2884a393a59ad64002292a3e90d46a5'
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return {
                'data': {
                    'sh_turnover': data.get('data', {}).get('sh', {}).get('rtAf', 0),
                    'sz_turnover': data.get('data', {}).get('sz', {}).get('rtAf', 0),
                    'net_inflow': data.get('data', {}).get('net', 0)
                },
                'source': 'EastMoney'
            }

        except Exception as e:
            logger.error(f"获取东方财富数据失败: {e}")
            return None

    @staticmethod
    def get_tushare_northbound_data(token: str, trade_date: str) -> Optional[pd.DataFrame]:
        """
        使用Tushare获取北向资金数据（需要付费）
        这是一个专业的数据源，但需要API token
        """
        try:
            import tushare as ts
            ts.set_token(token)
            pro = ts.pro_api()

            # 获取沪股通数据
            df_sh = pro.moneyflow_hsgt(
                trade_date=trade_date,
                trade_type='S'  # S=沪股通 G=港股通
            )

            return df_sh

        except Exception as e:
            logger.error(f"获取Tushare数据失败: {e}")
            return None

class NorthboundDataManager:
    """北向资金数据管理器"""

    def __init__(self, config: NorthboundConfig):
        self.config = config
        self.api = NorthboundFlowAPI(config)
        self.alternative = AlternativeDataSource()
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.config.db_path), exist_ok=True)

        conn = sqlite3.connect(self.config.db_path)
        cursor = conn.cursor()

        try:
            # 创建表
            cursor.execute(NorthboundDataSchema.CREATE_NORTHBOUND_FLOW_TABLE)
            cursor.execute(NorthboundDataSchema.CREATE_STOCK_NORTHBOUND_TABLE)
            cursor.execute(NorthboundDataSchema.CREATE_DATA_SOURCE_LOG_TABLE)

            # 创建索引
            for index_sql in NorthboundDataSchema.CREATE_INDEXES:
                cursor.execute(index_sql)

            conn.commit()
            logger.info("数据库初始化成功")

        except Exception as e:
            conn.rollback()
            logger.error(f"数据库初始化失败: {e}")
            raise
        finally:
            conn.close()

    async def collect_daily_data(self, date: Union[str, None] = None) -> bool:
        """
        收集指定日期的北向资金数据
        """
        target_date = date or datetime.now().strftime('%Y-%m-%d')

        # 检查数据是否已存在
        if self._check_data_exists(target_date):
            logger.info(f"日期 {target_date} 的数据已存在，跳过收集")
            return True

        success = False
        data_source = None

        # 尝试从不同数据源获取数据
        for source in ['HKEX', 'SSE', 'SZSE', 'EastMoney']:
            try:
                logger.info(f"尝试从 {source} 获取数据...")

                if source == 'HKEX':
                    data = self.api.get_hkex_northbound_data(target_date)
                elif source == 'SSE':
                    data = self.api.get_sse_northbound_data(target_date)
                elif source == 'SZSE':
                    data = self.api.get_szse_northbound_data(target_date)
                elif source == 'EastMoney':
                    data = self.alternative.get_eastmoney_northbound_data()

                if data and data.get('data'):
                    success = self._save_data(target_date, data, source)
                    if success:
                        data_source = source
                        break

                # 遵守rate limiting
                await asyncio.sleep(self.config.rate_limit_delay)

            except Exception as e:
                logger.error(f"从 {source} 获取数据失败: {e}")
                continue

        # 记录数据源日志
        self._log_data_source(data_source, success)

        return success

    def _check_data_exists(self, date: str) -> bool:
        """检查指定日期的数据是否已存在"""
        conn = sqlite3.connect(self.config.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT COUNT(*) FROM northbound_flow WHERE trade_date = ?",
                (date,)
            )
            count = cursor.fetchone()[0]
            return count > 0
        finally:
            conn.close()

    def _save_data(self, date: str, data: Dict, source: str) -> bool:
        """保存数据到数据库"""
        conn = sqlite3.connect(self.config.db_path)
        cursor = conn.cursor()

        try:
            # 解析并保存北向资金数据
            flow_data = self._parse_flow_data(data, date)

            for market, values in flow_data.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO northbound_flow
                    (trade_date, market, total_turnover, net_inflow, turnover_change)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    date,
                    market,
                    values.get('total_turnover', 0),
                    values.get('net_inflow', 0),
                    values.get('turnover_change', 0)
                ))

            # 如果有个股数据，也保存
            if 'stock_data' in data:
                self._save_stock_data(cursor, date, data['stock_data'])

            conn.commit()
            logger.info(f"成功保存 {date} 的北向资金数据（来源: {source}）")
            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"保存数据失败: {e}")
            return False
        finally:
            conn.close()

    def _parse_flow_data(self, data: Dict, date: str) -> Dict:
        """解析北向资金数据"""
        # 根据不同数据源的格式进行解析
        if data.get('source') == 'EastMoney':
            return {
                'SH': {
                    'total_turnover': data['data']['sh_turnover'],
                    'net_inflow': data['data']['net_inflow'] * 0.5  # 简化处理
                },
                'SZ': {
                    'total_turnover': data['data']['sz_turnover'],
                    'net_inflow': data['data']['net_inflow'] * 0.5
                }
            }
        else:
            # 其他数据源的解析逻辑
            return {}

    def _save_stock_data(self, cursor, date: str, stock_data: List[Dict]):
        """保存个股北向资金数据"""
        for stock in stock_data:
            cursor.execute("""
                INSERT OR REPLACE INTO stock_northbound_flow
                (trade_date, stock_code, stock_name, market,
                 buy_volume, sell_volume, net_volume, turnover, holding_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date,
                stock.get('code'),
                stock.get('name'),
                stock.get('market'),
                stock.get('buy_volume', 0),
                stock.get('sell_volume', 0),
                stock.get('net_volume', 0),
                stock.get('turnover', 0),
                stock.get('holding_ratio', 0)
            ))

    def _log_data_source(self, source: str, success: bool):
        """记录数据源日志"""
        conn = sqlite3.connect(self.config.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO data_source_log
                (source_name, endpoint, success)
                VALUES (?, ?, ?)
            """, (source, 'northbound_flow_api', success))

            conn.commit()
        finally:
            conn.close()

    def get_flow_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取指定日期范围的北向资金数据"""
        conn = sqlite3.connect(self.config.db_path)

        query = """
            SELECT trade_date, market, total_turnover, net_inflow, turnover_change
            FROM northbound_flow
            WHERE trade_date BETWEEN ? AND ?
            ORDER BY trade_date, market
        """

        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()

        return df

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算北向资金技术指标"""
        if df.empty:
            return df

        # 按市场分组
        df = df.copy()

        # 计算移动平均
        df['turnover_ma5'] = df.groupby('market')['total_turnover'].transform(
            lambda x: x.rolling(window=5).mean()
        )
        df['turnover_ma20'] = df.groupby('market')['total_turnover'].transform(
            lambda x: x.rolling(window=20).mean()
        )

        # 计算变化率
        df['turnover_change_pct'] = df.groupby('market')['total_turnover'].pct_change()
        df['net_inflow_change'] = df.groupby('market')['net_inflow'].diff()

        # 计算累计净流入
        df['cumulative_net_inflow'] = df.groupby('market')['net_inflow'].cumsum()

        # 计算Z-score（标准化）
        df['turnover_zscore'] = df.groupby('market')['total_turnover'].transform(
            lambda x: (x - x.mean()) / x.std()
        )

        # 生成信号
        df['signal'] = 0
        df.loc[df['turnover_zscore'] > 2, 'signal'] = 1  # 大幅流入
        df.loc[df['turnover_zscore'] < -2, 'signal'] = -1  # 大幅流出

        return df

class NorthboundScheduler:
    """北向资金数据更新调度器"""

    def __init__(self, manager: NorthboundDataManager):
        self.manager = manager

    async def start_scheduler(self):
        """启动定时任务"""
        while True:
            try:
                # 获取当前时间
                now = datetime.now()

                # 检查是否在交易时间
                if self._is_trading_time(now):
                    # 收集数据
                    await self.manager.collect_daily_data()

                # 等待下一次检查
                await asyncio.sleep(300)  # 5分钟检查一次

            except Exception as e:
                logger.error(f"调度器错误: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试

    def _is_trading_time(self, dt: datetime) -> bool:
        """检查是否是交易时间"""
        # 简化版：只在工作日的9:30-15:00运行
        if dt.weekday() >= 5:  # 周末
            return False

        if dt.hour == 9 and 30 <= dt.minute <= 59:
            return True
        elif 10 <= dt.hour < 15:
            return True

        return False

# 使用示例
async def main():
    """主函数示例"""
    # 创建配置
    config = NorthboundConfig()

    # 创建管理器
    manager = NorthboundDataManager(config)

    # 收集最近30天的数据
    for i in range(30):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        success = await manager.collect_daily_data(date)
        if success:
            print(f"✅ 成功收集 {date} 的数据")
        else:
            print(f"❌ 收集 {date} 的数据失败")

    # 获取并分析数据
    df = manager.get_flow_data(
        start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        end_date=datetime.now().strftime('%Y-%m-%d')
    )

    # 计算指标
    df_with_indicators = manager.calculate_indicators(df)

    print("\n北向资金数据分析:")
    print(df_with_indicators.tail())

    # 启动定时任务
    # scheduler = NorthboundScheduler(manager)
    # await scheduler.start_scheduler()

if __name__ == "__main__":
    asyncio.run(main())