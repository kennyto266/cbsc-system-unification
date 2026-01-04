/**
 * Date Utilities
 * 日期工具函數
 */

/**
 * Format date to localized string
 * 格式化日期為本地化字符串
 */
export const formatDate = (dateString: string): string => {
  try {
    return new Date(dateString).toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return '無效日期';
  }
};

/**
 * Format date to short string
 * 格式化日期為短字符串
 */
export const formatDateShort = (dateString: string): string => {
  try {
    return new Date(dateString).toLocaleString('zh-TW', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return '無效日期';
  }
};

/**
 * Format date to relative time
 * 格式化日期為相對時間
 */
export const formatRelativeTime = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays}天前`;
    } else if (diffHours > 0) {
      return `${diffHours}小時前`;
    } else if (diffMinutes > 0) {
      return `${diffMinutes}分鐘前`;
    } else {
      return '剛剛';
    }
  } catch (error) {
    return '未知時間';
  }
};

/**
 * Check if date is today
 * 檢查日期是否為今天
 */
export const isToday = (dateString: string): boolean => {
  try {
    const date = new Date(dateString);
    const today = new Date();

    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
  } catch (error) {
    return false;
  }
};

/**
 * Get start of day
 * 獲取一天的开始時間
 */
export const getStartOfDay = (date: Date = new Date()): Date => {
  const start = new Date(date);
  start.setHours(0, 0, 0, 0);
  return start;
};

/**
 * Get end of day
 * 獲取一天的结束時間
 */
export const getEndOfDay = (date: Date = new Date()): Date => {
  const end = new Date(date);
  end.setHours(23, 59, 59, 999);
  return end;
};

/**
 * Add days to date
 * 給日期添加天數
 */
export const addDays = (date: Date, days: number): Date => {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
};

/**
 * Subtract days from date
 * 從日期減去天數
 */
export const subtractDays = (date: Date, days: number): Date => {
  return addDays(date, -days);
};

/**
 * Format date range
 * 格式化日期範圍
 */
export const formatDateRange = (startDate: string, endDate: string): string => {
  try {
    const start = new Date(startDate);
    const end = new Date(endDate);

    return `${formatDate(startDate)} - ${formatDate(endDate)}`;
  } catch (error) {
    return '無效日期範圍';
  }
};

/**
 * Get date range for time period
 * 獲取時間段的日期範圍
 */
export const getDateRange = (period: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y'): { start: Date; end: Date } => {
  const end = new Date();
  let start: Date;

  switch (period) {
    case '1D':
      start = subtractDays(end, 1);
      break;
    case '1W':
      start = subtractDays(end, 7);
      break;
    case '1M':
      start = subtractDays(end, 30);
      break;
    case '3M':
      start = subtractDays(end, 90);
      break;
    case '6M':
      start = subtractDays(end, 180);
      break;
    case '1Y':
      start = subtractDays(end, 365);
      break;
    default:
      start = subtractDays(end, 30);
  }

  return { start, end };
};

export default {
  formatDate,
  formatDateShort,
  formatRelativeTime,
  isToday,
  getStartOfDay,
  getEndOfDay,
  addDays,
  subtractDays,
  formatDateRange,
  getDateRange
};