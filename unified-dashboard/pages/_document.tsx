/**
 * Next.js Document Component
 * CBSC量化交易系統的HTML文檔結構
 */

import { Html, Head, Main, NextScript } from 'next/document'
import Script from 'next/script'

export default function Document() {
  return (
    <Html lang="zh-HK" className="dark">
      <Head>
        {/* Meta Tags */}
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="theme-color" content="#3b82f6" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="CBSC Dashboard" />
        <meta name="application-name" content="CBSC Dashboard" />
        <meta name="msapplication-TileColor" content="#3b82f6" />
        <meta name="msapplication-config" content="/browserconfig.xml" />

        {/* SEO Meta Tags */}
        <meta name="description" content="CBSC量化交易策略管理平台 - 專業的量化交易策略管理和分析系統" />
        <meta name="keywords" content="量化交易,策略管理,金融分析,CBSC,投資理財" />
        <meta name="author" content="CBSC Team" />
        <meta name="robots" content="index,follow" />

        {/* Open Graph Meta Tags */}
        <meta property="og:title" content="CBSC量化交易策略管理平台" />
        <meta property="og:description" content="專業的量化交易策略管理和分析系統" />
        <meta property="og:type" content="website" />
        <meta property="og:image" content="/og-image.png" />
        <meta property="og:url" content="https://cbsc.com" />
        <meta property="og:site_name" content="CBSC Dashboard" />
        <meta property="og:locale" content="zh_HK" />

        {/* Twitter Card Meta Tags */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="CBSC量化交易策略管理平台" />
        <meta name="twitter:description" content="專業的量化交易策略管理和分析系統" />
        <meta name="twitter:image" content="/twitter-image.png" />
        <meta name="twitter:creator" content="@cbsc" />

        {/* Favicon and Icons */}
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/manifest.json" />

        {/* Preconnect to External Services */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="preconnect" href="https://api.cbsc.com" />

        {/* Google Fonts */}
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&family=JetBrains+Mono:wght@100..800&display=swap"
          rel="stylesheet"
        />

        {/* Additional CSS */}
        <link
          rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
        />

        {/* Security Headers */}
        <meta httpEquiv="Content-Security-Policy" content="
          default-src 'self';
          script-src 'self' 'unsafe-eval' 'unsafe-inline' https://www.googletagmanager.com;
          style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com;
          font-src 'self' https://fonts.gstatic.com;
          img-src 'self' data: https: www.google-analytics.com;
          connect-src 'self' https://api.cbsc.com wss://api.cbsc.com;
          frame-src 'none';
          object-src 'none';
        " />

        {/* PWA Meta Tags */}
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="theme-color" content="#3b82f6" />
        <link rel="apple-touch-startup-image" href="/apple-startup.png" />

        {/* Structured Data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "WebApplication",
              "name": "CBSC Dashboard",
              "description": "CBSC量化交易策略管理平台",
              "url": "https://cbsc.com",
              "applicationCategory": "FinanceApplication",
              "operatingSystem": "Any",
              "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "HKD"
              }
            })
          }}
        />
      </Head>

      <body className="font-sans antialiased">
        {/* Main Content */}
        <Main />
        <NextScript />

        {/* Third-party Scripts */}
        <Script
          id="google-analytics"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
              new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
              j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
              'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
              })(window,document,'script','dataLayer','GTM-XXXXXX');
            `
          }}
        />

        {/* Service Worker Registration */}
        <Script
          id="service-worker"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js')
                    .then(function(registration) {
                      console.log('SW registered: ', registration);
                    })
                    .catch(function(registrationError) {
                      console.log('SW registration failed: ', registrationError);
                    });
                });
              }
            `
          }}
        />

        {/* Error Tracking */}
        <Script
          id="error-tracking"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              window.addEventListener('error', function(e) {
                console.error('Global error:', e.error);
                // Send error to tracking service
              });

              window.addEventListener('unhandledrejection', function(e) {
                console.error('Unhandled promise rejection:', e.reason);
                // Send rejection to tracking service
              });
            `
          }}
        />
      </body>
    </Html>
  )
}