import { Routes, Route, Navigate } from 'react-router-dom'
import Portfolio from './Portfolio'

export default function PortfolioPages() {
  return (
    <Routes>
      <Route path="/" element={<Portfolio />} />
      <Route path="*" element={<Navigate to="/portfolio" replace />} />
    </Routes>
  )
}
