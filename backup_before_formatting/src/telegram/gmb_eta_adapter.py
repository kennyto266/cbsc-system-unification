#!/usr / bin / env python3
"""
GMB(專線小巴) ETA API 集成模塊
根據香港運輸署GMB ETA API規範實現
"""

import asyncio
import dataclasses
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

# 配置日誌
logger = logging.getLogger(__name__)


@dataclasses.dataclass
class GMBRoute:
    """GMB路線信息"""

    route_id: str
    route: str
    region: str
    orig_tc: str
    dest_tc: str


@dataclasses.dataclass
class GMBStop:
    """GMB站點信息"""

    stop_id: str
    stop_seq: int
    name_tc: str
    name_en: str
    lat: float
    long: float


@dataclasses.dataclass
class GMBETA:
    """GMB到站時間信息"""

    eta: str  # 時間格式 "YYYY - MM - DD HH:MM:SS"
    minutes: int  # 分鐘差
    rmk_tc: str  # 備註(中文)
    rmk_en: str  # 備註(英文)


class GMBETAAdapter:
    """GMB ETA API適配器"""

    BASE_URL = "https://data.etagmb.gov.hk"

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取HTTP會話"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Accept": "application / json"},
            )
        return self.session

    async def close(self):
        """關閉HTTP會話"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """發送HTTP請求"""
        try:
            session = await self._get_session()
            url = f"{self.BASE_URL}{endpoint}"

            logger.info(f"請求GMB API: {url}")
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status >= 400:
                    # API不可用，返回錯誤
                    logger.error(f"GMB API返回錯誤: HTTP {response.status}")
                    return {"error": f"API HTTP {response.status}"}
                else:
                    logger.error(f"GMB API請求失敗: HTTP {response.status}")
                    return {"error": f"HTTP {response.status}"}

        except asyncio.TimeoutError:
            logger.error("GMB API請求超時")
            return {"error": "請求超時"}
        except Exception as e:
            logger.error(f"GMB API請求異常: {e}")
            return {"error": str(e)}

    async def find_route_42(self) -> Optional[GMBRoute]:
        """查找42號小巴路線"""
        # 在各個地區搜索42號路線
        for region in ["nt", "kln", "hk"]:
            data = await self._make_request(f"/route/{region}")
            if "error" not in data and data.get("data"):
                for route_data in data["data"]:
                    if route_data.get("route") == "42":
                        return GMBRoute(
                            route_id=route_data["route_id"],
                            route=route_data["route"],
                            region=region,
                            orig_tc=route_data["orig_tc"],
                            dest_tc=route_data["dest_tc"],
                        )
        return None

    async def find_routes_by_location(self, location: str) -> List[GMBRoute]:
        """根據地名查找相關路線"""
        matching_routes = []

        # 在各個地區搜索包含指定地名的路線
        for region in ["nt", "kln", "hk"]:
            data = await self._make_request(f"/route/{region}")
            if "error" not in data and data.get("data"):
                for route_data in data["data"]:
                    # 處理不同格式的數據
                    if isinstance(route_data, dict):
                        # 標準格式
                        route_id = route_data.get(
                            "route_id", f"{region.upper()}{route_data.get('route', '')}"
                        )
                        route_num = route_data.get("route", "")
                        orig_tc = route_data.get("orig_tc", "")
                        dest_tc = route_data.get("dest_tc", "")
                    else:
                        # 可能是字符串或其他格式，跳過
                        continue

                    # 檢查起點或終點是否包含指定地名
                    if (
                        location.lower() in orig_tc.lower()
                        or location.lower() in dest_tc.lower()
                    ):
                        route = GMBRoute(
                            route_id=route_id,
                            route=route_num,
                            region=region,
                            orig_tc=orig_tc,
                            dest_tc=dest_tc,
                        )
                        matching_routes.append(route)

        return matching_routes

    async def find_ching_tsuen_wai_routes(self) -> List[GMBRoute]:
        """查找青磚圍相關路線"""
        return await self.find_routes_by_location("青磚圍")

    async def get_route_stops(self, route_id: str, route_seq: int = 1) -> List[GMBStop]:
        """獲取路線站點"""
        data = await self._make_request(f"/route - stop/{route_id}/{route_seq}")
        if "error" in data or not data.get("data"):
            return []

        stops = []
        for stop_data in data["data"]:
            stop = GMBStop(
                stop_id=stop_data["stop_id"],
                stop_seq=stop_data["stop_seq"],
                name_tc=stop_data["name_tc"],
                name_en=stop_data["name_en"],
                lat=stop_data["lat"],
                long=stop_data["long"],
            )
            stops.append(stop)

        return stops

    async def get_stop_eta(
        self, route_id: str, route_seq: int = 1, stop_seq: int = 1
    ) -> List[GMBETA]:
        """獲取指定站點的ETA信息"""
        data = await self._make_request(
            f"/eta / route - stop/{route_id}/{route_seq}/{stop_seq}"
        )
        if "error" in data or not data.get("data"):
            return []

        etas = []
        for eta_data in data["data"]:
            eta = GMBETA(
                eta=eta_data["eta"],
                minutes=eta_data["minutes"],
                rmk_tc=eta_data["rmk_tc"],
                rmk_en=eta_data["rmk_en"],
            )
            etas.append(eta)

        return etas

    async def get_route_42_complete(self) -> Optional[Dict[str, Any]]:
        """獲取42號小巴第1站和第10站ETA信息 - 使用真實API"""
        # 使用真實的Route ID: 2001012
        route_id = "2001012"

        try:
            # 步驟1: 獲取路線詳細信息
            route_info = await self._make_request("/route / NT / 42")
            if not route_info.get("data"):
                return {"error": "無法獲取42號小巴路線信息"}

            route_data = route_info["data"][0]
            direction1 = route_data["directions"][0]  # 第一個方向

            # 創建路線對象
            route = GMBRoute(
                route_id=route_id,
                route="42",
                region="nt",
                orig_tc=direction1["orig_tc"],  # 青磚圍
                dest_tc=direction1["dest_tc"],  # 屯門市中心(循環線)
            )

            # 步驟2: 獲取第1站（青磚圍）的ETA
            stop1_etas = []
            try:
                eta_data = await self._make_request(f"/eta / route - stop/{route_id}/1 / 1")
                if eta_data.get("data", {}).get("eta"):
                    for eta_item in eta_data["data"]["eta"]:
                        eta = GMBETA(
                            eta=eta_item["timestamp"],
                            minutes=eta_item["diff"],
                            rmk_tc=eta_item.get("remarks_tc", ""),
                            rmk_en=eta_item.get("remarks_en", ""),
                        )
                        stop1_etas.append(eta)
            except Exception as e:
                logger.warning(f"無法獲取第1站 ETA: {e}")

            # 步驟3: 獲取第10站（屯門市廣場）的ETA
            stop10_etas = []
            try:
                eta_data = await self._make_request(f"/eta / route - stop/{route_id}/1 / 10")
                if eta_data.get("data", {}).get("eta"):
                    for eta_item in eta_data["data"]["eta"]:
                        eta = GMBETA(
                            eta=eta_item["timestamp"],
                            minutes=eta_item["diff"],
                            rmk_tc=eta_item.get("remarks_tc", ""),
                            rmk_en=eta_item.get("remarks_en", ""),
                        )
                        stop10_etas.append(eta)
            except Exception as e:
                logger.warning(f"無法獲取第10站 ETA: {e}")

            return {
                "route": route,
                "stop1": {
                    "name": "青磚圍",
                    "name_en": "Tsing Chuen Wai",
                    "stop_seq": 1,
                    "etas": stop1_etas,
                },
                "stop10": {
                    "name": "屯門市廣場第4座外",
                    "name_en": "Tuen Shun Street, outside Block 4 of Tuen Mun Town Plaza",
                    "stop_seq": 10,
                    "etas": stop10_etas,
                },
                "success": True,
            }

        except Exception as e:
            logger.error(f"獲取42號小巴ETA信息時出錯: {e}")
            return {"error": f"獲取信息失敗: {str(e)}"}

    async def get_route_42_eta(self, stop_seq: int = 1) -> Optional[Dict[str, Any]]:
        """保留原有功能，兼容性"""
        return await self.get_route_42_complete()

    def format_eta_text(self, etas: List[GMBETA], stop_name: str = "") -> str:
        """格式化ETA信息為Telegram友好文本"""
        if not etas:
            return f"{stop_name}\n暫無到站時間信息"

        text = f"{stop_name} 專線小巴到站時間\n\n"

        for eta in etas[:5]:  # 最多顯示5班車
            try:
                # 解析時間
                eta_time = datetime.strptime(eta.eta, "%Y-%m-%d %H:%M:%S")
                time_str = eta_time.strftime("%H:%M")
                text += f"時間: {time_str} ({eta.minutes}分鐘後)"

                # 添加備註
                if eta.rmk_tc and eta.rmk_tc != "預定班次":
                    text += f" - {eta.rmk_tc}"

                text += "\n"
            except ValueError:
                text += f"時間: {eta.eta}\n"

        # 添加更新時間
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text += f"\n更新時間: {update_time}\n"
        text += "數據來源: 香港運輸署"

        return text

    def format_route_42_text(self, result: Dict[str, Any]) -> str:
        """格式化42號小巴簡化ETA信息"""
        if "error" in result:
            return f"[ERROR] {result['error']}"

        stop1 = result.get("stop1", {})
        stop10 = result.get("stop10", {})

        text = "青磚圍\n"
        text += "到站時間: "

        etas1 = stop1.get("etas", [])
        if etas1:
            times = []
            for eta in etas1[:3]:
                try:
                    eta_time = datetime.strptime(eta.eta, "%Y-%m-%dT % H:%M:%S.%f + 08:00")
                    time_str = eta_time.strftime("%H:%M")
                    times.append(time_str)
                except ValueError:
                    times.append(eta.eta)
            text += ", ".join(times)
        else:
            text += "暫無班次"

        text += "\n\n屯門市廣場\n"
        text += "到站時間: "

        etas10 = stop10.get("etas", [])
        if etas10:
            times = []
            for eta in etas10[:3]:
                try:
                    eta_time = datetime.strptime(eta.eta, "%Y-%m-%dT % H:%M:%S.%f + 08:00")
                    time_str = eta_time.strftime("%H:%M")
                    times.append(time_str)
                except ValueError:
                    times.append(eta.eta)
            text += ", ".join(times)
        else:
            text += "暫無班次"

        return text


# 全局適配器實例
_gmb_adapter: Optional[GMBETAAdapter] = None


def get_gmb_adapter() -> GMBETAAdapter:
    """獲取全局GMB適配器實例"""
    global _gmb_adapter
    if _gmb_adapter is None:
        _gmb_adapter = GMBETAAdapter()
    return _gmb_adapter


async def cleanup_gmb_adapter():
    """清理GMB適配器資源"""
    global _gmb_adapter
    if _gmb_adapter:
        await _gmb_adapter.close()
        _gmb_adapter = None


# 測試函數
async def test_gmb_api():
    """測試GMB API功能"""
    adapter = get_gmb_adapter()

    try:
        # 測試獲取地區
        regions = await adapter.get_regions()
        print(f"地區列表: {regions}")

        if regions:
            # 測試獲取某個地區的路線
            first_region = regions[0]
            routes = await adapter.get_routes_by_region(first_region)
            print(f"地區 {first_region} 的路線: {len(routes)} 條")

            if routes:
                # 測試獲取某條路線的站點
                first_route = routes[0]
                stops = await adapter.get_route_stops(first_route.route, first_region)
                print(f"路線 {first_route.route} 的站點: {len(stops)} 個")

                if stops:
                    # 測試獲取某個站點的ETA
                    first_stop = stops[0]
                    etas = await adapter.get_stop_eta(first_stop.stop)
                    print(f"站點 {first_stop.stop} 的ETA: {len(etas)} 條")

                    # 格式化輸出
                    eta_text = adapter.format_eta_text(etas, first_stop.name_tc)
                    print(eta_text)

    finally:
        await adapter.close()


if __name__ == "__main__":
    # 運行測試
    asyncio.run(test_gmb_api())
