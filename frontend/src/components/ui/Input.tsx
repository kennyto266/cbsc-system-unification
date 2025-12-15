/**
 * Input Component - 統一輸入框組件
 * 版本: 1.0.0
 * 描述: 符合CBSC設計規範的統一輸入框組件
 * 支持多種類型、尺寸、狀態
 */

import React, { forwardRef, useState } from 'react';
import { cn } from '../../utils/cn';
import { cva } from '../../utils/class-variance-authority';

// 輸入框變體類型
type InputVariant = 'default' | 'filled' | 'outlined' | 'underlined';

// 輸入框尺寸類型
type InputSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

// 輸入框狀態類型
type InputState = 'default' | 'success' | 'warning' | 'error';

// 輸入框Props接口
interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  variant?: InputVariant;
  size?: InputSize;
  state?: InputState;
  label?: string;
  helperText?: string;
  errorText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  leftElement?: React.ReactNode;
  rightElement?: React.ReactNode;
  fullWidth?: boolean;
  loading?: boolean;
  clearable?: boolean;
  onClear?: () => void;
}

// CVa - Class Variance Authority 配置
const inputVariants = cva(
  // 基礎樣式
  'flex w-full rounded-md border font-medium transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      // 變體樣式
      variant: {
        default: [
          'border-gray-300 bg-white hover:bg-gray-50 hover:border-gray-400 focus:border-primary-500 focus:ring-primary-500',
          'placeholder:text-gray-400 disabled:bg-gray-100'
        ],
        filled: [
          'border-transparent bg-gray-100 hover:bg-gray-200 focus:bg-white focus:border-primary-500 focus:ring-primary-500',
          'placeholder:text-gray-500 disabled:bg-gray-50'
        ],
        outlined: [
          'border-2 border-gray-300 bg-transparent hover:border-primary-300 focus:border-primary-500 focus:ring-primary-500',
          'placeholder:text-gray-400 disabled:bg-transparent disabled:border-gray-200'
        ],
        underlined: [
          'border-0 border-b-2 border-gray-300 bg-transparent rounded-none hover:border-primary-300 focus:border-primary-500 focus:ring-0 focus:ring-offset-0',
          'placeholder:text-gray-400 disabled:bg-transparent disabled:border-gray-200 px-0'
        ],
      },
      // 尺寸樣式
      size: {
        xs: [
          'h-8 text-xs px-2 py-1',
          'min-h-[2rem]' // 觸摸友好
        ],
        sm: [
          'h-9 text-sm px-3 py-1.5 rounded-sm',
          'min-h-[2.25rem]' // 觸摸友好
        ],
        md: [
          'h-10 text-base px-3 py-2',
          'min-h-[2.5rem]' // 觸摸友好
        ],
        lg: [
          'h-12 text-lg px-4 py-3 rounded-lg',
          'min-h-[3rem]' // 觸摸友好
        ],
        xl: [
          'h-14 text-xl px-5 py-4 rounded-lg',
          'min-h-[3.5rem]' // 觸摸友好
        ],
      },
      // 狀態樣式
      state: {
        default: '',
        success: [
          'border-green-500 focus:border-green-500 focus:ring-green-500',
          'pr-10' // 為成功圖標留出空間
        ],
        warning: [
          'border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500',
          'pr-10' // 為警告圖標留出空間
        ],
        error: [
          'border-red-500 focus:border-red-500 focus:ring-red-500',
          'pr-10' // 為錯誤圖標留出空間
        ],
      },
      // 全寬
      fullWidth: {
        true: 'w-full',
        false: 'w-auto',
      },
      // 載入狀態
      loading: {
        true: 'pr-10',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      state: 'default',
      fullWidth: true,
      loading: false,
    },
  }
);

