/**
 * API Validation Utilities
 * Provides validation functions for API requests and responses
 */

// Email validation
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// Password validation
export interface PasswordValidation {
  isValid: boolean
  errors: string[]
  score: number
}

export const validatePassword = (password: string): PasswordValidation => {
  const errors: string[] = []
  let score = 0

  // Length check
  if (password.length < 8) {
    errors.push('密码长度至少为8位')
  } else if (password.length >= 12) {
    score += 2
  } else {
    score += 1
  }

  // Uppercase letter
  if (/[A-Z]/.test(password)) {
    score += 1
  } else {
    errors.push('密码必须包含至少一个大写字母')
  }

  // Lowercase letter
  if (/[a-z]/.test(password)) {
    score += 1
  } else {
    errors.push('密码必须包含至少一个小写字母')
  }

  // Number
  if (/\d/.test(password)) {
    score += 1
  } else {
    errors.push('密码必须包含至少一个数字')
  }

  // Special character
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    score += 1
  } else {
    errors.push('密码必须包含至少一个特殊字符')
  }

  // Common patterns
  if (/(.)\1{2,}/.test(password)) {
    errors.push('密码不能包含连续相同字符')
    score -= 1
  }

  // Sequential characters
  const sequentialCheck = /(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)/i
  if (sequentialCheck.test(password)) {
    errors.push('密码不能包含连续字符')
    score -= 1
  }

  // Common passwords
  const commonPasswords = ['password', '123456', 'qwerty', 'admin', 'letmein']
  if (commonPasswords.some(common => password.toLowerCase().includes(common))) {
    errors.push('密码过于简单，请使用更复杂的密码')
    score -= 2
  }

  return {
    isValid: errors.length === 0 && score >= 4,
    errors,
    score: Math.max(0, Math.min(5, score)),
  }
}

// Username validation
export const validateUsername = (username: string): boolean => {
  // Alphanumeric and underscores only, 3-30 characters
  const usernameRegex = /^[a-zA-Z0-9_]{3,30}$/
  return usernameRegex.test(username)
}

// Phone number validation (international)
export const validatePhone = (phone: string, countryCode?: string): boolean => {
  // Remove all non-digit characters
  const digitsOnly = phone.replace(/\D/g, '')

  // Basic length check
  if (digitsOnly.length < 10 || digitsOnly.length > 15) {
    return false
  }

  // Country-specific validation
  switch (countryCode) {
    case 'CN':
      // China: 11 digits starting with 1
      return /^1[3-9]\d{9}$/.test(digitsOnly)
    case 'US':
    case 'CA':
      // North America: 10 digits
      return /^\d{10}$/.test(digitsOnly)
    case 'UK':
      // UK: 11 digits starting with 07
      return /^07\d{9}$/.test(digitsOnly)
    default:
      // General international format
      return /^\d{10,15}$/.test(digitsOnly)
  }
}

// Numeric range validation
export const validateRange = (value: number, min: number, max: number): boolean => {
  return value >= min && value <= max
}

// Required field validation
export const validateRequired = (value: any): boolean => {
  if (value === null || value === undefined) {
    return false
  }
  if (typeof value === 'string') {
    return value.trim().length > 0
  }
  if (Array.isArray(value)) {
    return value.length > 0
  }
  return true
}

// Array validation
export const validateArray = (value: any, minLength?: number, maxLength?: number): boolean => {
  if (!Array.isArray(value)) {
    return false
  }
  if (minLength !== undefined && value.length < minLength) {
    return false
  }
  if (maxLength !== undefined && value.length > maxLength) {
    return false
  }
  return true
}

// Date validation
export const validateDate = (date: string, format?: string): boolean => {
  const parsed = new Date(date)
  if (isNaN(parsed.getTime())) {
    return false
  }

  // Format-specific validation
  if (format) {
    const regex = new RegExp(format)
    return regex.test(date)
  }

  return true
}

// Date range validation
export const validateDateRange = (startDate: string, endDate: string): boolean => {
  const start = new Date(startDate)
  const end = new Date(endDate)

  if (isNaN(start.getTime()) || isNaN(end.getTime())) {
    return false
  }

  return start < end
}

// URL validation
export const validateURL = (url: string): boolean => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

// JSON validation
export const validateJSON = (jsonString: string): boolean => {
  try {
    JSON.parse(jsonString)
    return true
  } catch {
    return false
  }
}

