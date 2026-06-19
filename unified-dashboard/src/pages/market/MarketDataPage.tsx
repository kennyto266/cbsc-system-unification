import React, { useState, useEffect } from 'react'
import { Card, Table, Tag, Statistic, Row, Col, Progress, Spin, Empty, Tabs } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'

// 數據類型
interface HkexRecord {
  date: string
  trading_volume?: number
  advanced_stocks?: number
  declined_stocks?: number
  unchanged_stocks?: number
  turnover_hkd?: number
  deals?: number
  hsi_close?: number
  hsi_change?: number
  hsi_change_pct?: number
  hcei_close?: number
  hcei_change_pct?: number
}

interface StockConnectRecord {
  date: string
  southbound_total_mil?: number
  southbound_buy_mil?: number
  southbound_sell_mil?: number
  southbound_net_mil?: number
  sh_southbound_mil?: number
  sz_southbound_mil?: number
}

interface BacktestRecord {
  symbol: string
  sharpe: number
  return: number
  max_dd: number
  trades: number
  win_rate: number
  points: number
  status: string
}

// 工具函數
function formatHKD(value?: number): string {
  if (value == null) return '-'
  if (value >= 1e9) return `HK$${(value / 1e9).toFixed(2)}B`
  if (value >= 1e6) return `HK$${(value / 1e6).toFixed(0)}M`
  return `HK$${value.toLocaleString()}`
}

function formatMil(value?: number): string {
  if (value == null) return '-'
  return `${value.toLocaleString()}M`
}

