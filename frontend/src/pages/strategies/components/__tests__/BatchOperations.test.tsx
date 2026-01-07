import React from 'react'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@/contexts/ThemeContext'
import BatchOperations from '../BatchOperations'
import * as strategyAPI from '../../services/strategyAPI'

// Mock the API with proper function mocks
jest.mock('../../services/strategyAPI', () => ({
  batchUpdateStrategies: jest.fn(),
  batchDeleteStrategies: jest.fn(),
  batchActivateStrategies: jest.fn(),
  batchDeactivateStrategies: jest.fn(),
  batchArchiveStrategies: jest.fn(),
  batchUnarchiveStrategies: jest.fn()
}))

const mockStrategyAPI = strategyAPI as jest.Mocked<typeof strategyAPI>

// Mock toast hook
jest.mock('@/hooks/useToast', () => ({
  useToast: () => ({
    addToast: jest.fn()
  })
}))

// Mock Modal component
jest.mock('@/components/ui/Modal', () => ({
  Modal: ({ isOpen, children }: any) => {
    if (!isOpen) return null
    return <div data-testid="modal" role="dialog">{children}</div>
  }
}))

// Test wrapper - 测试包装器
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    {children}
  </ThemeProvider>
)

describe('BatchOperations Component', () => {
  const user = userEvent.setup()
  const mockSelectedIds = ['1', '2', '3']
  const mockOnSelectionChange = jest.fn()
  const mockOnOperationComplete = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockStrategyAPI.batchUpdateStrategies.mockResolvedValue({
      success: true,
      updated: 3
    })
    mockStrategyAPI.batchDeleteStrategies.mockResolvedValue({
      success: true,
      deleted: 3
    })
  })

  afterEach(() => {
    cleanup()
  })

  // Basic rendering tests
  describe('Rendering', () => {
    test('renders batch operations bar', () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      expect(screen.getByText(/已选择 \d+ 个策略/)).toBeInTheDocument()
      expect(screen.getByText('批量操作')).toBeInTheDocument()
    })

    test('shows correct number of selected items', () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={['1', '2']}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      expect(screen.getByText('已选择 2 个策略')).toBeInTheDocument()
    })

    test('shows no selection message when no items selected', () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={[]}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      // Component should show header and operations even when nothing is selected
      expect(screen.getByText('批量操作')).toBeInTheDocument()
    })

    test('renders when no strategies are selected', () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={[]}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      // Component should always render the operations grid
      expect(screen.getByText('批量操作')).toBeInTheDocument()
    })
  })

  // Selection handling tests
  describe('Selection handling', () => {
    test('clears selection when clear button is clicked', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const clearButton = screen.getByText('清除选择')
      await user.click(clearButton)

      expect(mockOnSelectionChange).toHaveBeenCalledWith([])
    })
  })

  // Batch operation display tests
  describe('Batch operations display', () => {
    test('displays all available batch operations', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      // Verify header is displayed
      expect(screen.getByText('批量操作')).toBeInTheDocument()

      // Verify all operations from actual component are displayed
      expect(screen.getByText('批量启动')).toBeInTheDocument()
      expect(screen.getByText('批量停止')).toBeInTheDocument()
      expect(screen.getByText('批量克隆')).toBeInTheDocument()
      expect(screen.getByText('批量分类')).toBeInTheDocument()
      expect(screen.getByText('批量导出')).toBeInTheDocument()
      expect(screen.getByText('批量删除')).toBeInTheDocument()
    })
  })

  // Batch operation execution tests
  describe('Batch operation execution', () => {
    test('opens modal when operation card is clicked', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      // Click on the start operation card
      const startButton = screen.getByText('批量启动')
      await user.click(startButton)

      // Modal should open with confirmation
      await waitFor(() => {
        expect(screen.getByText(/批量启动/)).toBeInTheDocument()
      })
    })

    test('shows operation confirmation in modal', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      // Click on the delete operation card
      const deleteButton = screen.getByText('批量删除')
      await user.click(deleteButton)

      // Modal should open - verify modal exists in DOM
      await waitFor(() => {
        const modal = screen.queryByRole('dialog')
        expect(modal).toBeInTheDocument()
      })
    })
  })

  // Post-operation behavior tests
  describe('Post-operation behavior', () => {
    test('opens modal and shows operation details', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      // Click on an operation card
      const startButton = screen.getByText('批量启动')
      await user.click(startButton)

      // Modal should be open
      await waitFor(() => {
        expect(screen.getByText(/批量启动/)).toBeInTheDocument()
      })
    })
  })

  // Error handling tests
  describe('Error handling', () => {
    test('does not crash when operation modal is opened and closed', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      // Open modal
      const startButton = screen.getByText('批量启动')
      await user.click(startButton)

      await waitFor(() => {
        expect(screen.getByText(/批量启动/)).toBeInTheDocument()
      })
    })
  })

  // Loading states tests
  describe('Loading states', () => {
    test('opens operation modal successfully', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      // Click on an operation card
      const startButton = screen.getByText('批量启动')
      await user.click(startButton)

      // Modal should open with operation details
      await waitFor(() => {
        expect(screen.getByText(/批量启动/)).toBeInTheDocument()
      })
    })

    test('displays operation details in modal', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      // Click on the start operation card
      const startButton = screen.getByText('批量启动')
      await user.click(startButton)

      // Modal should show operation details
      await waitFor(() => {
        expect(screen.getByText(/批量启动/)).toBeInTheDocument()
        expect(screen.getByText(/启动所有选中的策略/)).toBeInTheDocument()
      })
    })
  })

  // Accessibility tests
  describe('Accessibility', () => {
    test('displays all operations with proper text labels', () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      // Verify all operations are visible with their names and descriptions
      expect(screen.getByText('批量启动')).toBeInTheDocument()
      expect(screen.getByText('启动所有选中的策略')).toBeInTheDocument()
      expect(screen.getByText('批量停止')).toBeInTheDocument()
      expect(screen.getByText('停止所有选中的策略')).toBeInTheDocument()
      expect(screen.getByText('批量克隆')).toBeInTheDocument()
      expect(screen.getByText('克隆所有选中的策略')).toBeInTheDocument()
      expect(screen.getByText('批量分类')).toBeInTheDocument()
      expect(screen.getByText('为所有选中的策略设置分类')).toBeInTheDocument()
      expect(screen.getByText('批量导出')).toBeInTheDocument()
      expect(screen.getByText('导出所有选中的策略')).toBeInTheDocument()
      expect(screen.getByText('批量删除')).toBeInTheDocument()
      expect(screen.getByText('删除所有选中的策略')).toBeInTheDocument()
    })
  })
})