// Symbol validation for trading
export const validateSymbol = (symbol: string): boolean => {
  // Common format: 2-5 uppercase letters, optional slash and additional letters
  const symbolRegex = /^[A-Z]{2,5}(?:\/[A-Z]{2,5})?$/
  return symbolRegex.test(symbol)
}

// Timeframe validation
export const validateTimeframe = (timeframe: string): boolean => {
  const validTimeframes = [
    '1m', '3m', '5m', '15m', '30m',
    '1h', '2h', '4h', '6h', '8h', '12h',
    '1d', '3d', '1w', '1M'
  ]
  return validTimeframes.includes(timeframe)
}

// Trade parameters validation
export interface TradeValidation {
  isValid: boolean
  errors: string[]
}

export const validateTradeParams = (params: {
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price?: number
  type?: string
}): TradeValidation => {
  const errors: string[] = []

  // Symbol validation
  if (!validateSymbol(params.symbol)) {
    errors.push('无效的交易代码格式')
  }

  // Side validation
  if (!['buy', 'sell'].includes(params.side)) {
    errors.push('交易方向必须是 buy 或 sell')
  }

  // Quantity validation
  if (!validateRequired(params.quantity) || params.quantity <= 0) {
    errors.push('交易数量必须大于0')
  }

  // Price validation for limit orders
  if (params.type === 'limit') {
    if (!validateRequired(params.price) || params.price <= 0) {
      errors.push('限价单的价格必须大于0')
    }
  }

  // Quantity precision validation
  const decimals = params.quantity.toString().split('.')[1]?.length || 0
  if (decimals > 8) {
    errors.push('交易数量精度不能超过8位小数')
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Strategy parameters validation
export const validateStrategyParams = (
  params: Record<string, any>,
  schema: Record<string, any>
): TradeValidation => {
  const errors: string[] = []

  for (const [key, value] of Object.entries(schema)) {
    const paramValue = params[key]

    // Required check
    if (value.required && !validateRequired(paramValue)) {
      errors.push(`参数 ${key} 是必需的`)
      continue
    }

    // Type check
    if (paramValue !== undefined) {
      switch (value.type) {
        case 'number':
          if (typeof paramValue !== 'number' || isNaN(paramValue)) {
            errors.push(`参数 ${key} 必须是数字`)
          } else {
            // Range check
            if (value.min !== undefined && paramValue < value.min) {
              errors.push(`参数 ${key} 不能小于 ${value.min}`)
            }
            if (value.max !== undefined && paramValue > value.max) {
              errors.push(`参数 ${key} 不能大于 ${value.max}`)
            }
          }
          break
        case 'string':
          if (typeof paramValue !== 'string') {
            errors.push(`参数 ${key} 必须是字符串`)
          }
          break
        case 'boolean':
          if (typeof paramValue !== 'boolean') {
            errors.push(`参数 ${key} 必须是布尔值`)
          }
          break
        case 'array':
          if (!Array.isArray(paramValue)) {
            errors.push(`参数 ${key} 必须是数组`)
          }
          break
      }
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

// API response validation
export const validateApiResponse = (response: any): boolean => {
  if (!response || typeof response !== 'object') {
    return false
  }

  // Check for required fields
  if ('success' in response && typeof response.success !== 'boolean') {
    return false
  }

  if ('data' in response) {
    // Data can be any type
  }

  if ('message' in response && typeof response.message !== 'string') {
    return false
  }

  if ('timestamp' in response) {
    const timestamp = new Date(response.timestamp)
    if (isNaN(timestamp.getTime())) {
      return false
    }
  }

  return true
}

// Sanitization functions
export const sanitizeString = (input: string): string => {
  return input.trim().replace(/[<>]/g, '')
}

export const sanitizeNumber = (input: any): number | null => {
  const num = parseFloat(input)
  return isNaN(num) ? null : num
}

export const sanitizeEmail = (email: string): string => {
  return email.toLowerCase().trim()
}

// File validation
export const validateFile = (
  file: File,
  allowedTypes: string[],
  maxSize: number
): { isValid: boolean; error?: string } => {
  // Type validation
  if (!allowedTypes.includes(file.type)) {
    return {
      isValid: false,
      error: `不支持的文件类型。允许的类型：${allowedTypes.join(', ')}`,
    }
  }

  // Size validation (in bytes)
  if (file.size > maxSize) {
    return {
      isValid: false,
      error: `文件大小超过限制。最大允许大小：${Math.round(maxSize / 1024 / 1024)}MB`,
    }
  }

  return { isValid: true }
}