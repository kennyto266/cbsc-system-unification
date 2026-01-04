# CBSC Frontend Design System Documentation

## Overview

The CBSC Trading System frontend is built with React 18, TypeScript, Tailwind CSS, and a custom design system optimized for financial data visualization and trading operations.

## Tech Stack

### Core Framework
- **React**: 18.2.0 (Concurrent features, automatic batching)
- **TypeScript**: 5.3.3 (Strict mode enabled)
- **Vite**: 5.0.8 (Build tool with SWC compiler)
- **React Router**: 6.30.2 (Client-side routing with code splitting)

### UI & Styling
- **Tailwind CSS**: 3.3.6 (Utility-first CSS framework)
- **Ant Design**: 6.1.0 (Enterprise UI component library)
- **Headless UI**: 1.7.17 (Unstyled accessible components)
- **Heroicons**: 2.0.18 (SVG icon library)
- **Framer Motion**: 10.16.16 (Animation library)

### State Management
- **Redux Toolkit**: 2.11.2 (State management)
- **RTK Query**: Integrated (Data fetching and caching)
- **React Query**: 5.8.4 (Alternative for server state)

### Data Visualization
- **Chart.js**: 4.5.1 (Canvas-based charts)
- **Plotly.js**: 3.3.1 (Interactive scientific charts)
- **React Grid Layout**: 2.1.0 (Draggable dashboard layouts)

### Development Tools
- **Jest**: 30.2.0 (Unit testing)
- **Playwright**: E2E testing
- **ESLint**: 8.55.0 (Code linting)
- **Prettier**: 3.1.1 (Code formatting)
- **Husky**: 8.0.3 (Git hooks)

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoints
│   │   ├── baseQuery.ts  # RTK Query base configuration
│   │   └── endpoints/    # API endpoint definitions
│   ├── components/       # Reusable UI components
│   │   ├── ui/          # Base UI components (Button, Input, etc.)
│   │   ├── Charts/      # Chart components
│   │   ├── Layout/      # Layout components (Header, Sidebar)
│   │   └── StrategyControl/  # Strategy-specific components
│   ├── hooks/           # Custom React hooks
│   ├── pages/           # Page-level components
│   ├── services/        # Business logic services
│   ├── store/           # Redux store configuration
│   │   ├── slices/      # Redux slices
│   │   ├── services/    # RTK Query API services
│   │   └── index.ts     # Store configuration
│   ├── types/           # TypeScript type definitions
│   ├── utils/           # Utility functions
│   └── styles/          # Global styles (CSS)
├── public/              # Static assets
├── tests/               # Test files
├── index.html           # Entry HTML
├── vite.config.ts       # Vite configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Dependencies
```

## Design System

### Color Palette

#### Primary Colors
```css
/* Financial Blue - Trust and stability */
--color-primary-50: #eff6ff;
--color-primary-100: #dbeafe;
--color-primary-200: #bfdbfe;
--color-primary-300: #93c5fd;
--color-primary-400: #60a5fa;
--color-primary-500: #3b82f6;  /* Primary */
--color-primary-600: #2563eb;
--color-primary-700: #1d4ed8;
--color-primary-800: #1e40af;
--color-primary-900: #1e3a8a;
```

#### Semantic Colors
```css
/* Success - Profit/Up trends */
--color-success-500: #10b981;
--color-success-600: #059669;

/* Danger - Loss/Down trends */
--color-danger-500: #ef4444;
--color-danger-600: #dc2626;

/* Warning - Alert/Caution */
--color-warning-500: #f59e0b;
--color-warning-600: #d97706;

/* Info - Neutral information */
--color-info-500: #06b6d4;
--color-info-600: #0891b2;
```

#### Neutral Colors
```css
--color-gray-50: #f9fafb;
--color-gray-100: #f3f4f6;
--color-gray-200: #e5e7eb;
--color-gray-300: #d1d5db;
--color-gray-400: #9ca3af;
--color-gray-500: #6b7280;
--color-gray-600: #4b5563;
--color-gray-700: #374151;
--color-gray-800: #1f2937;
--color-gray-900: #111827;
```

### Typography

#### Font Families
```css
/* System font stack for UI text */
--font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
             'Helvetica Neue', Arial, sans-serif;

/* Monospace for numbers and code */
--font-mono: 'JetBrains Mono', 'Menlo', 'Monaco', 'Courier New', monospace;

