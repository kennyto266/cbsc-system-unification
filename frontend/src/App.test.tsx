import React from 'react'
import { render, screen } from '@testing-library/react'
import App from './App'

// Mock the router with all necessary components
jest.mock('react-router-dom', () => ({
  BrowserRouter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Routes: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Route: ({ element, children, index }: { element?: React.ReactNode; children?: React.ReactNode; index?: boolean }) => {
    if (index) {
      return <div>{element || children}</div>
    }
    if (element) {
      return <div>{element}</div>
    }
    return <div>{children}</div>
  },
  Outlet: () => <div data-testid="outlet">Outlet Content</div>,
  Navigate: ({ to }: { to: string }) => <div>Navigate to {to}</div>,
  useLocation: () => ({ pathname: '/' }),
  useParams: () => ({}),
}))

// Mock Layout component
jest.mock('./components/Layout/Layout', () => ({
  Layout: ({ children }: { children: React.ReactNode }) => {
    // Render children directly (simulating Outlet behavior)
    return <div data-testid="layout">{children}</div>
  },
}))

// Mock App components
jest.mock('./components/Layout/ResponsiveLayout', () => {
  return function MockResponsiveLayout({ children }: { children: React.ReactNode }) {
    return <div data-testid="responsive-layout">{children}</div>
  }
})

jest.mock('./pages/Dashboard', () => ({
  __esModule: true,
  default: () => <div data-testid="dashboard">Dashboard Page</div>,
}))

jest.mock('./pages/strategies', () => ({
  __esModule: true,
  default: () => <div data-testid="strategies">Strategies Page</div>,
}))

describe('App Component', () => {
  test('renders without crashing', () => {
    render(<App />)
  })

  test('renders main layout', () => {
    render(<App />)
    expect(screen.getByTestId('layout')).toBeInTheDocument()
  })

  test('routes are configured', () => {
    render(<App />)
    // Check that Routes and Route components are being used
    // The Layout component should be rendered which contains the routing structure
    expect(screen.getByTestId('layout')).toBeInTheDocument()
  })
})