---
name: personal-strategy-management-dashboard
title: Personal Strategy Management Dashboard
status: backlog
created: 2025-12-18T10:00:00Z
updated: 2025-12-18T10:00:00Z
---

# PRD: Personal Strategy Management Dashboard

## Executive Summary

创建一个个人使用的CBSC量化交易策略管理Dashboard，专注于策略表现监控和策略清单管理。该Dashboard将提供直观的界面来展示关键绩效指标（Sharpe比率SR和最大回撤MDD），支持最多4种策略的管理，并与现有的FastAPI后端无缝集成。

## Problem Statement

### 现状与挑战
- **分散的策略监控**: 个人量化交易者缺乏统一的策略表现监控界面
- **关键指标追踪困难**: Sharpe比率和最大回撤等重要绩效指标难以实时追踪
- **策略管理效率低**: 缺乏有效的策略清单管理工具
- **数据可视化不足**: 缺乏直观的图表展示策略表现趋势

## User Stories

### 主要用户：个人量化交易者

#### User Story 1: 策略概览查看
**作为一名**个人量化交易者
**我想要**在一个Dashboard中查看所有运行中的策略
**以便**快速了解整体策略表现

#### User Story 2: 策略详细分析
**作为一名**个人量化交易者
**我想要**深入分析每个策略的详细表现
**以便**做出明智的调整决策

#### User Story 3: 策略清单管理
**作为一名**个人量化交易者
**我想要**管理我的策略清单
**以便**添加、删除或暂停策略

## Requirements

### Functional Requirements

#### 1. Dashboard主页
- **策略概览卡片**: 显示所有策略的关键指标
  - 策略名称
  - 当前收益率
  - Sharpe比率（SR）
  - 最大回撤（MDD）
  - 运行状态
- **总体表现汇总**:
  - 总投资组合收益
  - 平均Sharpe比率
  - 最大回撤监控

#### 2. 策略详情页
- **交互式图表**:
  - 净值曲线（使用Chart.js）
  - 回撤曲线图
  - Sharpe比率趋势图
- **统计信息表格**:
  - 总收益率
  - 年化收益率
  - 夏普比率
  - 最大回撤
  - 胜率

#### 3. 策略管理功能
- **策略配置**:
  - 策略名称编辑
  - 策略描述
  - 初始资金设置
  - 风险参数设置
- **策略操作**:
  - 启动/暂停策略
  - 删除策略
  - 复制策略配置

## Technical Specifications

### 技术栈
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **图表库**: Chart.js
- **后端集成**: FastAPI
- **部署**: 本地静态文件服务

### API接口需求
```javascript
// 获取策略列表
GET /api/strategies
Response: {
  "strategies": [
    {
      "id": "strategy_001",
      "name": "动量策略",
      "status": "running",
      "current_return": 0.156,
      "sharpe_ratio": 1.23,
      "max_drawdown": -0.089
    }
  ]
}

// 获取策略详细数据
GET /api/strategies/{id}/performance?period=1m
Response: {
  "strategy_id": "strategy_001",
  "performance": {
    "daily_returns": [0.001, 0.002, -0.001],
    "cumulative_returns": [1.001, 1.003, 1.002],
    "drawdowns": [0, 0, -0.001],
    "sharpe_ratios": [1.1, 1.15, 1.12]
  }
}
```

## Success Criteria

### 定量指标
- **用户效率提升**: 策略监控时间减少70%
- **决策速度提升**: 策略分析决策时间减少50%
- **系统可用性**: 99.9%的本地运行稳定性

### 定性指标
- **用户满意度**: 界面直观易用，学习成本 < 30分钟
- **功能完整性**: 满足个人量化交易者90%的日常需求

## Constraints

### 技术约束
- **前端技术栈固定**: 必须使用HTML5 + CSS3 + Vanilla JavaScript
- **图表库**: 必须使用Chart.js
- **不使用框架**: 禁止使用React、Vue等前端框架

### 业务约束
- **个人使用限制**: 仅支持单用户使用
- **策略数量限制**: 最多支持4个策略
- **本地部署**: 仅支持本地环境运行

## Implementation Plan

### Phase 1: 基础架构搭建（1周）
- 创建基础HTML页面结构
- 设置CSS样式和响应式布局
- 建立JavaScript模块化架构
- 配置与FastAPI的API连接

### Phase 2: 核心功能开发（2周）
- 实现策略列表显示
- 开发策略详情页面
- 集成Chart.js图表组件
- 完成数据可视化功能

### Phase 3: 策略管理功能（1周）
- 实现策略增删改查
- 开发策略配置界面
- 添加策略状态管理

## Acceptance Criteria

### 功能验收
- [ ] 成功连接FastAPI后端并获取数据
- [ ] 正确显示最多4个策略的概览信息
- [ ] Chart.js图表正确渲染策略表现数据
- [ ] 策略管理功能（增删改查）正常工作

### 性能验收
- [ ] 首屏加载时间 < 3秒
- [ ] API响应时间 < 500ms
- [ ] 图表渲染流畅无卡顿

### 安全验收
- [ ] 所有数据存储在本地
- [ ] 不存在数据泄露风险