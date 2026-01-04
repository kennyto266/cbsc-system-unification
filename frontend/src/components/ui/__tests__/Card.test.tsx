import React from 'react'
import { render, screen, cleanup } from '@testing-library/react'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../Card'

describe('Card Component', () => {
  afterEach(() => {
    cleanup()
  })

  describe('Card Container', () => {
    test('renders with default styling', () => {
      const { container } = render(
        <div>
          <Card>Card Content</Card>
        </div>
      )

      const card = container.querySelector('.rounded-lg')
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
      const { container } = render(
        <div>
          <Card className="custom-card">Content</Card>
        </div>
      )

      const card = container.querySelector('.custom-card')
      expect(card).toBeInTheDocument()
      expect(card).toHaveClass('custom-card')
    })

    test('renders complex content', () => {
      render(
        <div>
          <Card>
            <h2>Title</h2>
            <p>Description</p>
            <button>Action</button>
          </Card>
        </div>
      )

      expect(screen.getByRole('heading', { name: 'Title' })).toBeInTheDocument()
      expect(screen.getByText('Description')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument()
    })

    test('supports data attributes', () => {
      render(
        <div>
          <Card data-testid="test-card">Content</Card>
        </div>
      )

      const card = screen.getByTestId('test-card')
      expect(card).toBeInTheDocument()
      expect(card).toHaveTextContent('Content')
    })
  })

  describe('CardHeader', () => {
    test('renders with default styling', () => {
      const { container } = render(
        <div>
          <CardHeader>Header Content</CardHeader>
        </div>
      )

      const header = container.querySelector('.flex.flex-col')
      expect(header).toBeInTheDocument()
      expect(header).toHaveClass(
        'flex',
        'flex-col',
        'space-y-1.5',
        'p-6'
      )
    })

    test('renders with custom className', () => {
      const { container } = render(
        <div>
          <CardHeader className="custom-header">Header</CardHeader>
        </div>
      )

      const header = container.querySelector('.custom-header')
      expect(header).toBeInTheDocument()
      expect(header).toHaveClass('custom-header')
    })

    test('renders complex header content', () => {
      render(
        <div>
          <CardHeader>
            <h2>Card Title</h2>
            <p>Subtitle</p>
            <button>Menu</button>
          </CardHeader>
        </div>
      )

      expect(screen.getByRole('heading', { name: 'Card Title' })).toBeInTheDocument()
      expect(screen.getByText('Subtitle')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Menu' })).toBeInTheDocument()
    })
  })

  describe('CardTitle', () => {
    test('renders as h3 element with default styling', () => {
      render(
        <div>
          <CardTitle>Card Title</CardTitle>
        </div>
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
        <div>
          <CardTitle className="custom-title">Title</CardTitle>
        </div>
      )

      const title = screen.getByRole('heading', { level: 3 })
      expect(title).toHaveClass('custom-title')
    })

    test('renders with long content', () => {
      render(
        <div>
          <CardTitle>
            This is a very long card title that should wrap properly when it exceeds the container width
          </CardTitle>
        </div>
      )

      const title = screen.getByRole('heading', { level: 3 })
      expect(title).toBeInTheDocument()
      // The title should handle long text gracefully
      expect(title.textContent).toContain('This is a very long card title')
    })
  })

  describe('CardContent', () => {
    test('renders with default styling', () => {
      const { container } = render(
        <div>
          <CardContent>Content here</CardContent>
        </div>
      )

      const content = container.querySelector('.p-6.pt-0')
      expect(content).toBeInTheDocument()
      expect(content).toHaveClass(
        'p-6',
        'pt-0'
      )
    })

    test('renders with custom className', () => {
      const { container } = render(
        <div>
          <CardContent className="custom-content">Content</CardContent>
        </div>
      )

      const content = container.querySelector('.custom-content')
      expect(content).toBeInTheDocument()
      expect(content).toHaveClass('custom-content')
    })

    test('renders complex content with multiple elements', () => {
      render(
        <div>
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
        </div>
      )

      expect(screen.getByText('Paragraph 1')).toBeInTheDocument()
      expect(screen.getByText('Item 1')).toBeInTheDocument()
      expect(screen.getByText('Item 2')).toBeInTheDocument()
      expect(screen.getByLabelText('Label')).toBeInTheDocument()
    })
  })

  describe('CardFooter', () => {
    test('renders with default styling', () => {
      const { container } = render(
        <div>
          <CardFooter>Footer Content</CardFooter>
        </div>
      )

      const footer = container.querySelector('.flex.items-center')
      expect(footer).toBeInTheDocument()
      expect(footer).toHaveClass(
        'flex',
        'items-center',
        'p-6',
        'pt-0'
      )
    })

    test('renders with custom className', () => {
      const { container } = render(
        <div>
          <CardFooter className="custom-footer">Footer</CardFooter>
        </div>
      )

      const footer = container.querySelector('.custom-footer')
      expect(footer).toBeInTheDocument()
      expect(footer).toHaveClass('custom-footer')
    })

    test('renders with action buttons', () => {
      render(
        <div>
          <CardFooter>
            <button>Cancel</button>
            <button>Submit</button>
          </CardFooter>
        </div>
      )

      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument()
    })

    test('aligns items correctly', () => {
      render(
        <div>
          <CardFooter>
            <span>Left content</span>
            <span style={{ marginLeft: 'auto' }}>Right content</span>
          </CardFooter>
        </div>
      )

      expect(screen.getByText('Left content')).toBeInTheDocument()
      expect(screen.getByText('Right content')).toBeInTheDocument()
    })
  })

  describe('Complete Card Composition', () => {
    test('renders all card components together', () => {
      render(
        <div>
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
        </div>
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
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Minimal Card</CardTitle>
            </CardHeader>
            <CardContent>
              Just title and content
            </CardContent>
          </Card>
        </div>
      )

      expect(screen.getByRole('heading', { name: 'Minimal Card' })).toBeInTheDocument()
      expect(screen.getByText('Just title and content')).toBeInTheDocument()
      // Footer should not be present
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })

    test('renders card with only content', () => {
      render(
        <div>
          <Card>
            <CardContent>
              Simple content only
            </CardContent>
          </Card>
        </div>
      )

      expect(screen.getByText('Simple content only')).toBeInTheDocument()
      // Header elements should not be present
      expect(screen.queryByRole('heading')).not.toBeInTheDocument()
    })

    test('handles nested content properly', () => {
      render(
        <div>
          <Card>
            <CardContent>
              <Card>
                <CardContent>Nested card content</CardContent>
              </Card>
            </CardContent>
          </Card>
        </div>
      )

      expect(screen.getByText('Nested card content')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    test('supports ARIA attributes', () => {
      render(
        <div>
          <Card role="article" aria-labelledby="card-title">
            <CardHeader>
              <CardTitle id="card-title">Accessible Card</CardTitle>
            </CardHeader>
            <CardContent>Content</CardContent>
          </Card>
        </div>
      )

      const card = screen.getByRole('article')
      expect(card).toHaveAttribute('aria-labelledby', 'card-title')
    })

    test('preserves semantic structure', () => {
      render(
        <div>
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
        </div>
      )

      expect(screen.getByRole('heading', { level: 3, name: 'Semantic Title' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { level: 4, name: 'Section Title' })).toBeInTheDocument()
      expect(screen.getByText('Section content')).toBeInTheDocument()
    })
  })
})