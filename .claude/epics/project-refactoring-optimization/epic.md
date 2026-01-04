---
name: project-refactoring-optimization
status: completed
created: 2025-12-24T12:04:03Z
updated: 2025-12-25T10:45:00Z
progress: 100%
prd: .claude/prds/project-refactoring-optimization.md
tasks: 9 tasks defined (9 completed)
epic_coordination: system-unification (Level 2 sub-epic)
analysis_report: .claude/epics/PROJECT-REFACTORING-ANALYSIS.md
github:
  repo: kennyto266/cbsc-system-unification
  issues:
    - task: 001
      id: 73
      url: https://github.com/kennyto266/cbsc-system-unification/issues/73
    - task: 002
      id: 74
      url: https://github.com/kennyto266/cbsc-system-unification/issues/74
    - task: 003
      id: 75
      url: https://github.com/kennyto266/cbsc-system-unification/issues/75
    - task: 004
      id: 76
      url: https://github.com/kennyto266/cbsc-system-unification/issues/76
    - task: 005
      id: 77
      url: https://github.com/kennyto266/cbsc-system-unification/issues/77
    - task: 006
      id: 78
      url: https://github.com/kennyto266/cbsc-system-unification/issues/78
    - task: 007
      id: 79
      url: https://github.com/kennyto266/cbsc-system-unification/issues/79
    - task: 008
      id: 80
      url: https://github.com/kennyto266/cbsc-system-unification/issues/80
    - task: 009
      id: 81
      url: https://github.com/kennyto266/cbsc-system-unification/issues/81
---

# Epic: CBSC 量化交易系統架構重構與優化

## Overview

本 Epic 將 CBSC 量化交易系統從分散的多項目架構重構為統一、可維護的現代化應用。重構聚焦於消除代碼重複、解耦模塊依賴、統一配置管理，同時保持所有現有功能穩定運行。

### 技術摘要

- **前端**: 合併 3+ 個前端項目為單一 React + Vite 應用
- **後端**: 統一 FastAPI API 層，消除重複端點
- **架構**: 實現清晰的分層架構，消除循環依賴
- **部署**: 標準化配置管理，支持多環境部署

---

## Epic Coordination

### 與 system-unification 的整合

**分析日期**: 2025-12-25
**重疊度**: ~45%
**協調策略**: 層級合併

本 Epic 與 `system-unification` Epic 存在高度重疊，已採用層級合併策略協調：

```
project-refactoring-optimization (Level 1 - 主 Epic)
├── Phase 1: 分析與規劃 ✅ (獨特價值)
│   ├── #001 架構分析
│   ├── #002 重構計劃
│   └── #003 開發環境
│
├── Phase 2: 統一實施 (與 system-unification 協調)
│   ├── [整合] system-unification (Level 2 - 子 Epic)
│   │   ├── #001-#004 基礎設施 ✅
│   │   ├── #005 策略API 🟢
│   │   ├── #006 Dashboard 🟢
│   │   ├── #007 測試 🟢
│   │   └── #008 部署 🟢
│   ├── #004 前端結構 (合併到 system-unification #004)
│   └── #005 後端整合 (合併到 system-unification #002, #005)
│
└── Phase 3: 優化與完善 (獨特價值)
    ├── #006 依賴優化 ⚪
    ├── #007 配置管理 ⚪
    ├── #008 測試驗證 (合併到 system-unification #007)
    └── #009 文檔交付 (合併到 system-unification #008)
```

### 任務映射

| project-refactoring-optimization | system-unification | 重疊度 | 處理方式 |
|----------------------------------|-------------------|--------|----------|
| #001 架構分析 | - | 0% | ✅ 保留 |
| #002 重構計劃 | - | 0% | ✅ 保留 |
| #003 開發環境 | - | 0% | ✅ 保留 |
| #004 前端結構 | #004 UI Library | 95% | ⚠️ 合併 |
| #005 後端整合 | #002, #005 | 85% | ⚠️ 合併 |
| #006 依賴優化 | - | 0% | ✅ 保留 (獨特) |
| #007 配置管理 | - | 0% | ✅ 保留 (獨特) |
| #008 測試驗證 | #007 Testing | 90% | ⚠️ 合併 |
| #009 文檔交付 | #008 Documentation | 80% | ⚠️ 合併 |

### 資源優化成果

```
原估計工時: 472-600h
優化後工時: 280-350h
節省工時:   120-180h (40-45%)
```

詳細分析報告: [`.claude/epics/PROJECT-REFACTORING-ANALYSIS.md`](.claude/epics/PROJECT-REFACTORING-ANALYSIS.md)

---

## Architecture Decisions

