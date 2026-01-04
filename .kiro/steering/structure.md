# Project Structure

## Organization Philosophy

混合式架構：**領域驅動的模組化設計** + **API版本化**，支持從單體到微服務的平滑演进

## Directory Patterns

### Core Backend (`src/`)
**Location**: `src/`
**Purpose**: 核心業務邏輯與數據處理
**Example**: 策略計算、回測引擎、風險管理

```
src/
├── api/          # FastAPI應用和路由
├── backtest/     # 回測引擎與風險管理
├── strategies/   # 交易策略實現
├── services/     # 業務服務層
└── utils/        # 通用工具函數
```

### Frontend Application (`frontend/`)
**Location**: `frontend/`
**Purpose**: React應用與用戶界面
**Example**: 策略儀表板、圖表組件、用戶管理

```
frontend/
├── src/
│   ├── components/  # React組件
│   ├── pages/       # 頁面組件
│   ├── services/    # API服務
│   ├── store/       # Redux狀態管理
│   └── utils/       # 前端工具
```

### API Versioning (`src/api/`)
**Location**: `src/api/`
**Purpose**: 版本化的API端點
**Example**: v2統一架構、v1兼容接口

```
api/
├── strategies/     # v2.0 新架構
├── v2/            # v2路由器
├── auth_endpoints.py
├── user_endpoints.py
└── *_endpoints.py  # v0.x 向後兼容
```

## Naming Conventions

### Files
- **Python**: `snake_case.py` (例: `enhanced_backtest_engine.py`)
- **TypeScript**: `PascalCase.tsx` (組件), `camelCase.ts` (工具)
- **配置文件**: `kebab-case.config.js`

### Components
- **React組件**: PascalCase (例: `StrategyDashboard.tsx`)
- **函數組件**: useCamelCase hook (例: `useStrategyData`)
- **類型定義**: PascalCase + `Type`/`Interface` 後綴

### Functions
- **Python**: snake_case (例: `calculate_sharpe_ratio`)
- **TypeScript**: camelCase (例: `fetchStrategyData`)

## Import Organization

### Python Backend
```python
# 標準庫
import os
import sys
from datetime import datetime

# 第三方庫
import pandas as pd
import numpy as np
from fastapi import FastAPI

# 本地模組 - 絕對導入
from src.backtest.enhanced_backtest_engine import BacktestEngine
from src.strategies.technical_indicators import RSIStrategy

# 相對導入 - 僅用於同級模組
from .utils import calculate_metrics
```

### TypeScript Frontend
```typescript
// React相關 - 優先
import { useState, useEffect } from 'react'
import { BrowserRouter as Router } from 'react-router-dom'

// Redux/RTK
import { useAppDispatch, useAppSelector } from '@/store/hooks'

// 絕對路徑導入 (使用 @/ 別名)
import { StrategyCard } from '@/components/Strategy'
import { fetchStrategies } from '@/services/strategyApi'

// 相對路徑導入 - 僅用於同級
import { LocalComponent } from './LocalComponent'
import './ComponentStyles.css'
```

**Path Aliases**:
- `@/`: 映射到 `frontend/src/`

## Code Organization Principles

### Layer Architecture
```
┌─────────────────┐
│   Presentation  │ ← React Components, Pages
├─────────────────┤
│    Business     │ ← Services, Strategy Logic
├─────────────────┤
│     Data        │ ← Models, Repositories, Cache
└─────────────────┘
```

### Dependency Rules
1. **單向依賴**: 上層可依賴下層，禁止反向依賴
2. **跨層通信**: 通過服務層接口，避免直接訪問
3. **循環依賴**: 使用依賴注入或事件系統解耦

### Module Boundaries
- **策略模組**: 獨立的策略邏輯，可插拔設計
- **認證模組**: 統一的用戶認證與授權
- **數據模組**: 抽象的數據訪問層
- **API模組**: 版本化的接口定義

### API Evolution Pattern
```python
# v2 - 新統一架構
/api/v2/strategies/          # 資源名複數
/api/v2/strategies/{id}      # 特定資源

# v1 - 當前穩定版
/api/v1/strategies/
/api/v1/strategies/personal/

# v0 - 向後兼容
/api/personal-strategies/    # 舊版命名
/api/strategies/             # CBSC特定
```

### Testing Structure
```
tests/
├── unit/          # 單元測試
├── integration/   # 集成測試
├── e2e/          # 端到端測試
└── fixtures/     # 測試數據
```

---
_記錄模式，而非文件樹。遵循現有模式的新文件不需要更新此文檔_