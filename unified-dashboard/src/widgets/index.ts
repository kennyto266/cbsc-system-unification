// Widget exports for CBSC Dashboard
// Maps widget type names to actual component locations.
// Components that don't exist yet fall back to MarketOverview.

import { lazy } from 'react'

export const MarketOverview = lazy(() => import('../components/dashboard/MarketOverview'))
export const RiskMetrics = lazy(() => import('../components/analytics/RiskMetrics'))
export const TradingPanel = lazy(() => import('../components/charts/widgets/TradingPanel'))
export const SystemStatus = lazy(() => import('../components/dashboard/SystemHealth'))

// Fallbacks for not-yet-implemented widgets — reuse an existing component
export { MarketOverview as StrategyMonitor }
export { MarketOverview as PortfolioSummary }
export { MarketOverview as NewsFeed }

// Widget registry for dynamic loading
export const widgetRegistry = {
  'market-overview': () => import('../components/dashboard/MarketOverview'),
  'risk-metrics': () => import('../components/analytics/RiskMetrics'),
  'trading-panel': () => import('../components/charts/widgets/TradingPanel'),
  'system-status': () => import('../components/dashboard/SystemHealth'),
  'strategy-monitor': () => import('../components/dashboard/MarketOverview'),
  'portfolio-summary': () => import('../components/dashboard/MarketOverview'),
  'news-feed': () => import('../components/dashboard/MarketOverview'),
} as const