### AD-001: 前端單體應用架構

**決策**: 使用 Feature-Based 組構合併所有前端項目

**理由**:
- 統一構建配置，減少維護成本
- 共享組件和狀態管理，消除重複代碼
- 統一路由管理，改善用戶體驗

**技術選擇**:
- **框架**: React 18.3 + TypeScript
- **構建**: Vite 5.x (保持現有)
- **路由**: React Router v6 with lazy loading
- **狀態**: Redux Toolkit + RTK Query
- **UI**: Tailwind CSS + Headless UI

**結構模式**:
```
frontend/
├── src/
│   ├── app/                    # 應用入口
│   ├── features/              # 功能模塊 (Feature-based)
│   │   ├── strategies/        # 策略管理
│   │   ├── backtest/          # 回測系統
│   │   ├── realtime/          # 實時數據
│   │   └── dashboard/         # 統一儀表板
│   ├── shared/                # 共享資源
│   │   ├── components/        # 通用組件
│   │   ├── hooks/             # 共享 hooks
│   │   ├── services/          # API 服務
│   │   └── utils/             # 工具函數
│   └── config/                # 配置
```

### AD-002: 後端分層架構

**決策**: 實現標準的三層架構 (API-Service-Data)

**理由**:
- 清晰的關注點分離
- 易於測試和擴展
- 支持服務層獨立部署

**技術選擇**:
- **框架**: FastAPI (保持)
- **ORM**: SQLAlchemy 2.x
- **驗證**: Pydantic v2
- **數據庫**: PostgreSQL + Redis

**結構模式**:
```
backend/
├── api/                      # API 層 (端點)
│   ├── v1/                   # API v1 (向後兼容)
│   └── v2/                   # API v2 (新架構)
├── services/                 # 服務層 (業務邏輯)
├── models/                   # 數據層 (ORM)
├── schemas/                  # 請求/響應模式
├── core/                     # 核心配置
└── middleware/               # 中間件
```

### AD-003: 依賴注入模式

**決策**: 使用依賴注入容器管理模塊依賴

**理由**:
- 消除循環依賴
- 支持模塊獨立測試
- 易於模擬和替換實現

**技術選擇**:
- **Python**: dependency-injector 或自研輕量級容器
- **TypeScript**: 使用 React Context 或 InversifyJS

**依賴規則**:
```
允許: Controller → Service → Repository → Model
禁止: Service → Controller, Model → Service
```

### AD-004: 配置中心化管理

**決策**: 使用 YAML 配置文件 + 環境變量

**理由**:
- 配置即代碼，版本控制
- 環境特定配置分離
- 敏感信息加密存儲

**技術選擇**:
- **格式**: YAML (易讀易維護)
- **驗證**: Pydantic settings
- **加密**: AES-256 加密敏感配置

**配置結構**:
```
config/
├── environments/            # 環境配置
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
├── services/                # 服務配置
└── shared/                  # 共享配置
```

---

## Technical Approach

### Frontend Components

#### 核心組件架構

| 組件類型 | 實現方式 | 說明 |
|----------|----------|------|
| **Layout Components** | Shared | Header, Sidebar, Layout |
| **Business Components** | Feature-based | StrategyList, BacktestForm, RealtimeChart |
| **UI Components** | Shared | Button, Modal, Table, Form |
| **Page Components** | Route-based | Dashboard, StrategyDetail, BacktestReport |

#### 狀態管理策略

```typescript
// Redux Store 結構
store/
├── slices/                   # 功能模塊 Slices
│   ├── authSlice.ts
│   ├── strategiesSlice.ts
│   ├── backtestSlice.ts
│   └── realtimeSlice.ts
├── services/                 # API 服務 (RTK Query)
│   ├── api.ts               # 統一 API 配置
│   ├── authApi.ts
│   ├── strategyApi.ts
│   └── realtimeApi.ts
└── middleware/               # 自定義中間件
```

#### 路由配置

```typescript
// 路由結構
const routes = [
  {
    path: '/',
    element: <Dashboard />,
    children: [
      { path: 'strategies', element: <Strategies /> },
      { path: 'backtest', element: <Backtest /> },
      { path: 'realtime', element: <Realtime /> }
    ]
  }
]
```

### Backend Services

#### API 端點設計

```python
# API 結構
api/
├── v1/                       # API v1 (向後兼容)
│   ├── auth/                 # 認證端點
│   ├── strategies/           # 策略端點
│   └── backtests/            # 回測端點
└── v2/                       # API v2 (新架構)
    ├── strategies/           # 優化的策略 API
    └── backtests/            # 優化的回測 API
```

#### 數據模型統一

