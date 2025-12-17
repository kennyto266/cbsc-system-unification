/**
 * Next.js Dashboard Page
 * CBSC量化交易系統主儀表板頁面
 */

import React from 'react'
import { GetServerSideProps } from 'next'
import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'
import { NextPageWithLayout } from '@/types'
import { MainLayout } from '@/components/layout'
import {
  Card,
  MetricCard,
  TradingCard,
  StrategyCard,
  Button,
  ActionButton,
} from '@/components/ui'
import { useAuth } from '@/hooks'
import { dashboardAPI } from '@/services'

// Dashboard組件
const DashboardPage: NextPageWithLayout = () => {
  const { user } = useAuth()

  // 獲取儀表板數據
  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardAPI.getDashboardData,
    refetchInterval: 30000, // 每30秒刷新
  })

  // 獲取策略列表
  const { data: strategies } = useQuery({
    queryKey: ['strategies'],
    queryFn: dashboardAPI.getStrategies,
    refetchInterval: 60000, // 每分鐘刷新
  })

  // 獲取市場數據
  const { data: marketData } = useQuery({
    queryKey: ['market-data'],
    queryFn: dashboardAPI.getMarketData,
    refetchInterval: 5000, // 每5秒刷新
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="p-6 max-w-md">
          <h2 className="text-xl font-bold mb-2">加載失敗</h2>
          <p className="text-gray-600 mb-4">
            無法加載儀表板數據，請檢查網絡連接。
          </p>
          <ActionButton.Create onClick={() => window.location.reload()}>
            重試
          </ActionButton.Create>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 頁面標題 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">儀表板</h1>
          <p className="text-gray-600">
            歡迎回來，{user?.name || '用戶'}！
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">刷新數據</Button>
          <ActionButton.Create>新建策略</ActionButton.Create>
        </div>
      </div>

      {/* 關鍵指標 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="總資產"
          value={dashboardData?.totalAssets || 'HK$0'}
          change={dashboardData?.totalAssetsChange || 0}
          changeType={dashboardData?.totalAssetsChange >= 0 ? 'increase' : 'decrease'}
        />
        <MetricCard
          title="今日盈虧"
          value={dashboardData?.todayPnL || 'HK$0'}
          change={dashboardData?.todayPnLChange || 0}
          changeType={dashboardData?.todayPnLChange >= 0 ? 'increase' : 'decrease'}
        />
        <MetricCard
          title="活躍策略"
          value={dashboardData?.activeStrategies || 0}
          change={dashboardData?.activeStrategiesChange || 0}
          changeType={dashboardData?.activeStrategiesChange >= 0 ? 'increase' : 'decrease'}
        />
        <MetricCard
          title="勝率"
          value={`${dashboardData?.winRate || 0}%`}
          change={dashboardData?.winRateChange || 0}
          changeType={dashboardData?.winRateChange >= 0 ? 'increase' : 'decrease'}
        />
      </div>

      {/* 主要內容區域 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 策略列表 */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>我的策略</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {strategies?.map((strategy) => (
                  <StrategyCard
                    key={strategy.id}
                    name={strategy.name}
                    status={strategy.status}
                    performance={strategy.performance}
                    lastRun={strategy.lastRun}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 市場數據 */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>市場快照</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {marketData?.map((market) => (
                  <TradingCard
                    key={market.symbol}
                    symbol={market.symbol}
                    price={market.price}
                    change={market.change}
                    changePercent={market.changePercent}
                    volume={market.volume}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 快速操作 */}
      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button className="w-full">創建策略</Button>
            <Button variant="outline" className="w-full">
              回測分析
            </Button>
            <Button variant="outline" className="w-full">
              風險管理
            </Button>
            <Button variant="outline" className="w-full">
              報告中心
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 頁面佈局
DashboardPage.getLayout = function getLayout(page: React.ReactNode) {
  return <MainLayout>{page}</MainLayout>
}

// 服務端渲染
export const getServerSideProps: GetServerSideProps = async ({ req }) => {
  const queryClient = new QueryClient()

  try {
    // 預加載儀表板數據
    await queryClient.prefetchQuery({
      queryKey: ['dashboard'],
      queryFn: dashboardAPI.getDashboardData,
    })

    // 預加載策略數據
    await queryClient.prefetchQuery({
      queryKey: ['strategies'],
      queryFn: dashboardAPI.getStrategies,
    })

    return {
      props: {
        dehydratedState: dehydrate(queryClient),
      },
    }
  } catch (error) {
    console.error('SSR error:', error)
    return {
      props: {
        dehydratedState: dehydrate(queryClient),
      },
    }
  }
}

export default DashboardPage