"""
统一数据管道模块

提供价格和非价格数据的统一管理、缓存、验证和同步功能。

Task #31: Data Flow Unification - Price and Non-Price Integration
"""

# 核心组件
from .cache_manager import (
    UnifiedCacheManager,
    unified_cache_manager,
    CacheEntry,
    CacheStats,
    LRUICache
)

from .quality_validator import (
    DataQualityValidator,
    data_quality_validator,
    QualityResult,
    QualityCheck,
    QualityLevel,
    QualityIssue,
    QualityThresholds
)

from .data_synchronizer import (
    DataSynchronizer,
    data_synchronizer,
    SyncTask,
    SyncStatus,
    DataSource,
    DataSyncConfig
)

from .data_pipeline import (
    UnifiedDataPipeline,
    unified_data_pipeline,
    DataRequest,
    DataSourceAdapter,
    PriceDataAdapter,
    HKMADataAdapter,
    SentimentDataAdapter
)

# 数据模型
from .models import (
    # Enums
    DataSource as ModelDataSource,
    DataType,
    PriceType,
    HKMAIndicator,
    SentimentType,

    # Pydantic Schemas
    UnifiedDataPointSchema,
    PriceDataSchema,
    HKMADataSchema,
    SentimentDataSchema,
    AlternativeDataSchema,
    UnifiedDataSeriesSchema,
    QualityResultSchema,

    # SQLAlchemy Models
    UnifiedDataPoint,
    PriceData,
    HKMAData,
    SentimentData,
    AlternativeData,
    DataSyncLog,

    # Utilities
    ModelConverter
)

# 版本信息
__version__ = "1.0.0"
__author__ = "CBSC Development Team"
__description__ = "统一数据管道 - 价格和非价格数据集成管理"

# 模块级配置
DEFAULT_CACHE_SIZE = 1000
DEFAULT_CLEANUP_INTERVAL = 300
DEFAULT_QUALITY_THRESHOLD = 0.8
DEFAULT_MAX_CONCURRENT_TASKS = 10

# 导出的公共接口
__all__ = [
    # Core Components
    'UnifiedCacheManager',
    'unified_cache_manager',
    'DataQualityValidator',
    'data_quality_validator',
    'DataSynchronizer',
    'data_synchronizer',
    'UnifiedDataPipeline',
    'unified_data_pipeline',

    # Data Models
    'UnifiedDataPointSchema',
    'PriceDataSchema',
    'HKMADataSchema',
    'SentimentDataSchema',
    'UnifiedDataSeriesSchema',
    'QualityResultSchema',

    # Enums
    'DataSource',
    'DataType',
    'QualityLevel',
    'SyncStatus',

    # Supporting Classes
    'DataRequest',
    'QualityThresholds',
    'CacheStats',
    'SyncTask',
    'ModelConverter',

    # Configuration
    'DEFAULT_CACHE_SIZE',
    'DEFAULT_CLEANUP_INTERVAL',
    'DEFAULT_QUALITY_THRESHOLD',
    'DEFAULT_MAX_CONCURRENT_TASKS',

    # Version Info
    '__version__',
    '__author__',
    '__description__'
]

# 初始化日志
import logging
logger = logging.getLogger(__name__)
logger.info(f"统一数据管道模块已加载: v{__version__}")

# 模块初始化函数
async def initialize_unified_system():
    """初始化统一数据系统"""
    try:
        # 初始化缓存管理器
        logger.info("初始化统一缓存管理器...")
        # unified_cache_manager 在导入时已创建

        # 初始化数据同步器
        logger.info("初始化数据同步器...")
        # data_synchronizer 在导入时已创建

        # 初始化数据管道
        logger.info("初始化统一数据管道...")
        # unified_data_pipeline 在导入时已创建

        # 注册数据源适配器
        await unified_data_pipeline.register_adapter(PriceDataAdapter())
        await unified_data_pipeline.register_adapter(HKMADataAdapter())
        await unified_data_pipeline.register_adapter(SentimentDataAdapter())

        logger.info("统一数据系统初始化完成")

    except Exception as e:
        logger.error(f"统一数据系统初始化失败: {e}")
        raise

# 模块清理函数
async def cleanup_unified_system():
    """清理统一数据系统"""
    try:
        logger.info("清理统一数据系统...")

        # 关闭数据同步器
        await data_synchronizer.close()

        # 关闭缓存管理器
        await unified_cache_manager.close()

        logger.info("统一数据系统清理完成")

    except Exception as e:
        logger.error(f"清理统一数据系统失败: {e}")