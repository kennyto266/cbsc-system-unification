import React from 'react'
import { render, screen } from '@testing-library/react'
import App from './App'

// Mock the router
jest.mock('react-router-dom', () => ({
  BrowserRouter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Routes: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Route: ({ element }: { element: React.ReactNode }) => element,
}))

// Mock App components
jest.mock('./components/Layout/ResponsiveLayout', () => {
  return function MockResponsiveLayout({ children }: { children: React.ReactNode }) {
    return <div data-testid="responsive-layout">{children}</div>
  }
})

jest.mock('./pages/Dashboard', () => {
  return function MockDashboard() {
    return <div data-testid="dashboard">Dashboard Page</div>
  }
})

jest.mock('./pages/strategies', () => {
  return function MockStrategies() {
    return <div data-testid="strategies">Strategies Page</div>
  }
})

describe('App Component', () => {
  test('renders without crashing', () => {
    render(<App />)
  })

  test('renders main layout', () => {
    render(<App />)
    expect(screen.getByTestId('responsive-layout')).toBeInTheDocument()
  })

  test('routes are configured', () => {
    render(<App />)
    // Should render dashboard as default route
    expect(screen.getByTestId('dashboard')).toBeInTheDocument()
  })
})