function formatPct(value?: number): string {
  if (value == null) return '-'
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

// HKEX 每日報告組件
const HkexReport: React.FC = () => {
  const [data, setData] = useState<HkexRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/data/hkex_daily.json')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <Spin tip="載入 HKEX 數據..." />
  if (!data.length) return <Empty description="暫無 HKEX 數據。運行 python scripts/hkex_daily_crawler.py" />

  const latest = data[0]

  const columns = [
    { title: '日期', dataIndex: 'date', key: 'date', width: 110 },
    {
      title: '恆指收市', dataIndex: 'hsi_close', key: 'hsi_close',
      render: (v: number, r: HkexRecord) => v ? (
        <span>
          {v.toLocaleString(undefined, { maximumFractionDigits: 2 })}
          {' '}
          <Tag color={r.hsi_change! >= 0 ? 'green' : 'red'}>
            {r.hsi_change! >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            {' '}{Math.abs(r.hsi_change || 0).toFixed(2)} ({formatPct(r.hsi_change_pct)})
          </Tag>
        </span>
      ) : '-',
    },
    {
      title: '成交額', dataIndex: 'turnover_hkd', key: 'turnover',
      render: (v: number) => formatHKD(v),
      sorter: (a: HkexRecord, b: HkexRecord) => (a.turnover_hkd || 0) - (b.turnover_hkd || 0),
    },
    { title: '成交宗數', dataIndex: 'deals', key: 'deals', render: (v: number) => v?.toLocaleString() || '-' },
    {
      title: '升/跌', key: 'adv_dec',
      render: (_: any, r: HkexRecord) => (
        <span>
          <Tag color="green">↑{r.advanced_stocks || 0}</Tag>
          <Tag color="red">↓{r.declined_stocks || 0}</Tag>
        </span>
      ),
    },
  ]

  return (
    <div>
      {/* 最新統計卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="恆生指數"
              value={latest.hsi_close || 0}
              precision={2}
              valueStyle={{ color: (latest.hsi_change || 0) >= 0 ? '#3f8600' : '#cf1322' }}
              prefix={(latest.hsi_change || 0) >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix={` (${formatPct(latest.hsi_change_pct)})`}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="成交額" value={formatHKD(latest.turnover_hkd)} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="成交宗數" value={latest.deals?.toLocaleString() || '-'} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="升跌比"
              value={`${latest.advanced_stocks || 0} / ${latest.declined_stocks || 0}`}
            />
          </Card>
        </Col>
      </Row>

      <Card title={`HKEX 每日成交統計（${data.length} 天）`}>
        <Table
          dataSource={data}
          columns={columns}
          rowKey="date"
          size="small"
          pagination={{ pageSize: 15, size: 'small' }}
        />
      </Card>
    </div>
  )
}

// 南北水資金流向組件
const StockConnect: React.FC = () => {
  const [data, setData] = useState<StockConnectRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/data/stock_connect.json')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <Spin tip="載入南北水數據..." />
  if (!data.length) return <Empty description="暫無南北水數據。運行 python scripts/stock_connect_crawler.py" />

  const latest = data[data.length - 1]
  const netColor = (latest.southbound_net_mil || 0) >= 0 ? '#3f8600' : '#cf1322'

  const columns = [
    { title: '日期', dataIndex: 'date', key: 'date' },
    {
      title: '港股通總成交', dataIndex: 'southbound_total_mil', key: 'total',
      render: (v: number) => formatMil(v),
      sorter: (a: StockConnectRecord, b: StockConnectRecord) => (a.southbound_total_mil || 0) - (b.southbound_total_mil || 0),
    },
    { title: '買入', dataIndex: 'southbound_buy_mil', key: 'buy', render: (v: number) => formatMil(v) },
    { title: '賣出', dataIndex: 'southbound_sell_mil', key: 'sell', render: (v: number) => formatMil(v) },
    {
      title: '淨買入', dataIndex: 'southbound_net_mil', key: 'net',
      render: (v: number) => (
        <span style={{ color: v >= 0 ? '#3f8600' : '#cf1322', fontWeight: 600 }}>
          {v >= 0 ? '+' : ''}{formatMil(v)}
        </span>
      ),
      sorter: (a: StockConnectRecord, b: StockConnectRecord) => (a.southbound_net_mil || 0) - (b.southbound_net_mil || 0),
    },
    { title: '滬港通', dataIndex: 'sh_southbound_mil', key: 'sh', render: (v: number) => formatMil(v) },
    { title: '深港通', dataIndex: 'sz_southbound_mil', key: 'sz', render: (v: number) => formatMil(v) },
  ]

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="港股通總成交"
              value={formatMil(latest.southbound_total_mil)}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="淨買入"
              value={formatMil(latest.southbound_net_mil)}
              valueStyle={{ color: netColor }}
              prefix={(latest.southbound_net_mil || 0) >= 0 ? '📈' : '📉'}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="日期"
              value={latest.date}
            />
          </Card>
        </Col>
      </Row>

      <Card title={`南北水資金流向（${data.length} 天）`}>
        <Table
          dataSource={data}
          columns={columns}
          rowKey="date"
          size="small"
          pagination={{ pageSize: 15 }}
        />
      </Card>
    </div>
  )
}

// 回測結果組件
const BacktestResults: React.FC = () => {
  const [data, setData] = useState<BacktestRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/data/backtest_results.json')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <Spin tip="載入回測結果..." />
  if (!data.length) return <Empty description="暫無回測結果。運行 python scripts/multiprocess_backtest.py" />

  const columns = [
    { title: '股票', dataIndex: 'symbol', key: 'symbol', width: 100,
      render: (v: string) => <strong>{v}</strong> },
    {
      title: 'Sharpe', dataIndex: 'sharpe', key: 'sharpe',
      render: (v: number) => <span style={{ color: v >= 0.5 ? '#3f8600' : v >= 0 ? '#faad14' : '#cf1322', fontWeight: 600 }}>{v.toFixed(3)}</span>,
      sorter: (a: BacktestRecord, b: BacktestRecord) => a.sharpe - b.sharpe,
      defaultSortOrder: 'descend' as const,
    },
    {
      title: '回報率', dataIndex: 'return', key: 'return',
      render: (v: number) => (
        <span style={{ color: v >= 0 ? '#3f8600' : '#cf1322' }}>
          {v >= 0 ? '+' : ''}{(v * 100).toFixed(1)}%
        </span>
      ),
      sorter: (a: BacktestRecord, b: BacktestRecord) => a.return - b.return,
    },
    {
      title: '最大回撤', dataIndex: 'max_dd', key: 'max_dd',
      render: (v: number) => <span style={{ color: '#cf1322' }}>{(v * 100).toFixed(1)}%</span>,
      sorter: (a: BacktestRecord, b: BacktestRecord) => a.max_dd - b.max_dd,
    },
    { title: '交易次數', dataIndex: 'trades', key: 'trades', sorter: (a: BacktestRecord, b: BacktestRecord) => a.trades - b.trades },
    {
      title: '勝率', dataIndex: 'win_rate', key: 'win_rate',
      render: (v: number) => <Progress percent={Math.round(v * 100)} size="small" format={() => `${(v * 100).toFixed(0)}%`} />,
      sorter: (a: BacktestRecord, b: BacktestRecord) => a.win_rate - b.win_rate,
    },
    { title: '數據點', dataIndex: 'points', key: 'points' },
  ]

  const bestSharpe = Math.max(...data.map(d => d.sharpe))
  const avgReturn = data.reduce((s, d) => s + d.return, 0) / data.length

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic title="回測股票數" value={data.length} suffix="隻" />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="最佳 Sharpe" value={bestSharpe.toFixed(3)} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="平均回報"
              value={`${(avgReturn * 100).toFixed(1)}%`}
              valueStyle={{ color: avgReturn >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title={`多 CPU 回測結果（${data.length} 隻股票）`}>
        <Table
          dataSource={data}
          columns={columns}
          rowKey="symbol"
          size="small"
          pagination={false}
        />
      </Card>
    </div>
  )
}

// 主頁面
const MarketDataPage: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: 24 }}>📊 市場數據中心</h1>
      <Tabs
        defaultActiveKey="hkex"
        items={[
          {
            key: 'hkex',
            label: '📈 HKEX 每日報告',
            children: <HkexReport />,
          },
          {
            key: 'connect',
            label: '💰 南北水資金流向',
            children: <StockConnect />,
          },
          {
            key: 'backtest',
            label: '🔬 回測結果',
            children: <BacktestResults />,
          },
        ]}
      />
    </div>
  )
}

export default MarketDataPage
