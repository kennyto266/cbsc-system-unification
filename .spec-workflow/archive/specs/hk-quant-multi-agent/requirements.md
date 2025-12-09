# Requirements — hk-quant-multi-agent

## Overview
面向香港股票市场（港股）的量化分析交易 AI 多代理团队（7 个代理），以高夏普比率为核心目标，覆盖数据→研究→执行→风控全链条，并与现有代码架构与 http_api 实盘数据源对接，形成可运行、可回测、可监控、可告警的闭环系统。

## Goals
- Sharpe Ratio 优先：在控制波动与回撤的同时优化收益。
- 7 代理分工与协作：数据、情绪、新闻、技术、研究辩论、交易执行、风险管理。
- 对接真实数据源（优先 http_api），提供走样本验证与标准化绩效指标。
- 集成后端 API/仪表板/Telegram/监控告警，端到端可用。

## Non-Goals
- 本规格不覆盖实盘券商下单（保留接口，先模拟执行）。
- 不引入复杂分布式中间件（沿用轻量消息队列抽象）。

## Stakeholders
- 研究/交易：产出策略与信号、回测与优化。
- 风险/运维：风险度量、告警、系统健康。
- 管理/产品：仪表板与机器人查看状态与绩效。

## Scope
1) 代理角色与职责：
- Fundamental：财务与宏观、估值与质量过滤。
- Sentiment：社媒/论坛情绪量化与异常检测。
- News：事件抽取、主题聚类、影响评估。
- Technical：SMA/EMA/RSI/MACD/布林，趋势与波动框架。
- Research（Bullish/Bearish）：基于多源报告辩论并加权定论。
- Trader：信号→订单建议、仓位 sizing、成本/滑点模拟。
- Risk：VaR/CVaR、回撤/相关性、压力测试、阈值与对冲建议。

2) 数据与回测
- 数据源：http_api（已验证 0939.HK），支持多标的；预留 HKEX/Yahoo。
- 回测：Sharpe、回撤、胜率、换手；支持走样本（walk-forward）。

3) 协作与汇总
- 结构化 JSON 报告，研究辩论汇总成“多/空/观望 + 置信度 + 依据”。
- 执行链：Trader 方案 → Risk 审核 → 执行（模拟）。

4) 输出
- API：/agents/status, /signals/latest, /portfolio/status, /risk/alerts。
- 仪表板：展示每代理状态/策略/指标/Sharpe。
- Telegram：/agent_status /trading_signals /portfolio_status /risk_alerts。

## Functional Requirements
- FR-1: 7 代理可独立运行与编排，互传结构化消息。
- FR-2: 技术/情绪/新闻/基本面对多标的输出打分与证据。
- FR-3: 研究辩论输出“结论+置信度+依据”。
- FR-4: 交易生成订单建议（含目标/止损/成本/滑点）。
- FR-5: 风险评估 VaR/CVaR/回撤/相关性/压力情景并可拒单或降杠杆。
- FR-6: http_api 支持限频/缓存/重试与批量拉取。
- FR-7: 统一回测接口输出 Sharpe 等，支持参数搜索与走样本。
- FR-8: 提供 REST/WS/Telegram 查询实时状态/信号/告警。

## NFR
- 可靠性：关键路径测试覆盖 ≥80%；异常有告警与降级。
- 性能：单标的基础分析 ≤1s；批量 ≤5s（视外部 API）。
- 合规：日志脱敏；可配置速率限制与超时重试。
- 可扩展：数据源/指标/代理可插拔；接口稳定。

## Risks
- 外部数据不稳：重试/缓存/限频/多源回退；离线镜像。
- 过拟合：走样本、正则化与早停；多代理辩论抑制偏见。
- 信号失真：风控阈值、成本/滑点/延迟建模、回撤限额降风控。

## Acceptance Criteria
- AC-1: 7 代理端到端跑通 http_api 多标的，产出策略与风控结论。
- AC-2: 回测输出 Sharpe/回撤/胜率等，并可在仪表板与 Telegram 查询。
- AC-3: 至少 1 策略样本内 Sharpe>1.0，具备走样本脚手架。
- AC-4: 核心 API 稳定返回并含总数/错误字段；对 429/超时自动退避。
