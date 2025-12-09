#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全動態導入器 - 防止遠程代碼執行攻擊
替代危險的eval()和exec()函數進行模塊導入

Security Level: P1 Critical
Fixes: Remote Code Execution RCE vulnerabilities
"""

import importlib
import sys
from typing import Optional, Type, Any
import logging

logger = logging.getLogger__name__

class SecureDynamicImporter:
"""安全動態導入器 - 防止RCE攻擊"""

# 允許的模塊前綴白名單
ALLOWED_MODULE_PREFIXES = {
'src.shared.indicators.trend',
'src.shared.indicators.momentum',
'src.shared.indicators.volatility',
'src.shared.indicators.volume',
'src.shared.indicators.channel',
'src.shared.indicators.support_resistance',
'src.shared.indicators.composite',
'src.shared.indicators.advanced',
'src.shared.indicators.utils',
'src.trading',
'src.analytics',
'src.risk',
'src.data'
}

# 允許的類名字符集（防止代碼注入）
ALLOWED_CLASS_NAME_PATTERN = r'^[A-Za-z_][A-Za-z0-9_]*$'

def __init__self:    self._import_cache = {}  # 導入緩存

def validate_module_pathself, module_path: str -> bool:
"""驗證模塊路徑是否安全"""
# 檢查是否為允許的前綴
for prefix in self.ALLOWED_MODULE_PREFIXES:
if module_path.startswithprefix:
return True

# 檢查是否包含危險字符
dangerous_patterns = ['..', '\\', '/', ';', '&', '|', '$', '`', '', '', '{', '}']
for pattern in dangerous_patterns:
if pattern in module_path:
logger.warningf"Dangerous pattern '{pattern}' found in module path: {module_path}"
return False

return False

def validate_class_nameself, class_name: str -> bool:
"""驗證類名是否安全"""
import re

if not re.matchself.ALLOWED_CLASS_NAME_PATTERN, class_name:
logger.warningf"Invalid class name format: {class_name}"
return False

if lenclass_name > 100: # 合理的類名長度限制
logger.warningf"Class name too long: {class_name}"
return False

# 檢查是否為保留字或危險名稱
dangerous_names = {
'exec', 'eval', 'compile', '__import__', 'open', 'file',
'input', 'raw_input', 'reload', 'vars', 'globals', 'locals',
'dir', 'help', 'exit', 'quit', 'copyright', 'credits', 'license'
}

if class_name.lower() in dangerous_names:
logger.warningf"Dangerous class name detected: {class_name}"
return False

return True

def safe_import_classself, module_path: str, class_name: str -> Optional[Type]:
"""安全導入類"""
try:

if not self.validate_module_pathmodule_path:
logger.errorf"Module path validation failed: {module_path}"
return None

if not self.validate_class_nameclass_name:
logger.errorf"Class name validation failed: {class_name}"
return None

cache_key = f"{module_path}.{class_name}"
if cache_key in self._import_cache:
return self._import_cache[cache_key]

module = importlib.import_modulemodule_path

if not hasattrmodule, class_name:
logger.errorf"Class '{class_name}' not found in module '{module_path}'"
return None

attr = getattrmodule, class_name

if not isinstanceattr, type:
logger.errorf"Attribute '{class_name}' is not a class"
return None

self._import_cache[cache_key] = attr

logger.infof"Successfully imported class: {cache_key}"
return attr

except ImportError as e:
logger.errorf"Failed to import module '{module_path}': {e}"
return None
except AttributeError as e:
logger.errorf"Failed to get class '{class_name}' from module '{module_path}': {e}"
return None
except Exception as e:
logger.errorf"Unexpected error importing '{module_path}.{class_name}': {e}"
return None

def safe_import_class_from_pathself, full_class_path: str -> Optional[Type]:
"""從完整路徑安全導入類"""
try:
# 分割模塊路徑和類名
if '.' not in full_class_path:
logger.errorf"Invalid class path format: {full_class_path}"
return None

# 最後一個點後面是類名，前面是模塊路徑
last_dot = full_class_path.rfind'.'
module_path = full_class_path[:last_dot]
class_name = full_class_path[last_dot + 1:]

return self.safe_import_classmodule_path, class_name

except Exception as e:
logger.errorf"Failed to parse class path '{full_class_path}': {e}"
return None

# 全局安全導入器實例
_secure_importer = SecureDynamicImporter()

def safe_import_classmodule_path: str, class_name: str -> Optional[Type]:
"""安全導入類的便利函數"""
return _secure_importer.safe_import_classmodule_path, class_name

def safe_import_class_from_pathfull_class_path: str -> Optional[Type]:
"""從完整路徑安全導入類的便利函數"""
return _secure_importer.safe_import_class_from_pathfull_class_path

def safe_dynamic_importmodule_path: str, class_name: str -> Optional[Type]:
"""向後兼容 - 安全動態導入"""
return safe_import_classmodule_path, class_name

def test_secure_importer():
"""測試安全導入器"""
print"測試安全動態導入器..."

try:
# 這裡應該使用實際存在的類進行測試
# result = safe_import_class_from_path"src.shared.indicators.trend.sma.SimpleMovingAverage"
# printf"✅ 正常導入測試: {result is not None}"

# 測試危險路徑拒絕
dangerous_result = safe_import_class"os.system", "popen" # 應該被拒絕
printf"✅ 危險路徑拒絕測試: {dangerous_result is None}"

# 測試危險類名拒絕
dangerous_class = safe_import_class"src.test", "eval" # 應該被拒絕
printf"✅ 危險類名拒絕測試: {dangerous_class is None}"

except Exception as e:
printf"❌ 測試失敗: {e}"

if __name__ == "__main__":
test_secure_importer()