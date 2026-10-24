import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { MarketState, MarketData, WebSocketState } from '../../types/store'
import { MarketDataResponse, TickerResponse } from '../../types/api'

// Initial state
const initialState: MarketState = {
  data: [],
  selectedSymbol: null,
  timeFrame: '1h',
  indicators: {
    sma: {},
    ema: {},
    rsi: {},
    macd: {},
    bollinger: {},
    volume: {},
  },
  websocket: {
    connected: false,
    reconnecting: false,
    error: null,
    reconnectAttempts: 0,
    subscriptions: [],
  },
  lastUpdate: null,
  loading: false,
  error: null,
}

// Async thunks
export const fetchMarketData = createAsyncThunk(
  'market/fetchMarketData',
  async (params: { symbol: string; interval: string; limit?: number }) => {
    const response = await fetch(`/api/market/data?symbol=${params.symbol}&interval=${params.interval}&limit=${params.limit || 100}`)
    if (!response.ok) {
      throw new Error('Failed to fetch market data')
    }
    return await response.json() as MarketDataResponse
  }
)

export const fetchTicker = createAsyncThunk(
  'market/fetchTicker',
  async (symbol: string) => {
    const response = await fetch(`/api/market/ticker?symbol=${symbol}`)
    if (!response.ok) {
      throw new Error('Failed to fetch ticker')
    }
    return await response.json() as TickerResponse
  }
)

export const fetchMultipleTickers = createAsyncThunk(
  'market/fetchMultipleTickers',
  async (symbols: string[]) => {
    const response = await fetch(`/api/market/tickers?symbols=${symbols.join(',')}`)
    if (!response.ok) {
      throw new Error('Failed to fetch tickers')
    }
    return await response.json() as TickerResponse[]
  }
)

export const subscribeToSymbol = createAsyncThunk(
  'market/subscribeToSymbol',
  async (symbol: string) => {
    const response = await fetch('/api/market/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel: 'ticker', symbol })
    })
    if (!response.ok) {
      throw new Error('Failed to subscribe to symbol')
    }
    return symbol
  }
)

export const unsubscribeFromSymbol = createAsyncThunk(
  'market/unsubscribeFromSymbol',
  async (symbol: string) => {
    const response = await fetch('/api/market/unsubscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel: 'ticker', symbol })
    })
    if (!response.ok) {
      throw new Error('Failed to unsubscribe from symbol')
    }
    return symbol
  }
)

