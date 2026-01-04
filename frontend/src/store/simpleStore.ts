import { configureStore, createSlice } from '@reduxjs/toolkit'

// Simple auth slice for testing
const simpleAuthSlice = createSlice({
  name: 'auth',
  initialState: {
    isAuthenticated: false,
    user: null,
    token: null,
  },
  reducers: {
    login: (state, action) => {
      state.isAuthenticated = true
      state.user = action.payload.user
      state.token = action.payload.token
    },
    logout: (state) => {
      state.isAuthenticated = false
      state.user = null
      state.token = null
    },
  },
})

// Create simple store
export const simpleStore = configureStore({
  reducer: {
    auth: simpleAuthSlice.reducer,
  },
})

export type RootState = ReturnType<typeof simpleStore.getState>
export type AppDispatch = typeof simpleStore.dispatch

// Export simple hooks
export const useAppDispatch = () => {
  // Placeholder
  return () => {}
}
export const useAppSelector = (selector: any) => {
  // Placeholder - just return default state for now
  return selector({
    auth: {
      isAuthenticated: false,
      user: null,
      token: null,
    }
  })
}

export default simpleStore