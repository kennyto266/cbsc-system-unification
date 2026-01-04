import { Routes, Route, Navigate } from 'react-router-dom'
import Monitoring from './Monitoring'

export default function MonitoringPages() {
  return (
    <Routes>
      <Route path="/" element={<Monitoring />} />
      <Route path="*" element={<Navigate to="/monitoring" replace />} />
    </Routes>
  )
}
