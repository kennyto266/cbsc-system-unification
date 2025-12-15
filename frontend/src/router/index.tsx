/**
 * Router Configuration - 路由配置
 * 版本: 1.0.0
 * 描述: 定義應用程序的所有路由配置
 */

import React, { Suspense, lazy } from 'react';
import { createBrowserRouter, RouterProvider, Outlet } from 'react-router-dom';
import { RouteConfig } from '../types/router';
import { RouteGuard } from '../components/RouteGuard';
import { AuthProvider } from '../hooks/useAuth';

// 懶加載組件
const Dashboard = lazy(() => import('../pages/Dashboard'));
const Login = lazy(() => import('../pages/Login'));
const Register = lazy(() => import('../pages/Register'));
const UserProfile = lazy(() => import('../pages/UserProfile'));
const StrategyManagement = lazy(() => import('../pages/StrategyManagement'));
const StrategyEditor = lazy(() => import('../pages/StrategyEditor'));
const BacktestAnalysis = lazy(() => import('../pages/BacktestAnalysis'));
const RiskManagement = lazy(() => import('../pages/RiskManagement'));
const Reports = lazy(() => import('../pages/Reports'));
const Settings = lazy(() => import('../pages/Settings'));
const NotFound = lazy(() => import('../pages/NotFound'));
const UIComponents = lazy(() => import('../pages/components/UIComponents'));

// 佈局組件
const MainLayout = lazy(() => import('../components/Layout/MainLayout'));
const AuthLayout = lazy(() => import('../components/Layout/AuthLayout'));

/**
 * 加載中組件
 */
const LoadingFallback = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
  </div>
);

/**
 * 路由配置數組
 */
export const routes: RouteConfig[] = [
  {
    path: '/',
    element: <MainLayout />,
    level: 'protected',
    meta: {
      requiresAuth: true,
      keepAlive: true,
    },
    children: [
      {
        path: '',
        element: <Dashboard />,
        meta: {
          title: '儀表板',
          description: 'CBSC 策略管理儀表板',
          requiresAuth: true,
          keepAlive: true,
        },
      },
      {
        path: 'strategies',
        element: <StrategyManagement />,
        meta: {
          title: '策略管理',
          description: '管理和配置交易策略',
          requiresAuth: true,
          permissions: ['strategy.read'],
        },
      },
      {
        path: 'strategies/new',
        element: <StrategyEditor />,
        meta: {
          title: '新建策略',
          description: '創建新的交易策略',
          requiresAuth: true,
          permissions: ['strategy.create'],
          hideInMenu: true,
        },
      },
      {
        path: 'strategies/:id/edit',
        element: <StrategyEditor />,
        meta: {
          title: '編輯策略',
          description: '編輯現有交易策略',
          requiresAuth: true,
          permissions: ['strategy.update'],
          hideInMenu: true,
        },
      },
      {
        path: 'backtest',
        element: <BacktestAnalysis />,
        meta: {
          title: '回測分析',
          description: '策略回測結果分析',
          requiresAuth: true,
          permissions: ['backtest.read'],
        },
      },
      {
        path: 'risk',
        element: <RiskManagement />,
        meta: {
          title: '風險管理',
          description: '監控和管理系統風險',
          requiresAuth: true,
          permissions: ['risk.read'],
        },
      },
      {
        path: 'reports',
        element: <Reports />,
        meta: {
          title: '報告中心',
          description: '查看系統報告和分析',
          requiresAuth: true,
          permissions: ['report.read'],
        },
      },
      {
        path: 'profile',
        element: <UserProfile />,
        meta: {
          title: '個人資料',
          description: '管理個人賬戶信息',
          requiresAuth: true,
          hideInMenu: true,
        },
      },
      {
        path: 'settings',
        element: <Settings />,
        meta: {
          title: '系統設置',
          description: '配置系統參數和偏好',
          requiresAuth: true,
          permissions: ['settings.update'],
        },
      },
      // 開發/測試路由
      {
        path: 'components',
        element: <UIComponents />,
        meta: {
          title: 'UI 組件',
          description: 'UI 組件展示和測試',
          requiresAuth: true,
          hideInMenu: process.env.NODE_ENV === 'production',
        },
      },
    ],
  },
  {
    path: '/auth',
    element: <AuthLayout />,
    level: 'public',
    children: [
      {
        path: 'login',
        element: <Login />,
        meta: {
          title: '登錄',
          description: '用戶登錄頁面',
          requiresAuth: false,
        },
      },
      {
        path: 'register',
        element: <Register />,
        meta: {
          title: '註冊',
          description: '新用戶註冊頁面',
          requiresAuth: false,
        },
      },
    ],
  },
  // 重定向路由
  {
    path: '/login',
    element: <Navigate to="/auth/login" replace />,
    meta: {
      requiresAuth: false,
    },
  },
  {
    path: '/register',
    element: <Navigate to="/auth/register" replace />,
    meta: {
      requiresAuth: false,
    },
  },
  // 404 路由
  {
    path: '*',
    element: <NotFound />,
    meta: {
      title: '頁面未找到',
      requiresAuth: false,
    },
  },
];

