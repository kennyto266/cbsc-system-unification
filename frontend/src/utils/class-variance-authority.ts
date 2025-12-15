/**
 * Class Variance Authority (CVA)
 * 版本: 1.0.0
 * 描述: 實用於創建變體樣式的工具函數
 */

import { type VariantProps, cva, cx } from 'class-variance-authority';

// 導出cva函數，保持與class-variance-authority庫的兼容性
export { cva, type VariantProps };

/**
 * 創建條件性類名的輔助函數
 *
 * @param condition - 條件
 * @param className - 條件為真時的類名
 * @returns 條件類名或空字符串
 */
export function cnConditional(
  condition: boolean,
  className: string
): string {
  return condition ? className : '';
}

/**
 * 多條件組合的類名函數
 *
 * @param conditions - 條件和類名的配對數組
 * @param defaultClassName - 默認類名
 * @returns 合併後的類名字符串
 */
export function cnMultiConditional(
  conditions: Record<string, boolean>,
  defaultClassName?: string
): string {
  const activeClasses = Object.entries(conditions)
    .filter(([_, active]) => active)
    .map(([className, _]) => className)
    .join(' ');

  return cx(activeClasses, defaultClassName);
}