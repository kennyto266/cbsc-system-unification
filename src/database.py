from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from typing import List, Optional, Dict, Any
import os
from datetime import datetime
import logging
import json

# Import the secure SQL framework
try:
    from .security.secure_sql_framework import SecureSQLFramework, QUANT_TRADING_SCHEMA, secure_read_sql
except ImportError:
    # Fallback for direct execution
    from security.secure_sql_framework import SecureSQLFramework, QUANT_TRADING_SCHEMA, secure_read_sql

logger = logging.getLogger('quant_system')

Base = declarative_base()

class StockData(Base):
    """股票数据表"""
    __tablename__ = 'stock_data'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    source = Column(String(50))  # 数据源

    def __repr__(self):
        return f"<StockData(symbol='{self.symbol}', timestamp='{self.timestamp}', close={self.close_price})>"

class StrategySignal(Base):
    """策略信号表"""
    __tablename__ = 'strategy_signals'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    strategy_name = Column(String(100), nullable=False)
    signal_type = Column(String(20))  # BUY, SELL, HOLD
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    parameters = Column(Text)  # JSON格式的参数

class MLModel(Base):
    """机器学习模型表"""
    __tablename__ = 'ml_models'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    model_type = Column(String(50))  # linear_regression, random_forest, lstm
    trained_at = Column(DateTime, default=datetime.utcnow)
    accuracy = Column(Float)
    parameters = Column(Text)  # JSON格式的模型参数
    model_path = Column(String(500))  # 模型文件路径

