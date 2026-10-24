/**
 * Market Data API Service
 * Handles all market data related API calls
 */

import { apiRequest } from '../client'
import { API_ENDPOINTS } from '../config'
import { ApiResponse, PaginatedResponse, BaseParams } from '../types/common'
import {
  MarketSymbol,
  MarketPrice,
  KlineData,
  TickData,
  OrderBook,
  MarketTrade,
  MarketStats,
  MarketOverview,
  ScreenerResult,
  MarketEvent,
  CalendarEvent,
  NewsItem,
} from '../types/market'

export class MarketService {
  /**
   * Get all available market symbols
   */
  async getSymbols(params?: BaseParams & {
    category?: string
    status?: 'active' | 'inactive'
    search?: string
  }): Promise<PaginatedResponse<MarketSymbol>> {
    return apiRequest.get<PaginatedResponse<MarketSymbol>>(API_ENDPOINTS.MARKET.SYMBOLS, { params })
  }

  /**
   * Get symbol details
   */
  async getSymbol(symbol: string): Promise<ApiResponse<MarketSymbol>> {
    return apiRequest.get<ApiResponse<MarketSymbol>>(API_ENDPOINTS.MARKET.SYMBOLS + `/${symbol}`)
  }

  /**
   * Get current price for a symbol
   */
  async getPrice(symbol: string): Promise<ApiResponse<MarketPrice>> {
    return apiRequest.get<ApiResponse<MarketPrice>>(API_ENDPOINTS.MARKET.PRICE(symbol))
  }

  /**
   * Get prices for multiple symbols
   */
  async getPrices(symbols: string[]): Promise<ApiResponse<Record<string, MarketPrice>>> {
    return apiRequest.post<ApiResponse<Record<string, MarketPrice>>>('/market/prices', { symbols })
  }

  /**
   * Get kline/candlestick data
   */
  async getKlineData(params: {
    symbol: string
    interval: '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w' | '1M'
    startTime?: number
    endTime?: number
    limit?: number
  }): Promise<ApiResponse<KlineData[]>> {
    return apiRequest.get<ApiResponse<KlineData[]>>(API_ENDPOINTS.MARKET.KLINE, { params })
  }

  /**
   * Get tick data
   */
  async getTickData(symbol: string, params?: {
    limit?: number
    lastId?: number
  }): Promise<ApiResponse<TickData[]>> {
    return apiRequest.get<ApiResponse<TickData[]>>(API_ENDPOINTS.MARKET.TICK(symbol), { params })
  }

  /**
   * Get order book
   */
  async getOrderBook(symbol: string, params?: {
    limit?: number
    depth?: number
  }): Promise<ApiResponse<OrderBook>> {
    return apiRequest.get<ApiResponse<OrderBook>>(API_ENDPOINTS.MARKET.DEPTH(symbol), { params })
  }

  /**
   * Get recent trades
   */
  async getTrades(symbol: string, params?: {
    limit?: number
    from?: number
    to?: number
  }): Promise<ApiResponse<MarketTrade[]>> {
    return apiRequest.get<ApiResponse<MarketTrade[]>>(API_ENDPOINTS.MARKET.TRADES(symbol), { params })
  }

  /**
   * Get market statistics
   */
  async getMarketStats(params?: {
    category?: string
    period?: '24h' | '7d' | '30d'
  }): Promise<ApiResponse<MarketStats>> {
    return apiRequest.get<ApiResponse<MarketStats>>(API_ENDPOINTS.MARKET.STATS, { params })
  }

  /**
   * Get market overview
   */
  async getMarketOverview(): Promise<ApiResponse<MarketOverview>> {
    return apiRequest.get<ApiResponse<MarketOverview>>(API_ENDPOINTS.MARKET.OVERVIEW)
  }

