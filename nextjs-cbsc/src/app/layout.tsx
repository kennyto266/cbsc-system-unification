import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import '@/styles/globals.css';
import { Providers } from '@/providers/Providers';
import { AuthProvider } from '@/providers/AuthProvider';
import { ThemeProvider } from '@/providers/ThemeProvider';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: {
    default: 'CBSC Strategy Management',
    template: '%s | CBSC Strategy Management',
  },
  description: 'Advanced quantitative trading strategy management platform',
  keywords: ['trading', 'strategy', 'quantitative', 'backtesting', 'portfolio'],
  authors: [{ name: 'CBSC Team' }],
  creator: 'CBSC',
  publisher: 'CBSC',
  robots: {
    index: false,
    follow: false,
    nocache: true,
    googleBot: {
      index: false,
      follow: false,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: process.env.NEXTAUTH_URL,
    title: 'CBSC Strategy Management',
    description: 'Advanced quantitative trading strategy management platform',
    siteName: 'CBSC Strategy Management',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'CBSC Strategy Management',
    description: 'Advanced quantitative trading strategy management platform',
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
  manifest: '/manifest.json',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>
          <AuthProvider>
            <ThemeProvider
              attribute="class"
              defaultTheme="system"
              enableSystem
              disableTransitionOnChange
            >
              {children}
              <ToastContainer
                position="top-right"
                autoClose={5000}
                hideProgressBar={false}
                newestOnTop={false}
                closeOnClick
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
                theme="colored"
              />
            </ThemeProvider>
          </AuthProvider>
        </Providers>
      </body>
    </html>
  );
}