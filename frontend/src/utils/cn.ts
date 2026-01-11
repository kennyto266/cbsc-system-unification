/**
 * cn - Utility function for className merging
 * 版本: 1.0.0
 * 描述: 優雅的類名合併工具函數，使用clsx庫
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * 優雅的類名合併函數
 * 結合了clsx和tailwind-merge
 *
 * @param inputs - 類名輸入
 * @returns 合併後的類名字符串
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * 導出默認
 */
export default cn;