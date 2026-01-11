import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // 返回模擬回測結果
    return NextResponse.json({
      success: true,
      result_id: `bt_${Date.now()}`,
      message: '回測已啟動（演示模式）',
      input: body,
      estimated_completion: '2024-01-01T12:00:00Z'
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: 'Invalid request body'
      },
      { status: 400 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    message: 'Backtest API endpoint',
    usage: 'POST /api/backtest with body: {strategy_id, start_date, end_date}'
  });
}