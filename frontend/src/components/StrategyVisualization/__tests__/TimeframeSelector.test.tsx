import React from 'react'
import { screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { render } from '../test-helpers'
import { TimeframeSelector } from '../TimeframeSelector'

describe('TimeframeSelector', () => {
  const defaultProps = {
    value: '1m',
    onChange: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<TimeframeSelector {...defaultProps} />)
    expect(screen.getByTestId('timeframe-selector')).toBeInTheDocument()
  })

  it('displays all timeframe options', () => {
    render(<TimeframeSelector {...defaultProps} />)

    expect(screen.getByText('1天')).toBeInTheDocument()
    expect(screen.getByText('1周')).toBeInTheDocument()
    expect(screen.getByText('1月')).toBeInTheDocument()
    expect(screen.getByText('1年')).toBeInTheDocument()
    expect(screen.getByText('全部')).toBeInTheDocument()
  })

  it('shows the selected value', () => {
    render(<TimeframeSelector {...defaultProps} value="1w" />)

    const selector = screen.getByTestId('timeframe-selector')
    expect(selector).toHaveValue('1w')
  })

  it('calls onChange when selection changes', () => {
    const mockOnChange = jest.fn()
    render(<TimeframeSelector {...defaultProps} onChange={mockOnChange} />)

    const selector = screen.getByTestId('timeframe-selector')
    fireEvent.change(selector, { target: { value: '1y' } })

    expect(mockOnChange).toHaveBeenCalledWith('1y')
  })

  it('applies custom className', () => {
    render(<TimeframeSelector {...defaultProps} className="custom-class" />)

    const selector = screen.getByTestId('timeframe-selector')
    expect(selector).toHaveClass('custom-class')
  })

  it('disables selector when disabled prop is true', () => {
    render(<TimeframeSelector {...defaultProps} disabled={true} />)

    const selector = screen.getByTestId('timeframe-selector')
    expect(selector).toBeDisabled()
  })

  it('shows label when provided', () => {
    render(<TimeframeSelector {...defaultProps} label="时间范围" />)

    expect(screen.getByText('时间范围')).toBeInTheDocument()
  })

  it('supports compact mode', () => {
    render(<TimeframeSelector {...defaultProps} compact={true} />)

    const selector = screen.getByTestId('timeframe-selector')
    expect(selector).toHaveClass('px-2', 'py-1', 'text-sm')
  })
})