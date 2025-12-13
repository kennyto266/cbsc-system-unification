import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button, ButtonGroup } from '../Button'
import { ThemeProvider } from '@/styles/themes'

// Test wrapper - 测试包装器
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    {children}
  </ThemeProvider>
)

// Button component tests - 按钮组件测试
describe('Button Component', () => {
  it('renders correctly with default props', () => {
    render(
      <TestWrapper>
        <Button>Test Button</Button>
      </TestWrapper>
    )

    const button = screen.getByRole('button', { name: /test button/i })
    expect(button).toBeInTheDocument()
    expect(button).toHaveClass('btn', 'primary', 'md')
  })

  it('applies variant classes correctly', () => {
    const { rerender } = render(
      <TestWrapper>
        <Button variant="secondary">Secondary</Button>
      </TestWrapper>
    )

    let button = screen.getByRole('button')
    expect(button).toHaveClass('secondary')

    rerender(
      <TestWrapper>
        <Button variant="outline">Outline</Button>
      </TestWrapper>
    )

    button = screen.getByRole('button')
    expect(button).toHaveClass('outline')
  })

  it('applies size classes correctly', () => {
    const { rerender } = render(
      <TestWrapper>
        <Button size="lg">Large Button</Button>
      </TestWrapper>
    )

    let button = screen.getByRole('button')
    expect(button).toHaveClass('lg')

    rerender(
      <TestWrapper>
        <Button size="sm">Small Button</Button>
      </TestWrapper>
    )

    button = screen.getByRole('button')
    expect(button).toHaveClass('sm')
  })

  it('shows loading state correctly', () => {
    render(
      <TestWrapper>
        <Button loading>Loading</Button>
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-busy', 'true')

    // Check for spinner - 检查加载动画
    const spinner = button.querySelector('svg')
    expect(spinner).toBeInTheDocument()
    expect(spinner).toHaveClass('animate-spin')
  })

  it('handles click events', () => {
    const handleClick = jest.fn()
    render(
      <TestWrapper>
        <Button onClick={handleClick}>Click me</Button>
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not trigger click when disabled', () => {
    const handleClick = jest.fn()
    render(
      <TestWrapper>
        <Button disabled onClick={handleClick}>
          Disabled
        </Button>
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    fireEvent.click(button)

    expect(handleClick).not.toHaveBeenCalled()
  })

  it('renders with icon', () => {
    const TestIcon = () => <span data-testid="test-icon">🔥</span>
    render(
      <TestWrapper>
        <Button icon={<TestIcon />}>With Icon</Button>
      </TestWrapper>
    )

    const icon = screen.getByTestId('test-icon')
    expect(icon).toBeInTheDocument()
    expect(icon.parentElement).toHaveClass('mr-2')
  })

  it('renders with full width', () => {
    render(
      <TestWrapper>
        <Button fullWidth>Full Width</Button>
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    expect(button).toHaveClass('w-full')
  })

  it('applies custom className', () => {
    render(
      <TestWrapper>
        <Button className="custom-class">Custom</Button>
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    expect(button).toHaveClass('custom-class')
  })

  it('supports ripple effect', () => {
    render(
      <TestWrapper>
        <Button ripple>Ripple</Button>
      </TestWrapper>
    )

    const button = screen.getByRole('button')

    // Mouse down should create ripple - 鼠标按下应创建涟漪
    fireEvent.mouseDown(button, {
      clientX: 50,
      clientY: 50,
    })

    // Check for ripple element - 检查涟漪元素
    const ripple = button.querySelector('.animate-ping')
    expect(ripple).toBeInTheDocument()
  })

  it('handles icon on the right', () => {
    const TestIcon = () => <span data-testid="test-icon">👉</span>
    render(
      <TestWrapper>
        <Button icon={<TestIcon />} iconPosition="right">
          Right Icon
        </Button>
      </TestWrapper>
    )

    const icon = screen.getByTestId('test-icon')
    expect(icon.parentElement).toHaveClass('ml-2')
  })
})

// Button Group tests - 按钮组测试
describe('ButtonGroup Component', () => {
  it('renders children correctly', () => {
    render(
      <TestWrapper>
        <ButtonGroup>
          <Button>Button 1</Button>
          <Button>Button 2</Button>
        </ButtonGroup>
      </TestWrapper>
    )

    const buttons = screen.getAllByRole('button')
    expect(buttons).toHaveLength(2)
    expect(screen.getByText('Button 1')).toBeInTheDocument()
    expect(screen.getByText('Button 2')).toBeInTheDocument()
  })

  it('applies spacing correctly', () => {
    const { container } = render(
      <TestWrapper>
        <ButtonGroup spacing="lg">
          <Button>Button 1</Button>
          <Button>Button 2</Button>
        </ButtonGroup>
      </TestWrapper>
    )

    const group = container.firstChild
    expect(group).toHaveClass('space-x-3')
  })

  it('applies alignment correctly', () => {
    const { container } = render(
      <TestWrapper>
        <ButtonGroup align="center">
          <Button>Button 1</Button>
          <Button>Button 2</Button>
        </ButtonGroup>
      </TestWrapper>
    )

    const group = container.firstChild
    expect(group).toHaveClass('justify-center')
  })
})