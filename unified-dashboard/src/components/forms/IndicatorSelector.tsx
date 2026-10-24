import React, { useState, useEffect } from 'react'
import {
  Card,
  Select,
  Transfer,
  Tag,
  Space,
  Tooltip,
  Input,
  Row,
  Col,
  Divider,
} from 'antd'
import { InfoCircleOutlined, SearchOutlined } from '@ant-design/icons'

const { Option } = Select
const { Search } = Input

// Technical indicators categories
const indicatorCategories = {
  trend: {
    name: '趋势指标',
    indicators: [
      { id: 'sma', name: '简单移动平均线 (SMA)', description: '计算特定周期内的平均价格' },
      { id: 'ema', name: '指数移动平均线 (EMA)', description: '给予近期价格更高权重的移动平均线' },
      { id: 'wma', name: '加权移动平均线 (WMA)', description: '线性加权的移动平均线' },
      { id: 'dema', name: '双指数移动平均线 (DEMA)', description: '减少滞后性的双重平滑移动平均线' },
      { id: 'tema', name: '三重指数移动平均线 (TEMA)', description: '进一步减少滞后性的三重平滑移动平均线' },
      { id: 'trima', name: '三角移动平均线 (TRIMA)', description: '基于三角移动平均线的平滑指标' },
      { id: 'kama', name: '考夫曼自适应移动平均线 (KAMA)', description: '根据市场波动性自动调整周期的移动平均线' },
      { id: 'mama', name: 'MESA自适应移动平均线 (MAMA)', description: '基于MESA算法的自适应移动平均线' },
      { id: 't3', name: 'T3移动平均线 (T3)', description: '使用多重平滑处理的高级移动平均线' },
    ],
  },
  momentum: {
    name: '动量指标',
    indicators: [
      { id: 'rsi', name: '相对强弱指数 (RSI)', description: '衡量价格变动速度和变化幅度' },
      { id: 'macd', name: 'MACD', description: '移动平均收敛发散指标，识别趋势变化' },
      { id: 'cci', name: '商品通道指数 (CCI)', description: '识别周期性买卖信号' },
      { id: 'roc', name: '变动率指标 (ROC)', description: '测量当前价格与n期前价格的变化百分比' },
      { id: 'stoch', name: '随机指标 (Stochastic)', description: '比较收盘价与价格范围' },
      { id: 'stochrsi', name: 'StochRSI', description: 'RSI的随机指标版本' },
      { id: 'willr', name: '威廉姆斯%R (Williams %R)', description: '测量超买超卖水平' },
      { id: 'ado', name: '积累/派发振荡器 (ADO)', description: '衡量资金流入流出' },
      { id: 'mfi', name: '资金流量指数 (MFI)', description: '结合价格和成交量的RSI指标' },
      { id: 'dx', name: '动向指标 (DX)', description: '衡量趋势强度' },
    ],
  },
  volatility: {
    name: '波动率指标',
    indicators: [
      { id: 'atr', name: '平均真实波幅 (ATR)', description: '衡量市场波动性' },
      { id: 'bbands', name: '布林带 (Bollinger Bands)', description: '基于标准差的价格通道' },
      { id: 'obv', name: '能量潮 (OBV)', description: '基于成交量的动量指标' },
      { id: 'natr', name: '标准化平均真实波幅 (NATR)', description: '标准化的ATR指标' },
      { id: 'vortex', name: '漩涡指标 (Vortex)', description: '识别趋势开始和变化' },
      { id: 'trange', name: '真实波幅 (TRANGE)', description: '计算价格的真实波动范围' },
    ],
  },
  volume: {
    name: '成交量指标',
    indicators: [
      { id: 'ad', name: '积累/派发线 (A/D Line)', description: '测量资金流入流出' },
      { id: 'obv', name: '能量潮 (OBV)', description: '累计成交量指标' },
      { id: 'adosc', name: '积累/派发振荡器 (ADOSC)', description: '基于成交量的振荡器' },
      { id: 'cmf', name: 'Chaikin资金流量 (CMF)', description: '衡量资金压力' },
      { id: 'fi', name: '力量指数 (Force Index)', description: '结合价格变动和成交量的指标' },
      { id: 'eom', name: '易动指标 (EOM)', description: '衡量价格变动所需成交量' },
      { id: 'vpt', name: '价量趋势 (VPT)', description: '结合价格和成交量的趋势指标' },
      { id: 'pvt', name: '价量确认 (PVT)', description: '成交量加权的价格趋势' },
    ],
  },
  cycle: {
    name: '周期指标',
    indicators: [
      { id: 'dpo', name: '去趋势价格振荡器 (DPO)', description: '识别价格周期' },
      { id: 'httrendline', name: '希尔伯特变换趋势线 (HT Trendline)', description: '使用希尔伯特变换的趋势指标' },
      { id: 'htsine', name: '希尔伯特正弦波 (HT Sine)', description: '识别周期模式' },
      { id: 'htlead', name: '希尔伯特领先相 (HT Lead)', description: '预测价格转折点' },
      { id: 'htphasor', name: '希尔伯特相量 (HT Phasor)', description: '显示市场周期相位' },
    ],
  },
  pattern: {
    name: '形态指标',
    indicators: [
      { id: 'cdl2crows', name: '两只乌鸦', description: '看跌反转形态' },
      { id: 'cdl3blackcrows', name: '三只黑乌鸦', description: '强烈看跌信号' },
      { id: 'cdl3whitesoldiers', name: '三白兵', description: '强烈看涨信号' },
      { id: 'cdlabandonedbaby', name: '弃婴形态', description: '强烈反转信号' },
      { id: 'cdldarkcloudcover', name: '乌云盖顶', description: '看跌反转形态' },
      { id: 'cdldoji', name: '十字星', description: '趋势可能反转' },
      { id: 'cdldragonflydoji', name: '蜻蜓十字星', description: '潜在看涨反转' },
      { id: 'cdleveningstar', name: '黄昏之星', description: '看跌反转形态' },
      { id: 'cdlhammer', name: '锤头线', description: '潜在看涨反转' },
    ],
  },
  statistical: {
    name: '统计指标',
    indicators: [
      { id: 'beta', name: '贝塔系数 (Beta)', description: '衡量股票相对于市场的波动性' },
      { id: 'correl', name: '相关系数 (Correlation)', description: '测量两个资产的相关性' },
      { id: 'linearreg', name: '线性回归 (Linear Regression)', description: '价格趋势的线性拟合' },
      { id: 'tsf', name: '时间序列预测 (TSF)', description: '基于线性回归的价格预测' },
      { id: 'stddev', name: '标准差 (Standard Deviation)', description: '测量价格波动性' },
      { id: 'var', name: '方差 (Variance)', description: '价格波动的方差' },
    ],
  },
  custom: {
    name: '自定义指标',
    indicators: [
      { id: 'ichimoku', name: '一目均衡表 (Ichimoku)', description: '日本技术分析系统' },
      { id: 'supertrend', name: '超级趋势 (Supertrend)', description: '基于ATR的趋势跟踪指标' },
      { id: 'fibonacci', name: '斐波那契回调', description: '基于斐波那契数列的支撑阻力位' },
      { id: 'pivot', name: '枢轴点 (Pivot Points)', description: '计算关键支撑阻力位' },
      { id: 'elasticity', name: '价格弹性', description: '衡量价格对变化的敏感度' },
    ],
  },
}

