'use client';

import React from 'react';
import { SquareCard, SquareBadge } from '@/components/ui';
import { CheckCircle, AlertCircle, Database, TrendingUp } from 'lucide-react';

interface DataSource {
  name: string;
  status: 'real' | 'simulated' | 'fallback';
  description: string;
  lastUpdate?: string;
}

const dataSources: DataSource[] = [
  {
    name: '股票市場數據',
    status: 'real',
    description: '來自 Yahoo Finance API 的實時股票數據',
    lastUpdate: '實時更新'
  },
  {
    name: '北向資金流向',
    status: 'simulated',
    description: '基於 HKEX 數據結構的模擬數據（來自本地爬蟲文件）',
    lastUpdate: '每日 30 秒更新'
  },
  {
    name: 'HIBOR 利率',
    status: 'simulated',
    description: '基於香港金管局的模擬 HIBOR 利率',
    lastUpdate: '每 30 秒更新'
  },
  {
    name: '美元兌港元匯率',
    status: 'simulated',
    description: '基於聯繫匯率制度的模擬數據',
    lastUpdate: '每 30 秒更新'
  },
  {
    name: '貨幣基礎',
    status: 'simulated',
    description: '基於香港金管局的模擬貨幣供應數據',
    lastUpdate: '每 30 秒更新'
  },
  {
    name: '策略數據',
    status: 'simulated',
    description: '演示用的策略列表和回測結果',
    lastUpdate: '靜態數據'
  },
  {
    name: '市場 regime 檢測',
    status: 'simulated',
    description: '模擬的牛熊市場指標',
    lastUpdate: '每 60 秒更新'
  }
];

export default function RealDataOverview() {
  const getStatusBadge = (status: DataSource['status']) => {
    switch (status) {
      case 'real':
        return <SquareBadge status="success" size="sm">真實數據</SquareBadge>;
      case 'simulated':
        return <SquareBadge status="warning" size="sm">模擬數據</SquareBadge>;
      case 'fallback':
        return <SquareBadge status="error" size="sm">備用數據</SquareBadge>;
      default:
        return <SquareBadge status="default" size="sm">未知</SquareBadge>;
    }
  };

  const getStatusIcon = (status: DataSource['status']) => {
    switch (status) {
      case 'real':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'simulated':
        return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case 'fallback':
        return <Database className="w-5 h-5 text-red-600" />;
      default:
        return <TrendingUp className="w-5 h-5 text-gray-600" />;
    }
  };

  const realDataCount = dataSources.filter(ds => ds.status === 'real').length;
  const simulatedDataCount = dataSources.filter(ds => ds.status === 'simulated').length;
  const fallbackDataCount = dataSources.filter(ds => ds.status === 'fallback').length;

  return (
    <SquareCard>
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">數據來源概覽</h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">真實數據:</span>
            <span className="text-lg font-semibold text-green-600">{realDataCount}</span>
            <span className="text-sm text-gray-500">模擬數據:</span>
            <span className="text-lg font-semibold text-yellow-600">{simulatedDataCount}</span>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* 統計卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <CheckCircle className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <div className="text-2xl font-bold text-green-900">{realDataCount}</div>
                <div className="text-sm text-green-700">真實數據源</div>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertCircle className="w-8 h-8 text-yellow-600 mr-3" />
              <div>
                <div className="text-2xl font-bold text-yellow-900">{simulatedDataCount}</div>
                <div className="text-sm text-yellow-700">模擬數據源</div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <Database className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <div className="text-2xl font-bold text-blue-900">{dataSources.length}</div>
                <div className="text-sm text-blue-700">總數據源</div>
              </div>
            </div>
          </div>
        </div>

        {/* 數據源列表 */}
        <div className="space-y-4">
          {dataSources.map((source, index) => (
            <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <div className="flex items-center space-x-3">
                {getStatusIcon(source.status)}
                <div>
                  <h4 className="text-sm font-medium text-gray-900">{source.name}</h4>
                  <p className="text-xs text-gray-600 mt-1">{source.description}</p>
                </div>
              </div>
              <div className="flex flex-col items-end space-y-2">
                {getStatusBadge(source.status)}
                {source.lastUpdate && (
                  <span className="text-xs text-gray-500">{source.lastUpdate}</span>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* 說明文字 */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="text-sm font-medium text-blue-900 mb-2">📊 數據說明</h4>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>• <span className="font-medium">真實數據</span>：來自實時 API（如 Yahoo Finance）</li>
            <li>• <span className="font-medium">模擬數據</span>：基於真實數據結構的生成數據</li>
            <li>• <span className="font-medium">北向資金</span>：使用本地爬蟲文件中的數據（HKEX_北向資金_5年數據.csv）</li>
          </ul>
        </div>
      </div>
    </SquareCard>
  );
}