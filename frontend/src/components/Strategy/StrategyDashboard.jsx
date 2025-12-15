/**
 * Strategy Dashboard Component
 * 策略仪表板组件
 *
 * Features:
 * - 显示所有策略概览
 * - 实时性能指标
 * - 策略执行状态
 * - 交互式图表展示
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Button,
  Space,
  Select,
  DatePicker,
  Progress,
  Tooltip,
  Modal,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
  LineChartOutlined,
} from '@ant-design/icons';
import { Line, Column } from '@ant-design/plots';
import { strategyAPI, wsManager } from '../../services/api';

const { Option } = Select;
const { RangePicker } = DatePicker;

const StrategyDashboard = () => {
  // State
  const [strategies, setStrategies] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('7d');
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  // Fetch strategies data
  const fetchStrategies = async () => {
    setLoading(true);
    try {
      const response = await strategyAPI.getStrategies(1, 100);
      setStrategies(response.data || []);

      // Generate performance data for demo
      const perfData = generatePerformanceData(response.data || []);
      setPerformanceData(perfData);
    } catch (error) {
      console.error('获取策略数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // Generate mock performance data
  const generatePerformanceData = (strategyList) => {
    const data = [];
    const dates = [];
    const now = new Date();

    // Generate date labels
    for (let i = 6; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      dates.push(date.toISOString().split('T')[0]);
    }

    // Generate data for each strategy
    strategyList.forEach(strategy => {
      dates.forEach(date => {
        data.push({
          date,
          strategy: strategy.name,
          value: Math.random() * 100 + 50,
          profit: (Math.random() - 0.5) * 20,
        });
      });
    });

    return data;
  };

  useEffect(() => {
    fetchStrategies();

    // Subscribe to WebSocket updates
    wsManager.subscribe('strategy_update', (data) => {
      setStrategies(prevStrategies =>
        prevStrategies.map(s =>
          s.id === data.strategy_id ? { ...s, ...data.updates } : s
        )
      );
    });

    wsManager.subscribe('strategy_execution', (data) => {
      // Update strategy execution status
      setStrategies(prevStrategies =>
        prevStrategies.map(s =>
          s.id === data.strategy_id
            ? { ...s, status: data.status, last_run: data.timestamp }
            : s
        )
      );
    });

    return () => {
      wsManager.unsubscribe('strategy_update');
      wsManager.unsubscribe('strategy_execution');
    };
  }, []);

  // Calculate statistics
  const activeStrategies = strategies.filter(s => s.status === 'active').length;
  const totalProfit = strategies.reduce((sum, s) => sum + (s.profit || 0), 0);
  const avgReturn = strategies.length > 0
    ? strategies.reduce((sum, s) => sum + (s.return_rate || 0), 0) / strategies.length
    : 0;

  // Table columns
  const columns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <span>{text}</span>
          {record.status === 'running' && (
            <Tag color="green" icon={<PlayCircleOutlined />}>运行中</Tag>
          )}
          {record.status === 'paused' && (
            <Tag color="orange" icon={<PauseCircleOutlined />}>已暂停</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => <Tag>{type}</Tag>,
    },
    {
      title: '收益率',
      dataIndex: 'return_rate',
      key: 'return_rate',
      render: (value) => (
        <span style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {value >= 0 ? '+' : ''}{value?.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '今日盈亏',
      dataIndex: 'daily_pnl',
      key: 'daily_pnl',
      render: (value) => (
        <span style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          ¥{value?.toFixed(2)}
        </span>
      ),
    },
    {
      title: '最大回撤',
      dataIndex: 'max_drawdown',
      key: 'max_drawdown',
      render: (value) => <span>{(value * 100)?.toFixed(2)}%</span>,
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpe_ratio',
      key: 'sharpe_ratio',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<LineChartOutlined />}
              onClick={() => {
                setSelectedStrategy(record);
                setDetailModalVisible(true);
              }}
            />
          </Tooltip>
          <Tooltip title="设置">
            <Button
              type="link"
              icon={<SettingOutlined />}
              onClick={() => {
                // TODO: Open settings modal
                console.log('Settings for:', record.name);
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // Chart config for performance trend
  const perfTrendConfig = {
    data: performanceData,
    xField: 'date',
    yField: 'value',
    seriesField: 'strategy',
    smooth: true,
    color: ['#5B8FF9', '#5AD8A6', '#5D7092', '#F6BD16', '#E8684A'],
    legend: {
      position: 'top',
    },
    point: {
      size: 3,
      shape: 'circle',
    },
  };

  // Chart config for profit distribution
  const profitDistConfig = {
    data: strategies.map(s => ({
      strategy: s.name,
      profit: s.profit || 0,
    })),
    xField: 'strategy',
    yField: 'profit',
    columnWidthRatio: 0.8,
    color: (data) => (data.profit >= 0 ? '#52c41a' : '#ff4d4f'),
  };

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between' }}>
        <h2>策略仪表板</h2>
        <Space>
          <Select
            value={timeRange}
            onChange={setTimeRange}
            style={{ width: 120 }}
          >
            <Option value="1d">今日</Option>
            <Option value="7d">7天</Option>
            <Option value="30d">30天</Option>
            <Option value="90d">90天</Option>
          </Select>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchStrategies}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行中策略"
              value={activeStrategies}
              suffix={`/ ${strategies.length}`}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总盈亏"
              value={totalProfit}
              precision={2}
              prefix="¥"
              valueStyle={{ color: totalProfit >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均收益率"
              value={avgReturn}
              precision={2}
              suffix="%"
              valueStyle={{ color: avgReturn >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="系统运行率"
              value={98.5}
              precision={1}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
            />
            <Progress percent={98.5} showInfo={false} />
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Card title="策略性能趋势" style={{ height: 400 }}>
            <Line {...perfTrendConfig} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="策略盈亏分布" style={{ height: 400 }}>
            <Column {...profitDistConfig} />
          </Card>
        </Col>
      </Row>

      {/* Strategy Table */}
      <Card title="策略列表">
        <Table
          columns={columns}
          dataSource={strategies}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个策略`,
          }}
        />
      </Card>

      {/* Strategy Detail Modal */}
      <Modal
        title={selectedStrategy?.name}
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedStrategy && (
          <div>
            <p><strong>策略类型:</strong> {selectedStrategy.type}</p>
            <p><strong>创建时间:</strong> {new Date(selectedStrategy.created_at).toLocaleString()}</p>
            <p><strong>状态:</strong> {selectedStrategy.status}</p>
            <p><strong>描述:</strong> {selectedStrategy.description || '-'}</p>
            {/* Add more details as needed */}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default StrategyDashboard;