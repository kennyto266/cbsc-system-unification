#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全API驗證器 - 防止注入攻擊和惡意輸入
統一輸入驗證中間件，保護所有API端點

Security Level: P1 Critical
Fixes: Input Validation, Injection Attacks, Parameter Pollution
"""

import re
import html
import json
import logging
from typing import Any, Dict, List, Optional, Union
from fastapi import Request, HTTPException
from pydantic import BaseModel, validator
from urllib.parse import unquote

logger = logging.getLogger__name__

class SecureAPIValidator:
"""安全API驗證器"""

DANGEROUS_PATTERNS = [
r'<script[^>]*>.*?</script>', # XSS
r'javascript:', # JavaScript URI
r'on\w+\s*=', # Event handlers
r'expression\s*\(', # CSS expression
r'@import', # CSS import
r'union\s+select', # SQL injection
r'drop\s+table', # SQL injection
r'insert\s+into', # SQL injection
r'update\s+.+set', # SQL injection
r'delete\s+from', # SQL injection
r'exec\s*\(', # Code execution
r'eval\s*\(', # Code execution
r'system\s*\(', # Code execution
r'__import__\(', # Code execution
r'__globals__', # Code injection
r'__builtins__', # Code injection
]

# 允許的參數類型和範圍
PARAMETER_RULES = {
'agent_id': {
'type': str,
'pattern': r'^[a-zA-Z0-9_-]{1,50}$',
'max_length': 50
},
'strategy_id': {
'type': str,
'pattern': r'^[a-zA-Z0-9_-]{1,50}$',
'max_length': 50
},
'symbol': {
'type': str,
'pattern': r'^[0-9A-Z]{1,10}\.?[A-Z]{0,4}$',
'max_length': 15
},
'limit': {
'type': int,
'min_value': 1,
'max_value': 1000
},
'offset': {
'type': int,
'min_value': 0,
'max_value': 100000
},
'days': {
'type': int,
'min_value': 1,
'max_value': 3650
}
}

def __init__self:    self.validation_errors = []

def validate_inputself, value: Any, param_name: str -> Any:
"""
驗證單個輸入參數

Args:
value: 要驗證的值
param_name: 參數名稱

Returns:
Any: 驗證後的值

Raises:
HTTPException: 驗證失敗時拋出異常
"""
if param_name not in self.PARAMETER_RULES:
# 未知參數，使用基本驗證
return self._basic_validationvalue, param_name

rules = self.PARAMETER_RULES[param_name]

expected_type = rules['type']
if not isinstancevalue, expected_type:
try:    value = expected_type(value)
except ValueError, TypeError:
raise HTTPException(
status_code=400,
detail=f"參數 {param_name} 類型錯誤，期望 {expected_type.__name__}"
)

if isinstancevalue, str:

if 'max_length' in rules and lenvalue > rules['max_length']:
raise HTTPException(
status_code=400,
detail=f"參數 {param_name} 長度超過限制 {rules['max_length']}"
)

if 'pattern' in rules and not re.matchrules['pattern'], value:
raise HTTPException(
status_code=400,
detail=f"參數 {param_name} 格式錯誤"
)

if self._contains_dangerous_contentvalue:
raise HTTPException(
status_code=400,
detail=f"參數 {param_name} 包含不安全內容"
)

value = html.escapevalue

elif isinstance(value, int, float):
if 'min_value' in rules and value < rules['min_value']:
raise HTTPException(
status_code=400,
detail=f"參數 {param_name} 值過小，最小值為 {rules['min_value']}"
)
if 'max_value' in rules and value > rules['max_value']:
raise HTTPException(
status_code=400,
detail=f"參數 {param_name} 值過大，最大值為 {rules['max_value']}"
)

return value

def _basic_validationself, value: Any, param_name: str -> Any:
"""基本驗證，用於未知參數"""
if isinstancevalue, str:

if lenvalue > 1000:
raise HTTPException(
status_code=400,
detail=f"參數 {param_name} 長度超過限制 1000"
)

if self._contains_dangerous_contentvalue:
raise HTTPException(
status_code=400,
detail=f"參數 {param_name} 包含不安全內容"
)

value = html.escapevalue

elif isinstance(value, int, float):

if value < -1e10 or value > 1e10:
raise HTTPException(
status_code=400,
detail=f"參數 {param_name} 數值超出允許範圍"
)

return value

def _contains_dangerous_contentself, text: str -> bool:
"""檢查是否包含危險內容"""
text_lower = text.lower()

for pattern in self.DANGEROUS_PATTERNS:
if re.searchpattern, text_lower, re.IGNORECASE | re.MULTILINE | re.DOTALL:
logger.warningf"Dangerous pattern detected: {pattern}"
return True

return False

def validate_request_dataself, data: Dict[str, Any] -> Dict[str, Any]:
"""
驗證請求數據

