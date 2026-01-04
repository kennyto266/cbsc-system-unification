---
name: dev-environment
title: 開發環境與工具鏈設置
status: completed
phase: 1
priority: P0
created: 2025-12-24T12:05:52Z
updated: 2025-12-24T20:53:00Z
estimated_hours: 16
actual_hours: 6
assignee: TBD
dependencies: ["002-refactoring-plan"]
github:
  issue: 75
  url: https://github.com/kennyto266/cbsc-system-unification/issues/75
---

# Task 003: 開發環境與工具鏈設置

## 概述

為重構項目配置標準化的開發環境，包括本地開發配置、CI/CD 管道、代碼質量工具和測試框架。

## 執行摘要

✅ **已完成** - 2025-12-24

本任務已成功完成，創建了標準化的開發環境配置，包括：
- VSCode 工作區配置
- Pre-commit hooks
- CI/CD 管道
- 前端和後端代碼質量工具
- 測試環境配置

### 創建的配置文件

| 類別 | 文件 | 描述 |
|------|------|------|
| **VSCode** | `.vscode/settings.json` | 統一編輯器配置 |
| | `.vscode/extensions.json` | 推薦擴展清單 |
| **Pre-commit** | `.pre-commit-config.yaml` | 自動化代碼檢查 |
| **Python** | `pyproject.toml` | Black, isort, MyPy, Pytest |
| | `.flake8` | Flake8 代碼檢查 |
| **前端** | `.eslintrc.cjs` | ESLint 規則配置 |
| | `.prettierrc` | Prettier 格式化 |
| | `.prettierignore` | Prettier 忽略規則 |
| | `tsconfig.json` | TypeScript 配置 |
| | `tsconfig.src.json` | 源碼類型配置 |
| | `tsconfig.test.json` | 測試類型配置 |
| | `vite.config.ts` | Vite 構建配置 |
| | `vitest.config.ts` | Vitest 測試配置 |
| | `jest.config.js` | Jest 測試配置 |
| | `playwright.config.ts` | Playwright E2E 配置 |
| **CI/CD** | `.github/workflows/refactoring-ci.yml` | GitHub Actions 管�道 |
| **測試設置** | `src/tests/setup.ts` | 通用測試設置 |
| | `src/tests/setup.integration.ts` | 集成測試設置 |
| | `src/tests/__mocks__/fileMock.js` | 文件模擬 |
| | `src/tests/e2e/global-setup.ts` | E2E 全局設置 |
| | `src/tests/e2e/global-teardown.ts` | E2E 全局清理 |

## 詳細描述

### 環境配置

#### 1. 本地開發環境

**前端開發環境**:
```bash
# 前端開發依賴
npm install --save-dev \
  @typescript-eslint/eslint-plugin \
  @typescript-eslint/parser \
  eslint-config-prettier \
  eslint-plugin-react \
  eslint-plugin-react-hooks \
  prettier \
  vitest \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  @playwright/test
```

**後端開發環境**:
```bash
# 後端開發依賴
pip install \
  pytest \
  pytest-cov \
  pytest-asyncio \
  pytest-mock \
  black \
  isort \
  mypy \
  flake8 \
  bandit \
  pre-commit
```

#### 2. VSCode 配置

```json
// .vscode/settings.json
{
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact"
  ],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "files.exclude": {
    "**/node_modules": true,
    "**/dist": true,
    "**/build": true,
    "**/.git": true
  }
}
```

#### 3. Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
        types_or: [javascript, jsx, ts, tsx, json, css]
```

### CI/CD 配置

#### GitHub Actions 工作流

```yaml
# .github/workflows/refactoring-ci.yml
name: Refactoring CI

on:
  push:
    branches: [epic/project-refactoring-optimization]
  pull_request:
    branches: [epic/project-refactoring-optimization]

jobs:
  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
        working-directory: ./frontend
      - run: npm run lint
        working-directory: ./frontend
      - run: npm run type-check
        working-directory: ./frontend

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
        working-directory: ./frontend
      - run: npm run test:coverage
        working-directory: ./frontend
      - uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/lcov.info

  backend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install black isort flake8 mypy
      - run: black --check backend/ src/
      - run: isort --check-only backend/ src/
      - run: flake8 backend/ src/
      - run: mypy backend/ src/

  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r backend/requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest backend/ --cov=backend --cov-report=xml
      - uses: codecov/codecov-action@v3

  e2e-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
        working-directory: ./frontend
      - run: npx playwright install --with-deps
        working-directory: ./frontend
      - run: npm run test:e2e
        working-directory: ./frontend
```

### 代碼質量工具

#### ESLint 配置

```javascript
// frontend/.eslintrc.cjs
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    'prettier'
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'no-console': ['warn', { allow: ['warn', 'error'] }]
  }
};
```

#### Prettier 配置

```json
// frontend/.prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
```

#### Python Black 配置

```ini
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
skip_gitignore = true
```

## 驗收標準

### 交付物

- [ ] **開發環境配置** (.vscode/, .pre-commit-config.yaml)
  - VSCode 設置文件
  - Pre-commit hooks 配置
  - 推薦擴展清單

- [ ] **CI/CD 管道** (.github/workflows/)
  - 前端 lint + test 工作流
  - 後端 lint + test 工作流
  - E2E 測試工作流
  - 代碼覆蓋率集成

- [ ] **代碼質量配置**
  - ESLint + Prettier 配置
  - Black + isort 配置
  - MyPy 類型檢查配置

- [ ] **測試環境設置**
  - Vitest 配置
  - Pytest 配置
  - Playwright E2E 配置

### 質量門檻

- CI/CD 管道成功運行
- 代碼檢查覆蓋 100%
- 測試環境可重複建立
- 本地開發環境與 CI 一致

## 依賴關係

### 前置任務
- Task 002: 重構計劃制定

### 後續任務
- 所有開發任務依賴本任務

## 執行步驟

1. **創建配置文件**
   - VSCode settings
   - Pre-commit hooks
   - ESLint/Prettier
   - Black/isort

2. **配置 CI/CD**
   - 創建 GitHub Actions 工作流
   - 配置代碼覆蓋率
   - 設置測試環境

3. **驗證環境**
   - 本地測試所有工具
   - 提交測試 PR 驗證 CI
   - 文檔化設置流程