/**
 * Input Component
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(({
  className,
  variant = 'default',
  size = 'md',
  state = 'default',
  type = 'text',
  label,
  helperText,
  errorText,
  leftIcon,
  rightIcon,
  leftElement,
  rightElement,
  fullWidth = true,
  loading = false,
  clearable = false,
  onClear,
  value,
  disabled,
  ...props
}, ref) => {
  const [focused, setFocused] = useState(false);
  const [internalValue, setInternalValue] = useState(value || '');

  // 處理值變化
  const currentValue = value !== undefined ? value : internalValue;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (value === undefined) {
      setInternalValue(e.target.value);
    }
    props.onChange?.(e);
  };

  // 處理清除
  const handleClear = () => {
    if (value === undefined) {
      setInternalValue('');
    }
    onClear?.();
  };

  // 處理焦點
  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    setFocused(true);
    props.onFocus?.(e);
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setFocused(false);
    props.onBlur?.(e);
  };

  // 計算實際狀態
  const actualState = errorText ? 'error' : state;

  // 渲染Loading圖標
  const renderLoadingIcon = () => (
    <svg
      className="animate-spin h-4 w-4 text-gray-400"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );

  // 渲染狀態圖標
  const renderStateIcon = () => {
    switch (actualState) {
      case 'success':
        return (
          <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="h-4 w-4 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        );
      case 'error':
        return (
          <svg className="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      default:
        return null;
    }
  };

  // 渲染清除按鈕
  const renderClearButton = () => {
    if (!clearable || !currentValue || disabled) return null;

    return (
      <button
        type="button"
        onClick={handleClear}
        className="p-1 hover:bg-gray-100 rounded-full transition-colors"
        tabIndex={-1}
      >
        <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    );
  };

  return (
    <div className={cn('flex flex-col space-y-1.5', fullWidth && 'w-full')}>
      {/* 標籤 */}
      {label && (
        <label className={cn(
          'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
          actualState === 'error' && 'text-red-500',
          actualState === 'success' && 'text-green-500',
          actualState === 'warning' && 'text-yellow-500'
        )}>
          {label}
        </label>
      )}

      {/* 輸入框容器 */}
      <div className="relative">
        {/* 左側元素 */}
        {(leftIcon || leftElement) && (
          <div className={cn(
            'absolute left-0 top-0 h-full flex items-center justify-center',
            'pl-3 pr-2'
          )}>
            {leftIcon}
            {leftElement}
          </div>
        )}

        {/* 輸入框 */}
        <input
          ref={ref}
          type={type}
          className={cn(
            inputVariants({
              variant,
              size,
              state: actualState,
              fullWidth,
              loading: loading || actualState !== 'default' || clearable,
              className
            }),
            // 左側元素時的內邊距調整
            (leftIcon || leftElement) && 'pl-10',
            // 右側元素時的內邊距調整
            (rightIcon || rightElement || loading || actualState !== 'default' || clearable) && 'pr-10',
            // 焦點狀態
            focused && 'ring-2 ring-primary-500 ring-offset-2'
          )}
          value={currentValue}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          disabled={disabled || loading}
          {...props}
        />

        {/* 右側元素容器 */}
        <div className={cn(
          'absolute right-0 top-0 h-full flex items-center justify-center',
          'pl-2 pr-3',
          'pointer-events-none'
        )}>
          {/* 載入圖標 */}
          {loading && (
            <div className="animate-spin pointer-events-auto">
              {renderLoadingIcon()}
            </div>
          )}

          {/* 狀態圖標 */}
          {!loading && actualState !== 'default' && (
            <div className="pointer-events-auto">
              {renderStateIcon()}
            </div>
          )}

          {/* 清除按鈕 */}
          {!loading && !errorText && (
            <div className="pointer-events-auto">
              {renderClearButton()}
            </div>
          )}

          {/* 自定義右側元素 */}
          {!loading && actualState === 'default' && !clearable && (rightIcon || rightElement) && (
            <div className="pointer-events-auto">
              {rightIcon}
              {rightElement}
            </div>
          )}
        </div>
      </div>

      {/* 輔助文本 */}
      {(helperText || errorText) && (
        <p className={cn(
          'text-xs',
          actualState === 'error' ? 'text-red-500' : 'text-gray-500'
        )}>
          {errorText || helperText}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

// 導出組件類型
export type { InputProps, InputVariant, InputSize, InputState };

// 默認導出
export default Input;