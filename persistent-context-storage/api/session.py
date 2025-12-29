"""
会话管理API模块 - 提供会话恢复和自动保存管理接口
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from services.context_service import ContextService
from services.scheduler_service import SchedulerService
from config.database import get_database_session
from models.context import Context

router = APIRouter()

# 初始化服务
try:
    context_service = ContextService()
    scheduler_service = SchedulerService(context_service)
    scheduler_service.start()  # 启动调度服务
    print("Session management services initialized successfully")
except Exception as e:
    print(f"Failed to initialize session management services: {e}")
    import traceback
    traceback.print_exc()
    context_service = None
    scheduler_service = None

# Pydantic models for request/response
class AutoSaveRequest(BaseModel):
    """自动保存请求模型"""
    title: str = Field(..., min_length=1, max_length=255, description="上下文标题")
    content: Dict[str, Any] = Field(..., description="上下文内容")
    description: Optional[str] = Field(None, max_length=1000, description="上下文描述")
    tags: Optional[List[str]] = Field(default=[], description="标签列表")
    project_path: Optional[str] = Field(None, max_length=500, description="项目路径")
    user_id: str = Field(..., max_length=100, description="用户ID")
    interval_minutes: int = Field(5, ge=1, le=60, description="自动保存间隔（分钟）")

class AutoSaveUpdateRequest(BaseModel):
    """自动保存更新请求模型"""
    content: Optional[Dict[str, Any]] = Field(None, description="更新的上下文内容")
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="更新的标题")
    description: Optional[str] = Field(None, max_length=1000, description="更新的描述")
    tags: Optional[List[str]] = Field(None, description="更新的标签列表")

class SessionResumeResponse(BaseModel):
    """会话恢复响应模型"""
    session_id: str
    contexts: List[Dict[str, Any]]
    total_contexts: int
    latest_context: Optional[Dict[str, Any]]
    session_metadata: Dict[str, Any]

class SessionStatusResponse(BaseModel):
    """会话状态响应模型"""
    session_id: str
    has_auto_save: bool
    next_save_time: Optional[str]
    pending_data: bool
    total_contexts: int
    latest_save: Optional[str]
    auto_save_enabled: bool

class SessionListResponse(BaseModel):
    """会话列表响应模型"""
    session_id: str
    user_id: str
    project_path: Optional[str]
    total_contexts: int
    latest_activity: Optional[str]
    has_auto_save: bool
    auto_save_enabled: bool

@router.get("/sessions/{session_id}/resume", response_model=SessionResumeResponse)
async def resume_session(
    session_id: str,
    user_id: Optional[str] = Query(None, description="用户ID（用于权限检查）"),
    include_content: bool = Query(True, description="是否包含完整上下文内容")
):
    """恢复指定会话的完整上下文历史"""
    try:
        if not context_service:
            raise HTTPException(status_code=500, detail="上下文服务未初始化")

        # 获取会话的所有上下文
        contexts = await context_service.list_contexts(
            session_id=session_id,
            user_id=user_id,
            limit=1000  # 获取大量历史记录
        )

        if not contexts:
            raise HTTPException(status_code=404, detail="会话不存在或无权访问")

        # 如果不需要完整内容，只保留元数据
        if not include_content:
            for context in contexts:
                context['metadata']['content_preview'] = str(context.get('content', {}))[:200] + '...'
                context.pop('content', None)

        # 获取最新上下文
        latest_context = max(contexts, key=lambda x: x.get('metadata', {}).get('updated_at', '')) if contexts else None

        # 生成会话元数据
        session_metadata = {
            'created_at': min(ctx.get('metadata', {}).get('created_at', '') for ctx in contexts) if contexts else None,
            'updated_at': max(ctx.get('metadata', {}).get('updated_at', '') for ctx in contexts) if contexts else None,
            'total_contexts': len(contexts),
            'tags': list(set(tag for ctx in contexts for tag in ctx.get('metadata', {}).get('tags', []))),
            'project_paths': list(set(ctx.get('metadata', {}).get('project_path') for ctx in contexts if ctx.get('metadata', {}).get('project_path'))),
            'auto_save_enabled': any(ctx.get('metadata', {}).get('auto_save_enabled', False) for ctx in contexts)
        }

        return SessionResumeResponse(
            session_id=session_id,
            contexts=contexts,
            total_contexts=len(contexts),
            latest_context=latest_context,
            session_metadata=session_metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复会话失败: {str(e)}")

@router.post("/sessions/{session_id}/auto-save", response_model=Dict[str, Any])
async def setup_auto_save(
    session_id: str,
    request: AutoSaveRequest
):
    """为指定会话设置自动保存"""
    try:
        if not scheduler_service:
            raise HTTPException(status_code=500, detail="调度服务未初始化")

        # 构建上下文数据
        context_data = {
            'title': request.title,
            'content': request.content,
            'user_id': request.user_id,
            'description': request.description,
            'tags': request.tags,
            'project_path': request.project_path,
            'session_id': session_id,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # 安排自动保存任务
        success = scheduler_service.schedule_auto_save(
            session_id=session_id,
            context_data=context_data,
            interval_minutes=request.interval_minutes
        )

        if not success:
            raise HTTPException(status_code=500, detail="设置自动保存失败")

        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "auto_save_enabled": True,
                "interval_minutes": request.interval_minutes,
                "message": "自动保存设置成功"
            },
            "message": "自动保存设置成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置自动保存失败: {str(e)}")

@router.put("/sessions/{session_id}/auto-save", response_model=Dict[str, Any])
async def update_auto_save_data(
    session_id: str,
    request: AutoSaveUpdateRequest,
    user_id: Optional[str] = Query(None, description="用户ID")
):
    """更新会话的自动保存数据"""
    try:
        if not scheduler_service:
            raise HTTPException(status_code=500, detail="调度服务未初始化")

        # 构建更新数据
        update_data = {}
        if request.content is not None:
            update_data['content'] = request.content
        if request.title is not None:
            update_data['title'] = request.title
        if request.description is not None:
            update_data['description'] = request.description
        if request.tags is not None:
            update_data['tags'] = request.tags
        if user_id:
            update_data['user_id'] = user_id

        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供要更新的数据")

        # 更新待保存的上下文数据
        success = scheduler_service.update_pending_context(session_id, update_data)

        if not success:
            raise HTTPException(status_code=404, detail="会话没有设置自动保存或更新失败")

        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "updated_fields": list(update_data.keys()),
                "message": "自动保存数据更新成功"
            },
            "message": "自动保存数据更新成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新自动保存数据失败: {str(e)}")

@router.delete("/sessions/{session_id}/auto-save", response_model=Dict[str, Any])
async def cancel_auto_save(session_id: str):
    """取消会话的自动保存"""
    try:
        if not scheduler_service:
            raise HTTPException(status_code=500, detail="调度服务未初始化")

        success = scheduler_service.cancel_auto_save(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="会话没有设置自动保存")

        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "auto_save_enabled": False,
                "message": "自动保存已取消"
            },
            "message": "自动保存已取消",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消自动保存失败: {str(e)}")

@router.get("/sessions/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: str,
    user_id: Optional[str] = Query(None, description="用户ID（用于权限检查）")
):
    """获取会话状态信息"""
    try:
        if not context_service or not scheduler_service:
            raise HTTPException(status_code=500, detail="服务未初始化")

        # 获取会话的上下文数量
        contexts = await context_service.list_contexts(
            session_id=session_id,
            user_id=user_id,
            limit=1
        )
        total_contexts = len(contexts) if contexts else 0

        # 获取调度任务信息
        jobs_info = scheduler_service.get_scheduled_jobs()
        session_job = jobs_info.get(session_id, {})

        # 获取最新上下文信息
        latest_contexts = await context_service.list_contexts(
            session_id=session_id,
            user_id=user_id,
            limit=1,
            sort_by="updated_at",
            sort_order="desc"
        )

        latest_save = None
        auto_save_enabled = False
        if latest_contexts:
            latest_save = latest_contexts[0].get('metadata', {}).get('updated_at')
            auto_save_enabled = latest_contexts[0].get('metadata', {}).get('auto_save_enabled', False)

        return SessionStatusResponse(
            session_id=session_id,
            has_auto_save=bool(session_job),
            next_save_time=session_job.get('next_run'),
            pending_data=session_job.get('has_pending_data', False),
            total_contexts=total_contexts,
            latest_save=latest_save,
            auto_save_enabled=auto_save_enabled
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话状态失败: {str(e)}")

@router.post("/sessions/{session_id}/force-save", response_model=Dict[str, Any])
async def force_save_session(session_id: str):
    """立即执行会话的自动保存"""
    try:
        if not scheduler_service:
            raise HTTPException(status_code=500, detail="调度服务未初始化")

        success = scheduler_service.force_save_now(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="会话没有待保存的数据")

        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "message": "强制保存执行成功"
            },
            "message": "强制保存执行成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"强制保存失败: {str(e)}")

@router.get("/sessions", response_model=List[SessionListResponse])
async def list_sessions(
    user_id: Optional[str] = Query(None, description="用户ID（用于权限过滤）"),
    project_path: Optional[str] = Query(None, description="项目路径过滤"),
    has_auto_save: Optional[bool] = Query(None, description="是否只显示有自动保存的会话"),
    limit: int = Query(50, ge=1, le=200, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="结果偏移量")
):
    """获取会话列表"""
    try:
        if not context_service or not scheduler_service:
            raise HTTPException(status_code=500, detail="服务未初始化")

        # 获取所有上下文（用于统计会话信息）
        all_contexts = await context_service.list_contexts(
            user_id=user_id,
            project_path=project_path,
            limit=10000  # 获取大量数据用于统计
        )

        # 按会话ID分组
        session_groups = {}
        for context in all_contexts:
            session_id = context.get('metadata', {}).get('session_id')
            if not session_id:
                continue

            if session_id not in session_groups:
                session_groups[session_id] = {
                    'session_id': session_id,
                    'contexts': [],
                    'user_id': context.get('metadata', {}).get('user_id'),
                    'project_path': context.get('metadata', {}).get('project_path'),
                    'auto_save_enabled': False
                }

            session_groups[session_id]['contexts'].append(context)

            # 检查是否有自动保存
            if context.get('metadata', {}).get('auto_save_enabled', False):
                session_groups[session_id]['auto_save_enabled'] = True

        # 获取调度任务信息
        jobs_info = scheduler_service.get_scheduled_jobs()

        # 构建响应列表
        sessions = []
        for session_id, group in session_groups.items():
            contexts = group['contexts']
            if not contexts:
                continue

            # 过滤条件
            if has_auto_save is not None and group['auto_save_enabled'] != has_auto_save:
                continue

            # 获取最新活动时间
            latest_activity = max(
                ctx.get('metadata', {}).get('updated_at', '') for ctx in contexts
            )

            sessions.append(SessionListResponse(
                session_id=session_id,
                user_id=group['user_id'],
                project_path=group['project_path'],
                total_contexts=len(contexts),
                latest_activity=latest_activity,
                has_auto_save=session_id in jobs_info,
                auto_save_enabled=group['auto_save_enabled']
            ))

        # 排序和分页
        sessions.sort(key=lambda x: x.latest_activity or '', reverse=True)
        paginated_sessions = sessions[offset:offset + limit]

        return paginated_sessions

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")

@router.get("/scheduler/status", response_model=Dict[str, Any])
async def get_scheduler_status():
    """获取调度服务状态"""
    try:
        if not scheduler_service:
            raise HTTPException(status_code=500, detail="调度服务未初始化")

        status = scheduler_service.get_status()
        jobs_info = scheduler_service.get_scheduled_jobs()

        return {
            "success": True,
            "data": {
                "scheduler_status": status,
                "active_jobs": jobs_info,
                "total_active_sessions": len(jobs_info)
            },
            "message": "获取调度状态成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取调度状态失败: {str(e)}")

@router.post("/scheduler/cleanup", response_model=Dict[str, Any])
async def cleanup_expired_sessions(hours: int = Query(24, ge=1, le=168, description="过期时间（小时）")):
    """清理过期的会话"""
    try:
        if not scheduler_service:
            raise HTTPException(status_code=500, detail="调度服务未初始化")

        cleaned_count = scheduler_service.cleanup_expired_sessions(hours=hours)

        return {
            "success": True,
            "data": {
                "cleaned_sessions": cleaned_count,
                "cleanup_hours": hours,
                "message": f"清理了 {cleaned_count} 个过期会话"
            },
            "message": "清理过期会话成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理过期会话失败: {str(e)}")