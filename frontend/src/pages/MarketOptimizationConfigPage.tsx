/**
 * Market-Wide Optimization Configuration Page
 * Allows users to configure and start optimization tasks
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Form, InputNumber, Select, Button, Space, Breadcrumb, message } from 'antd';
import { HomeOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import marketOptimizationApi from '../services/marketOptimizationApi';
import type { OptimizationConfig } from '../types/market-optimization';
import './MarketOptimizationConfigPage.css';

const { Range } = InputNumber;

const MarketOptimizationConfigPage: React.FC = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const configForm: OptimizationConfig = {
    stock_count: 50,
    start_date: '2020-01-01',
    end_date: '2024-12-31',
    strategy_type: 'ma_crossover',
    initial_cash: 100000,
    commission: 0.001,
    min_sharpe_ratio: 0.8,
    max_workers: 31
  };

  const handleStart = async (values: OptimizationConfig) => {
    setLoading(true);

    try {
      const response = await marketOptimizationApi.startOptimization(values);
      message.success('優化任務已啟動！');
      navigate(`/market-optimization/results/${response.task_id}`);
    } catch (error: any) {
      message.error('啟動失敗：' + (error.message || '未知錯誤'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container">
      <Breadcrumb className="breadcrumb">
        <Breadcrumb.Item>
          <Link to="/"><HomeOutlined /> 首頁</Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>市場優化</Breadcrumb.Item>
      </Breadcrumb>

      <Card className="config-card" bordered={false}>
        <div className="config-header">
          <h1>市場廣域參數優化</h1>
          <p>使用多進程並行優化多只股票的交易策略參數</p>
        </div>

        <Form
          form={form}
          layout="vertical"
          initialValues={configForm}
          onFinish={handleStart}
          className="config-form"
        >
          <Form.Item label="股票數量" name="stock_count" rules={[{ required: true }]}>
            <Select options={[
              { value: 10, label: '10 只股票（測試）' },
              { value: 30, label: '30 只股票' },
              { value: 50, label: '50 只股票（推薦）' }
            ]} />
          </Form.Item>

          <Space size="large">
            <Form.Item label="開始日期" name="start_date" rules={[{ required: true }]}>
              <InputNumber style={{ width: 150 }} min={2010} max={2024} />
            </Form.Item>

            <Form.Item label="結束日期" name="end_date" rules={[{ required: true }]}>
              <InputNumber style={{ width: 150 }} min={2010} max={2024} />
            </Form.Item>
          </Space>

          <Form.Item label="最小 Sharpe Ratio" name="min_sharpe_ratio" rules={[{ required: true }]}>
            <Select options={[
              { value: 0.5, label: '0.5 (寬鬆)' },
              { value: 0.8, label: '0.8 (中等)' },
              { value: 1.0, label: '1.0 (嚴格)' },
              { value: 1.5, label: '1.5 (很嚴格)' },
              { value: 2.0, label: '2.0 (極嚴格)' }
            ]} />
          </Form.Item>

          <Form.Item label="最大工作進程" name="max_workers" rules={[{ required: true }]}>
            <Select options={[
              { value: 15, label: '15 (半 CPU)' },
              { value: 31, label: '31 (推薦 - 32核CPU)' }
            ]} />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              size="large"
              icon={<PlayCircleOutlined />}
            >
              開始優化
            </Button>
          </Form.Item>
        </Form>

        <div className="info-section">
          <h3>預估信息</h3>
          <ul>
            <li>50 只股票 × ~468 參數組合 = ~23,400 個回測</li>
            <li>使用 31 個工作進程並行處理</li>
            <li>預計完成時間：1-2 分鐘</li>
            <li>使用真實 Yahoo Finance 市場數據</li>
          </ul>
        </div>
      </Card>
    </div>
  );
};

export default MarketOptimizationConfigPage;
