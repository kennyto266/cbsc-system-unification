import { Routes, Route, Navigate } from 'react-router-dom'
import Backtest from './Backtest'

export default function BacktestPages() {
  return (
    <Routes>
      <Route path="/" element={<Backtest />} />
      <Route path="*" element={<Navigate to="/backtest" replace />} />
    </Routes>
  )
}
