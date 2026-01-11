'use client';

import React, { useState } from 'react';
import {
  SquareButton,
  SquareCard,
  SquareBadge,
  SquareInput,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui';
import { Search, Plus, Download, Upload, Settings, User, Mail, Lock } from 'lucide-react';

export default function ShowcasePage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Square UI 組件展示</h1>
          <p className="text-xl text-gray-600">基於 Square 設計語言的現代化 React 組件庫</p>
        </div>

        {/* 按鈕展示 */}
        <SquareCard className="mb-8">
          <CardHeader>
            <CardTitle>按鈕組件</CardTitle>
            <CardDescription>不同變體和尺寸的 Square 風格按鈕</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">變體</h3>
                <div className="flex flex-wrap gap-3">
                  <SquareButton variant="primary">Primary</SquareButton>
                  <SquareButton variant="secondary">Secondary</SquareButton>
                  <SquareButton variant="outline">Outline</SquareButton>
                  <SquareButton variant="ghost">Ghost</SquareButton>
                  <SquareButton variant="destructive">Destructive</SquareButton>
                  <SquareButton variant="link">Link</SquareButton>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">帶圖標</h3>
                <div className="flex flex-wrap gap-3">
                  <SquareButton icon={<Search size={16} />} iconPosition="left">
                    搜索
                  </SquareButton>
                  <SquareButton icon={<Plus size={16} />} iconPosition="right">
                    新增
                  </SquareButton>
                  <SquareButton icon={<Download size={16} />} variant="outline">
                    下載
                  </SquareButton>
                  <SquareButton icon={<Upload size={16} />} variant="secondary">
                    上傳
                  </SquareButton>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">尺寸</h3>
                <div className="flex items-center gap-3">
                  <SquareButton size="sm">Small</SquareButton>
                  <SquareButton size="md">Medium</SquareButton>
                  <SquareButton size="lg">Large</SquareButton>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">加載狀態</h3>
                <div className="flex gap-3">
                  <SquareButton loading>載入中...</SquareButton>
                  <SquareButton variant="outline" loading>
                    處理中...
                  </SquareButton>
                </div>
              </div>
            </div>
          </CardContent>
        </SquareCard>

        {/* Badge 展示 */}
        <SquareCard className="mb-8">
          <CardHeader>
            <CardTitle>標籤組件</CardTitle>
            <CardDescription>不同狀態和顏色的標籤組件</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">預設變體</h3>
                <div className="flex flex-wrap gap-2">
                  <SquareBadge variant="default">Default</SquareBadge>
                  <SquareBadge variant="primary">Primary</SquareBadge>
                  <SquareBadge variant="success">Success</SquareBadge>
                  <SquareBadge variant="warning">Warning</SquareBadge>
                  <SquareBadge variant="error">Error</SquareBadge>
                  <SquareBadge variant="info">Info</SquareBadge>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">動態狀態</h3>
                <div className="flex flex-wrap gap-2">
                  <SquareBadge status="active">Active</SquareBadge>
                  <SquareBadge status="completed">Completed</SquareBadge>
                  <SquareBadge status="pending">Pending</SquareBadge>
                  <SquareBadge status="error">Error</SquareBadge>
                  <SquareBadge status="warning">Warning</SquareBadge>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">尺寸</h3>
                <div className="flex items-center gap-2">
                  <SquareBadge size="sm">Small</SquareBadge>
                  <SquareBadge size="md">Medium</SquareBadge>
                  <SquareBadge size="lg">Large</SquareBadge>
                </div>
              </div>
            </div>
          </CardContent>
        </SquareCard>

        {/* 輸入框展示 */}
        <SquareCard className="mb-8">
          <CardHeader>
            <CardTitle>輸入框組件</CardTitle>
            <CardDescription>帶標籤、圖標和驗證的輸入框</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <SquareInput
                label="電子郵件"
                type="email"
                placeholder="example@square.com"
                leftIcon={<Mail size={16} />}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                helper="我們不會分享您的電子郵件"
              />
              <SquareInput
                label="密碼"
                type="password"
                placeholder="••••••••"
                leftIcon={<Lock size={16} />}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <SquareInput
                label="搜索用戶"
                type="text"
                placeholder="輸入用戶名..."
                leftIcon={<Search size={16} />}
                rightIcon={<Settings size={16} />}
              />
              <SquareInput
                label="有錯誤的輸入"
                type="text"
                placeholder="必填字段"
                error="此字段為必填項"
                required
              />
            </div>
          </CardContent>
        </SquareCard>

        {/* 卡片展示 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <SquareCard variant="default">
            <div className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-blue-600" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">用戶管理</h3>
                <p className="text-sm text-gray-500">管理系統用戶和權限</p>
              </div>
            </div>
            <div className="mt-4">
              <SquareButton size="sm" className="w-full">
                查看詳情
              </SquareButton>
            </div>
          </SquareCard>

          <SquareCard variant="elevated">
            <div className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Plus className="w-6 h-6 text-green-600" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">創建策略</h3>
                <p className="text-sm text-gray-500">設計新的交易策略</p>
              </div>
            </div>
            <div className="mt-4">
              <SquareButton variant="primary" size="sm" className="w-full">
                開始創建
              </SquareButton>
            </div>
          </SquareCard>

          <SquareCard variant="outlined">
            <div className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                  <Settings className="w-6 h-6 text-yellow-600" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">系統設置</h3>
                <p className="text-sm text-gray-500">配置系統參數</p>
              </div>
            </div>
            <div className="mt-4">
              <SquareButton variant="outline" size="sm" className="w-full">
                進入設置
              </SquareButton>
            </div>
          </SquareCard>
        </div>
      </div>
    </div>
  );
}