interface IndicatorSelectorProps {
  selectedIndicators: string[]
  onChange: (indicators: string[]) => void
  maxSelections?: number
  disabled?: boolean
}

const IndicatorSelector: React.FC<IndicatorSelectorProps> = ({
  selectedIndicators,
  onChange,
  maxSelections = 10,
  disabled = false,
}) => {
  const [searchText, setSearchText] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  // Flatten all indicators for Transfer component
  const allIndicators = Object.entries(indicatorCategories).flatMap(([categoryKey, category]) =>
    category.indicators.map(indicator => ({
      ...indicator,
      category: category.name,
      categoryKey,
    }))
  )

  // Filter indicators based on search and category
  const filteredIndicators = allIndicators.filter(indicator => {
    const matchesSearch = indicator.name.toLowerCase().includes(searchText.toLowerCase()) ||
                         indicator.description.toLowerCase().includes(searchText.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || indicator.categoryKey === selectedCategory
    return matchesSearch && matchesCategory
  })

  // Transfer data format
  const transferData = filteredIndicators.map(indicator => ({
    key: indicator.id,
    title: indicator.name,
    description: indicator.description,
    category: indicator.category,
  }))

  // Selected keys for Transfer component
  const selectedKeys = selectedIndicators.filter(id =>
    transferData.some(item => item.key === id)
  )

  // Handle Transfer change
  const handleTransferChange = (nextTargetKeys: string[]) => {
    onChange(nextTargetKeys)
  }

  // Custom item rendering for Transfer
  const renderItem = (item: any) => {
    return (
      <div className="p-2 border rounded mb-2 hover:bg-gray-50">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="font-medium">{item.title}</div>
            <div className="text-xs text-gray-500 mt-1">{item.description}</div>
            <Tag size="small" color="blue" className="mt-1">{item.category}</Tag>
          </div>
        </div>
      </div>
    )
  }

  // Footer for Transfer component showing selection count
  const transferFooter = () => (
    <div className="text-center text-sm text-gray-500 p-2">
      已选择 {selectedIndicators.length} / {maxSelections} 个指标
    </div>
  )

  return (
    <div className="space-y-4">
      <Card title="技术指标选择" size="small">
        <Row gutter={[16, 16]} className="mb-4">
          <Col xs={24} sm={12}>
            <Search
              placeholder="搜索技术指标..."
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col xs={24} sm={12}>
            <Select
              style={{ width: '100%' }}
              placeholder="选择指标类别"
              value={selectedCategory}
              onChange={setSelectedCategory}
            >
              <Option value="all">全部类别</Option>
              {Object.entries(indicatorCategories).map(([key, category]) => (
                <Option key={key} value={key}>
                  {category.name} ({category.indicators.length})
                </Option>
              ))}
            </Select>
          </Col>
        </Row>

        <div className="mb-2">
          <Space>
            <InfoCircleOutlined style={{ color: '#1890ff' }} />
            <span className="text-sm text-gray-600">
              选择用于策略的技术指标（最多 {maxSelections} 个）
            </span>
          </Space>
        </div>

        <Transfer
          dataSource={transferData}
          titles={['可选指标', '已选指标']}
          targetKeys={selectedKeys}
          onChange={handleTransferChange}
          render={renderItem}
          oneWay
          style={{ marginBottom: 16 }}
          listStyle={{
            width: 300,
            height: 400,
          }}
          disabled={disabled}
          footer={transferFooter}
          showSearch={false}
        />
      </Card>

      {/* Quick Selection */}
      <Card title="快速选择" size="small">
        <Row gutter={[8, 8]}>
          <Col span={8}>
            <Button
              block
              size="small"
              onClick={() => {
                const commonIndicators = ['sma', 'ema', 'rsi', 'macd', 'bbands', 'atr', 'obv']
                onChange(commonIndicators.slice(0, maxSelections))
              }}
            >
              常用指标
            </Button>
          </Col>
          <Col span={8}>
            <Button
              block
              size="small"
              onClick={() => {
                const trendIndicators = allIndicators
                  .filter(i => i.categoryKey === 'trend')
                  .slice(0, Math.min(3, maxSelections))
                  .map(i => i.id)
                onChange(trendIndicators)
              }}
            >
              趋势跟踪
            </Button>
          </Col>
          <Col span={8}>
            <Button
              block
              size="small"
              onClick={() => {
                const meanReversionIndicators = ['sma', 'rsi', 'bbands', 'stoch']
                onChange(meanReversionIndicators)
              }}
            >
              均值回归
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Selected Indicators Preview */}
      {selectedIndicators.length > 0 && (
        <Card title="已选择的指标" size="small">
          <div className="space-y-2">
            {selectedIndicators.map(id => {
              const indicator = allIndicators.find(i => i.id === id)
              if (!indicator) return null
              return (
                <div key={id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div>
                    <div className="font-medium text-sm">{indicator.name}</div>
                    <div className="text-xs text-gray-500">{indicator.description}</div>
                  </div>
                  <Tag size="small" color="blue">{indicator.category}</Tag>
                </div>
              )
            })}
          </div>
        </Card>
      )}
    </div>
  )
}

export default IndicatorSelector