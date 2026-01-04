"""
Report Generation API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import uuid
from datetime import datetime

from src.backtest.report_generator import ReportGenerator

router = APIRouter(prefix="/api/reports", tags=["reports"])

# In-memory storage for task status (in production, use Redis or database)
report_tasks: Dict[str, Dict] = {}


class ReportRequest(BaseModel):
    """Request model for report generation"""
    backtest_id: str = Field(..., description="Backtest result ID")
    format: str = Field(default="pdf", description="Report format: pdf, excel, html, json")
    include_charts: bool = Field(default=True, description="Include charts in report")
    template_name: str = Field(default="default", description="Template name for HTML reports")
    email: Optional[str] = Field(None, description="Email to send report to")


class ReportResponse(BaseModel):
    """Response model for report generation"""
    task_id: str
    status: str
    message: str
    download_url: Optional[str] = None


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a backtest report

    This endpoint creates a report in the specified format.
    For large reports, it runs as a background task.
    """
    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Initialize task status
    report_tasks[task_id] = {
        "status": "pending",
        "message": "Report generation queued",
        "created_at": datetime.now(),
        "backtest_id": request.backtest_id,
        "format": request.format,
        "file_path": None,
        "error": None
    }

    # Queue background task
    background_tasks.add_task(
        _generate_report_task,
        task_id,
        request.backtest_id,
        request.format,
        request.include_charts,
        request.template_name
    )

    return ReportResponse(
        task_id=task_id,
        status="pending",
        message="Report generation started"
    )


@router.get("/status/{task_id}")
async def get_report_status(task_id: str):
    """
    Get the status of a report generation task
    """
    if task_id not in report_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = report_tasks[task_id]

    response = {
        "task_id": task_id,
        "status": task["status"],
        "message": task["message"],
        "created_at": task["created_at"]
    }

    if task["status"] == "completed" and task["file_path"]:
        response["download_url"] = f"/api/reports/download/{task_id}"

    if task["error"]:
        response["error"] = task["error"]

    return response


@router.get("/download/{task_id}")
async def download_report(task_id: str):
    """
    Download a generated report
    """
    if task_id not in report_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = report_tasks[task_id]

    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Report not ready")

    if not task["file_path"] or not os.path.exists(task["file_path"]):
        raise HTTPException(status_code=404, detail="Report file not found")

    # Determine media type based on format
    format = task["format"]
    media_types = {
        "pdf": "application/pdf",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "html": "text/html",
        "json": "application/json"
    }

    media_type = media_types.get(format, "application/octet-stream")

    return FileResponse(
        task["file_path"],
        media_type=media_type,
        filename=f"backtest_report_{task_id}.{format}"
    )


@router.get("/list")
async def list_reports():
    """
    List all report generation tasks
    """
    return {
        "tasks": [
            {
                "task_id": task_id,
                "status": task["status"],
                "created_at": task["created_at"],
                "backtest_id": task["backtest_id"],
                "format": task["format"]
            }
            for task_id, task in report_tasks.items()
        ]
    }


@router.delete("/task/{task_id}")
async def delete_report_task(task_id: str):
    """
    Delete a report task and associated file
    """
    if task_id not in report_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = report_tasks[task_id]

    # Delete file if it exists
    if task["file_path"] and os.path.exists(task["file_path"]):
        os.remove(task["file_path"])

    # Remove task from memory
    del report_tasks[task_id]

    return {"message": "Task deleted successfully"}


async def _generate_report_task(
    task_id: str,
    backtest_id: str,
    format: str,
    include_charts: bool,
    template_name: str
):
    """
    Background task to generate report
    """
    try:
        # Update task status
        report_tasks[task_id]["status"] = "processing"
        report_tasks[task_id]["message"] = "Generating report..."

        # Get backtest result (in production, fetch from database)
        # For now, we'll use mock data
        backtest_result = await _get_backtest_result(backtest_id)

        if not backtest_result:
            report_tasks[task_id]["status"] = "failed"
            report_tasks[task_id]["error"] = "Backtest result not found"
            return

        # Initialize report generator
        output_dir = os.path.join("reports", task_id)
        generator = ReportGenerator(output_dir=output_dir)

        # Generate report
        file_path = generator.generate_report(
            backtest_result=backtest_result,
            format=format,
            include_charts=include_charts,
            template_name=template_name
        )

        # Update task status
        report_tasks[task_id]["status"] = "completed"
        report_tasks[task_id]["message"] = "Report generated successfully"
        report_tasks[task_id]["file_path"] = file_path

    except Exception as e:
        # Update task with error
        report_tasks[task_id]["status"] = "failed"
        report_tasks[task_id]["error"] = str(e)
        report_tasks[task_id]["message"] = f"Error generating report: {str(e)}"


