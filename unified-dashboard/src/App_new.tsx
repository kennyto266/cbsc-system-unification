import React from 'react'
import { ConfigProvider, App as AntdApp } from 'antd'
import zhTW from 'antd/locale/zh_TW'
import { QueryClient, QueryClientProvider } from 'react-query'
import { ReactQueryDevtools } from 'react-query/devtools'
import { ThemeProvider } from './contexts/ThemeContext'
import AppRouter from './router'
import 'antd/dist/reset.css'
import './index.css'

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
})

// Ant Design theme configuration
const antdTheme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 8,
    wireframe: false,
  },
  components: {
    Layout: {
      siderBg: 'transparent',
      triggerBg: 'transparent',
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: 'rgba(24, 144, 255, 0.1)',
      itemHoverBg: 'rgba(24, 144, 255, 0.05)',
    },
  },
}

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={zhTW}
        theme={antdTheme}
      >
        <ThemeProvider>
          <AntdApp>
            <div className="app">
              <AppRouter />
            </div>

            {/* React Query Devtools - Only in development */}
            {process.env.NODE_ENV === 'development' && (
              <ReactQueryDevtools initialIsOpen={false} />
            )}
          </AntdApp>
        </ThemeProvider>
      </ConfigProvider>
    </QueryClientProvider>
  )
}

export default App