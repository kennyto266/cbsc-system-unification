#!/usr/bin/env python3
"""
批量更新缓存逻辑脚本
Batch Update Caching Logic Script

将所有指标方法更新为使用新的优化缓存系统

Author: Claude Code Assistant
Created: 2025-11-29
"""

import re

def update_indicator_method(content: str, method_name: str, param_names: list = None) -> str:
    """
    更新单个指标方法的缓存逻辑

    Args:
        content: 文件内容
        method_name: 方法名称
        param_names: 参数名称列表

    Returns:
        更新后的内容
    """
    if param_names is None:
        param_names = ['period']

    # 构建参数字典字符串
    param_dict = ", ".join([f"'{p}': {p}" for p in param_names])

    # 构建新的缓存逻辑
    new_cache_logic = f"""def calculate_{method_name}(self{', ' + ', '.join([f' {p}: int = 20' for p in param_names]) if param_names else ''}) -> pd.Series:
        \"\"\"计算{method_name.upper()}指标\"\"\"
        # 尝试从缓存获取
        cached_result = self.cache_manager.get('{method_name}', data, {{{param_dict}}})
        if cached_result is not None:
            return cached_result

        # 计算新结果
        result = # [原有计算逻辑]

        # 存入缓存
        self.cache_manager.put('{method_name}', data, result, {{{param_dict}}}, timeout=300)

        return result"""

    # 查找方法定义
    method_pattern = rf'def calculate_{method_name}\(self[^)]*\):.*?(?=def |\nclass |$)'

    match = re.search(method_pattern, content, re.DOTALL)
    if not match:
        return content

    original_method = match.group(0)

    # 提取参数
    param_pattern = r'def calculate_' + method_name + r'\(self([^)]*)\)'
    param_match = re.search(param_pattern, original_method)
    if param_match:
        params = param_match.group(1).strip()
        if params:
            param_list = [p.strip().split(':')[0] for p in params.split(',')]
            param_dict = ", ".join([f"'{p}': {p}" for p in param_list if p])

    # 构建新的方法
    lines = original_method.split('\n')
    docstring_line = -1
    implementation_start = -1

    for i, line in enumerate(lines):
        if '"""' in line:
            docstring_line = i
        if docstring_line != -1 and 'cache_key' in line:
            implementation_start = i
            break

    if implementation_start == -1:
        return content

    # 保留文档字符串
    new_lines = lines[:implementation_start]

    # 添加新的缓存逻辑
    cache_params = {}
    if param_names:
        cache_params = {p: p for p in param_names}

    # 构建参数字典
    param_str = ", ".join([f"'{k}': {v}" for k, v in cache_params.items()])

    new_lines.append("        # 尝试从缓存获取")
    new_lines.append(f"        cached_result = self.cache_manager.get('{method_name}', data, {{{param_str}}})")
    new_lines.append("        if cached_result is not None:")
    new_lines.append("            return cached_result")
    new_lines.append("")
    new_lines.append("        # 计算新结果")

    # 找到原始计算逻辑（跳过缓存相关代码）
    calc_lines = []
    in_calculation = False
    for line in lines[implementation_start:]:
        if 'cache_key' not in line and '_is_cache_valid' not in line and '_cache_result' not in line:
            if not in_calculation and (line.strip().startswith('sma =') or line.strip().startswith('ema =') or
                                      line.strip().startswith('rsi =') or line.strip().startswith('delta =') or
                                      'return' in line):
                in_calculation = True

            if in_calculation:
                # 替换return语句
                if 'self._cache_result' in line:
                    continue
                if 'return' in line and 'sma' in line or 'ema' in line or 'rsi' in line:
                    calc_lines.append("        result = " + line.strip().replace('return ', '').replace(';', ''))
                    calc_lines.append("")
                    calc_lines.append("        # 存入缓存")
                    calc_lines.append(f"        self.cache_manager.put('{method_name}', data, result, {{{param_str}}}, timeout=300)")
                    calc_lines.append("")
                    calc_lines.append("        return result")
                    break
                else:
                    calc_lines.append(line)

    new_lines.extend(calc_lines)

    # 替换原始方法
    updated_content = content.replace(original_method, '\n'.join(new_lines))

    return updated_content

def main():
    """主函数：更新所有缓存逻辑"""
    print("Updating indicator caching logic...")

    # 读取当前文件
    with open('core_indicators.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 需要更新的方法列表
    methods_to_update = [
        ('sma', ['period']),
        ('ema', ['period']),
        ('rsi', ['period']),
        ('macd', ['fast', 'slow', 'signal']),
        ('bollinger_bands', ['period', 'std_dev']),
        ('atr', ['period']),
        ('stochastic', ['k_period', 'd_period']),
        ('williams_r', ['period']),
        ('cci', ['period']),
        ('obv', []),
        ('vwap', []),
        ('mfi', ['period']),
        ('volume_sma', ['period']),
        ('hibor_momentum', ['period']),
        ('monetary_base_change', ['period']),
    ]

    updated_content = content

    # 逐个更新方法
    for method_name, params in methods_to_update:
        print(f"  Updating {method_name}...")
        updated_content = update_indicator_method(updated_content, method_name, params)

    # 更新缓存管理相关方法
    updated_content = re.sub(
        r'def _is_cache_valid.*?return False',
        'def _is_cache_valid(self, cache_key: str) -> bool:\n        """旧版本缓存检查 - 已弃用，使用新缓存系统"""\n        return False',
        updated_content,
        flags=re.DOTALL
    )

    updated_content = re.sub(
        r'def _cache_result.*?timestamp\(\)\)',
        'def _cache_result(self, cache_key: str, result):\n        """旧版本缓存存储 - 已弃用，使用新缓存系统"""\n        pass',
        updated_content,
        flags=re.DOTALL
    )

    # 更新clear_cache方法
    old_clear_cache = r'def clear_cache.*?logger\.info\("技术指标缓存已清空"\)'
    new_clear_cache = """def clear_cache(self, indicator_name: str = None):
        \"\"\"清空指标缓存\"\"\"
        if indicator_name:
            self.cache_manager.clear(indicator_name)
            logger.info(f"{indicator_name} 指标缓存已清空")
        else:
            self.cache_manager.clear()
            logger.info("所有技术指标缓存已清空")"""

    updated_content = re.sub(old_clear_cache, new_clear_cache, updated_content, flags=re.DOTALL)

    # 更新get_cache_info方法
    old_cache_info = r'def get_cache_info.*?cached_indicators.*?\]'
    new_cache_info = """def get_cache_info(self) -> Dict[str, Union[int, List[str]]]:
        \"\"\"获取缓存信息\"\"\"
        stats = self.cache_manager.get_stats()
        return {
            'cache_size': stats['cache_size'],
            'memory_usage_mb': stats['memory_usage_mb'],
            'hit_rate_percent': stats['hit_rate_percent'],
            'top_indicators': list(self.cache_manager.get_top_indicators(5).keys())
        }"""

    updated_content = re.sub(old_cache_info, new_cache_info, updated_content, flags=re.DOTALL)

    # 写入更新后的文件
    with open('core_indicators.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print("All indicator caching logic updated successfully!")
    print("Optimized caching system is now active.")

if __name__ == "__main__":
    main()