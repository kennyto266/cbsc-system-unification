"""
上下文API模块 - 提供上下文CRUD相关接口
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from services.context_service import ContextService
from config.database import get_database_session
from models.context import Context

router = APIRouter()

# 初始化上下文服务
try:
    context_service = ContextService()
    print("ContextService initialized successfully")
except Exception as e:
    print(f"Failed to initialize ContextService: {e}")
    import traceback
    traceback.print_exc()
    context_service = None

# Pydantic models for request/response
class ContextCreate(BaseModel):
    """创建上下文的请求模型"""
    title: str = Field(..., min_length=1, max_length=255, description="上下文标题")
    content: Dict[str, Any] = Field(..., description="上下文内容")
    description: Optional[str] = Field(None, max_length=1000, description="上下文描述")
    tags: Optional[List[str]] = Field(default=[], description="标签列表")
    session_id: Optional[str] = Field(None, max_length=100, description="会话ID")
    project_path: Optional[str] = Field(None, max_length=500, description="项目路径")
    visibility: Optional[str] = Field("private", pattern="^(private|team|public)$", description="可见性")
    auto_save_enabled: Optional[bool] = Field(True, description="是否启用自动保存")
    user_id: str = Field(..., max_length=100, description="用户ID")

class ContextUpdate(BaseModel):
    """更新上下文的请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="新标题")
    content: Optional[Dict[str, Any]] = Field(None, description="新内容")
    description: Optional[str] = Field(None, max_length=1000, description="新描述")
    tags: Optional[List[str]] = Field(None, description="新标签列表")

class ContextResponse(BaseModel):
    """上下文响应模型"""
    id: str
    title: str
    description: Optional[str]
    content: Dict[str, Any]
    metadata: Dict[str, Any]

class ContextListResponse(BaseModel):
    """上下文列表响应模型"""
    id: str
    title: str
    description: Optional[str]
    metadata: Dict[str, Any]

@router.post("/test")
async def test_endpoint():
    """测试端点"""
    return {"message": "Test endpoint works", "status": 201}

