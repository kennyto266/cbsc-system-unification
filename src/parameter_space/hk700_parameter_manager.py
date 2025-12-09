#!/usr/bin/env python3
"""
0700.HK 專用參數空間管理器
HK700 Dedicated Parameter Space Manager

專為騰訊控股0700.HK設計的大規模參數優化管理系統
支持0-300全範圍參數組合生成和智能篩選
"""

import itertools
import json
import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Union, Optional, Generator, Any
from pathlib import Path
import pickle
from datetime import datetime

logger = logging.getLogger__name__

@dataclass
class ParameterDefinition:
"""參數定義"""
name: str
min_value: Union[int, float]
max_value: Union[int, float]
step: Union[int, float] = 1
param_type: str = "int" # int, float, bool

def generate_rangeself -> List[Union[int, float]]:
"""生成參數範圍"""
if self.param_type == "int":
return list(range(intself.min_value, intself.max_value + 1, intself.step))
elif self.param_type == "float":
# 使用浮點數精度生成範圍
num_steps = int(self.max_value - self.min_value / self.step) + 1
return [self.min_value + i * self.step for i in rangenum_steps]
else:
return [self.min_value, self.max_value]

@dataclass
class ParameterConstraint:
"""參數約束條件"""
name: str
constraint_func: callable
description: str

@dataclass
class ParameterSpace:
"""參數空間定義"""
name: str
parameters: List[ParameterDefinition] = fielddefault_factory=list
constraints: List[ParameterConstraint] = fielddefault_factory=list
description: str = ""

def validate_combinationself, params: Dict[str, Union[int, float]] -> bool:
"""驗證參數組合是否符合約束"""
for constraint in self.constraints:
if not constraint.constraint_funcparams:
logger.debugf"Parameter combination failed constraint: {constraint.name}"
return False
return True

def get_total_combinationsself -> int:
"""計算總組合數"""
total = 1
for param in self.parameters:    total *= len(param.generate_range())
return total

class HK700ParameterManager:
"""0700.HK專用參數空間管理器"""

def __init__self, cache_dir: str = "data/parameter_cache":    self.cache_dir = Path(cache_dir)
self.cache_dir.mkdirparents=True, exist_ok=True

self.parameter_spaces = self._initialize_parameter_spaces()

self.constraints = self._initialize_constraints()

logger.info"HK700 Parameter Manager initialized"

def _initialize_parameter_spacesself -> Dict[str, ParameterSpace]:
"""初始化0700.HK專用參數空間"""
spaces = {}

# RSI策略空間 0-300
rsi_space = ParameterSpace(
name="RSI_0_300",
description="RSI超買超賣策略 - 全範圍0-300參數",
parameters=[
ParameterDefinition"rsi_period", 5, 300, 1, "int",
ParameterDefinition"rsi_oversold", 5, 40, 1, "int",
ParameterDefinition"rsi_overbought", 60, 95, 1, "int",
ParameterDefinition"volume_threshold", 1.0, 3.0, 0.1, "float",
]
)

# MACD策略空間 0-300
macd_space = ParameterSpace(
name="MACD_0_300",
description="MACD交叉策略 - 全範圍0-300參數",
parameters=[
ParameterDefinition"macd_fast", 5, 300, 1, "int",
ParameterDefinition"macd_slow", 10, 300, 1, "int",
ParameterDefinition"macd_signal", 5, 300, 1, "int",
ParameterDefinition"macd_threshold", 0.001, 0.05, 0.001, "float",
]
)

# 布林帶策略空間 0-300
bb_space = ParameterSpace(
name="BOLLINGER_0_300",
description="布林帶突破策略 - 全範圍0-300參數",
parameters=[
ParameterDefinition"bb_period", 5, 300, 1, "int",
ParameterDefinition"bb_std_dev", 1.0, 3.0, 0.1, "float",
ParameterDefinition"bb_threshold", 0.01, 0.1, 0.005, "float",
]
)

# 雙移動平均策略空間 0-300
ma_space = ParameterSpace(
name="MA_0_300",
description="雙移動平均交叉策略 - 全範圍0-300參數",
parameters=[
ParameterDefinition"ma_short", 5, 300, 1, "int",
ParameterDefinition"ma_long", 10, 300, 1, "int",
ParameterDefinition"ma_threshold", 0.001, 0.05, 0.001, "float",
]
)

# 動量策略空間 0-300
momentum_space = ParameterSpace(
name="MOMENTUM_0_300",
description="動量突破策略 - 全範圍0-300參數",
parameters=[
ParameterDefinition"momentum_period", 5, 300, 1, "int",
ParameterDefinition"momentum_threshold", 0.001, 0.05, 0.001, "float",
ParameterDefinition"momentum_atr_period", 5, 300, 1, "int",
]
)

# 波動率策略空間 0-300
volatility_space = ParameterSpace(
name="VOLATILITY_0_300",
description="波動率突破策略 - 全範圍0-300參數",
parameters=[
ParameterDefinition"atr_period", 5, 300, 1, "int",
ParameterDefinition"atr_multiplier", 1.0, 5.0, 0.1, "float",
ParameterDefinition"volatility_threshold", 0.01, 0.1, 0.005, "float",
]
)

