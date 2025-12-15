import React from 'react'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input } from '../Input'
import { ThemeProvider } from '@/styles/themes'

// Test wrapper - 测试包装器
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    {children}
  </ThemeProvider>
)

describe('Input Component', () => {
  const user = userEvent.setup()

  afterEach(() => {
    cleanup()
  })

  // Basic rendering tests
  describe('Rendering', () => {
    test('renders with minimal props', () => {
      render(
        <TestWrapper>
          <Input />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toBeInTheDocument()
      expect(input).toHaveClass(
        'block',
        'w-full',
        'px-3',
        'py-2',
        'text-sm',
        'border',
        'rounded-lg',
        'focus:outline-none',
        'focus:ring-2',
        'focus:ring-offset-0',
        'transition-all',
        'duration-200',
        'disabled:bg-neutral-100',
        'disabled:text-neutral-500',
        'border-neutral-300',
        'focus:ring-primary-500',
        'focus:border-primary-500'
      )
    })

    test('renders with placeholder', () => {
      render(
        <TestWrapper>
          <Input placeholder="Enter text here" />
        </TestWrapper>
      )

      const input = screen.getByPlaceholderText('Enter text here')
      expect(input).toBeInTheDocument()
    })

    test('renders with custom className', () => {
      render(
        <TestWrapper>
          <Input className="custom-input" />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('custom-input')
    })

    test('renders with value', () => {
      render(
        <TestWrapper>
          <Input value="Test value" readOnly />
        </TestWrapper>
      )

      const input = screen.getByDisplayValue('Test value')
      expect(input).toBeInTheDocument()
    })

    test('renders as disabled', () => {
      render(
        <TestWrapper>
          <Input disabled />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toBeDisabled()
      expect(input).toHaveClass('disabled:bg-neutral-100', 'disabled:text-neutral-500')
    })

    test('renders with different input types', () => {
      const types = ['text', 'email', 'password', 'number', 'tel', 'url', 'search']

      types.forEach(type => {
        const { unmount } = render(
          <TestWrapper>
            <Input type={type as any} data-testid={`input-${type}`} />
          </TestWrapper>
        )

        const input = screen.getByTestId(`input-${type}`)
        expect(input).toHaveAttribute('type', type)
        unmount()
      })
    })
  })

  // Label tests
  describe('Label', () => {
    test('renders with label', () => {
      render(
        <TestWrapper>
          <Input label="Username" />
        </TestWrapper>
      )

      expect(screen.getByText('Username')).toBeInTheDocument()
      const label = screen.getByText('Username')
      expect(label.tagName).toBe('LABEL')
      expect(label).toHaveClass('block', 'text-sm', 'font-medium', 'text-neutral-700', 'mb-1')
    })

    test('associates label with input', () => {
      render(
        <TestWrapper>
          <Input label="Email" id="email-input" />
        </TestWrapper>
      )

      const label = screen.getByText('Email')
      const input = screen.getByRole('textbox')

      expect(label).toHaveAttribute('for', 'email-input')
      expect(input).toHaveAttribute('id', 'email-input')
    })

    test('renders without label when not provided', () => {
      render(
        <TestWrapper>
          <Input />
        </TestWrapper>
      )

      // Should not find any label elements
      expect(screen.queryByRole('label')).not.toBeInTheDocument()
    })
  })

  // Error state tests
  describe('Error state', () => {
    test('renders with error message', () => {
      render(
        <TestWrapper>
          <Input error="This field is required" />
        </TestWrapper>
      )

      const errorMessage = screen.getByText('This field is required')
      expect(errorMessage).toBeInTheDocument()
      expect(errorMessage).toHaveClass('mt-1', 'text-sm', 'text-error-600')

      const input = screen.getByRole('textbox')
      expect(input).toHaveClass(
        'border-error-500',
        'focus:ring-error-500',
        'focus:border-error-500'
      )
    })

    test('does not show helper text when error is present', () => {
      render(
        <TestWrapper>
          <Input
            error="Error message"
            helperText="Helper text"
          />
        </TestWrapper>
      )

      expect(screen.getByText('Error message')).toBeInTheDocument()
      expect(screen.queryByText('Helper text')).not.toBeInTheDocument()
    })

    test('applies error styles to input', () => {
      render(
        <TestWrapper>
          <Input error="Invalid input" />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('border-error-500')
    })
  })

  // Helper text tests
  describe('Helper text', () => {
    test('renders with helper text', () => {
      render(
        <TestWrapper>
          <Input helperText="Enter at least 8 characters" />
        </TestWrapper>
      )

      const helperText = screen.getByText('Enter at least 8 characters')
      expect(helperText).toBeInTheDocument()
      expect(helperText).toHaveClass('mt-1', 'text-sm', 'text-neutral-500')
    })

    test('does not show helper text when error is present', () => {
      render(
        <TestWrapper>
          <Input
            helperText="Helper message"
            error="Error message"
          />
        </TestWrapper>
      )

      expect(screen.getByText('Error message')).toBeInTheDocument()
      expect(screen.queryByText('Helper message')).not.toBeInTheDocument()
    })
  })

  // Icon tests
  describe('Icons', () => {
    test('renders with left icon', () => {
      const TestIcon = () => <span data-testid="left-icon">🔍</span>

      render(
        <TestWrapper>
          <Input leftIcon={<TestIcon />} />
        </TestWrapper>
      )

      const icon = screen.getByTestId('left-icon')
      expect(icon).toBeInTheDocument()

      const iconContainer = icon.parentElement
      expect(iconContainer).toHaveClass(
        'absolute',
        'inset-y-0',
        'left-0',
        'pl-3',
        'flex',
        'items-center',
        'pointer-events-none'
      )

      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('pl-10')
    })

    test('renders with right icon', () => {
      const TestIcon = () => <span data-testid="right-icon">✓</span>

      render(
        <TestWrapper>
          <Input rightIcon={<TestIcon />} />
        </TestWrapper>
      )

      const icon = screen.getByTestId('right-icon')
      expect(icon).toBeInTheDocument()

      const iconContainer = icon.parentElement
      expect(iconContainer).toHaveClass(
        'absolute',
        'inset-y-0',
        'right-0',
        'pr-3',
        'flex',
        'items-center',
        'pointer-events-none'
      )

      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('pr-10')
    })

    test('renders with both left and right icons', () => {
      const LeftIcon = () => <span data-testid="left-icon">🔍</span>
      const RightIcon = () => <span data-testid="right-icon">✓</span>

      render(
        <TestWrapper>
          <Input
            leftIcon={<LeftIcon />}
            rightIcon={<RightIcon />}
          />
        </TestWrapper>
      )

      expect(screen.getByTestId('left-icon')).toBeInTheDocument()
      expect(screen.getByTestId('right-icon')).toBeInTheDocument()

      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('pl-10', 'pr-10')
    })

    test('icons are non-interactive', () => {
      const TestIcon = () => <span data-testid="icon">🔍</span>

      render(
        <TestWrapper>
          <Input leftIcon={<TestIcon />} />
        </TestWrapper>
      )

      const iconContainer = screen.getByTestId('icon').parentElement
      expect(iconContainer).toHaveClass('pointer-events-none')
    })
  })

  // Interaction tests
  describe('Interactions', () => {
    test('handles user input', async () => {
      const handleChange = jest.fn()

      render(
        <TestWrapper>
          <Input onChange={handleChange} />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      await user.type(input, 'Hello World')

      expect(handleChange).toHaveBeenCalledTimes(11) // Once for each character
      expect(input).toHaveValue('Hello World')
    })

    test('handles focus events', async () => {
      const handleFocus = jest.fn()
      const handleBlur = jest.fn()

      render(
        <TestWrapper>
          <Input
            onFocus={handleFocus}
            onBlur={handleBlur}
          />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')

      await user.click(input)
      expect(handleFocus).toHaveBeenCalledTimes(1)
      expect(input).toHaveFocus()

      await user.tab() // Move focus away
      expect(handleBlur).toHaveBeenCalledTimes(1)
      expect(input).not.toHaveFocus()
    })

    test('handles paste events', async () => {
      const handlePaste = jest.fn()

      render(
        <TestWrapper>
          <Input onPaste={handlePaste} />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')

      await user.click(input)
      await user.paste('Copied text')

      expect(input).toHaveValue('Copied text')
    })

    test('prevents input when disabled', async () => {
      render(
        <TestWrapper>
          <Input disabled />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      await user.type(input, 'Cannot type')

      expect(input).toHaveValue('')
    })

    test('prevents input when readonly', async () => {
      render(
        <TestWrapper>
          <Input readOnly value="Initial value" />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      await user.type(input, 'Cannot modify')

      expect(input).toHaveValue('Initial value')
    })
  })

  // Form integration tests
  describe('Form integration', () => {
    test('works as controlled component', () => {
      const TestComponent = () => {
        const [value, setValue] = React.useState('')

        return (
          <Input
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        )
      }

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('')

      fireEvent.change(input, { target: { value: 'Controlled' } })
      expect(input).toHaveValue('Controlled')
    })

    test('works as uncontrolled component', async () => {
      render(
        <TestWrapper>
          <Input defaultValue="Default" />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('Default')

      await user.clear(input)
      await user.type(input, 'New value')
      expect(input).toHaveValue('New value')
    })

    test('supports form submission', async () => {
      const handleSubmit = jest.fn(e => e.preventDefault())

      render(
        <TestWrapper>
          <form onSubmit={handleSubmit}>
            <Input name="testField" defaultValue="Test" />
            <button type="submit">Submit</button>
          </form>
        </TestWrapper>
      )

      const button = screen.getByRole('button', { name: 'Submit' })
      await user.click(button)

      expect(handleSubmit).toHaveBeenCalled()
    })

    test('supports required validation', () => {
      render(
        <TestWrapper>
          <form>
            <Input required />
            <button type="submit">Submit</button>
          </form>
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toBeRequired()
    })
  })

  // Accessibility tests
  describe('Accessibility', () => {
    test('supports ARIA attributes', () => {
      render(
        <TestWrapper>
          <Input
            aria-label="Search input"
            aria-describedby="search-description"
            aria-invalid="false"
          />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-label', 'Search input')
      expect(input).toHaveAttribute('aria-describedby', 'search-description')
      expect(input).toHaveAttribute('aria-invalid', 'false')
    })

    test('associates error message with input', () => {
      render(
        <TestWrapper>
          <Input
            error="Error message"
            id="input-with-error"
          />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      const errorMessage = screen.getByText('Error message')

      // Check if input references the error message
      expect(input).toHaveAttribute('aria-describedby')
      expect(input).toHaveAttribute('id', 'input-with-error')
    })

    test('supports auto-completion', () => {
      render(
        <TestWrapper>
          <Input
            autoComplete="email"
            list="email-suggestions"
          />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('autoComplete', 'email')
      expect(input).toHaveAttribute('list', 'email-suggestions')
    })

    test('handles keyboard navigation', async () => {
      render(
        <TestWrapper>
          <Input />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')

      // Tab to focus
      await user.tab()
      expect(input).toHaveFocus()

      // Type and navigate with arrow keys
      await user.type(input, 'test')
      await user.keyboard('{ArrowLeft}{ArrowRight}')

      // Select all text
      await user.keyboard('{Control>}{a}{/Control}')
    })
  })

  // Edge cases
  describe('Edge cases', () => {
    test('handles very long values', () => {
      render(
        <TestWrapper>
          <Input
            value={'a'.repeat(1000)}
            onChange={() => {}}
          />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toHaveValue('a'.repeat(1000))
    })

    test('handles special characters', async () => {
      render(
        <TestWrapper>
          <Input />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      const specialChars = '!@#$%^&*()_+-=[]{}|;:,.<>?'

      await user.type(input, specialChars)
      expect(input).toHaveValue(specialChars)
    })

    test('handles multiline input gracefully', () => {
      render(
        <TestWrapper>
          <Input value="Line 1\nLine 2\nLine 3" readOnly />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toBeInTheDocument()
    })
  })
})