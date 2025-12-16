'use client';

import { useEffect } from 'react';
import { SquareCard, SquareButton } from '@/components/ui';
import { AlertCircle, HomeIcon } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <SquareCard className="max-w-md w-full">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
            <AlertCircle className="h-6 w-6 text-red-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            系統錯誤
          </h1>
          <p className="text-gray-600 mb-6">
            抱歉，系統遇到了一個錯誤。請稍後再試或聯繫技術支持。
          </p>

          {process.env.NODE_ENV === 'development' && (
            <div className="text-left bg-gray-50 p-4 rounded-md mb-6">
              <p className="text-sm font-medium text-gray-900 mb-2">錯誤詳情：</p>
              <p className="text-xs text-gray-600 font-mono break-all">
                {error.message}
              </p>
              {error.digest && (
                <p className="text-xs text-gray-500 mt-2">
                  錯誤ID: {error.digest}
                </p>
              )}
            </div>
          )}

          <div className="space-y-3">
            <SquareButton
              variant="primary"
              onClick={reset}
              className="w-full"
            >
              重試
            </SquareButton>
            <SquareButton
              variant="outline"
              icon={<HomeIcon size={16} />}
              iconPosition="left"
              onClick={() => window.location.href = '/'}
              className="w-full"
            >
              返回首頁
            </SquareButton>
          </div>

          <p className="text-xs text-gray-500 mt-6">
            如果問題持續存在，請發送郵件至 support@cbsc.com
          </p>
        </div>
      </SquareCard>
    </div>
  );
}