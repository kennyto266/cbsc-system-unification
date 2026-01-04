# CODEX-- 架構問題可視化

## 當前架構混亂狀態

```
┌─────────────────────────────────────────────────────────────┐
│                     CODEX-- 項目結構                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  frontend/  │    │unified-dash/│    │  square-ui/ │      │
│  │  (React)    │    │  (React)    │    │  (Next.js)  │      │
│  │             │    │             │    │             │      │
│  │ 3000+ files │    │ 1500+ files │    │ 800+ files  │      │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │  API Gateway?  │ ← 未明確              │
│                    │  (多個衝突)     │                        │
│                    └───────┬────────┘                        │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐              │
│         │                  │                  │              │
│    ┌────▼────┐       ┌─────▼─────┐      ┌────▼────┐         │
│    │ src/api/ │       │ backend/  │      │gateway/ │         │
│    │          │       │          │      │         │         │
│    │main.py   │       │main.py   │      │main.py  │         │
│    │(1300+    │       │(500+     │      │(200+    │         │
│    │ files)   │       │ files)   │      │ files)  │         │
│    └────┬─────┘       └─────┬─────┘      └────┬────┘         │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │  PostgreSQL    │                        │
│                    │  Redis         │                        │
│                    │  InfluxDB      │                        │
│                    └────────────────┘                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**問題**: 前端 → API 網關 → 後端 的路徑不清晰，有多個衝突的入口點

---

## API 端點衝突圖

```
請求路徑: /api/strategies

                    ┌─ 用戶請求
                    │
           ┌────────▼────────┐
           │  Load Balancer? │
           └────────┬────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
    ┌───▼────┐ ┌───▼────┐ ┌───▼────┐
    │src/api/ │ │backend/│ │src/api/│
    │strategy │ │api/    │ │strategi│
    │_endpoint│ │strategi│ │es/v2/  │
    │s.py     │ │es.py   │ │routes.│
    │         │ │         │ │py     │
    │(3003)   │ │(3004?)  │ │(3005?) │
    └────┬────┘ └────┬────┘ └────┬────┘
         │           │           │
         └───────────┼───────────┘
                     │
            ┌────────▼────────┐
            │ 哪個是正確的？   │
            │ 結果不同？       │
            │ 哪個會被調用？   │
            └─────────────────┘
```

**風險**:
- 不同實現可能有不同的行為
- 測試可能通過一個但失敗於另一個
- 生產環境的不確定性

---

## 依賴版本衝突圖

```
pandas 依賴樹:

根目錄/requirements.txt        src/requirements.txt
       │                              │
       ├─ pandas==2.2.3               ├─ pandas==2.1.3
       │    │                         │    │
       │    ├─ numpy>=1.24.3          │    ├─ numpy>=1.25.2
       │    │    │                    │    │    │
       │    │    └─ [其他包]          │    │    └─ [其他包]
       │    │                         │    │
       │    └─ [其他依賴]             │    └─ [其他依賴]
       │                              │
問題: numpy 1.24.x vs 1.25.x 可能有
不同的數值計算結果，導致策略回測
不一致！
```

**影響**:
- 回測結果不可重現
- 數據分析結果不一致
- 潛在的財務風險

---

## 前端狀態管理混亂

```
組件層級:

Dashboard.tsx
    │
    ├─ useStrategies() ────→ strategiesSlice.ts (Redux)
    │                              │
    ├─ useStrategies() ────→ strategiesApi.ts (RTK Query)
    │                              │
    └─ useStrategies() ────→ strategyAPI.ts (Axios)

問題: 3 種不同的數據獲取方式，
哪一個會被使用？數據會同步嗎？
```

**影響**:
- 不必要的網絡請求 (3 次)
- 狀態不一致
- 難以調試

---

## Docker Compose 配置混亂

```
50+ 個 docker-compose 文件:

docker-compose.yml
├─ docker-compose.dev.yml
│   ├─ docker-compose.auth.yml
│   ├─ docker-compose.cbsc-api.yml
│   ├─ docker-compose.cbsc-unified.yml
│   └─ docker-compose.monitoring.yml
│       └─ docker-compose.test.yml
│           └─ [還有 40+ 個...]
│
問題: 應該用哪個啟動系統？
- docker-compose up                    (用哪個？)
- docker-compose -f dev.yml up         (dev.yml?)
- docker-compose -f cbsc-api.yml up    (api?)
```

**影響**:
- 新開發者不知道如何啟動
- 不同環境配置不一致
- 部署容易出錯

---

## 數據模型重複

```
User 模型定義在 6 個地方:

