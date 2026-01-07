import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { SensitivityAnalysis } from '../SensitivityAnalysis'

// Mock recharts with prop filtering
jest.mock('recharts', () => {
  const React = require('react')
  const RECHARTS_PROPS = [
    'dataKey', 'name', 'data', 'cx', 'cy', 'r', 'fill', 'stroke', 'strokeWidth',
    'labelLine', 'outerRadius', 'innerRadius', 'startAngle', 'endAngle',
    'label', 'legendType', 'hide', 'barSize', 'barGap', 'barCategoryGap',
    'tickFormatter', 'ticks', 'interval', 'angle', 'domain', 'type',
    'connectNulls', 'isAnimationActive', 'animationBegin', 'animationDuration',
    'layout', 'stackOffset', 'stackId', 'unit', 'nameKey', 'width', 'height',
    'min', 'max', 'padding', 'allowDataOverflow', 'margin', 'reverse',
    'x', 'y', 'z', 'line', 'lineType', 'dot', 'activeDot', 'hide',
    'isFront', 'background', 'clockwise', 'textBreakPoints'
  ]

  const filterProps = (props: any) => {
    const filtered: any = {}
    const dataAttrs: any = {}
    Object.entries(props).forEach(([key, value]) => {
      if (RECHARTS_PROPS.includes(key)) {
        // Skip Recharts props
      } else if (key.startsWith('data-')) {
        dataAttrs[key] = value
      } else if (key === 'dot' && value === false) {
        // Convert boolean false to string for DOM
        filtered[key] = 'false'
      } else {
        filtered[key] = value
      }
    })
    return { ...filtered, ...dataAttrs }
  }

  return {
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      React.createElement('div', { 'data-testid': 'responsive-container' }, children)
    ),
    LineChart: ({ children }: { children: React.ReactNode }) => (
      React.createElement('div', { 'data-testid': 'line-chart' }, children)
    ),
    Line: (props: any) => React.createElement('div', { 'data-testid': 'line', ...filterProps(props) }),
    XAxis: (props: any) => React.createElement('div', { 'data-testid': 'x-axis', ...filterProps(props) }),
    YAxis: (props: any) => React.createElement('div', { 'data-testid': 'y-axis', ...filterProps(props) }),
    CartesianGrid: (props: any) => React.createElement('div', { 'data-testid': 'cartesian-grid', ...filterProps(props) }),
    Tooltip: (props: any) => React.createElement('div', { 'data-testid': 'tooltip', ...filterProps(props) }),
    Legend: (props: any) => React.createElement('div', { 'data-testid': 'legend', ...filterProps(props) }),
    ScatterChart: ({ children }: { children: React.ReactNode }) => (
      React.createElement('div', { 'data-testid': 'scatter-chart' }, children)
    ),
    Scatter: (props: any) => React.createElement('div', { 'data-testid': 'scatter', ...filterProps(props) }),
    Cell: (props: any) => React.createElement('div', { 'data-testid': 'cell', ...filterProps(props) }),
    Surface: ({ children }: { children: React.ReactNode }) => (
      React.createElement('div', { 'data-testid': 'surface' }, children)
    )
  }
})

jest.mock('@/contexts/ThemeContext', () => ({
  useTheme: () => ({
    resolvedTheme: 'light'
  }),
  ThemeProvider: ({ children }: any) => <div>{children}</div>
}))

const mockParameters = {
  shortWindow: 10,
  longWindow: 30,
  rsiThreshold: 70
}

const mockSensitivityData = {
  shortWindow: [
    { value: 5, return: 0.08, sharpe: 1.2, drawdown: -0.12 },
    { value: 10, return: 0.15, sharpe: 1.8, drawdown: -0.08 },
    { value: 15, return: 0.12, sharpe: 1.5, drawdown: -0.10 }
  ],
  longWindow: [
    { value: 20, return: 0.10, sharpe: 1.3, drawdown: -0.15 },
    { value: 30, return: 0.15, sharpe: 1.8, drawdown: -0.08 },
    { value: 40, return: 0.13, sharpe: 1.6, drawdown: -0.09 }
  ],
  rsiThreshold: [
    { value: 60, return: 0.14, sharpe: 1.6, drawdown: -0.10 },
    { value: 70, return: 0.15, sharpe: 1.8, drawdown: -0.08 },
    { value: 80, return: 0.11, sharpe: 1.4, drawdown: -0.11 }
  ]
}

const mockHeatmapData = [
  { x: 5, y: 20, z: 0.08 },
  { x: 5, y: 30, z: 0.09 },
  { x: 10, y: 20, z: 0.14 },
  { x: 10, y: 30, z: 0.15 },
  { x: 15, y: 20, z: 0.10 },
  { x: 15, y: 30, z: 0.11 }
]

