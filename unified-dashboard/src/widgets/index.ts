// Widget exports for CBSC Dashboard
export { default as MarketOverview } from './MarketOverview'
export { default as StrategyMonitor } from './StrategyMonitor'
export { default as PortfolioSummary } from './PortfolioSummary'

// Placeholder exports for widgets that will be implemented
export const RiskMetrics = React.lazy(() => import('./RiskMetrics'))
export const TradingPanel = React.lazy(() => import('./TradingPanel'))
export const NewsFeed = React.lazy(() => import('./NewsFeed'))
export const SystemStatus = React.lazy(() => import('./SystemStatus'))
export const PerformanceChart = React.lazy(() => import('./PerformanceChart'))
export const OrderBook = React.lazy(() => import('./OrderBook'))
export const AlertCenter = React.lazy(() => import('./AlertCenter'))

// Widget registry for dynamic loading
export const widgetRegistry = {
  'market-overview': () => import('./MarketOverview'),
  'strategy-monitor': () => import('./StrategyMonitor'),
  'portfolio-summary': () => import('./PortfolioSummary'),
  'risk-metrics': () => import('./RiskMetrics'),
  'trading-panel': () => import('./TradingPanel'),
  'news-feed': () => import('./NewsFeed'),
  'system-status': () => import('./SystemStatus'),
  'performance-chart': () => import('./PerformanceChart'),
  'order-book': () => import('./OrderBook'),
  'alert-center': () => import('./AlertCenter'),
} as const