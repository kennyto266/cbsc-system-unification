import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { MarketData, MarketDataState } from '@/types/market'

const initialState: MarketDataState = {
  quotes: {},
  watchlist: [],
  isLoading: false,
}

export const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {
    setQuotes: (state, action: PayloadAction<Record<string, MarketData>>) => {
      state.quotes = action.payload
    },
    updateQuote: (state, action: PayloadAction<{ symbol: string; data: Partial<MarketData> }>) => {
      const { symbol, data } = action.payload
      if (state.quotes[symbol]) {
        state.quotes[symbol] = { ...state.quotes[symbol], ...data }
      } else {
        state.quotes[symbol] = data as MarketData
      }
    },
    setWatchlist: (state, action: PayloadAction<string[]>) => {
      state.watchlist = action.payload
    },
    addToWatchlist: (state, action: PayloadAction<string>) => {
      if (!state.watchlist.includes(action.payload)) {
        state.watchlist.push(action.payload)
      }
    },
    removeFromWatchlist: (state, action: PayloadAction<string>) => {
      state.watchlist = state.watchlist.filter(s => s !== action.payload)
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
  },
})

export const {
  setQuotes,
  updateQuote,
  setWatchlist,
  addToWatchlist,
  removeFromWatchlist,
  setLoading,
} = marketSlice.actions

export { marketSlice as default }