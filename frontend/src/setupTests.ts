// jest-dom adds custom matchers
import '@testing-library/jest-dom'

// Polyfill TextEncoder and TextDecoder for MSW and Node.js compatibility
import { TextEncoder, TextDecoder } from 'util'
global.TextEncoder = TextEncoder as any
global.TextDecoder = TextDecoder as any

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock WebSocket
global.WebSocket = class WebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  constructor(url: string) {
    this.url = url
    this.readyState = WebSocket.CONNECTING
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      this.onopen?.(new Event('open'))
    }, 100)
  }

  send(data: string | ArrayBufferLike | Blob | ArrayBufferView) {
    // Mock send
  }

  close() {
    this.readyState = WebSocket.CLOSED
    this.onclose?.(new Event('close'))
  }

  addEventListener() {}
  removeEventListener() {}
}

// Mock window.matchMedia with full event listener support
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => {
    const listeners: Array<(event: MediaQueryListEvent) => void> = []

    return {
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(), // deprecated
      removeListener: jest.fn(), // deprecated
      addEventListener: jest.fn((event: string, listener: any) => {
        if (event === 'change') {
          listeners.push(listener)
        }
      }),
      removeEventListener: jest.fn((event: string, listener: any) => {
        const index = listeners.indexOf(listener)
        if (index > -1) {
          listeners.splice(index, 1)
        }
      }),
      dispatchEvent: jest.fn(),
      // Helper method for testing
      _simulateChange: (matches: boolean) => {
        listeners.forEach(listener => {
          listener({ matches } as MediaQueryListEvent)
        })
      },
    }
  }),
})

// Mock getComputedStyle
Object.defineProperty(window, 'getComputedStyle', {
  value: () => ({
    getPropertyValue: () => '',
  }),
})

// Mock canvas for charts
HTMLCanvasElement.prototype.getContext = jest.fn().mockReturnValue({
  fillRect: jest.fn(),
  clearRect: jest.fn(),
  getImageData: jest.fn().mockReturnValue({ data: new Array(4) }),
  putImageData: jest.fn(),
  createImageData: jest.fn().mockReturnValue({ data: new Array(4) }),
  setTransform: jest.fn(),
  drawImage: jest.fn(),
  save: jest.fn(),
  fillText: jest.fn(),
  restore: jest.fn(),
  beginPath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  closePath: jest.fn(),
  stroke: jest.fn(),
  translate: jest.fn(),
  scale: jest.fn(),
  rotate: jest.fn(),
  arc: jest.fn(),
  fill: jest.fn(),
  measureText: jest.fn().mockReturnValue('0px'),
  transform: jest.fn(),
  rect: jest.fn(),
  clip: jest.fn(),
})

// Mock Plotly
jest.mock('plotly.js', () => ({
  newPlot: jest.fn(),
  react: jest.fn(),
  redraw: jest.fn(),
  purge: jest.fn(),
  restyle: jest.fn(),
  addFrames: jest.fn(),
}))

// Mock react-plotly.js for lazy loading support
jest.mock('react-plotly.js', () => {
  const React = require('react')

  const PlotComponent = class Plot extends React.Component {
    render() {
      const { layout, config, style, data } = this.props as any
      const title = typeof layout?.title === 'string'
        ? layout.title
        : layout?.title?.text || 'Plotly Chart'

      return React.createElement('div', {
        'data-testid': 'mock-plotly-chart',
        className: 'plotly-graph-div',
        style: style || { width: '100%', height: '400px' }
      }, title)
    }
  }

  // Return both default and named export to support different import styles
  return {
    __esModule: true,
    default: PlotComponent,
  }
})

// Mock Chart.js
jest.mock('chart.js', () => {
  const mockChartInstance = {
    update: jest.fn(),
    destroy: jest.fn(),
    resize: jest.fn(),
    clear: jest.fn(),
    draw: jest.fn(),
  }

  const mockChart = jest.fn(() => mockChartInstance)

  return {
    Chart: Object.assign(mockChart, {
      register: jest.fn(),
      defaults: {},
    }),
    register: jest.fn(),
    defaults: {},
  }
})

// Mock react-chartjs-2
jest.mock('react-chartjs-2', () => ({
  Bar: ({ data, options, ...props }: any) => {
    const React = require('react')
    return React.createElement('div', {
      'data-testid': 'mock-chart-bar',
      className: 'react-chartjs-2-bar',
      style: { height: props.height || 400 }
    }, 'Bar Chart')
  },
  Line: ({ data, options, ...props }: any) => {
    const React = require('react')
    return React.createElement('div', {
      'data-testid': 'mock-chart-line',
      className: 'react-chartjs-2-line',
      style: { height: props.height || 400 }
    }, 'Line Chart')
  },
  Radar: ({ data, options, ...props }: any) => {
    const React = require('react')
    return React.createElement('div', {
      'data-testid': 'mock-chart-radar',
      className: 'react-chartjs-2-radar',
      style: { height: props.height || 400 }
    }, 'Radar Chart')
  },
}))

