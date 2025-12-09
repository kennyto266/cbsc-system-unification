"""
用户资料和仪表板服务
User Profile and Dashboard Service
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, func
import os
import logging
import json
import hashlib
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./user_management.db")

# 数据库模型
Base = declarative_base()

class UserProfile(Base):
    """用户资料模型"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    avatar_url = Column(String(255))
    bio = Column(Text)
    phone = Column(String(20))
    timezone = Column(String(50), default='Asia/Shanghai')
    language = Column(String(10), default='zh-CN')
    theme = Column(String(20), default='light')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship("User", backref="profile")

class UserStatistics(Base):
    """用户统计模型"""
    __tablename__ = "user_statistics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stat_date = Column(DateTime)  # 统计日期
    login_count = Column(Integer, default=0)
    trade_count = Column(Integer, default=0)
    strategy_count = Column(Integer, default=0)
    performance_score = Column(Float, default=0.0)
    active_minutes = Column(Integer, default=0)  # 活跃分钟数
    created_at = Column(DateTime, default=datetime.utcnow)

class UserActivity(Base):
    """用户活动模型"""
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String(50))  # login, trade, strategy, settings, export
    description = Column(Text)
    metadata = Column(JSON)  # 额外的活动数据
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    user = relationship("User", backref="activities")

