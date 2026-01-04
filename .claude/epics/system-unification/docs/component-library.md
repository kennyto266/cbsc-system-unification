# CBSC Component Library Documentation

## Overview

The CBSC Component Library is a collection of reusable React components built with TypeScript, Tailwind CSS, and accessibility best practices. These components are designed for financial data visualization and trading operations.

## Component Structure

```
frontend/src/components/
├── ui/                    # Base UI components
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Select.tsx
│   ├── Checkbox.tsx
│   ├── Radio.tsx
│   ├── Modal.tsx
│   ├── Alert.tsx
│   ├── Badge.tsx
│   ├── Tooltip.tsx
│   └── index.ts
├── Layout/                # Layout components
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   ├── Footer.tsx
│   ├── Container.tsx
│   └── Grid.tsx
├── Charts/                # Chart components
│   ├── LineChart.tsx
│   ├── PerformanceChart.tsx
│   ├── CandlestickChart.tsx
│   └── ChartDashboard.tsx
├── StrategyControl/       # Strategy-specific components
│   ├── StrategyToggle.tsx
│   ├── StrategyMonitor.tsx
│   └── StrategySelector.tsx
└── Forms/                 # Form components
    ├── FormField.tsx
    ├── FormLabel.tsx
    └── FormError.tsx
```

## Base UI Components

### Button

A versatile button component with multiple variants and sizes.

```typescript
import { Button } from '@/components/ui/Button';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  fullWidth?: boolean;
}

// Usage examples
<Button variant="primary" size="md" onClick={handleClick}>
  Save Changes
</Button>

<Button variant="danger" size="sm" loading={isDeleting}>
  Delete
</Button>

<Button variant="ghost" size="xs" icon={<Icon />}>
  Icon Button
</Button>
```

**Variants:**
- `primary`: Blue background for primary actions
- `secondary`: Gray background for secondary actions
- `success`: Green background for positive actions
- `danger`: Red background for destructive actions
- `ghost`: Transparent background for minimal actions

**Sizes:**
- `xs`: 24px height - compact buttons
- `sm`: 32px height - small buttons
- `md`: 40px height - standard buttons (default)
- `lg`: 48px height - large buttons

### Input

A text input component with validation states.

```typescript
import { Input } from '@/components/ui/Input';

interface InputProps {
  type?: 'text' | 'email' | 'password' | 'number';
  size?: 'sm' | 'md' | 'lg';
  state?: 'default' | 'error' | 'success';
  placeholder?: string;
  disabled?: boolean;
  value: string;
  onChange: (value: string) => void;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  error?: string;
  label?: string;
  required?: boolean;
}

// Usage examples
<Input
  type="email"
  placeholder="user@example.com"
  value={email}
  onChange={setEmail}
  state={errors.email ? 'error' : 'default'}
  error={errors.email}
  label="Email Address"
  required
/>

<Input
  type="number"
  placeholder="Enter amount"
  value={amount}
  onChange={setAmount}
  prefix="$"
  suffix="USD"
/>
```

### Select

A dropdown select component with search functionality.

```typescript
import { Select } from '@/components/ui/Select';

interface SelectProps<T> {
  options: Array<{ value: T; label: string; disabled?: boolean }>;
  value: T | null;
  onChange: (value: T) => void;
  placeholder?: string;
  disabled?: boolean;
  searchable?: boolean;
  size?: 'sm' | 'md' | 'lg';
  error?: string;
  label?: string;
  required?: boolean;
}

// Usage examples
<Select
  options={[
    { value: 'active', label: 'Active' },
    { value: 'paused', label: 'Paused' },
    { value: 'archived', label: 'Archived' },
  ]}
  value={status}
  onChange={setStatus}
  placeholder="Select status"
  label="Strategy Status"
/>

<Select
  options={strategies}
  value={selectedStrategy}
  onChange={setStrategy}
  searchable
  placeholder="Search strategies..."
/>
```

### Modal

A modal dialog component with header, body, and footer sections.

```typescript
import { Modal } from '@/components/ui/Modal';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOverlayClick?: boolean;
  closeOnEsc?: boolean;
  showCloseButton?: boolean;
}

// Modal sub-components
Modal.Header: React.FC<{ title: string }>;
Modal.Body: React.FC<{ children: React.ReactNode }>;
Modal.Footer: React.FC<{ children: React.ReactNode }>;

// Usage examples
<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Create Strategy"
  size="md"
>
  <Modal.Body>
    <CreateStrategyForm />
  </Modal.Body>
  <Modal.Footer>
    <Button variant="ghost" onClick={() => setIsOpen(false)}>
      Cancel
    </Button>
    <Button variant="primary" onClick={handleSubmit}>
      Create
    </Button>
  </Modal.Footer>
</Modal>
```

### Alert

An alert component for displaying messages.

```typescript
import { Alert } from '@/components/ui/Alert';

interface AlertProps {
  type: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  message: string;
  dismissible?: boolean;
  icon?: React.ReactNode;
  onClose?: () => void;
}

// Usage examples
<Alert
  type="success"
  title="Success"
  message="Strategy created successfully"
  dismissible
/>

<Alert
  type="error"
  title="Error"
  message="Failed to create strategy"
  icon={<ErrorIcon />}
/>
```

