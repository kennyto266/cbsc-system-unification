import React, { useState, useMemo, useCallback } from 'react'
import {
  Card,
  Button,
  InputNumber,
  Select,
  Space,
  Typography,
  Row,
  Col,
  Statistic,
  Alert,
  Divider,
  Tooltip,
  Badge,
} from 'antd'
import {
  ShoppingCartOutlined,
  ShoppingOutlined,
  SwapOutlined,
  DollarOutlined,
  PercentageOutlined,
  SettingOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { motion, AnimatePresence } from 'framer-motion'
import { chartUtils } from '../../../utils/charts'
import { useRealTimeData } from '../hooks/useRealTimeData'

const { Text, Title } = Typography
const { Option } = Select

export interface OrderType {
  id: string
  name: string
  description?: string
  icon?: React.ReactNode
}

export interface TradingPair {
  symbol: string
  baseAsset: string
  quoteAsset: string
  price: number
  change24h: number
  volume24h: number
  minQuantity: number
  maxQuantity: number
  pricePrecision: number
  quantityPrecision: number
}

export interface OrderBookEntry {
  price: number
  quantity: number
  total: number
}

export interface TradingPanelProps {
  pair: TradingPair
  orderTypes: OrderType[]
  balances?: {
    base: number
    quote: number
  }
  orderBook?: {
    bids: OrderBookEntry[]
    asks: OrderBookEntry[]
  }
  currentPrice?: number
  theme?: 'light' | 'dark'
  compact?: boolean
  showAdvanced?: boolean
  onPlaceOrder?: (
    type: 'buy' | 'sell',
    orderType: string,
    quantity: number,
    price?: number
  ) => Promise<void>
  onPairChange?: (symbol: string) => void
  availablePairs?: TradingPair[]
  realTime?: boolean
  feeRate?: number
  className?: string
}

const TradingPanel: React.FC<TradingPanelProps> = ({
  pair,
  orderTypes,
  balances = { base: 0, quote: 0 },
  orderBook,
  currentPrice,
  theme = 'light',
  compact = false,
  showAdvanced = false,
  onPlaceOrder,
  onPairChange,
  availablePairs = [],
  realTime = false,
  feeRate = 0.001,
  className,
}) => {
  const [orderSide, setOrderSide] = useState<'buy' | 'sell'>('buy')
  const [orderType, setOrderType] = useState<string>('market')
  const [quantity, setQuantity] = useState<number | undefined>()
  const [price, setPrice] = useState<number | undefined>(currentPrice)
  const [total, setTotal] = useState<number | undefined>(0)
  const [loading, setLoading] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  // Real-time price subscription
  const { data: realTimePrice, isConnected } = useRealTimeData(
    realTime ? `price-${pair.symbol}` : null,
    1000
  )

  // Use real-time price if available
  const displayPrice = realTimePrice?.price || currentPrice || pair.price

  // Calculate total when quantity or price changes
  useMemo(() => {
    if (quantity && (orderType === 'market' ? displayPrice : price)) {
      const orderPrice = orderType === 'market' ? displayPrice : (price || 0)
      setTotal(quantity * orderPrice)
    } else {
      setTotal(0)
    }
  }, [quantity, price, orderType, displayPrice])

  // Calculate fee
  const fee = useMemo(() => {
    return total ? total * feeRate : 0
  }, [total, feeRate])

  // Get available balance for the order
  const availableBalance = useMemo(() => {
    if (orderSide === 'buy') {
      return balances.quote
    } else {
      return balances.base
    }
  }, [orderSide, balances])

  // Check if order is valid
  const isValidOrder = useMemo(() => {
    if (!quantity || quantity <= 0) return false
    if (quantity < pair.minQuantity) return false
    if (quantity > pair.maxQuantity) return false
    if (orderType !== 'market' && (!price || price <= 0)) return false
    if (total && total > availableBalance) return false
    return true
  }, [quantity, price, orderType, total, availableBalance, pair])

  // Handle place order
  const handlePlaceOrder = useCallback(async () => {
    if (!isValidOrder || !onPlaceOrder) return

    setLoading(true)
    try {
      await onPlaceOrder(
        orderSide,
        orderType,
        quantity!,
        orderType === 'market' ? undefined : price
      )
      // Reset form on success
      setQuantity(undefined)
      setPrice(currentPrice)
      setTotal(0)
    } catch (error) {
      console.error('Order failed:', error)
    } finally {
      setLoading(false)
    }
  }, [isValidOrder, onPlaceOrder, orderSide, orderType, quantity, price, currentPrice])

  // Quick quantity percentages
  const quantityPercentages = [25, 50, 75, 100]

  // Calculate best bid/ask from order book
  const bestBid = orderBook?.bids?.[0]?.price
  const bestAsk = orderBook?.asks?.[0]?.price
  const spread = bestBid && bestAsk ? bestAsk - bestBid : 0
  const spreadPercent = bestBid && bestAsk ? (spread / bestBid) * 100 : 0

  const orderSideColor = orderSide === 'buy' ? '#52c41a' : '#f5222d'

  return (
    <Card
      className={`trading-panel ${compact ? 'compact' : ''} ${className || ''}`}
      title={
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span>{pair.symbol}</span>
            {realTime && (
              <Badge
                status={isConnected ? 'success' : 'error'}
                text={isConnected ? 'Live' : 'Offline'}
              />
            )}
          </div>
          <div className="flex items-center space-x-4">
            <Statistic
              value={displayPrice}
              precision={pair.pricePrecision}
              prefix={pair.quoteAsset}
              valueStyle={{
                fontSize: '18px',
                fontWeight: 'bold',
                color: pair.change24h >= 0 ? '#52c41a' : '#f5222d',
              }}
            />
            <Button
              type="text"
              size="small"
              icon={<SettingOutlined />}
              onClick={() => setShowSettings(!showSettings)}
            />
          </div>
        </div>
      }
      size={compact ? 'small' : 'default'}
    >
      <AnimatePresence mode="wait">
        {!showSettings ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {/* Order Side Selector */}
            <div className="mb-4">
              <Button.Group size="large" style={{ width: '100%' }}>
                <Button
                  type={orderSide === 'buy' ? 'primary' : 'default'}
                  style={{
                    width: '50%',
                    backgroundColor: orderSide === 'buy' ? orderSideColor : undefined,
                    borderColor: orderSideColor,
                  }}
                  icon={<ShoppingCartOutlined />}
                  onClick={() => setOrderSide('buy')}
                >
                  Buy {pair.baseAsset}
                </Button>
                <Button
                  type={orderSide === 'sell' ? 'primary' : 'default'}
                  style={{
                    width: '50%',
                    backgroundColor: orderSide === 'sell' ? orderSideColor : undefined,
                    borderColor: orderSideColor,
                  }}
                  icon={<ShoppingOutlined />}
                  onClick={() => setOrderSide('sell')}
                >
                  Sell {pair.baseAsset}
                </Button>
              </Button.Group>
            </div>

            {/* Order Type */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <Text strong>Order Type</Text>
                <Tooltip title="Market orders execute immediately at current price">
                  <InfoCircleOutlined style={{ opacity: 0.5 }} />
                </Tooltip>
              </div>
              <Select
                value={orderType}
                onChange={setOrderType}
                style={{ width: '100%' }}
                size={compact ? 'small' : 'middle'}
              >
                {orderTypes.map(type => (
                  <Option key={type.id} value={type.id}>
                    <div className="flex items-center space-x-2">
                      {type.icon}
                      <div>
                        <div>{type.name}</div>
                        {type.description && (
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            {type.description}
                          </Text>
                        )}
                      </div>
                    </div>
                  </Option>
                ))}
              </Select>
            </div>

            {/* Price Input (for limit orders) */}
            {orderType !== 'market' && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <Text strong>Price</Text>
                  <Space>
                    {bestAsk && orderSide === 'buy' && (
                      <Button
                        type="link"
                        size="small"
                        onClick={() => setPrice(bestAsk)}
                      >
                        Best Ask: {chartUtils.formatNumber(bestAsk)}
                      </Button>
                    )}
                    {bestBid && orderSide === 'sell' && (
                      <Button
                        type="link"
                        size="small"
                        onClick={() => setPrice(bestBid)}
                      >
                        Best Bid: {chartUtils.formatNumber(bestBid)}
                      </Button>
                    )}
                  </Space>
                </div>
                <InputNumber
                  value={price}
                  onChange={setPrice}
                  style={{ width: '100%' }}
                  precision={pair.pricePrecision}
                  min={0}
                  size={compact ? 'small' : 'middle'}
                  prefix={<DollarOutlined />}
                />
              </div>
            )}

            {/* Quantity Input */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <Text strong>Quantity</Text>
                <Text type="secondary">
                  Available: {chartUtils.formatNumber(availableBalance, 4)}{' '}
                  {orderSide === 'buy' ? pair.quoteAsset : pair.baseAsset}
                </Text>
              </div>
              <InputNumber
                value={quantity}
                onChange={setQuantity}
                style={{ width: '100%' }}
                precision={pair.quantityPrecision}
                min={pair.minQuantity}
                max={pair.maxQuantity}
                size={compact ? 'small' : 'middle'}
              />
              {/* Quick Percentage Buttons */}
              <div className="flex space-x-2 mt-2">
                {quantityPercentages.map(percent => (
                  <Button
                    key={percent}
                    type="link"
                    size="small"
                    onClick={() => {
                      const maxQuantity = orderSide === 'buy'
                        ? availableBalance / (orderType === 'market' ? displayPrice : (price || 1))
                        : availableBalance
                      setQuantity(maxQuantity * (percent / 100))
                    }}
                  >
                    {percent}%
                  </Button>
                ))}
              </div>
            </div>

            {/* Total */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <Text strong>Total</Text>
                <Text type="secondary">
                  {total && chartUtils.formatCurrency(total, pair.quoteAsset)}
                </Text>
              </div>
              {fee > 0 && (
                <div className="flex items-center justify-between">
                  <Text type="secondary">
                    Fee ({(feeRate * 100).toFixed(2)}%)
                  </Text>
                  <Text type="secondary">
                    {chartUtils.formatCurrency(fee, pair.quoteAsset)}
                  </Text>
                </div>
              )}
            </div>

            {/* Order Button */}
            <Button
              type="primary"
              size="large"
              loading={loading}
              disabled={!isValidOrder}
              onClick={handlePlaceOrder}
              style={{
                width: '100%',
                backgroundColor: orderSideColor,
                borderColor: orderSideColor,
                height: '48px',
                fontSize: '16px',
                fontWeight: 'bold',
              }}
              icon={orderSide === 'buy' ? <ShoppingCartOutlined /> : <ShoppingOutlined />}
            >
              {orderSide === 'buy' ? 'Buy' : 'Sell'} {pair.baseAsset}
            </Button>

            {/* Market Info */}
            {showAdvanced && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="24h Volume"
                      value={pair.volume24h}
                      precision={0}
                      formatter={(value) => chartUtils.formatNumber(value as number)}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="Spread"
                      value={spreadPercent}
                      precision={2}
                      suffix="%"
                      formatter={(value) => chartUtils.formatNumber(value as number)}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="24h Change"
                      value={pair.change24h}
                      precision={2}
                      suffix="%"
                      valueStyle={{
                        color: pair.change24h >= 0 ? '#52c41a' : '#f5222d',
                      }}
                    />
                  </Col>
                </Row>
              </div>
            )}

            {/* Warning for insufficient balance */}
            {total > availableBalance && (
              <Alert
                message="Insufficient Balance"
                description={`You need ${chartUtils.formatCurrency(total - availableBalance, pair.quoteAsset)} more to complete this order`}
                type="warning"
                showIcon
                className="mt-4"
              />
            )}
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {/* Trading Pair Selector */}
            <div className="mb-4">
              <Text strong className="mb-2 block">Select Trading Pair</Text>
              <Select
                value={pair.symbol}
                onChange={onPairChange}
                style={{ width: '100%' }}
                showSearch
                filterOption={(input, option) =>
                  option?.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                }
              >
                {availablePairs.map(p => (
                  <Option key={p.symbol} value={p.symbol}>
                    {p.symbol}
                  </Option>
                ))}
              </Select>
            </div>

            {/* Fee Settings */}
            <div className="mb-4">
              <Text strong className="mb-2 block">Fee Rate</Text>
              <InputNumber
                value={feeRate * 100}
                onChange={(value) => {
                  // Update fee rate (would be passed as prop)
                }}
                style={{ width: '100%' }}
                min={0}
                max={1}
                step={0.01}
                precision={2}
                suffix="%"
              />
            </div>

            <Button
              type="primary"
              onClick={() => setShowSettings(false)}
              style={{ width: '100%' }}
            >
              Done
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  )
}

export default TradingPanel