/* Display font for headings */
--font-display: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
```

#### Type Scale
```css
/* Text sizes using Tailwind scale */
--text-xs: 0.75rem;     /* 12px - Captions */
--text-sm: 0.875rem;    /* 14px - Small text */
--text-base: 1rem;      /* 16px - Body text */
--text-lg: 1.125rem;    /* 18px - Emphasized */
--text-xl: 1.25rem;     /* 20px - Subheading */
--text-2xl: 1.5rem;     /* 24px - Heading */
--text-3xl: 1.875rem;   /* 30px - Large heading */
--text-4xl: 2.25rem;    /* 36px - Display */
```

#### Font Weights
```css
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Spacing System

Based on 4px units (8-point grid):

```css
--spacing-1: 0.25rem;   /* 4px */
--spacing-2: 0.5rem;    /* 8px */
--spacing-3: 0.75rem;   /* 12px */
--spacing-4: 1rem;      /* 16px */
--spacing-5: 1.25rem;   /* 20px */
--spacing-6: 1.5rem;    /* 24px */
--spacing-8: 2rem;      /* 32px */
--spacing-10: 2.5rem;   /* 40px */
--spacing-12: 3rem;     /* 48px */
--spacing-16: 4rem;     /* 64px */
--spacing-20: 5rem;     /* 80px */
```

### Component Variants

#### Button Component
```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';
  size: 'xs' | 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
}
```

**Variants:**
- **Primary**: Main action buttons (blue background)
- **Secondary**: Secondary actions (gray background)
- **Success**: Positive actions (green background)
- **Danger**: Destructive actions (red background)
- **Ghost**: Minimal actions (transparent background)

**Sizes:**
- **xs**: 24px height - icon buttons
- **sm**: 32px height - compact buttons
- **md**: 40px height - standard buttons
- **lg**: 48px height - large buttons

#### Input Component
```typescript
interface InputProps {
  type: 'text' | 'email' | 'password' | 'number';
  size: 'sm' | 'md' | 'lg';
  state: 'default' | 'error' | 'success';
  placeholder?: string;
  disabled?: boolean;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
}
```

**States:**
- **Default**: Normal input state
- **Error**: Validation error (red border)
- **Success**: Valid input (green border)

#### Alert Component
```typescript
interface AlertProps {
  type: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  message: string;
  dismissible?: boolean;
  icon?: React.ReactNode;
}
```

## Layout System

### Container
```css
.container {
  width: 100%;
  max-width: 1280px;  /* Large desktop */
  margin-left: auto;
  margin-right: auto;
  padding-left: 1rem;
  padding-right: 1rem;
}
```

### Grid System
Based on CSS Grid with 12 columns:

```css
.grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 1rem;
}

.col-span-1 { grid-column: span 1; }
.col-span-2 { grid-column: span 2; }
.col-span-3 { grid-column: span 3; }
.col-span-4 { grid-column: span 4; }
.col-span-6 { grid-column: span 6; }
.col-span-8 { grid-column: span 8; }
.col-span-12 { grid-column: span 12; }
```

### Breakpoints

```css
/* Mobile First Approach */
--screen-sm: 640px;    /* Small tablets */
--screen-md: 768px;    /* Tablets */
--screen-lg: 1024px;   /* Laptops */
--screen-xl: 1280px;   /* Desktops */
--screen-2xl: 1536px;  /* Large screens */
```

## Component Library

### Base Components (src/components/ui/)

#### Button
```typescript
import { Button } from '@/components/ui/Button';

<Button variant="primary" size="md" loading={isLoading}>
  Save Changes
</Button>
```

#### Input
```typescript
import { Input } from '@/components/ui/Input';

<Input
  type="email"
  placeholder="user@example.com"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  state={error ? 'error' : 'default'}
  message={error}
/>
```

#### Select
```typescript
import { Select } from '@/components/ui/Select';

<Select
  options={options}
  value={selected}
  onChange={setSelected}
  placeholder="Select option"
/>
```

#### Modal
```typescript
import { Modal } from '@/components/ui/Modal';

<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Modal Title"
>
  <Modal.Body>Modal content</Modal.Body>
  <Modal.Footer>
    <Button onClick={() => setIsOpen(false)}>Close</Button>
  </Modal.Footer>
</Modal>
```

### Layout Components

#### Header
```typescript
import { Header } from '@/components/Layout/Header';

<Header
  user={currentUser}
  onLogout={handleLogout}
  notifications={notifications}
/>
```

#### Sidebar
```typescript
import { Sidebar } from '@/components/Layout/Sidebar';

<Sidebar
  collapsed={collapsed}
  onToggle={setCollapsed}
  navigation={navItems}
/>
```

### Chart Components

#### Line Chart
```typescript
import { LineChart } from '@/components/Charts/LineChart';

<LineChart
  data={priceData}
  xKey="timestamp"
  yKey="price"
  title="Price History"
  color="primary"
/>
```

