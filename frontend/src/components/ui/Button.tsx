/**
 * Button Component - 統一按鈕組件
 * 版本: 1.0.0
 * 描述: 符合CBSC設計規範的統一按鈕組件
 * 支持多種變體、尺寸、狀態
 */

import React from 'react';
import { cn } from '../../utils/cn';
import { cva } from '../../utils/class-variance-authority';

// 按鈕變體類型
type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'outline'
  | 'ghost'
  | 'link'
  | 'success'
  | 'warning'
  | 'error';

// 按鈕尺寸類型
type ButtonSize =
  | 'xs'
  | 'sm'
  | 'md'
  | 'lg'
  | 'xl';

// 按鈕Props接口
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  rounded?: boolean;
  onTouchStart?: () => void;
  onTouchEnd?: () => void;
}

// CVa - Class Variance Authority 配置
const buttonVariants = cva(
  // 基礎樣式
  'inline-flex items-center justify-center font-medium transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      // 變體樣式
      variant: {
        primary: [
          'bg-primary-500 text-white hover:bg-primary-600 focus:ring-primary-500',
          'active:bg-primary-700 disabled:bg-primary-300'
        ],
        secondary: [
          'bg-secondary-500 text-white hover:bg-secondary-600 focus:ring-secondary-500',
          'active:bg-secondary-700 disabled:bg-secondary-300'
        ],
        outline: [
          'border border-primary-500 text-primary-500 bg-white hover:bg-primary-50 focus:ring-primary-500',
          'active:bg-primary-100 disabled:bg-gray-50 disabled:text-gray-400'
        ],
        ghost: [
          'text-primary-500 hover:bg-primary-50 focus:ring-primary-500',
          'active:bg-primary-100 disabled:bg-transparent disabled:text-gray-400'
        ],
        link: [
          'text-primary-500 hover:text-primary-600 hover:underline focus:ring-primary-500',
          'active:text-primary-700 disabled:text-gray-400'
        ],
        success: [
          'bg-success-500 text-white hover:bg-success-600 focus:ring-success-500',
          'active:bg-success-700 disabled:bg-success-300'
        ],
        warning: [
          'bg-warning-500 text-white hover:bg-warning-600 focus:ring-warning-500',
          'active:bg-warning-700 disabled:bg-warning-300'
        ],
        error: [
          'bg-error-500 text-white hover:bg-error-600 focus:ring-error-500',
          'active:bg-error-700 disabled:bg-error-300'
        ],
      },
      // 尺寸樣式
      size: {
        xs: [
          'text-xs px-2 py-1 rounded',
          'min-h-[1.75rem]' // 觸摸友好
        ],
        sm: [
          'text-sm px-3 py-1.5 rounded-md',
          'min-h-[2rem]' // 觸摸友好
        ],
        md: [
          'text-base px-4 py-2 rounded-md',
          'min-h-[2.5rem]' // 觸摸友好
        ],
        lg: [
          'text-lg px-6 py-3 rounded-lg',
          'min-h-[3rem]' // 觸摸友好
        ],
        xl: [
          'text-xl px-8 py-4 rounded-lg',
          'min-h-[3.5rem]' // 觸摸友好
        ],
      },
      // 圓角變化
      rounded: {
        true: 'rounded-full',
        false: '',
      },
      // 全寬
      fullWidth: {
        true: 'w-full',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
      rounded: false,
      fullWidth: false,
    },
  }
);

/**
 * Button Component
 */
