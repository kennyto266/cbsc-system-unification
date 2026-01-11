import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const searchParams = request.nextUrl.searchParams;
    const format = searchParams.get('format') || 'pdf';

    // 演示模式：返回一個簡單的 PDF 內容或 JSON
    if (format === 'pdf') {
      // 在實際應用中，這裡會生成或獲取真實的 PDF
      const pdfContent = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Strategy Report ${id}) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000054 00000 n
0000000123 00000 n
0000000309 00000 n
0000000398 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
483
%%EOF`;

      const headers = new Headers();
      headers.set('Content-Type', 'application/pdf');
      headers.set(
        'Content-Disposition',
        `attachment; filename="strategy_report_${id}_${new Date()
          .toISOString()
          .split('T')[0]}.pdf"`
      );

      return new NextResponse(pdfContent, {
        status: 200,
        headers,
      });
    } else {
      // 返回 JSON 格式的報告
      return NextResponse.json({
        strategy_id: id,
        report: {
          total_return: '+15.2%',
          sharpe_ratio: 1.45,
          max_drawdown: '-8.3%',
          win_rate: '68%',
          generated_at: new Date().toISOString()
        },
        message: 'Demo report data'
      });
    }
  } catch (error) {
    console.error('Export API error:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        message: '無法生成報告'
      },
      { status: 500 }
    );
  }
}