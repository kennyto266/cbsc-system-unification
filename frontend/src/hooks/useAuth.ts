/**
 * useAuth - 認證 Hook
 * 版本: 1.0.0
 * 描述: 處理用戶認證和授權邏輯
 */

import { useState, useEffect, useCallback, useContext, createContext } from 'react';
import { PermissionCheck } from '../types/router';

// 用戶信息接口
export interface User {
  id: string;
  username: string;
  email: string;
  roles: string[];
  permissions: string[];
  avatar?: string;
  lastLogin?: string;
  preferences?: Record<string, any>;
}

// 認證上下文接口
export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  refreshToken: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  hasAllRoles: (roles: string[]) => boolean;
  updateProfile: (data: Partial<User>) => Promise<void>;
  changePassword: (oldPassword: string, newPassword: string) => Promise<void>;
}

// 登錄憑證接口
export interface LoginCredentials {
  username: string;
  password: string;
  rememberMe?: boolean;
  captcha?: string;
  mfaCode?: string;
}

// 註冊數據接口
export interface RegisterData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  agreeToTerms: boolean;
  captcha?: string;
  invitationCode?: string;
}

// JWT Token 接口
export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
}

// 創建認證上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * 認證提供者組件
 */
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 檢查認證狀態
  const checkAuthStatus = useCallback(async () => {
    try {
      const tokens = getStoredTokens();
      if (!tokens || !isTokenValid(tokens.accessToken)) {
        // 嘗試刷新 token
        if (tokens && tokens.refreshToken) {
          await refreshAccessToken();
        } else {
          setIsLoading(false);
          return;
        }
      }

      // 獲取用戶信息
      const userInfo = await fetchUserInfo();
      setUser(userInfo);
    } catch (error) {
      console.error('Auth check failed:', error);
      clearStoredTokens();
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 登錄
  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    try {
      // 調用登錄 API
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Login failed');
      }

      const { tokens, user: userData } = await response.json();

      // 保存 tokens
      storeTokens(tokens);

      // 設置用戶信息
      setUser(userData);

      // 設置 axios 默認 header
      if (typeof window !== 'undefined') {
        (window as any).axios = (window as any).axios || {};
        (window as any).axios.defaults = (window as any).axios.defaults || {};
        (window as any).axios.defaults.headers = {
          ...((window as any).axios.defaults.headers || {}),
          Authorization: `Bearer ${tokens.accessToken}`,
        };
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 註冊
  const register = useCallback(async (userData: RegisterData) => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Registration failed');
      }

      const { message } = await response.json();
      console.log('Registration successful:', message);
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 登出
  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      // 調用登出 API
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getStoredTokens()?.accessToken}`,
        },
      });
    } catch (error) {
      console.error('Logout API error:', error);
    } finally {
      // 無論 API 調用是否成功，都清除本地狀態
      clearStoredTokens();
      setUser(null);
      setIsLoading(false);
    }
  }, []);

  // 刷新 token
  const refreshToken = useCallback(async () => {
    try {
      const tokens = await refreshAccessToken();
      setUser(prev => prev ? { ...prev } : null);
    } catch (error) {
      console.error('Token refresh failed:', error);
      await logout();
    }
  }, [logout]);

  // 權限檢查函數
  const hasPermission = useCallback((permission: string) => {
    if (!user) return false;
    return user.permissions.includes(permission);
  }, [user]);

  const hasRole = useCallback((role: string) => {
    if (!user) return false;
    return user.roles.includes(role);
  }, [user]);

  const hasAnyPermission = useCallback((permissions: string[]) => {
    if (!user) return false;
    return permissions.some(permission => user.permissions.includes(permission));
  }, [user]);

  const hasAllPermissions = useCallback((permissions: string[]) => {
    if (!user) return false;
    return permissions.every(permission => user.permissions.includes(permission));
  }, [user]);

  const hasAnyRole = useCallback((roles: string[]) => {
    if (!user) return false;
    return roles.some(role => user.roles.includes(role));
  }, [user]);

  const hasAllRoles = useCallback((roles: string[]) => {
    if (!user) return false;
    return roles.every(role => user.roles.includes(role));
  }, [user]);

  // 更新個人資料
  const updateProfile = useCallback(async (data: Partial<User>) => {
    try {
      const response = await fetch('/api/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getStoredTokens()?.accessToken}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Profile update failed');
      }

      const updatedUser = await response.json();
      setUser(updatedUser);
    } catch (error) {
      console.error('Profile update error:', error);
      throw error;
    }
  }, []);

  // 修改密碼
  const changePassword = useCallback(async (oldPassword: string, newPassword: string) => {
    try {
      const response = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getStoredTokens()?.accessToken}`,
        },
        body: JSON.stringify({ oldPassword, newPassword }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Password change failed');
      }
    } catch (error) {
      console.error('Password change error:', error);
      throw error;
    }
  }, []);

  // 初始化時檢查認證狀態
  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  // 定期刷新 token
  useEffect(() => {
    if (!user) return;

    const interval = setInterval(async () => {
      const tokens = getStoredTokens();
      if (tokens && isTokenExpiringSoon(tokens.accessToken)) {
        await refreshToken();
      }
    }, 60000); // 每分鐘檢查一次

    return () => clearInterval(interval);
  }, [user, refreshToken]);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    register,
    refreshToken,
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    hasAnyRole,
    hasAllRoles,
    updateProfile,
    changePassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * 使用認證的 Hook
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

