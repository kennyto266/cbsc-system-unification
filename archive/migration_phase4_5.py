#!/usr / bin / env python3
"""
架構遷移階段4和階段5執行腳本
階段4: 遷移API / Application
階段5: 遷移Domain模組
"""

import os
import shutil
import datetime
from pathlib import Path
import json
from typing import List, Dict, Any

# 配置
BACKUP_DIR = f"migration_backup_{datetime.datetime.now().strftime('%Y % m % d_ % H % M % S')}"
LOG_FILE = f"migration_log_{datetime.datetime.now().strftime('%Y % m % d_ % H % M % S')}.json"

def log_operation(operation: str, details: Dict[str, Any]):
    """記錄操作日誌"""
    with open(LOG_FILE, 'w', encoding='utf - 8') as f:
        json.dump({
            'timestamp': datetime.datetime.now().isoformat(),
            'operation': operation,
            'details': details
        }, f, ensure_ascii=False, indent=2)

def scan_directory(path: str, max_depth: int = 3) -> Dict[str, Any]:
    """掃描目錄結構"""
    result = {
        'path': path,
        'exists': os.path.exists(path),
        'type': 'directory' if os.path.isdir(path) else 'file',
        'contents': []
    }

    if os.path.isdir(path) and max_depth > 0:
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                result['contents'].append({
                    'name': item,
                    'path': item_path,
                    'is_dir': os.path.isdir(item_path),
                    'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                })
        except Exception as e:
            result['error'] = str(e)

    return result

def backup_files(files: List[str], backup_path: str):
    """備份文件"""
    if not os.path.exists(backup_path):
        os.makedirs(backup_path, exist_ok=True)

    for file in files:
        if os.path.exists(file):
            dest = os.path.join(backup_path, os.path.basename(file))
            shutil.copy2(file, dest)
            print(f"✓ 備份: {file} -> {dest}")
    return True

def move_files(files: List[str], dest_dir: str):
    """移動文件到目標目錄"""
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
        print(f"✓ 創建目錄: {dest_dir}")

    for file in files:
        if os.path.exists(file):
            dest = os.path.join(dest_dir, os.path.basename(file))
            shutil.move(file, dest)
            print(f"✓ 移動: {file} -> {dest}")
    return True

def find_imports(file_path: str) -> List[str]:
    """查找文件中的導入語句"""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf - 8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    imports.append(line)
    except Exception as e:
        print(f"✗ 讀取文件失敗 {file_path}: {e}")
    return imports

def update_imports(file_path: str, old_path: str, new_path: str):
    """更新文件中的導入路徑"""
    try:
        with open(file_path, 'r', encoding='utf - 8') as f:
            content = f.read()

        original_content = content
        content = content.replace(old_path, new_path)

        if content != original_content:
            with open(file_path, 'w', encoding='utf - 8') as f:
                f.write(content)
            print(f"✓ 更新導入: {file_path}")
            return True
    except Exception as e:
        print(f"✗ 更新失敗 {file_path}: {e}")
    return False

def phase4_migrate_api():
    """階段4: 遷移API / Application"""
    print("\n" + "="*60)
    print("階段4: 遷移API / Application")
    print("="*60)

    api_source = "src / api"
    api_target = "src / application / services / api"

    # 步驟1: 掃描api目錄
    print(f"\n步驟1: 掃描 {api_source} 目錄")
    api_structure = scan_directory(api_source)
    log_operation("phase4_scan_api", api_structure)

    if not api_structure['exists']:
        print(f"✗ 目錄不存在: {api_source}")
        return False

    # 收集所有Python文件
    api_files = []
    for root, dirs, files in os.walk(api_source):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                api_files.append(file_path)

    print(f"✓ 找到 {len(api_files)} 個Python文件")

    # 步驟2: 備份原始文件
    print(f"\n步驟2: 備份到 {BACKUP_DIR}")
    backup_files(api_files, os.path.join(BACKUP_DIR, "phase4_api_backup"))

    # 步驟3: 移動到新位置
    print(f"\n步驟3: 移動到 {api_target}")
    for file in api_files:
        dest_dir = api_target
        if os.path.dirname(file) != api_source:
            # 保持子目錄結構
            rel_path = os.path.relpath(file, api_source)
            dest_dir = os.path.join(api_target, os.path.dirname(rel_path))

        move_files([file], dest_dir)

    # 步驟4: 更新導入路徑（後續在測試中處理）
    print("\n步驟4: 準備更新導入路徑")
    for file in api_files:
        new_path = file.replace(api_source, api_target)
        if os.path.exists(new_path):
            imports = find_imports(new_path)
            log_operation("phase4_file_imports", {
                'file': new_path,
                'imports': imports
            })

    print("\n✓ 階段4完成")
    return True

def phase5_migrate_domain():
    """階段5: 遷移Domain模組"""
    print("\n" + "="*60)
    print("階段5: 遷移Domain模組")
    print("="*60)

    strategies_source = "src / strategies"
    strategies_target = "src / domain / strategy"

    # 步驟1: 掃描domain相關目錄
    print("\n步驟1: 掃描相關目錄")

    # 掃描現有的domain目錄
    domain_structure = scan_directory("src / domain")
    log_operation("phase5_scan_domain", domain_structure)

    # 掃描strategies目錄
    strategies_structure = scan_directory(strategies_source)
    log_operation("phase5_scan_strategies", strategies_structure)

    # 步驟2: 備份原始文件
    if strategies_structure['exists']:
        strategy_files = []
        for root, dirs, files in os.walk(strategies_source):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    strategy_files.append(file_path)

        print(f"\n步驟2: 備份到 {BACKUP_DIR}")
        backup_files(strategy_files, os.path.join(BACKUP_DIR, "phase5_strategies_backup"))

        # 步驟3: 移動到新位置
        print(f"\n步驟3: 移動到 {strategies_target}")
        for file in strategy_files:
            dest_dir = strategies_target
            if os.path.dirname(file) != strategies_source:
                rel_path = os.path.relpath(file, strategies_source)
                dest_dir = os.path.join(strategies_target, os.path.dirname(rel_path))

            move_files([file], dest_dir)

    # 步驟4: 檢查其他domain模組
    print("\n步驟4: 檢查其他domain模組")
    domain_files = []
    for root, dirs, files in os.walk("src"):
        if 'domain' in os.path.basename(root):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    domain_files.append(file_path)

    print(f"✓ 找到 {len(domain_files)} 個domain相關文件")

    # 步驟5: 記錄所有遷移的文件
    all_migrated = []
    for root, dirs, files in os.walk("src / domain"):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                all_migrated.append(file_path)

    log_operation("phase5_migration_complete", {
        'migrated_files': all_migrated,
        'count': len(all_migrated)
    })

    print("\n✓ 階段5完成")
    return True

def main():
    """主執行函數"""
    print("\n" + "="*60)
    print("架構遷移 - 階段4和階段5")
    print(f"開始時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # 創建備份目錄
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print(f"✓ 創建備份目錄: {BACKUP_DIR}")

    # 執行遷移
    try:
        phase4_success = phase4_migrate_api()
        phase5_success = phase5_migrate_domain()

        # 生成報告
        report = {
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'phases_completed': [4, 5] if (phase4_success and phase5_success) else [],
            'backup_directory': BACKUP_DIR,
            'log_file': LOG_FILE,
            'status': 'success' if (phase4_success and phase5_success) else 'partial'
        }

        with open(f"migration_report_{datetime.datetime.now().strftime('%Y % m % d_ % H % M % S')}.json", 'w', encoding='utf - 8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print("\n" + "="*60)
        print("遷移完成")
        print(f"報告: {report['log_file']}")
        print(f"備份: {BACKUP_DIR}")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 遷移失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    main()
