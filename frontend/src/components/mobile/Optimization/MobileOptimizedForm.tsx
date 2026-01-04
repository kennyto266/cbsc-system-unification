import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Eye, EyeOff, AlertCircle, Check, X,
  Calendar, Clock, MapPin, User, Mail, Phone,
  Lock, CreditCard, Camera, Image as ImageIcon
} from 'lucide-react';
import TouchFeedback from '../TouchFeedback';
import GestureRecognizer, { GestureCallbacks } from '../Gesture/GestureRecognizer';
import { clsx } from 'clsx';

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'tel' | 'date' | 'time' | 'select' | 'textarea' | 'file' | 'switch';
  value?: any;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  readonly?: boolean;
  options?: Array<{ label: string; value: any }>;
  validation?: {
    pattern?: RegExp;
    minLength?: number;
    maxLength?: number;
    min?: number;
    max?: number;
    custom?: (value: any) => string | null;
  };
  icon?: React.ReactNode;
  autoComplete?: string;
  autoFocus?: boolean;
}

export interface MobileOptimizedFormProps {
  fields: FormField[];
  onSubmit: (values: Record<string, any>) => void | Promise<void>;
  initialValues?: Record<string, any>;
  submitButtonText?: string;
  submitButtonDisabled?: boolean;
  className?: string;
  showValidationErrors?: boolean;
  validateOnChange?: boolean;
  enableGestures?: boolean;
  autoAdvance?: boolean; // Auto advance to next field on enter
  stickySubmit?: boolean; // Keep submit button visible
  largeTouchTargets?: boolean; // Increase touch target sizes
}

interface ValidationErrors {
  [fieldName: string]: string | null;
}

/**
 * MobileOptimizedForm - Touch-optimized form component for mobile devices
 */
