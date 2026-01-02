// jest-dom adds custom matchers
import '@testing-library/jest-dom'

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

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
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

// Mock react-plotly.js
jest.mock('react-plotly.js', () => {
  const React = require('react')
  return {
    default: class Plot extends React.Component {
      render() {
        const { layout, config, style } = this.props as any
        return React.createElement('div', {
          'data-testid': 'plotly-chart',
          className: 'plotly-graph-div',
          style: style || { width: '100%', height: '400px' }
        }, layout?.title || 'Plotly Chart')
      }
    }
  }
})

// Mock Chart.js
jest.mock('chart.js', () => ({
  Chart: jest.fn(() => ({
    update: jest.fn(),
    destroy: jest.fn(),
    resize: jest.fn(),
  })),
  register: jest.fn(),
  defaults: {},
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

// Mock file download
global.URL.createObjectURL = jest.fn(() => 'mock-url')
global.URL.revokeObjectURL = jest.fn()

// Mock fetch
global.fetch = jest.fn()

// Mock console methods in tests
const originalError = console.error
beforeAll(() => {
  console.error = jest.fn()
})

afterAll(() => {
  console.error = originalError
})