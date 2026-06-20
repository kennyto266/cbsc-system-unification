import React from 'react'
import ReactDOM from 'react-dom/client'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { QueryClient, QueryClientProvider } from 'react-query'
import { ReactQueryDevtools } from 'react-query/devtools'
import { HelmetProvider } from 'react-helmet-async'
import { Toaster } from 'react-hot-toast'

import App from './App'
import { store } from './store'
import websocketService from './services/websocket'
import './styles/globals.css'

// Clear stale Redux Persist data on version mismatch (prevents crash from
// old localStorage state that doesn't match current store structure)
const PERSIST_VERSION = 'v2-2026-06-19'
if (localStorage.getItem('cbsc_persist_version') !== PERSIST_VERSION) {
  Object.keys(localStorage).forEach(key => {
    if (key.startsWith('persist:')) localStorage.removeItem(key)
  })
  localStorage.setItem('cbsc_persist_version', PERSIST_VERSION)
}

// Import dayjs locale
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

// Configure dayjs
dayjs.locale('zh-cn')

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false
        }
        // Retry up to 3 times for other errors
        return failureCount < 3
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: false,
    },
  },
})

// Initialize WebSocket service
const initializeWebSocket = async () => {
  const token = localStorage.getItem('cbsc_token')
  if (token) {
    try {
      await websocketService.connect(token)
      websocketService.setStore(store)

      // Subscribe to default channels
      websocketService.subscribe('performance_updates')
      websocketService.subscribe('signals_updates')
      websocketService.subscribe('market_data')
      websocketService.subscribe('system_status')
      websocketService.subscribe('strategy_execution')

      console.log('WebSocket initialized successfully')
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error)
    }
  }
}

// Initialize app
const initializeApp = async () => {
  try {
    // Check authentication status
    const token = localStorage.getItem('cbsc_token')
    if (token) {
      // Validate token and get user info
      try {
        // This will be handled by the auth slice in the app
        console.log('Validating existing token...')
      } catch (error) {
        console.error('Token validation failed:', error)
        localStorage.removeItem('cbsc_token')
      }
    }

    // Initialize WebSocket if authenticated
    await initializeWebSocket()

  } catch (error) {
    console.error('App initialization failed:', error)
  }
}

// Configure Ant Design theme — CBSC Quant Terminal Dark Mode
import { theme as antdThemeLib } from 'antd'
const antdTheme = {
  algorithm: antdThemeLib.darkAlgorithm,
  token: {
    colorPrimary: '#00d4ff',
    colorSuccess: '#00ff88',
    colorWarning: '#ffa500',
    colorError: '#ff3366',
    colorInfo: '#00d4ff',
    colorBgBase: '#0a0e1a',
    colorBgContainer: '#111827',
    colorBgElevated: '#1a2332',
    colorText: '#e2e8f0',
    colorTextSecondary: '#94a3b8',
    colorBorder: 'rgba(255,255,255,0.1)',
    colorBorderSecondary: 'rgba(255,255,255,0.06)',
    borderRadius: 8,
    fontFamily: "'Noto Sans TC', 'PingFang SC', 'Microsoft YaHei', sans-serif",
    wireframe: false,
  },
  components: {
    Layout: {
      bodyBg: '#0a0e1a',
      headerBg: '#111827',
      siderBg: '#111827',
    },
    Menu: {
      darkItemBg: 'transparent',
      darkSubMenuItemBg: '#0d1117',
      darkItemSelectedBg: 'rgba(0,212,255,0.15)',
      darkItemColor: '#94a3b8',
      darkItemSelectedColor: '#00d4ff',
    },
    Button: { borderRadius: 6 },
    Card: {
      borderRadius: 12,
      colorBgContainer: '#111827',
      colorBorderSecondary: 'rgba(255,255,255,0.06)',
    },
    Table: {
      borderRadius: 8,
      colorBgContainer: 'transparent',
      headerBg: '#1a2332',
      headerColor: '#94a3b8',
      rowHoverBg: '#243044',
      borderColor: 'rgba(255,255,255,0.06)',
    },
  },
}

