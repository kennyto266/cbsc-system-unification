/**
 * Real-time Strategy Performance Component
 * 顯示實時策略性能的組件
 */

import React, { useMemo } from 'react'
import { useSelector } from 'react-redux'
import { RootState } from '../../store'
import { StrategyUpdate } from '../../types'

const RealTimeStrategyPerformance: React.FC = () => {
  const realtimeStrategies = useSelector((state: RootState) => state.ui.realtimeStrategies)
  const webSocketStatus = useSelector((state: RootState) => state.ui.webSocketStatus)

  // 計算匯總統計
  const statistics = useMemo(() => {
    if (realtimeStrategies.length === 0) {
      return {
        totalStrategies: 0,
        avgReturn: 0,
        avgSharpe: 0,
        avgWinRate: 0,
        totalActive: 0
      }
    }

    const totalReturn = realtimeStrategies.reduce((sum, s) => sum + s.annual_return, 0)
    const totalSharpe = realtimeStrategies.reduce((sum, s) => sum + s.sharpe_ratio, 0)
    const totalWinRate = realtimeStrategies.reduce((sum, s) => sum + s.win_rate, 0)
    const activeStrategies = realtimeStrategies.filter(s => s.risk_level !== 'low').length

    return {
      totalStrategies: realtimeStrategies.length,
      avgReturn: totalReturn / realtimeStrategies.length,
      avgSharpe: totalSharpe / realtimeStrategies.length,
      avgWinRate: totalWinRate / realtimeStrategies.length,
      totalActive: activeStrategies
    }
  }, [realtimeStrategies])

  const getReturnColor = (value: number) => {
    if (value > 0.15) return 'text-green-600'
    if (value > 0.05) return 'text-green-500'
    if (value > 0) return 'text-green-400'
    if (value > -0.05) return 'text-red-400'
    return 'text-red-600'
  }

  const getSharpeColor = (value: number) => {
    if (value > 2) return 'text-green-600'
    if (value > 1) return 'text-green-500'
    if (value > 0.5) return 'text-yellow-500'
    return 'text-red-500'
  }

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('zh-TW', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">實時策略性能</h3>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${webSocketStatus.connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {statistics.totalStrategies} 策略
          </span>
        </div>
      </div>

      {/* 匯總統計 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-3">
          <div className="text-sm text-blue-600 font-medium">平均年化回報</div>
          <div className={`text-lg font-bold ${getReturnColor(statistics.avgReturn)}`}>
            {formatPercent(statistics.avgReturn)}
          </div>
        </div>
        <div className="bg-green-50 rounded-lg p-3">
          <div className="text-sm text-green-600 font-medium">平均夏普比率</div>
          <div className={`text-lg font-bold ${getSharpeColor(statistics.avgSharpe)}`}>
            {statistics.avgSharpe.toFixed(2)}
          </div>
        </div>
        <div className="bg-purple-50 rounded-lg p-3">
          <div className="text-sm text-purple-600 font-medium">平均勝率</div>
          <div className="text-lg font-bold text-purple-700">
            {formatPercent(statistics.avgWinRate)}
          </div>
        </div>
        <div className="bg-orange-50 rounded-lg p-3">
          <div className="text-sm text-orange-600 font-medium">活躍策略</div>
          <div className="text-lg font-bold text-orange-700">
            {statistics.totalActive}
          </div>
        </div>
      </div>

      {/* 策略列表 */}
      <div className="space-y-3 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300">
        {realtimeStrategies.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <div className="text-4xl mb-2">📊</div>
            <p>等待策略數據...</p>
            {!webSocketStatus.connected && (
              <p className="text-sm mt-2">請檢查WebSocket連接</p>
            )}
          </div>
        ) : (
          realtimeStrategies.map((strategy) => (
            <div
              key={strategy.id}
              className="border rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-semibold text-gray-800">{strategy.name}</h4>
                  <p className="text-sm text-gray-600">
                    {strategy.category.replace(/_/g, ' ')}
                  </p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(strategy.risk_level)}`}>
                  {strategy.risk_level.toUpperCase()}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <div className="text-gray-500 text-xs">年化回報</div>
                  <div className={`font-semibold ${getReturnColor(strategy.annual_return)}`}>
                    {formatPercent(strategy.annual_return)}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 text-xs">夏普比率</div>
                  <div className={`font-semibold ${getSharpeColor(strategy.sharpe_ratio)}`}>
                    {strategy.sharpe_ratio.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 text-xs">最大回撤</div>
                  <div className="font-semibold text-red-600">
                    {formatPercent(strategy.max_drawdown)}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500 text-xs">勝率</div>
                  <div className="font-semibold text-blue-600">
                    {formatPercent(strategy.win_rate)}
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-100">
                <div className="text-xs text-gray-500">
                  波動率: {formatPercent(strategy.volatility)}
                </div>
                <div className="text-xs text-gray-400">
                  更新: {formatTime(strategy.last_updated)}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default RealTimeStrategyPerformance