// Mock recharts
jest.mock('recharts', () => {
  const React = require('react')

  return {
    ResponsiveContainer: ({ children, width, height }: any) =>
      React.createElement('div', {
        className: 'recharts-responsive-container',
        style: { width, height }
      }, children),
    LineChart: ({ children }: any) => React.createElement('div', { className: 'recharts-line-chart' }, children),
    BarChart: ({ children }: any) => React.createElement('div', { className: 'recharts-bar-chart' }, children),
    PieChart: ({ children }: any) => React.createElement('div', { className: 'recharts-pie-chart' }, children),
    AreaChart: ({ children }: any) => React.createElement('div', { className: 'recharts-area-chart' }, children),
    RadarChart: ({ children }: any) => React.createElement('div', { className: 'recharts-radar-chart' }, children),
    ScatterChart: ({ children }: any) => React.createElement('div', { className: 'recharts-scatter-chart' }, children),
    Line: ({ data, ...props }: any) => React.createElement('div', { className: 'recharts-line recharts-line' }),
    Bar: ({ data, ...props }: any) => React.createElement('div', { className: 'recharts-bar' }),
    Area: ({ data, ...props }: any) => React.createElement('div', { className: 'recharts-area recharts-area' }),
    Scatter: ({ data, ...props }: any) => React.createElement('div', {
      className: 'recharts-scatter recharts-scatter-symbol'
    }),
    XAxis: (props: any) => React.createElement('div', { className: 'recharts-xAxis recharts-xAxis' }),
    YAxis: (props: any) => React.createElement('div', { className: 'recharts-yAxis recharts-yAxis' }),
    ZAxis: (props: any) => React.createElement('div', { className: 'recharts-zAxis' }),
    CartesianGrid: (props: any) => React.createElement('div', { className: 'recharts-cartesian-grid' }),
    Tooltip: (props: any) => React.createElement('div', { className: 'recharts-tooltip-wrapper' }),
    Legend: (props: any) => React.createElement('div', { className: 'recharts-legend-wrapper' }),
    Cell: (props: any) => React.createElement('div', { className: 'recharts-cell recharts-scatter-symbol' }),
    ReferenceLine: (props: any) => React.createElement('div', { className: 'recharts-reference-line' }),
  }
})

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  Editor: () => null,
}))

// Mock @heroicons/react
const React = require('react')
jest.mock('@heroicons/react/24/outline', () => {
  const createIconMock = (displayName: string) => {
    const IconComponent = ({ className = '' }: { className?: string }) =>
      React.createElement('svg', {
        className,
        'data-testid': `icon-${displayName}`,
        'aria-hidden': 'true'
      })
    IconComponent.displayName = displayName
    return IconComponent
  }

  return {
    ArrowTrendingUpIcon: createIconMock('ArrowTrendingUpIcon'),
    ArrowTrendingDownIcon: createIconMock('ArrowTrendingDownIcon'),
    ShieldCheckIcon: createIconMock('ShieldCheckIcon'),
    CurrencyDollarIcon: createIconMock('CurrencyDollarIcon'),
    ChartBarIcon: createIconMock('ChartBarIcon'),
    InformationCircleIcon: createIconMock('InformationCircleIcon'),
    ChartPieIcon: createIconMock('ChartPieIcon'),
    ArrowsRightLeftIcon: createIconMock('ArrowsRightLeftIcon'),
    AcademicCapIcon: createIconMock('AcademicCapIcon'),
  }
})

// Mock file download
global.URL.createObjectURL = jest.fn(() => 'mock-url')
global.URL.revokeObjectURL = jest.fn()

// Mock fetch
global.fetch = jest.fn()

// Unified WebSocket Service Mock - 統一 WebSocket 服務 Mock
class MockWebSocketService {
  connect = jest.fn(() => Promise.resolve())
  disconnect = jest.fn(() => Promise.resolve())
  send = jest.fn()
  subscribe = jest.fn()
  unsubscribe = jest.fn()
  on = jest.fn()
  off = jest.fn()
  emit = jest.fn()
  isConnected = false
  getConnectionState = jest.fn(() => 'disconnected')
  destroy = jest.fn()
  reconnect = jest.fn()
}

// Export singleton instance
const mockWebSocketInstance = new MockWebSocketService()

// Mock all WebSocket service paths to use the same mock
jest.mock('@/services/websocketService', () => ({
  getWebSocketService: jest.fn(() => mockWebSocketInstance),
  WebSocketService: MockWebSocketService,
  default: mockWebSocketInstance,
}))

jest.mock('@/services/websocket/WebSocketService', () => ({
  getWebSocketService: jest.fn(() => mockWebSocketInstance),
  WebSocketService: jest.fn(() => mockWebSocketInstance),
  default: mockWebSocketInstance,
}))

jest.mock('@/services/socket/websocket-service', () => ({
  createWebSocketService: jest.fn(() => mockWebSocketInstance),
  default: mockWebSocketInstance,
}))

jest.mock('@/services/websocketManager', () => ({
  getWebSocketService: jest.fn(() => mockWebSocketInstance),
  default: mockWebSocketInstance,
}))

jest.mock('@/services/websocketService', () => ({
  getWebSocketService: jest.fn(() => mockWebSocketInstance),
  default: mockWebSocketInstance,
}))

// Mock console methods in tests
const originalError = console.error
beforeAll(() => {
  console.error = jest.fn()
})

afterAll(() => {
  console.error = originalError
})

// Mock useTheme hook for theme components
jest.mock('@/styles/themes', () => ({
  ...jest.requireActual('@/styles/themes'),
  useTheme: () => ({
    theme: 'light',
    themeConfig: { name: 'light', colors: { background: {}, text: {}, border: {}, icon: {} }, components: {}, status: {}, chart: {} },
    setTheme: jest.fn(),
    toggleTheme: jest.fn(),
  }),
}))