---
name: task-012-security-hardening
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: frontend-security-team
phase: 4
estimated_hours: 40
priority: high
---

# Task #12: 安全加固

## 📋 任務描述
對 CBSC Dashboard 進行全面的安全加固，包括 XSS 防護實施、CSRF 令牌集成、內容安全策略（CSP）和安全審計報告，確保金融數據和用戶信息的安全保護。

## 🎯 具體要求

### 12.1 XSS 防護實施
- [ ] 輸入驗證和清理
- [ ] 輸出編碼和轉義
- [ ] DOM based XSS 防護
- [ ] 安全的 HTML 渲染
- [ ] JSON 安全解析
- [ ] 內容過濾機制

### 12.2 CSRF 令牌集成
- [ ] CSRF 令牌生成和驗證
- [ ] Double Cookie Submit 模式
- [ ] AJAX 請求自動添加令牌
- [ ] 表單自動保護
- [ ] 令牌刷新機制
- [ ] 跨域請求控制

### 12.3 內容安全策略（CSP）
- [ ] CSP 頭部配置
- [ ] 內聯腳本限制
- [ ] 白名單資源源
- [ ] 報告違規行為
- [ ] 漸進式部署
- [ ] 動態策略更新

### 12.4 安全審計報告
- [ ] 依賴漏洞掃描
- [ ] 代碼安全審計
- [ ] 潛在威脅評估
- [ ] 安全測試報告
- [ ] 修復方案建議
- [ ] 持續監控機制

## ✅ 驗收標準

1. **安全標準**
   - [ ] 通過 OWASP ZAP 掃描
   - [ ] 無高危漏洞
   - [ ] 中危漏洞 < 5 個
   - [ ] CSP 違規率 < 1%

2. **合規要求**
   - [ ] 符合金融行業標準
   - [ ] GDPR 數據保護
   - [ ] PCI DSS 準則
   - [ ] 本地法規遵循

3. **性能影響**
   - [ ] 安全機制影響 < 5%
   - [ ] 無用戶體驗下降
   - [ ] 響應時間增加 < 50ms

## 🔧 技術要求

### XSS 防護實現
```typescript
// utils/security/xss.ts
export class XSSProtection {
  // 危险的 HTML 標籤
  private static readonly DANGEROUS_TAGS = [
    'script', 'iframe', 'object', 'embed', 'link', 'meta', 'style'
  ];

  // 危险的屬性
  private static readonly DANGEROUS_ATTRIBUTES = [
    'onload', 'onerror', 'onclick', 'onmouseover', 'onfocus', 'onblur',
    'javascript:', 'vbscript:', 'data:', 'src', 'href'
  ];

  // 清理 HTML 內容
  static sanitizeHTML(input: string): string {
    const tempDiv = document.createElement('div');
    tempDiv.textContent = input;
    return tempDiv.innerHTML;
  }

  // 安全的設置 HTML
  static setSecureHTML(element: HTMLElement, html: string): void {
    // 使用 DOMPurify 或自定義清理
    const cleanHTML = DOMPurify.sanitize(html, {
      ALLOWED_TAGS: [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p', 'br', 'strong', 'em', 'u',
        'ul', 'ol', 'li',
        'a', 'span', 'div',
        'table', 'thead', 'tbody', 'tr', 'td', 'th'
      ],
      ALLOWED_ATTR: ['href', 'title', 'class', 'id'],
      ALLOW_DATA_ATTR: false
    });

    element.innerHTML = cleanHTML;
  }

  // 驗證 URL
  static validateURL(url: string): boolean {
    try {
      const parsed = new URL(url, window.location.origin);

      // 只允許 http/https 協議
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        return false;
      }

      // 檢查是否為允許的域名
      const allowedDomains = [
        window.location.hostname,
        'api.cbsc.com',
        'cdn.cbsc.com'
      ];

      return allowedDomains.includes(parsed.hostname);
    } catch {
      return false;
    }
  }

  // 安全的 JSON 解析
  static safeJSONParse<T>(json: string): T | null {
    try {
      // 檢查是否包含危险模式
      if (this.hasDangerousPatterns(json)) {
        console.warn('Potentially dangerous JSON detected');
        return null;
      }

      return JSON.parse(json);
    } catch (error) {
      console.error('JSON parse error:', error);
      return null;
    }
  }

  // 检查危险模式
  private static hasDangerousPatterns(input: string): boolean {
    const dangerousPatterns = [
      /<script/i,
      /javascript:/i,
      /vbscript:/i,
      /on\w+\s*=/i,
      /expression\s*\(/i
    ];

    return dangerousPatterns.some(pattern => pattern.test(input));
  }
}

// 安全的組件屬性
interface SafeHTMLElementProps {
  dangerouslySetInnerHTML?: {
    __html: string;
  };
}

// 安全的渲染組件
export const SafeHTMLRenderer: React.FC<{
  html: string;
  tag?: keyof JSX.IntrinsicElements;
}> = ({ html, tag: Tag = 'div' }) => {
  const cleanHTML = useMemo(() => {
    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'br', 'p', 'span'],
      ALLOWED_ATTR: ['href', 'title', 'target', 'rel'],
      ADD_ATTR: ['target']
    });
  }, [html]);

  return <Tag dangerouslySetInnerHTML={{ __html: cleanHTML }} />;
};
```

