/**
 * WebSocket Connection Status Indicator
 * 顯示實時連接狀態的組件
 */

import React from 'react'
import { useSelector } from 'react-redux'
import { RootState } from '../../store'

const WebSocketStatusIndicator: React.FC = () => {
  const webSocketStatus = useSelector((state: RootState) => state.ui.webSocketStatus)

  const getStatusColor = () => {
    if (webSocketStatus.connected) {
      return 'bg-green-500'
    } else if (webSocketStatus.reconnecting) {
      return 'bg-yellow-500 animate-pulse'
    } else {
      return 'bg-red-500'
    }
  }

  const getStatusText = () => {
    if (webSocketStatus.connected) {
      return '已連接'
    } else if (webSocketStatus.reconnecting) {
      return `重連中... (${webSocketStatus.reconnectAttempts})`
    } else {
      return webSocketStatus.lastError || '連接中斷'
    }
  }

  const getStatusIcon = () => {
    if (webSocketStatus.connected) {
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      )
    } else if (webSocketStatus.reconnecting) {
      return (
        <svg className="w-4 h-4 animate-spin" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
        </svg>
      )
    } else {
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      )
    }
  }

  return (
    <div className="flex items-center space-x-2 text-sm">
      <div className={`flex items-center space-x-1 px-2 py-1 rounded-full ${getStatusColor()} bg-opacity-10`}>
        <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
        <span className={`${getStatusColor().replace('bg-', 'text-')} font-medium`}>
          {getStatusText()}
        </span>
      </div>
      <div className="text-gray-500">
        {getStatusIcon()}
      </div>
    </div>
  )
}

export default WebSocketStatusIndicator