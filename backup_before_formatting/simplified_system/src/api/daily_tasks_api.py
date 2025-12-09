#!/usr/bin/env python3
"""
簡化系統 - 每日任務API服務器
Simplified System - Daily Tasks API Server

高性能的政府數據收集和API服務
High-performance government data collection and API service
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our core modules
from ..data.government_data import (
    government_collector,
    collect_hkma_data,
    collect_all_government_data,
    get_latest_government_data
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CollectionStatus(BaseModel):
    """數據收集狀態模型"""
    source_name: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    last_update: datetime
    records_count: int = 0
    error_message: Optional[str] = None
    quality_score: Optional[float] = None

class DataRequest(BaseModel):
    """數據請求模型"""
    source_name: Optional[str] = None
    limit: int = 10
    days: int = 30

class APIResponse(BaseModel):
    """API響應模型"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime
    error: Optional[str] = None

# Global variables for background tasks
collection_status = {}
background_tasks_running = False

# API lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    global background_tasks_running

    # 啟動時執行
    logger.info("🚀 Daily Tasks API starting up...")

    # 初始化背景任務
    background_tasks_running = True
    asyncio.create_task(background_scheduler())

    yield

    # 關閉時執行
    logger.info("🔄 Daily Tasks API shutting down...")
    background_tasks_running = False
    await government_collector.close()