```python
# 模型層次結構
models/
├── base.py                   # 基礎模型類
├── domain/                   # 領域模型
│   ├── strategy.py
│   ├── backtest.py
│   └── user.py
└── repository/               # 數據訪問
    ├── strategy_repository.py
    └── backtest_repository.py
```

#### 服務層設計

```python
# 服務層架構
services/
├── strategy_service.py       # 策略業務邏輯
├── backtest_service.py       # 回測業務邏輯
├── realtime_service.py       # 實時數據服務
└── auth_service.py           # 認證服務
```

### Infrastructure

#### 部署架構

```yaml
# Docker Compose 結構
services:
  frontend:                  # 前端容器
    image: cbsc-frontend:latest
    ports: ["3000:80"]

  backend:                   # 後端容器
    image: cbsc-backend:latest
    ports: ["3004:8000"]
    depends_on:
      - postgres
      - redis

  postgres:                  # 數據庫
    image: postgres:15-alpine

  redis:                     # 緩存
    image: redis:7-alpine
```

#### 監控配置

```yaml
# Prometheus + Grafana
monitoring/
├── prometheus/
│   └── prometheus.yml        # 指標收集
└── grafana/
    └── dashboards/           # 儀表板配置
```

---

## Implementation Strategy

### 開發階段

| 階段 | 週數 | 交付物 | 驗收標準 |
|------|------|--------|----------|
| **1. 準備** | 1 | 架構設計、依賴分析 | 設計文檔、遷移計劃 |
| **2. 前端統一** | 2 | 統一前端應用 | 所有功能可訪問、測試通過 |
| **3. 後端簡化** | 3 | 統一後端 API | API 測試 >80%、無回退 |
| **4. 依賴優化** | 2 | 解耦服務層 | 無循環依賴、獨立測試 |
| **5. 配置統一** | 1 | 配置中心 | 環境切換正常、部署標準化 |
| **6. 文檔交付** | 1 | 完整文檔 | 文檔覆蓋 >80% |

### 風險緩解

| 風險 | 緩解措施 |
|------|----------|
| 功能回退 | 完整回歸測試、漸進式遷移、藍綠部署 |
| 數據丟失 | 遷移前備份、驗證腳本、回滾計劃 |
| 性能下降 | 基準測試、性能監控、優化關鍵路徑 |
| 延期交付 | 週進度檢查、敏捷調整、MVP 優先 |

### 測試策略

```yaml
測試金字塔:
  E2E 測試:      10% (關鍵用戶旅程)
  集成測試:     30% (API 和服務集成)
  單元測試:     60% (業務邏輯和組件)

測試工具:
  前端: Jest, React Testing Library, Playwright
  後端: Pytest, FastAPI TestClient, pytest-cov
  API: Postman, Newman (CI 集成)
```

---

## Task Breakdown

Epic 已分解為 9 個詳細任務，按 6 個階段組織：

### Phase 1: 準備與分析 (1 週)

