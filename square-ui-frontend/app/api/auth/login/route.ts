import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();

    // TODO: Implement actual authentication logic
    // For now, accept any email/password combination
    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    // Mock authentication - In production, verify against database
    const mockUser = {
      id: '1',
      email: email,
      name: 'CBSC User',
      role: 'user',
    };

    // Mock JWT token - In production, use proper JWT signing
    const mockToken = Buffer.from(JSON.stringify(mockUser)).toString('base64');

    // Create response with authentication cookie
    const response = NextResponse.json({
      success: true,
      data: {
        user: mockUser,
        token: mockToken,
      },
      message: 'Login successful',
    });

    // Set authentication cookie
    response.cookies.set('auth_token', mockToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 7, // 7 days
      path: '/',
    });

    return response;
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}