src/models/user.py
├─ id: int
├─ username: str
├─ email: str
└─ password_hash: str

backend/models/user.py
├─ id: int
├─ username: str
├─ email: str
└─ password_hash: str

src/api/strategies/models.py
├─ user_id: int         (不同的字段名！)
├─ username: str
├─ email: str
└─ password: str        (沒有 hash！)

問題: 哪個是正確的？字段名不一致
會導致序列化錯誤和數據丟失！
```

---

## 認證系統重複

```
6 個不同的認證實現:

src/auth_simple.py (300 行)
├─ verify_password()
├─ create_access_token()
└─ authenticate_user()

src/api/auth_endpoints.py (400 行)
├─ verify_password()
├─ create_access_token()
└─ authenticate_user()

src/api/auth/auth_endpoints_v2.py (500 行)
├─ verify_password_v2()
├─ create_access_token_v2()
└─ authenticate_user_v2()

backend/api/auth.py (350 行)
├─ check_password()
├─ generate_token()
└─ login()

src/services/auth.py (250 行)
├─ verify()
├─ token()
└─ auth()

src/api/auth/auth_utils.py (200 行)
└─ [工具函數]

總計: 2000 行重複代碼
問題: 如果一個有漏洞，其他也可能有
```

---

## 環境配置混亂

```
11 個 .env 文件:

.env                    ← 當前使用？
.env.auth.example
.env.backup
.env.dev.backup
.env.example
.env.full
.env.local
.env.memory           ← 這是什麼？
.env.prod
.env.production       ← 與 .prod 重複
.env.template

典型配置衝突:
.env:                  DATABASE_URL=postgresql://localhost:5432/cbsc
.env.prod:             DATABASE_URL=postgresql://prod-db:5432/cbsc_prod
docker-compose.dev:    POSTGRES_DB=cbsc_dev
docker-compose.prod:   POSTGRES_DB=cbsc_production

問題: 哪個是當前使用的？可能連接到錯誤的數據庫！
```

---

## 前端依賴冗餘

```
frontend/package.json (133 依賴):

圖表庫 (3 個):
├─ plotly.js (~6MB)
├─ chart.js (~200KB)
└─ recharts (~150KB)

UI 庫 (2 套完整系統):
├─ Ant Design (完整組件庫)
│   ├─ @ant-design/icons
│   ├─ antd
│   └─ [50+ 組件]
└─ Radix UI (完整組件庫)
    ├─ @radix-ui/react-accordion
    ├─ @radix-ui/react-avatar
    ├─ @radix-ui/react-checkbox
    ├─ @radix-ui/react-dialog
    └─ [30+ 組件]

狀態管理 (2 個):
├─ Redux Toolkit
└─ React Query

實際使用率: ~20%
浪費: ~10MB (40% bundle 大小)
```

---

## 測試文件分散

```
測試文件分散在 10+ 個位置:

tests/
├─ unit/
├─ integration/
├─ e2e/
├─ performance/
└─ load/

backend/tests/
├─ unit/
└─ integration/

src/api/*/tests/
├─ test_*.py
└─ conftest.py

frontend/src/tests/
├─ setupTests.ts
└─ *.test.tsx

frontend/src/**/__tests__/
└─ *.test.ts*

問題:
- 無法運行所有測試
- 測試配置不一致
- CI/CD 難以設置
```

---

## Git 工作樹混亂

```
19 個未清理的工作樹:

.worktrees/
├─ 001-
├─ 002-robust-error-handling-recovery
├─ 003-codebase-refactoring-performance-optimization
├─ 004-conflict-resolution-engine
├─ 005-decision-capture-tracking
├─ 006-advanced-progress-analytics
├─ 007-persistent-context-storage-system
├─ 008-real-time-collaboration-dashboard
├─ 009-end-to-end-traceability-system
├─ 010-live-code-review-system
├─ 011-intelligent-task-prioritization
├─ 012-automated-testing-integration
├─ 013-workflow-optimization-engine
├─ 014-smart-code-completion
├─ 015-multi-tool-integration-hub
├─ 016-mobile-companion-app
├─ 017-custom-agent-framework
├─ 018-enterprise-security-compliance
└─ 019-api-ecosystem-webhooks

