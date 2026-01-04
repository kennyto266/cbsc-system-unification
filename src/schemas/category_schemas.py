"""
Category Schemas for API v2
分類API v2的Pydantic模型定義

Pydantic models for category API request/response validation
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


# Category Response Models
class CategoryResponse(BaseModel):
    """分類響應模型"""
    id: UUID = Field(..., description="分類ID")
    name: str = Field(..., description="分類名稱")
    display_name: Optional[str] = Field(None, description="顯示名稱")
    description: Optional[str] = Field(None, description="分類描述")
    parent_id: Optional[UUID] = Field(None, description="父分類ID")
    level: int = Field(..., ge=0, description="分類層級")
    sort_order: int = Field(0, description="排序順序")
    icon: Optional[str] = Field(None, description="圖標名稱")
    color: Optional[str] = Field(None, description="顏色代碼")
    is_active: bool = Field(True, description="是否啟用")
    created_at: datetime = Field(..., description="創建時間")
    updated_at: datetime = Field(..., description="更新時間")
    strategy_count: Optional[int] = Field(None, description="策略數量")
    children: Optional[List['CategoryResponse']] = Field(default_factory=list, description="子分類")

    @classmethod
    def from_model(cls, model):
        """從數據庫模型創建"""
        return cls(
            id=model.id,
            name=model.name,
            display_name=getattr(model, 'display_name', None),
            description=model.description,
            parent_id=model.parent_id,
            level=model.level,
            sort_order=model.sort_order,
            icon=getattr(model, 'icon', None),
            color=getattr(model, 'color', None),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            strategy_count=getattr(model, 'strategy_count', None),
            children=getattr(model, 'children', [])
        )


class CategoryListResponse(BaseModel):
    """分類列表響應模型"""
    categories: List[CategoryResponse] = Field(..., description="分類列表")


class CategoryTreeResponse(BaseModel):
    """分類樹響應模型"""
    id: UUID = Field(..., description="分類ID")
    name: str = Field(..., description="分類名稱")
    display_name: Optional[str] = Field(None, description="顯示名稱")
    description: Optional[str] = Field(None, description="分類描述")
    level: int = Field(..., ge=0, description="分類層級")
    icon: Optional[str] = Field(None, description="圖標名稱")
    color: Optional[str] = Field(None, description="顏色代碼")
    strategy_count: Optional[int] = Field(None, description="策略數量")
    children: List['CategoryTreeResponse'] = Field(default_factory=list, description="子分類")

    class Config:
        from_attributes = True


# Category Request Models
class CategoryCreate(BaseModel):
    """創建分類請求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="分類名稱")
    display_name: Optional[str] = Field(None, max_length=100, description="顯示名稱")
    description: Optional[str] = Field(None, max_length=500, description="分類描述")
    parent_id: Optional[UUID] = Field(None, description="父分類ID")
    level: Optional[int] = Field(None, ge=0, description="分類層級")
    sort_order: int = Field(0, ge=0, description="排序順序")
    icon: Optional[str] = Field(None, max_length=50, description="圖標名稱")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="顏色代碼")
    is_active: bool = Field(True, description="是否啟用")

    @validator('name')
    def validate_name(cls, v):
        """驗證分類名稱"""
        if not v or not v.strip():
            raise ValueError('分類名稱不能為空')
        return v.strip()

    @validator('color')
    def validate_color(cls, v):
        """驗證顏色代碼"""
        if v and not v.startswith('#'):
            v = f'#{v}'
        return v


class CategoryUpdate(BaseModel):
    """更新分類請求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="分類名稱")
    display_name: Optional[str] = Field(None, max_length=100, description="顯示名稱")
    description: Optional[str] = Field(None, max_length=500, description="分類描述")
    parent_id: Optional[UUID] = Field(None, description="父分類ID")
    level: Optional[int] = Field(None, ge=0, description="分類層級")
    sort_order: Optional[int] = Field(None, ge=0, description="排序順序")
    icon: Optional[str] = Field(None, max_length=50, description="圖標名稱")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="顏色代碼")
    is_active: Optional[bool] = Field(None, description="是否啟用")

    @validator('name')
    def validate_name(cls, v):
        """驗證分類名稱"""
        if v is not None and not v.strip():
            raise ValueError('分類名稱不能為空')
        return v.strip() if v else v

    @validator('color')
    def validate_color(cls, v):
        """驗證顏色代碼"""
        if v and not v.startswith('#'):
            v = f'#{v}'
        return v


# Statistics Models
class CategoryStatistics(BaseModel):
    """分類統計模型"""
    total_categories: int = Field(..., description="總分類數")
    active_categories: int = Field(..., description="活躍分類數")
    root_categories: int = Field(..., description="根分類數")
    max_depth: int = Field(..., description="最大深度")
    categories_by_level: Dict[int, int] = Field(default_factory=dict, description="按層級分組")
    categories_with_strategies: int = Field(..., description="有策略的分類數")
    total_strategies: int = Field(..., description="總策略數")
    avg_strategies_per_category: float = Field(..., description="平均每個分類的策略數")


# Validation Models
class CategoryValidationResult(BaseModel):
    """分類驗證結果模型"""
    valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="錯誤列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    suggestions: List[str] = Field(default_factory=list, description="建議列表")


# Forward reference resolution
CategoryTreeResponse.model_rebuild()
CategoryResponse.model_rebuild()