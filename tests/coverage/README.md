# 测试覆盖率报告生成指南

## 概述

本文档描述了如何为CBSC量化交易策略管理系统生成全面的测试覆盖率报告。

## 覆盖率目标

### 整体目标
- **代码行覆盖率**: ≥80%
- **分支覆盖率**: ≥75%
- **函数覆盖率**: ≥85%
- **语句覆盖率**: ≥80%

### 分模块目标
- 核心业务逻辑: ≥90%
- API端点: ≥85%
- UI组件: ≥80%
- 工具函数: ≥90%

## 前端覆盖率报告

### 1. Jest覆盖率配置

Jest已经在 `jest.config.js` 中配置了覆盖率收集：

```javascript
module.exports = {
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html', 'json'],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
}
```

### 2. 生成覆盖率报告

```bash
# 进入前端目录
cd frontend

# 生成完整覆盖率报告
npm run test:coverage

# 生成覆盖率报告并监听模式
npm run test:coverage -- --watch

# 生成覆盖率报告（持续集成模式）
npm run test:ci
```

### 3. 覆盖率报告查看

生成的报告位于：
- HTML报告: `frontend/coverage/lcov-report/index.html`
- LCOV数据: `frontend/coverage/lcov.info`
- JSON数据: `frontend/coverage/coverage-final.json`
- 文本报告: 直接输出到控制台

## 后端覆盖率报告

### 1. Pytest覆盖率配置

覆盖率配置在 `pytest.ini` 中：

```ini
[tool:pytest]
addopts = --cov=src --cov-report=html --cov-report=term --cov-report=lcov --cov-report=json
```

### 2. 生成覆盖率报告

```bash
# 安装覆盖率工具
pip install coverage pytest-cov

# 运行测试并生成覆盖率
pytest --cov=src --cov-report=html --cov-report=term

# 只看特定模块的覆盖率
pytest --cov=src.api.strategies --cov-report=html

# 生成分支覆盖率
pytest --cov=src --cov-branch --cov-report=html
```

### 3. 覆盖率报告位置

- HTML报告: `htmlcov/index.html`
- LCOV数据: `coverage.lcov`
- 终端报告: 直接输出

## 合并覆盖率报告

### 使用工具合并前后端覆盖率

```bash
# 安装合并工具
npm install -g combine-coverage

# 合并覆盖率报告
combine-coverage \
  frontend/coverage/coverage-final.json \
  coverage.json \
  coverage/merged-coverage.json

# 生成合并后的HTML报告
nyc report --reporter=html --temp-dir=.nyc_output --report-dir=merged-coverage
```

### Python脚本合并覆盖率

创建 `scripts/merge-coverage.py`:

```python
#!/usr/bin/env python3
import json
import os
from pathlib import Path

def load_json_coverage(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def merge_coverage(frontend_cov, backend_cov):
    # 合并逻辑
    merged = {
        "total": {},
        "files": {}
    }

    # 处理前端覆盖率（JavaScript/TypeScript）
    for file_path, coverage in frontend_cov.get('files', {}).items():
        merged['files'][file_path] = coverage

    # 处理后端覆盖率（Python）
    for file_path, coverage in backend_cov.get('files', {}).items():
        merged['files'][file_path] = coverage

    # 计算总体覆盖率
    total_statements = sum(f.get('s', {}).get('total', 0) for f in merged['files'].values())
    total_covered = sum(f.get('s', {}).get('covered', 0) for f in merged['files'].values())

    merged['total'] = {
        'statements': {
            'total': total_statements,
            'covered': total_covered,
            'pct': round((total_covered / total_statements * 100) if total_statements > 0 else 0, 2)
        }
    }

    return merged

def main():
    # 生成前端覆盖率
    os.system('cd frontend && npm run test:coverage -- --silent --json --outputFile=coverage.json')

    # 生成后端覆盖率
    os.system('pytest --cov=src --cov-report=json --cov-fail-under=0')

    # 加载覆盖率数据
    frontend_cov = load_json_coverage('frontend/coverage.json')
    backend_cov = load_json_coverage('coverage.json')

    # 合并覆盖率
    merged_cov = merge_coverage(frontend_cov, backend_cov)

    # 保存合并后的覆盖率
    with open('coverage/merged-coverage.json', 'w') as f:
        json.dump(merged_cov, f, indent=2)

    print(f"合并后的总覆盖率: {merged_cov['total']['statements']['pct']}%")

if __name__ == '__main__':
    main()
```

