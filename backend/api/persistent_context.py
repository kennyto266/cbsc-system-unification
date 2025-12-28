"""
持久化上下文API模块 - 提供上下文存储和检索相关接口
Persistent Context API Module - Provides context storage and retrieval endpoints
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# 持久化上下文存储服务配置
PERSISTENT_CONTEXT_SERVICE_URL = "http://localhost:3007"

async def get_service_client():
    """获取HTTP客户端"""
    try:
        return httpx.AsyncClient(timeout=30.0)
    except Exception as e:
        logger.error(f"创建HTTP客户端失败: {e}")
        raise HTTPException(status_code=500, detail="服务连接失败")

def handle_service_error(response):
    """处理服务响应错误"""
    if response.status_code >= 400:
        error_msg = f"服务请求失败: {response.status_code}"
        try:
            error_data = response.json()
            if "detail" in error_data:
                error_msg = error_data["detail"]
            elif "message" in error_data:
                error_msg = error_data["message"]
        except:
            pass

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=error_msg)
        elif response.status_code == 400:
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=response.status_code, detail=error_msg)

# ==================== 上下文管理 API ====================

@router.post("/contexts")
async def create_context(request: Dict[str, Any]):
    """创建上下文"""
    async with await get_service_client() as client:
        try:
            response = await client.post(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/contexts",
                json=request
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "上下文创建成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"创建上下文请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.get("/contexts")
async def get_contexts(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    project_path: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """获取上下文列表"""
    params = {
        "limit": limit,
        "offset": offset
    }
    if user_id:
        params["user_id"] = user_id
    if session_id:
        params["session_id"] = session_id
    if project_path:
        params["project_path"] = project_path

    async with await get_service_client() as client:
        try:
            response = await client.get(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/contexts",
                params=params
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "上下文列表获取成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"获取上下文列表请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.get("/contexts/{context_id}")
async def get_context(context_id: str):
    """获取上下文详情"""
    async with await get_service_client() as client:
        try:
            response = await client.get(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/contexts/{context_id}"
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "上下文详情获取成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"获取上下文详情请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.put("/contexts/{context_id}")
async def update_context(context_id: str, request: Dict[str, Any]):
    """更新上下文"""
    async with await get_service_client() as client:
        try:
            response = await client.put(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/contexts/{context_id}",
                json=request
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "上下文更新成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"更新上下文请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.delete("/contexts/{context_id}")
async def delete_context(context_id: str):
    """删除上下文"""
    async with await get_service_client() as client:
        try:
            response = await client.delete(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/contexts/{context_id}"
            )
            handle_service_error(response)

            return {
                "success": True,
                "message": "上下文删除成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"删除上下文请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.get("/contexts/stats")
async def get_context_stats():
    """获取上下文统计信息"""
    async with await get_service_client() as client:
        try:
            response = await client.get(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/contexts/stats"
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "上下文统计信息获取成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"获取上下文统计信息请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

# ==================== 搜索 API ====================

@router.get("/contexts/search")
async def search_contexts(
    query: Optional[str] = None,
    tags: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    project_path: Optional[str] = None,
    visibility: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0
):
    """搜索上下文"""
    params = {
        "sort_by": sort_by,
        "sort_order": sort_order,
        "limit": limit,
        "offset": offset
    }

    if query:
        params["query"] = query
    if tags:
        params["tags"] = tags
    if user_id:
        params["user_id"] = user_id
    if session_id:
        params["session_id"] = session_id
    if project_path:
        params["project_path"] = project_path
    if visibility:
        params["visibility"] = visibility
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    async with await get_service_client() as client:
        try:
            response = await client.get(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/contexts/search",
                params=params
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "上下文搜索成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"搜索上下文请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.post("/contexts/search/advanced")
async def search_contexts_advanced(request: Dict[str, Any]):
    """高级搜索上下文"""
    async with await get_service_client() as client:
        try:
            response = await client.post(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/contexts/search/advanced",
                json=request
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "高级上下文搜索成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"高级搜索上下文请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.get("/contexts/search/tags/{tag}")
async def search_contexts_by_tag(tag: str, limit: int = 50):
    """按标签搜索上下文"""
    async with await get_service_client() as client:
        try:
            response = await client.get(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/contexts/search/tags/{tag}",
                params={"limit": limit}
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": f"标签 '{tag}' 的上下文搜索成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"按标签搜索上下文请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

# ==================== 会话管理 API ====================

@router.post("/sessions")
async def create_session(request: Dict[str, Any]):
    """创建会话"""
    async with await get_service_client() as client:
        try:
            response = await client.post(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/sessions",
                json=request
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "会话创建成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"创建会话请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话详情"""
    async with await get_service_client() as client:
        try:
            response = await client.get(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/sessions/{session_id}"
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "会话详情获取成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"获取会话详情请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.post("/sessions/{session_id}/resume")
async def resume_session(session_id: str, request: Dict[str, Any]):
    """恢复会话"""
    async with await get_service_client() as client:
        try:
            response = await client.post(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/sessions/{session_id}/resume",
                json=request
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "会话恢复成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"恢复会话请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.post("/sessions/{session_id}/save")
async def force_save_session(session_id: str):
    """强制保存会话"""
    async with await get_service_client() as client:
        try:
            response = await client.post(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/sessions/{session_id}/save"
            )
            handle_service_error(response)

            return {
                "success": True,
                "message": "会话强制保存成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"强制保存会话请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

# ==================== 团队协作 API ====================

@router.post("/team/share")
async def share_context(request: Dict[str, Any]):
    """分享上下文"""
    async with await get_service_client() as client:
        try:
            response = await client.post(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/team/share",
                json=request
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "上下文分享成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"分享上下文请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.post("/team/share/link")
async def create_share_link(request: Dict[str, Any]):
    """创建分享链接"""
    async with await get_service_client() as client:
        try:
            response = await client.post(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/team/share/link",
                json=request
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "分享链接创建成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"创建分享链接请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.get("/team/share/access/{share_token}")
async def access_shared_context(share_token: str):
    """通过分享链接访问上下文"""
    async with await get_service_client() as client:
        try:
            response = await client.get(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/team/share/access/{share_token}"
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "通过分享链接访问上下文成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"通过分享链接访问上下文请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.get("/team/shares")
async def get_shared_contexts(
    user_id: Optional[str] = None,
    context_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """获取分享的上下文列表"""
    params = {
        "limit": limit,
        "offset": offset
    }
    if user_id:
        params["user_id"] = user_id
    if context_id:
        params["context_id"] = context_id

    async with await get_service_client() as client:
        try:
            response = await client.get(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/team/shares",
                params=params
            )
            handle_service_error(response)

            data = response.json()
            return {
                "success": True,
                "data": data,
                "message": "分享的上下文列表获取成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"获取分享的上下文列表请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

@router.delete("/team/share/{share_id}")
async def revoke_share(share_id: str):
    """撤销分享"""
    async with await get_service_client() as client:
        try:
            response = await client.delete(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/api/team/share/{share_id}"
            )
            handle_service_error(response)

            return {
                "success": True,
                "message": "分享撤销成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"撤销分享请求失败: {e}")
            raise HTTPException(status_code=503, detail="持久化上下文服务不可用")

# ==================== 健康检查 API ====================

@router.get("/persistent-context/health")
async def health_check():
    """持久化上下文服务健康检查"""
    async with await get_service_client() as client:
        try:
            response = await client.get(
                f"{PERSISTENT_CONTEXT_SERVICE_URL}/health"
            )
            service_data = response.json()

            return {
                "success": True,
                "data": {
                    "backend_status": "healthy",
                    "persistent_context_service": service_data
                },
                "message": "持久化上下文服务健康检查成功",
                "timestamp": datetime.now().isoformat()
            }
        except httpx.RequestError as e:
            logger.error(f"持久化上下文服务健康检查失败: {e}")
            return {
                "success": False,
                "data": {
                    "backend_status": "healthy",
                    "persistent_context_service": {"status": "unhealthy", "error": str(e)}
                },
                "message": "持久化上下文服务不可用",
                "timestamp": datetime.now().isoformat()
            }