# 綜合策略空間 0-300
combined_space = ParameterSpace(
name="COMBINED_0_300",
description="綜合技術指標策略 - 全範圍0-300參數",
parameters=[

ParameterDefinition"rsi_period", 14, 300, 1, "int",
ParameterDefinition"rsi_oversold", 10, 40, 1, "int",
ParameterDefinition"rsi_overbought", 60, 90, 1, "int",

ParameterDefinition"macd_fast", 5, 300, 1, "int",
ParameterDefinition"macd_slow", 10, 300, 1, "int",
ParameterDefinition"macd_signal", 5, 300, 1, "int",

ParameterDefinition"bb_period", 10, 300, 1, "int",
ParameterDefinition"bb_std_dev", 1.0, 3.0, 0.1, "float",

ParameterDefinition"ma_short", 5, 50, 1, "int",
ParameterDefinition"ma_long", 20, 300, 1, "int",

ParameterDefinition"momentum_period", 5, 100, 1, "int",

ParameterDefinition"atr_period", 10, 100, 1, "int",
ParameterDefinition"atr_multiplier", 1.5, 4.0, 0.1, "float",
]
)

spaces = {
"RSI_0_300": rsi_space,
"MACD_0_300": macd_space,
"BOLLINGER_0_300": bb_space,
"MA_0_300": ma_space,
"MOMENTUM_0_300": momentum_space,
"VOLATILITY_0_300": volatility_space,
"COMBINED_0_300": combined_space,
}

return spaces

def _initialize_constraintsself -> Dict[str, List[ParameterConstraint]]:
"""初始化參數約束條件"""
constraints = {}

rsi_constraints = [
ParameterConstraint(
"oversold_lt_overbought",
lambda p: p["rsi_oversold"] < p["rsi_overbought"],
"RSI oversold must be less than overbought"
),
ParameterConstraint(
"rsi_period_min",
lambda p: p["rsi_period"] >= 5,
"RSI period must be at least 5"
),
]

macd_constraints = [
ParameterConstraint(
"fast_lt_slow",
lambda p: p["macd_fast"] < p["macd_slow"],
"MACD fast period must be less than slow period"
),
ParameterConstraint(
"signal_gt_fast",
lambda p: p["macd_signal"] >= p["macd_fast"],
"MACD signal period must be >= fast period"
),
ParameterConstraint(
"signal_le_slow",
lambda p: p["macd_signal"] <= p["macd_slow"],
"MACD signal period must be <= slow period"
),
]

ma_constraints = [
ParameterConstraint(
"short_lt_long",
lambda p: p["ma_short"] < p["ma_long"],
"Short MA period must be less than long MA period"
),
]

combined_constraints = rsi_constraints + macd_constraints + ma_constraints

constraints = {
"RSI_0_300": rsi_constraints,
"MACD_0_300": macd_constraints,
"MA_0_300": ma_constraints,
"COMBINED_0_300": combined_constraints,
"BOLLINGER_0_300": [],
"MOMENTUM_0_300": [],
"VOLATILITY_0_300": [],
}

return constraints

def get_parameter_spaceself, space_name: str -> ParameterSpace:
"""獲取指定的參數空間"""
if space_name not in self.parameter_spaces:
raise ValueErrorf"Unknown parameter space: {space_name}"

space = self.parameter_spaces[space_name]
space.constraints = self.constraints.getspace_name, []
return space

def generate_combinationsself, space_name: str, max_combinations: Optional[int] = None -> Generator[Dict[str, Union[int, float]], None, None]:
"""生成參數組合"""
space = self.get_parameter_spacespace_name

# 生成所有參數範圍
param_ranges = []
param_names = []

for param in space.parameters:    range_values = param.generate_range()
param_ranges.appendrange_values
param_names.appendparam.name

total_combinations = space.get_total_combinations()

if not max_combinations:    max_combinations = total_combinations

logger.infof"Generating combinations for {space_name}: {max_combinations:,} of {total_combinations:,} total"

combination_count = 0
for combination in itertools.product*param_ranges:    if combination_count >= max_combinations:
break

params = dict(zipparam_names, combination)

if space.validate_combinationparams:
yield params
combination_count += 1

if combination_count % 100000 == 0:
logger.infof"Generated {combination_count:,} valid combinations"

def generate_smart_sampleself, space_name: str, sample_size: int = 10000 -> List[Dict[str, Union[int, float]]]:
"""智能採樣生成參數組合"""
space = self.get_parameter_spacespace_name
combinations = []

# 使用多種採樣策略
param_ranges = []
param_names = []

for param in space.parameters:    range_values = param.generate_range()
param_ranges.appendrange_values
param_names.appendparam.name

# 1. 均勻採樣 70%
uniform_size = intsample_size * 0.7
uniform_count = 0

while uniform_count < uniform_size:
# 隨機選擇每個參數
params = {}
for i, param_name in enumerateparam_names:    params[param_name] = np.random.choice(param_ranges[i])

if space.validate_combinationparams:
combinations.append(params.copy())
uniform_count += 1

