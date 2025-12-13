import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { ToastContainer } from 'react-toastify';
import 'antd/dist/reset.css';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';

// 导入布局组件
import MainLayout from './pages/MainLayout';

// 导入页面组件
import StrategyDashboard from './components/Strategy/StrategyDashboard';
import UserList from './components/UserManagement/UserList';
import UserDetail from './components/UserManagement/UserDetail';

// 临时登录页面（后续需要实现）
const LoginPage = () => (
  <div style={{
    height: '100vh',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    background: '#f0f2f5'
  }}>
    <div style={{
      padding: 40,
      background: '#fff',
      borderRadius: 8,
      boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
    }}>
      <h2>CBSC量化交易系统</h2>
      <p>请输入用户名和密码登录</p>
      {/* TODO: 实现登录表单 */}
      <button onClick={() => window.location.href = '/dashboard'}>进入系统</button>
    </div>
  </div>
);

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
            {/* 登录页面 */}
            <Route path="/login" element={<LoginPage />} />

            {/* 主应用布局 */}
            <Route path="/" element={<MainLayout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />

              {/* 策略相关路由 */}
              <Route path="dashboard" element={<StrategyDashboard />} />
              <Route path="strategies/list" element={<StrategyDashboard />} />

              {/* 用户管理路由 */}
              <Route path="users" element={<UserList />} />
              <Route path="users/list" element={<UserList />} />
              <Route path="users/:userId" element={<UserDetail />} />

              {/* 其他页面（待实现） */}
              <Route path="strategies/create" element={<div>创建策略页面 - 待实现</div>} />
              <Route path="strategies/templates" element={<div>策略模板页面 - 待实现</div>} />
              <Route path="users/create" element={<div>新建用户页面 - 待实现</div>} />
              <Route path="users/roles" element={<div>角色权限页面 - 待实现</div>} />
              <Route path="monitoring" element={<div>系统监控页面 - 待实现</div>} />
              <Route path="settings" element={<div>系统设置页面 - 待实现</div>} />
            </Route>

            {/* 旧路由重定向 */}
            <Route path="/classification" element={<Navigate to="/dashboard" replace />} />

            {/* 404重定向 */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </Router>
    </ConfigProvider>
  );
}

export default App;