/**
 * Top Strategies Table Component
 * Displays top 10 strategies with selectable rows
 */

import React from 'react';
import { Table, Card, Tag } from 'antd';
import type { ColumnsType, TableProps } from 'antd';
import type { StrategyResult } from '../../types/market-optimization';
import type { SorterResult } from 'antd/es/table/interface';
import './TopStrategiesTable.css';

interface TopStrategiesTableProps {
  strategies: StrategyResult[];
  selectedIndex: number;
  onSelectStrategy: (index: number) => void;
}

interface TableRow extends StrategyResult {
  key: number;
  rank: number;
}

const TopStrategiesTable: React.FC<TopStrategiesTableProps> = ({
  strategies,
  selectedIndex,
  onSelectStrategy
}) => {
  if (!strategies || strategies.length === 0) {
    return (
      <Card className="top-strategies-table" bordered={false}>
        <div className="top-strategies-empty">
          沒有符合條件的策略結果
        </div>
      </Card>
    );
  }

  // Transform data for table
  const dataSource: TableRow[] = strategies.map((strategy, index) => ({
    ...strategy,
    key: index,
    rank: index + 1
  }));

  // Row click handler
  const handleRowClick: TableProps<TableRow>['onRow'] = (record, index) => ({
    onClick: () => {
      if (typeof index === 'number') {
        onSelectStrategy(index);
      }
    },
    style: { cursor: 'pointer' }
  });

  // Row class name
  const rowClassName = (record: TableRow, index: number | undefined) => {
    return index === selectedIndex ? 'selected-row' : '';
  };

  // Columns definition
  const columns: ColumnsType<TableRow> = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 70,
      align: 'center',
      render: (rank: number) => (
        <span className={`rank-badge rank-${rank <= 3 ? 'top' : 'normal'}`}>
          #{rank}
        </span>
      )
    },
    {
      title: '股票代碼',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
      render: (symbol: string) => <Tag color="blue">{symbol}</Tag>
    },
    {
      title: 'MA 參數',
      key: 'params',
      width: 100,
      render: (_, record: TableRow) => (
        <span>
          MA({record.params.short_period}/{record.params.long_period})
        </span>
      )
    },
    {
      title: '總回報',
      dataIndex: 'total_return',
      key: 'total_return',
      width: 110,
      sorter: (a: TableRow, b: TableRow) => a.total_return - b.total_return,
      render: (value: number) => (
        <span className={value >= 0 ? 'positive' : 'negative'}>
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </span>
      ),
      defaultSortOrder: 'descend' as const
    },
    {
      title: 'Sharpe',
      dataIndex: 'sharpe_ratio',
      key: 'sharpe_ratio',
      width: 90,
      sorter: (a: TableRow, b: TableRow) => a.sharpe_ratio - b.sharpe_ratio,
      render: (value: number) => (
        <span className={value >= 1 ? 'positive' : value >= 0 ? 'neutral' : 'negative'}>
          {value.toFixed(2)}
        </span>
      )
    },
    {
      title: '最大回撤',
      dataIndex: 'max_drawdown',
      key: 'max_drawdown',
      width: 100,
      sorter: (a: TableRow, b: TableRow) => a.max_drawdown - b.max_drawdown,
      render: (value: number) => (
        <span className="negative">
          {value.toFixed(2)}%
        </span>
      )
    },
    {
      title: '超額回報',
      dataIndex: 'excess_return',
      key: 'excess_return',
      width: 110,
      sorter: (a: TableRow, b: TableRow) => a.excess_return - b.excess_return,
      render: (value: number) => (
        <span className={value >= 0 ? 'positive' : 'negative'}>
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </span>
      )
    }
  ];

  return (
    <Card className="top-strategies-table" bordered={false} title="Top 10 策略">
      <Table
        columns={columns}
        dataSource={dataSource}
        onRow={handleRowClick}
        rowClassName={rowClassName}
        pagination={false}
        size="middle"
      />
    </Card>
  );
};

export default TopStrategiesTable;
