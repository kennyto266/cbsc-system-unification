/**
 * Test Utilities
 * 浬試工具函數
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { store } from '@/store';

// 创建完整的测试 Wrapper
interface AllTheProvidersProps {
  children: React.ReactNode;
}

export const AllTheProviders: React.FC<AllTheProvidersProps> = ({ children }) => {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </BrowserRouter>
    </Provider>
  );
};

// 自定义 render 函数
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  wrapper?: React.ComponentType<any>;
}

export function renderWithProviders(
  ui: ReactElement,
  { ...renderOptions }: CustomRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <AllTheProviders>{children}</AllTheProviders>;
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  };
}

// 仅 Redux Provider
export const withRedux = (component: ReactElement) => {
  return <Provider store={store}>{component}</Provider>;
};

// 仅 Theme Provider
export const withTheme = (component: ReactElement) => {
  return <ThemeProvider>{component}</ThemeProvider>;
};

// Redux + Theme Provider
export const withReduxAndTheme = (component: ReactElement) => {
  return (
    <Provider store={store}>
      <ThemeProvider>{component}</ThemeProvider>
    </Provider>
  );
};

// 重新导出所有 RTL 工具
export * from '@testing-library/react';
