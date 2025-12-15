import React from 'react'
import { Outlet, Routes, Route, Navigate } from 'react-router-dom'
import StrategyList from './components/StrategyList'
import StrategyEditor from './components/StrategyEditor'
import PerformanceAnalysis from './components/PerformanceAnalysis'

// Strategies Page Component - 策略管理主页面
const StrategiesPage: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<StrategyList />} />
      <Route path="/list" element={<StrategyList />} />
      <Route path="/create" element={<StrategyEditor />} />
      <Route path="/:id/edit" element={<StrategyEditor />} />
      <Route path="/:id/analysis" element={<PerformanceAnalysis />} />
      <Route path="*" element={<Navigate to="/strategies" replace />} />
    </Routes>
  )
}

export default StrategiesPage