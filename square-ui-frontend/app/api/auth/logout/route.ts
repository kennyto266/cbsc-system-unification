import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function POST(request: NextRequest) {
  try {
    // Create response and clear authentication cookie
    const response = NextResponse.json({
      success: true,
      message: 'Logout successful',
    });

    response.cookies.delete('auth_token');

    return response;
  } catch (error) {
    console.error('Logout error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}