#### Performance Chart
```typescript
import { PerformanceChart } from '@/components/Charts/PerformanceChart';

<PerformanceChart
  data={performanceData}
  benchmarks={benchmarks}
  showTooltip
/>
```

## State Management

### Redux Store Structure

```typescript
// Root state interface
interface RootState {
  auth: AuthState;           // User authentication
  strategies: StrategiesState;  // Strategy management
  strategy: StrategyState;   // Single strategy details
  dashboard: DashboardState;  // Dashboard data
  [apiSlice.reducerPath]: ApiState;  // RTK Query cache
}
```

### Auth Slice
```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
```

### Strategies Slice
```typescript
interface StrategiesState {
  items: Strategy[];
  selectedId: number | null;
  filters: StrategyFilters;
  pagination: PaginationState;
  isLoading: boolean;
  error: string | null;
}
```

### RTK Query API

```typescript
// API service definition
const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/v1',
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.token;
      if (token) headers.set('authorization', `Bearer ${token}`);
      return headers;
    },
  }),
  tagTypes: ['Strategy', 'User', 'Trade', 'Portfolio'],
  endpoints: (builder) => ({
    // Define endpoints here
  }),
});
```

## Routing

### Route Configuration

```typescript
const routes = [
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'strategies', element: <StrategyList /> },
      { path: 'strategies/:id', element: <StrategyDetail /> },
      { path: 'backtest', element: <Backtest /> },
      { path: 'portfolio', element: <Portfolio /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/register',
    element: <Register />,
  },
];
```

### Code Splitting

```typescript
// Lazy load page components
const StrategyDetail = lazy(() => import('@/pages/StrategyDetail'));
const Backtest = lazy(() => import('@/pages/Backtest'));

// Wrap with Suspense
<Suspense fallback={<Loading />}>
  <StrategyDetail />
</Suspense>
```

## Accessibility

### ARIA Labels
```typescript
<button
  aria-label="Close dialog"
  aria-pressed={isPressed}
  onClick={handleClose}
>
  <XIcon />
</button>
```

### Keyboard Navigation
```typescript
const handleKeyDown = (e: KeyboardEvent) => {
  switch (e.key) {
    case 'Escape':
      closeModal();
      break;
    case 'Enter':
      handleSubmit();
      break;
  }
};
```

### Focus Management
```typescript
import { useRef, useEffect } from 'react';

const modalRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (isOpen) {
    modalRef.current?.focus();
  }
}, [isOpen]);
```

## Performance Optimization

### Code Splitting
- Page-level code splitting with React.lazy()
- Vendor chunk splitting in Vite config
- Dynamic imports for heavy components

### Memoization
```typescript
// Use React.memo for expensive components
const ExpensiveComponent = React.memo(({ data }) => {
  // Component logic
});

// Use useMemo for expensive calculations
const processedData = useMemo(() => {
  return heavyComputation(rawData);
}, [rawData]);

// Use useCallback for event handlers
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);
```

### Virtual Scrolling
```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={items.length}
  itemSize={50}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>{items[index].name}</div>
  )}
</FixedSizeList>
```

## Testing

### Unit Tests
```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

test('renders button with text', () => {
  render(<Button>Click me</Button>);
  expect(screen.getByText('Click me')).toBeInTheDocument();
});

test('calls onClick when clicked', async () => {
  const handleClick = jest.fn();
  const user = userEvent.setup();

  render(<Button onClick={handleClick}>Click me</Button>);
  await user.click(screen.getByText('Click me'));

  expect(handleClick).toHaveBeenCalledTimes(1);
});
```

### Integration Tests
```typescript
import { renderWithProviders } from '@/tests/utils';
import { StrategyList } from './StrategyList';

test('displays strategy list', async () => {
  const { store } = renderWithProviders(<StrategyList />);
  // Test component behavior with Redux store
});
```

## Best Practices

### Component Design
1. **Keep components small** - Single responsibility
2. **Use TypeScript interfaces** - Type safety for props
3. **Default props** - Provide sensible defaults
4. **Prop drilling** - Use context or Redux for deep props
5. **Conditional rendering** - Use early returns

### Code Style
1. **Functional components** - Use hooks, not class components
2. **Arrow functions** - Concise syntax for callbacks
3. **Destructuring** - Extract props and state
4. **Template literals** - String interpolation
5. **Async/await** - Handle promises cleanly

### Performance
1. **Avoid inline functions** - Use useCallback
2. **Memo expensive operations** - Use useMemo
3. **Lazy load routes** - Code splitting
4. **Optimize images** - Use WebP format
5. **Bundle size** - Monitor with vite-plugin-visualizer

---
*Document Version: 1.0*
*Created: 2025-12-25*
*Author: CBSC System Unification Team*
