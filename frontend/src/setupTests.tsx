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

// Mock ResizeObserver - minimal implementation to avoid memory leaks
class ResizeObserverMock {
  callback: any;
  observedElements: Set<any>;

  constructor(callback: any) {
    this.callback = callback;
    this.observedElements = new Set();
  }

  observe(element: any) {
    // Store element for cleanup
    this.observedElements.add(element);

    // Don't call callback automatically to prevent infinite loops
    // Tests can trigger manually if needed
  }

  disconnect() {
    // Clear all references to allow garbage collection
    this.observedElements.clear();
    this.callback = null;
  }

  unobserve() {
    // No-op for mock
  }
}

global.ResizeObserver = ResizeObserverMock as any

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

// Polyfill Response for MSW (Mock Service Worker)
if (typeof Response === 'undefined') {
  global.Response = class Response {
    constructor(body?: any, init?: ResponseInit) {
      this.body = body;
      this.status = init?.status || 200;
      this.statusText = init?.statusText || 'OK';
      this.headers = new Headers(init?.headers);
      this.ok = this.status >= 200 && this.status < 300;
      this.redirected = !!init?.redirected;
      this.type = init?.type || 'basic';
      this.url = init?.url || '';
    }
    body: any;
    status: number;
    statusText: string;
    headers: Headers;
    ok: boolean;
    redirected: boolean;
    type: ResponseType;
    url: string;
    static redirect(url: string, status?: number): Response {
      return new Response(null, { status: status || 302, headers: { Location: url } });
    }
    static error(): Response {
      return new Response(null, { status: 0, statusText: 'error' });
    }
    static json(data: any): Response {
      return new Response(JSON.stringify(data), { headers: { 'Content-Type': 'application/json' } });
    }
    clone(): Response {
      return new Response(this.body, {
        status: this.status,
        statusText: this.statusText,
        headers: this.headers,
      });
    }
    async json(): Promise<any> {
      return JSON.parse(this.body);
    }
    async text(): Promise<string> {
      return this.body?.toString() || '';
    }
    async blob(): Promise<Blob> {
      return new Blob([this.body]);
    }
    async arrayBuffer(): Promise<ArrayBuffer> {
      return new TextEncoder().encode(this.body).buffer;
    }
  };
}

// Polyfill Headers if needed
if (typeof Headers === 'undefined') {
  global.Headers = class Headers {
    constructor(init?: HeadersInit) {
      this._headers = new Map<string, string>();
      if (init) {
        if (init instanceof Headers) {
          init.forEach((value, key) => this._headers.set(key, value));
        } else if (Array.isArray(init)) {
          init.forEach(([key, value]) => this._headers.set(key, value));
        } else {
          Object.entries(init).forEach(([key, value]) => this._headers.set(key, value));
        }
      }
    }
    private _headers: Map<string, string>;
    append(name: string, value: string): void {
      this._headers.set(name, value);
    }
    delete(name: string): void {
      this._headers.delete(name);
    }
    get(name: string): string | null {
      return this._headers.get(name) || null;
    }
    has(name: string): boolean {
      return this._headers.has(name);
    }
    set(name: string, value: string): void {
      this._headers.set(name, value);
    }
    forEach(callback: (value: string, key: string) => void): void {
      this._headers.forEach((value, key) => callback(value, key));
    }
    entries(): IterableIterator<[string, string]> {
      return this._headers.entries();
    }
  };
}

// Polyfill BroadcastChannel for MSW
if (typeof BroadcastChannel === 'undefined') {
  global.BroadcastChannel = class BroadcastChannel {
    constructor(name: string) {
      this.name = name;
      this.listeners = new Set<(message: any) => void>();
    }
    name: string;
    private listeners: Set<(message: any) => void>;

    postMessage(message: any): void {
      // In test environment, immediately deliver to all listeners
      this.listeners.forEach(listener => {
        try {
          listener(message);
        } catch (err) {
          console.error('BroadcastChannel listener error:', err);
        }
      });
    }

    addEventListener(type: string, listener: (message: any) => void): void {
      if (type === 'message') {
        this.listeners.add(listener);
      }
    }

    removeEventListener(type: string, listener: (message: any) => void): void {
      if (type === 'message') {
        this.listeners.delete(listener);
      }
    }

    close(): void {
      this.listeners.clear();
    }

    onmessage: ((event: MessageEvent) => void) | null = null;
    onmessageerror: ((event: MessageEvent) => void) | null = null;
  };
}

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

// Note: useWebSocketEnhanced mock removed - tests have their own mock in the test file// Global cleanup after each test to prevent memory leaks
afterEach(() => {
  // Clear all mocks to release references
  jest.clearAllMocks()
  // Clear all timers
  jest.clearAllTimers()
  // Force garbage collection if available
  if (global.gc) {
    global.gc()
  }
})
