import { useDispatch, useSelector } from 'react-redux'
import { useEffect } from 'react'
import type { RootState } from '@store/index'

export const useAuth = () => {
  const dispatch = useDispatch()
  const { isAuthenticated, isLoading, user } = useSelector((state: RootState) => state.auth)

  const initializeAuth = () => {
    // 检查本地存储的token
    const token = localStorage.getItem('cbsc_token')
    if (token) {
      console.log('Found existing token:', token)
    }
  }

  return {
    isAuthenticated,
    isLoading,
    user,
    initializeAuth,
  }
}
