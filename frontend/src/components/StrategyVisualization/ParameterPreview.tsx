import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { useTheme } from '../../contexts/ThemeContext'
import { useDebounce } from '../../hooks/useDebounce'

export type ParameterType = 'number' | 'select' | 'boolean' | 'range'

export interface ParameterConfig {
  type: ParameterType
  label: string
  min?: number
  max?: number
  step?: number
  options?: string[]
  unit?: string
  description?: string
  impact?: 'low' | 'medium' | 'high'
}

export interface StrategyParameters {
  [key: string]: any
}

export interface PreviewResults {
  totalReturn?: number
  sharpeRatio?: number
  maxDrawdown?: number
  winRate?: number
  profitFactor?: number
  calmarRatio?: number
  sortinoRatio?: number
}

export interface ParameterImpact {
  [parameter: string]: {
    impact: number
    sensitivity: 'low' | 'medium' | 'high'
    description?: string
  }
}

export interface ParameterPreviewProps {
  parameters: StrategyParameters
  parameterConfig: { [key: string]: ParameterConfig }
  defaultParameters?: StrategyParameters
  previewResults?: PreviewResults
  parameterImpact?: ParameterImpact
  onParameterChange?: (parameter: string, value: any) => void
  onApply?: (parameters: StrategyParameters) => void
  onReset?: () => void
  onOptimize?: (parameters: StrategyParameters) => void
  loading?: boolean
  debounceMs?: number
  showImpact?: boolean
  showOptimization?: boolean
  className?: string
}