## Layout Components

### Header

Application header with navigation and user menu.

```typescript
import { Header } from '@/components/Layout/Header';

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
  notifications?: Notification[];
}

// Usage
<Header
  user={currentUser}
  onLogout={handleLogout}
  notifications={notifications}
/>
```

### Sidebar

Collapsible sidebar with navigation menu.

```typescript
import { Sidebar } from '@/components/Layout/Sidebar';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  navigation: NavItem[];
  activePath: string;
}

// Usage
<Sidebar
  collapsed={collapsed}
  onToggle={() => setCollapsed(!collapsed)}
  navigation={navItems}
  activePath={location.pathname}
/>
```

## Chart Components

### Line Chart

Basic line chart for time series data.

```typescript
import { LineChart } from '@/components/Charts/LineChart';

interface LineChartProps {
  data: Array<{ timestamp: string; value: number }>;
  xKey: string;
  yKey: string;
  title?: string;
  color?: 'primary' | 'success' | 'danger' | 'warning';
  height?: number;
  showTooltip?: boolean;
  showLegend?: boolean;
}

// Usage
<LineChart
  data={priceData}
  xKey="timestamp"
  yKey="price"
  title="Price History"
  color="primary"
  height={300}
  showTooltip
/>
```

### Performance Chart

Advanced performance chart with benchmarks.

```typescript
import { PerformanceChart } from '@/components/Charts/PerformanceChart';

interface PerformanceChartProps {
  data: PerformanceData[];
  benchmarks?: BenchmarkData[];
  showTooltip?: boolean;
  height?: number;
}

// Usage
<PerformanceChart
  data={strategyPerformance}
  benchmarks={marketBenchmarks}
  height={400}
  showTooltip
/>
```

## Strategy Components

### StrategyToggle

Toggle component for strategy activation.

```typescript
import { StrategyToggle } from '@/components/StrategyControl/StrategyToggleEnhanced';

interface StrategyToggleProps {
  strategy: Strategy;
  onToggle: (id: number, active: boolean) => void;
}

// Usage
<StrategyToggle
  strategy={strategy}
  onToggle={handleToggle}
/>
```

## Best Practices

### Component Composition

```typescript
// Compose components for complex UIs
function StrategyCard({ strategy }: { strategy: Strategy }) {
  return (
    <Card>
      <Card.Header>
        <div className="flex justify-between">
          <h3>{strategy.name}</h3>
          <StrategyToggle strategy={strategy} onToggle={handleToggle} />
        </div>
      </Card.Header>
      <Card.Body>
        <PerformanceMetrics strategy={strategy} />
      </Card.Body>
      <Card.Footer>
        <Button onClick={() => viewDetails(strategy.id)}>View Details</Button>
      </Card.Footer>
    </Card>
  );
}
```

### Accessibility

```typescript
// Always include proper ARIA labels
<button
  aria-label="Close dialog"
  aria-pressed={isPressed}
  onClick={handleClose}
>
  <XIcon />
</button>

// Use semantic HTML
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/strategies">Strategies</a></li>
    <li><a href="/portfolio">Portfolio</a></li>
  </ul>
</nav>

// Support keyboard navigation
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') closeModal();
  if (e.key === 'Enter') handleSubmit();
};
```

### Performance

```typescript
// Use React.memo for expensive components
const ExpensiveChart = React.memo(({ data }: { data: ChartData[] }) => {
  return <LineChart data={data} />;
});

// Use useMemo for expensive calculations
const sortedStrategies = useMemo(() => {
  return strategies.sort((a, b) => b.return - a.return);
}, [strategies]);

// Use useCallback for event handlers
const handleClick = useCallback(() => {
  navigate(`/strategies/${id}`);
}, [id]);
```

### Error Handling

```typescript
// Wrap components in error boundaries
function ComponentWithErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      fallback={
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-600">Something went wrong</p>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}
```

## Testing

### Component Testing

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  test('renders button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  test('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('does not call onClick when disabled', () => {
    const handleClick = vi.fn();
    render(
      <Button onClick={handleClick} disabled>
        Click me
      </Button>
    );

    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  test('shows loading state', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

### Accessibility Testing

```typescript
import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';

describe('Button accessibility', () => {
  test('should not have accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

## Storybook Integration

```typescript
// Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Primary Button',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary Button',
  },
};

export const Loading: Story = {
  args: {
    variant: 'primary',
    loading: true,
    children: 'Loading...',
  },
};
```

## Contributing

When adding new components:

1. **Create component file** in appropriate directory
2. **Add TypeScript types** for props
3. **Implement accessibility** features
4. **Write tests** with React Testing Library
5. **Create Storybook stories** for documentation
6. **Update index.ts** to export component
7. **Follow naming conventions** (PascalCase for files)

---
*Document Version: 1.0*
*Created: 2025-12-25*
*Author: CBSC System Unification Team*