/**
 * 權限守衛 Hook
 */
export const usePermissionGuard = (
  requiredPermissions?: string[],
  requiredRoles?: string[]
): PermissionCheck => {
  const { isAuthenticated, hasAllPermissions, hasAllRoles } = useAuth();

  if (!isAuthenticated) {
    return {
      hasPermission: false,
      redirectPath: '/login',
    };
  }

  const missingPermissions = requiredPermissions?.filter(p => !hasAllPermissions([p])) || [];
  const missingRoles = requiredRoles?.filter(r => !hasAllRoles([r])) || [];

  const hasPermission = missingPermissions.length === 0 && missingRoles.length === 0;

  return {
    hasPermission,
    missingPermissions: missingPermissions.length > 0 ? missingPermissions : undefined,
    missingRoles: missingRoles.length > 0 ? missingRoles : undefined,
    redirectPath: !hasPermission ? '/403' : undefined,
  };
};

// 工具函數

/**
 * 獲取存儲的 tokens
 */
function getStoredTokens(): AuthTokens | null {
  if (typeof localStorage === 'undefined') return null;

  try {
    const tokenData = localStorage.getItem('cbsc_auth_tokens');
    return tokenData ? JSON.parse(tokenData) : null;
  } catch {
    return null;
  }
}

/**
 * 保存 tokens
 */
function storeTokens(tokens: AuthTokens): void {
  if (typeof localStorage === 'undefined') return;

  try {
    localStorage.setItem('cbsc_auth_tokens', JSON.stringify(tokens));
  } catch (error) {
    console.error('Failed to store tokens:', error);
  }
}

/**
 * 清除存儲的 tokens
 */
function clearStoredTokens(): void {
  if (typeof localStorage === 'undefined') return;

  try {
    localStorage.removeItem('cbsc_auth_tokens');
  } catch (error) {
    console.error('Failed to clear tokens:', error);
  }
}

/**
 * 檢查 token 是否有效
 */
function isTokenValid(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

/**
 * 檢查 token 是否即將過期（5分鐘內）
 */
function isTokenExpiringSoon(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const fiveMinutes = 5 * 60 * 1000;
    return payload.exp * 1000 - Date.now() < fiveMinutes;
  } catch {
    return true;
  }
}

/**
 * 刷新 access token
 */
async function refreshAccessToken(): Promise<AuthTokens> {
  const tokens = getStoredTokens();
  if (!tokens?.refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refreshToken: tokens.refreshToken }),
  });

  if (!response.ok) {
    throw new Error('Token refresh failed');
  }

  const newTokens = await response.json();
  storeTokens(newTokens);
  return newTokens;
}

/**
 * 獲取用戶信息
 */
async function fetchUserInfo(): Promise<User> {
  const tokens = getStoredTokens();
  if (!tokens) {
    throw new Error('No tokens available');
  }

  const response = await fetch('/api/auth/me', {
    headers: {
      'Authorization': `Bearer ${tokens.accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user info');
  }

  return response.json();
}

// 導出默認值
export default useAuth;