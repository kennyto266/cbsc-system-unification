/**
 * Data Validation Utilities
 * 數據驗證工具，用於驗證API響應數據的完整性和正確性
 *
 * Task #002: API接口集成和數據獲取
 */

// 驗證結果接口
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  data?: any;
}

// 數字範圍選項
interface NumberRange {
  min?: number;
  max?: number;
}

// 策略性能數據驗證器
export const validateStrategyPerformance = (data: any): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  // 檢查必需字段
  if (!data || typeof data !== 'object') {
    errors.push('策略性能數據必須是對象');
    return { isValid: false, errors, warnings };
  }

  // 驗證name字段
  if (!data.name || typeof data.name !== 'string') {
    errors.push('缺少策略名稱或名稱格式無效');
  }

  // 驗證數值字段
  const numericFields = [
    { key: 'sharpe_ratio', name: '夏普比率', range: { min: -10, max: 10 } },
    { key: 'max_drawdown', name: '最大回撤', range: { min: -1, max: 0 } },
    { key: 'total_return', name: '總回報率', range: { min: -10, max: 10 } },
    { key: 'win_rate', name: '勝率', range: { min: 0, max: 1 } },
    { key: 'daily_pnl', name: '每日盈虧', range: { min: -1000000, max: 1000000 } },
    { key: 'volatility', name: '波動率', range: { min: 0, max: 10 } },
    { key: 'calmar_ratio', name: '卡瑪比率', range: { min: -10, max: 10 } },
    { key: 'profit_factor', name: '盈利因子', range: { min: 0, max: 100 } }
  ];

  for (const field of numericFields) {
    const value = data[field.key];

    if (value !== undefined && value !== null) {
      if (typeof value !== 'number' || isNaN(value)) {
        errors.push(`${field.name}必須是有效數字`);
      } else if (field.range) {
        if (field.range.min !== undefined && value < field.range.min) {
          warnings.push(`${field.name}(${value})低於預期最小值(${field.range.min})`);
        }
        if (field.range.max !== undefined && value > field.range.max) {
          warnings.push(`${field.name}(${value})超過預期最大值(${field.range.max})`);
        }
      }
    } else if (field.key === 'sharpe_ratio' || field.key === 'max_drawdown' ||
               field.key === 'total_return' || field.key === 'win_rate') {
      errors.push(`缺少必需字段: ${field.name}`);
    }
  }

  // 驗證status字段
  if (data.status && !['enabled', 'disabled'].includes(data.status)) {
    errors.push('策略狀態必須是enabled或disabled');
  }

  // 驗證時間戳
  if (data.last_updated) {
    const date = new Date(data.last_updated);
    if (isNaN(date.getTime())) {
      errors.push('last_updated必須是有效的日期時間格式');
    }
  }

  // 數據合理性檢查
  if (data.win_rate !== undefined && data.win_rate < 0.3) {
    warnings.push('勝率較低，可能需要檢查策略參數');
  }

  if (data.max_drawdown !== undefined && data.max_drawdown < -0.5) {
    warnings.push('最大回撤超過50%，風險較高');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    data: errors.length === 0 ? data : undefined
  };
};

// 策略配置數據驗證器
export const validateStrategyConfig = (data: any): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!data || typeof data !== 'object') {
    errors.push('策略配置數據必須是對象');
    return { isValid: false, errors, warnings };
  }

  // 必需字段檢查
  const requiredFields = ['name', 'enabled', 'description', 'strategy_type'];
  for (const field of requiredFields) {
    if (!data[field]) {
      errors.push(`缺少必需字段: ${field}`);
    }
  }

  // 類型檢查
  if (typeof data.name !== 'string') {
    errors.push('策略名稱必須是字符串');
  }

  if (typeof data.enabled !== 'boolean') {
    errors.push('enabled必須是布爾值');
  }

  if (typeof data.description !== 'string') {
    errors.push('描述必須是字符串');
  }

  // 參數檢查
  if (data.parameters && typeof data.parameters !== 'object') {
    errors.push('parameters必須是對象');
  }

  // 時間戳檢查
  const dateFields = ['created_at', 'updated_at'];
  for (const field of dateFields) {
    if (data[field]) {
      const date = new Date(data[field]);
      if (isNaN(date.getTime())) {
        errors.push(`${field}必須是有效的日期時間格式`);
      }
    }
  }

  // 合理性檢查
  if (data.name && data.name.length < 2) {
    warnings.push('策略名稱過短');
  }

  if (data.description && data.description.length < 10) {
    warnings.push('策略描述過短，可能無法清楚說明策略功能');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    data: errors.length === 0 ? data : undefined
  };
};

// 策略詳細信息驗證器
export const validateStrategyDetail = (data: any): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!data || typeof data !== 'object') {
    errors.push('策略詳細信息必須是對象');
    return { isValid: false, errors, warnings };
  }

  // 驗證config部分
  if (data.config) {
    const configValidation = validateStrategyConfig(data.config);
    errors.push(...configValidation.errors);
    warnings.push(...configValidation.warnings);
  } else {
    errors.push('缺少策略配置信息');
  }

  // 驗證performance部分
  if (data.performance) {
    const perfValidation = validateStrategyPerformance(data.performance);
    errors.push(...perfValidation.errors);
    warnings.push(...perfValidation.warnings);
  } else {
    errors.push('缺少策略性能信息');
  }

  // 驗證last_signal
  if (data.last_signal) {
    const signal = data.last_signal;
    const signalFields = ['type', 'timestamp'];

    for (const field of signalFields) {
      if (!signal[field]) {
        errors.push(`信號缺少必需字段: ${field}`);
      }
    }

    if (signal.type && !['buy', 'sell', 'hold'].includes(signal.type)) {
      errors.push('信號類型必須是buy、sell或hold');
    }

    if (signal.strength !== undefined) {
      if (typeof signal.strength !== 'number' || signal.strength < 0 || signal.strength > 100) {
        errors.push('信號強度必須是0-100之間的數字');
      }
    }

    if (signal.timestamp) {
      const date = new Date(signal.timestamp);
      if (isNaN(date.getTime())) {
        errors.push('信號時間戳格式無效');
      }
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    data: errors.length === 0 ? data : undefined
  };
};