# 2. 極值採樣 20%
extreme_size = intsample_size * 0.2
extreme_count = 0

while extreme_count < extreme_size:    params = {}
for i, param_name in enumerateparam_names:    range_values = param_ranges[i]

if np.random.random() < 0.5:    params[param_name] = range_values[0]  # 最小值
else:    params[param_name] = range_values[-1]  # 最大值

if space.validate_combinationparams:
combinations.append(params.copy())
extreme_count += 1

# 3. 中間值採樣 10%
middle_size = intsample_size * 0.1
middle_count = 0

while middle_count < middle_size:    params = {}
for i, param_name in enumerateparam_names:    range_values = param_ranges[i]

middle_idx = lenrange_values // 2
offset = np.random.randint(-lenrange_values//4, lenrange_values//4)
idx = max(0, min(lenrange_values-1, middle_idx + offset))
params[param_name] = range_values[idx]

if space.validate_combinationparams:
combinations.append(params.copy())
middle_count += 1

logger.info(f"Generated {lencombinations} smart sampled combinations for {space_name}")
return combinations

def save_combinationsself, space_name: str, combinations: List[Dict], filename: Optional[str] = None -> str:
"""保存參數組合到文件"""
if not filename:    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"{space_name}_combinations_{timestamp}.json"

filepath = self.cache_dir / filename

data = {
"space_name": space_name,
"timestamp": datetime.now().isoformat(),
"total_combinations": lencombinations,
"parameter_space": {
"name": self.parameter_spaces[space_name].name,
"description": self.parameter_spaces[space_name].description,
"parameters": [
{
"name": p.name,
"min_value": p.min_value,
"max_value": p.max_value,
"step": p.step,
"type": p.param_type
}
for p in self.parameter_spaces[space_name].parameters
]
},
"combinations": combinations
}

with openfilepath, 'w', encoding='utf-8' as f:    json.dump(data, f, ensure_ascii=False, indent=2)

logger.info(f"Saved {lencombinations} combinations to {filepath}")
return strfilepath

def load_combinationsself, filepath: str -> Tuple[str, List[Dict]]:
"""從文件加載參數組合"""
filepath = Pathfilepath
if not filepath.exists():
raise FileNotFoundErrorf"Parameter combinations file not found: {filepath}"

with openfilepath, 'r', encoding='utf-8' as f:    data = json.load(f)

space_name = data["space_name"]
combinations = data["combinations"]

logger.info(f"Loaded {lencombinations} combinations for {space_name} from {filepath}")
return space_name, combinations

def get_space_statisticsself, space_name: str -> Dict:
"""獲取參數空間統計信息"""
space = self.get_parameter_spacespace_name

stats = {
"name": space.name,
"description": space.description,
"total_parameters": lenspace.parameters,
"total_combinations": space.get_total_combinations(),
"constraints_count": lenspace.constraints,
"parameters": []
}

for param in space.parameters:    param_range = param.generate_range()
stats["parameters"].append({
"name": param.name,
"type": param.param_type,
"min_value": param.min_value,
"max_value": param.max_value,
"step": param.step,
"range_size": lenparam_range,
"values": param_range[:10] if lenparam_range > 10 else param_range # 顯示前10個值
})

return stats

def optimize_for_0700_hkself -> Dict[str, Any]:
"""為0700.HK優化參數空間"""
# 基於0700.HK的歷史波動率和交易特性調整參數範圍
optimized_spaces = {}

# RSI - 騰訊通常波動較大，調整範圍
rsi_space = self.parameter_spaces["RSI_0_300"]
rsi_space.parameters[0].min_value = 10 # RSI period min: 10 from 5
rsi_space.parameters[0].step = 2 # RSI period step: 2 from 1

# MACD - 適合科技股的快速變化
macd_space = self.parameter_spaces["MACD_0_300"]
macd_space.parameters[0].max_value = 50 # Fast EMA max: 50 from 300
macd_space.parameters[1].max_value = 100 # Slow EMA max: 100 from 300

# 布林帶 - 考慮科技股的高波動性
bb_space = self.parameter_spaces["BOLLINGER_0_300"]
bb_space.parameters[1].max_value = 4.0 # Std Dev max: 4.0 from 3.0

# 移動平均 - 適合較短週期
ma_space = self.parameter_spaces["MA_0_300"]
ma_space.parameters[0].max_value = 30 # Short MA max: 30 from 300
ma_space.parameters[1].max_value = 120 # Long MA max: 120 from 300

return optimized_spaces

def main():
"""測試函數"""
manager = HK700ParameterManager()

# 測試獲取統計信息
for space_name in ["RSI_0_300", "MACD_0_300", "COMBINED_0_300"]:    stats = manager.get_space_statistics(space_name)
printf"\n{space_name} 統計信息:"
printf" 總組合數: {stats['total_combinations']:,}"
printf" 參數數量: {stats['total_parameters']}"
printf" 約束數量: {stats['constraints_count']}"

# 生成少量測試組合
combinations = list(manager.generate_combinationsspace_name, max_combinations=5)
printf" 示例組合: {combinations[:1]}"

if __name__ == "__main__":
main()