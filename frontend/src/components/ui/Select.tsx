/**
 * Select Component - 統一下拉選擇組件
 * 版本: 1.0.0
 * 描述: 符合CBSC設計規範的統一下拉選擇組件
 * 支持單選、多選、搜索、分組等功能
 */

import React, { forwardRef, useState, useRef, useEffect } from 'react';
import { cn } from '../../utils/cn';
import { cva } from '../../utils/class-variance-authority';
import Input from './Input';

// 選項接口
export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
  group?: string;
  icon?: React.ReactNode;
  description?: string;
}

// 分組選項接口
export interface SelectOptionGroup {
  label: string;
  options: SelectOption[];
}

// Select變體類型
type SelectVariant = 'default' | 'filled' | 'outlined';

// Select尺寸類型
type SelectSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

// Select Props接口
interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size' | 'onChange'> {
  variant?: SelectVariant;
  size?: SelectSize;
  options: SelectOption[] | SelectOptionGroup[];
  value?: string | number | string[] | number[];
  defaultValue?: string | number | string[] | number[];
  placeholder?: string;
  label?: string;
  helperText?: string;
  errorText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  loading?: boolean;
  clearable?: boolean;
  searchable?: boolean;
  multiple?: boolean;
  maxDisplay?: number;
  onClear?: () => void;
  onChange?: (value: string | number | string[] | number[]) => void;
  onSearch?: (query: string) => void;
  renderOption?: (option: SelectOption) => React.ReactNode;
  renderValue?: (value: string | number | string[] | number[]) => React.ReactNode;
}