export const ParameterPreview: React.FC<ParameterPreviewProps> = ({
  parameters,
  parameterConfig,
  defaultParameters,
  previewResults,
  parameterImpact,
  onParameterChange,
  onApply,
  onReset,
  onOptimize,
  loading = false,
  debounceMs = 300,
  showImpact = false,
  showOptimization = false,
  className = ''
}) => {
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'

  // Local state for parameter changes
  const [localParameters, setLocalParameters] = useState<StrategyParameters>(parameters)
  const [validationErrors, setValidationErrors] = useState<{ [key: string]: string }>({})
  const [isDirty, setIsDirty] = useState(false)

  // Debounced parameters for preview
  const debouncedParameters = useDebounce(localParameters, debounceMs)

  // Update local parameters when props change
  useEffect(() => {
    setLocalParameters(parameters)
    setIsDirty(false)
  }, [parameters])

  // Handle parameter change with validation
  const handleParameterChange = useCallback((parameter: string, value: any) => {
    const config = parameterConfig[parameter]
    const errors = { ...validationErrors }

    // Validate based on parameter type
    if (config.type === 'number' || config.type === 'range') {
      const numValue = parseFloat(value)

      if (isNaN(numValue)) {
        errors[parameter] = '请输入有效数字'
      } else if (config.min !== undefined && numValue < config.min) {
        errors[parameter] = `值不能小于 ${config.min}`
      } else if (config.max !== undefined && numValue > config.max) {
        errors[parameter] = `值不能大于 ${config.max}`
      } else {
        delete errors[parameter]
      }

      value = numValue
    }

    setValidationErrors(errors)
    setLocalParameters(prev => ({ ...prev, [parameter]: value }))
    setIsDirty(true)

    // Call parent handler if valid
    if (!errors[parameter]) {
      onParameterChange?.(parameter, value)
    }
  }, [parameterConfig, validationErrors, onParameterChange])

  // Check if all parameters are valid
  const isValid = useMemo(() => {
    return Object.keys(validationErrors).length === 0
  }, [validationErrors])

  // Apply parameters
  const handleApply = useCallback(() => {
    if (isValid && onApply) {
      onApply(localParameters)
      setIsDirty(false)
    }
  }, [isValid, localParameters, onApply])

  // Reset to default parameters
  const handleReset = useCallback(() => {
    if (defaultParameters) {
      setLocalParameters(defaultParameters)
      setValidationErrors({})
      setIsDirty(true)
      onReset?.()
    }
  }, [defaultParameters, onReset])

  // Render parameter input based on type
  const renderParameterInput = useCallback((key: string, config: ParameterConfig) => {
    const value = localParameters[key]
    const error = validationErrors[key]

    const baseClasses = `
      w-full px-3 py-2 rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500
      ${error
        ? 'border-red-500 focus:ring-red-500'
        : isDark
          ? 'bg-gray-700 border-gray-600 text-white hover:bg-gray-600'
          : 'bg-white border-gray-300 text-gray-900 hover:bg-gray-50'
      }
    `

    switch (config.type) {
      case 'number':
        return (
          <input
            type="number"
            min={config.min}
            max={config.max}
            step={config.step || 'any'}
            value={value || ''}
            onChange={(e) => handleParameterChange(key, e.target.value)}
            className={baseClasses}
          />
        )

      case 'range':
        return (
          <div className="space-y-2">
            <input
              type="range"
              min={config.min}
              max={config.max}
              step={config.step || 'any'}
              value={value || 0}
              onChange={(e) => handleParameterChange(key, parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>{config.min}</span>
              <span className="font-medium">{value}</span>
              <span>{config.max}</span>
            </div>
          </div>
        )

      case 'select':
        return (
          <select
            value={value || ''}
            onChange={(e) => handleParameterChange(key, e.target.value)}
            className={baseClasses}
          >
            {config.options?.map(option => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        )

      case 'boolean':
        return (
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={value || false}
              onChange={(e) => handleParameterChange(key, e.target.checked)}
              className="rounded text-blue-600 focus:ring-blue-500"
            />
            <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              {config.label}
            </span>
          </label>
        )

      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleParameterChange(key, e.target.value)}
            className={baseClasses}
          />
        )
    }
  }, [localParameters, validationErrors, isDark, handleParameterChange])

  return (
    <div className={`w-full space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className={`text-xl font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
          参数预览
        </h2>

        <div className="flex space-x-2">
          {showOptimization && onOptimize && (
            <button
              onClick={() => onOptimize(localParameters)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isDark
                  ? 'bg-purple-600 text-white hover:bg-purple-700'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              }`}
            >
              优化参数
            </button>
          )}

          {defaultParameters && (
            <button
              onClick={handleReset}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isDark
                  ? 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              重置为默认
            </button>
          )}

          <button
            onClick={handleApply}
            disabled={!isValid || !isDirty}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              !isValid || !isDirty
                ? 'opacity-50 cursor-not-allowed'
                : isDark
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            应用参数
          </button>
        </div>
      </div>

      {/* Parameters Grid */}
      <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(parameterConfig).map(([key, config]) => {
            const impact = parameterImpact?.[key]
            const value = localParameters[key]

            return (
              <div key={key} className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                    {config.label}
                    {config.unit && <span className="ml-1">({config.unit})</span>}
                  </label>

                  {showImpact && impact && (
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      impact.sensitivity === 'high'
                        ? 'bg-red-100 text-red-700'
                        : impact.sensitivity === 'medium'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-green-100 text-green-700'
                    }`}>
                      {impact.sensitivity === 'high' ? '高' :
                       impact.sensitivity === 'medium' ? '中' : '低'}敏感度
                    </span>
                  )}
                </div>

                {renderParameterInput(key, config)}

                {validationErrors[key] && (
                  <p className="text-sm text-red-500">
                    {validationErrors[key]}
                  </p>
                )}

                {config.description && (
                  <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    {config.description}
                  </p>
                )}

                {showImpact && impact && (
                  <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    影响: {(impact.impact * 100).toFixed(2)}%
                    {impact.description && ` - ${impact.description}`}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Preview Results */}
      {previewResults && (
        <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className={`text-lg font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
              预览结果
            </h3>

            {loading && (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  计算中...
                </span>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {previewResults.totalReturn !== undefined && (
              <div>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>总收益率</p>
                <p className={`text-lg font-semibold ${
                  previewResults.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {(previewResults.totalReturn * 100).toFixed(2)}%
                </p>
              </div>
            )}

            {previewResults.sharpeRatio !== undefined && (
              <div>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>夏普比率</p>
                <p className={`text-lg font-semibold ${
                  previewResults.sharpeRatio >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {previewResults.sharpeRatio.toFixed(3)}
                </p>
              </div>
            )}

            {previewResults.maxDrawdown !== undefined && (
              <div>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>最大回撤</p>
                <p className="text-lg font-semibold text-red-600">
                  {(previewResults.maxDrawdown * 100).toFixed(2)}%
                </p>
              </div>
            )}

            {previewResults.winRate !== undefined && (
              <div>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>胜率</p>
                <p className={`text-lg font-semibold ${
                  previewResults.winRate >= 0.5 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {(previewResults.winRate * 100).toFixed(2)}%
                </p>
              </div>
            )}

            {previewResults.profitFactor !== undefined && (
              <div>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>盈亏比</p>
                <p className={`text-lg font-semibold ${
                  previewResults.profitFactor >= 1 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {previewResults.profitFactor.toFixed(2)}
                </p>
              </div>
            )}

            {previewResults.calmarRatio !== undefined && (
              <div>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>卡尔马比率</p>
                <p className={`text-lg font-semibold ${
                  previewResults.calmarRatio >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {previewResults.calmarRatio.toFixed(3)}
                </p>
              </div>
            )}

            {previewResults.sortinoRatio !== undefined && (
              <div>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>索提诺比率</p>
                <p className={`text-lg font-semibold ${
                  previewResults.sortinoRatio >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {previewResults.sortinoRatio.toFixed(3)}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Parameter Impact Analysis */}
      {showImpact && parameterImpact && Object.keys(parameterImpact).length > 0 && (
        <div className={`p-4 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}>
          <h3 className={`text-lg font-medium mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            参数影响分析
          </h3>

          <div className="space-y-3">
            {Object.entries(parameterImpact)
              .sort((a, b) => Math.abs(b[1].impact) - Math.abs(a[1].impact))
              .map(([parameter, impact]) => {
                const config = parameterConfig[parameter]

                return (
                  <div key={parameter} className="flex items-center justify-between">
                    <div className="flex-1">
                      <span className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                        {config?.label || parameter}
                      </span>
                      {impact.description && (
                        <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                          {impact.description}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center space-x-4">
                      <span className={`text-sm ${
                        impact.sensitivity === 'high'
                          ? 'text-red-600'
                          : impact.sensitivity === 'medium'
                            ? 'text-yellow-600'
                            : 'text-green-600'
                      }`}>
                        {impact.sensitivity === 'high' ? '高' :
                         impact.sensitivity === 'medium' ? '中' : '低'}敏感度
                      </span>

                      <span className={`text-sm font-medium ${
                        impact.impact > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {impact.impact > 0 ? '+' : ''}{(impact.impact * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                )
              })}
          </div>
        </div>
      )}
    </div>
  )
}

export default ParameterPreview