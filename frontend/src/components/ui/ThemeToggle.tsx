import React from 'react'
import { useTheme } from '../../styles/themes'
import { clsx } from 'clsx'

// Theme toggle component interface - 主题切换组件接口
export interface ThemeToggleProps {
  /**
   * Toggle size - 切换器尺寸
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg'

  /**
   * Show label - 显示标签
   * @default false
   */
  showLabel?: boolean

  /**
   * Custom label - 自定义标签
   */
  label?: string

  /**
   * Additional classes - 额外样式类
   */
  className?: string
}

// Theme toggle component - 主题切换组件
export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  size = 'md',
  showLabel = false,
  label,
  className
}) => {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  // Size classes - 尺寸样式
  const sizeClasses = {
    sm: {
      container: 'w-8 h-4',
      thumb: 'w-3 h-3',
      translate: 'translate-x-4',
    },
    md: {
      container: 'w-11 h-6',
      thumb: 'w-5 h-5',
      translate: 'translate-x-5',
    },
    lg: {
      container: 'w-14 h-8',
      thumb: 'w-6 h-6',
      translate: 'translate-x-6',
    },
  }

  // Icon components - 图标组件
  const SunIcon = () => (
    <svg
      className="w-4 h-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  )

  const MoonIcon = () => (
    <svg
      className="w-4 h-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
      />
    </svg>
  )

  const handleToggle = () => {
    toggleTheme()
  }

  const containerClasses = clsx(
    // Base layout - 基础布局
    'relative',
    'inline-flex',
    'flex-shrink-0',
    'cursor-pointer',
    'rounded-full',
    'border-2',
    'border-transparent',
    'transition-colors',
    'duration-200',
    'ease-in-out',

    // Size - 尺寸
    sizeClasses[size].container,

    // Theme colors - 主题色
    isDark
      ? 'bg-gray-600'
      : 'bg-gray-200',

    // Focus - 焦点
    'focus:outline-none',
    'focus:ring-2',
    'focus:ring-offset-2',
    'focus:ring-primary',

    className
  )

  const thumbClasses = clsx(
    // Base layout - 基础布局
    'pointer-events-none',
    'inline-block',
    'rounded-full',
    'bg-white',
    'shadow-md',
    'ring-0',
    'transition-transform',
    'duration-200',
    'ease-in-out',

    // Size - 尺寸
    sizeClasses[size].thumb,

    // Position - 位置
    isDark
      ? sizeClasses[size].translate
      : 'translate-x-0'
  )

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        className={containerClasses}
        role="switch"
        aria-checked={isDark}
        onClick={handleToggle}
        aria-label={label || `Switch to ${isDark ? 'light' : 'dark'} theme`}
      >
        <span className={thumbClasses}>
          <span className="flex h-full w-full items-center justify-center">
            {isDark ? <MoonIcon /> : <SunIcon />}
          </span>
        </span>
      </button>

      {showLabel && (
        <span className="text-sm font-medium text-text-secondary">
          {label || (isDark ? 'Dark' : 'Light')}
        </span>
      )}
    </div>
  )
}

// Theme selector component with dropdown - 下拉主题选择器组件
export interface ThemeSelectorProps {
  /**
   * Selector size - 选择器尺寸
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg'

  /**
   * Show current theme icon - 显示当前主题图标
   * @default true
   */
  showIcon?: boolean

  /**
   * Custom trigger button - 自定义触发按钮
   */
  trigger?: React.ReactNode

  /**
   * Additional classes - 额外样式类
   */
  className?: string
}

export const ThemeSelector: React.FC<ThemeSelectorProps> = ({
  size = 'md',
  showIcon = true,
  trigger,
  className
}) => {
  const { theme, setTheme, themeConfig } = useTheme()
  const [isOpen, setIsOpen] = React.useState(false)

  // Theme options - 主题选项
  const themes = [
    {
      name: 'light',
      label: 'Light',
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
      ),
    },
    {
      name: 'dark',
      label: 'Dark',
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
          />
        </svg>
      ),
    },
  ]

  const handleSelectTheme = (themeName: string) => {
    setTheme(themeName)
    setIsOpen(false)
  }

  const currentTheme = themes.find(t => t.name === theme)

  // Size classes - 尺寸样式
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  }

  return (
    <div className="relative">
      {/* Trigger button - 触发按钮 */}
      {trigger ? (
        <div onClick={() => setIsOpen(!isOpen)}>{trigger}</div>
      ) : (
        <button
          type="button"
          className={clsx(
            'btn',
            'secondary',
            sizeClasses[size],
            'flex items-center gap-2',
            className
          )}
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
        >
          {showIcon && currentTheme?.icon}
          <span>{currentTheme?.label}</span>
          <svg
            className={clsx('w-4 h-4 transition-transform', isOpen && 'rotate-180')}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
      )}

      {/* Dropdown menu - 下拉菜单 */}
      {isOpen && (
        <>
          {/* Backdrop - 背景 */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />

          {/* Menu - 菜单 */}
          <div className="absolute right-0 z-20 mt-2 w-48 rounded-lg bg-background-primary border border-border-primary shadow-lg focus:outline-none">
            <div className="py-1" role="listbox">
              {themes.map((themeOption) => (
                <button
                  key={themeOption.name}
                  type="button"
                  className={clsx(
                    'w-full px-4 py-2 text-left flex items-center gap-3',
                    'text-sm text-text-primary hover:bg-background-secondary',
                    'focus:bg-background-secondary focus:outline-none',
                    theme === themeOption.name && 'bg-background-secondary text-primary'
                  )}
                  onClick={() => handleSelectTheme(themeOption.name)}
                  role="option"
                  aria-selected={theme === themeOption.name}
                >
                  <span className="flex-shrink-0">{themeOption.icon}</span>
                  <span>{themeOption.label}</span>
                  {theme === themeOption.name && (
                    <svg
                      className="w-4 h-4 ml-auto text-primary"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// Export theme components - 导出主题组件
export { ThemeToggle as default }