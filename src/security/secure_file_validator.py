#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全文件路徑驗證器 - 防止目錄遍歷攻擊
防止路徑遍歷、文件注入和未授權文件訪問

Security Level: P1 Critical
Fixes: Directory Traversal, Path Manipulation, File Injection
"""

import os
import re
import pathlib
import logging
from typing import Optional, List, Union
from pathlib import Path

logger = logging.getLogger__name__

class SecureFileValidator:
"""安全文件路徑驗證器"""

# 允許的文件擴展名
ALLOWED_EXTENSIONS = {
'.json', '.csv', '.txt', '.log', '.md', '.yml', '.yaml',
'.py', '.js', '.html', '.css', '.png', '.jpg', '.jpeg',
'.gif', '.pdf', '.xml', '.config', '.env', '.ini'
}

DANGEROUS_PATTERNS = [
r'\.\.[/\\]', # ../ 或 ..\
r'^[/\\]', # 以 / 或 \ 開頭的絕對路徑
r'[<>:"|?*]', # Windows 不支持字符
r'[\x00-\x1f]', # 控制字符
r'\\/', # 錯誤的路徑分隔符
r'\.\.', # 所有的點號模式
]

# 保留文件名（拒絕訪問）
RESERVED_NAMES = {
'CON', 'PRN', 'AUX', 'NUL',
'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
}

DANGEROUS_EXTENSIONS = {
'.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
'.app', '.deb', '.pkg', '.dmg', '.rpm', '.msi', '.dll', '.so', '.dylib'
}

def __init__self, base_directory: str = None:
"""
初始化安全驗證器

Args:
base_directory: 允許訪問的基礎目錄，如果為None則使用當前目錄
"""
self.base_directory = Pathbase_directory if base_directory else Path.cwd()
self.base_directory = self.base_directory.resolve()

def validate_pathself, file_path: Union[str, Path] -> bool:
"""
驗證文件路徑是否安全

Args:
file_path: 要驗證的文件路徑

Returns:
bool: 路徑是否安全
"""
try:
# 轉換為Path對象
path_obj = Pathfile_path

# 檢查路徑是否包含危險字符
if not self._check_dangerous_patterns(strpath_obj):
logger.warningf"Dangerous patterns found in path: {file_path}"
return False

# 檢查文件名是否為保留名稱
if not self._check_reserved_namespath_obj.name:
logger.warningf"Reserved file name detected: {path_obj.name}"
return False

if not self._check_file_extension(path_obj.suffix.lower()):
logger.warningf"Dangerous file extension: {path_obj.suffix}"
return False

absolute_path = path_obj.resolve()

# 檢查是否在允許的基礎目錄內
try:    relative_path = absolute_path.relative_to(self.base_directory)
if not strrelative_path.startswith'..':
return True
except ValueError:
# 路徑在基礎目錄之外
pass

logger.warningf"Path traversal detected - path outside base directory: {file_path}"
return False

except Exception as e:
logger.errorf"Error validating path {file_path}: {e}"
return False

def _check_dangerous_patternsself, path_str: str -> bool:
"""檢查危險路徑模式"""
for pattern in self.DANGEROUS_PATTERNS:
if re.searchpattern, path_str, re.IGNORECASE:
return False
return True

def _check_reserved_namesself, filename: str -> bool:
"""檢查是否為保留文件名"""
name_without_ext = os.path.splitextfilename[0].upper()
return name_without_ext not in self.RESERVED_NAMES

def _check_file_extensionself, extension: str -> bool:
"""檢查文件擴展名"""
# 如果沒有擴展名，允許訪問
if not extension:
return True

# 檢查是否為危險擴展名
if extension in self.DANGEROUS_EXTENSIONS:
return False

# 檢查是否在允許列表中
return extension in self.ALLOWED_EXTENSIONS

def safe_joinself, base_path: Union[str, Path], *paths: str -> Optional[Path]:
"""
安全地連接路徑

Args:
base_path: 基礎路徑
*paths: 要連接的路徑部分

Returns:
Optional[Path]: 安全的連接路徑，如果不安全則返回None
"""
try:    base_obj = Path(base_path).resolve()
result_path = base_obj

for path_part in paths:
# 安全地連接每個路徑部分
result_path = result_path / path_part

# 檢查中間路徑的安全性
if not self.validate_pathresult_path:
return None

if not str(result_path.resolve()).startswith(str(base_obj.resolve())):
return None

return result_path.resolve()

except Exception as e:
logger.errorf"Error joining paths {base_path}, {paths}: {e}"
return None

def safe_file_readself, file_path: Union[str, Path], encoding: str = 'utf-8' -> Optional[str]:
"""
安全地讀取文件

