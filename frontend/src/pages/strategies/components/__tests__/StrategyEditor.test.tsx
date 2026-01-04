import React from 'react'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { ThemeProvider } from '@/contexts/ThemeContext'
import StrategyEditor from '../StrategyEditor'
import * as strategyAPI from '../../services/strategyAPI'

// Mock the API
jest.mock('../../services/strategyAPI')
const mockStrategyAPI = strategyAPI as jest.Mocked<typeof strategyAPI>

// Mock navigation
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ id: '123' })
}))

// Test wrapper with Router and Theme - 带路由和主题的测试包装器
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    <MemoryRouter>
      {children}
    </MemoryRouter>
  </ThemeProvider>
)

// Mock strategy data
const mockStrategy = {
  id: '123',
  name: '测试策略',
  description: '这是一个测试策略',
  category: 'core_cbsc',
  type: 'momentum',
  status: 'active',
  parameters: {
    lookbackPeriod: 20,
    threshold: 0.02,
    stopLoss: 0.05
  },
  performance: {
    totalReturn: 0.15,
    sharpeRatio: 1.5,
    maxDrawdown: 0.05,
    winRate: 0.6
  },
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-12-01T00:00:00Z'
}

describe('StrategyEditor Component', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
    mockStrategyAPI.getStrategy.mockResolvedValue(mockStrategy)
    mockStrategyAPI.updateStrategy.mockResolvedValue(mockStrategy)
    mockStrategyAPI.createStrategy.mockResolvedValue({ ...mockStrategy, id: '456' })
  })

  afterEach(() => {
    cleanup()
  })

  // Basic rendering tests
  describe('Rendering', () => {
    test('renders strategy editor form', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('策略编辑器')).toBeInTheDocument()
      })

      // Check for form fields
      expect(screen.getByLabelText('策略名称')).toBeInTheDocument()
      expect(screen.getByLabelText('策略描述')).toBeInTheDocument()
      expect(screen.getByLabelText('策略类别')).toBeInTheDocument()
    })

    test('loads existing strategy data when editing', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(mockStrategyAPI.getStrategy).toHaveBeenCalledWith('123')
      })

      await waitFor(() => {
        expect(screen.getByDisplayValue('测试策略')).toBeInTheDocument()
        expect(screen.getByDisplayValue('这是一个测试策略')).toBeInTheDocument()
      })
    })

    test('renders empty form when creating new strategy', async () => {
      render(
        <TestWrapper>
          <MemoryRouter initialEntries={['/strategies/create']}>
            <StrategyEditor />
          </MemoryRouter>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('创建新策略')).toBeInTheDocument()
      })

      // Fields should be empty
      expect(screen.getByLabelText('策略名称')).toHaveValue('')
    })

    test('renders parameter configuration section', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('参数配置')).toBeInTheDocument()
      })

      // Check for parameter inputs
      expect(screen.getByLabelText('回看周期')).toBeInTheDocument()
      expect(screen.getByLabelText('阈值')).toBeInTheDocument()
      expect(screen.getByLabelText('止损比例')).toBeInTheDocument()
    })
  })

  // Form validation tests
  describe('Form validation', () => {
    test('validates required fields', async () => {
      mockStrategyAPI.getStrategy.mockResolvedValue(null) // No existing strategy

      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('创建新策略')).toBeInTheDocument()
      })

      // Try to submit without required fields
      const saveButton = screen.getByText('保存')
      await user.click(saveButton)

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText('策略名称是必填项')).toBeInTheDocument()
        expect(screen.getByText('策略类别是必选项')).toBeInTheDocument()
      })
    })

    test('validates numeric input ranges', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const lookbackInput = screen.getByLabelText('回看周期')
        await user.clear(lookbackInput)
        await user.type(lookbackInput, '-5')

        const saveButton = screen.getByText('保存')
        await user.click(saveButton)

        expect(screen.getByText('回看周期必须大于0')).toBeInTheDocument()
      })
    })

    test('shows success message on valid submission', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        // Form should load with valid data
        expect(screen.getByDisplayValue('测试策略')).toBeInTheDocument()
      })

      const saveButton = screen.getByText('保存')
      await user.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText('策略保存成功')).toBeInTheDocument()
      })
    })
  })

  // Form interaction tests
  describe('Form interactions', () => {
    test('updates strategy name', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const nameInput = screen.getByLabelText('策略名称')
        await user.clear(nameInput)
        await user.type(nameInput, '新策略名称')

        expect(nameInput).toHaveValue('新策略名称')
      })
    })

    test('updates strategy description', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const descInput = screen.getByLabelText('策略描述')
        await user.clear(descInput)
        await user.type(descInput, '新的策略描述')

        expect(descInput).toHaveValue('新的策略描述')
      })
    })

    test('changes strategy category', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const categorySelect = screen.getByLabelText('策略类别')
        await user.selectOptions(categorySelect, 'multi_factor')

        expect(categorySelect).toHaveValue('multi_factor')
      })
    })

    test('updates numeric parameters', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const lookbackInput = screen.getByLabelText('回看周期')
        await user.clear(lookbackInput)
        await user.type(lookbackInput, '30')

        expect(lookbackInput).toHaveValue(30)
      })
    })
  })

  // Save functionality tests
  describe('Save functionality', () => {
    test('saves strategy with updated data', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const nameInput = screen.getByLabelText('策略名称')
        await user.clear(nameInput)
        await user.type(nameInput, '更新后的策略')
      })

      const saveButton = screen.getByText('保存')
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockStrategyAPI.updateStrategy).toHaveBeenCalledWith('123', {
          name: '更新后的策略',
          description: expect.any(String),
          category: expect.any(String),
          parameters: expect.any(Object)
        })
      })
    })

    test('creates new strategy when no ID provided', async () => {
      render(
        <TestWrapper>
          <MemoryRouter initialEntries={['/strategies/create']}>
            <StrategyEditor />
          </MemoryRouter>
        </TestWrapper>
      )

      await waitFor(() => {
        const nameInput = screen.getByLabelText('策略名称')
        await user.type(nameInput, '新策略')
      })

      const saveButton = screen.getByText('保存')
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockStrategyAPI.createStrategy).toHaveBeenCalledWith({
          name: '新策略',
          description: expect.any(String),
          category: expect.any(String),
          parameters: expect.any(Object)
        })
      })
    })

    test('navigates back after successful save', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      const saveButton = screen.getByText('保存')
      await user.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText('策略保存成功')).toBeInTheDocument()
      })

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/strategies')
      }, { timeout: 3000 })
    })
  })

  // Cancel functionality tests
  describe('Cancel functionality', () => {
    test('shows confirmation dialog when cancelling with changes', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const nameInput = screen.getByLabelText('策略名称')
        await user.clear(nameInput)
        await user.type(nameInput, '修改')
      })

      const cancelButton = screen.getByText('取消')
      await user.click(cancelButton)

      expect(screen.getByText('确定要放弃所有更改吗？')).toBeInTheDocument()
    })

    test('navigates back when confirmed to cancel', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const nameInput = screen.getByLabelText('策略名称')
        await user.clear(nameInput)
      })

      const cancelButton = screen.getByText('取消')
      await user.click(cancelButton)

      const confirmButton = screen.getByText('确定')
      await user.click(confirmButton)

      expect(mockNavigate).toHaveBeenCalled()
    })

    test('stays on page when cancelled cancellation', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const nameInput = screen.getByLabelText('策略名称')
        await user.clear(nameInput)
      })

      const cancelButton = screen.getByText('取消')
      await user.click(cancelButton)

      const stayButton = screen.getByText('继续编辑')
      await user.click(stayButton)

      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  // Preview functionality tests
  describe('Preview functionality', () => {
    test('shows strategy preview', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      const previewButton = screen.getByText('预览')
      await user.click(previewButton)

      await waitFor(() => {
        expect(screen.getByText('策略预览')).toBeInTheDocument()
        expect(screen.getByText('测试策略')).toBeInTheDocument()
        expect(screen.getByText('这是一个测试策略')).toBeInTheDocument()
      })
    })

    test('closes preview modal', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      const previewButton = screen.getByText('预览')
      await user.click(previewButton)

      await waitFor(() => {
        const closeButton = screen.getByText('关闭')
        await user.click(closeButton)

        expect(screen.queryByText('策略预览')).not.toBeInTheDocument()
      })
    })
  })

  // Advanced features tests
  describe('Advanced features', () => {
    test('shows advanced parameters section', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      const advancedToggle = screen.getByText('高级设置')
      await user.click(advancedToggle)

      expect(screen.getByText('高级参数')).toBeInTheDocument()
    })

    test('handles parameter presets', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      const presetButton = screen.getByText('预设参数')
      await user.click(presetButton)

      await waitFor(() => {
        expect(screen.getByText('保守型')).toBeInTheDocument()
        expect(screen.getByText('激进型')).toBeInTheDocument()
      })

      const conservativeOption = screen.getByText('保守型')
      await user.click(conservativeOption)

      // Check if parameters were updated
      await waitFor(() => {
        const stopLossInput = screen.getByLabelText('止损比例')
        expect(stopLossInput).toHaveValue(0.02) // Conservative preset
      })
    })
  })

  // Error handling tests
  describe('Error handling', () => {
    test('shows error message when save fails', async () => {
      mockStrategyAPI.updateStrategy.mockRejectedValue(new Error('Save failed'))

      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      const saveButton = screen.getByText('保存')
      await user.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText('保存失败，请重试')).toBeInTheDocument()
      })
    })

    test('shows error message when load fails', async () => {
      mockStrategyAPI.getStrategy.mockRejectedValue(new Error('Load failed'))

      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('加载策略失败')).toBeInTheDocument()
      })
    })
  })

  // Performance tests
  describe('Performance', () => {
    test('loads quickly with large parameter set', async () => {
      const startTime = performance.now()

      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('策略编辑器')).toBeInTheDocument()
      })

      const endTime = performance.now()
      expect(endTime - startTime).toBeLessThan(500) // Should load within 500ms
    })
  })

  // Accessibility tests
  describe('Accessibility', () => {
    test('has proper form labels', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByLabelText('策略名称')).toBeInTheDocument()
        expect(screen.getByLabelText('策略描述')).toBeInTheDocument()
        expect(screen.getByLabelText('策略类别')).toBeInTheDocument()
      })
    })

    test('supports keyboard navigation', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const nameInput = screen.getByLabelText('策略名称')
        nameInput.focus()
        expect(nameInput).toHaveFocus()

        await user.tab()
        // Should move to next form element
        expect(document.activeElement).not.toBe(nameInput)
      })
    })

    test('shows ARIA descriptions for help text', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const helpText = screen.getByText(/回看周期用于计算/)
        expect(helpText).toBeInTheDocument()
      })
    })
  })
})