const MobileOptimizedForm: React.FC<MobileOptimizedFormProps> = ({
  fields,
  onSubmit,
  initialValues = {},
  submitButtonText = '提交',
  submitButtonDisabled = false,
  className,
  showValidationErrors = true,
  validateOnChange = true,
  enableGestures = true,
  autoAdvance = true,
  stickySubmit = true,
  largeTouchTargets = true,
}) => {
  const [values, setValues] = useState<Record<string, any>>(initialValues);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState<Record<string, boolean>>({});
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const inputRefs = useRef<Record<string, HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>>({});
  const formRef = useRef<HTMLFormElement>(null);

  // Initialize values from props
  useEffect(() => {
    const initialVals: Record<string, any> = {};
    fields.forEach(field => {
      initialVals[field.name] = initialValues[field.name] ?? field.value ?? '';
    });
    setValues(initialVals);
  }, [fields, initialValues]);

  // Validate single field
  const validateField = useCallback((field: FormField, value: any): string | null => {
    if (!field.validation) return null;

    const { validation } = field;

    // Required field validation
    if (field.required && (!value || value === '')) {
      return '此欄位為必填';
    }

    if (!value) return null; // Skip other validations if empty

    // Pattern validation
    if (validation.pattern && !validation.pattern.test(value)) {
      return '格式不正確';
    }

    // Length validation
    if (typeof value === 'string') {
      if (validation.minLength && value.length < validation.minLength) {
        return `最少需要 ${validation.minLength} 個字元`;
      }
      if (validation.maxLength && value.length > validation.maxLength) {
        return `最多允許 ${validation.maxLength} 個字元`;
      }
    }

    // Number validation
    if (field.type === 'number') {
      const num = parseFloat(value);
      if (isNaN(num)) return '請輸入有效的數字';
      if (validation.min !== undefined && num < validation.min) {
        return `數值不能小於 ${validation.min}`;
      }
      if (validation.max !== undefined && num > validation.max) {
        return `數值不能大於 ${validation.max}`;
      }
    }

    // Custom validation
    if (validation.custom) {
      return validation.custom(value);
    }

    return null;
  }, []);

  // Validate all fields
  const validateAll = useCallback(() => {
    const newErrors: ValidationErrors = {};
    let isValid = true;

    fields.forEach(field => {
      const error = validateField(field, values[field.name]);
      newErrors[field.name] = error;
      if (error) isValid = false;
    });

    setErrors(newErrors);
    return isValid;
  }, [fields, values, validateField]);

  // Handle field value change
  const handleFieldChange = useCallback((fieldName: string, value: any) => {
    setValues(prev => ({ ...prev, [fieldName]: value }));
    setTouched(prev => ({ ...prev, [fieldName]: true }));

    if (validateOnChange) {
      const field = fields.find(f => f.name === fieldName);
      if (field) {
        const error = validateField(field, value);
        setErrors(prev => ({ ...prev, [fieldName]: error }));
      }
    }
  }, [fields, validateOnChange, validateField]);

  // Handle field blur
  const handleFieldBlur = useCallback((fieldName: string) => {
    setFocusedField(null);
    setTouched(prev => ({ ...prev, [fieldName]: true }));

    const field = fields.find(f => f.name === fieldName);
    if (field) {
      const error = validateField(field, values[field.name]);
      setErrors(prev => ({ ...prev, [fieldName]: error }));
    }
  }, [fields, values, validateField]);

  // Handle field focus
  const handleFieldFocus = useCallback((fieldName: string) => {
    setFocusedField(fieldName);
  }, []);

  // Handle submit
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    const isValid = validateAll();
    if (!isValid) {
      // Focus on first field with error
      const firstErrorField = fields.find(f => errors[f.name]);
      if (firstErrorField && inputRefs.current[firstErrorField.name]) {
        inputRefs.current[firstErrorField.name].focus();
      }
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(values);
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [validateAll, errors, fields, values, onSubmit]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent, fieldName: string) => {
    if (e.key === 'Enter' && autoAdvance) {
      e.preventDefault();
      const currentIndex = fields.findIndex(f => f.name === fieldName);
      if (currentIndex < fields.length - 1) {
        const nextField = fields[currentIndex + 1];
        const nextInput = inputRefs.current[nextField.name];
        if (nextInput) {
          nextInput.focus();
        }
      } else {
        // Last field - submit form
        handleSubmit();
      }
    }
  }, [autoAdvance, fields, handleSubmit]);

  // Gesture callbacks for swipe navigation
  const gestureCallbacks: GestureCallbacks = {
    onSwipe: (direction) => {
      if (direction === 'left' && focusedField) {
        // Move to next field
        const currentIndex = fields.findIndex(f => f.name === focusedField);
        if (currentIndex < fields.length - 1) {
          const nextField = fields[currentIndex + 1];
          const nextInput = inputRefs.current[nextField.name];
          if (nextInput) {
            nextInput.focus();
          }
        }
      } else if (direction === 'right' && focusedField) {
        // Move to previous field
        const currentIndex = fields.findIndex(f => f.name === focusedField);
        if (currentIndex > 0) {
          const prevField = fields[currentIndex - 1];
          const prevInput = inputRefs.current[prevField.name];
          if (prevInput) {
            prevInput.focus();
          }
        }
      }
    },
  };

  // Get field icon
  const getFieldIcon = (type: FormField['type'], icon?: React.ReactNode) => {
    if (icon) return icon;

    switch (type) {
      case 'email': return <Mail className="w-5 h-5" />;
      case 'password': return <Lock className="w-5 h-5" />;
      case 'tel': return <Phone className="w-5 h-5" />;
      case 'date': return <Calendar className="w-5 h-5" />;
      case 'time': return <Clock className="w-5 h-5" />;
      case 'number': return <CreditCard className="w-5 h-5" />;
      case 'file': return <ImageIcon className="w-5 h-5" />;
      default: return null;
    }
  };

  // Render input field
  const renderField = (field: FormField) => {
    const hasError = touched[field.name] && errors[field.name];
    const isFocused = focusedField === field.name;
    const touchSize = largeTouchTargets ? 'p-4' : 'p-3';

    const commonProps = {
      ref: (el: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement) => {
        inputRefs.current[field.name] = el;
      },
      value: values[field.name] ?? '',
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const value = field.type === 'checkbox' ? e.target.checked : e.target.value;
        handleFieldChange(field.name, value);
      },
      onBlur: () => handleFieldBlur(field.name),
      onFocus: () => handleFieldFocus(field.name),
      onKeyDown: (e: React.KeyboardEvent) => handleKeyDown(e, field.name),
      disabled: field.disabled,
      readOnly: field.readonly,
      autoFocus: field.autoFocus,
      autoComplete: field.autoComplete,
      className: clsx(
        'w-full rounded-lg border transition-all duration-200',
        'focus:outline-none focus:ring-2',
        hasError ? 'border-red-300 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500',
        field.disabled && 'bg-gray-100 text-gray-500',
        touchSize,
        largeTouchTargets && 'text-lg'
      ),
    };

    switch (field.type) {
      case 'textarea':
        return (
          <textarea
            {...commonProps}
            rows={4}
            placeholder={field.placeholder}
          />
        );

      case 'select':
        return (
          <select {...commonProps}>
            <option value="">{field.placeholder || '請選擇...'}</option>
            {field.options?.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'file':
        return (
          <div className="relative">
            <input
              {...commonProps}
              type="file"
              className="hidden"
              id={`file-${field.name}`}
            />
            <TouchFeedback
              className={clsx(
                'flex items-center justify-center gap-2 w-full rounded-lg border-2 border-dashed',
                'border-gray-300 hover:border-gray-400',
                touchSize,
                hasError && 'border-red-300'
              )}
              onPress={() => {
                const fileInput = document.getElementById(`file-${field.name}`) as HTMLInputElement;
                fileInput?.click();
              }}
            >
              <Camera className="w-5 h-5 text-gray-400" />
              <span className="text-gray-600">
                {values[field.name]?.name || '選擇文件'}
              </span>
            </TouchFeedback>
          </div>
        );

      case 'password':
        return (
          <div className="relative">
            <input
              {...commonProps}
              type={showPassword[field.name] ? 'text' : 'password'}
              placeholder={field.placeholder}
            />
            <button
              type="button"
              onClick={() => setShowPassword(prev => ({ ...prev, [field.name]: !prev[field.name] }))}
              className={clsx(
                'absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded',
                'hover:bg-gray-100 active:bg-gray-200',
                largeTouchTargets && 'right-4'
              )}
            >
              {showPassword[field.name] ? (
                <EyeOff className="w-5 h-5 text-gray-400" />
              ) : (
                <Eye className="w-5 h-5 text-gray-400" />
              )}
            </button>
          </div>
        );

      default:
        return (
          <input
            {...commonProps}
            type={field.type}
            placeholder={field.placeholder}
            min={field.type === 'number' ? field.validation?.min : undefined}
            max={field.type === 'number' ? field.validation?.max : undefined}
            minLength={field.type === 'text' ? field.validation?.minLength : undefined}
            maxLength={field.type === 'text' ? field.validation?.maxLength : undefined}
            pattern={field.type === 'text' ? field.validation?.pattern?.source : undefined}
          />
        );
    }
  };

  return (
    <div className={clsx('w-full max-w-lg mx-auto', className)}>
      <form
        ref={formRef}
        onSubmit={handleSubmit}
        className="space-y-4"
        noValidate
      >
        {enableGestures ? (
          <GestureRecognizer callbacks={gestureCallbacks}>
            <div className="space-y-4">
              {fields.map(field => (
                <motion.div
                  key={field.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: fields.indexOf(field) * 0.05 }}
                >
                  <label className="block">
                    <span className={clsx(
                      'text-sm font-medium text-gray-700 mb-1 block',
                      hasError && 'text-red-600'
                    )}>
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </span>

                    <div className="relative">
                      {/* Field icon */}
                      {getFieldIcon(field.type, field.icon) && (
                        <div className={clsx(
                          'absolute left-3 top-1/2 -translate-y-1/2 text-gray-400',
                          largeTouchTargets && 'left-4'
                        )}>
                          {getFieldIcon(field.type, field.icon)}
                        </div>
                      )}

                      {/* Input field */}
                      <div className={clsx(
                        getFieldIcon(field.type, field.icon) && 'pl-10',
                        largeTouchTargets && getFieldIcon(field.type, field.icon) && 'pl-12'
                      )}>
                        {renderField(field)}
                      </div>

                      {/* Error message */}
                      <AnimatePresence>
                        {showValidationErrors && hasError && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-1 flex items-center gap-1 text-red-600 text-sm"
                          >
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            <span>{errors[field.name]}</span>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </label>
                </motion.div>
              ))}
            </div>
          </GestureRecognizer>
        ) : (
          <div className="space-y-4">
            {fields.map(field => (
              <motion.div
                key={field.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: fields.indexOf(field) * 0.05 }}
              >
                <label className="block">
                  <span className={clsx(
                    'text-sm font-medium text-gray-700 mb-1 block',
                    touched[field.name] && errors[field.name] && 'text-red-600'
                  )}>
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </span>

                  <div className="relative">
                    {renderField(field)}

                    <AnimatePresence>
                      {showValidationErrors && touched[field.name] && errors[field.name] && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-1 flex items-center gap-1 text-red-600 text-sm"
                        >
                          <AlertCircle className="w-4 h-4 flex-shrink-0" />
                          <span>{errors[field.name]}</span>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </label>
              </motion.div>
            ))}
          </div>
        )}

        {/* Submit button */}
        <div className={clsx(
          stickySubmit && 'fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200',
          !stickySubmit && 'pt-4'
        )}>
          <TouchFeedback
            disabled={submitButtonDisabled || isSubmitting}
            className={clsx(
              'w-full py-4 rounded-lg font-medium transition-all duration-200',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              submitButtonDisabled || isSubmitting
                ? 'bg-gray-300 text-gray-500'
                : 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800'
            )}
            onPress={handleSubmit}
          >
            {isSubmitting ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                處理中...
              </div>
            ) : (
              submitButtonText
            )}
          </TouchFeedback>
        </div>
      </form>

      {/* Buffer for sticky submit button */}
      {stickySubmit && <div className="h-20" />}
    </div>
  );
};

export default MobileOptimizedForm;