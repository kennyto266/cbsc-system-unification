/**
 * Input Validation Utilities
 * Provides comprehensive input validation for the CBSC Dashboard
 */

// Validation rule types
type ValidationRule = {
  pattern?: RegExp;
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  required?: boolean;
  allowEmpty?: boolean;
  custom?: (value: any) => boolean | string;
  message?: string;
};

type ValidationSchema = {
  [field: string]: ValidationRule | ValidationRule[];
};

// Predefined validation patterns
export const VALIDATION_PATTERNS = {
  // General patterns
  email: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
  phone: /^\+?[\d\s\-\(\)]+$/,
  url: /^https?:\/\/[^\s/$.?#].[^\s]*$/,
  username: /^[a-zA-Z0-9_]{3,20}$/,
  password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/,

  // Financial patterns
  currency: /^\$?\d{1,3}(,\d{3})*(\.\d{2})?$/,
  percentage: /^\d+(\.\d+)?%?$/,
  stockSymbol: /^[A-Z]{1,5}$/,
  isin: /^[A-Z]{2}[A-Z0-9]{9}[0-9]$/,
  cusip: /^[0-9A-Z]{9}$/,

  // Date patterns
  dateISO: /^\d{4}-\d{2}-\d{2}$/,
  datetimeISO: /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/,
  time: /^([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$/,

  // ID patterns
  uuid: /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
  numeric: /^\d+$/,
  alphanumeric: /^[a-zA-Z0-9]+$/,
  hex: /^[0-9a-fA-F]+$/,

  // Security patterns
  sqlInjection: /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)/i,
  xssPattern: /<script[^>]*>.*?<\/script>|javascript:|on\w+\s*=/gi,
  pathTraversal: /\.\.[\/\\]/,
  commandInjection: /[;&|`$(){}[\]]/
};

/**
 * Input Validation class
 */
export class InputValidator {
  private static instance: InputValidator;
  private customRules: Map<string, ValidationRule[]> = new Map();

  private constructor() {}

  /**
   * Singleton instance getter
   */
  public static getInstance(): InputValidator {
    if (!InputValidator.instance) {
      InputValidator.instance = new InputValidator();
    }
    return InputValidator.instance;
  }

  /**
   * Validate a single value against a rule
   */
  public validate(value: any, rule: ValidationRule): { valid: boolean; message?: string } {
    // Check required
    if (rule.required && (value === null || value === undefined || value === '')) {
      return {
        valid: false,
        message: rule.message || 'This field is required'
      };
    }

    // Allow empty check
    if (!rule.allowEmpty && (value === null || value === undefined || value === '')) {
      return { valid: true };
    }

    // Convert to string for pattern matching
    const stringValue = String(value);

    // Pattern validation
    if (rule.pattern && !rule.pattern.test(stringValue)) {
      return {
        valid: false,
        message: rule.message || 'Invalid format'
      };
    }

    // Length validation
    if (rule.minLength !== undefined && stringValue.length < rule.minLength) {
      return {
        valid: false,
        message: rule.message || `Minimum length is ${rule.minLength}`
      };
    }

    if (rule.maxLength !== undefined && stringValue.length > rule.maxLength) {
      return {
        valid: false,
        message: rule.message || `Maximum length is ${rule.maxLength}`
      };
    }

    // Numeric range validation
    if (rule.min !== undefined && Number(value) < rule.min) {
      return {
        valid: false,
        message: rule.message || `Minimum value is ${rule.min}`
      };
    }

    if (rule.max !== undefined && Number(value) > rule.max) {
      return {
        valid: false,
        message: rule.message || `Maximum value is ${rule.max}`
      };
    }

    // Custom validation
    if (rule.custom) {
      const customResult = rule.custom(value);
      if (customResult !== true) {
        return {
          valid: false,
          message: typeof customResult === 'string' ? customResult : rule.message || 'Validation failed'
        };
      }
    }

    return { valid: true };
  }

  /**
   * Validate an object against a schema
   */
  public validateSchema(data: any, schema: ValidationSchema): {
    valid: boolean;
    errors: { [field: string]: string };
    sanitized: any;
  } {
    const errors: { [field: string]: string } = {};
    const sanitized: any = {};

    // Check each field in schema
    for (const [field, rules] of Object.entries(schema)) {
      const fieldRules = Array.isArray(rules) ? rules : [rules];
      const value = data[field];

      let isValid = true;
      let errorMessage: string | undefined;

      // Validate against each rule
      for (const rule of fieldRules) {
        const result = this.validate(value, rule);
        if (!result.valid) {
          isValid = false;
          errorMessage = result.message;
          break;
        }
      }

      if (!isValid && errorMessage) {
        errors[field] = errorMessage;
      } else if (value !== undefined && value !== null) {
        // Sanitize and store valid value
        sanitized[field] = this.sanitize(value);
      }
    }

    // Check for unexpected fields
    for (const [field, value] of Object.entries(data)) {
      if (!(field in schema)) {
        console.warn(`Unexpected field in validation: ${field}`);
      }
    }

    return {
      valid: Object.keys(errors).length === 0,
      errors,
      sanitized
    };
  }

  /**
   * Sanitize input value
   */
  public sanitize(value: any): any {
    if (typeof value === 'string') {
      // Remove potential XSS vectors
      return value
        .replace(/<script[^>]*>.*?<\/script>/gi, '')
        .replace(/javascript:/gi, '')
        .replace(/on\w+\s*=/gi, '')
        .trim();
    }

    if (typeof value === 'object' && value !== null) {
      if (Array.isArray(value)) {
        return value.map(item => this.sanitize(item));
      }

      const sanitized: any = {};
      for (const [key, val] of Object.entries(value)) {
        sanitized[this.sanitize(key)] = this.sanitize(val);
      }
      return sanitized;
    }

    return value;
  }

  /**
   * Validate and sanitize user input for security
   */
  public validateSecureInput(input: string, type: 'text' | 'html' | 'url' | 'json' = 'text'): {
    valid: boolean;
    sanitized: string;
    threats: string[];
  } {
    const threats: string[] = [];
    let sanitized = input;

    // Check for XSS patterns
    if (VALIDATION_PATTERNS.xssPattern.test(input)) {
      threats.push('XSS');
      sanitized = sanitized.replace(/<[^>]*>/g, '');
    }

    // Check for SQL injection patterns
    if (VALIDATION_PATTERNS.sqlInjection.test(input)) {
      threats.push('SQL Injection');
      sanitized = sanitized.replace(/\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b/gi, '');
    }

    // Check for path traversal
    if (VALIDATION_PATTERNS.pathTraversal.test(input)) {
      threats.push('Path Traversal');
      sanitized = sanitized.replace(/\.\.[\/\\]/g, '');
    }

    // Check for command injection
    if (VALIDATION_PATTERNS.commandInjection.test(input)) {
      threats.push('Command Injection');
      sanitized = sanitized.replace(/[;&|`$(){}[\]]/g, '');
    }

    // Type-specific validation
    switch (type) {
      case 'html':
        // Additional HTML sanitization would go here
        // Use a library like DOMPurify in production
        break;

      case 'url':
        try {
          new URL(sanitized);
        } catch {
          threats.push('Invalid URL');
          sanitized = '';
        }
        break;

      case 'json':
        try {
          JSON.parse(sanitized);
        } catch {
          threats.push('Invalid JSON');
          sanitized = '{}';
        }
        break;
    }

    return {
      valid: threats.length === 0,
      sanitized: sanitized.trim(),
      threats
    };
  }

  /**
   * Validate financial data
   */
  public validateFinancialData(data: any): {
    valid: boolean;
    errors: string[];
    sanitized: any;
  } {
    const errors: string[] = [];
    const sanitized: any = {};

    // Validate amount
    if (data.amount !== undefined) {
      if (!VALIDATION_PATTERNS.currency.test(String(data.amount))) {
        errors.push('Invalid currency format');
      } else {
        sanitized.amount = parseFloat(String(data.amount).replace(/[$,]/g, ''));
      }
    }

    // Validate percentage
    if (data.percentage !== undefined) {
      if (!VALIDATION_PATTERNS.percentage.test(String(data.percentage))) {
        errors.push('Invalid percentage format');
      } else {
        sanitized.percentage = parseFloat(String(data.percentage).replace('%', ''));
      }
    }

    // Validate stock symbol
    if (data.symbol !== undefined) {
      if (!VALIDATION_PATTERNS.stockSymbol.test(String(data.symbol))) {
        errors.push('Invalid stock symbol');
      } else {
        sanitized.symbol = String(data.symbol).toUpperCase();
      }
    }

    // Validate date range
    if (data.startDate && data.endDate) {
      const start = new Date(data.startDate);
      const end = new Date(data.endDate);

      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        errors.push('Invalid date format');
      } else if (start > end) {
        errors.push('Start date must be before end date');
      } else {
        sanitized.startDate = data.startDate;
        sanitized.endDate = data.endDate;
      }
    }

    // Copy safe fields
    ['id', 'name', 'description', 'type'].forEach(field => {
      if (data[field] !== undefined) {
        sanitized[field] = this.sanitize(data[field]);
      }
    });

    return {
      valid: errors.length === 0,
      errors,
      sanitized
    };
  }

  /**
   * Register custom validation rule
   */
  public registerRule(name: string, rules: ValidationRule[]): void {
    this.customRules.set(name, rules);
  }

  /**
   * Get registered rule
   */
  public getRule(name: string): ValidationRule[] | undefined {
    return this.customRules.get(name);
  }

  /**
   * Validate using registered rule
   */
  public validateUsingRule(data: any, ruleName: string): {
    valid: boolean;
    errors: { [field: string]: string };
    sanitized: any;
  } {
    const rules = this.customRules.get(ruleName);
    if (!rules) {
      throw new Error(`Validation rule '${ruleName}' not found`);
    }

    // Convert rules array to schema format
    const schema: ValidationSchema = {};
    rules.forEach((rule, index) => {
      schema[`field${index}`] = rule;
    });

    return this.validateSchema(data, schema);
  }
}

