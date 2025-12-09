#!/usr/bin/env python3
"""
真實數據每日任務API系統
自動收集香港政府真實數據，提供API接口
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import pandas as pd
import schedule
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_real_data_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataCollectionStatus(BaseModel):
    """數據收集狀態模型"""
    data_source: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    last_update: datetime
    records_count: int = 0
    error_message: Optional[str] = None
    data_quality_score: Optional[float] = None

class DataSourceConfig(BaseModel):
    """數據源配置模型"""
    name: str
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    data_path: str  # JSON路徑或CSV列名
    date_field: str
    value_field: str
    refresh_interval: str = "daily"  # daily, weekly, monthly

class DataQualityMetrics(BaseModel):
    """數據質量指標模型"""
    completeness: float  # 完整性 0-1
    timeliness: float    # 及時性 0-1
    consistency: float   # 一致性 0-1
    overall_score: float # 總體評分 0-1

class RealDataCollector:
    """真實數據收集器"""

    def __init__(self):
        self.data_sources = self._initialize_data_sources()
        self.collection_status = {}
        self.data_storage_path = Path("data/daily_real_data")
        self.data_storage_path.mkdir(parents=True, exist_ok=True)

    def _initialize_data_sources(self) -> List[DataSourceConfig]:
        """初始化數據源配置"""
        return [
            # HIBOR利率數據
            DataSourceConfig(
                name="hibor_overnight",
                url="https://www.hkma.gov.hk/eng/market-data-and-statistics/daily-statistical-releases/monetary-statistics-daily/",
                data_path="table.data[0].data",
                date_field="date",
                value_field="overnight_rate"
            ),

            # GDP數據
            DataSourceConfig(
                name="gdp_growth",
                url="https://www.statistics.gov.hk/pub/B10200032023MM23B0100.xls",
                method="GET",
                data_path="sheet.data",
                date_field="period",
                value_field="gdp_growth_rate"
            ),

            # 失業率數據
            DataSourceConfig(
                name="unemployment_rate",
                url="https://www.statistics.gov.hk/pub/B10500012023MM23B0100.xls",
                method="GET",
                data_path="sheet.data",
                date_field="period",
                value_field="unemployment_rate"
            ),

            # 零售業銷售額
            DataSourceConfig(
                name="retail_sales",
                url="https://www.statistics.gov.hk/pub/B10600012023MM23B0100.xls",
                method="GET",
                data_path="sheet.data",
                date_field="period",
                value_field="retail_sales_index"
            ),

            # 訪客人次
            DataSourceConfig(
                name="visitor_arrivals",
                url="https://www.tourism.gov.hk/english/statistics/statistics_per_month.html",
                data_path="visitor_data",
                date_field="month",
                value_field="arrivals"
            ),

            # 貿易數據
            DataSourceConfig(
                name="trade_volume",
                url="https://www.censtatd.gov.hk/en/web_table.html?id=188",
                data_path="trade_data",
                date_field="period",
                value_field="total_trade"
            ),

            # 匯率數據
            DataSourceConfig(
                name="exchange_rate",
                url="https://www.hkma.gov.hk/eng/market-data-and-statistics/daily-statistical-releases/monetary-statistics-daily/",
                data_path="exchange_rates",
                date_field="date",
                value_field="hkd_usd"
            ),

            # 基準利率
            DataSourceConfig(
                name="base_rate",
                url="https://www.hkma.gov.hk/eng/market-data-and-statistics/daily-statistical-releases/monetary-statistics-daily/",
                data_path="base_rates",
                date_field="date",
                value_field="base_rate"
            ),

            # 貨幣基數
            DataSourceConfig(
                name="monetary_base",
                url="https://www.hkma.gov.hk/eng/market-data-and-statistics/daily-statistical-releases/monetary-statistics-daily/",
                data_path="monetary_base",
                date_field="date",
                value_field="amount"
            )
        ]

    async def collect_data_source(self, source_config: DataSourceConfig) -> Dict[str, Any]:
        """收集單個數據源的數據"""
        try:
            logger.info(f"開始收集數據源: {source_config.name}")

            # 更新狀態為運行中
            self.collection_status[source_config.name] = DataCollectionStatus(
                data_source=source_config.name,
                status="running",
                last_update=datetime.now(),
                records_count=0
            )

            async with aiohttp.ClientSession() as session:
                if source_config.method == "GET":
                    async with session.get(
                        source_config.url,
                        headers=source_config.headers,
                        params=source_config.params,
                        timeout=30
                    ) as response:
                        response.raise_for_status()

                        if response.content_type.startswith('application/json'):
                            data = await response.json()
                        else:
                            # 處理Excel/CSV文件
                            content = await response.read()
                            if source_config.url.endswith('.xls') or source_config.url.endswith('.xlsx'):
                                data = pd.read_excel(content)
                            else:
                                data = pd.read_csv(content)
                else:
                    # POST請求處理
                    async with session.post(
                        source_config.url,
                        headers=source_config.headers,
                        json=source_config.params,
                        timeout=30
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()

            # 解析數據
            parsed_data = self._parse_data(data, source_config)

            # 數據質量檢查
            quality_metrics = self._assess_data_quality(parsed_data, source_config)

            # 保存數據
            saved_path = await self._save_data(parsed_data, source_config.name)

            # 更新狀態為完成
            self.collection_status[source_config.name] = DataCollectionStatus(
                data_source=source_config.name,
                status="completed",
                last_update=datetime.now(),
                records_count=len(parsed_data) if isinstance(parsed_data, list) else 1,
                data_quality_score=quality_metrics.overall_score
            )

            logger.info(f"成功收集 {source_config.name}: {len(parsed_data) if isinstance(parsed_data, list) else 1} 條記錄")

            return {
                "success": True,
                "data_source": source_config.name,
                "records": len(parsed_data) if isinstance(parsed_data, list) else 1,
                "quality_score": quality_metrics.overall_score,
                "saved_path": str(saved_path)
            }

        except Exception as e:
            logger.error(f"收集 {source_config.name} 失敗: {e}")

            # 更新狀態為失敗
            self.collection_status[source_config.name] = DataCollectionStatus(
                data_source=source_config.name,
                status="failed",
                last_update=datetime.now(),
                records_count=0,
                error_message=str(e)
            )

            return {
                "success": False,
                "data_source": source_config.name,
                "error": str(e)
            }

    def _parse_data(self, raw_data: Any, config: DataSourceConfig) -> List[Dict[str, Any]]:
        """解析原始數據"""
        try:
            if isinstance(raw_data, dict):
                # JSON數據解析
                if "." in config.data_path:
                    # 支持嵌套路徑如 "table.data[0].data"
                    parts = config.data_path.split(".")
                    current = raw_data
                    for part in parts:
                        if "[" in part and part.endswith("]"):
                            # 處理數組索引
                            field_name = part.split("[")[0]
                            index = int(part.split("[")[1].split("]")[0])
                            current = current[field_name][index]
                        else:
                            current = current[part]
                    data = current
                else:
                    data = raw_data[config.data_path]

                # 確保是列表格式
                if not isinstance(data, list):
                    data = [data]

                return data

            elif isinstance(raw_data, pd.DataFrame):
                # DataFrame解析
                if config.date_field in raw_data.columns and config.value_field in raw_data.columns:
                    return [
                        {
                            "date": str(row[config.date_field]),
                            "value": float(row[config.value_field])
                        }
                        for _, row in raw_data.iterrows()
                    ]

            return []

        except Exception as e:
            logger.error(f"解析數據失敗 {config.name}: {e}")
            return []

    def _assess_data_quality(self, data: List[Dict[str, Any]], config: DataSourceConfig) -> DataQualityMetrics:
        """評估數據質量"""
        if not data:
            return DataQualityMetrics(
                completeness=0.0,
                timeliness=0.0,
                consistency=0.0,
                overall_score=0.0
            )

        try:
            # 完整性檢查
            total_fields = len(data)
            valid_records = len([
                record for record in data
                if record.get("date") and record.get("value") is not None
            ])
            completeness = valid_records / total_fields if total_fields > 0 else 0

            # 及時性檢查 (最近30天內的數據比例)
            recent_date = datetime.now() - timedelta(days=30)
            recent_records = len([
                record for record in data
                if datetime.strptime(record["date"], "%Y-%m-%d") > recent_date
            ])
            timeliness = recent_records / total_fields if total_fields > 0 else 0

            # 一致性檢查 (數值範圍合理性)
            values = [record["value"] for record in data if record.get("value") is not None]
            if values:
                # 檢查是否有異常值 (超過3個標準差)
                mean_val = sum(values) / len(values)
                variance = sum((x - mean_val) ** 2 for x in values) / len(values)
                std_dev = variance ** 0.5 if variance > 0 else 1

                normal_values = len([
                    value for value in values
                    if abs(value - mean_val) <= 3 * std_dev
                ])
                consistency = normal_values / len(values)
            else:
                consistency = 0

            # 總體評分
            overall_score = (completeness + timeliness + consistency) / 3

            return DataQualityMetrics(
                completeness=completeness,
                timeliness=timeliness,
                consistency=consistency,
                overall_score=overall_score
            )

        except Exception as e:
            logger.error(f"數據質量評估失敗: {e}")
            return DataQualityMetrics(
                completeness=0.0,
                timeliness=0.0,
                consistency=0.0,
                overall_score=0.0
            )

    async def _save_data(self, data: List[Dict[str, Any]], source_name: str) -> Path:
        """保存數據到文件"""
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{source_name}_{timestamp}.json"
        filepath = self.data_storage_path / filename

        # 保存JSON格式
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "data_source": source_name,
                "collection_time": datetime.now().isoformat(),
                "data": data,
                "records_count": len(data)
            }, f, ensure_ascii=False, indent=2, default=str)

        # 同時保存CSV格式供分析使用
        if data:
            csv_filepath = self.data_storage_path / f"{source_name}_{timestamp}.csv"
            df = pd.DataFrame(data)
            df.to_csv(csv_filepath, index=False, encoding='utf-8')

        logger.info(f"數據已保存: {filepath}")
        return filepath

# 全局數據收集器實例
data_collector = RealDataCollector()

# API生命週期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時執行
    logger.info("真實數據API服務啟動")

    # 啟動後台調度任務
    asyncio.create_task(schedule_background_tasks())

    yield

    # 關閉時執行
    logger.info("真實數據API服務關閉")

# 創建FastAPI應用
app = FastAPI(
    title="真實數據每日任務API",
    description="自動收集香港政府真實數據的API系統",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def schedule_background_tasks():
    """後台調度任務"""
    while True:
        try:
            # 每天早上8點執行數據收集
            schedule.every().day.at("08:00").do(collect_all_data_sources)

            # 每小時檢查一次
            while True:
                schedule.run_pending()
                await asyncio.sleep(3600)  # 1小時

        except Exception as e:
            logger.error(f"後台調度任務錯誤: {e}")
            await asyncio.sleep(300)  # 5分鐘後重試

def collect_all_data_sources():
    """收集所有數據源"""
    logger.info("開始每日數據收集任務")

    # 在異步環境中運行同步函數
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(
            asyncio.gather(*[
                data_collector.collect_data_source(source)
                for source in data_collector.data_sources
            ])
        )
        logger.info("每日數據收集任務完成")
    except Exception as e:
        logger.error(f"每日數據收集任務失敗: {e}")
    finally:
        loop.close()

# API端點
@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "真實數據每日任務API",
        "version": "1.0.0",
        "status": "運行中",
        "data_sources_count": len(data_collector.data_sources)
    }

@app.get("/status")
async def get_system_status():
    """獲取系統狀態"""
    return {
        "system_status": "運行中",
        "last_update": datetime.now().isoformat(),
        "data_sources": len(data_collector.data_sources),
        "active_collections": len([
            s for s in data_collector.collection_status.values()
            if s.status == "running"
        ]),
        "total_collections_today": len(data_collector.collection_status)
    }

@app.get("/data-sources")
async def get_data_sources():
    """獲取所有數據源配置"""
    return {
        "data_sources": [
            {
                "name": source.name,
                "url": source.url,
                "method": source.method,
                "refresh_interval": source.refresh_interval
            }
            for source in data_collector.data_sources
        ]
    }

@app.get("/collection-status")
async def get_collection_status():
    """獲取收集狀態"""
    return {
        "status": data_collector.collection_status
    }

@app.post("/collect/{source_name}")
async def trigger_collection(source_name: str, background_tasks: BackgroundTasks):
    """手動觸發數據收集"""
    # 查找數據源配置
    source_config = None
    for source in data_collector.data_sources:
        if source.name == source_name:
            source_config = source
            break

    if not source_config:
        raise HTTPException(status_code=404, detail=f"數據源 {source_name} 未找到")

    # 添加後台任務
    background_tasks.add_task(data_collector.collect_data_source, source_config)

    return {
        "message": f"已觸發 {source_name} 數據收集",
        "status": "pending"
    }

@app.post("/collect-all")
async def trigger_collect_all(background_tasks: BackgroundTasks):
    """觸發所有數據源收集"""
    background_tasks.add_task(collect_all_data_sources)

    return {
        "message": "已觸發所有數據源收集",
        "total_sources": len(data_collector.data_sources),
        "status": "pending"
    }

@app.get("/data/{source_name}/latest")
async def get_latest_data(source_name: str, limit: int = 10):
    """獲取最新數據"""
    try:
        # 查找最新的數據文件
        data_files = list(data_collector.data_storage_path.glob(f"{source_name}_*.json"))
        if not data_files:
            raise HTTPException(status_code=404, detail=f"未找到 {source_name} 的數據文件")

        # 按修改時間排序，獲取最新的
        latest_file = max(data_files, key=lambda x: x.stat().st_mtime)

        with open(latest_file, encoding='utf-8') as f:
            data = json.load(f)

        # 返回最新的limit條記錄
        records = data.get("data", [])[-limit:] if limit > 0 else data.get("data", [])

        return {
            "data_source": source_name,
            "collection_time": data.get("collection_time"),
            "total_records": data.get("records_count", 0),
            "records": records,
            "file_path": str(latest_file)
        }

    except Exception as e:
        logger.error(f"獲取最新數據失敗 {source_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/{source_name}/history")
async def get_historical_data(source_name: str, days: int = 30):
    """獲取歷史數據"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        all_records = []

        # 查找所有相關的數據文件
        data_files = sorted(
            data_collector.data_storage_path.glob(f"{source_name}_*.json"),
            key=lambda x: x.stat().st_mtime
        )

        for data_file in data_files:
            file_date = datetime.strptime(data_file.stem.split("_")[1], "%Y%m%d")

            if start_date <= file_date <= end_date:
                with open(data_file, encoding='utf-8') as f:
                    data = json.load(f)
                    all_records.extend(data.get("data", []))

        # 按日期排序
        all_records.sort(key=lambda x: x.get("date", ""))

        return {
            "data_source": source_name,
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "total_records": len(all_records),
            "records": all_records
        }

    except Exception as e:
        logger.error(f"獲取歷史數據失敗 {source_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quality-metrics")
async def get_quality_metrics():
    """獲取數據質量指標"""
    try:
        metrics = {}

        for source_name, status in data_collector.collection_status.items():
            if status.status == "completed" and status.data_quality_score:
                metrics[source_name] = {
                    "quality_score": status.data_quality_score,
                    "last_update": status.last_update.isoformat(),
                    "records_count": status.records_count
                }

        return {
            "metrics": metrics,
            "summary": {
                "total_sources": len(data_collector.data_sources),
                "successful_collections": len([
                    s for s in data_collector.collection_status.values()
                    if s.status == "completed"
                ]),
                "average_quality_score": sum(
                    m["quality_score"] for m in metrics.values()
                ) / len(metrics) if metrics else 0
            }
        }

    except Exception as e:
        logger.error(f"獲取質量指標失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "運行中"
    }

if __name__ == "__main__":
    import uvicorn

    # 直接運行用於測試
    uvicorn.run(
        "daily_real_data_api:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