class UserSettings(Base):
    """用户设置模型"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    email_notifications = Column(JSON)  # 邮件通知设置
    browser_notifications = Column(JSON)  # 浏览器通知设置
    privacy_settings = Column(JSON)  # 隐私设置
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship("User", backref="settings")

# 用户资料服务类
class UserProfileService:
    """用户资料服务类"""

    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """创建数据库表"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("用户资料相关数据库表创建完成")

    def get_db(self):
        """获取数据库会话"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def get_or_create_profile(self, user_id: int, db=None) -> UserProfile:
        """获取或创建用户资料"""
        if db is None:
            db = self.SessionLocal()

        try:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

            if not profile:
                profile = UserProfile(user_id=user_id)
                db.add(profile)
                db.commit()
                logger.info(f"为用户 {user_id} 创建了默认资料")

            return profile
        except Exception as e:
            logger.error(f"获取用户资料失败: {e}")
            db.rollback()
            raise
        finally:
            if db is not None:
                db.close()

    def update_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """更新用户资料"""
        try:
            db = self.SessionLocal()
            profile = self.get_or_create_profile(user_id, db)

            # 更新允许的字段
            updateable_fields = ['bio', 'phone', 'timezone', 'language', 'theme']
            for field in updateable_fields:
                if field in profile_data:
                    setattr(profile, field, profile_data[field])

            profile.updated_at = datetime.utcnow()
            db.commit()

            # 记录活动
            self.record_activity(
                user_id,
                'settings',
                '更新了个人资料',
                {'updated_fields': list(profile_data.keys())},
                db
            )

            logger.info(f"用户 {user_id} 更新了个人资料")
            return True

        except Exception as e:
            logger.error(f"更新用户资料失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def upload_avatar(self, user_id: int, avatar_file_data: bytes, file_extension: str) -> str:
        """上传用户头像"""
        try:
            # 创建上传目录
            upload_dir = Path("uploads/avatars")
            upload_dir.mkdir(parents=True, exist_ok=True)

            # 生成唯一文件名
            file_hash = hashlib.md5(avatar_file_data).hexdigest()
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"avatar_{user_id}_{timestamp}_{file_hash[:8]}.{file_extension}"
            file_path = upload_dir / filename

            # 保存文件
            with open(file_path, "wb") as f:
                f.write(avatar_file_data)

            # 更新数据库中的头像URL
            avatar_url = f"/uploads/avatars/{filename}"
            db = self.SessionLocal()
            try:
                profile = self.get_or_create_profile(user_id, db)
                profile.avatar_url = avatar_url
                profile.updated_at = datetime.utcnow()
                db.commit()

                # 记录活动
                self.record_activity(
                    user_id,
                    'settings',
                    '上传了新头像',
                    {'avatar_url': avatar_url},
                    db
                )

            except Exception as e:
                db.rollback()
                # 删除已保存的文件
                if file_path.exists():
                    file_path.unlink()
                raise
            finally:
                db.close()

            logger.info(f"用户 {user_id} 上传了头像: {avatar_url}")
            return avatar_url

        except Exception as e:
            logger.error(f"上传头像失败: {e}")
            raise

    def get_user_statistics(self, user_id: int, period_days: int = 30) -> Dict[str, Any]:
        """获取用户统计信息"""
        try:
            db = self.SessionLocal()

            # 计算日期范围
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)

            # 获取总统计
            total_stats = db.query(
                func.sum(UserStatistics.login_count).label('total_logins'),
                func.sum(UserStatistics.trade_count).label('total_trades'),
                func.sum(UserStatistics.strategy_count).label('total_strategies'),
                func.avg(UserStatistics.performance_score).label('avg_performance'),
                func.sum(UserStatistics.active_minutes).label('total_minutes')
            ).filter(
                UserStatistics.user_id == user_id,
                UserStatistics.stat_date >= start_date
            ).first()

            # 获取今日统计
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())

            today_stats = db.query(UserStatistics).filter(
                UserStatistics.user_id == user_id,
                UserStatistics.stat_date >= today_start
            ).first()

            # 获取最近活动
            recent_activities = db.query(UserActivity).filter(
                UserActivity.user_id == user_id
            ).order_by(UserActivity.created_at.desc()).limit(10).all()

            # 计算活跃天数
            active_days = db.query(func.count(func.distinct(UserStatistics.stat_date))).filter(
                UserStatistics.user_id == user_id,
                UserStatistics.stat_date >= start_date
            ).scalar()

            return {
                'period': f'{period_days}d',
                'login_count': int(total_stats.total_logins or 0),
                'trade_count': int(total_stats.total_trades or 0),
                'strategy_count': int(total_stats.total_strategies or 0),
                'performance_score': float(total_stats.avg_performance or 0),
                'active_minutes': int(total_stats.total_minutes or 0),
                'active_days': active_days,
                'today_login_count': today_stats.login_count if today_stats else 0,
                'today_trade_count': today_stats.trade_count if today_stats else 0,
                'recent_activities': [
                    {
                        'id': activity.id,
                        'type': activity.activity_type,
                        'description': activity.description,
                        'timestamp': activity.created_at.isoformat(),
                        'metadata': activity.metadata or {}
                    }
                    for activity in recent_activities
                ]
            }

        except Exception as e:
            logger.error(f"获取用户统计失败: {e}")
            return {}
        finally:
            db.close()

    def record_activity(self, user_id: int, activity_type: str, description: str, metadata: Dict[str, Any] = None, db=None):
        """记录用户活动"""
        if db is None:
            db = self.SessionLocal()

        try:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                metadata=metadata or {}
            )

            db.add(activity)
            db.commit()

        except Exception as e:
            logger.error(f"记录用户活动失败: {e}")
            db.rollback()
        finally:
            if db is not None:
                db.close()

    def record_daily_statistics(self, user_id: int, stats_data: Dict[str, Any]):
        """记录每日统计"""
        try:
            db = self.SessionLocal()

            # 检查今天是否已有统计记录
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())

            existing_stats = db.query(UserStatistics).filter(
                UserStatistics.user_id == user_id,
                UserStatistics.stat_date >= today_start
            ).first()

            if existing_stats:
                # 更新现有记录
                for key, value in stats_data.items():
                    if hasattr(existing_stats, key):
                        setattr(existing_stats, key, value)
            else:
                # 创建新记录
                stats = UserStatistics(
                    user_id=user_id,
                    stat_date=datetime.utcnow(),
                    **stats_data
                )
                db.add(stats)

            db.commit()
            logger.info(f"记录用户 {user_id} 的每日统计")

        except Exception as e:
            logger.error(f"记录每日统计失败: {e}")
            db.rollback()
        finally:
            db.close()

    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """获取用户设置"""
        try:
            db = self.SessionLocal()

            settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

            if not settings:
                # 创建默认设置
                default_settings = {
                    'email_notifications': {
                        'system_alerts': True,
                        'security_alerts': True,
                        'trade_alerts': False,
                        'weekly_summary': True
                    },
                    'browser_notifications': {
                        'enabled': False,
                        'trade_alerts': True,
                        'system_alerts': True
                    },
                    'privacy_settings': {
                        'show_email': False,
                        'show_phone': False,
                        'show_activity': True
                    }
                }

                settings = UserSettings(
                    user_id=user_id,
                    **default_settings
                )
                db.add(settings)
                db.commit()

                return default_settings

            return {
                'email_notifications': settings.email_notifications or {},
                'browser_notifications': settings.browser_notifications or {},
                'privacy_settings': settings.privacy_settings or {}
            }

        except Exception as e:
            logger.error(f"获取用户设置失败: {e}")
            return {}
        finally:
            db.close()

    def update_user_settings(self, user_id: int, settings_data: Dict[str, Any]) -> bool:
        """更新用户设置"""
        try:
            db = self.SessionLocal()

            settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()

            if not settings:
                settings = UserSettings(user_id=user_id)
                db.add(settings)

            # 更新设置
            if 'email_notifications' in settings_data:
                settings.email_notifications = settings_data['email_notifications']
            if 'browser_notifications' in settings_data:
                settings.browser_notifications = settings_data['browser_notifications']
            if 'privacy_settings' in settings_data:
                settings.privacy_settings = settings_data['privacy_settings']

            settings.updated_at = datetime.utcnow()
            db.commit()

            # 记录活动
            self.record_activity(
                user_id,
                'settings',
                '更新了通知设置',
                {'updated_categories': list(settings_data.keys())},
                db
            )

            logger.info(f"用户 {user_id} 更新了设置")
            return True

        except Exception as e:
            logger.error(f"更新用户设置失败: {e}")
            db.rollback()
            return False
        finally:
            db.close()

# 全局用户资料服务实例
user_profile_service = UserProfileService()

# 初始化函数
def init_user_profile_service():
    """初始化用户资料服务"""
    user_profile_service.create_tables()
    logger.info("用户资料服务初始化完成")

if __name__ == "__main__":
    init_user_profile_service()