  /**
   * Market screener
   */
  async screener(params: {
    filters: Record<string, any>
    sort?: string
    order?: 'asc' | 'desc'
    limit?: number
  }): Promise<ApiResponse<ScreenerResult[]>> {
    return apiRequest.get<ApiResponse<ScreenerResult[]>>(API_ENDPOINTS.MARKET.SCREENER, { params })
  }

  /**
   * Get market calendar
   */
  async getCalendar(params?: {
    startDate?: string
    endDate?: string
    country?: string
    type?: string
  }): Promise<ApiResponse<CalendarEvent[]>> {
    return apiRequest.get<ApiResponse<CalendarEvent[]>>(API_ENDPOINTS.MARKET.CALENDAR, { params })
  }

  /**
   * Get market news
   */
  async getNews(params?: {
    category?: string
    symbols?: string[]
    limit?: number
    from?: string
    to?: string
  }): Promise<ApiResponse<NewsItem[]>> {
    return apiRequest.get<ApiResponse<NewsItem[]>>(API_ENDPOINTS.MARKET.NEWS, { params })
  }

  /**
   * Search market data
   */
  async search(query: string, params?: {
    type?: 'symbol' | 'news' | 'event'
    limit?: number
  }): Promise<ApiResponse<any[]>> {
    return apiRequest.get<ApiResponse<any[]>>('/market/search', {
      params: { q: query, ...params },
    })
  }

  /**
   * Get market movers (gainers/losers)
   */
  async getMarketMovers(params?: {
    category?: string
    period?: '1h' | '24h' | '7d'
    type?: 'gainers' | 'losers' | 'active'
    limit?: number
  }): Promise<ApiResponse<ScreenerResult[]>> {
    return apiRequest.get<ApiResponse<ScreenerResult[]>>('/market/movers', { params })
  }

  /**
   * Get market sectors
   */
  async getMarketSectors(): Promise<ApiResponse<Record<string, any>>> {
    return apiRequest.get<ApiResponse<Record<string, any>>>('/market/sectors')
  }

  /**
   * Get market indices
   */
  async getMarketIndices(params?: {
    country?: string
  }): Promise<ApiResponse<any[]>> {
    return apiRequest.get<ApiResponse<any[]>>('/market/indices', { params })
  }

  /**
   * Get market heat map
   */
  async getHeatMap(params?: {
    category?: string
    period?: '1h' | '24h' | '7d'
  }): Promise<ApiResponse<Record<string, any>>> {
    return apiRequest.get<ApiResponse<Record<string, any>>>('/market/heatmap', { params })
  }

  /**
   * Get market sentiment
   */
  async getMarketSentiment(params?: {
    symbol?: string
    timeframe?: '1h' | '24h' | '7d'
  }): Promise<ApiResponse<{
    overall: 'bullish' | 'bearish' | 'neutral'
    score: number
    factors: Record<string, number>
  }>> {
    return apiRequest.get<ApiResponse<any>>('/market/sentiment', { params })
  }

  /**
   * Get market alerts
   */
  async getMarketAlerts(params?: BaseParams): Promise<PaginatedResponse<MarketEvent>> {
    return apiRequest.get<PaginatedResponse<MarketEvent>>('/market/alerts', { params })
  }

  /**
   * Create market alert
   */
  async createMarketAlert(data: {
    symbol: string
    type: string
    condition: Record<string, any>
    isActive: boolean
  }): Promise<ApiResponse<MarketEvent>> {
    return apiRequest.post<ApiResponse<MarketEvent>>('/market/alerts', data)
  }

  /**
   * Update market alert
   */
  async updateMarketAlert(id: string, data: Partial<MarketEvent>): Promise<ApiResponse<MarketEvent>> {
    return apiRequest.put<ApiResponse<MarketEvent>>(`/market/alerts/${id}`, data)
  }

  /**
   * Delete market alert
   */
  async deleteMarketAlert(id: string): Promise<void> {
    return apiRequest.delete<void>(`/market/alerts/${id}`)
  }
}

// Create singleton instance
export const marketService = new MarketService()