/**
 * 將路由配置轉換為 React Router 對象
 */
const createRouteObject = (route: RouteConfig): any => {
  const routeObject: any = {
    path: route.path,
    element: route.element || <Outlet />,
  };

  // 添加錯誤邊界
  if (route.errorBoundary) {
    routeObject.errorElement = <route.errorBoundary error={new Error('Route error')} />;
  }

  // 添加子路由
  if (route.children && route.children.length > 0) {
    routeObject.children = route.children.map(createRouteObject);
  }

  return routeObject;
};

/**
 * 帶守衛的路由包裝器
 */
const RouteWithGuard: React.FC<{ route: RouteConfig; children: React.ReactNode }> = ({
  route,
  children
}) => (
  <RouteGuard route={route}>
    <Suspense fallback={<LoadingFallback />}>
      {children}
    </Suspense>
  </RouteGuard>
);

/**
 * 創建帶權限控制的路由
 */
const createProtectedRoute = (route: RouteConfig): any => {
  const element = route.children ? (
    <RouteWithGuard route={route}>
      <Outlet />
    </RouteWithGuard>
  ) : (
    <RouteWithGuard route={route}>
      {route.element}
    </RouteWithGuard>
  );

  const routeObject: any = {
    path: route.path,
    element,
  };

  // 處理子路由
  if (route.children && route.children.length > 0) {
    routeObject.children = route.children.map(child => ({
      ...createProtectedRoute(child),
      index: child.path === '',
    }));
  }

  return routeObject;
};

