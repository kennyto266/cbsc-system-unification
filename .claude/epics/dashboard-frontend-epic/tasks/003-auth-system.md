---
name: task-003-auth-system
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: frontend-backend-team
phase: 1
estimated_hours: 32
priority: high
---

# Task #3: 認證與授權系統

## 📋 任務描述
實現 CBSC Dashboard 的完整認證與授權系統，包括 JWT 認證流程、角色權限控制（RBAC）、路由守衛機制和會話管理系統，確保系統安全性和用戶數據保護。

## 🎯 具體要求

### 3.1 JWT 認證流程
- [ ] 實現用戶登錄功能
- [ ] JWT token 獲取和存儲
- [ ] Token 自動刷新機制
- [ ] 安全登出處理
- [ ] 記住登錄狀態功能

### 3.2 角色權限控制（RBAC）
- [ ] 權限模型設計
- [ ] 角色定義（管理員、交易員、分析師、只讀用戶）
- [ ] 權限檢查 Hook 實現
- [ ] 動態權限驗證
- [ ] 權限緩存機制

### 3.3 路由守衛機制
- [ ] 私有路由保護
- [ ] 權限級別路由控制
- [ ] 未授權訪問重定向
- [ ] 路由級權限檢查
- [ ] 動態路由生成

### 3.4 會話管理系統
- [ ] 活動會話監控
- [ ] 會話超時處理
- [ ] 多設備會話管理
- [ ] 會話安全檢查
- [ ] SSO 單點登錄準備

## ✅ 驗收標準

1. **功能驗收**
   - [ ] 用戶可以成功登錄並獲得適當權限
   - [ ] 未登錄用戶無法訪問受保護路由
   - [ ] 權限變更即時生效
   - [ ] Token 過期自動刷新

2. **安全標準**
   - [ ] JWT token 使用 RS256 簽名
   - [ ] 敏感數據加密存儲
   - [ ] XSS 和 CSRF 防護
   - [ ] 密碼強度驗證
   - [ ] 會話劫持防護

3. **性能標準**
   - [ ] 登錄響應時間 < 500ms
   - [ ] 權限檢查時間 < 10ms
   - [ ] Token 刷新無感知
   - [ ] 會話管理內存佔用 < 1MB

## 🔧 技術要求

### 認證服務實現
```typescript
// services/auth/authService.ts
export interface LoginCredentials {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  roles: Role[];
  permissions: Permission[];
  lastLogin: Date;
}

export class AuthService {
  private token: string | null = null;
  private refreshToken: string | null = null;
  private tokenExpiry: number | null = null;

  constructor(private storage: Storage = localStorage) {
    this.initializeFromStorage();
  }

  async login(credentials: LoginCredentials): Promise<AuthUser> {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(credentials)
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const { access_token, refresh_token, user } = await response.json();

      this.setToken(access_token);
      this.setRefreshToken(refresh_token);

      if (credentials.rememberMe) {
        this.storage.setItem('auth_remember', 'true');
      }

      return user;
    } catch (error) {
      this.clearTokens();
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`
        }
      });
    } finally {
      this.clearTokens();
      window.location.href = '/login';
    }
  }

  hasPermission(permission: string): boolean {
    const user = this.getCurrentUser();
    return user?.permissions?.some(p => p.name === permission) ?? false;
  }

  hasRole(role: string): boolean {
    const user = this.getCurrentUser();
    return user?.roles?.some(r => r.name === role) ?? false;
  }

  async refreshTokenIfNeeded(): Promise<boolean> {
    if (!this.token || !this.isTokenExpiringSoon()) {
      return true;
    }

    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token: this.refreshToken })
      });

      if (response.ok) {
        const { access_token } = await response.json();
        this.setToken(access_token);
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }

    this.clearTokens();
    return false;
  }

  private isTokenExpiringSoon(): boolean {
    if (!this.tokenExpiry) return true;
    return Date.now() > this.tokenExpiry - 5 * 60 * 1000; // 5 minutes before expiry
  }
}
```

### 權限 Hook 實現
```typescript
// hooks/useAuth.ts
export const useAuth = () => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const authService = useMemo(() => new AuthService(), []);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const isValid = await authService.validateToken();
        if (isValid) {
          const currentUser = authService.getCurrentUser();
          setUser(currentUser);
        }
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [authService]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const user = await authService.login(credentials);
    setUser(user);
    return user;
  }, [authService]);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, [authService]);

  const hasPermission = useCallback((permission: string) => {
    return authService.hasPermission(permission);
  }, [authService]);

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    hasPermission,
    hasRole: authService.hasRole.bind(authService)
  };
};
```

### 路由守衛組件
```typescript
// components/guards/ProtectedRoute.tsx
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requiredRole?: string;
  fallback?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredPermission,
  requiredRole,
  fallback = <Navigate to="/unauthorized" replace />
}) => {
  const { isAuthenticated, hasPermission, hasRole, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <PageLoading />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return fallback;
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return fallback;
  }

  return <>{children}</>;
};