@router.post("/contexts", response_model=Dict[str, Any], status_code=201)
async def create_context(request: ContextCreate):
    """创建新的上下文"""
    try:
        # 检查服务是否初始化
        if context_service is None:
            raise HTTPException(status_code=500, detail="Context服务未初始化")

        # 调用服务层创建上下文
        context_id = await context_service.save_context(
            title=request.title,
            content=request.content,
            user_id=request.user_id,
            description=request.description,
            tags=request.tags,
            session_id=request.session_id,
            project_path=request.project_path,
            visibility=request.visibility,
            auto_save_enabled=request.auto_save_enabled
        )

        if not context_id:
            raise HTTPException(status_code=500, detail="创建上下文失败")

        return {
            "success": True,
            "data": {
                "id": context_id,
                "title": request.title,
                "message": "上下文创建成功"
            },
            "message": "上下文创建成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error creating context: {str(e)}\nTraceback:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"创建上下文失败: {str(e)}")

@router.get("/contexts/{context_id}", response_model=ContextResponse)
async def get_context(
    context_id: str,
    user_id: Optional[str] = Query(None, description="用户ID（用于权限检查）")
):
    """获取指定上下文"""
    try:
        context_data = await context_service.load_context(
            context_id=context_id,
            user_id=user_id
        )

        if not context_data:
            raise HTTPException(status_code=404, detail="上下文不存在或无权访问")

        return ContextResponse(**context_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取上下文失败: {str(e)}")

@router.put("/contexts/{context_id}", response_model=Dict[str, Any])
async def update_context(
    context_id: str,
    request: ContextUpdate,
    user_id: Optional[str] = Query(None, description="用户ID（用于权限检查）")
):
    """更新指定上下文"""
    try:
        # 检查是否有要更新的字段
        if all(field is None for field in [request.title, request.content, request.description, request.tags]):
            raise HTTPException(status_code=400, detail="没有提供要更新的字段")

        success = await context_service.update_context(
            context_id=context_id,
            content=request.content,
            title=request.title,
            description=request.description,
            tags=request.tags,
            user_id=user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="上下文不存在或无权更新")

        return {
            "success": True,
            "data": {
                "id": context_id,
                "message": "上下文更新成功"
            },
            "message": "上下文更新成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新上下文失败: {str(e)}")

@router.delete("/contexts/{context_id}", response_model=Dict[str, Any])
async def delete_context(
    context_id: str,
    user_id: Optional[str] = Query(None, description="用户ID（用于权限检查）")
):
    """删除指定上下文"""
    try:
        success = await context_service.delete_context(
            context_id=context_id,
            user_id=user_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="上下文不存在或无权删除")

        return {
            "success": True,
            "data": {
                "id": context_id,
                "message": "上下文删除成功"
            },
            "message": "上下文删除成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除上下文失败: {str(e)}")

@router.get("/contexts", response_model=List[ContextListResponse])
async def list_contexts(
    user_id: Optional[str] = Query(None, description="用户ID"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    project_path: Optional[str] = Query(None, description="项目路径"),
    tags: Optional[List[str]] = Query(None, description="标签过滤"),
    limit: int = Query(50, ge=1, le=100, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="结果偏移量")
):
    """列出上下文"""
    try:
        contexts = await context_service.list_contexts(
            user_id=user_id,
            session_id=session_id,
            project_path=project_path,
            tags=tags,
            limit=limit,
            offset=offset
        )

        return [ContextListResponse(**context) for context in contexts]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出上下文失败: {str(e)}")

# Enhanced search request model
class AdvancedSearchRequest(BaseModel):
    """高级搜索请求模型"""
    query: Optional[str] = Field(None, description="全文搜索查询字符串")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    user_id: Optional[str] = Field(None, description="用户ID过滤")
    session_id: Optional[str] = Field(None, description="会话ID过滤")
    project_path: Optional[str] = Field(None, description="项目路径过滤")
    visibility: Optional[str] = Field(None, pattern="^(private|team|public)$", description="可见性过滤")
    date_from: Optional[str] = Field(None, description="开始日期 (ISO格式)")
    date_to: Optional[str] = Field(None, description="结束日期 (ISO格式)")
    content_type: Optional[str] = Field(None, description="内容类型过滤")
    file_size_min: Optional[int] = Field(None, ge=0, description="最小文件大小")
    file_size_max: Optional[int] = Field(None, ge=0, description="最大文件大小")
    sort_by: Optional[str] = Field("created_at", pattern="^(created_at|updated_at|title|file_size)$", description="排序字段")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="排序方向")
    limit: int = Field(10, ge=1, le=100, description="结果数量限制")
    offset: int = Field(0, ge=0, description="结果偏移量")

@router.get("/contexts/search", response_model=List[Dict[str, Any]])
async def search_contexts(
    q: str = Query(..., min_length=1, description="搜索查询字符串"),
    user_id: Optional[str] = Query(None, description="用户ID（用于权限过滤）"),
    tags: Optional[List[str]] = Query(None, description="标签过滤"),
    session_id: Optional[str] = Query(None, description="会话ID过滤"),
    project_path: Optional[str] = Query(None, description="项目路径过滤"),
    visibility: Optional[str] = Query(None, pattern="^(private|team|public)$", description="可见性过滤"),
    date_from: Optional[str] = Query(None, description="开始日期过滤 (ISO格式)"),
    date_to: Optional[str] = Query(None, description="结束日期过滤 (ISO格式)"),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|title|file_size)$", description="排序字段"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    limit: int = Query(10, ge=1, le=50, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="结果偏移量")
):
    """搜索上下文（支持高级过滤）"""
    try:
        # 使用高级搜索逻辑
        search_filters = {
            "query": q,
            "user_id": user_id,
            "tags": tags,
            "session_id": session_id,
            "project_path": project_path,
            "visibility": visibility,
            "date_from": date_from,
            "date_to": date_to,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "offset": offset
        }

        results = await context_service.search_contexts_advanced(**search_filters)
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索上下文失败: {str(e)}")

@router.post("/contexts/search/advanced", response_model=List[Dict[str, Any]])
async def search_contexts_advanced(request: AdvancedSearchRequest):
    """高级搜索上下文（POST方法，支持复杂查询）"""
    try:
        search_filters = request.dict(exclude_none=True)
        results = await context_service.search_contexts_advanced(**search_filters)
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"高级搜索上下文失败: {str(e)}")