/**
 * 創建最終的路由配置
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <AuthProvider>
        <Outlet />
      </AuthProvider>
    ),
    children: [
      // 公共路由
      {
        path: 'auth',
        element: <AuthLayout />,
        children: [
          {
            index: true,
            element: <Navigate to="/auth/login" replace />,
          },
          {
            path: 'login',
            element: (
              <Suspense fallback={<LoadingFallback />}>
                <Login />
              </Suspense>
            ),
          },
          {
            path: 'register',
            element: (
              <Suspense fallback={<LoadingFallback />}>
                <Register />
              </Suspense>
            ),
          },
        ],
      },
      // 受保護的路由
      {
        path: '/',
        element: <MainLayout />,
        children: [
          {
            index: true,
            element: (
              <RouteGuard route={routes[0]}>
                <Suspense fallback={<LoadingFallback />}>
                  <Dashboard />
                </Suspense>
              </RouteGuard>
            ),
          },
          {
            path: 'strategies',
            element: (
              <RouteGuard route={routes[0]}>
                <Suspense fallback={<LoadingFallback />}>
                  <StrategyManagement />
                </Suspense>
              </RouteGuard>
            ),
          },
          {
            path: 'strategies/new',
            element: (
              <RouteGuard route={routes[0]}>
                <Suspense fallback={<LoadingFallback />}>
                  <StrategyEditor />
                </Suspense>
              </RouteGuard>
            ),
          },
          {
            path: 'strategies/:id/edit',
            element: (
              <RouteGuard route={routes[0]}>
                <Suspense fallback={<LoadingFallback />}>
                  <StrategyEditor />
                </Suspense>
              </RouteGuard>
            ),
          },
          {
            path: 'backtest',
            element: (
              <RouteGuard route={routes[0]}>
                <Suspense fallback={<LoadingFallback />}>
                  <BacktestAnalysis />
                </Suspense>
              </RouteGuard>
            ),
          },
          {
            path: 'risk',
            element: (
              <RouteGuard route={routes[0]}>
                <Suspense fallback={<LoadingFallback />}>
                  <RiskManagement />
                </Suspense>
              </RouteGuard>
            ),
          },
          {
            path: 'reports',
            element: (
              <RouteGuard route={routes[0]}>
                <Suspense fallback={<LoadingFallback />}>
                  <Reports />
                </Suspense>
              </RouteGuard>
            ),
          },
          {
            path: 'profile',
            element: (
              <RouteGuard route={routes[0]}>
                <Suspense fallback={<LoadingFallback />}>
                  <UserProfile />
                </Suspense>
              </RouteGuard>
            ),
          },
          {
            path: 'settings',
            element: (
              <RouteGuard route={routes[0]}>
                <Suspense fallback={<LoadingFallback />}>
                  <Settings />
                </Suspense>
              </RouteGuard>
            ),
          },
          // 開發路由
          ...(process.env.NODE_ENV !== 'production' ? [{
            path: 'components',
            element: (
              <RouteGuard route={routes[0]}>
                <Suspense fallback={<LoadingFallback />}>
                  <UIComponents />
                </Suspense>
              </RouteGuard>
            ),
          }] : []),
        ],
      },
      // 重定向
      {
        path: 'login',
        element: <Navigate to="/auth/login" replace />,
      },
      {
        path: 'register',
        element: <Navigate to="/auth/register" replace />,
      },
    ],
    // 404
    {
      path: '*',
      element: (
        <Suspense fallback={<LoadingFallback />}>
          <NotFound />
        </Suspense>
      ),
    },
  },
]);

/**
 * 路由提供者組件
 */
export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

/**
 * 獲取菜單配置
 */
export const getMenuConfig = (): any[] => {
  return routes
    .filter(route => route.meta && !route.meta.hideInMenu)
    .map(route => ({
      key: route.path,
      label: route.meta?.title,
      path: route.path,
      icon: route.meta?.icon,
      children: route.children?.filter(child => child.meta && !child.meta.hideInMenu)
        .map(child => ({
          key: child.path,
          label: child.meta?.title,
          path: `${route.path}/${child.path}`,
        })),
    }));
};

/**
 * 根據路徑獲取面包屑
 */
export const getBreadcrumb = (pathname: string): any[] => {
  const breadcrumbs: any[] = [];
  const pathSegments = pathname.split('/').filter(Boolean);

  // 添加首頁
  breadcrumbs.push({
    title: '首頁',
    path: '/',
  });

  // 遍歷路徑段
  let currentPath = '';
  for (const segment of pathSegments) {
    currentPath += `/${segment}`;
    const route = findRouteByPath(currentPath);
    if (route && route.meta?.title) {
      breadcrumbs.push({
        title: route.meta.title,
        path: currentPath,
      });
    }
  }

  return breadcrumbs;
};

/**
 * 根據路徑查找路由配置
 */
const findRouteByPath = (path: string, routesList: RouteConfig[] = routes): RouteConfig | null => {
  for (const route of routesList) {
    if (route.path === path) {
      return route;
    }
    if (route.children) {
      const found = findRouteByPath(path, route.children);
      if (found) return found;
    }
  }
  return null;
};

export default router;