// Export singleton instance
export const inputValidator = InputValidator.getInstance();

// Predefined validation schemas
export const USER_SCHEMA: ValidationSchema = {
  username: {
    pattern: VALIDATION_PATTERNS.username,
    required: true,
    message: 'Username must be 3-20 characters, alphanumeric and underscore only'
  },
  email: {
    pattern: VALIDATION_PATTERNS.email,
    required: true,
    message: 'Invalid email address'
  },
  password: {
    pattern: VALIDATION_PATTERNS.password,
    required: true,
    minLength: 8,
    message: 'Password must be at least 8 characters with uppercase, lowercase, and number'
  },
  phone: {
    pattern: VALIDATION_PATTERNS.phone,
    required: false,
    message: 'Invalid phone number'
  }
};

export const STRATEGY_SCHEMA: ValidationSchema = {
  name: {
    required: true,
    minLength: 1,
    maxLength: 100,
    message: 'Strategy name is required (max 100 characters)'
  },
  description: {
    maxLength: 1000,
    message: 'Description too long (max 1000 characters)'
  },
  symbol: {
    pattern: VALIDATION_PATTERNS.stockSymbol,
    required: true,
    message: 'Invalid stock symbol'
  },
  initialCapital: {
    pattern: VALIDATION_PATTERNS.currency,
    required: true,
    min: 1000,
    message: 'Initial capital must be at least $1,000'
  },
  startDate: {
    pattern: VALIDATION_PATTERNS.dateISO,
    required: true,
    message: 'Invalid start date format (YYYY-MM-DD)'
  },
  endDate: {
    pattern: VALIDATION_PATTERNS.dateISO,
    required: true,
    message: 'Invalid end date format (YYYY-MM-DD)'
  }
};

// Convenience functions
export const validateInput = (value: any, rule: ValidationRule): { valid: boolean; message?: string } =>
  inputValidator.validate(value, rule);
export const validateSecure = (input: string, type?: 'text' | 'html' | 'url' | 'json') =>
  inputValidator.validateSecureInput(input, type);
export const validateFinancial = (data: any) =>
  inputValidator.validateFinancialData(data);