export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  rounded = false,
  onTouchStart,
  onTouchEnd,
  ...props
}) => {
  // 處理觸摸事件
  const handleTouchStart = (e: React.TouchEvent) => {
    // 添加觸摸反饋
    e.currentTarget.style.transform = 'scale(0.95)';
    onTouchStart?.();
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    // 移除觸摸反饋
    e.currentTarget.style.transform = 'scale(1)';
    onTouchEnd?.();
  };

  // 渲染Loading狀態的圖標
  const renderLoadingIcon = () => (
    <svg
      className="animate-spin -ml-1 mr-2 h-4 w-4"
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

  // 渲染圖標
  const renderIcon = () => {
    if (loading) {
      return renderLoadingIcon();
    }

    if (icon) {
      const iconSize = {
        xs: 'h-3 w-3',
        sm: 'h-4 w-4',
        md: 'h-4 w-4',
        lg: 'h-5 w-5',
        xl: 'h-6 w-6',
      }[size];

      return <span className={cn(iconSize, 'flex-shrink-0')}>{icon}</span>;
    }

    return null;
  };

  // 計算圖標和文字的間距
  const iconSpacing = icon ? (iconPosition === 'left' ? 'mr-2' : 'ml-2') : '';

  return (
    <button
      className={cn(
        buttonVariants({
          variant,
          size,
          rounded,
          fullWidth,
          className
        }),
        // 觸摸反饋
        'active:scale-95',
        // 禁用時不顯示觸摸反饋
        disabled && 'active:scale-100'
      )}
      disabled={disabled || loading}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      {...props}
    >
      {/* 左側圖標 */}
      {icon && iconPosition === 'left' && renderIcon()}

      {/* 按鈕文字 */}
      <span className={cn(
        'truncate',
        // 添加圖標間距
        iconSpacing
      )}>
        {children}
      </span>

      {/* 右側圖標 */}
      {icon && iconPosition === 'right' && renderIcon()}
    </button>
  );
};

// 按鈕組組件
interface ButtonGroupProps {
  children: React.ReactNode;
  className?: string;
  vertical?: boolean;
  gap?: 'sm' | 'md' | 'lg';
}

export const ButtonGroup: React.FC<ButtonGroupProps> = ({
  children,
  className,
  vertical = false,
  gap = 'sm',
  ...props
}) => {
  const gapClasses = {
    sm: 'space-x-1 space-y-1',
    md: 'space-x-2 space-y-2',
    lg: 'space-x-3 space-y-3',
  };

  const flexClasses = vertical
    ? 'flex-col'
    : 'flex-row';

  return (
    <div
      className={cn(
        'flex',
        flexClasses,
        gapClasses[gap],
        className
      )}
      role="group"
      {...props}
    >
      {React.Children.map(children, (child, index) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, {
            ...child.props,
            className: cn(
              // 按鈕組中的第一個按鈕
              index === 0 && (vertical ? 'rounded-t-lg rounded-b-none rounded-l-lg rounded-r-none' : 'rounded-l-lg rounded-r-none'),
              // 按鈕組中的最後一個按鈕
              index === React.Children.count(children) - 1 && (vertical ? 'rounded-b-lg rounded-t-none rounded-l-none rounded-r-lg' : 'rounded-r-lg rounded-l-none'),
              // 按鈕組中的中間按鈕
              index > 0 && index < React.Children.count(children) - 1 && 'rounded-none',
              child.props.className
            )
          });
        }
        return child;
      })}
    </div>
  );
};

// 懸浮操作按鈕 (FAB)
interface FabProps extends ButtonProps {
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  extended?: boolean;
}

export const Fab: React.FC<FabProps> = ({
  children,
  className,
  position = 'bottom-right',
  extended = false,
  size = extended ? 'lg' : 'md',
  ...props
}) => {
  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
  };

  return (
    <button
      className={cn(
        'fixed z-50 shadow-lg rounded-full p-0 hover:shadow-xl transition-all',
        'bg-primary-500 text-white hover:bg-primary-600 focus:ring-primary-500',
        'min-h-[3.5rem] min-w-[3.5rem]',
        'flex items-center justify-center',
        extended && 'px-6 py-3 rounded-full',
        positionClasses[position],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};

// 導出組件類型
export type { ButtonProps, ButtonGroupProps, FabProps, ButtonVariant, ButtonSize };

// 默認導出
export default Button;