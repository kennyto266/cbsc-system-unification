import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus,
  Settings,
  TrendingUp,
  Grid3X3,
  List,
  Play,
  Pause,
  Square,
  Activity,
  DollarSign,
  Target,
  AlertCircle
} from 'lucide-react'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { Badge } from '../../components/ui/badge'
import { MetricCard } from '../../components/square-ui/MetricCard'
import { Grid } from '../../components/square-ui/Grid'
import { useStrategies } from '../../hooks/useStrategies'
import StrategyList from '../../components/strategy/StrategyList'
import StrategyForm from '../../components/strategy/StrategyForm'
import StrategyDetails from '../../components/strategy/StrategyDetails'
import { Strategy, StrategyStatus } from '../../types'
import { cn } from '../../lib/utils'

const StrategiesPageModern: React.FC = () => {
  const [activeTab, setActiveTab] = useState('list')
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create')
  const [viewMode, setViewMode] = useState<'table' | 'card'>('card')

  const {
    strategies,
    statistics,
    isLoading,
    createStrategy,
    updateStrategy,
    deleteStrategy,
    updateStatus,
  } = useStrategies()

  // Calculate statistics with trends
  const statsWithTrends = useMemo(() => ({
    total: {
      value: statistics.total,
      label: '总策略数',
      icon: Target,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      trend: '+12%',
      trendUp: true
    },
    active: {
      value: statistics.active,
      label: '运行中',
      icon: Play,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      trend: '+8%',
      trendUp: true
    },
    testing: {
      value: statistics.testing,
      label: '测试中',
      icon: Activity,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      trend: '+15%',
      trendUp: true
    },
    inactive: {
      value: statistics.inactive,
      label: '已暂停',
      icon: Pause,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
      trend: '-5%',
      trendUp: false
    }
  }), [statistics])

  // Handle strategy selection
  const handleStrategySelect = (strategy: Strategy) => {
    setSelectedStrategy(strategy)
    setActiveTab('details')
  }

  // Handle strategy edit
  const handleStrategyEdit = (strategy: Strategy) => {
    setSelectedStrategy(strategy)
    setFormMode('edit')
    setActiveTab('form')
  }

  // Handle strategy create
  const handleStrategyCreate = () => {
    setSelectedStrategy(null)
    setFormMode('create')
    setActiveTab('form')
  }

  // Handle form submission
  const handleFormSubmit = async (strategyData: Partial<Strategy>) => {
    try {
      if (formMode === 'create') {
        await createStrategy(strategyData)
      } else {
        await updateStrategy(selectedStrategy!.id, strategyData)
      }
      setActiveTab('list')
    } catch (error) {
      console.error('Failed to submit strategy:', error)
    }
  }

  // Handle strategy status change
  const handleStatusChange = async (strategyId: string, newStatus: StrategyStatus) => {
    try {
      await updateStatus(strategyId, newStatus)
    } catch (error) {
      console.error('Failed to update status:', error)
    }
  }

  // Handle strategy delete
  const handleStrategyDelete = async (strategyId: string) => {
    try {
      await deleteStrategy(strategyId)
      if (selectedStrategy?.id === strategyId) {
        setSelectedStrategy(null)
        setActiveTab('list')
      }
    } catch (error) {
      console.error('Failed to delete strategy:', error)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className="p-6 space-y-6"
    >
      {/* Header */}
      <div className="space-y-2">
        <motion.h1
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="text-4xl font-bold tracking-tight"
        >
          策略管理
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="text-muted-foreground text-lg"
        >
          管理和监控您的量化交易策略
        </motion.p>
      </div>

      {/* Statistics Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Grid cols={{ xs: 1, sm: 2, lg: 4 }} gap={4}>
          {Object.entries(statsWithTrends).map(([key, stat], index) => {
            const Icon = stat.icon
            return (
              <motion.div
                key={key}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 * index }}
              >
                <MetricCard
                  title={stat.label}
                  value={stat.value}
                  icon={<Icon className="h-5 w-5" />}
                  trend={stat.trend}
                  trendUp={stat.trendUp}
                  className={cn(
                    'transition-all duration-200 hover:shadow-lg',
                    'hover:scale-105 cursor-pointer'
                  )}
                  valueClassName={stat.color}
                  iconClassName={cn(stat.bgColor, stat.color)}
                />
              </motion.div>
            )
          })}
        </Grid>
      </motion.div>

      {/* Main Content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="shadow-lg">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl">策略中心</CardTitle>
              <div className="flex items-center space-x-2">
                {/* View Mode Toggle */}
                <div className="flex items-center space-x-1 rounded-lg bg-muted p-1">
                  <Button
                    variant={viewMode === 'card' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('card')}
                    className="h-8 w-8 p-0"
                  >
                    <Grid3X3 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'table' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('table')}
                    className="h-8 w-8 p-0"
                  >
                    <List className="h-4 w-4" />
                  </Button>
                </div>

                {/* Create Strategy Button */}
                <Button
                  onClick={handleStrategyCreate}
                  className="cbsc-primary"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  新建策略
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent className="p-0">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="m-0">
              <TabsList className="grid w-full grid-cols-3 bg-transparent p-0">
                <TabsTrigger
                  value="list"
                  className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary"
                >
                  <TrendingUp className="mr-2 h-4 w-4" />
                  策略列表
                  <Badge variant="secondary" className="ml-2">
                    {statistics.total}
                  </Badge>
                </TabsTrigger>
                <TabsTrigger
                  value="form"
                  className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary"
                >
                  <Settings className="mr-2 h-4 w-4" />
                  {formMode === 'create' ? '新建策略' : '编辑策略'}
                </TabsTrigger>
                {selectedStrategy && (
                  <TabsTrigger
                    value="details"
                    className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary"
                  >
                    <Activity className="mr-2 h-4 w-4" />
                    策略详情
                  </TabsTrigger>
                )}
              </TabsList>

              <AnimatePresence mode="wait">
                <TabsContent value="list" className="mt-6">
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.2 }}
                  >
                    <StrategyList
                      strategies={strategies}
                      onStrategySelect={handleStrategySelect}
                      onStrategyEdit={handleStrategyEdit}
                      onStrategyCreate={handleStrategyCreate}
                      viewMode={viewMode}
                      isLoading={isLoading}
                    />
                  </motion.div>
                </TabsContent>

                <TabsContent value="form" className="mt-6">
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.2 }}
                  >
                    <StrategyForm
                      strategy={selectedStrategy || undefined}
                      onSubmit={handleFormSubmit}
                      onCancel={() => setActiveTab('list')}
                      mode={formMode}
                      loading={false}
                    />
                  </motion.div>
                </TabsContent>

                {selectedStrategy && (
                  <TabsContent value="details" className="mt-6">
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.2 }}
                    >
                      <StrategyDetails
                        strategyId={selectedStrategy.id}
                        onEdit={handleStrategyEdit}
                        onStatusChange={handleStatusChange}
                      />
                    </motion.div>
                  </TabsContent>
                )}
              </AnimatePresence>
            </Tabs>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}

export default StrategiesPageModern