@router.get("/contexts/search/tags/{tag}", response_model=List[Dict[str, Any]])
async def search_contexts_by_tag(
    tag: str,
    user_id: Optional[str] = Query(None, description="用户ID（用于权限过滤）"),
    limit: int = Query(10, ge=1, le=50, description="结果数量限制"),
    offset: int = Query(0, ge=0, description="结果偏移量")
):
    """按标签搜索上下文"""
    try:
        # 使用搜索服务的标签搜索功能
        search_results = await context_service.search_service.search_by_tag(
            tag=tag,
            limit=limit,
            offset=offset
        )

        # 权限过滤
        filtered_results = []
        with get_database_session() as db:
            for result in search_results:
                context_id = result['id']
                context = db.query(Context).filter(Context.id == context_id).first()

                if context:
                    # 权限检查
                    if not user_id or context.user_id == user_id or context.visibility != "private":
                        filtered_result = {
                            "id": context.id,
                            "title": context.title,
                            "description": context.description,
                            "content_preview": result.get('content', '')[:200] + '...' if len(result.get('content', '')) > 200 else result.get('content', ''),
                            "score": result['score'],
                            "metadata": {
                                "user_id": context.user_id,
                                "session_id": context.session_id,
                                "project_path": context.project_path,
                                "visibility": context.visibility,
                                "file_size": context.file_size,
                                "original_size": context.original_size,
                                "compression_ratio": context.compression_ratio,
                                "created_at": context.created_at.isoformat() if context.created_at else None,
                                "updated_at": context.updated_at.isoformat() if context.updated_at else None,
                                "tags": [tag_obj.tag_name for tag_obj in context.tags] if context.tags else []
                            }
                        }
                        filtered_results.append(filtered_result)

        return filtered_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"按标签搜索上下文失败: {str(e)}")

@router.get("/contexts/search/suggestions", response_model=List[Dict[str, Any]])
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="查询前缀"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    limit: int = Query(5, ge=1, le=20, description="建议数量限制")
):
    """获取搜索建议（基于标题和标签）"""
    try:
        suggestions = await context_service.get_search_suggestions(
            query_prefix=q,
            user_id=user_id,
            limit=limit
        )
        return suggestions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取搜索建议失败: {str(e)}")

@router.get("/contexts/filters/tags", response_model=List[Dict[str, Any]])
async def get_available_tags(
    user_id: Optional[str] = Query(None, description="用户ID（用于权限过滤）"),
    limit: int = Query(50, ge=1, le=200, description="标签数量限制")
):
    """获取可用的标签列表（按使用频率排序）"""
    try:
        tags = await context_service.get_popular_tags(
            user_id=user_id,
            limit=limit
        )
        return tags

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取标签列表失败: {str(e)}")

@router.get("/contexts/filters/projects", response_model=List[Dict[str, Any]])
async def get_available_projects(
    user_id: Optional[str] = Query(None, description="用户ID（用于权限过滤）"),
    limit: int = Query(50, ge=1, le=200, description="项目数量限制")
):
    """获取可用的项目路径列表"""
    try:
        projects = await context_service.get_available_projects(
            user_id=user_id,
            limit=limit
        )
        return projects

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")

@router.get("/contexts/filters/sessions", response_model=List[Dict[str, Any]])
async def get_available_sessions(
    user_id: Optional[str] = Query(None, description="用户ID（用于权限过滤）"),
    limit: int = Query(50, ge=1, le=200, description="会话数量限制")
):
    """获取可用的会话ID列表"""
    try:
        sessions = await context_service.get_available_sessions(
            user_id=user_id,
            limit=limit
        )
        return sessions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")

@router.get("/contexts/stats", response_model=Dict[str, Any])
async def get_context_stats(
    user_id: Optional[str] = Query(None, description="用户ID（可选）")
):
    """获取上下文统计信息"""
    try:
        stats = await context_service.get_context_stats(user_id=user_id)

        return {
            "success": True,
            "data": stats,
            "message": "获取统计信息成功",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")