async def _get_backtest_result(backtest_id: str) -> Optional[Dict]:
    """
    Get backtest result by ID
    In production, this would fetch from database
    """
    # Mock data for testing
    import numpy as np
    import pandas as pd

    # Generate sample data
    dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
    portfolio_values = np.cumprod(1 + np.random.randn(len(dates)) * 0.01) * 100000
    daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]

    return {
        "strategy_name": "MA Crossover Strategy",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 100000,
        "final_capital": portfolio_values[-1],
        "total_return": (portfolio_values[-1] - 100000) / 100000,
        "annualized_return": ((portfolio_values[-1] / 100000) ** (252 / len(dates))) - 1,
        "sharpe_ratio": 1.23,
        "max_drawdown": -0.15,
        "metrics": {
            "volatility": 0.18,
            "sortino_ratio": 1.45,
            "calmar_ratio": 0.82,
            "information_ratio": 0.65,
            "total_trades": 45,
            "winning_trades": 28,
            "losing_trades": 17,
            "win_rate": 0.622,
            "profit_factor": 1.75,
            "avg_win": 1250.50,
            "avg_loss": -680.25,
            "total_commission": 1250.00,
            "total_slippage": 890.50,
            "var_95": -0.025,
            "var_99": -0.040,
            "expected_shortfall_95": -0.032,
            "max_drawdown_duration": 45,
            "omega_ratio": 1.35,
            "beta": 0.95,
            "alpha": 0.045,
            "treynor_ratio": 0.155,
            "jensen_alpha": 0.038,
            "relative_sharpe_ratio": 0.12,
            "buy_hold_sharpe": 1.11,
            "enhanced_calmar": 0.82,
            "enhanced_sortino": 1.45,
            "information_ratio_enhanced": 0.65,
            "upside_capture": 1.05,
            "downside_capture": 0.92,
            "gain_loss_ratio": 1.84,
            "profit_factor_enhanced": 1.75
        },
        "trades": [
            {
                "date": "2023-01-15",
                "symbol": "HK.00700",
                "action": "BUY",
                "quantity": 1000,
                "price": 185.50,
                "commission": 5.00,
                "slippage": 10.25,
                "pnl": 1250.00
            },
            {
                "date": "2023-02-20",
                "symbol": "HK.00700",
                "action": "SELL",
                "quantity": 1000,
                "price": 195.75,
                "commission": 5.00,
                "slippage": 8.50,
                "pnl": 10150.00
            }
        ],
        "portfolio_values": portfolio_values.tolist(),
        "daily_returns": daily_returns.tolist()
    }


@router.get("/templates")
async def list_report_templates():
    """
    List available report templates
    """
    templates = [
        {
            "name": "default",
            "description": "Standard CBSC report template",
            "format": "html"
        },
        {
            "name": "executive",
            "description": "Executive summary template",
            "format": "html"
        },
        {
            "name": "detailed",
            "description": "Detailed analysis template",
            "format": "html"
        }
    ]

    return {"templates": templates}


@router.post("/preview")
async def preview_report(
    backtest_id: str,
    template_name: str = "default",
    include_charts: bool = False
):
    """
    Generate a quick preview of the report (HTML only)
    """
    try:
        # Get backtest result
        backtest_result = await _get_backtest_result(backtest_id)

        if not backtest_result:
            raise HTTPException(status_code=404, detail="Backtest result not found")

        # Initialize report generator
        generator = ReportGenerator(output_dir="temp_reports")

        # Generate HTML preview
        preview_path = generator.generate_report(
            backtest_result=backtest_result,
            format="html",
            include_charts=include_charts,
            template_name=template_name
        )

        # Read and return HTML content
        with open(preview_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Clean up temporary file
        os.remove(preview_path)

        return HTMLResponse(content=html_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi.responses import HTMLResponse