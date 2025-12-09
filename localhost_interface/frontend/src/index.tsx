/**
 * 量化交易系統應用入口文件
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// 獲取根DOM節點
const container = document.getElementById('root');
if (!container) {
  throw new Error('找不到根DOM節點');
}

// 創建React根節點並渲染應用
const root = ReactDOM.createRoot(container);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);