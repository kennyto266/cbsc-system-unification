import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeToggle, ThemeSelector } from '../ThemeToggle'

// Mock useTheme hook - Mock useTheme hook
const mockToggleTheme = jest.fn()
const mockSetTheme = jest.fn()

jest.mock('@/styles/themes', () => ({
  useTheme: () => ({
    theme: 'light',
    themeConfig: {
      name: 'light',
      colors: { background: {}, text: {}, border: {}, icon: {} },
      components: {},
      status: {},
      chart: {}
    },
    setTheme: mockSetTheme,
    toggleTheme: mockToggleTheme,
  }),
}))

// Theme Toggle tests - 主题切换测试
describe('ThemeToggle Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders correctly', () => {
    render(<ThemeToggle />)

    const toggle = screen.getByRole('switch')
    expect(toggle).toBeInTheDocument()
    expect(toggle).toHaveAttribute('aria-checked', 'false')
  })

  it('shows label when showLabel is true', () => {
    render(<ThemeToggle showLabel />)

    expect(screen.getByText('Light')).toBeInTheDocument()
  })

  it('toggles theme on click', () => {
    render(<ThemeToggle />)

    const toggle = screen.getByRole('switch')
    expect(toggle).toHaveAttribute('aria-checked', 'false')

    fireEvent.click(toggle)
    expect(mockToggleTheme).toHaveBeenCalledTimes(1)
  })

  it('applies size classes correctly', () => {
    const { container } = render(<ThemeToggle size="lg" />)

    const toggle = container.querySelector('[role="switch"]')
    expect(toggle).toHaveClass('w-14', 'h-8')
  })

  it('applies custom className', () => {
    const { container } = render(<ThemeToggle className="custom-class" />)

    const toggle = container.querySelector('[role="switch"]')
    expect(toggle).toHaveClass('custom-class')
  })
})

// Theme Selector tests - 主题选择器测试
describe('ThemeSelector Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders correctly with default trigger', () => {
    render(<ThemeSelector />)

    expect(screen.getByText('Light')).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('opens dropdown on click', () => {
    render(<ThemeSelector />)

    const button = screen.getByRole('button')
    fireEvent.click(button)

    expect(screen.getByText('Dark')).toBeInTheDocument()
    expect(screen.getAllByText('Light')).toHaveLength(2) // One in button, one in dropdown
  })

  it('closes dropdown when clicking outside', () => {
    render(<ThemeSelector />)

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
    render(<ThemeSelector />)

    const button = screen.getByRole('button')
    fireEvent.click(button)

    const darkOption = screen.getByText('Dark').closest('button')
    fireEvent.click(darkOption!)

    expect(mockSetTheme).toHaveBeenCalledWith('dark')
  })

  it('shows selected theme with checkmark', () => {
    render(<ThemeSelector />)

    const button = screen.getByRole('button')
    fireEvent.click(button)

    // Light should be selected by default - 默认应选中Light
    // Get all the Light text elements and find the one inside a button in the dropdown
    const lightOptions = screen.getAllByText('Light')
    const dropdownLightOption = lightOptions.find(text => {
      const button = text.closest('button')
      return button && button.getAttribute('role') === 'option'
    })
    expect(dropdownLightOption).toBeInTheDocument()

    const lightOptionButton = dropdownLightOption?.closest('button')
    const checkmark = lightOptionButton?.querySelector('svg[class*="w-4"]')
    expect(checkmark).toBeInTheDocument()
  })

  it('uses custom trigger when provided', () => {
    const CustomTrigger = () => <button>Custom Trigger</button>

    render(<ThemeSelector trigger={<CustomTrigger />} />)

    expect(screen.getByText('Custom Trigger')).toBeInTheDocument()
  })

  it('applies size classes correctly', () => {
    const { container } = render(<ThemeSelector size="lg" />)

    const button = container.querySelector('button')
    expect(button).toHaveClass('px-4', 'py-2', 'text-base')
  })
})