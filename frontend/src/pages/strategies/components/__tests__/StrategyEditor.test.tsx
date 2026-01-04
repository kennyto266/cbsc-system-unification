import React from 'react'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MemoryRouter } from 'react-router-dom'
import StrategyEditor from '../StrategyEditor'

// Mock navigation
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useParams: () => ({ id: '123' })
}))

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  default: ({ onChange, value }: any) => (
    <div data-testid="monaco-editor">
      <textarea
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
        data-testid="code-editor"
      />
    </div>
  ),
}))

// Mock UI components
jest.mock('@/components/ui', () => ({
  Card: ({ children, className }: any) => <div className={className}>{children}</div>,
  Button: ({ children, onClick, disabled, variant }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant}>
      {children}
    </button>
  ),
  Input: ({ onChange, value, ...props }: any) => (
    <input onChange={onChange} value={value} {...props} />
  ),
  Select: ({ children, onChange, value, ...props }: any) => (
    <select onChange={onChange} value={value} {...props}>
      {children}
    </select>
  ),
  Textarea: ({ onChange, value, ...props }: any) => (
    <textarea onChange={onChange} value={value} {...props} />
  ),
  Badge: ({ children, variant }: any) => <span data-variant={variant}>{children}</span>,
  Progress: ({ value }: any) => <div role="progressbar" aria-valuenow={value} />,
}))

// Mock ThemeProvider
jest.mock('@/contexts/ThemeContext', () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useTheme: () => ({ theme: { mode: 'light' } }),
}))

// Mock useToast hook
jest.mock('@/hooks/useToast', () => ({
  useToast: () => ({
    addToast: jest.fn(),
  }),
}))

// Mock RTK Query hooks
jest.mock('@/store/api/apiSlice', () => ({
  useGetStrategyQuery: () => ({ data: null, isLoading: false }),
  useCreateStrategyMutation: () => [
    jest.fn(),
    {
      isLoading: false,
      mutateAsync: jest.fn(() => Promise.resolve({ id: '456', name: 'New Strategy' })),
    },
  ],
  useUpdateStrategyMutation: () => [
    jest.fn(),
    {
      isLoading: false,
      mutateAsync: jest.fn(() => Promise.resolve({ id: '123', name: 'Updated Strategy' })),
    },
  ],
}))

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <MemoryRouter>
    {children}
  </MemoryRouter>
)

describe('StrategyEditor Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
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
        expect(screen.getByText('编辑策略')).toBeInTheDocument()
      })

      // Check for basic elements
      expect(screen.getByText('基本信息')).toBeInTheDocument()
      expect(screen.getByText('参数配置')).toBeInTheDocument()
    })
  })

  // Navigation tests
  describe('Navigation', () => {
    test('navigates back when cancel button clicked', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('取消')).toBeInTheDocument()
      })

      const cancelButton = screen.getByText('取消')
      cancelButton.click()

      // Should navigate back
      expect(mockNavigate).toHaveBeenCalled()
    })
  })

  // Step navigation
  describe('Step Navigation', () => {
    test('shows step indicators', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('基本信息')).toBeInTheDocument()
        expect(screen.getByText('参数配置')).toBeInTheDocument()
        expect(screen.getByText('策略代码')).toBeInTheDocument()
        expect(screen.getByText('风险控制')).toBeInTheDocument()
        expect(screen.getByText('确认提交')).toBeInTheDocument()
      })
    })
  })

  // Form inputs
  describe('Form Inputs', () => {
    test('renders strategy name input', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('策略名称')).toBeInTheDocument()
      })
    })

    test('renders strategy type selector', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('策略类型')).toBeInTheDocument()
      })
    })
  })

  // Code editor
  describe('Code Editor', () => {
    test('renders Monaco editor placeholder', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        const editor = screen.queryByTestId('monaco-editor')
        expect(editor).toBeInTheDocument()
      })
    })
  })

  // Parameters step
  describe('Parameters Configuration', () => {
    test('renders parameter inputs when on params step', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('初始资金')).toBeInTheDocument()
        expect(screen.getByText('最大仓位')).toBeInTheDocument()
        expect(screen.getByText('止损')).toBeInTheDocument()
        expect(screen.getByText('止盈')).toBeInTheDocument()
      })
    })
  })

  // Action buttons
  describe('Action Buttons', () => {
    test('renders navigation buttons', async () => {
      render(
        <TestWrapper>
          <StrategyEditor />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('取消')).toBeInTheDocument()
        expect(screen.getByText('下一步')).toBeInTheDocument()
      })
    })
  })
})
