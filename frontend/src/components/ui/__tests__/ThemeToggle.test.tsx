import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeToggle, ThemeSelector } from '../ThemeToggle'
import { ThemeProvider } from '@/contexts/ThemeContext'

// Test wrapper - 测试包装器
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    {children}
  </ThemeProvider>
)

// Theme Toggle tests - 主题切换测试
describe('ThemeToggle Component', () => {
  it('renders correctly', () => {
    render(
      <TestWrapper>
        <ThemeToggle />
      </TestWrapper>
    )

    const toggle = screen.getByRole('switch')
    expect(toggle).toBeInTheDocument()
    expect(toggle).toHaveAttribute('aria-checked', 'false')
  })

  it('shows label when showLabel is true', () => {
    render(
      <TestWrapper>
        <ThemeToggle showLabel />
      </TestWrapper>
    )

    expect(screen.getByText('Light')).toBeInTheDocument()
  })

  it('toggles theme on click', () => {
    render(
      <TestWrapper>
        <ThemeToggle />
      </TestWrapper>
    )

    const toggle = screen.getByRole('switch')
    expect(toggle).toHaveAttribute('aria-checked', 'false')

    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-checked', 'true')

    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-checked', 'false')
  })

  it('applies size classes correctly', () => {
    const { container } = render(
      <TestWrapper>
        <ThemeToggle size="lg" />
      </TestWrapper>
    )

    const toggle = container.querySelector('[role="switch"]')
    expect(toggle).toHaveClass('w-14', 'h-8')
  })

  it('applies custom className', () => {
    const { container } = render(
      <TestWrapper>
        <ThemeToggle className="custom-class" />
      </TestWrapper>
    )

    const toggle = container.querySelector('[role="switch"]')
    expect(toggle).toHaveClass('custom-class')
  })
})

// Theme Selector tests - 主题选择器测试
describe('ThemeSelector Component', () => {
  it('renders correctly with default trigger', () => {
    render(
      <TestWrapper>
        <ThemeSelector />
      </TestWrapper>
    )

    expect(screen.getByText('Light')).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('opens dropdown on click', () => {
    render(
      <TestWrapper>
        <ThemeSelector />
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    expect(screen.getByText('Dark')).toBeInTheDocument()
    expect(screen.getByText('Light')).toBeInTheDocument()
  })

  it('closes dropdown when clicking outside', () => {
    render(
      <TestWrapper>
        <ThemeSelector />
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    // Click backdrop - 点击背景
    const backdrop = document.querySelector('.fixed.inset-0')
    expect(backdrop).toBeInTheDocument()
    fireEvent.click(backdrop!)

    // Should be closed - 应该已关闭
    expect(screen.queryByText('Dark')).not.toBeInTheDocument()
  })

  it('selects theme on option click', () => {
    render(
      <TestWrapper>
        <ThemeSelector />
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    const darkOption = screen.getByText('Dark')
    fireEvent.click(darkOption)

    expect(button).toHaveTextContent('Dark')
  })

  it('shows selected theme with checkmark', () => {
    render(
      <TestWrapper>
        <ThemeSelector />
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    // Light should be selected by default - 默认应选中Light
    const lightOption = screen.getByText('Light').closest('button')
    const checkmark = lightOption?.querySelector('svg')
    expect(checkmark).toBeInTheDocument()
  })

  it('uses custom trigger when provided', () => {
    const CustomTrigger = () => <button>Custom Trigger</button>

    render(
      <TestWrapper>
        <ThemeSelector trigger={<CustomTrigger />} />
      </TestWrapper>
    )

    expect(screen.getByText('Custom Trigger')).toBeInTheDocument()
  })

  it('applies size classes correctly', () => {
    const { container } = render(
      <TestWrapper>
        <ThemeSelector size="lg" />
      </TestWrapper>
    )

    const button = container.querySelector('button')
    expect(button).toHaveClass('px-4', 'py-2', 'text-base')
  })
})