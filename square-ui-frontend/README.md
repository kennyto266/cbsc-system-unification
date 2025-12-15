# Square UI Frontend

A modern, responsive dashboard interface built with React 18, TypeScript, and Tailwind CSS.

## Features

- 🎨 **Modern UI Design** - Clean, professional interface with Tailwind CSS
- 📱 **Fully Responsive** - Works seamlessly on desktop, tablet, and mobile
- ♿ **Accessibility First** - WCAG compliant with ARIA labels and keyboard navigation
- 🌙 **Dark Mode Support** - Built-in dark/light theme toggle
- 🔐 **Secure by Default** - Implements security best practices
- ⚡ **Performance Optimized** - Code splitting and lazy loading
- 🎯 **TypeScript** - Full type safety and IntelliSense support

## Architecture

### Components Structure

```
src/
├── components/
│   └── Layout/
│       ├── Header.tsx      # Top navigation bar with search and user menu
│       ├── Sidebar.tsx     # Collapsible navigation with nested items
│       ├── Footer.tsx      # Simple footer component
│       ├── Breadcrumb.tsx  # Navigation breadcrumbs
│       └── index.tsx       # Main layout wrapper with context
├── navigation/
│   ├── routes.tsx          # Route definitions with lazy loading
│   └── NavigationProvider.tsx # Router context provider
├── pages/
│   ├── Dashboard.tsx       # Main dashboard with stats and charts
│   ├── UserList.tsx        # User management table
│   ├── UserRoles.tsx       # Role and permissions management
│   ├── ReportsAnalytics.tsx # Analytics and reports
│   ├── ReportsActivity.tsx # Activity logs timeline
│   ├── Calendar.tsx        # Calendar view with events
│   ├── Settings.tsx        # Application settings
│   └── NotFound.tsx        # 404 error page
├── hooks/
├── types/
├── utils/
└── styles/
```

### Key Features Implemented

1. **Responsive Header**
   - Sidebar toggle button
   - Search bar (hidden on mobile)
   - Theme switcher (Light/Dark/System)
   - Notifications with badge
   - User dropdown menu

2. **Collapsible Sidebar**
   - Multi-level navigation items
   - Active item highlighting
   - Badge notifications
   - Smooth collapse/expand animations
   - User profile section
   - Auto-collapse on mobile

3. **Breadcrumb Navigation**
   - Dynamic breadcrumbs based on route
   - Home icon as first item
   - Clickable breadcrumb links
   - Current page highlighting

4. **Main Content Area**
   - Flexible layout for different page types
   - Responsive grid system
   - Consistent spacing and typography
   - Loading states for lazy-loaded pages

5. **Responsive Design**
   - Mobile-first approach
   - Tablet optimizations
   - Desktop experience
   - Touch-friendly interactions

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Clone the repository
2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Build for Production

```bash
npm run build
```

### Linting

```bash
npm run lint
```

## Accessibility Features

- Full keyboard navigation support
- ARIA labels and landmarks
- Focus management
- Screen reader friendly
- High contrast ratios
- Semantic HTML structure

## Keyboard Shortcuts

- `Tab` - Navigate through interactive elements
- `Enter/Space` - Activate buttons and links
- `Escape` - Close modals and dropdowns
- `Alt + M` - Toggle mobile menu
- `Alt + S` - Focus search input

## Theme Customization

The theme can be customized by modifying the `tailwind.config.js` file:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Custom primary colors
      },
      dark: {
        // Custom dark mode colors
      }
    }
  }
}
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- iOS Safari 14+
- Android Chrome 90+

## Contributing

1. Follow the existing code style
2. Write TypeScript for all new code
3. Ensure all components are accessible
4. Test on multiple devices
5. Keep performance in mind

## License

MIT License - see LICENSE file for details.