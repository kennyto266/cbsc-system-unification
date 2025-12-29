import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { getToken } from 'next-auth/jwt'

// 不需要認證的路由
const publicRoutes = ['/login', '/register', '/api/auth']
// 需要認證的路由前綴
const protectedRoutes = ['/dashboard', '/api/strategies', '/api/analytics']

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // 獲取token
  const token = await getToken({
    req: request,
    secret: process.env.NEXTAUTH_SECRET,
  })

  // 檢查是否是API路由
  if (pathname.startsWith('/api/')) {
    // 跳過認證的API路由
    for (const route of publicRoutes) {
      if (pathname.startsWith(route)) {
        return NextResponse.next()
      }
    }

    // 保護API路由
    if (!token) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }
  }

  // 檢查保護的路由
  for (const route of protectedRoutes) {
    if (pathname.startsWith(route)) {
      if (!token) {
        // 重定向到登錄頁，保存當前URL
        const loginUrl = new URL('/login', request.url)
        loginUrl.searchParams.set('callbackUrl', pathname)
        return NextResponse.redirect(loginUrl)
      }

      // 檢查用戶是否活躍
      if (token.isActive === false) {
        const errorUrl = new URL('/login', request.url)
        errorUrl.searchParams.set('error', 'account_deactivated')
        return NextResponse.redirect(errorUrl)
      }
    }
  }

  // 已登錄用戶訪問登錄頁，重定向到dashboard
  if (token && (pathname === '/login' || pathname === '/register')) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  // 設置安全頭
  const response = NextResponse.next()
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  response.headers.set(
    'Strict-Transport-Security',
    'max-age=31536000; includeSubDomains'
  )

  // 設置CSP頭
  const cspHeader = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://cdn.jsdelivr.net https://www.googletagmanager.com",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: https:",
    "connect-src 'self' ws://localhost:3004 https://api.cbsc.com",
    "frame-src 'none'",
  ].join('; ')

  response.headers.set('Content-Security-Policy', cspHeader)

  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
}