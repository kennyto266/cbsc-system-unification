import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Tag, Space, Progress, Typography, Tooltip, BackTop } from 'antd';
import { ArrowLeftOutlined, StarOutlined, TrophyOutlined, FireOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { Strategy } from '../../types/index';
import './StrategyList.css';

const { Title, Text } = Typography;

interface StrategyListProps {
  category: string;
  filters?: any;
  onBack: () => void;
}

const StrategyList: React.FC<StrategyListProps> = ({ category, filters = {}, onBack }) => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState<{
    key: keyof Strategy;
    direction: 'asc' | 'desc';
  } | null>(null);

  // 模擬策略數據
  const mockStrategies: Strategy[] = [
    {
      id: 1,
      name: '月度低頻RSI策略',
      category: 'monthly_low_frequency',
      subcategory: 'RSI-Based',
      annual_return: 0.156,
      sharpe_ratio: 1.24,
      max_drawdown: 0.087,
      win_rate: 0.632,
      volatility: 0.124,
      trading_frequency: 'monthly',
      risk_level: 'medium',
      grade: 'A-',
      description: '基於月度RSI信號的低頻交易策略，專注於長期趨勢捕捉'
    },
    {
      id: 2,
      name: '月度MACD趨勢策略',
      category: 'monthly_low_frequency',
      subcategory: 'MACD-Based',
      annual_return: 0.142,
      sharpe_ratio: 1.18,
      max_drawdown: 0.093,
      win_rate: 0.598,
      volatility: 0.119,
      trading_frequency: 'monthly',
      risk_level: 'medium',
      grade: 'B+',
      description: '利用月度MACD指標識別趨勢轉折點的長期策略'
    },
    {
      id: 3,
      name: '動量突破策略',
      category: 'monthly_low_frequency',
      subcategory: 'Momentum',
      annual_return: 0.189,
      sharpe_ratio: 1.45,
      max_drawdown: 0.112,
      win_rate: 0.654,
      volatility: 0.136,
      trading_frequency: 'monthly',
      risk_level: 'medium',
      grade: 'A',
      description: '捕捉市場動量突破的月度交易策略'
    },
    {
      id: 4,
      name: '均值回歸策略',
      category: 'monthly_low_frequency',
      subcategory: 'Mean Reversion',
      annual_return: 0.134,
      sharpe_ratio: 1.09,
      max_drawdown: 0.089,
      win_rate: 0.621,
      volatility: 0.118,
      trading_frequency: 'monthly',
      risk_level: 'low',
      grade: 'B+',
      description: '基於均值回歸理論的保守型月度策略'
    },
    {
      id: 5,
      name: '波動率加權策略',
      category: 'monthly_low_frequency',
      subcategory: 'Volatility-Based',
      annual_return: 0.167,
      sharpe_ratio: 1.38,
      max_drawdown: 0.098,
      win_rate: 0.643,
      volatility: 0.129,
      trading_frequency: 'monthly',
      risk_level: 'medium',
      grade: 'A-',
      description: '根據市場波動率調整頭寸大小的動態策略'
    }
  ];

  useEffect(() => {
    const loadStrategies = async () => {
      setLoading(true);
      try {
        // 模擬API調用
        await new Promise(resolve => setTimeout(resolve, 1000));

        // 應用篩選條件
        let filteredStrategies = [...mockStrategies];

        if (filters.grades?.length > 0) {
          filteredStrategies = filteredStrategies.filter(s =>
            filters.grades.includes(s.grade)
          );
        }

        if (filters.risk_levels?.length > 0) {
          filteredStrategies = filteredStrategies.filter(s =>
            filters.risk_levels.includes(s.risk_level)
          );
        }

        if (filters.min_sharpe !== null) {
          filteredStrategies = filteredStrategies.filter(s =>
            (s.sharpe_ratio || 0) >= filters.min_sharpe
          );
        }

        if (filters.min_return !== null) {
          filteredStrategies = filteredStrategies.filter(s =>
            s.annual_return >= filters.min_return
          );
        }

        if (filters.search_term) {
          const searchTerm = filters.search_term.toLowerCase();
          filteredStrategies = filteredStrategies.filter(s =>
            s.name.toLowerCase().includes(searchTerm) ||
            s.description.toLowerCase().includes(searchTerm)
          );
        }

        setStrategies(filteredStrategies);
      } catch (error) {
        console.error('Failed to load strategies:', error);
      } finally {
        setLoading(false);
      }
    };

    loadStrategies();
  }, [category, filters]);

  const handleSort = (key: keyof Strategy) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedStrategies = React.useMemo(() => {
    if (!sortConfig) return strategies;

    return [...strategies].sort((a, b) => {
      const aValue = a[sortConfig.key] || 0;
      const bValue = b[sortConfig.key] || 0;

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [strategies, sortConfig]);

  const getGradeColor = (grade: string) => {
    const gradeColors: { [key: string]: string } = {
      'A+': '#52c41a',
      'A': '#73d13d',
      'A-': '#95de64',
      'B+': '#b7eb8f',
      'B': '#d9f7be',
      'B-': '#fff7e6',
      'C+': '#ffe7ba',
      'C': '#ffd666',
      'C-': '#ffccc7',
      'D+': '#ff9c6e',
      'D': '#ff7875',
      'D-': '#ff4d4f',
      'F': '#cf1322'
    };
    return gradeColors[grade] || '#d9d9d9';
  };

  const getRiskColor = (risk: string) => {
    const riskColors: { [key: string]: string } = {
      'low': '#52c41a',
      'medium': '#faad14',
      'high': '#ff4d4f'
    };
    return riskColors[risk] || '#d9d9d9';
  };

  const columns = [
    {
      title: '策略名稱',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (name: string, record: Strategy) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
            {name}
          </div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.subcategory}
          </Text>
        </div>
      )
    },
    {
      title: '年化收益',
      dataIndex: 'annual_return',
      key: 'annual_return',
      width: 100,
      sorter: true,
      render: (value: number) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>
            {(value * 100).toFixed(2)}%
          </div>
        </div>
      )
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpe_ratio',
      key: 'sharpe_ratio',
      width: 100,
      sorter: true,
      render: (value: number | null) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>
            {value?.toFixed(2) || 'N/A'}
          </div>
        </div>
      )
    },
    {
      title: '最大回撤',
      dataIndex: 'max_drawdown',
      key: 'max_drawdown',
      width: 100,
      sorter: true,
      render: (value: number) => (
        <div>
          <div style={{ fontWeight: 'bold', color: '#ff4d4f' }}>
            -{(value * 100).toFixed(2)}%
          </div>
        </div>
      )
    },
    {
      title: '勝率',
      dataIndex: 'win_rate',
      key: 'win_rate',
      width: 100,
      sorter: true,
      render: (value: number) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>
            {(value * 100).toFixed(1)}%
          </div>
          <Progress
            percent={value * 100}
            size="small"
            showInfo={false}
            strokeColor={value >= 0.6 ? '#52c41a' : value >= 0.5 ? '#faad14' : '#ff4d4f'}
          />
        </div>
      )
    },
    {
      title: '評級',
      dataIndex: 'grade',
      key: 'grade',
      width: 80,
      render: (grade: string) => (
        <Tag color={getGradeColor(grade)}>
          {grade}
        </Tag>
      )
    },
    {
      title: '風險',
      dataIndex: 'risk_level',
      key: 'risk_level',
      width: 80,
      render: (risk: string) => (
        <Tag color={getRiskColor(risk)}>
          {risk === 'low' ? '低' : risk === 'medium' ? '中' : '高'}
        </Tag>
      )
    },
    {
      title: '交易頻率',
      dataIndex: 'trading_frequency',
      key: 'trading_frequency',
      width: 100,
      render: (frequency: string) => (
        <span>
          {frequency === 'monthly' ? '月度' :
           frequency === 'daily' ? '日度' :
           frequency === 'weekly' ? '週度' : '實時'}
        </span>
      )
    }
  ];

  const categoryInfo: { [key: string]: { title: string; description: string; icon: React.ReactNode } } = {
    'monthly_low_frequency': {
      title: '月度低頻策略',
      description: '專注於長期投資回報的月度交易策略',
      icon: <StarOutlined />
    },
    'multi_strategy_validation': {
      title: '多策略驗證系統',
      description: '結合多種策略信號進行風險控制的綜合系統',
      icon: <TrophyOutlined />
    },
    'multi_factor_model': {
      title: '多因子模型',
      description: '基於多個市場因子的量化模型策略',
      icon: <ThunderboltOutlined />
    },
    'core_cbsc_technical': {
      title: '核心CBSC技術分析',
      description: '基於CBSC數據的傳統技術指標策略',
      icon: <FireOutlined />
    },
    'core_cbsc_sentiment': {
      title: '核心CBSC情緒分析',
      description: '利用市場情緒指標的CBSC策略',
      icon: <StarOutlined />
    },
    'core_cbsc_aggressive': {
      title: '核心CBSC激進策略',
      description: '高風險高回報的激進型CBSC策略',
      icon: <ThunderboltOutlined />
    },
    'portfolio_optimization': {
      title: '投資組合優化',
      description: '基於現代投資組合理論的優化策略',
      icon: <TrophyOutlined />
    }
  };

  const currentCategory = categoryInfo[category] || { title: category, description: '', icon: <StarOutlined /> };

  return (
    <div style={{ padding: '24px' }}>
      {/* 頭部信息 */}
      <Card style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={onBack}
            style={{ marginRight: '16px' }}
          >
            返回分類
          </Button>
          <div style={{ flex: 1 }}>
            <Title level={3} style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
              {currentCategory.icon}
              <span style={{ marginLeft: '8px' }}>{currentCategory.title}</span>
            </Title>
            <Text type="secondary">{currentCategory.description}</Text>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <Text strong>策略總數:</Text> {strategies.length}
          </div>
          {strategies.length > 0 && (
            <>
              <div>
                <Text strong>平均年化收益:</Text> {(strategies.reduce((sum, s) => sum + s.annual_return, 0) / strategies.length * 100).toFixed(2)}%
              </div>
              <div>
                <Text strong>平均夏普比率:</Text> {(strategies.reduce((sum, s) => sum + (s.sharpe_ratio || 0), 0) / strategies.length).toFixed(2)}
              </div>
              <div>
                <Text strong>平均勝率:</Text> {(strategies.reduce((sum, s) => sum + s.win_rate, 0) / strategies.length * 100).toFixed(1)}%
              </div>
            </>
          )}
        </div>
      </Card>

      {/* 策略列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={sortedStrategies}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} 共 ${total} 條`,
            pageSizeOptions: ['10', '20', '50', '100']
          }}
          onChange={(pagination, filters, sorter) => {
            if (sorter && !Array.isArray(sorter)) {
              handleSort(sorter.columnKey as keyof Strategy);
            }
          }}
          scroll={{ x: 1000 }}
          onRow={(record) => ({
            onClick: () => {
              console.log('查看策略詳情:', record.name);
            },
            style: { cursor: 'pointer' }
          })}
        />
      </Card>

      <BackTop />
    </div>
  );
};

export default StrategyList;