describe('SensitivityAnalysis', () => {
  const defaultProps = {
    parameters: mockParameters,
    sensitivityData: mockSensitivityData,
    onParameterChange: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(<SensitivityAnalysis {...defaultProps} />)
    expect(screen.getByText('参数敏感性分析')).toBeInTheDocument()
  })

  it('displays parameter selection dropdown', () => {
    render(<SensitivityAnalysis {...defaultProps} />)

    const selector = screen.getByTestId('parameter-selector')
    expect(selector).toBeInTheDocument()

    expect(screen.getByText('shortWindow')).toBeInTheDocument()
    expect(screen.getByText('longWindow')).toBeInTheDocument()
    expect(screen.getByText('rsiThreshold')).toBeInTheDocument()
  })

  it('switches parameter when selection changes', async () => {
    render(<SensitivityAnalysis {...defaultProps} />)

    const selector = screen.getByTestId('parameter-selector')
    fireEvent.change(selector, { target: { value: 'longWindow' } })

    await waitFor(() => {
      expect(selector).toHaveValue('longWindow')
    })
  })

  it('displays sensitivity chart', () => {
    render(<SensitivityAnalysis {...defaultProps} />)

    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    const lines = screen.getAllByTestId('line')
    expect(lines.length).toBeGreaterThan(0)
  })

  it('shows multiple metrics in chart', () => {
    render(<SensitivityAnalysis {...defaultProps} />)

    const lines = screen.getAllByTestId('line')
    expect(lines.length).toBeGreaterThan(1) // Should have multiple lines for different metrics
  })

  it('displays optimal parameters when available', () => {
    const optimalParams = {
      shortWindow: 10,
      longWindow: 30,
      rsiThreshold: 70
    }

    render(
      <SensitivityAnalysis
        {...defaultProps}
        optimalParameters={optimalParams}
      />
    )

    expect(screen.getByText('最优参数值: 10')).toBeInTheDocument()
  })

  it('shows heatmap view for two-parameter analysis', () => {
    render(
      <SensitivityAnalysis
        {...defaultProps}
        heatmapData={mockHeatmapData}
        heatmapConfig={{
          xParam: 'shortWindow',
          yParam: 'longWindow',
          metric: 'return'
        }}
        showHeatmap={true}
      />
    )

    expect(screen.getByText('双参数热力图')).toBeInTheDocument()
  })

  it('handles parameter range change', async () => {
    render(<SensitivityAnalysis {...defaultProps} />)

    const rangeStart = screen.getByLabelText('范围起始')
    const rangeEnd = screen.getByLabelText('范围结束')

    fireEvent.change(rangeStart, { target: { value: '8' } })
    fireEvent.change(rangeEnd, { target: { value: '12' } })

    await waitFor(() => {
      expect(defaultProps.onParameterChange).toHaveBeenCalledWith('shortWindow', {
        range: { min: 8, max: 12 }
      })
    })
  })

  it('exports sensitivity results when export button is clicked', () => {
    const mockExport = jest.fn()
    render(<SensitivityAnalysis {...defaultProps} onExport={mockExport} />)

    const exportButton = screen.getByText('导出结果')
    fireEvent.click(exportButton)

    expect(mockExport).toHaveBeenCalledWith(mockSensitivityData)
  })

  it('shows loading state during analysis', () => {
    render(<SensitivityAnalysis {...defaultProps} loading={true} />)

    expect(screen.getByText('分析中...')).toBeInTheDocument()
  })

  it('handles zero or negative data gracefully', () => {
    const zeroData = {
      shortWindow: [
        { value: 10, return: 0, sharpe: 0, drawdown: 0 }
      ]
    }

    render(<SensitivityAnalysis {...defaultProps} sensitivityData={zeroData} />)

    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  it('adjusts axis scales based on data range', () => {
    const largeValueData = {
      shortWindow: [
        { value: 10, return: 2.5, sharpe: 5.0, drawdown: -0.8 }
      ]
    }

    render(<SensitivityAnalysis {...defaultProps} sensitivityData={largeValueData} />)

    const yAxes = screen.getAllByTestId('y-axis')
    expect(yAxes.length).toBeGreaterThan(0)
  })

  it('supports custom metric selection', () => {
    render(<SensitivityAnalysis {...defaultProps} />)

    expect(screen.getByText('收益率')).toBeInTheDocument()
    expect(screen.getByText('夏普比率')).toBeInTheDocument()
    expect(screen.getByText('最大回撤')).toBeInTheDocument()
  })

  it('shows parameter recommendations', () => {
    const recommendations = [
      {
        parameter: 'shortWindow',
        reason: '提高收益率',
        suggestion: '增加到12',
        impact: 'high' as const
      }
    ]

    render(
      <SensitivityAnalysis
        {...defaultProps}
        recommendations={recommendations}
      />
    )

    expect(screen.getByText('参数建议')).toBeInTheDocument()
    expect(screen.getByText('shortWindow: 增加到12')).toBeInTheDocument()
  })

  it('handles empty sensitivity data', () => {
    render(<SensitivityAnalysis {...defaultProps} sensitivityData={{}} />)

    expect(screen.getByText('暂无敏感性数据')).toBeInTheDocument()
  })
})
