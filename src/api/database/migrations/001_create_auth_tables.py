"""
认证相关表的数据库迁移脚本
Migration script for authentication tables

创建用户认证和权限管理所需的数据库表
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_auth_tables(engine):
    """创建认证相关的表"""

    # 创建角色表
    create_roles_table = """
    CREATE TABLE IF NOT EXISTS roles (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) UNIQUE NOT NULL,
        description TEXT,
        is_system_role BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # 创建权限表
    create_permissions_table = """
    CREATE TABLE IF NOT EXISTS permissions (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) UNIQUE NOT NULL,
        resource VARCHAR(50) NOT NULL,
        action VARCHAR(50) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # 创建用户角色关联表
    create_user_roles_table = """
    CREATE TABLE IF NOT EXISTS user_roles (
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        assigned_by INTEGER REFERENCES users(id),
        PRIMARY KEY (user_id, role_id)
    );
    """

    # 创建角色权限关联表
    create_role_permissions_table = """
    CREATE TABLE IF NOT EXISTS role_permissions (
        role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
        permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (role_id, permission_id)
    );
    """

    # 创建用户表（如果不存在）
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        is_verified BOOLEAN DEFAULT FALSE,
        is_superuser BOOLEAN DEFAULT FALSE,
        mfa_enabled BOOLEAN DEFAULT FALSE,
        mfa_secret VARCHAR(255),
        backup_codes TEXT,
        failed_login_attempts INTEGER DEFAULT 0,
        locked_until TIMESTAMP,
        password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # 创建登录历史表
    create_login_history_table = """
    CREATE TABLE IF NOT EXISTS login_history (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        ip_address VARCHAR(45),
        user_agent TEXT,
        device_info TEXT,
        location VARCHAR(100),
        success BOOLEAN DEFAULT TRUE,
        failure_reason VARCHAR(100),
        login_type VARCHAR(20) DEFAULT 'password',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # 创建用户会话表
    create_user_sessions_table = """
    CREATE TABLE IF NOT EXISTS user_sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        session_token VARCHAR(255) UNIQUE NOT NULL,
        refresh_token VARCHAR(255) UNIQUE NOT NULL,
        device_name VARCHAR(100),
        device_type VARCHAR(50),
        ip_address VARCHAR(45),
        is_active BOOLEAN DEFAULT TRUE,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # 创建社交账号关联表
    create_social_accounts_table = """
    CREATE TABLE IF NOT EXISTS social_accounts (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        provider VARCHAR(50) NOT NULL,
        provider_id VARCHAR(255) NOT NULL,
        access_token TEXT,
        refresh_token TEXT,
        email VARCHAR(255),
        name VARCHAR(100),
        avatar_url VARCHAR(500),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # 创建审计日志表
    create_audit_logs_table = """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        action VARCHAR(100) NOT NULL,
        resource_type VARCHAR(50),
        resource_id INTEGER,
        old_values JSONB,
        new_values JSONB,
        ip_address VARCHAR(45),
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # 创建索引
    create_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON login_history(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_login_history_created_at ON login_history(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_refresh_token ON user_sessions(refresh_token);",
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);",
        "CREATE INDEX IF NOT EXISTS idx_social_accounts_user_id ON social_accounts(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_social_accounts_provider ON social_accounts(provider);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);"
    ]

    # 创建触发器自动更新updated_at字段
    create_triggers = [
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """,
        """
        DROP TRIGGER IF EXISTS update_users_updated_at ON users;
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
    ]

    try:
        with engine.connect() as conn:
            # 创建表
            conn.execute(text(create_users_table))
            conn.execute(text(create_roles_table))
            conn.execute(text(create_permissions_table))
            conn.execute(text(create_user_roles_table))
            conn.execute(text(create_role_permissions_table))
            conn.execute(text(create_login_history_table))
            conn.execute(text(create_user_sessions_table))
            conn.execute(text(create_social_accounts_table))
            conn.execute(text(create_audit_logs_table))

            # 创建索引
            for index_sql in create_indexes:
                conn.execute(text(index_sql))

            # 创建触发器（仅PostgreSQL）
            if engine.dialect.name == 'postgresql':
                for trigger_sql in create_triggers:
                    conn.execute(text(trigger_sql))

            conn.commit()
            logger.info("认证相关表创建成功")

    except Exception as e:
        logger.error(f"创建认证表失败: {e}")
        raise

def insert_default_data(engine):
    """插入默认的权限和角色数据"""

    # 默认权限
    default_permissions = [
        # 用户管理权限
        ("user:create", "user", "create", "创建用户"),
        ("user:read", "user", "read", "查看用户信息"),
        ("user:update", "user", "update", "更新用户信息"),
        ("user:delete", "user", "delete", "删除用户"),
        ("user:list", "user", "list", "列出所有用户"),

        # 角色管理权限
        ("role:create", "role", "create", "创建角色"),
        ("role:read", "role", "read", "查看角色信息"),
        ("role:update", "role", "update", "更新角色信息"),
        ("role:delete", "role", "delete", "删除角色"),
        ("role:list", "role", "list", "列出所有角色"),
        ("role:assign", "role", "assign", "分配角色"),

        # 策略管理权限
        ("strategy:create", "strategy", "create", "创建策略"),
        ("strategy:read", "strategy", "read", "查看策略"),
        ("strategy:update", "strategy", "update", "更新策略"),
        ("strategy:delete", "strategy", "delete", "删除策略"),
        ("strategy:execute", "strategy", "execute", "执行策略"),
        ("strategy:backtest", "strategy", "backtest", "回测策略"),

        # 系统管理权限
        ("system:config", "system", "config", "系统配置"),
        ("system:monitor", "system", "monitor", "系统监控"),
        ("system:backup", "system", "backup", "系统备份"),
        ("system:restore", "system", "restore", "系统恢复"),
        ("system:logs", "system", "logs", "查看系统日志"),

        # 数据管理权限
        ("data:read", "data", "read", "读取数据"),
        ("data:write", "data", "write", "写入数据"),
        ("data:import", "data", "import", "导入数据"),
        ("data:export", "data", "export", "导出数据"),

        # 报表权限
        ("report:view", "report", "view", "查看报表"),
        ("report:create", "report", "create", "创建报表"),
        ("report:export", "report", "export", "导出报表"),
    ]

    # 默认角色
    default_roles = [
        ("superuser", "超级管理员", True, [
            "user:create", "user:read", "user:update", "user:delete", "user:list",
            "role:create", "role:read", "role:update", "role:delete", "role:list", "role:assign",
            "strategy:create", "strategy:read", "strategy:update", "strategy:delete", "strategy:execute", "strategy:backtest",
            "system:config", "system:monitor", "system:backup", "system:restore", "system:logs",
            "data:read", "data:write", "data:import", "data:export",
            "report:view", "report:create", "report:export"
        ]),

        ("admin", "管理员", True, [
            "user:read", "user:list",
            "role:read", "role:list",
            "strategy:create", "strategy:read", "strategy:update", "strategy:execute", "strategy:backtest",
            "system:monitor",
            "data:read", "data:write", "data:import",
            "report:view", "report:create", "report:export"
        ]),

        ("strategist", "策略师", False, [
            "strategy:create", "strategy:read", "strategy:update", "strategy:execute", "strategy:backtest",
            "data:read", "data:import",
            "report:view", "report:create", "report:export"
        ]),

        ("analyst", "分析师", False, [
            "strategy:read", "strategy:backtest",
            "data:read", "data:import",
            "report:view", "report:create", "report:export"
        ]),

        ("viewer", "访客", False, [
            "strategy:read",
            "data:read",
            "report:view"
        ])
    ]

    try:
        with engine.connect() as conn:
            # 插入权限
            for perm_name, resource, action, description in default_permissions:
                conn.execute(text("""
                    INSERT INTO permissions (name, resource, action, description)
                    VALUES (:name, :resource, :action, :description)
                    ON CONFLICT (name) DO NOTHING
                """), {
                    "name": perm_name,
                    "resource": resource,
                    "action": action,
                    "description": description
                })

            # 插入角色和关联权限
            for role_name, role_desc, is_system, permissions in default_roles:
                # 插入角色
                result = conn.execute(text("""
                    INSERT INTO roles (name, description, is_system_role)
                    VALUES (:name, :description, :is_system)
                    ON CONFLICT (name) DO NOTHING
                    RETURNING id
                """), {
                    "name": role_name,
                    "description": role_desc,
                    "is_system": is_system
                })

                # 获取角色ID
                role_id = conn.execute(text(
                    "SELECT id FROM roles WHERE name = :name"
                ), {"name": role_name}).scalar()

                if role_id and permissions:
                    # 为角色分配权限
                    for perm_name in permissions:
                        perm_id = conn.execute(text(
                            "SELECT id FROM permissions WHERE name = :name"
                        ), {"name": perm_name}).scalar()

                        if perm_id:
                            conn.execute(text("""
                                INSERT INTO role_permissions (role_id, permission_id)
                                VALUES (:role_id, :perm_id)
                                ON CONFLICT (role_id, permission_id) DO NOTHING
                            """), {
                                "role_id": role_id,
                                "perm_id": perm_id
                            })

            conn.commit()
            logger.info("默认权限和角色数据插入成功")

    except Exception as e:
        logger.error(f"插入默认数据失败: {e}")
        raise

def create_admin_user(engine, username: str = "admin", email: str = "admin@cbsc.com", password: str = None):
    """创建默认管理员用户"""
    if not password:
        password = "admin123"  # 默认密码，生产环境应该修改

    # 导入密码管理器
    from src.api.services.auth import PasswordManager

    password_manager = PasswordManager()
    password_hash = password_manager.hash_password(password)

    try:
        with engine.connect() as conn:
            # 插入管理员用户
            result = conn.execute(text("""
                INSERT INTO users (username, email, password_hash, is_active, is_verified, is_superuser)
                VALUES (:username, :email, :password_hash, :is_active, :is_verified, :is_superuser)
                ON CONFLICT (username) DO NOTHING
                RETURNING id
            """), {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "is_active": True,
                "is_verified": True,
                "is_superuser": True
            })

            user_id = result.scalar()

            if user_id:
                # 获取超级管理员角色ID
                role_id = conn.execute(text(
                    "SELECT id FROM roles WHERE name = 'superuser'"
                )).scalar()

                if role_id:
                    # 分配超级管理员角色
                    conn.execute(text("""
                        INSERT INTO user_roles (user_id, role_id)
                        VALUES (:user_id, :role_id)
                        ON CONFLICT (user_id, role_id) DO NOTHING
                    """), {
                        "user_id": user_id,
                        "role_id": role_id
                    })

                logger.info(f"默认管理员用户 {username} 创建成功")
                return user_id
            else:
                logger.info(f"管理员用户 {username} 已存在")
                return conn.execute(text(
                    "SELECT id FROM users WHERE username = :username"
                ), {"username": username}).scalar()

            conn.commit()

    except Exception as e:
        logger.error(f"创建管理员用户失败: {e}")
        raise

def run_migration(database_url: str = None):
    """运行认证相关的数据库迁移"""
    if not database_url:
        database_url = os.getenv("DATABASE_URL", "sqlite:///./cbsc_quant.db")

    # 创建数据库引擎
    engine = create_engine(database_url)

    try:
        # 创建表
        create_auth_tables(engine)

        # 插入默认数据
        insert_default_data(engine)

        # 创建默认管理员
        create_admin_user(engine)

        logger.info("认证系统数据库迁移完成")

    except Exception as e:
        logger.error(f"认证系统数据库迁移失败: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行迁移
    run_migration()