class User(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), default='user')  # admin, user
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class SecureDatabaseManager:
    """安全数据库管理器 - 集成SQL注入防护"""

    def __init__(self):
        # 获取数据库URL并验证 (使用 docker-compose 凭据)
        database_url = os.getenv('DATABASE_URL', 'postgresql://cbsc_user:cbsc_password@localhost:5432/cbsc_strategy')

        # 基本验证数据库URL
        if not self._validate_database_url(database_url):
            raise ValueError("Invalid database URL format")

        self.engine = create_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_timeout=30
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # 初始化安全SQL框架
        self.secure_sql = SecureSQLFramework(QUANT_TRADING_SCHEMA)

        # 扩展CBSC专用表模式
        self.cbsc_schema = {
            **QUANT_TRADING_SCHEMA,
            'stock_data': ['id', 'symbol', 'timestamp', 'open_price', 'high_price',
                          'low_price', 'close_price', 'volume', 'source'],
            'strategy_signals': ['id', 'symbol', 'strategy_name', 'signal_type',
                               'confidence', 'timestamp', 'parameters'],
            'ml_models': ['id', 'name', 'model_type', 'trained_at', 'accuracy',
                         'parameters', 'model_path'],
            'users': ['id', 'username', 'email', 'hashed_password', 'role',
                     'created_at', 'is_active']
        }

        # 更新安全框架的模式
        self.secure_sql.allowed_tables = self.cbsc_schema

        self.create_tables()

    def _validate_database_url(self, url: str) -> bool:
        """验证数据库URL格式"""
        try:
            # 基本格式检查
            if not url.startswith(('postgresql://', 'mysql://', 'sqlite:///')):
                logger.warning(f"Potentially insecure database URL scheme: {url}")
                return False

            # 检查是否包含敏感信息明文（应该在环境变量中）
            if 'password' in url and 'localhost' not in url:
                logger.warning("Database URL contains password - should use environment variables")

            return True
        except Exception as e:
            logger.error(f"Database URL validation failed: {e}")
            return False

    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    def save_stock_data(self, symbol: str, data: dict, source: str = 'primary'):
        """安全保存股票数据"""
        # 验证输入参数
        if not self.secure_sql.validate_table_name('stock_data'):
            raise ValueError("Invalid table access")

        # 验证symbol格式（港股代码格式）
        if not self._validate_stock_symbol(symbol):
            raise ValueError(f"Invalid stock symbol format: {symbol}")

        session = self.get_session()
        try:
            # 验证数据格式
            validated_data = self._validate_stock_data(data)

            stock_data = StockData(
                symbol=symbol,
                timestamp=datetime.fromisoformat(validated_data['date']) if 'date' in validated_data else datetime.utcnow(),
                open_price=validated_data.get('open'),
                high_price=validated_data.get('high'),
                low_price=validated_data.get('low'),
                close_price=validated_data['price'],
                volume=validated_data.get('volume'),
                source=source
            )
            session.add(stock_data)
            session.commit()
            logger.info(f"Saved stock data for {symbol}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save stock data: {e}")
            raise
        finally:
            session.close()

    def _validate_stock_symbol(self, symbol: str) -> bool:
        """验证股票代码格式"""
        import re
        # 港股代码格式验证 (例如: 0700.HK, 9988.HK)
        pattern = r'^[0-9]{4}\.HK$'
        return bool(re.match(pattern, symbol.upper()))

    def _validate_stock_data(self, data: dict) -> dict:
        """验证股票数据格式"""
        validated = {}

        # 必需字段
        if 'price' not in data:
            raise ValueError("Price is required")

        try:
            validated['price'] = float(data['price'])
            if validated['price'] <= 0:
                raise ValueError("Price must be positive")
        except (ValueError, TypeError):
            raise ValueError("Invalid price format")

        # 可选字段验证
        for field in ['open', 'high', 'low', 'volume']:
            if field in data and data[field] is not None:
                try:
                    if field == 'volume':
                        validated[field] = int(data[field])
                        if validated[field] < 0:
                            raise ValueError(f"{field} cannot be negative")
                    else:
                        validated[field] = float(data[field])
                        if validated[field] < 0:
                            raise ValueError(f"{field} cannot be negative")
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid {field} format")

        # 日期验证
        if 'date' in data:
            try:
                datetime.fromisoformat(data['date'])
                validated['date'] = data['date']
            except ValueError:
                raise ValueError("Invalid date format, use ISO format")

        return validated

    def get_stock_history(self, symbol: str, limit: int = 1000) -> List[dict]:
        """安全获取股票历史数据"""
        # 验证输入
        if not self._validate_stock_symbol(symbol):
            raise ValueError(f"Invalid stock symbol format: {symbol}")

        if not isinstance(limit, int) or limit <= 0 or limit > 10000:
            raise ValueError("Invalid limit value (must be 1-10000)")

        session = self.get_session()
        try:
            # 使用SQLAlchemy的安全查询
            records = session.query(StockData).filter_by(symbol=symbol).order_by(
                StockData.timestamp.desc()
            ).limit(limit).all()

            return [{
                'symbol': record.symbol,
                'timestamp': record.timestamp.isoformat(),
                'open': record.open_price,
                'high': record.high_price,
                'low': record.low_price,
                'close': record.close_price,
                'volume': record.volume
            } for record in records]
        except Exception as e:
            logger.error(f"Failed to get stock history: {e}")
            raise
        finally:
            session.close()

    def save_strategy_signal(self, symbol: str, strategy_name: str, signal_type: str,
                           confidence: float, parameters: dict = None):
        """安全保存策略信号"""
        # 验证输入
        if not self._validate_stock_symbol(symbol):
            raise ValueError(f"Invalid stock symbol format: {symbol}")

        if signal_type not in ['BUY', 'SELL', 'HOLD']:
            raise ValueError(f"Invalid signal type: {signal_type}")

        if not (0 <= confidence <= 1):
            raise ValueError("Confidence must be between 0 and 1")

        session = self.get_session()
        try:
            signal = StrategySignal(
                symbol=symbol,
                strategy_name=strategy_name,
                signal_type=signal_type,
                confidence=confidence,
                parameters=json.dumps(parameters) if parameters else None
            )
            session.add(signal)
            session.commit()
            logger.info(f"Saved strategy signal: {strategy_name} for {symbol}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save strategy signal: {e}")
            raise
        finally:
            session.close()

    def get_strategy_signals(self, symbol: str = None, limit: int = 100) -> List[dict]:
        """安全获取策略信号"""
        if symbol and not self._validate_stock_symbol(symbol):
            raise ValueError(f"Invalid stock symbol format: {symbol}")

        if not isinstance(limit, int) or limit <= 0 or limit > 1000:
            raise ValueError("Invalid limit value (must be 1-1000)")

        session = self.get_session()
        try:
            query = session.query(StrategySignal)
            if symbol:
                query = query.filter_by(symbol=symbol)

            signals = query.order_by(StrategySignal.timestamp.desc()).limit(limit).all()

            return [{
                'id': signal.id,
                'symbol': signal.symbol,
                'strategy_name': signal.strategy_name,
                'signal_type': signal.signal_type,
                'confidence': signal.confidence,
                'timestamp': signal.timestamp.isoformat(),
                'parameters': signal.parameters
            } for signal in signals]
        except Exception as e:
            logger.error(f"Failed to get strategy signals: {e}")
            raise
        finally:
            session.close()

    def save_ml_model(self, name: str, model_type: str, accuracy: float,
                     parameters: dict = None, model_path: str = None):
        """安全保存ML模型信息"""
        # 验证输入
        if not name or not isinstance(name, str):
            raise ValueError("Model name is required and must be a string")

        if model_type not in ['linear_regression', 'random_forest', 'lstm', 'xgboost', 'neural_network']:
            raise ValueError(f"Invalid model type: {model_type}")

        if not (0 <= accuracy <= 1):
            raise ValueError("Accuracy must be between 0 and 1")

        session = self.get_session()
        try:
            existing = session.query(MLModel).filter_by(name=name).first()
            if existing:
                existing.trained_at = datetime.utcnow()
                existing.accuracy = accuracy
                existing.parameters = json.dumps(parameters) if parameters else None
                existing.model_path = model_path
            else:
                model = MLModel(
                    name=name,
                    model_type=model_type,
                    accuracy=accuracy,
                    parameters=json.dumps(parameters) if parameters else None,
                    model_path=model_path
                )
                session.add(model)

            session.commit()
            logger.info(f"Saved ML model: {name}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save ML model: {e}")
            raise
        finally:
            session.close()

    def get_ml_models(self) -> List[dict]:
        """安全获取所有ML模型"""
        session = self.get_session()
        try:
            models = session.query(MLModel).all()
            return [{
                'id': model.id,
                'name': model.name,
                'model_type': model.model_type,
                'trained_at': model.trained_at.isoformat(),
                'accuracy': model.accuracy,
                'model_path': model.model_path
            } for model in models]
        except Exception as e:
            logger.error(f"Failed to get ML models: {e}")
            raise
        finally:
            session.close()

# 创建全局安全数据库管理器实例
db_manager = SecureDatabaseManager()

# 向后兼容的别名
DatabaseManager = SecureDatabaseManager