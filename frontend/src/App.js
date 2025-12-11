import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { ToastContainer } from 'react-toastify';
import 'antd/dist/reset.css';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

// 導入我們的組件
import StrategyClassificationPage from './views/StrategyClassificationPage';
import StrategyDashboard from './components/StrategyDashboard/StrategyDashboard';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <div className="App">
          <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="light"
          />
          <Routes>
            <Route path="/" element={<Navigate to="/classification" replace />} />
            <Route path="/classification" element={<StrategyClassificationPage />} />
            <Route path="/dashboard" element={<StrategyDashboard />} />
            <Route path="*" element={<Navigate to="/classification" replace />} />
          </Routes>
        </div>
      </Router>
    </ConfigProvider>
  );
}

export default App;