import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import { LayoutProvider } from '@/components/Layout'
import AppRoutes from './routes'

interface NavigationProviderProps {
  children?: React.ReactNode
}

const NavigationProvider: React.FC<NavigationProviderProps> = ({
  children,
}) => {
  return (
    <BrowserRouter>
      <LayoutProvider>
        {children || <AppRoutes />}
      </LayoutProvider>
    </BrowserRouter>
  )
}

export default NavigationProvider