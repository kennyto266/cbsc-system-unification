import { Routes, Route, Navigate } from 'react-router-dom'
import Analytics from './Analytics'

export default function AnalyticsPages() {
  return (
    <Routes>
      <Route path="/" element={<Analytics />} />
      <Route path="*" element={<Navigate to="/analytics" replace />} />
    </Routes>
  )
}
