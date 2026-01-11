#!/usr/bin/env python3
"""
CBSC數據遷移執行腳本

一鍵執行完整的數據遷移流程，將現有CBSC系統數據遷移到統一模型。
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 設置環境變量
os.environ.setdefault('PYTHONPATH', str(project_root))

from src.migrations.data_migration_executor import DataMigrationExecutor, main
from src.migrations.migration_manager import MigrationManager
from src.database.connection import db_manager

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cbsc_migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_migration_prerequisites():
    """檢查遷移先決條件"""
    print("檢查遷移先決條件...")

    # 1. 檢查Python版本
    if sys.version_info < (3, 8):
        print("❌ 錯誤: 需要Python 3.8或更高版本")
        return False
    print("✓ Python版本檢查通過")

    # 2. 檢查必要的目錄
    required_dirs = [
        'src',
        'src/migrations',
        'src/models',
        'src/database'
    ]

    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"❌ 錯誤: 缺少目錄 {dir_path}")
            return False
    print("✓ 目錄結構檢查通過")

    # 3. 檢查必要的文件
    required_files = [
        'src/migrations/data_migration_executor.py',
        'src/migrations/migration_manager.py',
        'src/models/__init__.py'
    ]

    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ 錯誤: 缺少文件 {file_path}")
            return False
    print("✓ 必要文件檢查通過")

    # 4. 檢查數據源
    data_sources = []
    pattern_patterns = [
        "*_backtest_results_*.json",
        "*optimization_results_*.json",
        "*.csv"
    ]

    for pattern in pattern_patterns:
        files = list(Path('.').glob(pattern))
        if files:
            data_sources.extend([str(f) for f in files])

    if not data_sources:
        print("⚠️ 警告: 未找到數據源文件，遷移可能不完整")
    else:
        print(f"✓ 找到 {len(data_sources)} 個數據源文件")

    return True

def show_migration_menu():
    """顯示遷移菜單"""
    print("\n" + "="*60)
    print("CBSC 系統數據遷移工具")
    print("="*60)
    print("1. 執行完整遷移 (推薦)")
    print("2. 僅創建數據庫模式")
    print("3. 僅遷移策略數據")
    print("4. 僅遷移市場數據")
    print("5. 僅遷移用戶數據")
    print("6. 驗證遷移結果")
    print("7. 查看遷移狀態")
    print("8. 退出")
    print("="*60)

async def execute_full_migration():
    """執行完整遷移"""
    print("\n開始執行完整數據遷移...")
    print("這將包括:")
    print("  - 創建統一數據庫模式")
    print("  - 遷移策略數據")
    print("  - 遷移市場數據")
    print("  - 遷移用戶和系統配置")

    confirm = input("\n確認執行完整遷移? (y/N): ").lower().strip()
    if confirm != 'y':
        print("遷移已取消")
        return

    try:
        executor = DataMigrationExecutor()
        report = await executor.execute_full_migration()

        if report["summary"]["failed_migrations"] == 0:
            print("\n🎉 遷移成功完成!")
            print(f"執行時間: {report['summary']['total_execution_time_ms']:.2f} ms")
            print(f"成功遷移: {report['summary']['successful_migrations']}/{report['summary']['total_migrations']}")
        else:
            print("\n❌ 遷移部分失敗")
            print(f"失敗遷移: {report['summary']['failed_migrations']}")
            print("請檢查錯誤日誌並重試")

    except Exception as e:
        print(f"\n❌ 遷移執行失敗: {e}")
        logger.error(f"Full migration failed: {e}")

async def execute_schema_only():
    """僅執行數據庫模式創建"""
    print("\n創建統一數據庫模式...")

    try:
        from src.migrations.scripts.001_create_unified_schema import migration

        async with db_manager.get_async_session() as session:
            # 檢查是否已執行
            manager = MigrationManager()
            if await manager.is_migration_executed(migration.version):
                print("✓ 數據庫模式已存在")
                return

            # 執行SQL
            up_sql = migration.get_up_sql()
            await session.execute(up_sql)
            await session.commit()

            # 記錄遷移
            await manager.record_migration_execution(session, migration, {"success": True})

            print("✓ 數據庫模式創建成功")

    except Exception as e:
        print(f"❌ 數據庫模式創建失敗: {e}")

async def execute_strategy_migration():
    """僅執行策略數據遷移"""
    print("\n遷移策略數據...")

    try:
        from src.migrations.scripts.002_migrate_strategy_data import migration

        async with db_manager.get_async_session() as session:
            result = await migration.execute_migration(session)
            await session.commit()

            if result.get("success", False):
                print("✓ 策略數據遷移成功")
                print(f"  策略: {result.get('strategies_migrated', 0)}")
                print(f"  配置: {result.get('configs_migrated', 0)}")
                print(f"  性能記錄: {result.get('performance_records_migrated', 0)}")
            else:
                print("❌ 策略數據遷移失敗")
                if "errors" in result:
                    for error in result["errors"]:
                        print(f"  錯誤: {error}")

    except Exception as e:
        print(f"❌ 策略數據遷移執行失敗: {e}")

async def execute_market_migration():
    """僅執行市場數據遷移"""
    print("\n遷移市場數據...")

    try:
        from src.migrations.scripts.003_migrate_market_data import migration

        async with db_manager.get_async_session() as session:
            result = await migration.execute_migration(session)
            await session.commit()

            if result.get("success", False):
                print("✓ 市場數據遷移成功")
                print(f"  市場數據: {result.get('market_data_migrated', 0)}")
                print(f"  技術指標: {result.get('technical_indicators_migrated', 0)}")
                print(f"  情緒數據: {result.get('sentiment_data_migrated', 0)}")
            else:
                print("❌ 市場數據遷移失敗")
                if "errors" in result:
                    for error in result["errors"]:
                        print(f"  錯誤: {error}")

    except Exception as e:
        print(f"❌ 市場數據遷移執行失敗: {e}")

async def execute_user_migration():
    """僅執行用戶數據遷移"""
    print("\n遷移用戶和系統數據...")

    try:
        from src.migrations.scripts.004_migrate_user_data import migration

        async with db_manager.get_async_session() as session:
            result = await migration.execute_migration(session)
            await session.commit()

            if result.get("success", False):
                print("✓ 用戶數據遷移成功")
                print(f"  用戶: {result.get('users_created', 0)}")
                print(f"  角色: {result.get('roles_created', 0)}")
                print(f"  系統配置: {result.get('system_configs_migrated', 0)}")
                print(f"  審計日誌: {result.get('audit_logs_created', 0)}")
            else:
                print("❌ 用戶數據遷移失敗")
                if "errors" in result:
                    for error in result["errors"]:
                        print(f"  錯誤: {error}")

    except Exception as e:
        print(f"❌ 用戶數據遷移執行失敗: {e}")

async def validate_migration():
    """驗證遷移結果"""
    print("\n驗證遷移結果...")

    try:
        async with db_manager.get_async_session() as session:
            # 檢查表和記錄數量
            tables_to_check = [
                ("users", "用戶"),
                ("roles", "角色"),
                ("strategies", "策略"),
                ("strategy_performance", "策略性能"),
                ("market_data", "市場數據"),
                ("technical_indicators", "技術指標"),
                ("system_config", "系統配置"),
                ("audit_logs", "審計日誌")
            ]

            print("\n遷移結果驗證報告:")
            print("-" * 50)

            for table_name, display_name in tables_to_check:
                try:
                    result = await session.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = result.scalar()
                    status = "✓" if count > 0 else "⚠️"
                    print(f"{status} {display_name} ({table_name}): {count:,} 條記錄")
                except Exception as e:
                    print(f"❌ {display_name} ({table_name}): 檢查失敗 - {e}")

            print("-" * 50)

            # 檢查遷移歷史
            try:
                result = await session.execute("SELECT version, name, executed_at FROM migration_history ORDER BY executed_at")
                migrations = result.fetchall()

                print(f"\n遷移歷史記錄 ({len(migrations)} 條):")
                for version, name, executed_at in migrations:
                    print(f"  ✓ {version} - {name} - {executed_at}")

            except Exception as e:
                print(f"\n❌ 遷移歷史檢查失敗: {e}")

    except Exception as e:
        print(f"❌ 驗證失敗: {e}")

async def show_migration_status():
    """顯示遷移狀態"""
    print("\n遷移狀態檢查...")

    try:
        manager = MigrationManager()

        # 檢查待執行的遷移
        pending_migrations = await manager.get_pending_migrations()

        print(f"待執行遷移: {len(pending_migrations)}")
        for migration in pending_migrations:
            print(f"  - {migration.version}: {migration.name}")

        # 檢查已執行的遷移
        executed_migrations = await manager.get_executed_migrations()

        print(f"已執行遷移: {len(executed_migrations)}")
        for migration in executed_migrations:
            print(f"  ✓ {migration.version}: {migration.name} - {migration.executed_at}")

    except Exception as e:
        print(f"❌ 狀態檢查失敗: {e}")

async def main_menu():
    """主菜單循環"""
    # 檢查先決條件
    if not check_migration_prerequisites():
        print("\n無法繼續遷移，請解決上述問題後重試")
        return

    while True:
        show_migration_menu()

        try:
            choice = input("\n請選擇操作 (1-8): ").strip()

            if choice == '1':
                await execute_full_migration()
            elif choice == '2':
                await execute_schema_only()
            elif choice == '3':
                await execute_strategy_migration()
            elif choice == '4':
                await execute_market_migration()
            elif choice == '5':
                await execute_user_migration()
            elif choice == '6':
                await validate_migration()
            elif choice == '7':
                await show_migration_status()
            elif choice == '8':
                print("\n退出遷移工具")
                break
            else:
                print("\n無效選擇，請輸入 1-8")

        except KeyboardInterrupt:
            print("\n\n用戶中斷，退出遷移工具")
            break
        except Exception as e:
            print(f"\n操作執行錯誤: {e}")
            logger.error(f"Menu operation error: {e}")

        input("\n按回車鍵繼續...")

def run_direct_migration():
    """直接運行完整遷移（命令行模式）"""
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        print("執行直接完整遷移...")
        if check_migration_prerequisites():
            asyncio.run(execute_full_migration())
        else:
            print("先決條件檢查失敗")
            sys.exit(1)
    else:
        # 顯示菜單
        asyncio.run(main_menu())

if __name__ == "__main__":
    try:
        run_direct_migration()
    except Exception as e:
        print(f"遷移工具啟動失敗: {e}")
        logger.error(f"Migration tool startup failed: {e}")
        sys.exit(1)