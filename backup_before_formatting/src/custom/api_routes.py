"""
自定义模块 API 路由
提供策略模板、模板管理和策略测试的 REST API
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from .strategy_template import (
    StrategyNode,
    StrategyTemplateEngine,
    TemplateStatus,
    TemplateType,
    TemplateVariable,
    create_predefined_templates,
)
from .strategy_tester import StrategyTester, TestConfig, TestType
from .template_manager import ExportFormat, TemplateManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api / custom", tags=["custom"])

# 全局实例
template_engine = None
template_manager = None
strategy_tester = None


def get_template_engine():
    """获取模板引擎实例"""
    global template_engine
    if template_engine is None:
        template_engine = StrategyTemplateEngine()
        # 创建预定义模板
        create_predefined_templates(template_engine)
    return template_engine


def get_template_manager():
    """获取模板管理器实例"""
    global template_manager
    if template_manager is None:
        template_manager = TemplateManager(get_template_engine())
    return template_manager


def get_strategy_tester():
    """获取策略测试器实例"""
    global strategy_tester
    if strategy_tester is None:
        strategy_tester = StrategyTester()
    return strategy_tester


# ==================== 策略模板 API ====================


class TemplateVariableModel(BaseModel):
    name: str
    type: str
    default: Any
    description: str
    required: bool = False


class StrategyNodeModel(BaseModel):
    id: str
    type: str
    name: str
    parameters: Dict[str, Any] = {}
    dependencies: List[str] = []
    position: Dict[str, float] = {"x": 0, "y": 0}


class CreateTemplateModel(BaseModel):
    name: str
    type: str
    description: str
    author: str
    variables: List[TemplateVariableModel] = []
    nodes: List[StrategyNodeModel] = []
    code_template: str = ""


@router.post("/templates")
def create_template(template: CreateTemplateModel):
    """创建新模板"""
    try:
        engine = get_template_engine()
        template_id = engine.create_template(
            name=template.name,
            template_type=TemplateType(template.type),
            description=template.description,
            author=template.author,
            variables=[TemplateVariable(**v.dict()) for v in template.variables],
            nodes=[StrategyNode(**n.dict()) for n in template.nodes],
            code_template=template.code_template,
        )
        return {"success": True, "template_id": template_id}
    except Exception as e:
        logger.error(f"创建模板失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates")
def list_templates(
    template_type: Optional[str] = None, status: Optional[str] = None, limit: int = 100
):
    """列出所有模板"""
    try:
        engine = get_template_engine()

        type_filter = TemplateType(template_type) if template_type else None
        status_filter = TemplateStatus(status) if status else None

        templates = engine.list_templates(
            template_type=type_filter, status=status_filter
        )

        return {
            "success": True,
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "type": t.type.value,
                    "description": t.description,
                    "version": t.version,
                    "author": t.author,
                    "status": t.status.value,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at,
                }
                for t in templates[:limit]
            ],
            "total": len(templates),
        }
    except Exception as e:
        logger.error(f"获取模板列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}")
def get_template(template_id: str):
    """获取单个模板"""
    try:
        engine = get_template_engine()
        template = engine.get_template(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        return {
            "success": True,
            "template": {
                "id": template.id,
                "name": template.name,
                "type": template.type.value,
                "description": template.description,
                "version": template.version,
                "author": template.author,
                "status": template.status.value,
                "variables": [v.__dict__ for v in template.variables],
                "nodes": [n.__dict__ for n in template.nodes],
                "edges": template.edges,
                "code_template": template.code_template,
                "metadata": template.metadata,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/{template_id}")
def update_template(template_id: str, updates: Dict[str, Any]):
    """更新模板"""
    try:
        engine = get_template_engine()
        success = engine.update_template(template_id, **updates)

        if not success:
            raise HTTPException(status_code=404, detail="模板不存在")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}")
def delete_template(template_id: str):
    """删除模板"""
    try:
        engine = get_template_engine()
        success = engine.delete_template(template_id)

        if not success:
            raise HTTPException(status_code=404, detail="模板不存在")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_id}/instantiate")
def instantiate_template(template_id: str, variables: Dict[str, Any]):
    """实例化模板"""
    try:
        engine = get_template_engine()
        result = engine.instantiate_template(template_id, variables)

        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"实例化模板失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates/{template_id}/export")
def export_template(template_id: str, format: str = "json"):
    """导出模板"""
    try:
        engine = get_template_engine()
        content = engine.export_template(template_id, format)

        if format == "json":
            return StreamingResponse(
                iter([content]),
                media_type="application / json",
                headers={
                    "Content - Disposition": f"attachment; filename=template_{template_id}.json"
                },
            )
        elif format == "yaml":
            return StreamingResponse(
                iter([content]),
                media_type="application / x - yaml",
                headers={
                    "Content - Disposition": f"attachment; filename=template_{template_id}.yaml"
                },
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的格式")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates / import")
async def import_template(
    file: UploadFile = File(...), format: str = "json", overwrite: bool = False
):
    """导入模板"""
    try:
        manager = get_template_manager()
        content = await file.read()

        # 保存临时文件
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(content)

        template_id = manager.import_template(
            temp_path, ExportFormat(format), overwrite
        )

        # 删除临时文件
        Path(temp_path).unlink(missing_ok=True)

        return {"success": True, "template_id": template_id}
    except Exception as e:
        logger.error(f"导入模板失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates / statistics")
def get_template_statistics():
    """获取模板统计信息"""
    try:
        manager = get_template_manager()
        stats = manager.get_template_analytics()

        return {"success": True, "statistics": stats}
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 模板管理 API ====================


@router.get("/templates / search")
def search_templates(
    query: Optional[str] = None,
    template_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    author: Optional[str] = None,
    sort_by: str = "updated",
    sort_order: str = "desc",
    limit: int = 100,
):
    """搜索模板"""
    try:
        manager = get_template_manager()

        tags_list = tags.split(",") if tags else None

        templates = manager.search_templates(
            query=query,
            template_type=TemplateType(template_type) if template_type else None,
            category=category,
            tags=tags_list,
            author=author,
            limit=limit,
        )

        return {
            "success": True,
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "type": t.type.value,
                    "description": t.description,
                    "category": t.metadata.get("category"),
                    "tags": t.metadata.get("tags", []),
                    "author": t.author,
                    "updated_at": t.updated_at,
                }
                for t in templates
            ],
        }
    except Exception as e:
        logger.error(f"搜索模板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates / categories")
def get_template_categories():
    """获取所有分类"""
    try:
        manager = get_template_manager()
        categories = manager.get_categories()

        return {"success": True, "categories": categories}
    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates / tags")
def get_template_tags():
    """获取所有标签"""
    try:
        manager = get_template_manager()
        tags = manager.get_tags()

        return {"success": True, "tags": tags}
    except Exception as e:
        logger.error(f"获取标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates / bulk - export")
def bulk_export_templates(template_ids: List[str], format: str = "zip"):
    """批量导出模板"""
    try:
        manager = get_template_manager()
        output_path = manager.bulk_export(
            template_ids, "bulk_export", ExportFormat(format)
        )

        if not output_path:
            raise HTTPException(status_code=400, detail="导出失败")

        return FileResponse(
            output_path, media_type="application / zip", filename=Path(output_path).name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量导出失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates / backup")
def backup_templates():
    """备份所有模板"""
    try:
        manager = get_template_manager()
        backup_path = manager.backup_templates()

        return FileResponse(
            backup_path, media_type="application / zip", filename=Path(backup_path).name
        )
    except Exception as e:
        logger.error(f"备份失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 策略测试 API ====================


class TestConfigModel(BaseModel):
    strategy_code: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    commission_rate: float = 0.0003
    slippage: float = 0.0001


@router.post("/tests / backtest")
def run_backtest(config: TestConfigModel, background_tasks: BackgroundTasks):
    """运行回测"""
    try:
        tester = get_strategy_tester()
        test_config = TestConfig(
            strategy_code=config.strategy_code,
            symbol=config.symbol,
            start_date=config.start_date,
            end_date=config.end_date,
            initial_capital=config.initial_capital,
            commission_rate=config.commission_rate,
            slippage=config.slippage,
        )

        result = tester.run_backtest(test_config)

        return {
            "success": True,
            "test_id": result.test_id,
            "metrics": {
                "total_return": result.total_return,
                "annualized_return": result.annualized_return,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "win_rate": result.win_rate,
                "total_trades": result.total_trades,
            },
        }
    except Exception as e:
        logger.error(f"回测失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tests / walk - forward")
def run_walk_forward(
    config: TestConfigModel,
    train_period: int = 252,
    test_period: int = 63,
    step: int = 21,
):
    """运行前进分析"""
    try:
        tester = get_strategy_tester()
        test_config = TestConfig(
            strategy_code=config.strategy_code,
            symbol=config.symbol,
            start_date=config.start_date,
            end_date=config.end_date,
            initial_capital=config.initial_capital,
            commission_rate=config.commission_rate,
            slippage=config.slippage,
        )

        results = tester.run_walk_forward(test_config, train_period, test_period, step)

        return {
            "success": True,
            "num_rounds": len(results),
            "results": [
                {
                    "test_id": r.test_id,
                    "total_return": r.total_return,
                    "sharpe_ratio": r.sharpe_ratio,
                    "max_drawdown": r.max_drawdown,
                }
                for r in results
            ],
        }
    except Exception as e:
        logger.error(f"前进分析失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tests / monte - carlo")
def run_monte_carlo(
    config: TestConfigModel, num_simulations: int = 1000, confidence_level: float = 0.95
):
    """运行蒙特卡洛模拟"""
    try:
        tester = get_strategy_tester()
        test_config = TestConfig(
            strategy_code=config.strategy_code,
            symbol=config.symbol,
            start_date=config.start_date,
            end_date=config.end_date,
            initial_capital=config.initial_capital,
            commission_rate=config.commission_rate,
            slippage=config.slippage,
        )

        result = tester.run_monte_carlo(test_config, num_simulations, confidence_level)

        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"蒙特卡洛模拟失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tests/{test_id}")
def get_test_result(test_id: str):
    """获取测试结果"""
    try:
        tester = get_strategy_tester()
        result = tester.get_test_result(test_id)

        if not result:
            raise HTTPException(status_code=404, detail="测试结果不存在")

        return {
            "success": True,
            "result": {
                "test_id": result.test_id,
                "test_type": result.test_type.value,
                "start_date": result.start_date,
                "end_date": result.end_date,
                "initial_capital": result.initial_capital,
                "final_capital": result.final_capital,
                "total_return": result.total_return,
                "annualized_return": result.annualized_return,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown,
                "win_rate": result.win_rate,
                "total_trades": result.total_trades,
                "equity_curve": result.equity_curve[:50],  # 只返回前50个点
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取测试结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tests")
def list_tests(
    test_type: Optional[str] = None, strategy_id: Optional[str] = None, limit: int = 100
):
    """列出测试结果"""
    try:
        tester = get_strategy_tester()

        type_filter = TestType(test_type) if test_type else None

        results = tester.list_tests(
            test_type=type_filter, strategy_id=strategy_id, limit=limit
        )

        return {
            "success": True,
            "tests": [
                {
                    "test_id": r.test_id,
                    "test_type": r.test_type.value,
                    "strategy_id": r.strategy_id,
                    "start_date": r.start_date,
                    "end_date": r.end_date,
                    "total_return": r.total_return,
                    "sharpe_ratio": r.sharpe_ratio,
                    "created_at": r.created_at,
                }
                for r in results
            ],
        }
    except Exception as e:
        logger.error(f"获取测试列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tests/{test_id}/report")
def generate_test_report(test_id: str):
    """生成测试报告"""
    try:
        tester = get_strategy_tester()
        report_path = tester.generate_report(test_id)

        return FileResponse(
            report_path, media_type="text / html", filename=f"test_report_{test_id}.html"
        )
    except Exception as e:
        logger.error(f"生成报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tests / compare")
def compare_strategies(test_ids: List[str]):
    """比较多个策略"""
    try:
        tester = get_strategy_tester()
        comparison = tester.compare_strategies(test_ids)

        return {"success": True, "comparison": comparison}
    except Exception as e:
        logger.error(f"策略比较失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 健康检查 ====================


@router.get("/health")
def health_check():
    """健康检查"""
    try:
        return {
            "status": "healthy",
            "services": {
                "template_engine": template_engine is not None,
                "template_manager": template_manager is not None,
                "strategy_tester": strategy_tester is not None,
            },
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {"status": "unhealthy", "error": str(e)}
