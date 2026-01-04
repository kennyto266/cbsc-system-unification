// CBSC Trading System - Page Loading Component
// Loading spinner for lazy-loaded pages

import { Spin } from 'antd';

/**
 * Full-page loading spinner
 */
export const PageLoading: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        width: '100vw',
      }}
    >
      <Spin size="large" tip="載入中..." />
    </div>
  );
};
