import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'antd/dist/reset.css';
import './App.css';

// 導入我們的組件
import StrategyClassificationPage from './views/StrategyClassificationPage';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<Navigate to="/classification" replace />} />
            <Route path="/classification" element={<StrategyClassificationPage />} />
            <Route path="*" element={<Navigate to="/classification" replace />} />
          </Routes>
        </div>
      </Router>
    </ConfigProvider>
  );
}

export default App;