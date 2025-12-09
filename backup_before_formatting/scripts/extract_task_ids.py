#!/usr / bin / env python3
"""
任務ID提取器
用於從Git提交信息和代碼文件中提取任務ID

用法:
    pre - commit hook: 自動提取並添加到提交信息
    命令行: python scripts / extract_task_ids.py <file1> <file2> ...
"""

import re
import sys
from typing import List, Set


# 任務ID模式
TASK_ID_PATTERN = re.compile(r'(?:TASK-|#)(\d{3})')

# 關鍵詞模式（檢查提交信息是否包含任務相關關鍵詞）
TASK_KEYWORDS = [
    'feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'per", "ci',
    '重構', '修復', '實現', '創建', '添加', '更新', '刪除', '測試', '優化', '文檔'
]


def extract_task_ids_from_message(message: str) -> Set[str]:
    """
    從文本中提取任務ID

    Args:
        message: 文本消息

    Returns:
        提取的任務ID集合
    """
    matches = TASK_ID_PATTERN.findall(message)
    return {f'TASK-{match}' for match in matches}


def extract_task_ids_from_file(file_path: str) -> Set[str]:
    """
    從文件中提取任務ID

    Args:
        file_path: 文件路徑

    Returns:
        提取的任務ID集合
    """
    task_ids = set()

    try:
        with open(file_path, 'r', encoding='utf - 8', errors='ignore') as f:
            content = f.read()

        # 從註釋中提取
        # Python: # TASK - XXX
        # JavaScript / Vue: // TASK - XXX or /* TASK - XXX */
        # Markdown: <!-- TASK - XXX -->
        comment_patterns = [
            r'//\s*(TASK-\d{3})',  # JavaScript單行註釋
            r'/\*\s*(TASK-\d{3})',  # C風格註釋開始
            r'(TASK-\d{3})\s*\*/',  # C風格註釋結束
            r'<!--\s*(TASK-\d{3})',  # HTML註釋開始
            r'(TASK-\d{3})\s*-->',  # HTML註釋結束
            r'#\s*(TASK-\d{3})',  # Python / shell註釋
            r'---\s*(TASK-\d{3})',  # YAML註釋
        ]

        for pattern in comment_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            task_ids.update(matches)

        # 從 TODO / FIXME 註釋中提取
        todo_pattern = r'(?:TODO|FIXME|BUG|HACK)\s*[:：]\s*(TASK-\d{3})'
        matches = re.findall(todo_pattern, content, re.IGNORECASE)
        task_ids.update(matches)

    except Exception as e:
        print(f'Warning: 無法讀取文件 {file_path}: {e}', file=sys.stderr)

    return task_ids


def should_include_task_ids(commit_message: str) -> bool:
    """
    判斷提交信息是否應該包含任務ID

    Args:
        commit_message: 提交信息

    Returns:
        是否應該包含任務ID
    """
    # 檢查是否包含任務相關關鍵詞
    for keyword in TASK_KEYWORDS:
        if keyword.lower() in commit_message.lower():
            return True

    # 檢查是否已經包含任務ID
    if extract_task_ids_from_message(commit_message):
        return True

    # 合併提交或版本標籤不需要任務ID
    skip_patterns = [
        r'^merge\s+',
        r'^revert\s+',
        r'^tag:\s + v?\d+\.\d+\.\d+',
        r'^\[maven - release - plugin\]\s+',
    ]

    for pattern in skip_patterns:
        if re.match(pattern, commit_message, re.IGNORECASE):
            return False

    # 其他情況需要任務ID
    return True


def main():
    """主函數"""
    # 從環境變量獲取提交信息
    commit_message = sys.argv[1] if len(sys.argv) > 1 else ''
    file_paths = sys.argv[2:] if len(sys.argv) > 2 else []

    # 從文件中提取任務ID
    file_task_ids = set()
    for file_path in file_paths:
        ids = extract_task_ids_from_file(file_path)
        file_task_ids.update(ids)

    # 從提交信息中提取任務ID
    msg_task_ids = extract_task_ids_from_message(commit_message)

    # 合併任務ID
    all_task_ids = file_task_ids.union(msg_task_ids)

    if all_task_ids and should_include_task_ids(commit_message):
        # 生成帶任務ID的提交信息
        task_list = ' '.join(sorted(all_task_ids))
        new_message = f'{commit_message}\n\n任務: {task_list}'

        # 寫入臨時文件，供後續hook使用
        with open('.gitmessage_tmp', 'w', encoding='utf - 8') as f:
            f.write(new_message)

        print(f'✅ 提取到任務ID: {task_list}', file=sys.stderr)
    elif all_task_ids:
        print("⚠️  跳過任務ID（合併 / 版本提交）", file=sys.stderr)
    else:
        print('ℹ️  未提取到任務ID', file=sys.stderr)


if __name__ == '__main__':
    main()
