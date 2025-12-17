// Square-UI to Unified Dashboard Adapter
// This script migrates design tokens and components from square-ui to unified-dashboard

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const SQUARE_UI_PATH = path.join(__dirname, '../square-ui');
const UNIFIED_DASHBOARD_PATH = path.join(__dirname, '../unified-dashboard');
const COMPONENTS_OUTPUT_PATH = path.join(UNIFIED_DASHBOARD_PATH, 'src/components/square');

console.log('🔄 Starting Square-UI adaptation process...\n');

// 1. Create output directory if it doesn't exist
if (!fs.existsSync(COMPONENTS_OUTPUT_PATH)) {
  fs.mkdirSync(COMPONENTS_OUTPUT_PATH, { recursive: true });
  console.log('✅ Created components/square directory');
}

// 2. Extract and adapt design tokens
function adaptDesignTokens() {
  console.log('\n📨 Adapting design tokens...');

  const tailwindConfigPath = path.join(SQUARE_UI_PATH, 'tailwind.config.js');
  const unifiedTailwindPath = path.join(UNIFIED_DASHBOARD_PATH, 'tailwind.config.js');

  if (fs.existsSync(tailwindConfigPath)) {
    // Read square config as text and parse it
    const squareConfigText = fs.readFileSync(tailwindConfigPath, 'utf8');

    // Extract the module exports from square config
    const squareConfigMatch = squareConfigText.match(/module\.exports = ({[\s\S]*});/);
    if (!squareConfigMatch) {
      console.error('Could not parse square-ui tailwind config');
      return;
    }

    // Read unified config as text
    const unifiedConfigText = fs.readFileSync(unifiedTailwindPath, 'utf8');

    // Create a new config with square-ui extensions
    const newConfigText = unifiedConfigText.replace(
      /}(?=\s*,?\s*plugins)/,
      `,
      // Square-UI design tokens
      colors: {
        ...theme.extend.colors,
        // Square brand colors
        square: {
          50: '#f0f4ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#667eea',
          600: '#5a67d8',
          700: '#4c51bf',
          800: '#434190',
          900: '#3c366b',
          950: '#312e81',
        },
        // Gradient definitions
        gradient: {
          primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          success: 'linear-gradient(135deg, #13B497 0%, #59D4A4 100%)',
          warning: 'linear-gradient(135deg, #F7B500 0%, #F5A623 100%)',
          error: 'linear-gradient(135deg, #FF5252 0%, #FF3838 100%)',
        }
      },
      // Custom shadows
      boxShadow: {
        ...theme.extend.boxShadow,
        'square': '0 10px 30px rgba(0, 0, 0, 0.1)',
        'square-sm': '0 2px 10px rgba(0, 0, 0, 0.05)',
        'square-lg': '0 20px 40px rgba(0, 0, 0, 0.15)',
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
      },
      // Backdrop blur
      backdropBlur: {
        square: '10px',
      },
      // Animations
      animation: {
        ...theme.extend.animation,
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
      },
      // Keyframes
      keyframes: {
        ...theme.extend.keyframes,
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      // Additional spacing
      spacing: {
        ...theme.extend.spacing,
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      // Border radius
      borderRadius: {
        ...theme.extend.borderRadius,
        'square': '12px',
        'square-lg': '16px',
        'square-sm': '8px',
      },
      }`
    );

    fs.writeFileSync(unifiedTailwindPath, newConfigText);
    console.log('✅ Updated tailwind.config.js with Square-UI design tokens');
  }
}

// 3. Copy CSS variables for light/dark theme support
function copyCSSVariables() {
  console.log('\n🎨 Copying CSS variables...');

  const stylesPath = path.join(UNIFIED_DASHBOARD_PATH, 'src/styles');

  if (!fs.existsSync(stylesPath)) {
    fs.mkdirSync(stylesPath, { recursive: true });
  }

  const cssVariables = `/* Square-UI Design Tokens */
:root {
  /* Base colors */
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;
  --popover: 0 0% 100%;
  --popover-foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96.1%;
  --accent-foreground: 222.2 47.4% 11.2%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 221.2 83.2% 53.3%;
  --radius: 0.5rem;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --card: 222.2 84% 4.9%;
  --card-foreground: 210 40% 98%;
  --popover: 222.2 84% 4.9%;
  --popover-foreground: 210 40% 98%;
  --primary: 217.2 91.2% 59.8%;
  --primary-foreground: 222.2 47.4% 11.2%;
  --secondary: 217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;
  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;
  --accent: 217.2 32.6% 17.5%;
  --accent-foreground: 210 40% 98%;
  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;
  --border: 217.2 32.6% 17.5%;
  --input: 217.2 32.6% 17.5%;
  --ring: 224.3 76.3% 48%;
}

/* Square brand utilities */
.square-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.glass-effect {
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.dark .glass-effect {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
`;

  fs.writeFileSync(path.join(stylesPath, 'square-ui.css'), cssVariables);
  console.log('✅ Created square-ui.css with design tokens');
}