// Slice
const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {
    setSelectedSymbol: (state, action: PayloadAction<string | null>) => {
      state.selectedSymbol = action.payload
    },
    setTimeFrame: (state, action: PayloadAction<'1m' | '5m' | '15m' | '1h' | '4h' | '1d'>) => {
      state.timeFrame = action.payload
    },
    updateRealTimeData: (state, action: PayloadAction<TickerResponse>) => {
      const { symbol, price, change, changePercent, volume, timestamp } = action.payload

      // Update or add market data
      const existingIndex = state.data.findIndex(d => d.symbol === symbol)
      if (existingIndex >= 0) {
        state.data[existingIndex] = {
          ...state.data[existingIndex],
          price,
          change,
          changePercent,
          volume,
          timestamp,
        }
      } else {
        state.data.push({
          symbol,
          price,
          change,
          changePercent,
          volume,
          high24h: price,
          low24h: price,
          timestamp,
        })
      }

      state.lastUpdate = timestamp
    },
    updateOHLCData: (state, action: PayloadAction<{ symbol: string; ohlc: MarketData['ohlc'] }>) => {
      const { symbol, ohlc } = action.payload
      const existingIndex = state.data.findIndex(d => d.symbol === symbol)

      if (existingIndex >= 0) {
        state.data[existingIndex].ohlc = ohlc
      } else {
        state.data.push({
          symbol,
          price: 0,
          change: 0,
          changePercent: 0,
          volume: 0,
          high24h: 0,
          low24h: 0,
          timestamp: new Date().toISOString(),
          ohlc,
        })
      }
    },
    setWebSocketState: (state, action: PayloadAction<Partial<WebSocketState>>) => {
      state.websocket = { ...state.websocket, ...action.payload }
    },
    addSubscription: (state, action: PayloadAction<string>) => {
      if (!state.websocket.subscriptions.includes(action.payload)) {
        state.websocket.subscriptions.push(action.payload)
      }
    },
    removeSubscription: (state, action: PayloadAction<string>) => {
      state.websocket.subscriptions = state.websocket.subscriptions.filter(
        sub => sub !== action.payload
      )
    },
    updateIndicators: (state, action: PayloadAction<{
      symbol: string
      type: keyof MarketState['indicators']
      data: any
    }>) => {
      const { symbol, type, data } = action.payload
      state.indicators[type][symbol] = data
    },
    clearMarketData: (state) => {
      state.data = []
      state.lastUpdate = null
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    // fetchMarketData
    builder
      .addCase(fetchMarketData.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchMarketData.fulfilled, (state, action) => {
        state.loading = false
        const { symbol, data, interval } = action.payload

        // Convert API response to internal format
        const ohlcData = data.map(d => ({
          time: new Date(d.timestamp).getTime(),
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
          volume: d.volume,
        }))

        const existingIndex = state.data.findIndex(d => d.symbol === symbol)
        if (existingIndex >= 0) {
          state.data[existingIndex].ohlc = ohlcData
        } else {
          state.data.push({
            symbol,
            price: data[data.length - 1]?.close || 0,
            change: 0,
            changePercent: 0,
            volume: data[data.length - 1]?.volume || 0,
            high24h: Math.max(...data.map(d => d.high)),
            low24h: Math.min(...data.map(d => d.low)),
            timestamp: data[data.length - 1]?.timestamp,
            ohlc: ohlcData,
          })
        }

        state.lastUpdate = new Date().toISOString()
      })
      .addCase(fetchMarketData.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch market data'
      })

    // fetchTicker
    builder
      .addCase(fetchTicker.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchTicker.fulfilled, (state, action) => {
        state.loading = false
        const ticker = action.payload

        // Update or add ticker data
        const existingIndex = state.data.findIndex(d => d.symbol === ticker.symbol)
        if (existingIndex >= 0) {
          state.data[existingIndex] = {
            ...state.data[existingIndex],
            price: ticker.price,
            change: ticker.change,
            changePercent: ticker.changePercent,
            volume: ticker.volume,
            high24h: ticker.high24h,
            low24h: ticker.low24h,
            timestamp: ticker.timestamp,
          }
        } else {
          state.data.push({
            symbol: ticker.symbol,
            price: ticker.price,
            change: ticker.change,
            changePercent: ticker.changePercent,
            volume: ticker.volume,
            high24h: ticker.high24h,
            low24h: ticker.low24h,
            timestamp: ticker.timestamp,
          })
        }

        state.lastUpdate = ticker.timestamp
      })
      .addCase(fetchTicker.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch ticker'
      })

    // fetchMultipleTickers
    builder
      .addCase(fetchMultipleTickers.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchMultipleTickers.fulfilled, (state, action) => {
        state.loading = false
        const tickers = action.payload

        tickers.forEach(ticker => {
          const existingIndex = state.data.findIndex(d => d.symbol === ticker.symbol)
          if (existingIndex >= 0) {
            state.data[existingIndex] = {
              ...state.data[existingIndex],
              price: ticker.price,
              change: ticker.change,
              changePercent: ticker.changePercent,
              volume: ticker.volume,
              high24h: ticker.high24h,
              low24h: ticker.low24h,
              timestamp: ticker.timestamp,
            }
          } else {
            state.data.push({
              symbol: ticker.symbol,
              price: ticker.price,
              change: ticker.change,
              changePercent: ticker.changePercent,
              volume: ticker.volume,
              high24h: ticker.high24h,
              low24h: ticker.low24h,
              timestamp: ticker.timestamp,
            })
          }
        })

        state.lastUpdate = new Date().toISOString()
      })
      .addCase(fetchMultipleTickers.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch tickers'
      })

    // subscribeToSymbol
    builder
      .addCase(subscribeToSymbol.fulfilled, (state, action) => {
        const symbol = action.payload
        if (!state.websocket.subscriptions.includes(symbol)) {
          state.websocket.subscriptions.push(symbol)
        }
      })
      .addCase(subscribeToSymbol.rejected, (state, action) => {
        state.error = action.error.message || 'Failed to subscribe to symbol'
      })

    // unsubscribeFromSymbol
    builder
      .addCase(unsubscribeFromSymbol.fulfilled, (state, action) => {
        const symbol = action.payload
        state.websocket.subscriptions = state.websocket.subscriptions.filter(
          sub => sub !== symbol
        )
      })
      .addCase(unsubscribeFromSymbol.rejected, (state, action) => {
        state.error = action.error.message || 'Failed to unsubscribe from symbol'
      })
  },
})

export const {
  setSelectedSymbol,
  setTimeFrame,
  updateRealTimeData,
  updateOHLCData,
  setWebSocketState,
  addSubscription,
  removeSubscription,
  updateIndicators,
  clearMarketData,
  setError,
  clearError,
} = marketSlice.actions

export default marketSlice.reducer

// Selectors
export const selectMarketData = (state: { market: MarketState }) => state.market.data
export const selectSelectedSymbol = (state: { market: MarketState }) => state.market.selectedSymbol
export const selectMarketSymbol = (symbol: string) => (state: { market: MarketState }) =>
  state.market.data.find(d => d.symbol === symbol)
export const selectMarketOHLC = (symbol: string) => (state: { market: MarketState }) =>
  state.market.data.find(d => d.symbol === symbol)?.ohlc
export const selectTimeFrame = (state: { market: MarketState }) => state.market.timeFrame
export const selectWebSocketStatus = (state: { market: MarketState }) => state.market.websocket
export const selectMarketIndicators = (symbol: string) => (state: { market: MarketState }) => ({
  sma: state.market.indicators.sma[symbol],
  ema: state.market.indicators.ema[symbol],
  rsi: state.market.indicators.rsi[symbol],
  macd: state.market.indicators.macd[symbol],
  bollinger: state.market.indicators.bollinger[symbol],
  volume: state.market.indicators.volume[symbol],
})
export const selectMarketLoading = (state: { market: MarketState }) => state.market.loading
export const selectMarketError = (state: { market: MarketState }) => state.market.error