### CSRF 保護機制
```typescript
// utils/security/csrf.ts
export class CSRFProtection {
  private static readonly TOKEN_COOKIE = 'csrf-token';
  private static readonly TOKEN_HEADER = 'X-CSRF-Token';
  private static readonly TOKEN_LENGTH = 32;

  // 生成 CSRF Token
  static generateToken(): string {
    const array = new Uint8Array(this.TOKEN_LENGTH);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  // 設置 Token
  static setToken(token: string): void {
    document.cookie = `${this.TOKEN_COOKIE}=${token}; path=/; secure; samesite=strict`;
  }

  // 獲取 Token
  static getToken(): string | null {
    const match = document.cookie.match(
      new RegExp(`(?:^|; )${this.TOKEN_COOKIE}=([^;]*)`)
    );
    return match ? decodeURIComponent(match[1]) : null;
  }

  // 驗證 Token
  static validateToken(receivedToken: string): boolean {
    const storedToken = this.getToken();
    return storedToken !== null && storedToken === receivedToken;
  }

  // 初始化 CSRF 保護
  static initialize(): void {
    // 如果沒有 Token，生成一個
    if (!this.getToken()) {
      this.setToken(this.generateToken());
    }

    // 攔截所有 fetch 請求
    const originalFetch = window.fetch;
    window.fetch = async (input, init) => {
      const token = this.getToken();

      if (token && init && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(init.method?.toUpperCase() || '')) {
        init.headers = {
          ...init.headers,
          [this.TOKEN_HEADER]: token
        };
      }

      return originalFetch.call(window, input, init);
    };

    // 攔截 XMLHttpRequest
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method: string, ...args: any[]) {
      (this as any)._method = method.toUpperCase();
      return originalXHROpen.apply(this, [method, ...args]);
    };

    XMLHttpRequest.prototype.send = function(body) {
      const method = (this as any)._method;
      const token = CSRFProtection.getToken();

      if (token && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
        this.setRequestHeader(CSRFProtection.TOKEN_HEADER, token);
      }

      return originalXHRSend.call(this, body);
    };
  }

  // 為表單添加 CSRF Token
  static protectForm(form: HTMLFormElement): void {
    const token = this.getToken();
    if (!token) return;

    // 檢查是否已經有隱藏的 CSRF input
    let csrfInput = form.querySelector(`input[name="${this.TOKEN_COOKIE}"]`) as HTMLInputElement;

    if (!csrfInput) {
      csrfInput = document.createElement('input');
      csrfInput.type = 'hidden';
      csrfInput.name = this.TOKEN_COOKIE;
      form.appendChild(csrfInput);
    }

    csrfInput.value = token;
  }
}

// React Hook 使用 CSRF 保護
export const useCSRF = () => {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const token = CSRFProtection.getToken();
    setToken(token);
  }, []);

  const protectedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
    const currentToken = CSRFProtection.getToken();

    if (currentToken && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase() || '')) {
      options.headers = {
        ...options.headers,
        'X-CSRF-Token': currentToken
      };
    }

    return fetch(url, options);
  }, []);

  return {
    token,
    protectedFetch,
    refresh: () => {
      const newToken = CSRFProtection.generateToken();
      CSRFProtection.setToken(newToken);
      setToken(newToken);
    }
  };
};
```

