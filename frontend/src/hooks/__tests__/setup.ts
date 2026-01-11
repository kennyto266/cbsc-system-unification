/**
 * Test setup for hooks
 *
 * This file contains common setup for hook tests including
 * global mocks and test utilities.
 */

import { vi } from 'vitest';

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation((callback) => {
  return {
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  };
});

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation((callback) => {
  return {
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  };
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock scrollTo
window.scrollTo = vi.fn();

// Mock getComputedStyle
window.getComputedStyle = vi.fn(() => ({
  getPropertyValue: vi.fn(() => ''),
}));

// Mock URL.createObjectURL and revokeObjectURL
Object.defineProperty(URL, 'createObjectURL', {
  writable: true,
  value: vi.fn(() => 'mocked-url'),
});

Object.defineProperty(URL, 'revokeObjectURL', {
  writable: true,
  value: vi.fn(),
});

// Mock HTMLElement methods
HTMLElement.prototype.scrollIntoView = vi.fn();
HTMLElement.prototype.click = vi.fn();

// Mock Canvas API
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  fillRect: vi.fn(),
  clearRect: vi.fn(),
  getImageData: vi.fn(() => ({ data: new Array(4) })),
  putImageData: vi.fn(),
  createImageData: vi.fn(() => ({ data: new Array(4) })),
  setTransform: vi.fn(),
  drawImage: vi.fn(),
  save: vi.fn(),
  fillText: vi.fn(),
  restore: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  closePath: vi.fn(),
  stroke: vi.fn(),
  translate: vi.fn(),
  scale: vi.fn(),
  rotate: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  measureText: vi.fn(() => ({ width: 0 })),
  transform: vi.fn(),
  rect: vi.fn(),
  clip: vi.fn(),
  fillStyle: '',
  font: '',
  globalAlpha: 1,
  lineDash: [],
  lineDashOffset: 0,
  lineJoin: '',
  lineCap: '',
  lineWidth: 1,
  miterLimit: 1,
  shadowBlur: 0,
  shadowColor: '',
  shadowOffsetX: 0,
  shadowOffsetY: 0,
  strokeStyle: '',
  textAlign: '',
  textBaseline: '',
}));

HTMLCanvasElement.prototype.toDataURL = vi.fn(() => 'data:image/png;base64,mock');

HTMLCanvasElement.prototype.toBlob = vi.fn((callback) => {
  callback(new Blob(['mock-image'], { type: 'image/png' }));
});

// Mock WebSocket
global.WebSocket = vi.fn().mockImplementation(() => ({
  close: vi.fn(),
  send: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  readyState: 1,
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
}));

// Mock fetch
global.fetch = vi.fn();

// Mock Request and Response
global.Request = vi.fn();
global.Response = vi.fn();

// Mock btoa and atob
global.btoa = vi.fn((str) => Buffer.from(str).toString('base64'));
global.atob = vi.fn((str) => Buffer.from(str, 'base64').toString());

// Mock Image
global.Image = vi.fn().mockImplementation(() => ({
  onload: null,
  onerror: null,
  src: '',
  width: 0,
  height: 0,
  complete: true,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
})) as any;

// Mock performance APIs
Object.defineProperty(window, 'requestAnimationFrame', {
  writable: true,
  value: vi.fn((cb) => setTimeout(cb, 0)),
});

Object.defineProperty(window, 'cancelAnimationFrame', {
  writable: true,
  value: vi.fn((id) => clearTimeout(id)),
});

Object.defineProperty(window, 'performance', {
  writable: true,
  value: {
    now: vi.fn(() => Date.now()),
    mark: vi.fn(),
    measure: vi.fn(),
    getEntriesByName: vi.fn(() => []),
    getEntriesByType: vi.fn(() => []),
  },
});

// Mock console methods for tests
const originalConsole = {
  ...console,
};

beforeEach(() => {
  vi.clearAllMocks();

  // Restore console methods
  Object.assign(console, originalConsole);
});

// Common test utilities
export const createMockRef = <T = any>(initialValue: T | null = null) => ({
  current: initialValue,
});

export const createMockElement = (tagName: string, properties: Record<string, any> = {}) => {
  const element = document.createElement(tagName);
  Object.entries(properties).forEach(([key, value]) => {
    (element as any)[key] = value;
  });
  return element;
};

export const createMockCanvas = (width = 800, height = 600) => {
  const canvas = document.createElement('canvas');
  Object.defineProperty(canvas, 'width', { value: width });
  Object.defineProperty(canvas, 'height', { value: height });
  return canvas;
};

export const createMockSVG = (width = 800, height = 600) => {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', width.toString());
  svg.setAttribute('height', height.toString());
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  return svg;
};

export const waitFor = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0));

// Export common mock data
export const mockChartData = [
  { timestamp: 1, value: 100, label: 'Test1' },
  { timestamp: 2, value: 200, label: 'Test2' },
  { timestamp: 3, value: 150, label: 'Test3' },
];

export const mockWebSocketMessage = {
  id: 'test-id',
  type: 'DATA',
  channel: 'STRATEGY_UPDATES',
  data: { value: 123, timestamp: Date.now() },
  timestamp: Date.now(),
};

export const mockToastData = {
  type: 'success' as const,
  message: 'Test message',
  duration: 3000,
};