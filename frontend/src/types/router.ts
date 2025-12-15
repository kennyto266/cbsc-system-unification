/**
 * Router Types - 路由類型定義
 * 版本: 1.0.0
 * 描述: 定義路由系統的類型結構
 */

import { ReactNode } from 'react';

// 路由級別
export type RouteLevel = 'public' | 'protected' | 'admin';

// 路由配置接口
export interface RouteConfig {
  path: string;
  element: ReactNode | React.ComponentType;
  level?: RouteLevel;
  title?: string;
  description?: string;
  meta?: {
    requiresAuth?: boolean;
    roles?: string[];
    permissions?: string[];
    keepAlive?: boolean;
    hideInMenu?: boolean;
    icon?: ReactNode;
    badge?: string | number;
  };
  children?: RouteConfig[];
  // 懶加載配置
  lazy?: boolean;
  // 預加載
  preload?: boolean;
  // 錯誤邊界
  errorBoundary?: React.ComponentType<{ error: Error }>;
}

// 菜單項接口
export interface MenuItem {
  key: string;
  label: string;
  path?: string;
  icon?: ReactNode;
  children?: MenuItem[];
  badge?: string | number;
  disabled?: boolean;
  hidden?: boolean;
}

// 面包屑項接口
export interface BreadcrumbItem {
  title: string;
  path?: string;
  icon?: ReactNode;
}

// 路由元數據
export interface RouteMeta {
  title: string;
  description?: string;
  keywords?: string[];
  requiresAuth?: boolean;
  roles?: string[];
  permissions?: string[];
  keepAlive?: boolean;
  hideInMenu?: boolean;
  fullPage?: boolean;
  transition?: string;
}

// 路由參數類型
export interface RouteParams {
  [key: string]: string | undefined;
}

// 查詢參數類型
export interface QueryParams {
  [key: string]: string | string[] | undefined;
}

// 導航選項
export interface NavigationOptions {
  replace?: boolean;
  state?: any;
  shallow?: boolean;
}

// 路由守衛類型
export type RouteGuard = (
  to: RouteLocation,
  from: RouteLocation,
  next: (to?: string | false) => void
) => void;

// 路由位置信息
export interface RouteLocation {
  path: string;
  params: RouteParams;
  query: QueryParams;
  hash: string;
  fullPath: string;
  meta: RouteMeta;
}

// 權限檢查結果
export interface PermissionCheck {
  hasPermission: boolean;
  missingRoles?: string[];
  missingPermissions?: string[];
  redirectPath?: string;
}

// 路由緩存配置
export interface RouteCacheConfig {
  max: number;
  ttl: number; // Time to live in milliseconds
}

// 動態路由配置
export interface DynamicRouteConfig {
  name: string;
  path: string;
  component: () => Promise<{ default: React.ComponentType }>;
  meta?: RouteMeta;
  props?: Record<string, any>;
}

// 路由匹配結果
export interface RouteMatch {
  route: RouteConfig;
  params: RouteParams;
  query: QueryParams;
  meta: RouteMeta;
}