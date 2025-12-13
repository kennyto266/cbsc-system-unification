import React from 'react'
import { clsx } from 'clsx'

// Button component interface - 按钮组件接口
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Button variant - 按钮变体
   * @default 'primary'
   */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success'

  /**
   * Button size - 按钮尺寸
   * @default 'md'
   */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'

  /**
   * Loading state - 加载状态
   * @default false
   */
  loading?: boolean

  /**
   * Icon element - 图标元素
   */
  icon?: React.ReactNode

  /**
   * Icon position - 图标位置
   * @default 'left'
   */
  iconPosition?: 'left' | 'right'

  /**
   * Show ripple effect - 显示涟漪效果
   * @default false
   */
  ripple?: boolean

  /**
   * Full width button - 全宽按钮
   * @default false
   */
  fullWidth?: boolean

  /**
   * Button content - 按钮内容
   */
  children: React.ReactNode
}

// Enhanced Button component with design system - 基于设计系统的增强按钮组件
export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  iconPosition = 'left',
  ripple = false,
  fullWidth = false,
  children,
  className,
  disabled,
  onClick,
  ...props
}) => {
  // Base classes - 基础样式类
  const baseClasses = [
    // Base layout - 基础布局
    'btn',

    // Positioning - 定位
    'relative',
    'inline-flex',
    'items-center',
    'justify-center',

    // Typography - 字体
    'font-medium',
    'text-sm',

    // Border & Shape - 边框和形状
    'border',
    'rounded-lg',

    // Transitions - 过渡
    'transition-all',
    'duration-200',

    // Cursor - 光标
    'cursor-pointer',

    // Select - 选择
    'select-none',

    // Focus - 焦点
    'focus:outline-none',
    'focus-visible:ring-2',
    'focus-visible:ring-offset-2',

    // Disabled state - 禁用状态
    'disabled:opacity-50',
    'disabled:cursor-not-allowed',

    // Full width - 全宽
    fullWidth && 'w-full',
  ]

  // Variant classes - 变体样式类
  const variantClasses = {
    primary: [
      'bg-primary',
      'text-white',
      'border-primary',
      'shadow-sm',
      'hover:bg-primary-hover',
      'hover:shadow-md',
      'focus-visible:ring-primary',
    ],
    secondary: [
      'bg-background-secondary',
      'text-text-primary',
      'border-border-primary',
      'hover:bg-background-tertiary',
      'hover:border-border-secondary',
      'focus-visible:ring-primary',
    ],
    outline: [
      'bg-transparent',
      'text-primary',
      'border-primary',
      'hover:bg-primary',
      'hover:text-white',
      'focus-visible:ring-primary',
    ],
    ghost: [
      'bg-transparent',
      'text-text-secondary',
      'border-transparent',
      'hover:bg-background-secondary',
      'hover:text-text-primary',
      'focus-visible:ring-primary',
    ],
    danger: [
      'bg-error',
      'text-white',
      'border-error',
      'shadow-sm',
      'hover:bg-red-600',
      'hover:shadow-md',
      'focus-visible:ring-error',
    ],
    success: [
      'bg-success',
      'text-white',
      'border-success',
      'shadow-sm',
      'hover:bg-green-600',
      'hover:shadow-md',
      'focus-visible:ring-success',
    ],
  }

  // Size classes - 尺寸样式类
  const sizeClasses = {
    xs: ['px-2', 'py-1', 'text-xs', 'rounded-md'],
    sm: ['px-3', 'py-1.5', 'text-xs'],
    md: ['px-4', 'py-2', 'text-sm'],
    lg: ['px-6', 'py-3', 'text-base'],
    xl: ['px-8', 'py-4', 'text-lg', 'rounded-xl'],
  }

  // Loading spinner - 加载动画
  const LoadingSpinner = () => (
    <svg
      className="animate-spin h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
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
  )

  // Ripple effect - 涟漪效果
  const [rippleCoords, setRippleCoords] = React.useState<{ x: number; y: number } | null>(null)

  const handleMouseDown = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!ripple || disabled || loading) return

    const button = e.currentTarget
    const rect = button.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    setRippleCoords({ x, y })

    // Reset ripple after animation - 动画后重置涟漪
    setTimeout(() => setRippleCoords(null), 600)
  }

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (loading || disabled) {
      e.preventDefault()
      return
    }
    onClick?.(e)
  }

  // Combine all classes - 合并所有样式类
  const classes = clsx(
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    className
  )

  return (
    <button
      className={classes}
      disabled={disabled || loading}
      onClick={handleClick}
      onMouseDown={handleMouseDown}
      {...props}
    >
      {/* Ripple effect - 涟漪效果 */}
      {ripple && rippleCoords && (
        <span
          className="absolute pointer-events-none animate-ping"
          style={{
            left: rippleCoords.x,
            top: rippleCoords.y,
            width: '20px',
            height: '20px',
            marginLeft: '-10px',
            marginTop: '-10px',
            borderRadius: '50%',
            backgroundColor: 'rgba(255, 255, 255, 0.5)',
          }}
        />
      )}

      {/* Loading state - 加载状态 */}
      {loading && <LoadingSpinner />}

      {/* Icon - 图标 */}
      {icon && !loading && iconPosition === 'left' && (
        <span className="mr-2" aria-hidden="true">
          {icon}
        </span>
      )}

      {/* Button content - 按钮内容 */}
      <span>{children}</span>

      {/* Icon on the right - 右侧图标 */}
      {icon && !loading && iconPosition === 'right' && (
        <span className="ml-2" aria-hidden="true">
          {icon}
        </span>
      )}
    </button>
  )
}