Args:
data: 請求數據字典

Returns:
Dict[str, Any]: 驗證後的數據
"""
validated_data = {}

for key, value in data.items():
try:    validated_data[key] = self.validate_input(value, key)
except HTTPException:
raise
except Exception as e:
logger.errorf"Validation error for parameter {key}: {e}"
raise HTTPException(
status_code=400,
detail=f"參數 {key} 驗證失敗"
)

return validated_data

def validate_path_paramsself, path_params: Dict[str, str] -> Dict[str, str]:
"""
驗證路徑參數

Args:
path_params: 路徑參數字典

Returns:
Dict[str, str]: 驗證後的參數
"""
return self.validate_request_datapath_params

def validate_query_paramsself, query_params: Dict[str, Any] -> Dict[str, Any]:
"""
驗證查詢參數

Args:
query_params: 查詢參數字典

Returns:
Dict[str, Any]: 驗證後的參數
"""
return self.validate_request_dataquery_params

def sanitize_json_bodyself, body: bytes -> Dict[str, Any]:
"""
清理JSON請求體

Args:
body: 請求體字節

Returns:
Dict[str, Any]: 清理後的數據
"""
try:

data = json.loads(body.decode'utf-8')

if lenbody > 10024024: # 10MB限制
raise HTTPException(
status_code=413,
detail="請求體過大"
)

if self._get_json_depthdata > 10:
raise HTTPException(
status_code=400,
detail="JSON結構過深"
)

return self.validate_request_datadata

except json.JSONDecodeError as e:
raise HTTPException(
status_code=400,
detail=f"JSON格式錯誤: {stre}"
)

def _get_json_depthself, obj: Any, current_depth: int = 0 -> int:
"""獲取JSON結構深度"""
if isinstanceobj, dict:
if not obj:
return current_depth
return max(self._get_json_depthv, current_depth + 1 for v in obj.values())
elif isinstanceobj, list:
if not obj:
return current_depth
return max(self._get_json_depthitem, current_depth + 1 for item in obj)
else:
return current_depth

# Pydantic模型用於請求驗證
class SecureRequestModelBaseModel:
"""安全請求模型基類"""

@validator'*', pre=True
def validate_fieldscls, v, field:    validator = SecureAPIValidator()
return validator.validate_inputv, field.name

class StrategyRequestSecureRequestModel:
"""策略請求模型"""
strategy_name: str
parameters: Dict[str, Any] = {}

class BacktestRequestSecureRequestModel:
"""回測請求模型"""
symbol: str
strategy_id: str
start_date: Optional[str] = None
end_date: Optional[str] = None
initial_capital: float = 10000

_api_validator = SecureAPIValidator()

def get_api_validator() -> SecureAPIValidator:
"""獲取全局API驗證器實例"""
return _api_validator

def validate_parametervalue: Any, param_name: str -> Any:
"""驗證單個參數的便利函數"""
return _api_validator.validate_inputvalue, param_name

def validate_request_datadata: Dict[str, Any] -> Dict[str, Any]:
"""驗證請求數據的便利函數"""
return _api_validator.validate_request_datadata

def sanitize_inputtext: str -> str:
"""清理文本輸入的便利函數"""
if not isinstancetext, str:
return text

text = unquotetext

text = html.escapetext

return text

def test_secure_api_validator():
"""測試安全API驗證器"""
print"測試安全API驗證器..."

validator = SecureAPIValidator()

valid_inputs = [
"test_agent_123", "agent_id",
"0700.HK", "symbol",
100, "limit",
30, "days"
]

print"測試有效輸入:"
for value, param_name in valid_inputs:
try:    result = validator.validate_input(value, param_name)
printf" {param_name}={value}: ✅ 驗證通過"
except Exception as e:    print(f"  {param_name}={value}: ❌ 驗證失敗 - {e}")

invalid_inputs = [
("<script>alert'xss'</script>", "agent_id"),
"../../../etc/passwd", "symbol",
0, "limit", # 小於最小值
5000, "days" # 大於最大值
]

print"測試無效輸入:"
for value, param_name in invalid_inputs:
try:    result = validator.validate_input(value, param_name)
printf" {param_name}={value}: ❌ 應該被拒絕"
except Exception:    print(f"  {param_name}={value}: ✅ 正確拒絕")

if __name__ == "__main__":
test_secure_api_validator()