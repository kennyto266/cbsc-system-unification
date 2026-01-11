/**
 * Next.js App Component
 * CBSC量化交易系統的全局應用組件
 */

import React from 'react'
import type { AppProps } from 'next/app'
import { appWithTranslation } from 'next-i18next'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Provider } from 'react-redux'
import { ThemeProvider } from '@/themes/ThemeProvider'
import { Toaster } from '@/components/ui'
import { store } from '@/store'
import '@/styles/globals.css'

// 創建React Query客戶端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5分鐘
      retry: 3,
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
})

// 組件屬性類型
interface MyAppProps extends AppProps {
  Component: AppProps['Component'] & {
    auth?: boolean
    layout?: React.ComponentType
  }
  pageProps: {
    session?: any
    [key: string]: any
  }
}

// 主應用組件
function MyApp({ Component, pageProps: { session, ...pageProps } }: MyAppProps) {
  // 獲取組件的佈局
  const getLayout = Component.getLayout || ((page: React.ReactNode) => page)

  return (
    <React.StrictMode>
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <div className="min-h-screen bg-background text-foreground">
              {getLayout(<Component {...pageProps} />)}
            </div>
            <Toaster />
          </ThemeProvider>
          {process.env.NODE_ENV === 'development' && (
            <ReactQueryDevtools initialIsOpen={false} />
          )}
        </QueryClientProvider>
      </Provider>
    </React.StrictMode>
  )
}

// 應用包裝器，用於i18n
export default appWithTranslation(MyApp)

// 全局應用配置
MyApp.getInitialProps = async ({ Component, ctx }: any) => {
  let pageProps = {}

  // 如果組件有getInitialProps，調用它
  if (Component.getInitialProps) {
    pageProps = await Component.getInitialProps(ctx)
  }

  // 添加全局頁面屬性
  pageProps = {
    ...pageProps,
    // 獲取用戶代理
    userAgent: ctx.req?.headers['user-agent'] || null,
    // 獲取客戶端IP
    clientIP: ctx.req?.connection?.remoteAddress || ctx.req?.socket?.remoteAddress || null,
    // 獲取當前語言
    locale: ctx.locale || 'zh-HK',
  }

  return { pageProps }
}

// 錯誤邊界組件
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

    // 這裡可以添加錯誤日誌服務
    // logErrorToService(error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6 text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              系統錯誤
            </h1>
            <p className="text-gray-600 mb-6">
              抱歉，系統遇到了一個錯誤。請刷新頁面或聯繫技術支持。
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              刷新頁面
            </button>
            {process.env.NODE_ENV === 'development' && (
              <details className="mt-6 text-left">
                <summary className="cursor-pointer text-sm text-gray-500">
                  錯誤詳情 (開發模式)
                </summary>
                <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">
                  {this.state.error?.stack}
                </pre>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}