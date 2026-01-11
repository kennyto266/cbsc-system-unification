import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface DashboardStats {
  totalStrategies: number
  activeStrategies: number
  totalReturn: number
  dailyReturn: number
  totalTrades: number
  winRate: number
}

interface RecentActivity {
  id: string
  type: 'strategy' | 'trade' | 'alert'
  message: string
  timestamp: string
}

interface DashboardState {
  stats: DashboardStats | null
  recentActivities: RecentActivity[]
  isLoading: boolean
  error: string | null
}

const initialState: DashboardState = {
  stats: null,
  recentActivities: [],
  isLoading: false,
  error: null,
}

export const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    setStats: (state, action: PayloadAction<DashboardStats>) => {
      state.stats = action.payload
    },
    setRecentActivities: (state, action: PayloadAction<RecentActivity[]>) => {
      state.recentActivities = action.payload
    },
    addActivity: (state, action: PayloadAction<RecentActivity>) => {
      state.recentActivities.unshift(action.payload)
      // Keep only last 10 activities
      state.recentActivities = state.recentActivities.slice(0, 10)
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
  },
})

export const {
  setStats,
  setRecentActivities,
  addActivity,
  setLoading,
  setError,
} = dashboardSlice.actions