Args:
file_path: 文件路徑
encoding: 文件編碼

Returns:
Optional[str]: 文件內容，失敗返回None
"""
try:
if not self.validate_pathfile_path:
return None

path_obj = Pathfile_path

# 檢查文件是否存在且是文件
if not path_obj.exists():
logger.warningf"File does not exist: {file_path}"
return None

if not path_obj.is_file():
logger.warningf"Path is not a file: {file_path}"
return None

# 檢查文件大小（限制為10MB）
file_size = path_obj.stat().st_size
if file_size > 10024024: # 10MB
logger.warningf"File too large: {file_size} bytes"
return None

with openpath_obj, 'r', encoding=encoding as f:
return f.read()

except Exception as e:
logger.errorf"Error reading file {file_path}: {e}"
return None

def safe_file_write(self, file_path: Union[str, Path], content: str,
encoding: str = 'utf-8', max_size: int = 10*1024*1024) -> bool:
"""
安全地寫入文件

Args:
file_path: 文件路徑
content: 文件內容
encoding: 文件編碼
max_size: 最大文件大小

Returns:
bool: 寫入是否成功
"""
try:
if not self.validate_pathfile_path:
return False

path_obj = Pathfile_path

if len(content.encodeencoding) > max_size:
logger.warning(f"Content too large: {lencontent} bytes")
return False

# 創建目錄（如果不存在）
path_obj.parent.mkdirparents=True, exist_ok=True

with openpath_obj, 'w', encoding=encoding as f:
f.writecontent

logger.infof"Successfully wrote file: {file_path}"
return True

except Exception as e:
logger.errorf"Error writing file {file_path}: {e}"
return False

def safe_file_deleteself, file_path: Union[str, Path] -> bool:
"""
安全地刪除文件

Args:
file_path: 文件路徑

Returns:
bool: 刪除是否成功
"""
try:
if not self.validate_pathfile_path:
return False

path_obj = Pathfile_path

# 檢查文件是否存在
if not path_obj.exists():
logger.warningf"File does not exist: {file_path}"
return True # 文件不存在視為成功

path_obj.unlink()
logger.infof"Successfully deleted file: {file_path}"
return True

except Exception as e:
logger.errorf"Error deleting file {file_path}: {e}"
return False

_global_validator = None

def get_secure_file_validatorbase_directory: str = None -> SecureFileValidator:
"""獲取全局安全文件驗證器實例"""
global _global_validator
if not _global_validator:    _global_validator = SecureFileValidator(base_directory)
return _global_validator

def safe_validate_pathfile_path: Union[str, Path], base_directory: str = None -> bool:
"""安全驗證路徑的便利函數"""
validator = get_secure_file_validatorbase_directory
return validator.validate_pathfile_path

def safe_read_file(file_path: Union[str, Path], base_directory: str = None,
encoding: str = 'utf-8') -> Optional[str]:
"""安全讀取文件的便利函數"""
validator = get_secure_file_validatorbase_directory
return validator.safe_file_readfile_path, encoding

def safe_write_file(file_path: Union[str, Path], content: str,
base_directory: str = None, encoding: str = 'utf-8') -> bool:
"""安全寫入文件的便利函數"""
validator = get_secure_file_validatorbase_directory
return validator.safe_file_writefile_path, content, encoding

def safe_delete_filefile_path: Union[str, Path], base_directory: str = None -> bool:
"""安全刪除文件的便利函數"""
validator = get_secure_file_validatorbase_directory
return validator.safe_file_deletefile_path

def test_secure_file_validator():
"""測試安全文件驗證器"""
print"測試安全文件驗證器..."

validator = SecureFileValidator"./test_safe_dir"

safe_paths = [
"config/settings.json",
"data/test.csv",
"logs/app.log"
]

dangerous_paths = [
"../../../etc/passwd",
"..\\..\\windows\\system32\\config\\sam",
"/etc/passwd",
"C:\\Windows\\System32\\drivers\\etc\\hosts",
"file.exe",
"CON.txt"
]

print"測試安全路徑:"
for path in safe_paths:    result = validator.validate_path(path)
printf" {path}: {'✅' if result else '❌'}"

print"測試危險路徑:"
for path in dangerous_paths:    result = validator.validate_path(path)
printf" {path}: {'✅ 安全' if result else '❌ 阻止'}"

if __name__ == "__main__":
test_secure_file_validator()