問題: 佔用大量磁盤空間，影響 git 操作性能
```

---

## 建議的清理後架構

```
┌─────────────────────────────────────────────────────────────┐
│               清理後的 CODEX-- 項目結構                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐                                            │
│  │  frontend/  │ (統一的前端應用)                            │
│  │  (React)    │                                            │
│  │  1000 files │                                            │
│  └──────┬──────┘                                            │
│         │                                                    │
│         │ HTTP/WebSocket                                    │
│         │                                                    │
│  ┌──────▼────────────────────────────────┐                  │
│  │         API Gateway (端口 8000)       │                  │
│  │  ┌─────────────────────────────────┐  │                  │
│  │  │  路由管理                       │  │                  │
│  │  │  認證                           │  │                  │
│  │  │  限流                           │  │                  │
│  │  │  日誌                           │  │                  │
│  │  └─────────────────────────────────┘  │                  │
│  └──────┬────────────────────────────────┘                  │
│         │                                                    │
│         ├──────────────┬──────────────┐                     │
│         │              │              │                     │
│    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐                │
│    │Strategy  │   │Backtest │   │Analytics│                │
│    │Service   │   │Service  │   │Service  │                │
│    │(3003)    │   │(3004)    │   │(3005)    │                │
│    └────┬─────┘   └────┬─────┘   └────┬─────┘                │
│         │              │              │                     │
│         └──────────────┼──────────────┘                     │
│                        │                                    │
│                ┌───────▼────────┐                          │
│                │  PostgreSQL    │                          │
│                │  Redis         │                          │
│                │  InfluxDB      │                          │
│                └────────────────┘                          │
│                                                               │
│  測試: tests/ (統一位置)                                      │
│  文檔: docs/ (統一位置)                                      │
│  配置: docker-compose.yml (單一文件 + overrides)             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 遷移步驟可視化

```
Phase 1: 穩定化 (Week 1-2)
├─ [ ] 凍結新功能
├─ [ ] 備份數據庫
├─ [ ] 設置 CI/CD
└─ [ ] 創建分支

Phase 2: 整合 (Week 3-4)
├─ [ ] 合併 API 端點
├─ [ ] 統一前端
├─ [ ] 整合測試
└─ [ ] 更新文檔

Phase 3: 優化 (Week 5-8)
├─ [ ] 性能優化
├─ [ ] 架構重構
├─ [ ] 實施監控
└─ [ ] 安全審計

Phase 4: 維護 (持續)
├─ [ ] 代碼審查
├─ [ ] 依賴更新
├─ [ ] 文檔維護
└─ [ ] 債務管理
```

---

## 重複度熱力圖

```
文件類型              重複度    優先級
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API 端點 (.py)       ████ 85%  Critical
認證系統 (.py)       ████ 80%  Critical
前端組件 (.tsx)      ███  60%  High
數據模型 (.py)       ███  60%  High
配置文件 (.yml)      ███  70%  High
測試文件 (.py/.ts)   ██   40%  Medium
文檔 (.md)           ██   50%  Medium
工具函數 (.py/.ts)   ██   45%  Medium
```

---

## 風險評估矩陣

```
影響
高 │   API 衝突    依賴衝突    數據庫遷移
   │  (Critical)  (Critical)  (Medium)
   │
中 │   前端整合    Docker配置  測試整合
   │  (High)      (Medium)    (Medium)
   │
低 │   文檔整理    代碼格式    Git清理
   │  (Low)       (Low)       (Low)
   └───────────────────────────────→ 可能性
          低    中    高
```

---

## 資源分配建議

```
人力: 2-3 名開發者
時間: 6-8 週
預算: [根據團隊調整]

Week 1-2: 20% 時間
- 穩定化和準備
- 風險最低但收益高

Week 3-4: 40% 時間
- 核心整合
- 風險和收益都高

Week 5-8: 30% 時間
- 優化和改進
- 中等風險

持續: 10% 時間
- 維護和監控
- 低風險
```

---

**生成時間**: 2026-01-04
**可視化工具**: ASCII Art
**狀態**: ✅ 完成
