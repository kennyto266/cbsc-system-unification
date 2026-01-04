/**
 * Setup Tests Configuration
 * 测试环境配置文件
 */

// Import jest-dom for custom matchers
import '@testing-library/jest-dom'

// @ts-ignore
import { TextEncoder, TextDecoder } from 'util'

// Polyfill for TextEncoder/TextDecoder
global.TextEncoder = TextEncoder
// @ts-ignore
global.TextDecoder = TextDecoder

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return []
  }
  unobserve() {}
} as any

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any

// Mock requestAnimationFrame
global.requestAnimationFrame = (callback: FrameRequestCallback) => {
  return setTimeout(callback, 0) as unknown as number
}

global.cancelAnimationFrame = (id: number) => {
  clearTimeout(id)
}

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
    get length() {
      return Object.keys(store).length
    },
    key: (index: number) => {
      return Object.keys(store)[index] || null
    },
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock URL.createObjectURL and revokeObjectURL
global.URL.createObjectURL = jest.fn(() => 'mock-url')
global.URL.revokeObjectURL = jest.fn()

export {}

// Mock HTMLCanvasElement for jsPDF
HTMLCanvasElement.prototype.getContext = jest.fn() as any
HTMLCanvasElement.prototype.toDataURL = jest.fn() as any

// Fix for React 18 createRoot issue with jsdom
global.IS_REACT_ACT_ENVIRONMENT = true

// ===== CHART MOCKS =====
// Mock Recharts components
jest.mock('recharts', () => {
  const React = require('react')

  // Create mock component
  const createMockComponent = (displayName: string, className: string) => {
    const MockComponent = React.forwardRef<any, any>(
      ({ children, data, className: customClassName, style, ...props }: any, ref) => {
        return (
          <div
            data-testid={`recharts-${displayName.toLowerCase()}`}
            className={`${className} ${customClassName || ''}`.trim()}
            style={style}
            ref={ref}
            {...props}
          >
            {children}
          </div>
        )
      }
    )
    MockComponent.displayName = displayName
    return MockComponent
  }

  return {
    ResponsiveContainer: createMockComponent('ResponsiveContainer', 'recharts-responsive-container'),
    AreaChart: createMockComponent('AreaChart', 'recharts-area-chart'),
    LineChart: createMockComponent('LineChart', 'recharts-line-chart'),
    BarChart: createMockComponent('BarChart', 'recharts-bar-chart'),
    ScatterChart: createMockComponent('ScatterChart', 'recharts-scatter-chart'),
    PieChart: createMockComponent('PieChart', 'recharts-pie-chart'),
    RadarChart: createMockComponent('RadarChart', 'recharts-radar-chart'),
    Area: createMockComponent('Area', 'recharts-area'),
    Line: createMockComponent('Line', 'recharts-line'),
    Bar: createMockComponent('Bar', 'recharts-bar'),
    Scatter: createMockComponent('Scatter', 'recharts-scatter'),
    Pie: createMockComponent('Pie', 'recharts-pie'),
    Radar: createMockComponent('Radar', 'recharts-radar'),
    Cell: createMockComponent('Cell', 'recharts-cell'),
    XAxis: createMockComponent('XAxis', 'recharts-xAxis'),
    YAxis: createMockComponent('YAxis', 'recharts-yAxis'),
    ZAxis: createMockComponent('ZAxis', 'recharts-zAxis'),
    CartesianGrid: createMockComponent('CartesianGrid', 'recharts-cartesian-grid'),
    Tooltip: createMockComponent('Tooltip', 'recharts-tooltip-wrapper'),
    Legend: createMockComponent('Legend', 'recharts-legend'),
    ReferenceLine: createMockComponent('ReferenceLine', 'recharts-reference-line'),
    ReferenceArea: createMockComponent('ReferenceArea', 'recharts-reference-area'),
    ReferenceDot: createMockComponent('ReferenceDot', 'recharts-reference-dot'),
  }
})

// Mock Plotly.js
jest.mock('react-plotly.js', () => {
  const React = require('react')
  return React.forwardRef<any, any>((props, ref) => (
    <div
      data-testid="mock-plotly-chart"
      ref={ref}
      style={{ width: props.width || '100%', height: props.height || '100%' }}
      className="plotly-chart"
    >
      <div data-testid="plotly-data">{JSON.stringify(props.data)}</div>
      <div data-testid="plotly-layout">{JSON.stringify(props.layout)}</div>
      <div data-testid="plotly-config">{JSON.stringify(props.config)}</div>
    </div>
  ))
})

// Mock Chart.js
jest.mock('react-chartjs-2', () => {
  const React = require('react')
  return {
    Line: React.forwardRef<any, any>((props: any, ref) => {
      const { width, height, data, options, tabIndex, ...rest } = props
      return (
        <div
          data-testid="mock-line-chart"
          ref={ref}
          tabIndex={tabIndex}
          style={{ width: width || '100%', height: height || '100%' }}
          className="chartjs-line"
          {...rest}
        >
          <div data-testid="chart-data">{JSON.stringify(data)}</div>
          <div data-testid="chart-options">{JSON.stringify(options)}</div>
        </div>
      )
    }),
    Bar: React.forwardRef<any, any>((props: any, ref) => (
      <div
        data-testid="mock-bar-chart"
        ref={ref}
        tabIndex={props.tabIndex}
        className="chartjs-bar"
      >
        <div data-testid="chart-data">{JSON.stringify(props.data)}</div>
      </div>
    )),
    Doughnut: React.forwardRef<any, any>((props: any, ref) => (
      <div
        data-testid="mock-doughnut-chart"
        ref={ref}
        className="chartjs-doughnut"
      >
        <div data-testid="chart-data">{JSON.stringify(props.data)}</div>
      </div>
    )),
    Pie: React.forwardRef<any, any>((props: any, ref) => (
      <div
        data-testid="mock-pie-chart"
        ref={ref}
        className="chartjs-pie"
      >
        <div data-testid="chart-data">{JSON.stringify(props.data)}</div>
      </div>
    )),
    Radar: React.forwardRef<any, any>((props: any, ref) => (
      <div
        data-testid="mock-radar-chart"
        ref={ref}
        className="chartjs-radar"
      >
        <div data-testid="chart-data">{JSON.stringify(props.data)}</div>
      </div>
    )),
  }
})

