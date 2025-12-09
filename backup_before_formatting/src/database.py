import logging
import os
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

logger = logging.getLogger("quant_system")

Base = declarative_base()


class StockData(Base):
    """股票数据表"""

    __tablename__ = "stock_data"

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

    __tablename__ = "strategy_signals"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    strategy_name = Column(String(100), nullable=False)
    signal_type = Column(String(20))  # BUY, SELL, HOLD
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    parameters = Column(Text)  # JSON格式的参数


class MLModel(Base):
    """机器学习模型表"""

    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    model_type = Column(String(50))  # linear_regression, random_forest, lstm
    trained_at = Column(DateTime, default=datetime.utcnow)
    accuracy = Column(Float)
    parameters = Column(Text)  # JSON格式的模型参数
    model_path = Column(String(500))  # 模型文件路径


class User(Base):
    """用户表"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(20), default="user")  # admin, user
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        database_url = os.getenv(
            "DATABASE_URL", "postgresql://user:password@localhost / quant_system"
        )
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # 创建表
        self.create_tables()

    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")

    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    def save_stock_data(self, symbol: str, data: dict, source: str = "primary"):
        """保存股票数据"""
        session = self.get_session()
        try:
            stock_data = StockData(
                symbol=symbol,
                timestamp=(
                    datetime.fromisoformat(data["date"])
                    if "date" in data
                    else datetime.utcnow()
                ),
                open_price=data.get("open"),
                high_price=data.get("high"),
                low_price=data.get("low"),
                close_price=data["price"],
                volume=data.get("volume"),
                source=source,
            )
            session.add(stock_data)
            session.commit()
            logger.info(f"Saved stock data for {symbol}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save stock data: {e}")
        finally:
            session.close()

    def get_stock_history(self, symbol: str, limit: int = 1000) -> List[dict]:
        """获取股票历史数据"""
        session = self.get_session()
        try:
            records = (
                session.query(StockData)
                .filter_by(symbol=symbol)
                .order_by(StockData.timestamp.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "symbol": record.symbol,
                    "timestamp": record.timestamp.isoformat(),
                    "open": record.open_price,
                    "high": record.high_price,
                    "low": record.low_price,
                    "close": record.close_price,
                    "volume": record.volume,
                }
                for record in records
            ]
        except Exception as e:
            logger.error(f"Failed to get stock history: {e}")
            return []
        finally:
            session.close()

    def save_strategy_signal(
        self,
        symbol: str,
        strategy_name: str,
        signal_type: str,
        confidence: float,
        parameters: dict = None,
    ):
        """保存策略信号"""
        session = self.get_session()
        try:
            signal = StrategySignal(
                symbol=symbol,
                strategy_name=strategy_name,
                signal_type=signal_type,
                confidence=confidence,
                parameters=str(parameters) if parameters else None,
            )
            session.add(signal)
            session.commit()
            logger.info(f"Saved strategy signal: {strategy_name} for {symbol}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save strategy signal: {e}")
        finally:
            session.close()

    def get_strategy_signals(self, symbol: str = None, limit: int = 100) -> List[dict]:
        """获取策略信号"""
        session = self.get_session()
        try:
            query = session.query(StrategySignal)
            if symbol:
                query = query.filter_by(symbol=symbol)

            signals = query.order_by(StrategySignal.timestamp.desc()).limit(limit).all()

            return [
                {
                    "id": signal.id,
                    "symbol": signal.symbol,
                    "strategy_name": signal.strategy_name,
                    "signal_type": signal.signal_type,
                    "confidence": signal.confidence,
                    "timestamp": signal.timestamp.isoformat(),
                    "parameters": signal.parameters,
                }
                for signal in signals
            ]
        except Exception as e:
            logger.error(f"Failed to get strategy signals: {e}")
            return []
        finally:
            session.close()

    def save_ml_model(
        self,
        name: str,
        model_type: str,
        accuracy: float,
        parameters: dict = None,
        model_path: str = None,
    ):
        """保存ML模型信息"""
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(MLModel).filter_by(name=name).first()
            if existing:
                existing.trained_at = datetime.utcnow()
                existing.accuracy = accuracy
                existing.parameters = str(parameters) if parameters else None
                existing.model_path = model_path
            else:
                model = MLModel(
                    name=name,
                    model_type=model_type,
                    accuracy=accuracy,
                    parameters=str(parameters) if parameters else None,
                    model_path=model_path,
                )
                session.add(model)

            session.commit()
            logger.info(f"Saved ML model: {name}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save ML model: {e}")
        finally:
            session.close()

    def get_ml_models(self) -> List[dict]:
        """获取所有ML模型"""
        session = self.get_session()
        try:
            models = session.query(MLModel).all()
            return [
                {
                    "id": model.id,
                    "name": model.name,
                    "model_type": model.model_type,
                    "trained_at": model.trained_at.isoformat(),
                    "accuracy": model.accuracy,
                    "model_path": model.model_path,
                }
                for model in models
            ]
        except Exception as e:
            logger.error(f"Failed to get ML models: {e}")
            return []
        finally:
            session.close()


# 全局实例
db_manager = DatabaseManager()