// Button group component - 按钮组组件
export interface ButtonGroupProps {
  /**
   * Spacing between buttons - 按钮间距
   * @default 'sm'
   */
  spacing?: 'none' | 'xs' | 'sm' | 'md'

  /**
   * Button alignment - 按钮对齐
   * @default 'left'
   */
  align?: 'left' | 'center' | 'right'

  /**
   * Group children - 子元素
   */
  children: React.ReactNode

  /**
   * Additional classes - 额外样式类
   */
  className?: string
}

export const ButtonGroup: React.FC<ButtonGroupProps> = ({
  spacing = 'sm',
  align = 'left',
  children,
  className
}) => {
  const spacingClasses = {
    none: '',
    xs: 'space-x-1',
    sm: 'space-x-2',
    md: 'space-x-3',
  }

  const alignClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
  }

  const classes = clsx(
    'flex',
    spacingClasses[spacing],
    alignClasses[align],
    className
  )

  return <div className={classes}>{children}</div>
}

// Floating Action Button (FAB) component - 浮动操作按钮组件
export interface FabProps extends Omit<ButtonProps, 'size'> {
  /**
   * FAB position - FAB位置
   * @default 'bottom-right'
   */
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'

  /**
   * Extended FAB with label - 扩展FAB带标签
   * @default false
   */
  extended?: boolean

  /**
   * FAB label text - FAB标签文本
   */
  label?: string
}

export const Fab: React.FC<FabProps> = ({
  position = 'bottom-right',
  extended = false,
  label,
  icon,
  children,
  className,
  ...props
}) => {
  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6',
    'top-right': 'top-6 right-6',
    'top-left': 'top-6 left-6',
  }

  const fabClasses = clsx(
    // Position - 定位
    'fixed',
    'z-50',
    positionClasses[position],

    // Shape - 形状
    'rounded-full',
    'shadow-lg',

    // Size - 尺寸
    extended ? 'px-6 py-3' : 'w-14 h-14',

    // Layout - 布局
    'flex',
    'items-center',
    'justify-center',

    // Transitions - 过渡
    'transition-all',
    'duration-200',

    // Hover - 悬停
    'hover:shadow-xl',
    'hover:scale-110',

    className
  )

  return (
    <button className={fabClasses} {...props}>
      {icon && (
        <span className={extended ? 'mr-2' : ''} aria-hidden="true">
          {icon}
        </span>
      )}
      {extended && (label || children)}
      {!extended && !icon && children}
    </button>
  )
}

// Export all button components - 导出所有按钮组件
export { Button as default }