# Create FastAPI application
app = FastAPI(
    title="每日任務API服務器",
    description="高性能香港政府數據收集API",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def background_scheduler():
    """
    背景調度任務
    定期收集政府數據
    """
    logger.info("🕐 Background scheduler started")

    while background_tasks_running:
        try:
            # 每天早上8點執行完整數據收集
            current_time = datetime.now()
            if current_time.hour == 8 and current_time.minute < 5:
                logger.info("🌅 Starting scheduled daily data collection")

                results = await collect_all_government_data()

                # 更新狀態
                for result in results:
                    collection_status[result.source_name] = CollectionStatus(
                        source_name=result.source_name,
                        status="completed" if result.success else "failed",
                        last_update=result.collection_time,
                        records_count=result.record_count,
                        error_message=result.error_message,
                        quality_score=result.data_quality_score
                    )

                successful = sum(1 for r in results if r.success)
                total_records = sum(r.record_count for r in results if r.success)
                logger.info(f"✅ Scheduled collection completed: {successful}/{len(results)} successful, {total_records} records")

            # 每小時檢查一次
            await asyncio.sleep(3600)

        except Exception as e:
            logger.error(f"❌ Background scheduler error: {e}")
            await asyncio.sleep(300)  # 5分鐘後重試

# API endpoints
@app.get("/")
async def root():
    """根端點"""
    return APIResponse(
        success=True,
        message="每日任務API服務器運行中",
        data={
            "service": "每日任務API",
            "version": "2.0.0",
            "status": "running",
            "background_tasks": background_tasks_running,
            "data_sources": len(government_collector.data_sources)
        },
        timestamp=datetime.now()
    )

@app.get("/health")
async def health_check():
    """健康檢查"""
    return APIResponse(
        success=True,
        message="服務健康",
        data={
            "status": "healthy",
            "background_tasks": background_tasks_running,
            "uptime": "running"
        },
        timestamp=datetime.now()
    )

@app.get("/status")
async def get_system_status():
    """獲取系統狀態"""
    active_collections = len([
        s for s in collection_status.values()
        if s.status == "running"
    ])

    return APIResponse(
        success=True,
        message="系統狀態獲取成功",
        data={
            "system_status": "running",
            "last_update": datetime.now().isoformat(),
            "data_sources": len(government_collector.data_sources),
            "active_collections": active_collections,
            "total_collections_today": len(collection_status),
            "background_tasks_running": background_tasks_running
        },
        timestamp=datetime.now()
    )

@app.get("/data-sources")
async def get_data_sources():
    """獲取所有數據源配置"""
    sources_info = []
    for source in government_collector.data_sources:
        sources_info.append({
            "name": source.name,
            "url": source.url,
            "data_type": source.data_type,
            "refresh_interval": source.refresh_interval,
            "priority": source.priority
        })

    return APIResponse(
        success=True,
        message="數據源配置獲取成功",
        data={
            "data_sources": sources_info,
            "total_count": len(sources_info)
        },
        timestamp=datetime.now()
    )

@app.get("/collection-status")
async def get_collection_status():
    """獲取收集狀態"""
    status_data = {}
    for source_name, status in collection_status.items():
        status_data[source_name] = {
            "status": status.status,
            "last_update": status.last_update.isoformat(),
            "records_count": status.records_count,
            "error_message": status.error_message,
            "quality_score": status.quality_score
        }

    return APIResponse(
        success=True,
        message="收集狀態獲取成功",
        data={
            "status": status_data,
            "summary": {
                "total_sources": len(government_collector.data_sources),
                "completed_collections": len([s for s in collection_status.values() if s.status == "completed"]),
                "failed_collections": len([s for s in collection_status.values() if s.status == "failed"])
            }
        },
        timestamp=datetime.now()
    )

@app.post("/collect/{source_name}")
async def trigger_collection(source_name: str, background_tasks: BackgroundTasks):
    """
    手動觸發特定數據源收集
    """
    # 驗證數據源是否存在
    source_exists = any(source.name == source_name for source in government_collector.data_sources)
    if not source_exists:
        raise HTTPException(status_code=404, detail=f"數據源 {source_name} 未找到")

    # 添加後台任務
    background_tasks.add_task(collect_and_update_status, source_name)

    return APIResponse(
        success=True,
        message=f"已觸發 {source_name} 數據收集",
        data={"source_name": source_name, "status": "pending"},
        timestamp=datetime.now()
    )

@app.post("/collect-all")
async def trigger_collect_all(background_tasks: BackgroundTasks):
    """
    觸發所有數據源收集
    """
    # 添加後台任務
    background_tasks.add_task(collect_all_and_update_status)

    return APIResponse(
        success=True,
        message="已觸發所有數據源收集",
        data={
            "total_sources": len(government_collector.data_sources),
            "status": "pending"
        },
        timestamp=datetime.now()
    )

async def collect_and_update_status(source_name: str):
    """後台任務：收集數據並更新狀態"""
    try:
        logger.info(f"🔄 Starting background collection for {source_name}")

        # 更新狀態為運行中
        collection_status[source_name] = CollectionStatus(
            source_name=source_name,
            status="running",
            last_update=datetime.now()
        )

        # 執行收集
        result = await collect_hkma_data(source_name)

        if result:
            # 更新狀態為完成或失敗
            collection_status[source_name] = CollectionStatus(
                source_name=result.source_name,
                status="completed" if result.success else "failed",
                last_update=result.collection_time,
                records_count=result.record_count,
                error_message=result.error_message,
                quality_score=result.data_quality_score
            )

            if result.success:
                logger.info(f"✅ Background collection completed for {source_name}: {result.record_count} records")
            else:
                logger.error(f"❌ Background collection failed for {source_name}: {result.error_message}")
        else:
            # 收集返回None，設置為失敗
            collection_status[source_name] = CollectionStatus(
                source_name=source_name,
                status="failed",
                last_update=datetime.now(),
                records_count=0,
                error_message="Collection returned None"
            )
            logger.error(f"❌ Background collection returned None for {source_name}")

    except Exception as e:
        # 異常處理
        collection_status[source_name] = CollectionStatus(
            source_name=source_name,
            status="failed",
            last_update=datetime.now(),
            records_count=0,
            error_message=str(e)
        )
        logger.error(f"❌ Background collection exception for {source_name}: {e}")

async def collect_all_and_update_status():
    """後台任務：收集所有數據源並更新狀態"""
    try:
        logger.info("🔄 Starting background collection for all data sources")

        results = await collect_all_government_data()

        # 更新所有狀態
        for result in results:
            collection_status[result.source_name] = CollectionStatus(
                source_name=result.source_name,
                status="completed" if result.success else "failed",
                last_update=result.collection_time,
                records_count=result.record_count,
                error_message=result.error_message,
                quality_score=result.data_quality_score
            )

        successful = sum(1 for r in results if r.success)
        total_records = sum(r.record_count for r in results if r.success)
        logger.info(f"✅ Background collection completed: {successful}/{len(results)} successful, {total_records} records")

    except Exception as e:
        logger.error(f"❌ Background collection exception: {e}")

@app.get("/data/{source_name}/latest")
async def get_latest_data_api(source_name: str, limit: int = 10):
    """
    獲取指定數據源的最新數據
    """
    try:
        data = await get_latest_government_data(source_name, limit)

        if data is None:
            raise HTTPException(status_code=404, detail=f"未找到 {source_name} 的數據")

        return APIResponse(
            success=True,
            message=f"成功獲取 {source_name} 最新數據",
            data=data,
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest data for {source_name}: {e}")
        return APIResponse(
            success=False,
            message=f"獲取數據失敗: {str(e)}",
            error=str(e),
            timestamp=datetime.now()
        )

@app.get("/data/all/latest")
async def get_all_latest_data(limit: int = 5):
    """
    獲取所有數據源的最新數據摘要
    """
    try:
        all_data = {}
        errors = []

        for source_config in government_collector.data_sources:
            try:
                data = await get_latest_government_data(source_config.name, limit)
                if data:
                    all_data[source_config.name] = {
                        "data_type": source_config.data_type,
                        "priority": source_config.priority,
                        "total_records": data.get("total_records", 0),
                        "sample_records": data.get("records", [])[:2]  # 只返回前2條作為樣本
                    }
                else:
                    errors.append(f"{source_config.name}: 無數據")
            except Exception as e:
                errors.append(f"{source_config.name}: {str(e)}")

        return APIResponse(
            success=True,
            message="成功獲取所有數據源摘要",
            data={
                "sources": all_data,
                "total_sources": len(all_data),
                "errors": errors
            },
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error getting all latest data: {e}")
        return APIResponse(
            success=False,
            message=f"獲取數據失敗: {str(e)}",
            error=str(e),
            timestamp=datetime.now()
        )

@app.get("/metrics")
async def get_quality_metrics():
    """
    獲取數據質量指標
    """
    try:
        metrics = {}
        total_quality_score = 0
        quality_count = 0

        for source_name, status in collection_status.items():
            if status.status == "completed" and status.quality_score is not None:
                metrics[source_name] = {
                    "quality_score": status.quality_score,
                    "last_update": status.last_update.isoformat(),
                    "records_count": status.records_count
                }
                total_quality_score += status.quality_score
                quality_count += 1

        average_quality = total_quality_score / quality_count if quality_count > 0 else 0

        return APIResponse(
            success=True,
            message="質量指標獲取成功",
            data={
                "metrics": metrics,
                "summary": {
                    "total_sources": len(government_collector.data_sources),
                    "successful_collections": len([
                        s for s in collection_status.values() if s.status == "completed"
                    ]),
                    "average_quality_score": round(average_quality, 3),
                    "quality_assessed_sources": quality_count
                }
            },
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error getting quality metrics: {e}")
        return APIResponse(
            success=False,
            message=f"獲取質量指標失敗: {str(e)}",
            error=str(e),
            timestamp=datetime.now()
        )

if __name__ == "__main__":
    import uvicorn

    print("Starting Daily Tasks API Server...")
    print("Service URL: http://localhost:8001")
    print("API Documentation: http://localhost:8001/docs")

    # Run the server
    uvicorn.run(
        "daily_tasks_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )