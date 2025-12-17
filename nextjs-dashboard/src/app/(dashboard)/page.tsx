import { DashboardPage } from '@/components/dashboard/dashboard-page'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: '策略管理',
  description: '實時監控您的量化交易策略表現和市場動態',
}

export default function Page() {
  return <DashboardPage />
}