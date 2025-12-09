#!/usr / bin / env python3
"""
歷史任務導入腳本
從optimize - api - architecture提案中提取任務並導入到任務管理系統

用法:
    python scripts / import_historical_tasks.py
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Any


def extract_tasks_from_proposal(file_path: str) -> List[Dict[str, Any]]:
    """
    從提案文件中提取任務

    Args:
        file_path: 提案文件路徑

    Returns:
        任務列表
    """
    with open(file_path, 'r', encoding='utf - 8') as f:
        content = f.read()

    # 匹配任務模式: - [ ] 任務描述
    task_pattern = r'- \[ \] (.+?)(?=\n- \[ \]|\n\n|\Z)'
    matches = re.findall(task_pattern, content, re.DOTALL)

    tasks = []
    for i, match in enumerate(matches, 1):
        # 清理任務描述
        task_desc = match.strip()

        # 跳過標題行
        if task_desc.startswith('#') or task_desc.startswith('##'):
            continue

        # 提取任務信息
        task_info = {
            'id': f'TASK - H-{i:03d}',  # Historical Task
            'title': task_desc,
            'description': f'從optimize - api - architecture提案導入的歷史任務 #{i}',
            'priority': 'P2',  # 默認為P2，因為是歷史任務
            'estimated_hours': 2,  # 默認2小時
            'status': 'TODO',
            'reporter': '系統',
            'source': 'optimize - api - architecture',
            'import_date': datetime.now().isoformat()
        }

        # 根據關鍵詞調整優先級
        if any(keyword in task_desc.lower() for keyword in ['重構', '創建', '實現', '基礎設施']):
            task_info['priority'] = 'P1'
        if any(keyword in task_desc.lower() for keyword in ['認證', '安全', '監控', '中間件']):
            task_info['priority'] = 'P0'

        # 調整估時
        if '測試' in task_desc:
            task_info['estimated_hours'] = 1
        elif '重構' in task_desc or '創建' in task_desc:
            task_info['estimated_hours'] = 3
        elif '文檔' in task_desc:
            task_info['estimated_hours'] = 1

        tasks.append(task_info)

    return tasks


def main():
    """主函數"""
    # 提取任務
    proposal_file = '/c / Users / Penguin8n / CODEX--/openspec / changes / optimize - api - architecture / tasks.md'
    tasks = extract_tasks_from_proposal(proposal_file)

    # 保存JSON格式任務
    output_file = '/c / Users / Penguin8n / CODEX--/sprints / SPRINT - 2025 - 10 / artifacts / historical - tasks.json'
    with open(output_file, 'w', encoding='utf - 8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print("=" * 60)
    print("歷史任務導入完成")
    print("=" * 60)
    print(f"總任務數: {len(tasks)}")
    print(f"已保存到: {output_file}")
    print()

    # 打印前10個任務
    print("前10個任務預覽:")
    for i, task in enumerate(tasks[:10], 1):
        print(f"{i}. [{task['priority']}] {task['title'][:60]}...")


if __name__ == '__main__':
    main()