// Error boundary component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          padding: '20px',
          textAlign: 'center',
        }}>
          <h1 style={{ color: '#f5222d', marginBottom: '16px' }}>
            应用程序出现错误
          </h1>
          <p style={{ color: '#666', marginBottom: '24px' }}>
            抱歉，应用程序遇到了意外错误。请刷新页面重试。
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '8px 16px',
              backgroundColor: '#1890ff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
          >
            刷新页面
          </button>
          {process.env.NODE_ENV === 'development' && (
            <details style={{ marginTop: '24px', textAlign: 'left' }}>
              <summary>错误详情</summary>
              <pre style={{
                background: '#f5f5f5',
                padding: '16px',
                borderRadius: '4px',
                overflow: 'auto',
                fontSize: '12px',
              }}>
                {this.state.error?.stack}
              </pre>
            </details>
          )}
        </div>
      )
    }

    return this.props.children
  }
}

// Root component
const Root: React.FC = () => {
  return (
    <ErrorBoundary>
      <React.StrictMode>
        <HelmetProvider>
          <Provider store={store}>
            <QueryClientProvider client={queryClient}>
              <BrowserRouter>
                <ConfigProvider
                  locale={zhCN}
                  theme={antdTheme}
                >
                  <App />
                  <Toaster
                    position="top-right"
                    toastOptions={{
                      duration: 4000,
                      style: {
                        background: '#363636',
                        color: '#fff',
                      },
                      success: {
                        duration: 3000,
                        iconTheme: {
                          primary: '#52c41a',
                          secondary: '#fff',
                        },
                      },
                      error: {
                        duration: 5000,
                        iconTheme: {
                          primary: '#f5222d',
                          secondary: '#fff',
                        },
                      },
                    }}
                  />
                </ConfigProvider>
              </BrowserRouter>
              {process.env.NODE_ENV === 'development' && (
                <ReactQueryDevtools initialIsOpen={false} />
              )}
            </QueryClientProvider>
          </Provider>
        </HelmetProvider>
      </React.StrictMode>
    </ErrorBoundary>
  )
}

// Get root element
const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Root element not found')
}

// Create root and render
const root = ReactDOM.createRoot(rootElement)

// Initialize app and render
initializeApp().then(() => {
  root.render(<Root />)
}).catch((error) => {
  console.error('Failed to initialize app:', error)
  root.render(
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      padding: '20px',
      textAlign: 'center',
    }}>
      <div>
        <h1 style={{ color: '#f5222d', marginBottom: '16px' }}>
          应用程序初始化失败
        </h1>
        <p style={{ color: '#666', marginBottom: '24px' }}>
          应用程序初始化过程中出现错误，请检查网络连接或稍后重试。
        </p>
        <button
          onClick={() => window.location.reload()}
          style={{
            padding: '8px 16px',
            backgroundColor: '#1890ff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          重试
        </button>
        {process.env.NODE_ENV === 'development' && (
          <details style={{ marginTop: '24px', textAlign: 'left' }}>
            <summary>错误详情</summary>
            <pre style={{
              background: '#f5f5f5',
              padding: '16px',
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '12px',
            }}>
              {error?.message}
              {error?.stack}
            </pre>
          </details>
        )}
      </div>
    </div>
  )
})

// Performance monitoring
if (process.env.NODE_ENV === 'production') {
  // Report web vitals
  const reportWebVitals = (onPerfEntry?: (metric: any) => void) => {
    if (onPerfEntry && onPerfEntry instanceof Function) {
      import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
        getCLS(onPerfEntry)
        getFID(onPerfEntry)
        getFCP(onPerfEntry)
        getLCP(onPerfEntry)
        getTTFB(onPerfEntry)
      })
    }
  }

  reportWebVitals((metric) => {
    // Send metrics to analytics service
    console.log('Web Vital:', metric)
  })
}

// Service Worker disabled (personal use, PWA removed)


export default Root