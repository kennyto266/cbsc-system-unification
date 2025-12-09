#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU配置遷移工具
幫助用戶從舊配置遷移到新的GPU加速配置
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

def backup_existing_config(config_path: str) -> str:
    """備份現有配置文件"""
    if os.path.exists(config_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{config_path}.backup_{timestamp}"
        shutil.copy2(config_path, backup_path)
        print(f"已備份現有配置到: {backup_path}")
        return backup_path
    return ""

def migrate_from_data_sources_config(old_config_path: str, new_config_path: str) -> bool:
    """從舊的data_sources.yml遷移到GPU配置"""
    try:
        import yaml

        # 讀取舊配置
        with open(old_config_path, 'r', encoding='utf-8') as f:
            old_config = yaml.safe_load(f)

        # 讀取新的GPU配置模板
        new_config_path_template = os.path.join(os.path.dirname(__file__), 'config', 'gpu_ta_config.yaml')
        with open(new_config_path_template, 'r', encoding='utf-8') as f:
            new_config = yaml.safe_load(f)

        # 遷移數據源配置
        if 'sources' in old_config:
            print("遷移數據源配置...")
            for source_name, source_config in old_config['sources'].items():
                if source_name in new_config['data_sources']['government_data']:
                    # 保留用戶的自定義設置
                    if 'enabled' in source_config:
                        new_config['data_sources']['government_data'][source_name]['enabled'] = source_config['enabled']
                    if 'api' in source_config:
                        new_config['data_sources']['government_data'][source_name].update(source_config['api'])

        # 遷移系統配置
        if 'system' in old_config:
            print("遷移系統配置...")
            if 'multiprocessing' in old_config['system']:
                new_config['optimization']['settings']['max_workers'] = old_config['system']['multiprocessing'].get('max_workers', 32)
            if 'monitoring' in old_config['system']:
                if 'logging_level' in old_config['system']['monitoring']:
                    new_config['performance_monitoring']['logging']['level'] = old_config['system']['monitoring']['logging_level']

        # 遷移緩存配置
        if 'system' in old_config and 'caching' in old_config['system']:
            print("遷移緩存配置...")
            new_config['system']['caching'].update(old_config['system']['caching'])

        # 保存新配置
        with open(new_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True, indent=2)

        print(f"配置遷移完成: {old_config_path} -> {new_config_path}")
        return True

    except Exception as e:
        print(f"配置遷移失敗: {e}")
        return False

def create_sample_config(output_path: str) -> bool:
    """創建示例配置文件"""
    try:
        import yaml

        # 讀取GPU配置模板
        template_path = os.path.join(os.path.dirname(__file__), 'config', 'gpu_ta_config.yaml')
        with open(template_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 為示例添加註釋
        config['_comments'] = {
            'purpose': 'GPU加速非價格TA回測系統配置文件',
            'created': datetime.now().isoformat(),
            'usage': '修改此文件以自定義系統行為'
        }

        # 保存示例配置
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)

        print(f"示例配置已創建: {output_path}")
        return True

    except Exception as e:
        print(f"創建示例配置失敗: {e}")
        return False

def validate_config(config_path: str) -> bool:
    """驗證配置文件格式"""
    try:
        import yaml

        print(f"驗證配置文件: {config_path}")

        # 嘗試加載配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 檢查必需的節點
        required_sections = ['gpu', 'data_sources', 'vectorbt', 'optimization']
        missing_sections = [section for section in required_sections if section not in config]

        if missing_sections:
            print(f"❌ 缺少必需的配置節: {', '.join(missing_sections)}")
            return False

        # 檢查GPU配置
        gpu_config = config.get('gpu', {})
        if not isinstance(gpu_config.get('detection', {}), dict):
            print("❌ GPU detection配置格式錯誤")
            return False

        # 檢查數據源配置
        data_sources = config.get('data_sources', {})
        if 'government_data' not in data_sources:
            print("❌ 缺少government_data配置")
            return False

        # 檢查VectorBT配置
        vectorbt_config = config.get('vectorbt', {})
        if 'strategies' not in vectorbt_config:
            print("❌ 缺少VectorBT策略配置")
            return False

        print("✅ 配置文件驗證通過")
        return True

    except yaml.YAMLError as e:
        print(f"❌ YAML格式錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 配置驗證失敗: {e}")
        return False

def show_config_diff(old_config: str, new_config: str):
    """顯示配置差異"""
    try:
        import yaml

        # 讀取兩個配置文件
        with open(old_config, 'r', encoding='utf-8') as f:
            old_data = yaml.safe_load(f)

        with open(new_config, 'r', encoding='utf-8') as f:
            new_data = yaml.safe_load(f)

        print("\n" + "="*60)
        print("配置差異分析")
        print("="*60)

        # 新增的功能
        new_features = []
        if 'gpu' in new_data and 'gpu' not in old_data:
            new_features.append("GPU加速配置")
        if 'vectorbt' in new_data and 'vectorbt' not in old_data:
            new_features.append("VectorBT集成配置")
        if 'optimization' in new_data and 'optimization' not in old_data:
            new_features.append("參數優化配置")

        if new_features:
            print(f"🆕 新增功能: {', '.join(new_features)}")

        # 保留的配置
        preserved_sections = []
        for section in ['data_sources', 'system']:
            if section in old_data and section in new_data:
                preserved_sections.append(section)

        if preserved_sections:
            print(f"✅ 保留配置: {', '.join(preserved_sections)}")

        print("\n主要變更:")
        print("- 添加了完整的GPU加速支持")
        print("- 集成了VectorBT專業回測引擎")
        print("- 優化了參數範圍配置(0-300)")
        print("- 增強了性能監控功能")

    except Exception as e:
        print(f"差異分析失敗: {e}")

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="GPU配置遷移工具")
    parser.add_argument(
        '--migrate', '-m',
        help='從舊配置遷移到GPU配置'
    )
    parser.add_argument(
        '--create-sample', '-s',
        help='創建示例配置文件'
    )
    parser.add_argument(
        '--validate', '-v',
        help='驗證配置文件'
    )
    parser.add_argument(
        '--backup', '-b',
        action='store_true',
        help='備份現有配置'
    )
    parser.add_argument(
        '--diff', '-d',
        nargs=2,
        metavar=('OLD_CONFIG', 'NEW_CONFIG'),
        help='比較兩個配置文件的差異'
    )

    args = parser.parse_args()

    # 執行相應操作
    if args.migrate:
        if args.backup:
            backup_existing_config(args.migrate)

        output_config = args.migrate.replace('.yml', '_gpu.yml').replace('.yaml', '_gpu.yaml')
        if migrate_from_data_sources_config(args.migrate, output_config):
            show_config_diff(args.migrate, output_config)

    elif args.create_sample:
        create_sample_config(args.create_sample)

    elif args.validate:
        validate_config(args.validate)

    elif args.diff:
        show_config_diff(args.diff[0], args.diff[1])

    else:
        print("請指定操作。使用 --help 查看幫助信息。")

if __name__ == "__main__":
    main()