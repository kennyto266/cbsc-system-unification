"""
Data Export API v2 Endpoints
數據導出API v2端點實現

Provides data export functionality with background job processing
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import json
import csv
import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
import logging
import pandas as pd
import asyncio

from ...deps import get_db, get_current_user
from ...services.influxdb_service import InfluxDBService
from ...services.cache_service import CacheService
from ...models.user import User

logger = logging.getLogger(__name__)

# Create router for export endpoints
export_router = APIRouter(prefix="/data", tags=["data-export"])

# Initialize services
influxdb_service = InfluxDBService()
cache_service = CacheService()

# In-memory storage for export jobs (in production, use Redis or database)
export_jobs: Dict[str, Dict] = {}


class ExportRequest:
    """Export request schema"""
    def __init__(
        self,
        data_type: str,
        symbols: Optional[List[str]] = None,
        indicators: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        format: str = "csv",
        include_metadata: bool = True,
        email: Optional[str] = None
    ):
        self.data_type = data_type
        self.symbols = symbols or []
        self.indicators = indicators or []
        self.start_date = start_date
        self.end_date = end_date
        self.format = format
        self.include_metadata = include_metadata
        self.email = email


@export_router.post("/export", response_model=Dict[str, Any], status_code=202)
async def create_export_job(
    export_request: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    創建數據導出任務

    Args:
        export_request: 導出請求參數
        background_tasks: 後台任務
        current_user: 當前用戶

    Returns:
        導出任務ID和狀態
    """
    try:
        # Validate export request
        if not export_request.get("data_type"):
            raise HTTPException(
                status_code=400,
                detail="data_type is required"
            )

        # Create export job
        job_id = str(uuid4())
        job = {
            "id": job_id,
            "user_id": current_user.id,
            "status": "queued",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "progress": 0,
            "request": export_request,
            "result_url": None,
            "error_message": None,
            "file_size": None,
            "record_count": None
        }

        # Store job
        export_jobs[job_id] = job

        # Add background task
        background_tasks.add_task(
            process_export_job,
            job_id,
            current_user.id
        )

        return {
            "job_id": job_id,
            "status": "queued",
            "message": "導出任務已創建，正在處理中...",
            "created_at": job["created_at"].isoformat(),
            "estimated_time": _estimate_export_time(export_request)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating export job: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create export job"
        )


@export_router.get("/export/{job_id}", response_model=Dict[str, Any])
async def get_export_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取導出任務狀態

    Args:
        job_id: 任務ID
        current_user: 當前用戶

    Returns:
        任務狀態信息
    """
    try:
        # Get job from storage
        job = export_jobs.get(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Export job not found"
            )

        # Check ownership
        if job["user_id"] != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

        return {
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "created_at": job["created_at"].isoformat(),
            "updated_at": job["updated_at"].isoformat(),
            "result_url": job["result_url"],
            "file_size": job["file_size"],
            "record_count": job["record_count"],
            "error_message": job["error_message"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export job status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get export job status"
        )


@export_router.get("/export/{job_id}/download")
async def download_export_file(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    下載導出文件

    Args:
        job_id: 任務ID
        current_user: 當前用戶

    Returns:
        文件下載響應
    """
    try:
        # Get job from storage
        job = export_jobs.get(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Export job not found"
            )

        # Check ownership
        if job["user_id"] != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

        # Check if job is completed
        if job["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Export job not completed. Current status: {job['status']}"
            )

        # Get file path
        file_path = job.get("result_url")
        if not file_path or not Path(file_path).exists():
            raise HTTPException(
                status_code=404,
                detail="Export file not found"
            )

        # Read file
        file_content = Path(file_path).read_bytes()

        # Determine media type
        if file_path.endswith(".csv"):
            media_type = "text/csv"
        elif file_path.endswith(".json"):
            media_type = "application/json"
        elif file_path.endswith(".zip"):
            media_type = "application/zip"
        else:
            media_type = "application/octet-stream"

        # Generate filename
        filename = f"export_{job_id}_{job['request']['data_type']}.{job['request']['format']}"

        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export file: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to download export file"
        )