### CSP 配置
```typescript
// utils/security/csp.ts
export class CSPConfig {
  private static readonly DEFAULT_DIRECTIVES = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"], // 開發階段，生產環境移除 unsafe
    'style-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", 'data:', 'https:'],
    'font-src': ["'self'", 'data:'],
    'connect-src': ["'self'", 'wss:', 'https://api.cbsc.com'],
    'frame-src': ["'none'"],
    'object-src': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
    'frame-ancestors': ["'none'"],
    'upgrade-insecure-requests': []
  };

  // 生成 CSP 字符串
  static generateCSP(customDirectives?: Partial<typeof CSPConfig.DEFAULT_DIRECTIVES>): string {
    const directives = { ...this.DEFAULT_DIRECTIVES, ...customDirectives };

    return Object.entries(directives)
      .map(([key, values]) => {
        const value = values.join(' ');
        return `${key} ${value}`;
      })
      .join('; ');
  }

  // 通過 Meta 標籤設置 CSP
  static setMetaCSP(): void {
    const csp = this.generateCSP();

    // 移除現有的 CSP meta 標籤
    const existing = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
    if (existing) {
      existing.remove();
    }

    // 添加新的 CSP meta 標籤
    const meta = document.createElement('meta');
    meta.httpEquiv = 'Content-Security-Policy';
    meta.content = csp;
    document.head.appendChild(meta);
  }

  // 報告 CSP 違規
  static setupCSPReporting(reportUri: string): void {
    // 創建報告端點
    if ('ReportingObserver' in window) {
      const observer = new ReportingObserver((reports) => {
        reports.forEach(report => {
          if (report.type === 'csp-violation') {
            this.reportViolation(report as Report);
          }
        });
      });

      observer.observe();
    }

    // 傳統的 report-uri
    const csp = this.generateCSP({
      'report-uri': [reportUri]
    });

    this.setMetaCSP();
  }

  // 報告違規
  private static reportViolation(report: Report): void {
    const violation = report.body as CSPViolationReportBody;

    console.warn('CSP Violation:', {
      blockedURL: violation.blockedURL,
      documentURL: violation.documentURL,
      referrer: violation.referrer,
      violatedDirective: violation.violatedDirective,
      effectiveDirective: violation.effectiveDirective,
      originalPolicy: violation.originalPolicy,
      disposition: violation.disposition,
      sample: violation.sample
    });

    // 發送到服務器
    fetch('/api/security/csp-report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        violation
      })
    }).catch(console.error);
  }
}

// 生產環境 CSP 配置
export const productionCSP = CSPConfig.generateCSP({
  'script-src': ["'self'"], // 移除 unsafe-inline 和 unsafe-eval
  'style-src': ["'self'"], // 移除 unsafe-inline，使用 nonce
  'report-uri': ['/api/security/csp-report']
});
```

### 安全審計工具
```typescript
// utils/security/audit.ts
export class SecurityAudit {
  // 掃描依賴漏洞
  static async scanDependencies(): Promise<DependencyVulnerability[]> {
    try {
      // 使用 npm audit 或其他掃描工具
      const response = await fetch('/api/security/audit-dependencies');
      const audit = await response.json();

      return audit.vulnerabilities.map((vuln: any) => ({
        package: vuln.packageName,
        severity: vuln.severity,
        version: vuln.version,
        description: vuln.description,
        patchedIn: vuln.patchedVersions?.[0]
      }));
    } catch (error) {
      console.error('Dependency scan failed:', error);
      return [];
    }
  }

  // 檢查代碼中的安全問題
  static auditCode(code: string): CodeSecurityIssue[] {
    const issues: CodeSecurityIssue[] = [];

    // 檢查硬編碼的秘密
    const secretPatterns = [
      /password\s*=\s*["'][^"']+["']/gi,
      /api[_-]?key\s*=\s*["'][^"']+["']/gi,
      /secret\s*=\s*["'][^"']+["']/gi,
      /token\s*=\s*["'][^"']+["']/gi
    ];

    secretPatterns.forEach(pattern => {
      const matches = code.matchAll(pattern);
      for (const match of matches) {
        issues.push({
          type: 'hardcoded-secret',
          severity: 'high',
          line: this.getLineNumber(code, match.index!),
          description: 'Potentially hardcoded secret detected',
          recommendation: 'Use environment variables or secure storage'
        });
      }
    });

    // 檢查不安全的使用
    const unsafePatterns = [
      { pattern: /eval\s*\(/gi, issue: 'use-of-eval' },
      { pattern: /innerHTML\s*=/gi, issue: 'use-innerHTML' },
      { pattern: /document\.write\s*\(/gi, issue: 'use-document-write' }
    ];

    unsafePatterns.forEach(({ pattern, issue }) => {
      const matches = code.matchAll(pattern);
      for (const match of matches) {
        issues.push({
          type: issue,
          severity: 'medium',
          line: this.getLineNumber(code, match.index!),
          description: 'Potentially unsafe code pattern',
          recommendation: 'Use safer alternatives'
        });
      }
    });

    return issues;
  }

  // 檢查 localStorage 使用
  static auditLocalStorage(): StorageUsage[] {
    const usages: StorageUsage[] = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key) {
        const value = localStorage.getItem(key);
        const size = (key.length + (value?.length || 0)) * 2; // UTF-16

        usages.push({
          key,
          size,
          isSensitive: this.isSensitiveData(key, value || ''),
          isEncrypted: value?.startsWith('encrypted:') || false
        });
      }
    }

    return usages;
  }

  // 檢查網絡請求安全
  static auditNetworkRequests(): NetworkSecurityIssue[] {
    const issues: NetworkSecurityIssue[] = [];

    // 檢查是否使用 HTTPS
    if (window.location.protocol !== 'https:') {
      issues.push({
        type: 'insecure-protocol',
        severity: 'high',
        description: 'Application not served over HTTPS',
        recommendation: 'Always use HTTPS in production'
      });
    }

    // 檢查混合內容
    // TODO: 實現混合內容檢測

    return issues;
  }

  // 生成安全報告
  static async generateReport(): Promise<SecurityReport> {
    const [dependencies, localStorageUsage, networkIssues] = await Promise.all([
      this.scanDependencies(),
      Promise.resolve(this.auditLocalStorage()),
      Promise.resolve(this.auditNetworkRequests())
    ]);

    // 審計當前代碼
    const codeIssues = this.auditCode(
      document.documentElement.outerHTML
    );

    return {
      timestamp: new Date().toISOString(),
      version: process.env.REACT_APP_VERSION || 'unknown',
      dependencies,
      codeIssues,
      localStorage: localStorageUsage,
      networkIssues,
      score: this.calculateSecurityScore({
        dependencies,
        codeIssues,
        networkIssues
      })
    };
  }

  // 計算安全評分
  private static calculateSecurityScore(data: {
    dependencies: DependencyVulnerability[];
    codeIssues: CodeSecurityIssue[];
    networkIssues: NetworkSecurityIssue[];
  }): number {
    let score = 100;

    // 依賴漏洞扣分
    data.dependencies.forEach(vuln => {
      if (vuln.severity === 'high') score -= 20;
      else if (vuln.severity === 'medium') score -= 10;
      else if (vuln.severity === 'low') score -= 5;
    });

    // 代碼問題扣分
    data.codeIssues.forEach(issue => {
      if (issue.severity === 'high') score -= 15;
      else if (issue.severity === 'medium') score -= 8;
      else if (issue.severity === 'low') score -= 3;
    });

    // 網絡問題扣分
    data.networkIssues.forEach(issue => {
      if (issue.severity === 'high') score -= 25;
      else if (issue.severity === 'medium') score -= 12;
      else if (issue.severity === 'low') score -= 6;
    });

    return Math.max(0, score);
  }

  // 獲取行號
  private static getLineNumber(code: string, index: number): number {
    return code.substring(0, index).split('\n').length;
  }

  // 檢查是否為敏感數據
  private static isSensitiveData(key: string, value: string): boolean {
    const sensitiveKeys = ['password', 'token', 'secret', 'key', 'auth'];
    return sensitiveKeys.some(k => key.toLowerCase().includes(k));
  }
}

// 安全審計組件
export const SecurityAuditReport: React.FC = () => {
  const [report, setReport] = useState<SecurityReport | null>(null);
  const [loading, setLoading] = useState(false);

  const generateReport = async () => {
    setLoading(true);
    try {
      const securityReport = await SecurityAudit.generateReport();
      setReport(securityReport);
    } catch (error) {
      console.error('Failed to generate security report:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>安全審計報告</CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={generateReport} disabled={loading}>
          {loading ? '生成中...' : '生成報告'}
        </Button>

        {report && (
          <div className="mt-6 space-y-4">
            {/* 總體評分 */}
            <div className="flex items-center justify-between">
              <span className="text-lg font-medium">安全評分</span>
              <span className={`text-2xl font-bold ${
                report.score >= 80 ? 'text-green-600' :
                report.score >= 60 ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {report.score}/100
              </span>
            </div>

            {/* 依賴漏洞 */}
            {report.dependencies.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">依賴漏洞 ({report.dependencies.length})</h4>
                <ul className="space-y-1">
                  {report.dependencies.map((dep, index) => (
                    <li key={index} className="text-sm">
                      {dep.package}@{dep.version} - {dep.severity}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 代碼問題 */}
            {report.codeIssues.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">代碼問題 ({report.codeIssues.length})</h4>
                <ul className="space-y-1">
                  {report.codeIssues.map((issue, index) => (
                    <li key={index} className="text-sm">
                      行 {issue.line}: {issue.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 網絡問題 */}
            {report.networkIssues.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">網絡問題 ({report.networkIssues.length})</h4>
                <ul className="space-y-1">
                  {report.networkIssues.map((issue, index) => (
                    <li key={index} className="text-sm">
                      {issue.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| XSS 防護實施 | 16小時 | 安全工程師 + 前端工程師 A |
| CSRF 令牌集成 | 8小時 | 安全工程師 + 前端工程師 B |
| CSP 配置 | 8小時 | 安全工程師 |
| 安全審計報告 | 8小時 | 安全工程師 |
| **總計** | **40小時** | |

## 🔗 依賴關係
- 前置任務：Task #11 (測試覆蓋)
- 後續任務：Task #13 (生產部署)

## 📝 注意事項
1. 定期更新安全依賴
2. 持續監控安全威脅
3. 建立安全事件響應流程
4. 定期進行安全培訓
5. 遵循最小權限原則

## 🧪 安全測試
```typescript
// src/test/security/xss.test.tsx
describe('XSS Protection', () => {
  test('should sanitize malicious HTML', () => {
    const maliciousHTML = '<script>alert("xss")</script><p>Safe content</p>';
    const sanitized = XSSProtection.sanitizeHTML(maliciousHTML);

    expect(sanitized).not.toContain('<script>');
    expect(sanitized).toContain('<p>Safe content</p>');
  });

  test('should validate URLs', () => {
    expect(XSSProtection.validateURL('https://cbsc.com')).toBe(true);
    expect(XSSProtection.validateURL('javascript:alert(1)')).toBe(false);
    expect(XSSProtection.validateURL('data:text/html,<script>')).toBe(false);
  });
});

// src/test/security/csrf.test.ts
describe('CSRF Protection', () => {
  beforeEach(() => {
    CSRFProtection.initialize();
  });

  test('should add token to fetch requests', async () => {
    const fetchSpy = jest.spyOn(global, 'fetch');

    await fetch('/api/test', { method: 'POST' });

    expect(fetchSpy).toHaveBeenCalledWith(
      '/api/test',
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-CSRF-Token': expect.any(String)
        })
      })
    );
  });

  test('should protect forms', () => {
    const form = document.createElement('form');
    CSRFProtection.protectForm(form);

    const input = form.querySelector('input[name="csrf-token"]');
    expect(input).toBeTruthy();
    expect(input?.value).toBeTruthy();
  });
});
```

## 📚 相關文檔
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [DOMPurify 文檔](https://github.com/cure53/DOMPurify)
- [CSRF Protection Guide](https://owasp.org/www-community/attacks/csrf)
- [Security Headers](https://securityheaders.com/)