// 性能摘要驗證器
export const validatePerformanceSummary = (data: any): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!data || typeof data !== 'object') {
    errors.push('性能摘要必須是對象');
    return { isValid: false, errors, warnings };
  }

  // 數值字段驗證
  const numericFields = [
    { key: 'total_strategies', name: '總策略數', min: 0, max: 10000 },
    { key: 'active_strategies', name: '活躍策略數', min: 0, max: 10000 },
    { key: 'total_return', name: '總回報率', min: -10, max: 10 },
    { key: 'daily_pnl', name: '每日盈虧', min: -1000000, max: 1000000 },
    { key: 'sharpe_ratio', name: '夏普比率', min: -10, max: 10 },
    { key: 'max_drawdown', name: '最大回撤', min: -1, max: 0 },
    { key: 'win_rate', name: '勝率', min: 0, max: 1 }
  ];

  for (const field of numericFields) {
    const value = data[field.key];

    if (value !== undefined && value !== null) {
      if (typeof value !== 'number' || isNaN(value)) {
        errors.push(`${field.name}必須是有效數字`);
      } else {
        if (field.min !== undefined && value < field.min) {
          warnings.push(`${field.name}(${value})低於預期最小值(${field.min})`);
        }
        if (field.max !== undefined && value > field.max) {
          warnings.push(`${field.name}(${value})超過預期最大值(${field.max})`);
        }
      }
    } else {
      errors.push(`缺少必需字段: ${field.name}`);
    }
  }

  // 邏輯檢查
  if (data.active_strategies && data.total_strategies) {
    if (data.active_strategies > data.total_strategies) {
      errors.push('活躍策略數不能大於總策略數');
    }
  }

  if (data.best_strategy && data.worst_strategy) {
    if (data.best_strategy.sharpe_ratio <= data.worst_strategy.sharpe_ratio) {
      warnings.push('最佳策略的夏普比率應該高於最差策略');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    data: errors.length === 0 ? data : undefined
  };
};

// 通用數組驗證器
export const validateArray = (
  data: any,
  itemValidator: (item: any) => ValidationResult,
  itemName: string = '項目'
): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];
  const validItems: any[] = [];

  if (!Array.isArray(data)) {
    errors.push(`${itemName}列表必須是數組`);
    return { isValid: false, errors, warnings };
  }

  data.forEach((item, index) => {
    const validation = itemValidator(item);
    if (validation.isValid) {
      validItems.push(validation.data || item);
    } else {
      errors.push(`${itemName}[${index}]: ${validation.errors.join(', ')}`);
    }
    warnings.push(...validation.warnings.map(w => `${itemName}[${index}]: ${w}`));
  });

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    data: validItems
  };
};

// API響應格式驗證器
export const validateApiResponse = (data: any): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!data || typeof data !== 'object') {
    errors.push('API響應必須是對象');
    return { isValid: false, errors, warnings };
  }

  // 檢查必要字段
  if (!data.hasOwnProperty('success')) {
    errors.push('API響應缺少success字段');
  }

  if (data.success === true && !data.data) {
    warnings.push('成功響應缺少data字段');
  }

  if (data.success === false && !data.error && !data.message) {
    warnings.push('錯誤響應缺少錯誤信息');
  }

  // 檢查時間戳
  if (data.timestamp) {
    const date = new Date(data.timestamp);
    if (isNaN(date.getTime())) {
      errors.push('timestamp必須是有效的日期時間格式');
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    data
  };
};

// 數據清理工具
export const sanitizeData = (data: any): any => {
  if (data === null || data === undefined) {
    return data;
  }

  if (typeof data === 'object') {
    if (Array.isArray(data)) {
      return data.map(sanitizeData);
    }

    const sanitized: any = {};
    for (const [key, value] of Object.entries(data)) {
      // Remove null/undefined values
      if (value !== null && value !== undefined) {
        sanitized[key] = sanitizeData(value);
      }
    }
    return sanitized;
  }

  // For primitive types, return as-is
  return data;
};

// 數據轉換工具
export const transformPerformanceData = (data: any): any => {
  if (!data) return data;

  const transformed = { ...data };

  // Ensure numeric fields are numbers
  const numericFields = [
    'sharpe_ratio', 'max_drawdown', 'total_return', 'win_rate',
    'daily_pnl', 'volatility', 'calmar_ratio', 'profit_factor'
  ];

  numericFields.forEach(field => {
    if (transformed[field] !== undefined && transformed[field] !== null) {
      const num = parseFloat(transformed[field]);
      transformed[field] = isNaN(num) ? 0 : num;
    }
  });

  // Ensure status is normalized
  if (transformed.status) {
    transformed.status = transformed.status.toString().toLowerCase();
  }

  return transformed;
};

// 導出所有驗證器
export const validators = {
  strategyPerformance: validateStrategyPerformance,
  strategyConfig: validateStrategyConfig,
  strategyDetail: validateStrategyDetail,
  performanceSummary: validatePerformanceSummary,
  array: validateArray,
  apiResponse: validateApiResponse
};

// 導出工具函數
export const utils = {
  sanitize: sanitizeData,
  transform: transformPerformanceData
};