/**
 * RouteGuard - 路由守衛組件
 * 版本: 1.0.0
 * 描述: 保護需要認證或特定權限的路由
 */

import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { RouteConfig } from '../types/router';
import { Button } from './ui';

interface RouteGuardProps {
  children: React.ReactNode;
  route: RouteConfig;
  fallback?: React.ComponentType;
}

/**
 * 路由守衛組件
 */
export const RouteGuard: React.FC<RouteGuardProps> = ({
  children,
  route,
  fallback: FallbackComponent
}) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkPermissions = async () => {
      setChecking(true);
      // 這裡可以添加額外的權限檢查邏輯
      setChecking(false);
    };

    checkPermissions();
  }, [route]);

  // 顯示加載中狀態
  if (isLoading || checking) {
    const Fallback = FallbackComponent || DefaultLoadingFallback;
    return <Fallback />;
  }

  // 檢查是否需要認證
  if (route.meta?.requiresAuth && !isAuthenticated) {
    // 保存當前路徑以便登錄後重定向
    const redirectPath = `/login?redirect=${encodeURIComponent(location.pathname + location.search)}`;
    return <Navigate to={redirectPath} replace />;
  }

  // 檢查角色權限
  if (route.meta?.roles && route.meta.roles.length > 0) {
    // 這裡應該檢查用戶是否有所需角色
    // 暫時跳過具體實現
  }

  // 檢查具體權限
  if (route.meta?.permissions && route.meta.permissions.length > 0) {
    // 這裡應該檢查用戶是否有所需權限
    // 暫時跳過具體實現
  }

  return <>{children}</>;
};

/**
 * 默認加載中組件
 */
const DefaultLoadingFallback: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
);

/**
 * 權限不足組件
 */
export const AccessDenied: React.FC<{
  message?: string;
  onGoBack?: () => void;
  onGoHome?: () => void;
}> = ({
  message = '您沒有權限訪問此頁面',
  onGoBack,
  onGoHome
}) => {
  const handleGoBack = () => {
    if (onGoBack) {
      onGoBack();
    } else {
      window.history.back();
    }
  };

  const handleGoHome = () => {
    if (onGoHome) {
      onGoHome();
    } else {
      window.location.href = '/';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        <div className="mb-4">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">訪問被拒絕</h1>
        <p className="text-gray-600 mb-6">{message}</p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button variant="outline" onClick={handleGoBack}>
            返回上頁
          </Button>
          <Button onClick={handleGoHome}>
            返回首頁
          </Button>
        </div>
      </div>
    </div>
  );
};

/**
 * 404 頁面未找到組件
 */
export const NotFound: React.FC<{
  onGoHome?: () => void;
}> = ({ onGoHome }) => {
  const handleGoHome = () => {
    if (onGoHome) {
      onGoHome();
    } else {
      window.location.href = '/';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        <div className="mb-4">
          <h1 className="text-6xl font-bold text-gray-300">404</h1>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">頁面未找到</h2>
        <p className="text-gray-600 mb-6">抱歉，您訪問的頁面不存在或已被移除。</p>
        <Button onClick={handleGoHome}>
          返回首頁
        </Button>
      </div>
    </div>
  );
};

export default RouteGuard;