@export_router.get("/export", response_model=Dict[str, Any])
async def list_export_jobs(
    status: Optional[str] = Query(None, regex="^(queued|processing|completed|failed)$"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取用戶的導出任務列表

    Args:
        status: 按狀態過濾
        limit: 返回數量限制

    Returns:
        導出任務列表
    """
    try:
        # Filter jobs by user
        user_jobs = []
        for job_id, job in export_jobs.items():
            if job["user_id"] == current_user.id:
                if not status or job["status"] == status:
                    user_jobs.append({
                        "job_id": job_id,
                        "status": job["status"],
                        "created_at": job["created_at"].isoformat(),
                        "updated_at": job["updated_at"].isoformat(),
                        "data_type": job["request"]["data_type"],
                        "file_size": job["file_size"],
                        "record_count": job["record_count"]
                    })

        # Sort by created_at (newest first)
        user_jobs.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply limit
        user_jobs = user_jobs[:limit]

        return {
            "jobs": user_jobs,
            "total": len(user_jobs),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error listing export jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list export jobs"
        )


@export_router.delete("/export/{job_id}")
async def delete_export_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刪除導出任務和相關文件

    Args:
        job_id: 任務ID
        current_user: 當前用戶

    Returns:
        刪除結果
    """
    try:
        # Get job from storage
        job = export_jobs.get(job_id)
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Export job not found"
            )

        # Check ownership
        if job["user_id"] != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

        # Delete file if exists
        file_path = job.get("result_url")
        if file_path and Path(file_path).exists():
            Path(file_path).unlink()

        # Delete job from storage
        del export_jobs[job_id]

        return {
            "message": "Export job deleted successfully",
            "job_id": job_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting export job: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete export job"
        )


async def process_export_job(job_id: str, user_id: int):
    """
    處理導出任務（後台任務）

    Args:
        job_id: 任務ID
        user_id: 用戶ID
    """
    try:
        # Get job
        job = export_jobs.get(job_id)
        if not job:
            return

        # Update status to processing
        job["status"] = "processing"
        job["updated_at"] = datetime.utcnow()

        # Get request parameters
        request = job["request"]
        data_type = request["data_type"]
        format_type = request.get("format", "csv")

        # Parse dates
        start_date = None
        end_date = None
        if request.get("start_date"):
            start_date = datetime.strptime(request["start_date"], "%Y-%m-%d")
        if request.get("end_date"):
            end_date = datetime.strptime(request["end_date"], "%Y-%m-%d")

        # Update progress
        job["progress"] = 10

        # Fetch data based on type
        if data_type == "market_data":
            data = await fetch_market_data(
                symbols=request.get("symbols", []),
                start_date=start_date,
                end_date=end_date
            )
        elif data_type == "economic_indicators":
            data = await fetch_economic_data(
                indicators=request.get("indicators", []),
                start_date=start_date,
                end_date=end_date
            )
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Update progress
        job["progress"] = 50

        # Export data to file
        export_path = await export_data_to_file(
            data=data,
            format_type=format_type,
            job_id=job_id,
            include_metadata=request.get("include_metadata", True)
        )

        # Update job
        job["status"] = "completed"
        job["progress"] = 100
        job["updated_at"] = datetime.utcnow()
        job["result_url"] = export_path
        job["file_size"] = Path(export_path).stat().st_size
        job["record_count"] = len(data) if isinstance(data, list) else len(data.get("data", []))

        logger.info(f"Export job {job_id} completed successfully")

    except Exception as e:
        # Update job with error
        job["status"] = "failed"
        job["error_message"] = str(e)
        job["updated_at"] = datetime.utcnow()
        logger.error(f"Export job {job_id} failed: {e}")


async def fetch_market_data(symbols: List[str], start_date: Optional[datetime], end_date: Optional[datetime]) -> List[Dict]:
    """獲取市場數據"""
    all_data = []

    for symbol in symbols:
        # Fetch from InfluxDB
        data = await influxdb_service.get_market_data(
            symbol=symbol,
            interval="1d",
            start_time=start_date,
            end_time=end_date
        )

        # Add symbol to each record
        for record in data:
            record["symbol"] = symbol

        all_data.extend(data)

    return all_data


async def fetch_economic_data(indicators: List[str], start_date: Optional[datetime], end_date: Optional[datetime]) -> Dict:
    """獲取經濟指標數據"""
    data = {"indicators": {}}

    for indicator in indicators:
        # Fetch from InfluxDB
        records = await influxdb_service.get_economic_data(
            indicator=indicator,
            start_time=start_date,
            end_time=end_date
        )

        data["indicators"][indicator] = records

    return data


async def export_data_to_file(data: Any, format_type: str, job_id: str, include_metadata: bool = True) -> str:
    """導出數據到文件"""
    # Create export directory
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)

    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"export_{job_id}_{timestamp}.{format_type}"
    file_path = export_dir / filename

    if format_type == "csv":
        # Export to CSV
        if isinstance(data, list) and data:
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
        else:
            # Handle nested data
            with open(file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Indicator", "Date", "Value", "Unit"])

                if isinstance(data, dict) and "indicators" in data:
                    for indicator, records in data["indicators"].items():
                        for record in records:
                            writer.writerow([
                                indicator,
                                record.get("time", ""),
                                record.get("value", ""),
                                record.get("unit", "")
                            ])

    elif format_type == "json":
        # Export to JSON
        export_data = {
            "data": data,
            "exported_at": datetime.utcnow().isoformat()
        }

        if include_metadata:
            export_data["metadata"] = {
                "total_records": len(data) if isinstance(data, list) else sum(len(v) for v in data.values() if isinstance(v, list)),
                "export_format": "json",
                "version": "1.0"
            }

        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

    elif format_type == "excel":
        # Export to Excel
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            if isinstance(data, list) and data:
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name="Data", index=False)
            elif isinstance(data, dict) and "indicators" in data:
                # Create separate sheet for each indicator
                for indicator, records in data["indicators"].items():
                    df = pd.DataFrame(records)
                    df.to_excel(writer, sheet_name=indicator[:31], index=False)  # Sheet name max 31 chars

    return str(file_path)


def _estimate_export_time(request: Dict) -> str:
    """估算導出時間"""
    data_type = request.get("data_type")
    symbols = request.get("symbols", [])
    indicators = request.get("indicators", [])

    # Simple estimation based on data size
    total_items = len(symbols) + len(indicators)

    if total_items <= 5:
        return "< 1 minute"
    elif total_items <= 20:
        return "1-3 minutes"
    elif total_items <= 50:
        return "3-5 minutes"
    else:
        return "5+ minutes"