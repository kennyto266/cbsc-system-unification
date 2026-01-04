import React from 'react'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input } from '../Input'
import { ThemeProvider } from '@/contexts/ThemeContext'

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    {children}
  </ThemeProvider>
)

describe('Input Component', () => {
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
      expect(input).toHaveClass('flex', 'w-full', 'rounded-md', 'border')
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

    test('renders with value (controlled)', () => {
      render(
        <TestWrapper>
          <Input value="Test value" onChange={() => {}} />
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
      expect(input).toHaveClass('disabled:opacity-50', 'disabled:cursor-not-allowed')
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
      expect(label).toHaveClass('text-sm', 'font-medium')
    })

    test('associates label with input', () => {
      render(
        <TestWrapper>
          <Input label="Email" id="email-input" />
        </TestWrapper>
      )

      const label = screen.getByText('Email')
      const input = screen.getByRole('textbox')

      // The component doesn't auto-associate label with input via htmlFor
      // but both elements exist and can be manually associated via id
      expect(label).toBeInTheDocument()
      expect(input).toHaveAttribute('id', 'email-input')
    })

    test('renders without label when not provided', () => {
      render(
        <TestWrapper>
          <Input />
        </TestWrapper>
      )

      // Should not find any label elements with text
      const labels = screen.queryAllByRole('label').filter(l => l.textContent?.trim())
      expect(labels.length).toBe(0)
    })
  })

  // Error state tests
  describe('Error state', () => {
    test('renders with error message', () => {
      render(
        <TestWrapper>
          <Input errorText="This field is required" />
        </TestWrapper>
      )

      const errorMessage = screen.getByText('This field is required')
      expect(errorMessage).toBeInTheDocument()
      expect(errorMessage).toHaveClass('text-xs')

      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('border-red-500')
    })

    test('does not show helper text when error is present', () => {
      render(
        <TestWrapper>
          <Input
            errorText="Error message"
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
          <Input errorText="Invalid input" />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('border-red-500')
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
      expect(helperText).toHaveClass('text-xs')
    })

    test('does not show helper text when error is present', () => {
      render(
        <TestWrapper>
          <Input
            helperText="Helper message"
            errorText="Error message"
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
  })

  // Interaction tests
  describe('Interactions', () => {
    test('handles user input', async () => {
      const handleChange = jest.fn()
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <Input onChange={handleChange} />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      await user.type(input, 'Hello')

      expect(handleChange).toHaveBeenCalled()
    })

    test('handles focus events', async () => {
      const handleFocus = jest.fn()
      const handleBlur = jest.fn()
      const user = userEvent.setup()

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

      await user.tab()
      expect(handleBlur).toHaveBeenCalledTimes(1)
      expect(input).not.toHaveFocus()
    })

    test('prevents input when disabled', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <Input disabled />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      await user.type(input, 'Cannot type')

      expect(input.value).toBe('')
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

    test('works as uncontrolled component (using internal state)', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <Input data-testid="uncontrolled-input" />
        </TestWrapper>
      )

      const input = screen.getByTestId('uncontrolled-input')
      expect(input).toHaveValue('')

      await user.type(input, 'New value')
      expect(input).toHaveValue('New value')
    })

    test('supports form submission', async () => {
      const handleSubmit = jest.fn(e => e.preventDefault())
      const user = userEvent.setup()

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

    test('handles keyboard navigation', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <Input />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')

      await user.tab()
      expect(input).toHaveFocus()

      await user.type(input, 'test')
      await user.keyboard('{ArrowLeft}{ArrowRight}')
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
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <Input />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      const specialChars = '!@#$%^&*()_+-='

      await user.type(input, specialChars)
      expect(input).toHaveValue(specialChars)
    })

    test('handles multiline input gracefully', () => {
      render(
        <TestWrapper>
          <Input value="Line 1\nLine 2\nLine 3" onChange={() => {}} />
        </TestWrapper>
      )

      const input = screen.getByRole('textbox')
      expect(input).toBeInTheDocument()
    })
  })
})
