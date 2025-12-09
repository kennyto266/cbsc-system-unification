"""
系統配置管理
支持環境變量和配置文件
"""

import os
import secrets
from typing import List, Optional
from pydantic import BaseSettings, validator
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """應用程式配置"""

    # 基本配置
    APP_NAME: str = "量化交易系統API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # 服務器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = True

    # 安全配置
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3001",
        "http://localhost:3001",
        "http://127.0.0.1:8080",
        "http://localhost:8080"
    ]

    # 數據庫配置
    DATABASE_URL: str = "sqlite:///./trading_system.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10
    CACHE_TTL: int = 300  # 5分鐘

    # 香港政府API配置
    HKMA_API_BASE_URL: str = "https://api.hkma.gov.hk/public"
    HKMA_RATE_LIMIT: int = 100  # 每分鐘請求數
    HKMA_TIMEOUT: int = 30  # 秒

    # 支持的股票符號
    SUPPORTED_SYMBOLS: List[str] = [
        "0700.HK",  # 騰訊控股
        "0941.HK",  # 中國移動
        "1299.HK",  # 友邦保險
        "2318.HK",  # 中國平安
        "0005.HK",  # 匯豐控股
        "0388.HK",  # 香港交易所
        "0011.HK",  # 恒生銀行
        "0012.HK",  # 恒基地產
        "0002.HK",  # 中電控股
        "0883.HK"   # 中國海洋石油
    ]

    # WebSocket配置
    WEBSOCKET_MAX_CONNECTIONS: int = 100
    WEBSOCKET_RATE_LIMIT: int = 100  # 每分鐘消息數
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # 秒

    # 回測配置
    MAX_CONCURRENT_BACKTESTS: int = 5
    BACKTEST_TIMEOUT: int = 600  # 秒
    DEFAULT_INITIAL_CAPITAL: float = 1000000.0
    DEFAULT_COMMISSION: float = 0.001
    DEFAULT_SLIPPAGE: float = 0.0001

    # 數據保留配置
    DATA_RETENTION_DAYS: int = 365
    LOG_RETENTION_DAYS: int = 30
    BACKUP_RETENTION_DAYS: int = 90

    # 風險管理配置
    MAX_POSITION_SIZE: float = 0.2  # 最大持倉比例
    MAX_DAILY_LOSS: float = 0.05  # 最大日損失比例
    MAX_VAR_PERCENTAGE: float = 0.02  # 最大VaR比例
    EMERGENCY_STOP_THRESHOLD: float = 0.1  # 緊急停止閾值

    # 監控配置
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    HEALTH_CHECK_INTERVAL: int = 60  # 秒

    # 日誌配置
    LOG_FILE_PATH: str = "logs/api.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @validator("SUPPORTED_SYMBOLS", pre=True)
    def parse_symbols(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

class DevelopmentSettings(Settings):
    """開發環境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    RELOAD: bool = True
    WORKERS: int = 1
    REDIS_URL: str = "redis://localhost:6379/1"  # 使用不同的數據庫

class ProductionSettings(Settings):
    """生產環境配置"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    RELOAD: bool = False
    WORKERS: int = 4
    SECRET_KEY: str  # 必須在環境變量中設置
    DATABASE_URL: str  # 必須在環境變量中設置

class TestingSettings(Settings):
    """測試環境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DATABASE_URL: str = "sqlite:///./test_trading_system.db"
    REDIS_URL: str = "redis://localhost:6379/2"
    SUPPORTED_SYMBOLS: List[str] = ["0700.HK"]  # 測試時只用一個股票

# 環境映射
ENVIRONMENT_SETTINGS = {
    "development": DevelopmentSettings,
    "production": ProductionSettings,
    "testing": TestingSettings
}

def get_settings() -> Settings:
    """獲取當前環境的配置"""
    env = os.getenv("ENVIRONMENT", "development").lower()

    # 根據環境選擇設置類
    settings_class = ENVIRONMENT_SETTINGS.get(env, Settings)

    try:
        settings = settings_class()
        logger.info(f"使用 {env} 環境配置")
        return settings
    except Exception as e:
        logger.error(f"載入配置失敗: {e}")
        # 回退到默認配置
        return Settings()

# 配置驗證
def validate_settings(settings: Settings) -> bool:
    """驗證配置是否正確"""
    try:
        # 驗證必要的配置項
        required_settings = [
            "SECRET_KEY",
            "DATABASE_URL"
        ]

        for setting_name in required_settings:
            value = getattr(settings, setting_name, None)
            if not value or value == "":
                logger.error(f"缺少必要配置: {setting_name}")
                return False

        # 驗證數值範圍
        numeric_validations = {
            "PORT": (1, 65535),
            "ACCESS_TOKEN_EXPIRE_MINUTES": (1, 1440),
            "WEBSOCKET_MAX_CONNECTIONS": (1, 1000),
            "WEBSOCKET_RATE_LIMIT": (1, 1000),
            "BACKTEST_TIMEOUT": (30, 3600),
            "MAX_CONCURRENT_BACKTESTS": (1, 20),
            "DATA_RETENTION_DAYS": (1, 3650),
            "LOG_RETENTION_DAYS": (1, 365)
        }

        for setting_name, (min_val, max_val) in numeric_validations.items():
            value = getattr(settings, setting_name)
            if not (min_val <= value <= max_val):
                logger.error(f"配置值超出範圍: {setting_name} = {value}, 應在 {min_val}-{max_val} 之間")
                return False

        logger.info("配置驗證通過")
        return True

    except Exception as e:
        logger.error(f"配置驗證失敗: {e}")
        return False

# 配置打印
def print_settings(settings: Settings):
    """打印配置信息（隱藏敏感信息）"""
    safe_settings = {}
    sensitive_fields = ["SECRET_KEY", "DATABASE_URL"]

    for key, value in settings.dict().items():
        if key in sensitive_fields:
            safe_settings[key] = "***REDACTED***"
        elif isinstance(value, list):
            safe_settings[key] = f"[{len(value)} items]"
        else:
            safe_settings[key] = value

    logger.info("當前配置:")
    for key, value in safe_settings.items():
        logger.info(f"  {key}: {value}")

# 環境變量設置
def set_environment_variables():
    """設置默認環境變量"""
    # 如果沒有設置密鑰，生成一個
    if not os.getenv("SECRET_KEY"):
        os.environ["SECRET_KEY"] = secrets.token_urlsafe(32)
        logger.warning("生成新的SECRET_KEY，建議保存到環境變量中")

    # 設置默認數據庫URL
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:///./trading_system.db"

    # 設置默認Redis URL
    if not os.getenv("REDIS_URL"):
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"

# 初始化配置
def initialize_config() -> Settings:
    """初始化配置"""
    # 設置環境變量
    set_environment_variables()

    # 獲取配置
    settings = get_settings()

    # 驗證配置
    if not validate_settings(settings):
        raise ValueError("配置驗證失敗，請檢查配置文件或環境變量")

    # 創建必要的目錄
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # 打印配置（開發環境）
    if settings.DEBUG:
        print_settings(settings)

    return settings

# 全局配置實例
settings = get_settings()