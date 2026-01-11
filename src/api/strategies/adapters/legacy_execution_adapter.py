"""
Legacy Execution API Adapter
將舊的策略執行API調用適配到新的執行服務
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..services.execution_service import ExecutionService

logger = logging.getLogger(__name__)


class LegacyExecutionAdapter:
    """
    適配器模式實現 - 將舊執行API的數據格式轉換為新格式
    """

    def __init__(self, execution_service: ExecutionService):
        self.execution_service = execution_service

    async def execute_strategy(
        self,
        strategy_id: str,
        user_id: int,
        execution_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        適配舊的策略執行接口
        原接口: POST /api/strategies/{id}/execute
        """
        try:
            # 轉換參數格式
            execution_request = self._convert_execution_params(
                strategy_id,
                user_id,
                execution_params
            )

            # 調用新服務
            execution = await self.execution_service.execute_strategy(execution_request)

            return {
                "success": True,
                "data": {
                    "execution_id": execution.id,
                    "strategy_id": execution.strategy_id,
                    "status": execution.status,
                    "start_time": execution.start_time,
                    "message": "策略執行已啟動"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"執行策略失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "EXECUTION_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    async def stop_strategy_execution(
        self,
        execution_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        適配舊的停止策略執行接口
        原接口: POST /api/strategies/{id}/stop
        """
        try:
            await self.execution_service.stop_execution(execution_id, user_id)

            return {
                "success": True,
                "message": "策略執行已停止",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"停止策略執行失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "STOP_EXECUTION_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_execution_status(
        self,
        execution_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        適配舊的獲取執行狀態接口
        原接口: GET /api/strategies/executions/{execution_id}
        """
        try:
            execution = await self.execution_service.get_execution(
                execution_id, user_id
            )

            return {
                "success": True,
                "data": {
                    "execution_id": execution.id,
                    "strategy_id": execution.strategy_id,
                    "status": execution.status,
                    "progress": execution.progress,
                    "start_time": execution.start_time,
                    "end_time": execution.end_time,
                    "results": execution.results,
                    "error_message": execution.error_message
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"獲取執行狀態失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "GET_STATUS_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_strategy_performance(
        self,
        strategy_id: str,
        user_id: int,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        適配舊的獲取策略性能接口
        原接口: GET /api/strategies/{id}/performance
        """
        try:
            # 轉換時間範圍參數
            start_time, end_time = self._parse_time_range(time_range)

            # 調用新服務
            performance = await self.execution_service.get_performance_metrics(
                strategy_id, user_id, start_time, end_time
            )

            return {
                "success": True,
                "data": {
                    "strategy_id": strategy_id,
                    "total_return": performance.total_return,
                    "sharpe_ratio": performance.sharpe_ratio,
                    "max_drawdown": performance.max_drawdown,
                    "win_rate": performance.win_rate,
                    "total_trades": performance.total_trades,
                    "profitable_trades": performance.profitable_trades,
                    "time_range": time_range or "all"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"獲取策略性能失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "GET_PERFORMANCE_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    def _convert_execution_params(
        self,
        strategy_id: str,
        user_id: int,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        轉換執行參數格式
        """
        # 映射執行模式
        mode_mapping = {
            "backtest": "backtest",
            "paper": "paper_trading",
            "live": "live_trading"
        }

        return {
            "strategy_id": strategy_id,
            "user_id": user_id,
            "execution_mode": mode_mapping.get(
                params.get("mode", "backtest"),
                "backtest"
            ),
            "start_time": params.get("start_time"),
            "end_time": params.get("end_time"),
            "initial_capital": params.get("initial_capital", 100000),
            "parameters": params.get("parameters", {}),
            "risk_controls": params.get("risk_controls", {})
        }

    def _parse_time_range(
        self,
        time_range: Optional[str]
    ) -> tuple:
        """
        解析時間範圍參數
        """
        if not time_range:
            return None, None

        # 簡單的時間範圍解析
        if time_range == "1d":
            # 最近1天
            from datetime import datetime, timedelta
            end = datetime.utcnow()
            start = end - timedelta(days=1)
            return start, end
        elif time_range == "1w":
            # 最近1周
            from datetime import datetime, timedelta
            end = datetime.utcnow()
            start = end - timedelta(weeks=1)
            return start, end
        elif time_range == "1m":
            # 最近1月
            from datetime import datetime, timedelta
            end = datetime.utcnow()
            start = end - timedelta(days=30)
            return start, end
        else:
            return None, None