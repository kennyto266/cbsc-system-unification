import React from 'react'
import { useTheme } from '../../contexts/ThemeContext'

export type Timeframe = '1d' | '1w' | '1m' | '1y' | 'all'

export interface TimeframeSelectorProps {
  value: Timeframe | string
  onChange: (value: Timeframe) => void
  label?: string
  disabled?: boolean
  compact?: boolean
  className?: string
}

const timeframeOptions: { value: Timeframe; label: string }[] = [
  { value: '1d', label: '1天' },
  { value: '1w', label: '1周' },
  { value: '1m', label: '1月' },
  { value: '1y', label: '1年' },
  { value: 'all', label: '全部' }
]

export const TimeframeSelector: React.FC<TimeframeSelectorProps> = ({
  value,
  onChange,
  label,
  disabled = false,
  compact = false,
  className = ''
}) => {
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'

  const baseClasses = `
    rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500
    ${compact ? 'px-2 py-1 text-sm' : 'px-3 py-2'}
    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
    ${isDark
      ? 'bg-gray-700 border-gray-600 text-white hover:bg-gray-600'
      : 'bg-white border-gray-300 text-gray-900 hover:bg-gray-50'
    }
  `

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {label && (
        <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          {label}
        </label>
      )}

      <select
        data-testid="timeframe-selector"
        value={value}
        onChange={(e) => onChange(e.target.value as Timeframe)}
        disabled={disabled}
        className={`${baseClasses} ${className}`}
      >
        {timeframeOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export default TimeframeSelector