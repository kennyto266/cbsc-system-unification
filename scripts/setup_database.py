#!/usr/bin/env python3
"""
数据库初始化脚本
Database Initialization Script
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from auth_simple import auth_service
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_default_admin():
    """创建默认管理员用户"""
    try:
        db = next(auth_service.get_db())

        # 检查是否已存在管理员用户
        from auth_simple import User
        admin_user = db.query(User).filter(User.username == 'admin').first()

        if admin_user:
            logger.info("管理员用户已存在，跳过创建")
            return

        # 创建默认管理员
        admin_user = User(
            username='admin',
            email='admin@cbsc.local',
            password_hash=auth_service.hash_password('admin123'),
            is_active=True
        )

        db.add(admin_user)
        db.commit()

        logger.info("✅ 默认管理员用户创建完成")
        logger.info("   用户名: admin")
        logger.info("   密码: admin123")
        logger.info("   ⚠️  请在生产环境中修改默认密码")

    except Exception as e:
        logger.error(f"创建默认管理员失败: {e}")
        db.rollback()
    finally:
        db.close()

def create_test_user():
    """创建测试用户"""
    try:
        db = next(auth_service.get_db())

        # 检查测试用户是否存在
        from auth_simple import User
        test_user = db.query(User).filter(User.username == 'testuser').first()

        if test_user:
            logger.info("测试用户已存在，跳过创建")
            return

        # 创建测试用户
        test_user = User(
            username='testuser',
            email='test@cbsc.local',
            password_hash=auth_service.hash_password('testpass123'),
            is_active=True
        )

        db.add(test_user)
        db.commit()

        logger.info("✅ 测试用户创建完成")
        logger.info("   用户名: testuser")
        logger.info("   密码: testpass123")

    except Exception as e:
        logger.error(f"创建测试用户失败: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """主函数"""
    logger.info("🗄️  开始初始化数据库...")

    try:
        # 创建数据库表
        logger.info("📋 创建数据库表...")
        auth_service.create_tables()
        logger.info("✅ 数据库表创建完成")

        # 创建默认管理员用户
        create_default_admin()

        # 创建测试用户
        create_test_user()

        logger.info("🎉 数据库初始化完成！")
        logger.info("")
        logger.info("🚀 下一步:")
        logger.info("1. 启动API服务: python src/api/main.py")
        logger.info("2. 访问API文档: http://localhost:3004/docs")
        logger.info("3. 使用管理员账户登录测试")

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()