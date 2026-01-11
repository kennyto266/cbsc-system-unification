"""
数据库配置模块
"""

import sqlite3
import os
import json
from pathlib import Path
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 数据库文件路径
DB_PATH = "data/persistent_context_storage.db"

def get_db_connection():
    """获取数据库连接"""
    # 确保数据目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
    return conn

def init_database():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 创建上下文存储表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_storage (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                context_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,  -- JSON格式存储元数据
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        # 创建用户配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT NOT NULL,
                setting_type TEXT DEFAULT 'string',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, setting_key)
            )
        """)

        # 创建会话管理表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_management (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_name TEXT,
                session_metadata TEXT,  -- JSON格式存储会话元数据
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)

        # 创建上下文标签表（用于分类和搜索）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_id TEXT NOT NULL,
                tag_name TEXT NOT NULL,
                tag_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES context_storage(id) ON DELETE CASCADE,
                UNIQUE(context_id, tag_name)
            )
        """)

        # 创建上下文关系表（用于建立上下文之间的关联）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_context_id TEXT NOT NULL,
                child_context_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                relationship_metadata TEXT,  -- JSON格式存储关系元数据
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_context_id) REFERENCES context_storage(id) ON DELETE CASCADE,
                FOREIGN KEY (child_context_id) REFERENCES context_storage(id) ON DELETE CASCADE,
                UNIQUE(parent_context_id, child_context_id, relationship_type)
            )
        """)

        # 创建搜索索引表（用于快速检索）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_search_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_id TEXT NOT NULL,
                content_text TEXT NOT NULL,
                tokens TEXT,  -- JSON数组存储分词结果
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES context_storage(id) ON DELETE CASCADE
            )
        """)

        # 创建访问日志表（用于审计和分析）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                access_metadata TEXT,  -- JSON格式存储访问元数据
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES context_storage(id)
            )
        """)

        # 创建索引以提高查询性能
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_storage_user_session ON context_storage(user_id, session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_storage_type_active ON context_storage(context_type, is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_storage_expires ON context_storage(expires_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_settings_user ON user_settings(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_management_user ON session_management(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_tags_name ON context_tags(tag_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_context_search_content ON context_search_index(content_text)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_context ON access_logs(context_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_user ON access_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp ON access_logs(timestamp)")

        conn.commit()
        print("数据库初始化完成")

    except Exception as e:
        print(f"数据库初始化失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def cleanup_expired_contexts():
    """清理过期的上下文"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 删除过期的上下文
        cursor.execute("""
            DELETE FROM context_storage
            WHERE expires_at IS NOT NULL AND expires_at < datetime('now')
        """)

        deleted_count = cursor.rowcount

        # 清理孤立的数据（删除不存在的上下文相关数据）
        cursor.execute("DELETE FROM context_tags WHERE context_id NOT IN (SELECT id FROM context_storage)")
        cursor.execute("DELETE FROM context_relationships WHERE parent_context_id NOT IN (SELECT id FROM context_storage)")
        cursor.execute("DELETE FROM context_relationships WHERE child_context_id NOT IN (SELECT id FROM context_storage)")
        cursor.execute("DELETE FROM context_search_index WHERE context_id NOT IN (SELECT id FROM context_storage)")

        conn.commit()
        print(f"清理完成，删除了 {deleted_count} 条过期记录")
        return deleted_count

    except Exception as e:
        print(f"清理过期上下文失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def vacuum_database():
    """优化数据库"""
    conn = get_db_connection()

    try:
        conn.execute("VACUUM")
        print("数据库优化完成")

    except Exception as e:
        print(f"数据库优化失败: {e}")
        raise
    finally:
        conn.close()

# SQLAlchemy配置
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 创建SQLAlchemy引擎
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 设置为True可以看到SQL日志
    pool_pre_ping=True,  # 连接池预检查
    connect_args={
        "check_same_thread": False,  # SQLite特有配置，允许多线程访问
        "timeout": 20  # 连接超时时间
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型类
Base = declarative_base()

@contextmanager
def get_database_session():
    """
    获取数据库会话的上下文管理器

    Returns:
        Session: SQLAlchemy会话对象
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_db():
    """获取数据库会话 - 用于FastAPI依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_sqlalchemy_database():
    """初始化SQLAlchemy数据库表"""
    try:
        # 导入所有模型以确保它们被注册到Base.metadata
        from models.context import Context, ContextTag, ContextShare, ContextAccess
        from models.tag import Tag, ContextTagAssociation, TagSuggestion, TagRule, TagStats
        from models.user import User, Team, UserTeamAssociation, Permission

        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("SQLAlchemy数据库初始化完成")
        return True
    except Exception as e:
        print(f"SQLAlchemy数据库初始化失败: {e}")
        return False

if __name__ == "__main__":
    # 初始化原有的数据库
    init_database()
    # 初始化SQLAlchemy数据库
    init_sqlalchemy_database()