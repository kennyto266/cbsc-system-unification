/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 基于HSL的语义化颜色系统
        primary: {
          50: 'hsl(211, 98%, 97%)',
          100: 'hsl(211, 91%, 93%)',
          200: 'hsl(211, 84%, 85%)',
          300: 'hsl(211, 78%, 73%)',
          400: 'hsl(211, 71%, 59%)',
          500: 'hsl(211, 98%, 52%)',
          600: 'hsl(211, 100%, 43%)',
          700: 'hsl(211, 100%, 35%)',
          800: 'hsl(211, 100%, 28%)',
          900: 'hsl(211, 100%, 20%)',
          950: 'hsl(211, 100%, 11%)',
        },
        success: {
          50: 'hsl(142, 76%, 96%)',
          100: 'hsl(142, 70%, 89%)',
          200: 'hsl(142, 65%, 78%)',
          300: 'hsl(142, 58%, 65%)',
          400: 'hsl(142, 49%, 51%)',
          500: 'hsl(142, 71%, 45%)',
          600: 'hsl(142, 76%, 36%)',
          700: 'hsl(142, 70%, 28%)',
          800: 'hsl(142, 68%, 21%)',
          900: 'hsl(142, 60%, 15%)',
          950: 'hsl(142, 71%, 8%)',
        },
        warning: {
          50: 'hsl(48, 100%, 96%)',
          100: 'hsl(48, 100%, 90%)',
          200: 'hsl(48, 100%, 81%)',
          300: 'hsl(48, 100%, 71%)',
          400: 'hsl(48, 100%, 60%)',
          500: 'hsl(38, 92%, 50%)',
          600: 'hsl(32, 95%, 44%)',
          700: 'hsl(26, 94%, 36%)',
          800: 'hsl(22, 84%, 28%)',
          900: 'hsl(18, 80%, 22%)',
          950: 'hsl(12, 83%, 15%)',
        },
        error: {
          50: 'hsl(0, 100%, 97%)',
          100: 'hsl(0, 100%, 94%)',
          200: 'hsl(0, 100%, 88%)',
          300: 'hsl(0, 100%, 80%)',
          400: 'hsl(0, 100%, 71%)',
          500: 'hsl(0, 84%, 60%)',
          600: 'hsl(0, 72%, 51%)',
          700: 'hsl(0, 63%, 41%)',
          800: 'hsl(0, 61%, 32%)',
          900: 'hsl(0, 63%, 25%)',
          950: 'hsl(0, 70%, 15%)',
        },
        // CBSC品牌色
        cbsc: {
          blue: 'hsl(211, 98%, 52%)',
          green: 'hsl(142, 71%, 45%)',
          orange: 'hsl(26, 94%, 36%)',
          red: 'hsl(0, 84%, 60%)',
          purple: 'hsl(263, 70%, 50%)',
          cyan: 'hsl(188, 94%, 43%)',
        },
        // Square-UI品牌色
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
        // Square-UI渐变定义
        gradient: {
          primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          success: 'linear-gradient(135deg, #13B497 0%, #59D4A4 100%)',
          warning: 'linear-gradient(135deg, #F7B500 0%, #F5A623 100%)',
          error: 'linear-gradient(135deg, #FF5252 0%, #FF3838 100%)',
        },
        // 中性色系统
        gray: {
          50: 'hsl(210, 40%, 98%)',
          100: 'hsl(210, 40%, 96%)',
          200: 'hsl(210, 40%, 93%)',
          300: 'hsl(210, 40%, 88%)',
          400: 'hsl(210, 40%, 81%)',
          500: 'hsl(210, 40%, 73%)',
          600: 'hsl(210, 40%, 62%)',
          700: 'hsl(210, 40%, 46%)',
          800: 'hsl(210, 40%, 33%)',
          900: 'hsl(210, 40%, 21%)',
          950: 'hsl(210, 40%, 11%)',
        },
        // shadcn/ui colors
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
      },
      // 基于系统字体栈的字体系统
      fontFamily: {
        sans: [
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          '"Noto Sans"',
          'sans-serif',
          '"Apple Color Emoji"',
          '"Segoe UI Emoji"',
          '"Segoe UI Symbol"',
          '"Noto Color Emoji"'
        ],
        serif: [
          'ui-serif',
          'Georgia',
          'Cambria',
          '"Times New Roman"',
          'Times',
          'serif'
        ],
        mono: [
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Monaco',
          'Consolas',
          '"Liberation Mono"',
          '"Courier New"',
          'monospace'
        ],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        // Square-UI animations
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        // Square-UI keyframes
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      // 基于4px的8点网格系统
      spacing: {
        '0.5': '0.125rem',  // 2px
        '1.5': '0.375rem',  // 6px
        '2.5': '0.625rem',  // 10px
        '3.5': '0.875rem',  // 14px
        '4.5': '1.125rem',  // 18px
        '5.5': '1.375rem',  // 22px
        '6.5': '1.625rem',  // 26px
        '7.5': '1.875rem',  // 30px
        '8.5': '2.125rem',  // 34px
        '9.5': '2.375rem',  // 38px
        '10.5': '2.625rem', // 42px
        '11.5': '2.875rem', // 46px
        '12.5': '3.125rem', // 50px
        '13.5': '3.375rem', // 54px
        '14.5': '3.625rem', // 58px
        '15.5': '3.875rem', // 62px
        '16.5': '4.125rem', // 66px
        '17.5': '4.375rem', // 70px
        '18.5': '4.625rem', // 74px
        '19.5': '4.875rem', // 78px
        '20.5': '5.125rem', // 82px
        '21.5': '5.375rem', // 86px
        '22.5': '5.625rem', // 90px
        '23.5': '5.875rem', // 94px
        '24.5': '6.125rem', // 98px
        '88': '22rem',
        '128': '32rem',
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
        // Square-UI border radius
        'square': '12px',
        'square-lg': '16px',
        'square-sm': '8px',
      },
      boxShadow: {
        'cbsc': '0 10px 40px rgba(24, 144, 255, 0.15)',
        'cbsc-lg': '0 20px 60px rgba(24, 144, 255, 0.2)',
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'card-lg': '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'modal': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        // Square-UI shadows
        'square': '0 10px 30px rgba(0, 0, 0, 0.1)',
        'square-sm': '0 2px 10px rgba(0, 0, 0, 0.05)',
        'square-lg': '0 20px 40px rgba(0, 0, 0, 0.15)',
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
      },
      // backdrop blur
      backdropBlur: {
        square: '10px',
      },
      // 断点系统
      screens: {
        'xs': '475px',
        '3xl': '1600px',
      },
    },
  },
  plugins: [require('tailwindcss-animate'),
    // 添加组件变体插件
    require('tailwindcss/plugin')(({ addUtilities, theme }) => {
      addUtilities({
        '.text-gradient': {
          background: `linear-gradient(to right, ${theme('colors.primary.500')}, ${theme('colors.cbsc.cyan')})`,
          '-webkit-background-clip': 'text',
          '-webkit-text-fill-color': 'transparent',
          'background-clip': 'text',
        },
        '.glass': {
          'background': 'rgba(255, 255, 255, 0.8)',
          'backdrop-filter': 'blur(10px)',
          '-webkit-backdrop-filter': 'blur(10px)',
          'border': '1px solid rgba(255, 255, 255, 0.2)',
        },
        '.glass-dark': {
          'background': 'rgba(0, 0, 0, 0.8)',
          'backdrop-filter': 'blur(10px)',
          '-webkit-backdrop-filter': 'blur(10px)',
          'border': '1px solid rgba(255, 255, 255, 0.1)',
        },
        // Square-UI utilities
        '.square-gradient': {
          'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        },
        '.glass-effect': {
          'backdrop-filter': 'blur(10px)',
          'background': 'rgba(255, 255, 255, 0.1)',
          'border': '1px solid rgba(255, 255, 255, 0.2)',
        },
        '.dark .glass-effect': {
          'background': 'rgba(0, 0, 0, 0.2)',
          'border': '1px solid rgba(255, 255, 255, 0.1)',
        },
      })
    }),
    // 添加响应式容器插件
    function({ addComponents, theme }) {
      addComponents({
        '.container': {
          maxWidth: 'none',
          marginLeft: 'auto',
          marginRight: 'auto',
          paddingLeft: theme('spacing.6'),
          paddingRight: theme('spacing.6'),
          '@screen sm': {
            paddingLeft: theme('spacing.8'),
            paddingRight: theme('spacing.8'),
          },
          '@screen md': {
            paddingLeft: theme('spacing.12'),
            paddingRight: theme('spacing.12'),
          },
        },
      })
    },
  ],
}