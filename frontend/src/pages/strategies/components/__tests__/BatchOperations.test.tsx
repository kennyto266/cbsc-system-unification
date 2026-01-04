import React from 'react'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@/contexts/ThemeContext'
import BatchOperations from '../BatchOperations'
import * as strategyAPI from '../../services/strategyAPI'

// Mock the API
jest.mock('../../services/strategyAPI')
const mockStrategyAPI = strategyAPI as jest.Mocked<typeof strategyAPI>

// Mock toast hook
jest.mock('@/hooks/useToast', () => ({
  useToast: () => ({
    addToast: jest.fn()
  })
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

      expect(screen.getByText('未选择任何策略')).toBeInTheDocument()
      expect(screen.getByText('批量操作')).toBeDisabled()
    })

    test('does not render when no strategies exist', () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={[]}
            strategies={[]}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      expect(screen.queryByText('批量操作')).not.toBeInTheDocument()
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

    test('selects all strategies when select all is clicked', async () => {
      const allStrategies = [
        { id: '1', name: 'Strategy 1' },
        { id: '2', name: 'Strategy 2' },
        { id: '3', name: 'Strategy 3' }
      ]

      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={[]}
            strategies={allStrategies}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const selectAllButton = screen.getByText('全选')
      await user.click(selectAllButton)

      expect(mockOnSelectionChange).toHaveBeenCalledWith(['1', '2', '3'])
    })
  })

  // Batch operation dropdown tests
  describe('Batch operations dropdown', () => {
    test('opens dropdown when batch operations button is clicked', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      expect(screen.getByText('批量启动')).toBeInTheDocument()
      expect(screen.getByText('批量停止')).toBeInTheDocument()
      expect(screen.getByText('批量暂停')).toBeInTheDocument()
      expect(screen.getByText('批量删除')).toBeInTheDocument()
      expect(screen.getByText('批量编辑')).toBeInTheDocument()
    })

    test('closes dropdown when clicking outside', async () => {
      render(
        <TestWrapper>
          <div>
            <BatchOperations
              selectedIds={mockSelectedIds}
              onSelectionChange={mockOnSelectionChange}
              onOperationComplete={mockOnOperationComplete}
            />
            <button data-testid="outside-element">Outside</button>
          </div>
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      expect(screen.getByText('批量启动')).toBeInTheDocument()

      const outsideElement = screen.getByTestId('outside-element')
      await user.click(outsideElement)

      await waitFor(() => {
        expect(screen.queryByText('批量启动')).not.toBeInTheDocument()
      })
    })
  })

  // Batch operation execution tests
  describe('Batch operation execution', () => {
    test('executes batch start operation', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const startButton = screen.getByText('批量启动')
      await user.click(startButton)

      await waitFor(() => {
        expect(mockStrategyAPI.batchUpdateStrategies).toHaveBeenCalledWith({
          ids: mockSelectedIds,
          updates: { status: 'active' }
        })
      })
    })

    test('executes batch stop operation', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const stopButton = screen.getByText('批量停止')
      await user.click(stopButton)

      await waitFor(() => {
        expect(mockStrategyAPI.batchUpdateStrategies).toHaveBeenCalledWith({
          ids: mockSelectedIds,
          updates: { status: 'inactive' }
        })
      })
    })

    test('executes batch pause operation', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const pauseButton = screen.getByText('批量暂停')
      await user.click(pauseButton)

      await waitFor(() => {
        expect(mockStrategyAPI.batchUpdateStrategies).toHaveBeenCalledWith({
          ids: mockSelectedIds,
          updates: { status: 'paused' }
        })
      })
    })

    test('shows confirmation dialog for batch delete', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const deleteButton = screen.getByText('批量删除')
      await user.click(deleteButton)

      expect(screen.getByText(/确定要删除选中的 \d+ 个策略吗？/)).toBeInTheDocument()
      expect(screen.getByText('此操作不可撤销')).toBeInTheDocument()
    })

    test('executes batch delete after confirmation', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const deleteButton = screen.getByText('批量删除')
      await user.click(deleteButton)

      const confirmButton = screen.getByText('确定删除')
      await user.click(confirmButton)

      await waitFor(() => {
        expect(mockStrategyAPI.batchDeleteStrategies).toHaveBeenCalledWith({
          ids: mockSelectedIds
        })
      })
    })

    test('opens batch edit modal', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const editButton = screen.getByText('批量编辑')
      await user.click(editButton)

      expect(screen.getByText('批量编辑策略')).toBeInTheDocument()
      expect(screen.getByLabelText('策略类别')).toBeInTheDocument()
    })
  })

  // Post-operation behavior tests
  describe('Post-operation behavior', () => {
    test('clears selection after successful operation', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const startButton = screen.getByText('批量启动')
      await user.click(startButton)

      await waitFor(() => {
        expect(mockOnSelectionChange).toHaveBeenCalledWith([])
      })
    })

    test('calls onOperationComplete after successful operation', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const stopButton = screen.getByText('批量停止')
      await user.click(stopButton)

      await waitFor(() => {
        expect(mockOnOperationComplete).toHaveBeenCalled()
      })
    })
  })

  // Error handling tests
  describe('Error handling', () => {
    test('shows error message when batch operation fails', async () => {
      mockStrategyAPI.batchUpdateStrategies.mockRejectedValue(
        new Error('Batch operation failed')
      )

      const mockAddToast = jest.fn()
      jest.mocked(require('@/hooks/useToast').useToast).mockReturnValue({
        addToast: mockAddToast
      })

      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const startButton = screen.getByText('批量启动')
      await user.click(startButton)

      await waitFor(() => {
        expect(mockAddToast).toHaveBeenCalledWith({
          type: 'error',
          message: '批量启动失败'
        })
      })
    })

    test('handles partial success in batch operations', async () => {
      mockStrategyAPI.batchUpdateStrategies.mockResolvedValue({
        success: true,
        updated: 2,
        failed: ['3'],
        errors: ['Strategy 3 update failed']
      })

      const mockAddToast = jest.fn()
      jest.mocked(require('@/hooks/useToast').useToast).mockReturnValue({
        addToast: mockAddToast
      })

      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const startButton = screen.getByText('批量启动')
      await user.click(startButton)

      await waitFor(() => {
        expect(mockAddToast).toHaveBeenCalledWith({
          type: 'warning',
          message: '部分策略操作失败'
        })
      })
    })
  })

  // Loading states tests
  describe('Loading states', () => {
    test('shows loading state during batch operation', async () => {
      mockStrategyAPI.batchUpdateStrategies.mockReturnValue(
        new Promise(resolve => setTimeout(() => resolve({
          success: true,
          updated: 3
        }), 1000))
      )

      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const startButton = screen.getByText('批量启动')
      await user.click(startButton)

      // Check for loading state
      expect(screen.getByText('正在执行批量操作...')).toBeInTheDocument()
      expect(dropdownButton).toBeDisabled()
    })

    test('disables all operations during loading', async () => {
      mockStrategyAPI.batchUpdateStrategies.mockReturnValue(
        new Promise(() => {}) // Never resolves
      )

      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const startButton = screen.getByText('批量启动')
      await user.click(startButton)

      // Check that buttons are disabled
      expect(screen.getByText('清除选择')).toBeDisabled()
      expect(screen.getByText('全选')).toBeDisabled()
    })
  })

  // Batch edit modal tests
  describe('Batch edit modal', () => {
    test('updates multiple strategies via batch edit', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const editButton = screen.getByText('批量编辑')
      await user.click(editButton)

      const categorySelect = screen.getByLabelText('策略类别')
      await user.selectOptions(categorySelect, 'multi_factor')

      const saveButton = screen.getByText('保存更改')
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockStrategyAPI.batchUpdateStrategies).toHaveBeenCalledWith({
          ids: mockSelectedIds,
          updates: { category: 'multi_factor' }
        })
      })
    })

    test('closes batch edit modal without saving', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      await user.click(dropdownButton)

      const editButton = screen.getByText('批量编辑')
      await user.click(editButton)

      const cancelButton = screen.getByText('取消')
      await user.click(cancelButton)

      await waitFor(() => {
        expect(screen.queryByText('批量编辑策略')).not.toBeInTheDocument()
      })
    })
  })

  // Accessibility tests
  describe('Accessibility', () => {
    test('supports keyboard navigation', async () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      dropdownButton.focus()
      expect(dropdownButton).toHaveFocus()

      await user.keyboard('{Enter}')
      expect(screen.getByText('批量启动')).toBeInTheDocument()
    })

    test('has proper ARIA labels', () => {
      render(
        <TestWrapper>
          <BatchOperations
            selectedIds={mockSelectedIds}
            onSelectionChange={mockOnSelectionChange}
            onOperationComplete={mockOnOperationComplete}
          />
        </TestWrapper>
      )

      const dropdownButton = screen.getByText('批量操作')
      expect(dropdownButton).toHaveAttribute('aria-haspopup', 'true')
      expect(dropdownButton).toHaveAttribute('aria-expanded', 'false')
    })
  })
})