// 4. Create utility functions for component adaptation
function createUtils() {
  console.log('\n🛠️ Creating utility functions...');

  const utilsPath = path.join(COMPONENTS_OUTPUT_PATH, '../utils');
  if (!fs.existsSync(utilsPath)) {
    fs.mkdirSync(utilsPath, { recursive: true });
  }

  const utils = `// Square-UI Utility Functions
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Enhanced cn function with square-ui support
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Square color utilities
export const squareColors = {
  primary: {
    50: '#f0f4ff',
    100: '#e0e7ff',
    200: '#c7d2fe',
    300: '#a5b4fc',
    400: '#818cf8',
    500: '#667eea',
    600: '#5a67d8',
    700: '#4c51bf',
    800: '#434190',
    900: '#3c366b',
    950: '#312e81',
  },
  gradient: {
    primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    success: 'linear-gradient(135deg, #13B497 0%, #59D4A4 100%)',
    warning: 'linear-gradient(135deg, #F7B500 0%, #F5A623 100%)',
    error: 'linear-gradient(135deg, #FF5252 0%, #FF3838 100%)',
  }
};

// Theme utilities
export const getThemeClasses = (variant: 'primary' | 'secondary' | 'success' | 'warning' | 'error') => {
  const variants = {
    primary: 'bg-gradient-to-r from-square-500 to-purple-600 text-white shadow-square',
    secondary: 'bg-gradient-to-r from-purple-100 to-pink-100 text-purple-900',
    success: 'bg-gradient-to-r from-green-400 to-emerald-500 text-white',
    warning: 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white',
    error: 'bg-gradient-to-r from-red-500 to-pink-500 text-white',
  };
  return variants[variant] || variants.primary;
};

// Animation utilities
export const animations = {
  fadeIn: 'animate-fade-in',
  slideUp: 'animate-slide-up',
  slideDown: 'animate-slide-down',
  scaleIn: 'animate-scale-in',
  float: 'animate-float',
  pulseSlow: 'animate-pulse-slow',
};
`;

  fs.writeFileSync(path.join(utilsPath, 'square-utils.ts'), utils);
  console.log('✅ Created square-utils.ts utility functions');
}

// 5. Create base component template
function createComponentTemplate() {
  console.log('\n🧩 Creating component templates...');

  const template = `// Square-UI Base Component Template
import React from 'react';
import { cn } from '../utils/square-utils';

export interface SquareComponentProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
}

export const SquareComponent: React.FC<SquareComponentProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  ...props
}) => {
  const baseClasses = cn(
    'inline-flex items-center justify-center rounded-square font-medium transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-square-500 focus:ring-offset-2',
    {
      'shadow-square hover:shadow-square-lg': !disabled,
      'opacity-50 cursor-not-allowed': disabled,
      'animate-pulse': loading,
    },
    className
  );

  const variantClasses = {
    primary: 'bg-gradient-to-r from-square-500 to-purple-600 text-white',
    secondary: 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-900',
    success: 'bg-gradient-to-r from-green-400 to-emerald-500 text-white',
    warning: 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white',
    error: 'bg-gradient-to-r from-red-500 to-pink-500 text-white',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size]
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg className=\"animate-spin -ml-1 mr-2 h-4 w-4\" fill=\"none\" viewBox=\"0 0 24 24\">
          <circle className=\"opacity-25\" cx=\"12\" cy=\"12\" r=\"10\" stroke=\"currentColor\" strokeWidth=\"4\" />
          <path className=\"opacity-75\" fill=\"currentColor\" d=\"M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z\" />
        </svg>
      )}
      {children}
    </button>
  );
};

export default SquareComponent;
`;

  fs.writeFileSync(path.join(COMPONENTS_OUTPUT_PATH, 'SquareComponent.tsx'), template);
  console.log('✅ Created SquareComponent.tsx template');
}

// 6. Create index file for exports
function createIndexFile() {
  console.log('\n📦 Creating index file...');

  const indexContent = `// Square-UI Components Export
export { default as SquareComponent, type SquareComponentProps } from './SquareComponent';
export { cn, squareColors, getThemeClasses, animations } from '../utils/square-utils';

// Additional components will be added here as they are adapted
// export { default as SquareButton } from './SquareButton';
// export { default as SquareCard } from './SquareCard';
// export { default as SquareInput } from './SquareInput';
`;

  fs.writeFileSync(path.join(COMPONENTS_OUTPUT_PATH, 'index.ts'), indexContent);
  console.log('✅ Created index.ts export file');
}

// Execute adaptation steps
try {
  adaptDesignTokens();
  copyCSSVariables();
  createUtils();
  createComponentTemplate();
  createIndexFile();

  console.log('\n✅ Square-UI adaptation completed successfully!');
  console.log('\n📋 Next steps:');
  console.log('1. Import the CSS variables in your main CSS file');
  console.log('2. Start using SquareComponent and utilities in unified-dashboard');
  console.log('3. Adapt more components from square-ui as needed');

} catch (error) {
  console.error('\n❌ Error during adaptation:', error);
  process.exit(1);
}