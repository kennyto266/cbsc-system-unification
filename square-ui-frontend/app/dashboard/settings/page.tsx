'use client';

import { SquareCard, SquareButton } from '@/components/ui';
import { UserIcon, BellIcon, ShieldIcon, PaletteIcon, GlobeIcon } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">系統設置</h1>
        <p className="mt-2 text-gray-600">管理您的帳戶和系統偏好設置</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Settings Menu */}
        <div className="lg:col-span-1">
          <SquareCard>
            <nav className="space-y-1 p-2">
              <a
                href="#"
                className="group flex items-center px-3 py-2 text-sm font-medium rounded-md text-blue-600 bg-blue-50"
              >
                <UserIcon className="mr-3 h-5 w-5 text-blue-500" />
                個人資料
              </a>
              <a
                href="#"
                className="group flex items-center px-3 py-2 text-sm font-medium rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-50"
              >
                <BellIcon className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                通知設置
              </a>
              <a
                href="#"
                className="group flex items-center px-3 py-2 text-sm font-medium rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-50"
              >
                <ShieldIcon className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                安全設置
              </a>
              <a
                href="#"
                className="group flex items-center px-3 py-2 text-sm font-medium rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-50"
              >
                <PaletteIcon className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                外觀設置
              </a>
              <a
                href="#"
                className="group flex items-center px-3 py-2 text-sm font-medium rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-50"
              >
                <GlobeIcon className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                語言設置
              </a>
            </nav>
          </SquareCard>
        </div>

        {/* Settings Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Profile Settings */}
          <SquareCard>
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">個人資料</h3>
            </div>
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    名字
                  </label>
                  <input
                    type="text"
                    className="block w-full border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                    defaultValue="CBSC"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    姓氏
                  </label>
                  <input
                    type="text"
                    className="block w-full border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                    defaultValue="用戶"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  電子郵件
                </label>
                <input
                  type="email"
                  className="block w-full border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                  defaultValue="user@cbsc.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  頭像
                </label>
                <div className="flex items-center space-x-4">
                  <div className="w-20 h-20 bg-gray-300 rounded-full flex items-center justify-center">
                    <UserIcon className="h-8 w-8 text-gray-500" />
                  </div>
                  <div>
                    <SquareButton variant="outline" size="sm">
                      更換頭像
                    </SquareButton>
                    <p className="text-xs text-gray-500 mt-1">
                      JPG, PNG 或 GIF. 最大 2MB.
                    </p>
                  </div>
                </div>
              </div>
              <div className="pt-4">
                <SquareButton variant="primary">
                  保存更改
                </SquareButton>
              </div>
            </div>
          </SquareCard>

          {/* Notification Settings */}
          <SquareCard>
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">通知設置</h3>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">郵件通知</h4>
                  <p className="text-sm text-gray-500">接收策略執行和警報郵件</p>
                </div>
                <button
                  type="button"
                  className="relative inline-flex h-6 w-11 items-center rounded-full bg-blue-600"
                >
                  <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition"></span>
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">推送通知</h4>
                  <p className="text-sm text-gray-500">瀏覽器推送通知</p>
                </div>
                <button
                  type="button"
                  className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200"
                >
                  <span className="translate-x-1 inline-block h-4 w-4 transform rounded-full bg-white transition"></span>
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">每日報告</h4>
                  <p className="text-sm text-gray-500">每日策略表現摘要</p>
                </div>
                <button
                  type="button"
                  className="relative inline-flex h-6 w-11 items-center rounded-full bg-blue-600"
                >
                  <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition"></span>
                </button>
              </div>
            </div>
          </SquareCard>

          {/* Security Settings */}
          <SquareCard>
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">安全設置</h3>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between py-4 border-b border-gray-200">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">修改密碼</h4>
                  <p className="text-sm text-gray-500">上次修改：30天前</p>
                </div>
                <SquareButton variant="outline" size="sm">
                  修改密碼
                </SquareButton>
              </div>
              <div className="flex items-center justify-between py-4 border-b border-gray-200">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">雙因素認證</h4>
                  <p className="text-sm text-gray-500">額外的安全保護層</p>
                </div>
                <SquareButton variant="outline" size="sm">
                  啟用
                </SquareButton>
              </div>
              <div className="flex items-center justify-between py-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">登錄會話</h4>
                  <p className="text-sm text-gray-500">當前 1 個活躍會話</p>
                </div>
                <SquareButton variant="outline" size="sm">
                  管理
                </SquareButton>
              </div>
            </div>
          </SquareCard>
        </div>
      </div>
    </div>
  );
}