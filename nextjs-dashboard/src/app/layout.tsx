import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ToastProvider } from '@/components/ui/toast'
import { ThemeProvider } from '@/components/providers/theme-provider'
import { QueryProvider } from '@/components/providers/query-provider'
import { AuthProvider } from '@/components/providers/auth-provider'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'CBSC策略管理Dashboard',
    template: '%s | CBSC量化交易系統'
  },
  description: 'CBSC量化交易策略管理系統 - 專業的策略分析與監控平台',
  keywords: [
    '量化交易',
    '策略管理',
    'CBSC',
    '技術分析',
    '回測系統',
    '風險管理'
  ],
  authors: [{ name: 'CBSC Team' }],
  creator: 'CBSC Development Team',
  publisher: 'CBSC',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL('https://dashboard.cbsc.com'),
  alternates: {
    canonical: '/',
    languages: {
      'zh-CN': '/zh-CN',
      'en-US': '/en-US',
    },
  },
  openGraph: {
    type: 'website',
    locale: 'zh_CN',
    url: 'https://dashboard.cbsc.com',
    title: 'CBSC策略管理Dashboard',
    description: '專業的量化交易策略管理與監控平台',
    siteName: 'CBSC Dashboard',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'CBSC Dashboard',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'CBSC策略管理Dashboard',
    description: '專業的量化交易策略管理與監控平台',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: 'your-google-verification-code',
    yandex: 'your-yandex-verification-code',
    yahoo: 'your-yahoo-verification-code',
  },
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'white' },
    { media: '(prefers-color-scheme: dark)', color: 'black' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            <AuthProvider>
              <ToastProvider>
                {children}
              </ToastProvider>
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}