/**
 * StressTestTable Component
 * Table showing stress test results across 4 scenarios
 */

import React from 'react';
import { Table, Empty, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { useAppSelector } from '../../../../hooks/redux';
import type { StressTestResult } from '../../../../store/slices/performanceAnalyticsSlice';

interface StressTestRecord extends StressTestResult {
  key: string;
}

export const StressTestTable: React.FC = () => {
  const stressTest = useAppSelector((state) => state.performanceAnalytics.stressTest);
  const isLoading = useAppSelector((state) => state.performanceAnalytics.isLoading);

  const columns: ColumnsType<StressTestRecord> = [
    {
      title: '場景',
      dataIndex: 'scenario',
      key: 'scenario',
      width: 150,
    },
    {
      title: '預期收益',
      dataIndex: 'expectedReturn',
      key: 'expectedReturn',
      align: 'right',
      render: (value: number) => (
        <span className={`stress-value ${value >= 0 ? 'positive' : 'negative'}`}>
          {value >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '最大回撤',
      dataIndex: 'maxDrawdown',
      key: 'maxDrawdown',
      align: 'right',
      render: (value: number) => (
        <span className="stress-value negative">
          {value.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpeRatio',
      key: 'sharpeRatio',
      align: 'right',
      render: (value: number) => {
        let color = 'default';
        if (value > 1) color = 'success';
        else if (value > 0) color = 'warning';
        else color = 'error';
        return <Tag color={color}>{value.toFixed(2)}</Tag>;
      },
    },
  ];

  const dataSource = React.useMemo(() => {
    if (!stressTest) return [];
    return stressTest.map((item, index) => ({
      key: index.toString(),
      ...item,
    }));
  }, [stressTest]);

  if (!stressTest && !isLoading) {
    return <Empty description="無數據" />;
  }

  return (
    <div className="stress-test-table">
      <Table
        columns={columns}
        dataSource={dataSource}
        loading={isLoading}
        pagination={false}
        size="middle"
      />
    </div>
  );
};

export default StressTestTable;
