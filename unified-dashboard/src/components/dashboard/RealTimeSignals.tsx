/**
 * Real-time Trading Signals Component
 * 顯示實時交易信號的組件
 */

import React, { useEffect, useRef } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { RootState } from '../../store'
import { addNewSignal } from '../../store/slices/uiSlice'
import { TradingSignal } from '../../types'

const RealTimeSignals: React.FC = () => {
  const dispatch = useDispatch()
  const realtimeSignals = useSelector((state: RootState) => state.ui.realtimeSignals)
  const webSocketStatus = useSelector((state: RootState) => state.ui.webSocketStatus)
  const containerRef = useRef<HTMLDivElement>(null)

  // 自動滾動到最新信號
  useEffect(() => {
    if (containerRef.current && realtimeSignals.length > 0) {
      containerRef.current.scrollTop = 0
    }
  }, [realtimeSignals])

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'SELL':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'HOLD':
        return 'bg-gray-100 text-gray-800 border-gray-300'
      default:
        return 'bg-blue-100 text-blue-800 border-blue-300'
    }
  }

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'BUY':
        return '📈'
      case 'SELL':
        return '📉'
      case 'HOLD':
        return '⏸️'
      default:
        return '📊'
    }
  }

  const formatTime = (timestamp: Date) => {
    return new Date(timestamp).toLocaleTimeString('zh-TW', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  // 測試用：添加模擬信號
  const addTestSignal = () => {
    const testSignals: TradingSignal[] = [
      {
        id: `test_${Date.now()}`,
        category: 'core_cbsc_technical',
        signal: 'BUY',
        confidence: 0.85,
        strength: 0.9,
        timestamp: new Date()
      },
      {
        id: `test_${Date.now() + 1}`,
        category: 'multi_factor_model',
        signal: 'SELL',
        confidence: 0.72,
        strength: 0.6,
        timestamp: new Date()
      }
    ]

    const randomSignal = testSignals[Math.floor(Math.random() * testSignals.length)]
    dispatch(addNewSignal(randomSignal))
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4 h-96 flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">實時交易信號</h3>
        <div className="flex items-center space-x-2">
          {/* 連接狀態指示器 */}
          <div className={`w-2 h-2 rounded-full ${webSocketStatus.connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {webSocketStatus.connected ? '實時連接' : '連接中斷'}
          </span>
          {/* 測試按鈕 */}
          <button
            onClick={addTestSignal}
            className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            測試信號
          </button>
        </div>
      </div>

      {/* 信號列表 */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-gray-300"
      >
        {realtimeSignals.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <div className="text-4xl mb-2">📡</div>
            <p>等待信號數據...</p>
            {!webSocketStatus.connected && (
              <p className="text-sm mt-2">請檢查WebSocket連接</p>
            )}
          </div>
        ) : (
          realtimeSignals.map((signal) => (
            <div
              key={signal.id}
              className={`border rounded-lg p-3 transition-all duration-300 ${getSignalColor(signal.signal)}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{getSignalIcon(signal.signal)}</span>
                  <div>
                    <div className="font-semibold text-sm">
                      {signal.signal}
                    </div>
                    <div className="text-xs opacity-75">
                      {signal.category.replace(/_/g, ' ')}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-medium">
                    置信度:
                    <span className={`ml-1 ${getConfidenceColor(signal.confidence)}`}>
                      {(signal.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="text-xs opacity-75">
                    強度: {(signal.strength * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs opacity-60 mt-1">
                    {formatTime(signal.timestamp)}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 底部統計信息 */}
      {realtimeSignals.length > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-200">
          <div className="flex justify-between text-xs text-gray-600">
            <span>最新信號數量: {realtimeSignals.length}</span>
            <span>
              BUY: {realtimeSignals.filter(s => s.signal === 'BUY').length} |
              SELL: {realtimeSignals.filter(s => s.signal === 'SELL').length} |
              HOLD: {realtimeSignals.filter(s => s.signal === 'HOLD').length}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default RealTimeSignals