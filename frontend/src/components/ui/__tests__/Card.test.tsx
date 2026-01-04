import React from 'react'
import { render, screen, cleanup } from '@testing-library/react'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../Card'
import { ThemeProvider } from '@/contexts/ThemeContext'

// Test wrapper - 测试包装器
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    {children}
  </ThemeProvider>
)

describe('Card Component', () => {
  afterEach(() => {
    cleanup()
  })

  describe('Card Container', () => {
    test('renders with default styling', () => {
      render(
        <TestWrapper>
          <Card>Card Content</Card>
        </TestWrapper>
      )

      const card = screen.getByText('Card Content').parentElement
      expect(card).toBeInTheDocument()
      expect(card).toHaveClass(
        'rounded-lg',
        'border',
        'border-gray-200',
        'bg-white',
        'shadow-sm'
      )
    })

    test('renders with custom className', () => {
      render(
        <TestWrapper>
          <Card className="custom-card">Content</Card>
        </TestWrapper>
      )

      const card = screen.getByText('Content').parentElement
      expect(card).toHaveClass('custom-card')
    })

    test('renders complex content', () => {
      render(
        <TestWrapper>
          <Card>
            <h2>Title</h2>
            <p>Description</p>
            <button>Action</button>
          </Card>
        </TestWrapper>
      )

      expect(screen.getByRole('heading', { name: 'Title' })).toBeInTheDocument()
      expect(screen.getByText('Description')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument()
    })

    test('supports data attributes', () => {
      render(
        <TestWrapper>
          <Card data-testid="test-card">Content</Card>
        </TestWrapper>
      )

      const card = screen.getByTestId('test-card')
      expect(card).toBeInTheDocument()
      expect(card).toHaveTextContent('Content')
    })
  })

  describe('CardHeader', () => {
    test('renders with default styling', () => {
      render(
        <TestWrapper>
          <CardHeader>Header Content</CardHeader>
        </TestWrapper>
      )

      const header = screen.getByText('Header Content').parentElement
      expect(header).toBeInTheDocument()
      expect(header).toHaveClass(
        'flex',
        'flex-col',
        'space-y-1.5',
        'p-6'
      )
    })

    test('renders with custom className', () => {
      render(
        <TestWrapper>
          <CardHeader className="custom-header">Header</CardHeader>
        </TestWrapper>
      )

      const header = screen.getByText('Header').parentElement
      expect(header).toHaveClass('custom-header')
    })

    test('renders complex header content', () => {
      render(
        <TestWrapper>
          <CardHeader>
            <h2>Card Title</h2>
            <p>Subtitle</p>
            <button>Menu</button>
          </CardHeader>
        </TestWrapper>
      )

      expect(screen.getByRole('heading', { name: 'Card Title' })).toBeInTheDocument()
      expect(screen.getByText('Subtitle')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Menu' })).toBeInTheDocument()
    })
  })

  describe('CardTitle', () => {
    test('renders as h3 element with default styling', () => {
      render(
        <TestWrapper>
          <CardTitle>Card Title</CardTitle>
        </TestWrapper>
      )

      const title = screen.getByRole('heading', { level: 3, name: 'Card Title' })
      expect(title).toBeInTheDocument()
      expect(title).toHaveClass(
        'text-2xl',
        'font-semibold',
        'leading-none',
        'tracking-tight'
      )
    })

    test('renders with custom className', () => {
      render(
        <TestWrapper>
          <CardTitle className="custom-title">Title</CardTitle>
        </TestWrapper>
      )

      const title = screen.getByRole('heading', { level: 3 })
      expect(title).toHaveClass('custom-title')
    })

    test('renders with long content', () => {
      render(
        <TestWrapper>
          <CardTitle>
            This is a very long card title that should wrap properly when it exceeds the container width
          </CardTitle>
        </TestWrapper>
      )

      const title = screen.getByRole('heading', { level: 3 })
      expect(title).toBeInTheDocument()
      // The title should handle long text gracefully
      expect(title.textContent).toContain('This is a very long card title')
    })
  })

  describe('CardContent', () => {
    test('renders with default styling', () => {
      render(
        <TestWrapper>
          <CardContent>Content here</CardContent>
        </TestWrapper>
      )

      const content = screen.getByText('Content here').parentElement
      expect(content).toBeInTheDocument()
      expect(content).toHaveClass(
        'p-6',
        'pt-0'
      )
    })

    test('renders with custom className', () => {
      render(
        <TestWrapper>
          <CardContent className="custom-content">Content</CardContent>
        </TestWrapper>
      )

      const content = screen.getByText('Content').parentElement
      expect(content).toHaveClass('custom-content')
    })

    test('renders complex content with multiple elements', () => {
      render(
        <TestWrapper>
          <CardContent>
            <p>Paragraph 1</p>
            <ul>
              <li>Item 1</li>
              <li>Item 2</li>
            </ul>
            <div>
              <label htmlFor="input">Label</label>
              <input id="input" type="text" />
            </div>
          </CardContent>
        </TestWrapper>
      )

      expect(screen.getByText('Paragraph 1')).toBeInTheDocument()
      expect(screen.getByText('Item 1')).toBeInTheDocument()
      expect(screen.getByText('Item 2')).toBeInTheDocument()
      expect(screen.getByLabelText('Label')).toBeInTheDocument()
    })
  })

  describe('CardFooter', () => {
    test('renders with default styling', () => {
      render(
        <TestWrapper>
          <CardFooter>Footer Content</CardFooter>
        </TestWrapper>
      )

      const footer = screen.getByText('Footer Content').parentElement
      expect(footer).toBeInTheDocument()
      expect(footer).toHaveClass(
        'flex',
        'items-center',
        'p-6',
        'pt-0'
      )
    })

    test('renders with custom className', () => {
      render(
        <TestWrapper>
          <CardFooter className="custom-footer">Footer</CardFooter>
        </TestWrapper>
      )

      const footer = screen.getByText('Footer').parentElement
      expect(footer).toHaveClass('custom-footer')
    })

    test('renders with action buttons', () => {
      render(
        <TestWrapper>
          <CardFooter>
            <button>Cancel</button>
            <button>Submit</button>
          </CardFooter>
        </TestWrapper>
      )

      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument()
    })

    test('aligns items correctly', () => {
      render(
        <TestWrapper>
          <CardFooter>
            <span>Left content</span>
            <span style={{ marginLeft: 'auto' }}>Right content</span>
          </CardFooter>
        </TestWrapper>
      )

      expect(screen.getByText('Left content')).toBeInTheDocument()
      expect(screen.getByText('Right content')).toBeInTheDocument()
    })
  })

  describe('Complete Card Composition', () => {
    test('renders all card components together', () => {
      render(
        <TestWrapper>
          <Card data-testid="complete-card">
            <CardHeader>
              <CardTitle>Complete Card</CardTitle>
            </CardHeader>
            <CardContent>
              <p>This is the card content area.</p>
              <p>It can contain multiple elements.</p>
            </CardContent>
            <CardFooter>
              <button>Cancel</button>
              <button>Save</button>
            </CardFooter>
          </Card>
        </TestWrapper>
      )

      const card = screen.getByTestId('complete-card')
      expect(card).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: 'Complete Card' })).toBeInTheDocument()
      expect(screen.getByText('This is the card content area.')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument()
    })

    test('renders card without all optional components', () => {
      render(
        <TestWrapper>
          <Card>
            <CardHeader>
              <CardTitle>Minimal Card</CardTitle>
            </CardHeader>
            <CardContent>
              Just title and content
            </CardContent>
          </Card>
        </TestWrapper>
      )

      expect(screen.getByRole('heading', { name: 'Minimal Card' })).toBeInTheDocument()
      expect(screen.getByText('Just title and content')).toBeInTheDocument()
      // Footer should not be present
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })

    test('renders card with only content', () => {
      render(
        <TestWrapper>
          <Card>
            <CardContent>
              Simple content only
            </CardContent>
          </Card>
        </TestWrapper>
      )

      expect(screen.getByText('Simple content only')).toBeInTheDocument()
      // Header elements should not be present
      expect(screen.queryByRole('heading')).not.toBeInTheDocument()
    })

    test('handles nested content properly', () => {
      render(
        <TestWrapper>
          <Card>
            <CardContent>
              <Card>
                <CardContent>Nested card content</CardContent>
              </Card>
            </CardContent>
          </Card>
        </TestWrapper>
      )

      expect(screen.getByText('Nested card content')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    test('supports ARIA attributes', () => {
      render(
        <TestWrapper>
          <Card role="article" aria-labelledby="card-title">
            <CardHeader>
              <CardTitle id="card-title">Accessible Card</CardTitle>
            </CardHeader>
            <CardContent>Content</CardContent>
          </Card>
        </TestWrapper>
      )

      const card = screen.getByRole('article')
      expect(card).toHaveAttribute('aria-labelledby', 'card-title')
    })

    test('preserves semantic structure', () => {
      render(
        <TestWrapper>
          <Card>
            <CardHeader>
              <CardTitle>Semantic Title</CardTitle>
            </CardHeader>
            <CardContent>
              <section>
                <h4>Section Title</h4>
                <p>Section content</p>
              </section>
            </CardContent>
          </Card>
        </TestWrapper>
      )

      expect(screen.getByRole('heading', { level: 3, name: 'Semantic Title' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { level: 4, name: 'Section Title' })).toBeInTheDocument()
      expect(screen.getByText('Section content')).toBeInTheDocument()
    })
  })
})