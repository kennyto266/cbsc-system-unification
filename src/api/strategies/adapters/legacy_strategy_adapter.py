"""
Legacy Strategy API Adapter
將舊的個人策略API調用適配到新的策略服務
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..services.strategy_service import BaseStrategyService
from ..schemas import StrategyCreate, StrategyUpdate, StrategyResponse
from ..models import StrategyType, StrategyStatus, RiskLevel

logger = logging.getLogger(__name__)


class LegacyStrategyAdapter:
    """
    適配器模式實現 - 將舊API的數據格式轉換為新格式
    """

    def __init__(self, strategy_service: BaseStrategyService):
        self.strategy_service = strategy_service

    async def get_personal_strategies(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        適配舊的獲取個人策略接口
        原接口: GET /api/personal-strategies
        """
        try:
            # 轉換查詢參數
            filters = {}
            if status:
                filters["status"] = status

            # 調用新服務
            result = await self.strategy_service.list_strategies(
                page=page,
                page_size=page_size,
                user_id=user_id,
                **filters
            )

            # 轉換為舊格式響應
            return {
                "success": True,
                "data": result["items"],
                "pagination": {
                    "page": result["page"],
                    "page_size": result["page_size"],
                    "total": result["total"],
                    "pages": result["pages"]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"獲取個人策略失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "GET_STRATEGIES_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    async def create_personal_strategy(
        self,
        user_id: int,
        strategy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        適配舊的創建策略接口
        原接口: POST /api/personal-strategies
        """
        try:
            # 轉換舊格式到新格式
            create_request = self._convert_legacy_to_create(strategy_data, user_id)

            # 調用新服務
            strategy = await self.strategy_service.create_strategy(create_request, user_id)

            return {
                "success": True,
                "data": strategy.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"創建策略失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "CREATE_STRATEGY_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    async def update_personal_strategy(
        self,
        strategy_id: str,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        適配舊的更新策略接口
        原接口: PUT /api/personal-strategies/{id}
        """
        try:
            # 轉換為新格式
            update_request = self._convert_legacy_to_update(update_data)

            # 調用新服務
            strategy = await self.strategy_service.update_strategy(
                strategy_id, update_request, user_id
            )

            return {
                "success": True,
                "data": strategy.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"更新策略失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "UPDATE_STRATEGY_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    async def delete_personal_strategy(
        self,
        strategy_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        適配舊的刪除策略接口
        原接口: DELETE /api/personal-strategies/{id}
        """
        try:
            await self.strategy_service.delete_strategy(strategy_id, user_id)

            return {
                "success": True,
                "message": "策略刪除成功",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"刪除策略失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "DELETE_STRATEGY_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_strategy_detail(
        self,
        strategy_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        適配舊的獲取策略詳情接口
        原接口: GET /api/personal-strategies/{id}
        """
        try:
            strategy = await self.strategy_service.get_strategy(strategy_id, user_id)

            return {
                "success": True,
                "data": strategy.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"獲取策略詳情失敗: {e}")
            return {
                "success": False,
                "error": {
                    "code": "GET_STRATEGY_FAILED",
                    "message": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

    def _convert_legacy_to_create(
        self,
        legacy_data: Dict[str, Any],
        user_id: int
    ) -> StrategyCreate:
        """
        將舊格式數據轉換為StrategyCreate對象
        """
        # 映射策略類型
        strategy_type_mapping = {
            "RSI": StrategyType.DIRECT_RSI,
            "MACD": StrategyType.MACD_CROSS,
            "BOLLINGER": StrategyType.BOLLINGER_BANDS,
            "CUSTOM": StrategyType.CUSTOM
        }

        # 映射風險級別
        risk_mapping = {
            "LOW": RiskLevel.LOW,
            "MEDIUM": RiskLevel.MEDIUM,
            "HIGH": RiskLevel.HIGH
        }

        return StrategyCreate(
            name=legacy_data.get("name"),
            description=legacy_data.get("description", ""),
            strategy_type=strategy_type_mapping.get(
                legacy_data.get("strategy_type", "CUSTOM"),
                StrategyType.CUSTOM
            ),
            parameters=legacy_data.get("parameters", {}),
            risk_level=risk_mapping.get(
                legacy_data.get("risk_level", "MEDIUM"),
                RiskLevel.MEDIUM
            ),
            is_active=legacy_data.get("is_active", True),
            user_id=user_id
        )

    def _convert_legacy_to_update(
        self,
        legacy_data: Dict[str, Any]
    ) -> StrategyUpdate:
        """
        將舊格式數據轉換為StrategyUpdate對象
        """
        update_data = {}

        if "name" in legacy_data:
            update_data["name"] = legacy_data["name"]
        if "description" in legacy_data:
            update_data["description"] = legacy_data["description"]
        if "parameters" in legacy_data:
            update_data["parameters"] = legacy_data["parameters"]
        if "is_active" in legacy_data:
            update_data["is_active"] = legacy_data["is_active"]

        return StrategyUpdate(**update_data)