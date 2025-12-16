import Link from 'next/link';
import { SquareCard, SquareButton } from '@/components/ui';
import { HomeIcon, SearchIcon } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <SquareCard className="max-w-md w-full">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 mb-4">
            <SearchIcon className="h-6 w-6 text-blue-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">404</h1>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            頁面未找到
          </h2>
          <p className="text-gray-600 mb-6">
            抱歉，您訪問的頁面不存在或已被移除。
          </p>

          <div className="space-y-3">
            <Link href="/dashboard">
              <SquareButton
                variant="primary"
                icon={<HomeIcon size={16} />}
                iconPosition="left"
                className="w-full"
              >
                返回儀表板
              </SquareButton>
            </Link>
            <Link href="/">
              <SquareButton variant="outline" className="w-full">
                返回首頁
              </SquareButton>
            </Link>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              您可能在尋找：
            </p>
            <ul className="mt-2 text-sm text-blue-600 space-y-1">
              <li>
                <Link href="/dashboard/strategies" className="hover:underline">
                  策略管理
                </Link>
              </li>
              <li>
                <Link href="/dashboard/analytics" className="hover:underline">
                  數據分析
                </Link>
              </li>
              <li>
                <Link href="/dashboard/settings" className="hover:underline">
                  系統設置
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </SquareCard>
    </div>
  );
}