// 使用示例
// <Route path="/admin/*" element={
//   <ProtectedRoute requiredRole="admin">
//     <AdminRoutes />
//   </ProtectedRoute>
// } />
```

### Redux Store 配置
```typescript
// store/slices/authSlice.ts
export interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  lastActivity: number;
}

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    loginSuccess: (state, action) => {
      state.user = action.payload;
      state.isAuthenticated = true;
      state.isLoading = false;
      state.lastActivity = Date.now();
    },
    loginFailure: (state, action) => {
      state.error = action.payload;
      state.isLoading = false;
    },
    logout: (state) => {
      state.user = null;
      state.isAuthenticated = false;
      state.error = null;
    },
    updateUser: (state, action) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
    updateLastActivity: (state) => {
      state.lastActivity = Date.now();
    }
  }
});
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| JWT 認證流程 | 8小時 | 前端工程師 A |
| RBAC 權限系統 | 10小時 | 前端工程師 B |
| 路由守衛機制 | 6小時 | 前端工程師 A |
| 會話管理系統 | 8小時 | 後端工程師 + 前端工程師 B |
| **總計** | **32小時** | |

## 🔗 依賴關係
- 前置任務：Task #1 (項目初始化), Task #2 (設計系統)
- 後續任務：Task #4 (Dashboard主界面)

## 📝 注意事項
1. 所有認證相關的 API 請求必須使用 HTTPS
2. 敏感信息不能存儲在 localStorage 中（考慮使用 sessionStorage 或 HttpOnly cookies）
3. 實現登錄失敗次數限制
4. 考慮實現多因素認證（MFA）

## 🧪 測試要求
```typescript
// services/auth/__tests__/authService.test.ts
describe('AuthService', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('should handle successful login', async () => {
    const mockResponse = {
      access_token: 'mock-token',
      refresh_token: 'mock-refresh',
      user: mockUser
    };

    fetchMock.mockResponseOnce(JSON.stringify(mockResponse));

    const authService = new AuthService();
    const user = await authService.login(mockCredentials);

    expect(user).toEqual(mockUser);
    expect(localStorage.getItem('access_token')).toBe('mock-token');
  });

  test('should handle login failure', async () => {
    fetchMock.mockResponseOnce('', { status: 401 });

    const authService = new AuthService();
    await expect(authService.login(mockCredentials)).rejects.toThrow('Login failed');
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  test('should check permissions correctly', () => {
    const authService = new AuthService();
    localStorage.setItem('user', JSON.stringify(mockUser));

    expect(authService.hasPermission('read:strategies')).toBe(true);
    expect(authService.hasPermission('write:system')).toBe(false);
  });
});
```

## 📚 相關文籠
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [React Router v6 文檔](https://reactrouter.com/)