/**
 * CBSC 牛熊证监控标签页
 * CBSC Bull/Bear Contract Monitoring Tab Page
 */

import React from 'react';
import { Tabs } from 'antd';
import {
  DashboardOutlined,
  BarChartOutlined,
  TrophyOutlined
} from '@ant-design/icons';
import CBSCDashboard from '../../components/cbsc/CBSCDashboard';
import { useTranslation } from 'react-i18next';

const { TabPane } = Tabs;

const CBSCTabPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="h-full">
      <Tabs
        defaultActiveKey="overview"
        size="large"
        className="w-full"
        items={[
          {
            key: 'overview',
            label: (
              <span>
                <DashboardOutlined />
                市场总览
              </span>
            ),
            children: <CBSCDashboard />,
          },
          {
            key: 'analysis',
            label: (
              <span>
                <BarChartOutlined />
                深度分析
              </span>
            ),
            children: (
              <div className="p-6">
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-semibold mb-4">深度市场分析</h2>
                  <div className="text-gray-600">
                    <p>此功能正在开发中，敬请期待...</p>
                    <p className="mt-2">将包含：</p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>技术指标深度分析</li>
                      <li>资金流向分析</li>
                      <li>机构持仓分析</li>
                      <li>波动率预测模型</li>
                    </ul>
                  </div>
                </div>
              </div>
            ),
          },
          {
            key: 'ranking',
            label: (
              <span>
                <TrophyOutlined />
                排行榜
              </span>
            ),
            children: (
              <div className="p-6">
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-xl font-semibold mb-4">牛熊证排行榜</h2>
                  <div className="text-gray-600">
                    <p>此功能正在开发中，敬请期待...</p>
                    <p className="mt-2">将包含：</p>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      <li>涨幅榜</li>
                      <li>跌幅榜</li>
                      <li>成交量榜</li>
                      <li>热门追踪榜</li>
                    </ul>
                  </div>
                </div>
              </div>
            ),
          },
        ]}
      />
    </div>
  );
};

export default CBSCTabPage;