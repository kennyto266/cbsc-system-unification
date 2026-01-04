import React from 'react'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { render } from './testUtils'
import { ParameterPreview } from '../ParameterPreview'

const mockParameters = {
  shortWindow: 10,
  longWindow: 30,
  rsiPeriod: 14,
  rsiThreshold: 70,
  volumeThreshold: 10000,
  stopLoss: 0.05,
  takeProfit: 0.1
}

const mockParameterConfig = {
  shortWindow: { type: 'number', min: 5, max: 20, step: 1, label: '短期窗口' },
  longWindow: { type: 'number', min: 20, max: 60, step: 1, label: '长期窗口' },
  rsiPeriod: { type: 'number', min: 7, max: 21, step: 1, label: 'RSI周期' },
  rsiThreshold: { type: 'number', min: 30, max: 90, step: 5, label: 'RSI阈值' },
  volumeThreshold: { type: 'number', min: 1000, max: 50000, step: 1000, label: '成交量阈值' },
  stopLoss: { type: 'number', min: 0.01, max: 0.2, step: 0.01, label: '止损比例' },
  takeProfit: { type: 'number', min: 0.02, max: 0.3, step: 0.01, label: '止盈比例' }
}

describe('ParameterPreview', () => {
  const defaultProps = {
    parameters: mockParameters,
    parameterConfig: mockParameterConfig,
    onParameterChange: jest.fn(),
    onApply: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<ParameterPreview {...defaultProps} />)
    expect(screen.getByText('参数预览')).toBeInTheDocument()
  })

  it('displays all parameters with their values', () => {
    render(<ParameterPreview {...defaultProps} />)

    expect(screen.getByDisplayValue('10')).toBeInTheDocument() // shortWindow
    expect(screen.getByDisplayValue('30')).toBeInTheDocument() // longWindow
    expect(screen.getByDisplayValue('14')).toBeInTheDocument() // rsiPeriod
    expect(screen.getByDisplayValue('70')).toBeInTheDocument() // rsiThreshold
  })

  it('shows parameter labels', () => {
    render(<ParameterPreview {...defaultProps} />)

    expect(screen.getByText('短期窗口')).toBeInTheDocument()
    expect(screen.getByText('长期窗口')).toBeInTheDocument()
    expect(screen.getByText('RSI周期')).toBeInTheDocument()
    expect(screen.getByText('RSI阈值')).toBeInTheDocument()
  })

  it('calls onParameterChange when a parameter is modified', async () => {
    render(<ParameterPreview {...defaultProps} />)

    const shortWindowInput = screen.getByDisplayValue('10')
    fireEvent.change(shortWindowInput, { target: { value: '12' } })

    await waitFor(() => {
      expect(defaultProps.onParameterChange).toHaveBeenCalledWith('shortWindow', 12)
    })
  })

  it('validates parameter constraints', () => {
    render(<ParameterPreview {...defaultProps} />)

    const shortWindowInput = screen.getByDisplayValue('10')
    fireEvent.change(shortWindowInput, { target: { value: '25' } }) // Beyond max of 20

    expect(screen.getByText(/超出范围/)).toBeInTheDocument()
  })

  it('shows real-time preview of results', () => {
    const mockResults = {
      totalReturn: 0.15,
      sharpeRatio: 1.5,
      maxDrawdown: -0.08,
      winRate: 0.65
    }

    render(<ParameterPreview {...defaultProps} previewResults={mockResults} />)

    expect(screen.getByText('15.00%')).toBeInTheDocument() // totalReturn
    expect(screen.getByText('1.500')).toBeInTheDocument() // sharpeRatio
    expect(screen.getByText('65.00%')).toBeInTheDocument() // winRate
  })

  it('resets parameters to default values', () => {
    const defaultParameters = {
      shortWindow: 5,
      longWindow: 20,
      rsiPeriod: 14,
      rsiThreshold: 50,
      volumeThreshold: 5000,
      stopLoss: 0.03,
      takeProfit: 0.06
    }

    render(
      <ParameterPreview
        {...defaultProps}
        defaultParameters={defaultParameters}
      />
    )

    const resetButton = screen.getByText('重置为默认')
    fireEvent.click(resetButton)

    expect(defaultProps.onParameterChange).toHaveBeenCalledTimes(Object.keys(mockParameters).length)
  })

  it('supports different parameter types', () => {
    const parameters = {
      strategyType: 'mean_reversion',
      tradingMode: 'automatic',
      riskLevel: 'medium'
    }

    const config = {
      strategyType: { type: 'select', options: ['mean_reversion', 'trend_following'], label: '策略类型' },
      tradingMode: { type: 'select', options: ['manual', 'automatic'], label: '交易模式' },
      riskLevel: { type: 'select', options: ['low', 'medium', 'high'], label: '风险等级' }
    }

    render(
      <ParameterPreview
        {...defaultProps}
        parameters={parameters}
        parameterConfig={config}
      />
    )

    expect(screen.getByDisplayValue('mean_reversion')).toBeInTheDocument()
    expect(screen.getByDisplayValue('automatic')).toBeInTheDocument()
    expect(screen.getByDisplayValue('medium')).toBeInTheDocument()
  })

  it('enables apply button only when parameters are valid', () => {
    render(<ParameterPreview {...defaultProps} />)

    const applyButton = screen.getByText('应用参数')
    expect(applyButton).toBeEnabled()

    // Make parameters invalid
    const shortWindowInput = screen.getByDisplayValue('10')
    fireEvent.change(shortWindowInput, { target: { value: '0' } })

    expect(applyButton).toBeDisabled()
  })

  it('debounces parameter changes to avoid excessive updates', async () => {
    jest.useFakeTimers()

    render(<ParameterPreview {...defaultProps} debounceMs={500} />)

    const shortWindowInput = screen.getByDisplayValue('10')

    // Fire multiple changes rapidly
    fireEvent.change(shortWindowInput, { target: { value: '11' } })
    fireEvent.change(shortWindowInput, { target: { value: '12' } })
    fireEvent.change(shortWindowInput, { target: { value: '13' } })

    // Should not have been called yet
    expect(defaultProps.onParameterChange).not.toHaveBeenCalled()

    // Fast-forward time
    jest.advanceTimersByTime(500)

    // Should only be called once with the last value
    await waitFor(() => {
      expect(defaultProps.onParameterChange).toHaveBeenCalledTimes(1)
      expect(defaultProps.onParameterChange).toHaveBeenCalledWith('shortWindow', 13)
    })

    jest.useRealTimers()
  })

  it('shows loading state during preview calculation', () => {
    render(<ParameterPreview {...defaultProps} loading={true} />)

    expect(screen.getByText('计算中...')).toBeInTheDocument()
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('displays parameter impact analysis', () => {
    const mockImpact = {
      shortWindow: { impact: 0.02, sensitivity: 'high' },
      longWindow: { impact: 0.01, sensitivity: 'medium' },
      rsiThreshold: { impact: 0.005, sensitivity: 'low' }
    }

    render(<ParameterPreview {...defaultProps} parameterImpact={mockImpact} />)

    expect(screen.getByText('参数影响分析')).toBeInTheDocument()
    expect(screen.getByText('短期窗口')).toBeInTheDocument()
    expect(screen.getByText('高')).toBeInTheDocument() // sensitivity for shortWindow
  })
})