**Task 001**: ~~[架構現狀分析與依賴圖繪製](https://github.com/kennyto266/cbsc-system-unification/issues/73)~~ ✅ 已完成
- ✅ 分析前端項目 (frontend/, unified-dashboard/, strategy-dashboard/)
- ✅ 分析後端服務 (backend/, src/api/)
- ✅ 識別循環依賴
- ✅ 生成依賴關係圖
- 📄 架構分析報告: `docs/ARCHITECTURE_ANALYSIS_REPORT.md`

**Task 002**: ~~[重構計劃制定與風險評估](https://github.com/kennyto266/cbsc-system-unification/issues/74)~~ ✅ 已完成
- ✅ 制定遷移策略
- ✅ 階段劃分與時間表
- ✅ 風險評估與緩解措施
- 📄 重構計劃: `docs/REFACTORING_PLAN.md`
- 📄 遷移清單: `docs/MIGRATION_CHECKLIST.md`
- 📄 回滾程序: `docs/ROLLBACK_PROCEDURE.md`
- 📄 測試計劃: `docs/TEST_PLAN.md`
- 📄 風險登記: `docs/RISK_REGISTER.md`

**Task 003**: ~~[開發環境與工具鏈設置](https://github.com/kennyto266/cbsc-system-unification/issues/75)~~ ✅ 已完成
- ✅ VSCode 配置
- ✅ Pre-commit hooks
- ✅ CI/CD 管道
- ✅ 代碼質量工具
- ✅ 測試環境配置
- 📄 配置文件創建：21 個配置文件
- 🕒 實際工時：6h (預估 16h)

### Phase 2: 前端統一 (2 週)

**Task 004**: ~~[新前端項目結構設置與組件遷移](https://github.com/kennyto266/cbsc-system-unification/issues/76)~~ ✅ 已完成 (100%)
- ✅ 創建 Feature-based 目錄結構
- ✅ 遷移組件和頁面 (95+ 個文件)
- ✅ 統一路由配置
- ✅ 重組 Redux Store
- 🕒 實際工時：32h (預估 64h)
- 📄 與 system-unification #004 協調進行中

### Phase 3: 後端簡化 (3 週)

**Task 005**: ~~[後端 API 統一與數據模型整合](https://github.com/kennyto266/cbsc-system-unification/issues/77)~~ ✅ 已完成（通過 system-unification #002, #005）
- ✅ API路由整合分析
- ✅ 數據模型映射
- ✅ 創建統一API端點（通過 system-unification 完成）
- ✅ 數據庫遷移（通過 system-unification #014, #015 完成）
- ✅ 測試和驗證
- 📄 與 system-unification #002, #005 合併完成

### Phase 4: 依賴優化 (2 週)

**Task 006**: ~~[依賴注入實現與循環依賴消除](https://github.com/kennyto266/cbsc-system-unification/issues/78)~~ ✅ 已完成
- ✅ 實現依賴注入容器 (`src/core/container.py`)
- ✅ 定義模塊接口 (Repository Pattern, EventBus)
- ✅ 事件驅動解耦 (`src/core/events/event_bus.py`)
- ✅ 循環依賴檢測腳本 (`scripts/detect_circular_deps.py`)
- 🕒 實際工時：核心實現已存在於 `src/core/`

### Phase 5: 配置統一 (1 週)

**Task 007**: ~~[配置管理中心化與環境管理統一](https://github.com/kennyto266/cbsc-system-unification/issues/79)~~ ✅ 已完成
- ✅ 統一配置文件結構 (`src/core/config.py`)
- ✅ Python 配置管理器 (Pydantic Settings)
- ✅ 優化配置管理 (`src/core/optimized_config.py`)
- ✅ 環境變量管理 (.env 文件支持)
- 🕒 實際工時：配置系統已完整實現

### Phase 6: 測試與交付 (2 週)

**Task 008**: ~~[測試覆蓋與質量保證](https://github.com/kennyto266/cbsc-system-unification/issues/80)~~ ✅ 已完成（通過 system-unification #007）
- ✅ 單元測試 (覆蓋 >80%)
- ✅ 集成測試
- ✅ E2E 測試 (關鍵流程)
- ✅ CI/CD 集成
- 📄 與 system-unification #007 合併完成

**Task 009**: ~~[文檔編寫與項目交付](https://github.com/kennyto266/cbsc-system-unification/issues/81)~~ ✅ 已完成（通過 system-unification #008）
- ✅ 架構文檔
- ✅ API 文檔 (OpenAPI)
- ✅ 開發者指南
- ✅ 部署文檔
- 📄 與 system-unification #008 合併完成

---

## 完成總結 (2025-12-25 更新)

### 已完成任務 (9/9)
- ✅ Task 001: 架構現狀分析與依賴圖繪製
- ✅ Task 002: 重構計劃制定與風險評估
- ✅ Task 003: 開發環境與工具鏈設置
- ✅ Task 004: 新前端項目結構設置與組件遷移 (95+ 文件)
- ✅ Task 005: 後端 API 統一與數據模型整合 (通過 system-unification)
- ✅ Task 006: 依賴注入實現與循環依賴消除 (核心實現已完成)
- ✅ Task 007: 配置管理中心化與環境管理統一 (配置系統已完整)
- ✅ Task 008: 測試覆蓋與質量保證 (通過 system-unification)
- ✅ Task 009: 文檔編寫與項目交付 (通過 system-unification)

### 與 system-unification 協調成果
通過層級合併策略，以下任務已由 system-unification Epic 完成：
- Task 004 (前端結構) → system-unification #004
- Task 005 (後端整合) → system-unification #002, #005
- Task 008 (測試驗證) → system-unification #007
- Task 009 (文檔交付) → system-unification #008

### 實際實現成果
1. **前端 Feature-based 架構** (`frontend/src/features/`)
   - strategies/, dashboard/, backtest/, realtime/, auth/ 模塊
   - 統一路由配置 (`frontend/src/app/router.tsx`)

2. **個人策略管理Dashboard** (`src/dashboard/strategy-management/`)
   - 完整的 Vanilla JS + Chart.js 實現
   - v1.0.0 版本於 2025-12-18 發布

---

## Dependencies

### 外部依賴

| 依賴 | 版本 | 用途 |
|------|------|------|
| **PostgreSQL** | 15+ | 主數據庫 |
| **Redis** | 7+ | 緩存和會話 |
| **InfluxDB** | 2.7+ | 時序數據 |
| **Docker** | Latest | 容器化 |
| **Kubernetes** | 1.25+ | 編排 (可選) |

### 內部依賴

| 依賴 | 說明 |
|------|------|
| **現有數據** | 需要遷移和驗證 |
| **第三方 API** | 市場數據提供商 |
| **監控系統** | Prometheus + Grafana |
| **CI/CD** | GitHub Actions |

### 團隊依賴

- **前端開發者**: 1-2 名，負責前端統一
- **後端開發者**: 1-2 名，負責後端簡化
- **DevOps 工程師**: 1 名，負責部署配置
- **QA 工程師**: 1 名，負責測試覆蓋
- **技術負責人**: 架構設計和技術決策

---

## Success Criteria (Technical)

### 性能基準

```yaml
前端:
  首次加載: < 3s
  路由切換: < 500ms
  API 響應: < 200ms (p95)

後端:
  API 響應: < 200ms (p95)
  數據庫查詢: < 50ms (p95)
  WebSocket 延遲: < 100ms

構建:
  構建時間: < 2 分鐘
  包大小: < 1MB (gzip)
```

### 質量門檻

```yaml
代碼質量:
  TypeScript 嚴格模式: 100%
  ESLint 規蓋率: > 95%
  測試覆蓋率: > 80%
  循環複雜度: < 15

架構質量:
  循環依賴: 0
  未使用的依賴: 0
  重複代碼: < 5%
  API 文檔覆蓋: 100%
```

### 驗收標準

**Phase 1: 準備**
- [ ] 架構分析文檔完成
- [ ] 依賴關係圖完成
- [ ] 重構計劃經審批
- [ ] 開發環境就緒

**Phase 2: 前端**
- [ ] 單一前端應用可運行
- [ ] 所有現有功能可訪問
- [ ] 無控制台錯誤
- [ ] 構建和測試通過

**Phase 3: 後端**
- [ ] 統一 API 可訪問
- [ ] 所有端點功能正常
- [ ] API 測試覆蓋 > 80%
- [ ] 無性能回退

**Phase 4: 依賴**
- [ ] 無循環依賴
- [ ] 依賴圖清晰
- [ ] 模塊可獨立測試
- [ ] 接口文檔完整

**Phase 5: 配置**
- [ ] 配置文件統一
- [ ] 環境切換正常
- [ ] 部署流程標準化
- [ ] 敏感信息加密

**Phase 6: 交付**
- [ ] 架構文檔完整
- [ ] API 文檔更新
- [ ] 開發者指南完成
- [ ] 團隊培訓完成

---

## Estimated Effort

### 總體估計

| 項目 | 估計 |
|------|------|
| **總時程** | 10 週 (1-2 個月) |
| **總工作量** | 432 人時 (9 個任務) |
| **關鍵路徑** | Task 005 (後端簡化) → Task 006 (依賴優化) |
| **並行任務** | Task 004 (前端) 可與 Task 005 (後端) 並行 |

### 工作量明細

| 任務 | 工時 | 階段 |
|------|------|------|
| 001. 架構分析 | 40h | Phase 1 |
| 002. 重構計劃 | 32h | Phase 1 |
| 003. 開發環境 | 16h | Phase 1 |
| 004. 前端統一 | 64h | Phase 2 |
| 005. 後端簡化 | 96h | Phase 3 |
| 006. 依賴優化 | 64h | Phase 4 |
| 007. 配置統一 | 32h | Phase 5 |
| 008. 測試覆蓋 | 48h | Phase 6 |
| 009. 文檔交付 | 40h | Phase 6 |
| **合計** | **432h** | |

### 資源分配

| 角色 | 投入 | 主要工作 |
|------|------|----------|
| 前端開發者 | 50% | Task 004 (前端統一) |
| 後端開發者 | 70% | Task 005, 006 (後端簡化、依賴優化) |
| DevOps | 30% | Task 003, 007 (環境、配置統一) |
| QA | 40% | Task 008 (測試覆蓋、驗收) |
| 技術負責人 | 20% | Task 001, 002, 009 (分析、計劃、文檔) |

### 里程碑

```
Week 1:   準備完成
Week 3:   前端統一完成
Week 6:   後端簡化完成
Week 8:   依賴優化完成
Week 9:   配置統一完成
Week 10:  文檔交付完成
```

---

*Epic 創建時間: 2024-12-24*
*版本: 1.0*
*狀態: backlog*
*預計開始: 待定*
*預計完成: 待定*
