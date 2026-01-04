// CBSC Trading System - Unified Application Entry Point
// This file initializes the React app with providers and router

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { Provider } from 'react-redux';
import { RouterProvider } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';
import zhTW from 'antd/locale/zh_TW';

import { store } from '@/store';
import { router } from './router';
import '@/styles/globals.css';

// Initialize app
const container = document.getElementById('root');
if (!container) {
  throw new Error('Root element not found');
}

const root = createRoot(container);

root.render(
  <StrictMode>
    <Provider store={store}>
      <ConfigProvider
        locale={zhTW}
        theme={{
          algorithm: theme.defaultAlgorithm,
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
            fontSize: 14,
          },
          components: {
            Layout: {
              headerBg: '#001529',
              siderBg: '#001529',
            },
          },
        }}
      >
        <RouterProvider router={router} />
      </ConfigProvider>
    </Provider>
  </StrictMode>
);

// Enable hot module replacement in development
if (import.meta.env.DEV && typeof module !== 'undefined' && module.hot) {
  module.hot.accept();
}
