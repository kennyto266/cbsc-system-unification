# Design — hk-quant-multi-agent

## Architecture Overview
- Pattern: Multi-agent micro-modules + shared DataService + Backtest + Monitoring
- Runtime: Python async (FastAPI backend already exists), Telegram bot for ops
- Data: `http_api` adapter (rate-limited, cached) + pluggable adapters
- Messaging: existing `MessageQueue` abstraction (local/in-memory/Redis-ready)
- Observability: Health, alerts, performance tracker; dashboard + Telegram

## Components
- Data Layer
  - DataService → loads adapters from `config/data_adapters.json`
  - `HttpApiDataAdapter` (done): RPS 和 per-symbol 限频、重试、缓存
  - Schema: `RealMarketData` (pydantic) + validation/quality scoring
- Agent Layer (7 roles)
  - Fundamental, Sentiment, News, Technical, Research(Bullish/Bearish), Trader, Risk
  - Base: `BaseRealAgent` (async initialize/analyze/generate/execute)
  - Analyzer: `RealDataAnalyzer` 产出 `AnalysisResult`
  - Message: `Message` via `MessageQueue`（本地可直调 + 未来可接Redis）
- Strategy/Backtest
  - Simple SMA/RSI baseline + parameter grid hooks
  - Backtest metrics: Sharpe/MaxDD/WinRate/Turnover（已在 backtest 模块定义接口）
- API & Dashboard
  - FastAPI endpoints: `/agents/status`, `/signals/latest`, `/risk/alerts`, `/portfolio/status`
  - Telegram commands: `/agent_status`, `/trading_signals`, `/portfolio_status`, `/risk_alerts`

## Data Flow (Happy Path)
1) DataService pulls symbols via `http_api` (限频与缓存生效)
2) Technical/Sentiment/News/Fundamental 各自分析→结构化 JSON（证据+不确定性）
3) Research(Bullish/Bearish) 聚合辩论 → 结论(多/空/观望)+置信度+依据
4) Trader sizing（目标价/止损/成本/滑点），生成可执行指令（模拟执行）
5) Risk 评估 VaR/CVaR、相关性、情景压力 → 通过/降杠杆/拒单
6) 输出到 API/Telegram；监控模块记录指标并做告警

## Message Contracts (JSON)
- AnalysisReport
  - `{ symbol, sources: [tech/sentiment/news/fundamental], scores:{...}, confidence, insights[], warnings[] }`
- ResearchDecision
  - `{ symbol, decision: buy|sell|hold, confidence, rationale[] }`
- TradePlan
  - `{ symbol, side, size, target, stop, est_cost, slippage_model }`
- RiskReview
  - `{ symbol, decision: approve|lower|reject, reasons[], limits{} }`

## Key Algorithms
- Technical: SMA/EMA/RSI/MACD/布林；简单 regime 判别
- Sentiment/News: 先占位词频/关键词模型（可后续引 HuggingFace）
- Research: 规则加权 + 置信度融合；可扩展为 Pair of Agents 辩论
- Trader: Position sizing = f(strength, confidence, risk limit, max_position_size)
- Risk: VaR(历史/正态近似)、回撤、相关性、压力情景（预置若干港股场景）

## Rate-limit & Resilience
- HttpApi: `rate_limit_rps`, `per_symbol_min_interval_sec`, `max_retries`, `timeout`
- 缓存：短 TTL 减少抖动；错误退避 0.5s 递增
- 质量：`DataValidationResult` + quality score gate

## APIs (Minimal)
- GET `/agents/status` → { total, agents: [{id,type,status,last_analysis,...}] }
- GET `/signals/latest?symbol=...` → 最新决策/置信度/依据
- GET `/risk/alerts` → 最近告警
- GET `/portfolio/status` → 目标权重/执行统计（模拟）

## Telemetry & Alerts
- 指标：延迟、错误率、RPS、队列长度、CPU/Mem
- 阈值：429/5xx/超时比例、分析失败率、Sharpe < min 基线
- 通知：Telegram（管理员 chat_id）

## Implementation Plan (High-level)
1) Agents
  - 补齐 7 角色具体类（如已存在则增强）：初始化、_enhance_analysis/_enhance_signals/_execute_signal
  - 研究辩论代理：合并多源报告，输出 ResearchDecision
  - 交易与风控代理：生成/审核 TradePlan
2) Pipelines
  - `scripts/agent_http_pipeline.py` 扩展为多标的调度（symbols 列表）
  - 增加批量分析与并发（受限于 http_api 限频）
3) Backtest
  - 将 `scripts/dev_strategy_0939.py` 逻辑抽到 backtest 接口，实现 Sharpe/MaxDD 输出
  - 参数网格/走样本 CLI 脚本
4) API/Telegram
  - 补全 `/signals/latest`、`/risk/alerts` 聚合真实数据
  - 机器人命令接入实时后端
5) Monitoring
  - 记录全链路指标；触发告警；仪表板卡片展示 Sharpe 等

## Risks / Mitigations
- 外部 API 不稳 → 限频/缓存/退避/回退至离线
- 数据稀疏 → 最小窗口校验，回退为“观望”并标警告
- 过拟合 → 参数搜索加走样本；研究辩论抑制偏差

## Done Criteria
- 7 代理可在多标的上跑通 pipeline，输出决策和风控结论
- 后端与 Telegram 能查询状态/信号/风险；回测生成 Sharpe 等指标
- 监控项齐全，异常有告警；示范策略样本内 Sharpe>1.0