// CVa - Class Variance Authority 配置
const selectVariants = cva(
  // 基礎樣式
  'flex w-full rounded-md border font-medium transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      // 變體樣式
      variant: {
        default: [
          'border-gray-300 bg-white hover:bg-gray-50 hover:border-gray-400 focus:border-primary-500 focus:ring-primary-500',
          'disabled:bg-gray-100'
        ],
        filled: [
          'border-transparent bg-gray-100 hover:bg-gray-200 focus:bg-white focus:border-primary-500 focus:ring-primary-500',
          'disabled:bg-gray-50'
        ],
        outlined: [
          'border-2 border-gray-300 bg-transparent hover:border-primary-300 focus:border-primary-500 focus:ring-primary-500',
          'disabled:bg-transparent disabled:border-gray-200'
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
      // 錯誤狀態
      error: {
        true: [
          'border-red-500 focus:border-red-500 focus:ring-red-500',
          'pr-10' // 為錯誤圖標留出空間
        ],
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      error: false,
    },
  }
);

/**
 * Select Component
 */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(({
  className,
  variant = 'default',
  size = 'md',
  options = [],
  value,
  defaultValue,
  placeholder = '請選擇...',
  label,
  helperText,
  errorText,
  leftIcon,
  rightIcon,
  fullWidth = true,
  loading = false,
  clearable = false,
  searchable = false,
  multiple = false,
  maxDisplay = 3,
  onClear,
  onChange,
  onSearch,
  renderOption,
  renderValue,
  disabled,
  ...props
}, ref) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [internalValue, setInternalValue] = useState(defaultValue || (multiple ? [] : ''));
  const selectRef = useRef<HTMLSelectElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 處理值變化
  const currentValue = value !== undefined ? value : internalValue;

  // 格式化選項為統一格式
  const formatOptions = (): SelectOption[] => {
    const formatted: SelectOption[] = [];

    options.forEach((option) => {
      if ('group' in option) {
        // 這是一個分組
        const group = option as SelectOptionGroup;
        group.options.forEach((opt) => {
          formatted.push({
            ...opt,
            group: group.label,
          });
        });
      } else {
        // 這是一個普通選項
        formatted.push(option as SelectOption);
      }
    });

    // 如果啟用搜索，過濾選項
    if (searchQuery) {
      return formatted.filter((option) =>
        option.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        option.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    return formatted;
  };

  const formattedOptions = formatOptions();

  // 處理選擇變化
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newValue = multiple
      ? Array.from(e.target.selectedOptions, (option) => option.value)
      : e.target.value;

    if (value === undefined) {
      setInternalValue(newValue);
    }
    onChange?.(newValue);
  };

  // 處理清除
  const handleClear = () => {
    const newValue = multiple ? [] : '';
    if (value === undefined) {
      setInternalValue(newValue);
    }
    onClear?.();
    onChange?.(newValue);
  };

  // 獲取顯示文本
  const getDisplayText = () => {
    if (!currentValue || (Array.isArray(currentValue) && currentValue.length === 0)) {
      return placeholder;
    }

    if (renderValue) {
      return renderValue(currentValue);
    }

    if (Array.isArray(currentValue)) {
      if (currentValue.length === 0) return placeholder;
      if (currentValue.length <= maxDisplay) {
        return currentValue
          .map((val) => formattedOptions.find((opt) => opt.value === val)?.label || val)
          .join(', ');
      }
      return `${currentValue.length} 項已選擇`;
    }

    const selectedOption = formattedOptions.find((opt) => opt.value === currentValue);
    return selectedOption?.label || currentValue;
  };

  // 點擊外部關閉下拉菜單
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // 渲染原生Select（用於無障礙和基礎功能）
  const renderNativeSelect = () => (
    <select
      ref={selectRef}
      className={cn(
        'absolute inset-0 w-full h-full opacity-0 cursor-pointer',
        disabled && 'cursor-not-allowed'
      )}
      value={currentValue}
      onChange={handleChange}
      disabled={disabled || loading}
      multiple={multiple}
      {...props}
    >
      {!currentValue && !multiple && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {formattedOptions.map((option) => (
        <option
          key={`${option.group ? `${option.group}-` : ''}${option.value}`}
          value={option.value}
          disabled={option.disabled}
        >
          {option.label}
        </option>
      ))}
    </select>
  );

  // 渲染自定義下拉內容
  const renderDropdown = () => {
    if (!isOpen) return null;

    // 按分組排序選項
    const groupedOptions = formattedOptions.reduce((acc, option) => {
      const group = option.group || '默認';
      if (!acc[group]) acc[group] = [];
      acc[group].push(option);
      return acc;
    }, {} as Record<string, SelectOption[]>);

    return (
      <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
        {searchable && (
          <div className="p-2 border-b border-gray-200">
            <Input
              size="sm"
              placeholder="搜索選項..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                onSearch?.(e.target.value);
              }}
              leftIcon={
                <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              }
            />
          </div>
        )}

        {Object.entries(groupedOptions).map(([groupName, groupOptions]) => (
          <div key={groupName}>
            {groupName !== '默認' && (
              <div className="px-3 py-2 text-xs font-semibold text-gray-500 bg-gray-50">
                {groupName}
              </div>
            )}
            {groupOptions.map((option) => (
              <div
                key={option.value}
                className={cn(
                  'px-3 py-2 cursor-pointer hover:bg-gray-100 flex items-center space-x-2',
                  option.disabled && 'opacity-50 cursor-not-allowed',
                  (Array.isArray(currentValue) ? currentValue.includes(option.value) : currentValue === option.value) && 'bg-primary-50 text-primary-600'
                )}
                onClick={() => {
                  if (option.disabled) return;

                  let newValue;
                  if (multiple) {
                    const currentArray = Array.isArray(currentValue) ? currentValue : [];
                    if (currentArray.includes(option.value)) {
                      newValue = currentArray.filter((val) => val !== option.value);
                    } else {
                      newValue = [...currentArray, option.value];
                    }
                  } else {
                    newValue = option.value;
                  }

                  if (value === undefined) {
                    setInternalValue(newValue);
                  }
                  onChange?.(newValue);

                  if (!multiple) {
                    setIsOpen(false);
                  }
                }}
              >
                {option.icon && <span className="flex-shrink-0">{option.icon}</span>}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">
                    {renderOption ? renderOption(option) : option.label}
                  </div>
                  {option.description && (
                    <div className="text-xs text-gray-500 truncate">
                      {option.description}
                    </div>
                  )}
                </div>
                {(Array.isArray(currentValue) ? currentValue.includes(option.value) : currentValue === option.value) && (
                  <svg className="h-4 w-4 text-primary-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={cn('flex flex-col space-y-1.5', fullWidth && 'w-full')}>
      {/* 標籤 */}
      {label && (
        <label className={cn(
          'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
          errorText && 'text-red-500'
        )}>
          {label}
        </label>
      )}

      {/* Select容器 */}
      <div className={cn('relative', fullWidth && 'w-full')} ref={dropdownRef}>
        {/* Select觸發器 */}
        <div
          className={cn(
            selectVariants({
              variant,
              size,
              error: !!errorText,
              className
            }),
            'cursor-pointer pr-10',
            leftIcon && 'pl-10',
            disabled && 'cursor-not-allowed'
          )}
          onClick={() => !disabled && !loading && setIsOpen(!isOpen)}
        >
          {/* 左側圖標 */}
          {leftIcon && (
            <div className="absolute left-0 top-0 h-full flex items-center justify-center pl-3 pr-2">
              {leftIcon}
            </div>
          )}

          {/* 顯示文本 */}
          <div className="flex-1 truncate">
            {getDisplayText()}
          </div>

          {/* 右側圖標 */}
          <div className="absolute right-0 top-0 h-full flex items-center justify-center pr-3">
            {loading ? (
              <svg className="animate-spin h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : clearable && currentValue ? (
              <button
                type="button"
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClear();
                }}
              >
                <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            ) : rightIcon ? (
              rightIcon
            ) : (
              <svg className={cn('h-4 w-4 text-gray-400 transition-transform', isOpen && 'rotate-180')} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            )}
          </div>

          {/* 原生Select（隱藏但可訪問） */}
          {renderNativeSelect()}
        </div>

        {/* 自定義下拉內容 */}
        {renderDropdown()}
      </div>

      {/* 輔助文本 */}
      {(helperText || errorText) && (
        <p className={cn(
          'text-xs',
          errorText ? 'text-red-500' : 'text-gray-500'
        )}>
          {errorText || helperText}
        </p>
      )}
    </div>
  );
});

Select.displayName = 'Select';

// 導出組件類型
export type { SelectProps, SelectVariant, SelectSize, SelectOption, SelectOptionGroup };

// 默認導出
export default Select;