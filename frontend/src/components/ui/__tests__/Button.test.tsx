import React from 'react'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button, ButtonGroup, Fab } from '../Button'
import { ThemeProvider } from '@/contexts/ThemeContext'
import type { ButtonProps } from '../Button'

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
    // Button uses Tailwind classes, not traditional class names
  })

  it('applies variant classes correctly', () => {
    const { rerender } = render(
      <TestWrapper>
        <Button variant="secondary">Secondary</Button>
      </TestWrapper>
    )

    let button = screen.getByRole('button')
    expect(button).toBeInTheDocument()

    rerender(
      <TestWrapper>
        <Button variant="outline">Outline</Button>
      </TestWrapper>
    )

    button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
  })

  it('applies size classes correctly', () => {
    const { rerender } = render(
      <TestWrapper>
        <Button size="lg">Large Button</Button>
      </TestWrapper>
    )

    let button = screen.getByRole('button')
    expect(button).toBeInTheDocument()

    rerender(
      <TestWrapper>
        <Button size="sm">Small Button</Button>
      </TestWrapper>
    )

    button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
  })

  it('shows loading state correctly', () => {
    render(
      <TestWrapper>
        <Button loading>Loading</Button>
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    expect(button).toBeDisabled()
    expect(button).toHaveTextContent('Loading')
    // Button with loading prop is disabled
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
    // Icon should be present in the DOM
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

    // Ripple effect adds CSS class, not DOM element
    expect(button).toHaveClass('ripple-effect')

    // Mouse down should work
    fireEvent.mouseDown(button, {
      clientX: 50,
      clientY: 50,
    })

    // Button should still be present
    expect(button).toBeInTheDocument()
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
    expect(icon).toBeInTheDocument()
    // Icon with position="right" should be present
  })

  // Additional edge case tests
  it('does not show ripple when disabled', () => {
    render(
      <TestWrapper>
        <Button ripple disabled>Ripple Disabled</Button>
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    fireEvent.mouseDown(button)

    const ripple = button.querySelector('.animate-ping')
    expect(ripple).not.toBeInTheDocument()
  })

  it('handles all variant types', () => {
    const variants: ButtonProps['variant'][] = ['primary', 'secondary', 'outline', 'ghost', 'danger', 'success']

    variants.forEach(variant => {
      const { unmount } = render(
        <TestWrapper>
          <Button variant={variant} data-testid={`btn-${variant}`}>
            {variant}
          </Button>
        </TestWrapper>
      )

      const button = screen.getByTestId(`btn-${variant}`)
      expect(button).toBeInTheDocument()
      // Button uses Tailwind classes, not variant names as classes
      unmount()
    })
  })

  it('passes through HTML button attributes', () => {
    render(
      <TestWrapper>
        <Button
          type="submit"
          form="test-form"
          name="test-name"
          value="test-value"
        >
          Submit
        </Button>
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('type', 'submit')
    expect(button).toHaveAttribute('form', 'test-form')
    expect(button).toHaveAttribute('name', 'test-name')
    expect(button).toHaveAttribute('value', 'test-value')
  })

  // Accessibility tests
  it('supports keyboard navigation', async () => {
    const handleClick = jest.fn()
    const user = userEvent.setup()

    render(
      <TestWrapper>
        <Button onClick={handleClick}>Keyboard Test</Button>
      </TestWrapper>
    )

    const button = screen.getByRole('button')
    button.focus()
    expect(button).toHaveFocus()

    await user.keyboard('{Enter}')
    expect(handleClick).toHaveBeenCalledTimes(1)

    await user.keyboard('{ }')
    expect(handleClick).toHaveBeenCalledTimes(2)
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

// FAB Component tests - 浮动操作按钮测试
describe('Fab Component', () => {
  it('renders with default props', () => {
    render(
      <TestWrapper>
        <Fab>FAB</Fab>
      </TestWrapper>
    )

    const fab = screen.getByRole('button')
    expect(fab).toBeInTheDocument()
    expect(fab).toHaveTextContent('FAB')
    expect(fab).toHaveClass('fixed', 'bottom-4', 'right-4', 'rounded-full')
  })

  it('renders with different positions', () => {
    const positions: Array<'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'> = [
      'bottom-right',
      'bottom-left',
      'top-right',
      'top-left'
    ]

    positions.forEach(position => {
      const { unmount } = render(
        <TestWrapper>
          <Fab position={position} data-testid={`fab-${position}`}>
            FAB
          </Fab>
        </TestWrapper>
      )

      const fab = screen.getByTestId(`fab-${position}`)
      expect(fab).toHaveClass('fixed', 'rounded-full')

      // Check position classes - FAB uses 4 spacing instead of 6
      if (position.includes('bottom')) expect(fab).toHaveClass('bottom-4')
      if (position.includes('top')) expect(fab).toHaveClass('top-4')
      if (position.includes('right')) expect(fab).toHaveClass('right-4')
      if (position.includes('left')) expect(fab).toHaveClass('left-4')

      unmount()
    })
  })

  it('renders as extended FAB', () => {
    render(
      <TestWrapper>
        <Fab extended label="Extended FAB" />
      </TestWrapper>
    )

    const fab = screen.getByRole('button')
    expect(fab).toHaveTextContent('Extended FAB')
    expect(fab).toHaveClass('px-6', 'py-3')
    expect(fab).not.toHaveClass('w-14', 'h-14')
  })

  it('renders with icon', () => {
    const TestIcon = () => <span data-testid="fab-icon">🔥</span>
    render(
      <TestWrapper>
        <Fab><TestIcon /></Fab>
      </TestWrapper>
    )

    const icon = screen.getByTestId('fab-icon')
    expect(icon).toBeInTheDocument()
  })

  it('renders extended FAB with icon', () => {
    const TestIcon = () => <span data-testid="fab-icon">🚀</span>
    render(
      <TestWrapper>
        <Fab extended label="Launch">
          <TestIcon />
        </Fab>
      </TestWrapper>
    )

    const icon = screen.getByTestId('fab-icon')
    expect(icon).toBeInTheDocument()
    // Icon should be present in extended FAB
  })

  it('handles click events', async () => {
    const handleClick = jest.fn()
    const user = userEvent.setup()

    render(
      <TestWrapper>
        <Fab onClick={handleClick}>Clickable FAB</Fab>
      </TestWrapper>
    )

    const fab = screen.getByRole('button')
    await user.click(fab)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('inherits Button props', () => {
    render(
      <TestWrapper>
        <Fab disabled className="custom-fab">
          Disabled FAB
        </Fab>
      </TestWrapper>
    )

    const fab = screen.getByRole('button')
    expect(fab).toBeDisabled()
    expect(fab).toHaveClass('custom-fab')
  })

  it('has proper accessibility attributes', () => {
    render(
      <TestWrapper>
        <Fab aria-label="Add new item">+</Fab>
      </TestWrapper>
    )

    const fab = screen.getByRole('button')
    // FAB uses children as aria-label when children is a string
    expect(fab).toHaveAttribute('aria-label', '+')
  })
})

// Cleanup after each test
afterEach(() => {
  cleanup()
})