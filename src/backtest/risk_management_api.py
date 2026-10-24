"""
Risk Management API Service
============================

FastAPI service providing comprehensive risk analysis endpoints for the CBSC system.
Integrates enhanced risk analyzer, real-time monitor, and dynamic adjuster.

Author: CBSC Risk Management Team
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio
import logging
import json
import numpy as np
import pandas as pd
from enum import Enum

# Import our risk management modules
from enhanced_risk_analyzer import (
    EnhancedRiskAnalyzer,
    RiskMetrics,
    StressTestResult,
    RiskContribution
)
from real_time_risk_monitor import (
    RealTimeRiskMonitor,
    RiskAlert,
    RiskLevel,
    AdjustmentType
)
from dynamic_risk_adjuster import (
    DynamicRiskAdjustmentSystem,
    AdjustmentRule,
    PositionScalingAdjuster,
    VolatilityTargetingAdjuster
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CBSC Risk Management API",
    description="Advanced risk analysis and management for quantitative trading strategies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your security requirements
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
risk_analyzer = EnhancedRiskAnalyzer()
risk_monitor = None  # Will be initialized per strategy
dynamic_adjuster = DynamicRiskAdjustmentSystem()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, strategy_id: str):
        await websocket.accept()
        if strategy_id not in self.active_connections:
            self.active_connections[strategy_id] = []
        self.active_connections[strategy_id].append(websocket)
        logger.info(f"WebSocket connected for strategy {strategy_id}")

    def disconnect(self, websocket: WebSocket, strategy_id: str):
        if strategy_id in self.active_connections:
            self.active_connections[strategy_id].remove(websocket)
            if not self.active_connections[strategy_id]:
                del self.active_connections[strategy_id]
        logger.info(f"WebSocket disconnected for strategy {strategy_id}")

    async def send_personal_message(self, message: dict, strategy_id: str):
        if strategy_id in self.active_connections:
            for connection in self.active_connections[strategy_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")

manager = ConnectionManager()

# Pydantic models for API
class ReturnsData(BaseModel):
    """Returns data for analysis"""
    returns: List[float] = Field(..., description="Daily returns series")
    dates: Optional[List[str]] = Field(None, description="Corresponding dates")

class PortfolioData(BaseModel):
    """Portfolio data for comprehensive analysis"""
    values: List[float] = Field(..., description="Portfolio values over time")
    positions: Dict[str, float] = Field(..., description="Current positions")
    cash: float = Field(0.0, description="Cash position")

class RiskAnalysisRequest(BaseModel):
    """Request for comprehensive risk analysis"""
    strategy_id: str = Field(..., description="Strategy identifier")
    returns_data: ReturnsData = Field(..., description="Returns data")
    portfolio_data: Optional[PortfolioData] = Field(None, description="Portfolio data")
    benchmark_returns: Optional[List[float]] = Field(None, description="Benchmark returns")
    confidence_levels: Optional[List[float]] = Field([0.95, 0.99], description="VaR confidence levels")
    analysis_window: Optional[int] = Field(252, description="Analysis window in days")

class StressTestRequest(BaseModel):
    """Request for stress testing"""
    strategy_id: str
    returns_data: ReturnsData
    portfolio_data: PortfolioData
    scenarios: Optional[List[str]] = Field(None, description="Custom stress scenarios")
    historical_crises: Optional[List[str]] = Field(None, description="Historical crisis periods")

class MonitoringRequest(BaseModel):
    """Request to start real-time monitoring"""
    strategy_id: str
    thresholds: Dict[str, Dict[str, float]] = Field(..., description="Risk thresholds")
    update_frequency: int = Field(60, description="Update frequency in seconds")
    auto_adjust: bool = Field(False, description="Enable automatic adjustments")
    adjustment_rules: Optional[List[Dict]] = Field(None, description="Adjustment rules")

class AdjustmentRequest(BaseModel):
    """Request for dynamic position adjustment"""
    strategy_id: str
    current_positions: Dict[str, float]
    returns_data: ReturnsData
    portfolio_data: PortfolioData
    adjustment_type: str = Field("position_scaling", description="Type of adjustment")
    risk_budget: float = Field(0.02, description="Daily risk budget")
    target_leverage: float = Field(1.0, description="Target leverage")

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "CBSC Risk Management API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/risk/comprehensive")
async def comprehensive_risk_analysis(request: RiskAnalysisRequest):
    """
    Comprehensive risk analysis including VaR, drawdowns, and other metrics
    """
    try:
        # Convert data to numpy arrays
        returns = np.array(request.returns_data.returns)

        portfolio_values = None
        if request.portfolio_data:
            portfolio_values = np.array(request.portfolio_data.values)

        benchmark_returns = None
        if request.benchmark_returns:
            benchmark_returns = np.array(request.benchmark_returns)

        # Perform comprehensive risk analysis
        risk_metrics = risk_analyzer.calculate_comprehensive_risk_metrics(
            returns=returns,
            portfolio_values=portfolio_values,
            positions=request.portfolio_data.positions if request.portfolio_data else {},
            benchmark_returns=benchmark_returns,
            confidence_levels=request.confidence_levels
        )

        # Format response
        response = {
            "strategy_id": request.strategy_id,
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "comprehensive",
            "risk_metrics": {
                "var_metrics": {
                    f"var_{int(conf*100)}%": float(var) for conf, var in risk_metrics.var.confidence_levels.items()
                },
                "expected_shortfall": {
                    f"es_{int(conf*100)}%": float(es) for conf, es in risk_metrics.expected_shortfall.confidence_levels.items()
                },
                "drawdown_analysis": {
                    "max_drawdown": float(risk_metrics.drawdown_metrics.max_drawdown),
                    "avg_drawdown": float(risk_metrics.drawdown_metrics.average_drawdown),
                    "drawdown_duration": risk_metrics.drawdown_metrics.max_drawdown_duration,
                    "current_drawdown": float(risk_metrics.drawdown_metrics.current_drawdown)
                },
                "volatility_metrics": {
                    "annual_volatility": float(risk_metrics.volatility_metrics.annualized),
                    "monthly_volatility": float(risk_metrics.volatility_metrics.monthly),
                    "daily_volatility": float(risk_metrics.volatility_metrics.daily),
                    "volatility_regime": risk_metrics.volatility_metrics.regime
                },
                "correlation_metrics": {
                    "avg_correlation": float(risk_metrics.correlation_metrics.average_correlation),
                    "max_correlation": float(risk_metrics.correlation_metrics.max_correlation),
                    "concentration_ratio": risk_metrics.correlation_metrics.concentration_ratio,
                    "effective_positions": risk_metrics.correlation_metrics.effective_positions
                },
                "tail_ratio": float(risk_metrics.tail_ratio),
                "skewness": float(risk_metrics.skewness),
                "excess_kurtosis": float(risk_metrics.excess_kurtosis),
                "calmar_ratio": float(risk_metrics.calmar_ratio),
                "sortino_ratio": float(risk_metrics.sortino_ratio),
                "information_ratio": float(risk_metrics.information_ratio) if risk_metrics.information_ratio else None
            }
        }

        return response

    except Exception as e:
        logger.error(f"Error in comprehensive risk analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/risk/stress-test")
async def stress_test_analysis(request: StressTestRequest):
    """
    Perform stress testing on the strategy
    """
    try:
        returns = np.array(request.returns_data.returns)
        portfolio_values = np.array(request.portfolio_data.values)

        # Define stress scenarios
        scenarios = request.scenarios or [
            "market_crash_2008",
            "covid_crash_2020",
            "dot_com_bubble_2000",
            "inflation_shock",
            "interest_rate_spike",
            "liquidity_crisis"
        ]

        # Perform stress testing
        stress_results = {}
        for scenario in scenarios:
            result = risk_analyzer.run_stress_test(
                returns=returns,
                portfolio_values=portfolio_values,
                positions=request.portfolio_data.positions,
                scenario=scenario
            )
            stress_results[scenario] = {
                "scenario_loss": float(result.scenario_loss),
                "portfolio_impact": float(result.portfolio_impact),
                "var_breach": result.var_breach,
                "worst_position": result.worst_position,
                "recovery_time": result.recovery_time,
                "description": result.description
            }

        return {
            "strategy_id": request.strategy_id,
            "timestamp": datetime.now().isoformat(),
            "stress_results": stress_results,
            "summary": {
                "worst_scenario": min(stress_results.keys(),
                                    key=lambda x: stress_results[x]["scenario_loss"]),
                "avg_scenario_loss": np.mean([r["scenario_loss"] for r in stress_results.values()]),
                "var_breaches": sum(1 for r in stress_results.values() if r["var_breach"])
            }
        }

    except Exception as e:
        logger.error(f"Error in stress test analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/monitoring/start")
async def start_real_time_monitoring(
    request: MonitoringRequest,
    background_tasks: BackgroundTasks
):
    """
    Start real-time risk monitoring for a strategy
    """
    try:
        if request.strategy_id in [s.split('_')[1] for s in manager.active_connections.keys()]:
            return {"message": f"Monitoring already active for strategy {request.strategy_id}"}

        # Create monitoring instance
        global risk_monitor
        risk_monitor = RealTimeRiskMonitor(
            strategy_id=request.strategy_id,
            thresholds=request.thresholds,
            update_frequency=request.update_frequency,
            auto_adjust=request.auto_adjust
        )

        # Add adjustment rules if provided
        if request.adjustment_rules:
            for rule_data in request.adjustment_rules:
                rule = AdjustmentRule(
                    name=rule_data["name"],
                    trigger_condition=rule_data["trigger_condition"],
                    adjustment_type=AdjustmentType(rule_data["adjustment_type"]),
                    parameters=rule_data["parameters"]
                )
                risk_monitor.add_adjustment_rule(rule)

        # Start monitoring in background
        background_tasks.add_task(
            run_monitoring_task,
            risk_monitor,
            request.strategy_id
        )

        return {
            "message": f"Real-time monitoring started for strategy {request.strategy_id}",
            "strategy_id": request.strategy_id,
            "monitoring_config": {
                "update_frequency": request.update_frequency,
                "auto_adjust": request.auto_adjust,
                "thresholds": request.thresholds
            }
        }

    except Exception as e:
        logger.error(f"Error starting real-time monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/monitoring/stop")
async def stop_real_time_monitoring(strategy_id: str):
    """
    Stop real-time monitoring for a strategy
    """
    try:
        # Stop monitoring
        if risk_monitor and risk_monitor.strategy_id == strategy_id:
            risk_monitor.stop_monitoring()
            return {"message": f"Monitoring stopped for strategy {strategy_id}"}
        else:
            return {"message": f"No active monitoring found for strategy {strategy_id}"}

    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/adjustment/evaluate")
async def evaluate_adjustments(request: AdjustmentRequest):
    """
    Evaluate and suggest dynamic position adjustments
    """
    try:
        returns = np.array(request.returns_data.returns)
        portfolio_values = np.array(request.portfolio_data.values)

        # Evaluate adjustments
        adjustments = dynamic_adjuster.evaluate_and_adjust(
            current_positions=request.current_positions,
            returns=returns,
            portfolio_values=portfolio_values,
            risk_budget=request.risk_budget,
            target_leverage=request.target_leverage
        )

        # Format response
        adjustment_list = []
        for adj in adjustments:
            adjustment_list.append({
                "asset": adj.asset,
                "current_size": float(adj.current_size),
                "suggested_size": float(adj.suggested_size),
                "adjustment_reason": adj.reason,
                "risk_impact": float(adj.risk_impact),
                "expected_return_impact": float(adj.expected_return_impact)
            })

        return {
            "strategy_id": request.strategy_id,
            "timestamp": datetime.now().isoformat(),
            "adjustments": adjustment_list,
            "summary": {
                "total_adjustment_count": len(adjustments),
                "net_leverage_change": sum([adj["suggested_size"] - adj["current_size"]
                                          for adj in adjustment_list]),
                "risk_reduction_estimate": sum([abs(adj["risk_impact"]) for adj in adjustment_list])
            }
        }

    except Exception as e:
        logger.error(f"Error evaluating adjustments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/monitoring/alerts/{strategy_id}")
async def get_monitoring_alerts(strategy_id: str, limit: int = 50):
    """
    Get recent alerts for a strategy
    """
    try:
        # This would typically fetch from database
        # For now, return mock data
        return {
            "strategy_id": strategy_id,
            "alerts": [
                {
                    "timestamp": "2024-01-15T10:30:00Z",
                    "level": "HIGH",
                    "type": "VAR_BREACH",
                    "message": "VaR 95% breached: actual loss -3.2% vs limit -2.0%",
                    "current_value": -0.032,
                    "threshold": -0.02,
                    "action_taken": "Position reduced by 20%"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{strategy_id}")
async def websocket_endpoint(websocket: WebSocket, strategy_id: str):
    await manager.connect(websocket, strategy_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, strategy_id)

# Background task for monitoring
async def run_monitoring_task(monitor: RealTimeRiskMonitor, strategy_id: str):
    """
    Background task to run real-time monitoring
    """
    try:
        await monitor.start_monitoring()

        # Keep monitoring running
        while monitor.monitoring_active:
            # Get latest alerts
            alerts = monitor.get_recent_alerts(limit=10)

            # Send updates via WebSocket
            if alerts:
                await manager.send_personal_message(
                    {
                        "type": "risk_alert",
                        "strategy_id": strategy_id,
                        "alerts": [
                            {
                                "timestamp": alert.timestamp.isoformat(),
                                "level": alert.level.value,
                                "type": alert.alert_type,
                                "message": alert.message,
                                "current_value": alert.current_value,
                                "threshold": alert.threshold,
                                "action_taken": alert.action_taken
                            } for alert in alerts
                        ]
                    },
                    strategy_id
                )

            await asyncio.sleep(60)  # Check every minute

    except Exception as e:
        logger.error(f"Error in monitoring task: {e}")
        await manager.send_personal_message(
            {
                "type": "error",
                "strategy_id": strategy_id,
                "message": f"Monitoring error: {str(e)}"
            },
            strategy_id
        )

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "risk_management_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )