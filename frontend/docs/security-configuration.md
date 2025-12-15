# 安全配置指南 (Security Configuration Guide)

本文檔說明如何配置和使用 CBSC Dashboard 的安全功能。

## 目錄

1. [概述](#概述)
2. [初始化](#初始化)
3. [XSS 防護](#xss-防護)
4. [CSRF 保護](#csrf-保護)
5. [內容安全策略 (CSP)](#內容安全策略-csp)
6. [輸入驗證](#輸入驗證)
7. [加密](#加密)
8. [安全審計](#安全審計)
9. [安全中間件](#安全中間件)
10. [React 組件](#react-組件)
11. [React Hooks](#react-hooks)
12. [最佳實踐](#最佳實踐)

## 概述

CBSC Dashboard 安全系統提供多層次的保護：

- **XSS 防護**: 防止跨站腳本攻擊
- **CSRF 保護**: 防止跨站請求偽造
- **CSP**: 內容安全策略控制
- **輸入驗證**: 嚴格的數據驗證和清理
- **加密**: 敏感數據加密存儲
- **安全審計**: 持續的安全監控和審計

## 初始化

### 基本初始化

```typescript
import { initializeSecurity } from './security-init';

// 在應用啟動時初始化
const initApp = async () => {
  const securityInitialized = await initializeSecurity();
  if (!securityInitialized) {
    console.error('Security initialization failed');
    // 處理初始化失敗
  }

  // 繼續應用初始化...
};

initApp();
```

### 環境特定配置

```typescript
import { securityManager } from './utils/security';

// 開發環境
if (process.env.NODE_ENV === 'development') {
  securityManager.enableDevelopmentMode();
}

// 生產環境
if (process.env.NODE_ENV === 'production') {
  securityManager.enableProductionMode();
}
```

## XSS 防護

### 基本使用

```typescript
import { xssProtection, sanitizeHTML } from './utils/security';

// 清理 HTML 內容
const dirtyHTML = '<script>alert("XSS")</script><p>Safe content</p>';
const cleanHTML = sanitizeHTML(dirtyHTML);

// URL 驗證
const safeURL = xssProtection.sanitizeURL(userInputURL);

// JSON 安全解析
const safeData = xssProtection.safeJSONParse(jsonString);
```

### 配置 XSS 防護

```typescript
import { xssProtection } from './utils/security';

// 自定義配置
xssProtection.configure({
  ALLOWED_TAGS: ['p', 'b', 'i', 'strong', 'em', 'a'],
  ALLOWED_ATTR: ['href', 'title', 'class'],
  FORBID_TAGS: ['script', 'iframe', 'object'],
  FORBID_ATTR: ['onclick', 'onload', 'onerror']
});

// 添加信任的域名
xssProtection.addToWhitelist('https://partner.com');
```

### 使用 SafeHTML 組件

```typescript
import { SafeHTML } from './components/security/SafeHTML';

function UserContent({ content }) {
  return (
    <SafeHTML
      html={content}
      tag="div"
      className="user-content"
      onViolation={(violation) => {
        console.warn('XSS violation detected:', violation);
      }}
    />
  );
}
```

## CSRF 保護

### 自動保護

```typescript
import { csrfProtection } from './utils/security';

// 初始化（通常在應用啟動時完成）
csrfProtection.initialize();

// 獲取當前令牌
const token = csrfProtection.getToken();
```

### 手動添加令牌

```typescript
// 添加到請求頭
const headers = csrfProtection.addTokenToHeaders({
  'Content-Type': 'application/json'
});

// 添加到表單數據
const formData = new FormData();
csrfProtection.addTokenToFormData(formData);
```

### 使用安全的 fetch

```typescript
import { fetchWithCSRF } from './utils/security';

// 自動添加 CSRF 令牌的 fetch
const response = await fetchWithCSRF('/api/data', {
  method: 'POST',
  body: JSON.stringify(data)
});
```

### 使用 SecureForm 組件

```typescript
import { SecureForm, SecureInput } from './components/forms/SecureForm';

function StrategyForm({ onSubmit }) {
  return (
    <SecureForm onSubmit={onSubmit}>
      <SecureInput
        name="name"
        type="text"
        label="Strategy Name"
        required
        validation={(value) => {
          if (!value || value.length < 3) {
            return 'Name must be at least 3 characters';
          }
          return null;
        }}
      />
      <button type="submit">Submit</button>
    </SecureForm>
  );
}
```

## 內容安全策略 (CSP)

### 基本配置

```typescript
import { cspConfig } from './utils/security';

// 設置違規報告端點
cspConfig.setReportEndpoint('/api/security/csp-report');

// 添加信任的域名
cspConfig.addTrustedDomain('script-src', 'https://analytics.cbsc.com');
cspConfig.addTrustedDomain('connect-src', 'wss://ws.cbsc.com');
```

### 使用 Nonce

```typescript
// 啟用 nonce 進行內聯腳本保護
cspConfig.enableNonceForScripts();

// 在模板中使用 nonce
const nonce = cspConfig.getNonce();
// <script nonce={nonce}>...</script>
```

### 嚴格模式

```typescript
// 啟用嚴格的 CSP（推薦用於生產環境）
cspConfig.enableStrictMode();
```

## 輸入驗證

### 基本驗證

```typescript
import { inputValidator, validateFinancial } from './utils/security';

// 驗證電子郵件
const emailResult = inputValidator.validate(userEmail, {
  pattern: inputValidator.VALIDATION_PATTERNS.email,
  required: true
});

// 驗證金融數據
const financialData = {
  amount: '$1,000.00',
  symbol: 'AAPL',
  percentage: '15%'
};
const validationResult = validateFinancial(financialData);
```

### 使用預定義模式

```typescript
// 使用內置驗證模式
const patterns = {
  email: inputValidator.VALIDATION_PATTERNS.email,
  phone: inputValidator.VALIDATION_PATTERNS.phone,
  stockSymbol: inputValidator.VALIDATION_PATTERNS.stockSymbol,
  isin: inputValidator.VALIDATION_PATTERNS.isin
};
```

### 自定義驗證規則

```typescript
const customRule = {
  custom: (value) => {
    if (value.includes('admin')) {
      return 'Cannot use admin in value';
    }
    return true;
  }
};

const result = inputValidator.validate(userInput, customRule);
```

## 加密

### 基本加密

```typescript
import { encryption } from './utils/security';

// 初始化
await encryption.initialize();

// 加密字符串
const encrypted = encryption.encrypt('Sensitive data');
const decrypted = encryption.decrypt(encrypted);

// 加密對象
const encryptedObj = encryption.encryptObject({
  apiKey: 'secret-key',
  password: 'user-password'
});
const decryptedObj = encryption.decryptObject(encryptedObj);
```

### 安全存儲

```typescript
// 存儲加密數據到 localStorage
encryption.setSecureItem('userToken', token);
const storedToken = encryption.getSecureItem('userToken');

// 存儲到 sessionStorage
encryption.setSecureSessionItem('sessionData', data);
const sessionData = encryption.getSecureSessionItem('sessionData');
```

### 密碼保護的加密

```typescript
// 使用密碼加密（不存儲密鑰）
const passwordProtected = encryption.encryptWithPassword(data, userPassword);
const decrypted = encryption.decryptWithPassword(passwordProtected, userPassword);
```

## 安全審計

### 運行審計

```typescript
import { securityAudit } from './utils/security';

// 運行完整審計
securityAudit.runFullAudit();

// 獲取審計報告
const report = securityAudit.generateSecurityReport();
console.log('Security Score:', report.overallScore);
console.log('Vulnerabilities:', report.vulnerabilities);
```

### 配置審計

```typescript
// 更新審計配置
securityAudit.updateConfig({
  enabledChecks: {
    xss: true,
    csp: true,
    dependencies: true,
    localStorage: true,
    networkRequests: true
  },
  auditInterval: 30000 // 30秒
});
```

### 使用 SecurityAudit 組件

```typescript
import { SecurityAudit } from './components/security/SecurityAudit';

function SecurityDashboard() {
  return (
    <SecurityAudit
      autoRefresh={true}
      refreshInterval={60000}
      showDetails={true}
      onIssueClick={(issue) => {
        console.log('Issue clicked:', issue);
      }}
    />
  );
}
```

## 安全中間件

### 使用安全 fetch

```typescript
import { secureFetch } from './middleware/security';

const response = await secureFetch('/api/data', {
  method: 'POST',
  body: JSON.stringify(data),
  securityConfig: {
    enableCSRF: true,
    enableXSSProtection: true
  }
});
```

### 安全 WebSocket

```typescript
import { SecureWebSocket } from './middleware/security';

const ws = new SecureWebSocket('wss://api.cbsc.com/ws');
await ws.connect();

ws.send(JSON.stringify({ type: 'subscribe', channel: 'prices' }));
```

## React 組件

### 安全表單

```typescript
import { SecureForm, SecureInput, SecureTextarea } from './components/forms/SecureForm';

function ContactForm() {
  return (
    <SecureForm onSubmit={handleSubmit}>
      <SecureInput
        name="name"
        label="Name"
        required
        maxLength={100}
      />
      <SecureInput
        name="email"
        type="email"
        label="Email"
        required
      />
      <SecureTextarea
        name="message"
        label="Message"
        rows={4}
        maxLength={1000}
        sanitize={true}
      />
      <button type="submit">Send</button>
    </SecureForm>
  );
}
```

### 安全指標器

```typescript
import { SecurityIndicator, SecurityBadge } from './components/security/SecurityIndicator';

function Header() {
  return (
    <header>
      <h1>CBSC Dashboard</h1>
      <SecurityIndicator
        mode="compact"
        onClick={() => navigate('/security')}
      />
      <SecurityBadge type="xss" status="active" />
      <SecurityBadge type="csrf" status="active" />
    </header>
  );
}
```

## React Hooks

### XSS 防護 Hook

```typescript
import { useXSS, useSafeHTML } from './hooks/useXSS';

function UserInput() {
  const { input, setInput, sanitized, isValid, threats } = useXSS('', {
    validateOnType: true,
    maxLength: 500
  });

  return (
    <div>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Enter content..."
      />
      {!isValid && (
        <div className="error">
          Threats detected: {threats.join(', ')}
        </div>
      )}
    </div>
  );
}
```

### CSRF 保護 Hook

```typescript
import { useCSRF, useSecureAPI } from './hooks/useCSRF';

function APICalls() {
  const api = useSecureAPI('/api', {
    defaultHeaders: { 'Authorization': `Bearer ${token}` }
  });

  const loadData = async () => {
    try {
      const data = await api.get('/strategies');
      setData(data);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  return (
    <button onClick={loadData} disabled={api.loading}>
      {api.loading ? 'Loading...' : 'Load Data'}
    </button>
  );
}
```

### 安全審計 Hook

```typescript
import { useSecurityAudit, useSecurityMonitor } from './hooks/useSecurityAudit';

function SecurityPanel() {
  const { report, runAudit, autoRefresh } = useSecurityAudit({
    autoRefresh: true,
    refreshInterval: 60000
  });

  const { violations, thresholds, getSecurityHealth } = useSecurityMonitor();

  return (
    <div>
      <h2>Security Score: {report?.overallScore}/100</h2>
      <button onClick={runAudit}>Run Audit</button>
      <SecurityAudit report={report} />
    </div>
  );
}
```

## 最佳實踐

### 1. 永遠驗證用戶輸入

```typescript
// ❌ 錯誤：直接使用用戶輸入
element.innerHTML = userInput;

// ✅ 正確：清理和驗證輸入
element.innerHTML = sanitizeHTML(userInput);
```

### 2. 使用 HTTPS

```typescript
// 確保所有請求都使用 HTTPS
if (location.protocol !== 'https:') {
  location.replace(`https:${location.href.substring(location.protocol.length)}`);
}
```

### 3. 實施最小權限原則

```typescript
// 只授予必要的權限
const userPermissions = {
  canViewReports: true,
  canEditStrategies: false,  // 用戶不需要編輯權限
  canDeleteData: false
};
```

### 4. 定期更新依賴

```bash
# 定期運行
npm audit
npm audit fix
npm update
```

### 5. 監控安全事件

```typescript
// 設置安全警報
const { securityAudit } = require('./utils/security');

securityAudit.updateConfig({
  reportEndpoint: '/api/security/alerts'
});

// 監控關鍵事件
window.addEventListener('securitypolicyviolation', (event) => {
  // 發送警報到監控系統
  sendAlert({
    type: 'CSP_VIOLATION',
    details: event
  });
});
```

### 6. 使用安全標頭

```typescript
// 在生產環境中確保設置正確的標頭
if (process.env.NODE_ENV === 'production') {
  // 這些通常在服務器端設置
  const securityHeaders = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block'
  };
}
```

### 7. 處理錯誤安全

```typescript
// 不要洩露敏感錯誤信息
try {
  await sensitiveOperation();
} catch (error) {
  // ❌ 錯誤：洩露錯誤詳情
  // setError(`Failed: ${error.message}`);

  // ✅ 正確：通用錯誤消息
  setError('Operation failed. Please try again.');

  // 記錄詳細錯誤用於調試
  console.error('Operation failed:', error);
}
```

### 8. 實施速率限制

```typescript
// 客戶端速率限制
const rateLimiter = {
  attempts: 0,
  maxAttempts: 5,
  windowMs: 60000, // 1分鐘
  resetTime: 0,

  checkLimit() {
    const now = Date.now();
    if (now > this.resetTime) {
      this.attempts = 0;
      this.resetTime = now + this.windowMs;
    }

    this.attempts++;
    return this.attempts <= this.maxAttempts;
  }
};

// 使用示例
if (!rateLimiter.checkLimit()) {
  throw new Error('Too many requests. Please try again later.');
}
```

## 故障排除

### 常見問題

1. **CSRF 令牌錯誤**
   - 確保服務器端正確驗證令牌
   - 檢查 cookie 設置（SameSite, Secure, HttpOnly）

2. **CSP 違規**
   - 檢查 CSP 策略是否過於嚴格
   - 使用 nonce 或 hash 允許必要的內聯腳本

3. **加密失敗**
   - 確保正確初始化加密模塊
   - 檢查是否正確處理異步初始化

### 調試技巧

```typescript
// 啟用詳細日誌
if (process.env.NODE_ENV === 'development') {
  // 查看安全事件
  console.log('Security Events:', getSecurityEvents());

  // 查看當前安全狀態
  console.log('Security Status:', securityManager.getSecurityStatus());

  // 查看審計結果
  console.log('Audit Report:', securityAudit.generateSecurityReport());
}
```

## 總結

通過正確配置和使用這些安全功能，CBSC Dashboard 可以提供強大的安全保護，保護用戶數據和金融信息免受各種網絡威脅。

記住：
- 安全是一個持續的過程，不是一次性的設置
- 定期審查和更新安全配置
- 保持對最新安全威脅的了解
- 始終遵循安全最佳實踐