## 覆盖率报告集成到CI/CD

### GitHub Actions集成

```yaml
- name: Generate Coverage Report
  run: |
    # 前端覆盖率
    cd frontend && npm run test:coverage

    # 后端覆盖率
    cd .. && pytest --cov=src --cov-report=lcov

    # 合并覆盖率
    python scripts/merge-coverage.py

- name: Upload Coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage/merged-coverage.lcov
    flags: unittests
    name: codecov-umbrella
    fail_ci_if_error: true
```

## 覆盖率徽章

在README.md中添加覆盖率徽章：

```markdown
![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)
![Frontend Coverage](https://img.shields.io/badge/frontend-85%25-brightgreen)
![Backend Coverage](https://img.shields.io/badge/backend-75%25-brightgreen)
```

## 覆盖率质量门禁

### Pre-commit钩子

创建 `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: coverage-check
        name: Coverage check
        entry: scripts/check-coverage.sh
        language: script
        pass_filenames: false
        always_run: true
```

### 覆盖率检查脚本

创建 `scripts/check-coverage.sh`:

```bash
#!/bin/bash

# 生成覆盖率
npm run test:coverage > /dev/null 2>&1
pytest --cov=src --cov-report=json > /dev/null 2>&1

# 检查覆盖率阈值
FRONTEND_COVERAGE=$(node -p "JSON.parse(require('fs').readFileSync('frontend/coverage/coverage-summary.json')).total.lines.pct")
BACKEND_COVERAGE=$(node -p "JSON.parse(require('fs').readFileSync('coverage.json')).totals.percent_covered")

MIN_COVERAGE=80

if (( $(echo "$FRONTEND_COVERAGE < $MIN_COVERAGE" | bc -l) )); then
    echo "❌ Frontend coverage ($FRONTEND_COVERAGE%) is below threshold ($MIN_COVERAGE%)"
    exit 1
fi

if (( $(echo "$BACKEND_COVERAGE < $MIN_COVERAGE" | bc -l) )); then
    echo "❌ Backend coverage ($BACKEND_COVERAGE%) is below threshold ($MIN_COVERAGE%)"
    exit 1
fi

echo "✅ All coverage checks passed!"
```

## 覆盖率优化建议

### 1. 识别未覆盖的代码

```bash
# Jest: 查看未覆盖的行
npm run test:coverage -- --verbose

# Pytest: 查看未覆盖的行
pytest --cov=src --cov-report=term-missing
```

### 2. 优先级测试策略

1. **高优先级**（必须覆盖）：
   - 核心业务逻辑
   - 安全相关代码
   - 错误处理
   - API端点

2. **中优先级**（建议覆盖）：
   - 工具函数
   - 数据转换
   - 组件交互

3. **低优先级**（可选覆盖）：
   - UI纯展示代码
   - 开发工具
   - 调试代码

### 3. 测试覆盖率最佳实践

- 为每个新功能编写测试
- 在修复bug时添加回归测试
- 定期审查和维护测试
- 使用突变测试验证测试质量
- 保持测试代码的可读性和可维护性

## 报告示例输出

```
================ Coverage Report ===============
File                           |   Stmts   |  Miss |   Cover
--------------------------------|-----------|-------|---------
src/api/main.py               |     100   |    20   |   80.00%
src/strategies/service.py     |     200   |    40   |   80.00%
src/utils/helpers.py          |      50   |     5   |   90.00%
--------------------------------|-----------|-------|---------
TOTAL                         |     350   |    65   |   81.43%

================ Coverage Threshold ===========
Required coverage: 80%
Actual coverage: 81.43%
Status: PASSED ✅
```

## 持续监控

1. **每日报告**: 自动生成并发送覆盖率报告
2. **趋势分析**: 跟踪覆盖率变化趋势
3. **团队激励**: 设置覆盖率目标和奖励机制
4. **代码审查**: 在PR中检查覆盖率变化

通过遵循本指南，您可以确保CBSC系统具有高质量的测试覆盖率，从而提高代码质量和系统可靠性。