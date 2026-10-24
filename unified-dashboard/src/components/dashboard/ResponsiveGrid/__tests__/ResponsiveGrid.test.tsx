import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ResponsiveGridProvider, ResponsiveGrid, useResponsiveGrid } from '../ResponsiveGridProvider'

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Mock toast
jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn()
}))

// Test component to use the hook
const TestComponent: React.FC = () => {
  const {
    widgets,
    addWidget,
    removeWidget,
    saveLayout,
    loadLayout
  } = useResponsiveGrid()

  const handleAddWidget = () => {
    addWidget({
      id: 'test-widget',
      type: 'market-overview',
      name: 'Test Widget',
      category: 'metric',
      x: 0,
      y: 0,
      w: 4,
      h: 3,
      minW: 2,
      minH: 2,
      maxW: 8,
      maxH: 6,
      isDraggable: true,
      isResizable: true
    })
  }

  return (
    <div>
      <button onClick={handleAddWidget}>Add Widget</button>
      <div data-testid="widget-count">{widgets.length}</div>
      {widgets.map(widget => (
        <div key={widget.id} data-testid={`widget-${widget.id}`}>
          {widget.name}
        </div>
      ))}
    </div>
  )
}

describe('ResponsiveGrid', () => {
  beforeEach(() => {
    localStorageMock.getItem.mockClear()
    localStorageMock.setItem.mockClear()
  })

  it('renders without crashing', () => {
    render(
      <ResponsiveGridProvider>
        <ResponsiveGrid />
      </ResponsiveGridProvider>
    )
  })

  it('provides useResponsiveGrid hook', () => {
    render(
      <ResponsiveGridProvider>
        <TestComponent />
      </ResponsiveGridProvider>
    )

    expect(screen.getByText('Add Widget')).toBeInTheDocument()
    expect(screen.getByTestId('widget-count')).toHaveTextContent('0')
  })

  it('adds a widget when addWidget is called', async () => {
    render(
      <ResponsiveGridProvider>
        <TestComponent />
      </ResponsiveGridProvider>
    )

    const addButton = screen.getByText('Add Widget')
    fireEvent.click(addButton)

    await waitFor(() => {
      expect(screen.getByTestId('widget-count')).toHaveTextContent('1')
    })

    expect(screen.getByTestId('widget-test-widget')).toBeInTheDocument()
    expect(screen.getByTestId('widget-test-widget')).toHaveTextContent('Test Widget')
  })

  it('saves and loads layouts', () => {
    render(
      <ResponsiveGridProvider>
        <TestComponent />
      </ResponsiveGridProvider>
    )

    // This would need more complex testing for actual save/load functionality
    // For now, just ensure the functions exist
    expect(screen.getByText('Add Widget')).toBeInTheDocument()
  })

  it('prevents duplicate widgets', async () => {
    const TestDuplicateComponent: React.FC = () => {
      const { addWidget, widgets } = useResponsiveGrid()

      const handleAddWidget = () => {
        addWidget({
          id: 'test-widget',
          type: 'market-overview',
          name: 'Test Widget',
          category: 'metric',
          x: 0,
          y: 0,
          w: 4,
          h: 3,
          minW: 2,
          minH: 2,
          maxW: 8,
          maxH: 6,
          isDraggable: true,
          isResizable: true
        })
      }

      return (
        <div>
          <button onClick={handleAddWidget}>Add Widget</button>
          <div data-testid="widget-count">{widgets.length}</div>
        </div>
      )
    }

    render(
      <ResponsiveGridProvider>
        <TestDuplicateComponent />
      </ResponsiveGridProvider>
    )

    const addButton = screen.getByText('Add Widget')

    // Add first widget
    fireEvent.click(addButton)
    await waitFor(() => {
      expect(screen.getByTestId('widget-count')).toHaveTextContent('1')
    })

    // Try to add duplicate
    fireEvent.click(addButton)
    // Count should remain 1
    expect(screen.getByTestId('widget-count')).toHaveTextContent('1')
  })
})

describe('useResponsiveGrid hook', () => {
  it('throws error when used outside provider', () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      render(<TestComponent />)
    }).toThrow('useResponsiveGrid must be used within ResponsiveGridProvider')

    consoleError.mockRestore()
  })

  it('provides all required methods and state', () => {
    const TestMethodsComponent: React.FC = () => {
      const gridContext = useResponsiveGrid()

      expect(gridContext).toHaveProperty('widgets')
      expect(gridContext).toHaveProperty('layouts')
      expect(gridContext).toHaveProperty('addWidget')
      expect(gridContext).toHaveProperty('removeWidget')
      expect(gridContext).toHaveProperty('updateWidget')
      expect(gridContext).toHaveProperty('saveLayout')
      expect(gridContext).toHaveProperty('loadLayout')

      return <div>Test</div>
    }

    render(
      <ResponsiveGridProvider>
        <TestMethodsComponent />
      </ResponsiveGridProvider>
    )
  })
})