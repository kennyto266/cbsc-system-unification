import { useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import {
  Activity,
  Cpu,
  HardDrive,
  Database,
  Network,
  Server,
  Clock,
  Zap,
  Monitor,
} from 'lucide-react'
import { PageTemplate } from '../../components/layout/PageTemplate'

interface SystemMetric {
  label: string
  value: string
  status: 'healthy' | 'warning' | 'critical'
}

interface SystemStatus {
  cpu: SystemMetric
  memory: SystemMetric
  disk: SystemMetric
  network: SystemMetric
  services: Array<{
    name: string
    status: 'running' | 'stopped' | 'error'
    uptime: string
  }>
}

export default function Monitoring() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // Simulate WebSocket connection for real-time monitoring
    // In production, this would connect to /ws endpoint
    const mockData: SystemStatus = {
      cpu: { label: 'CPU 使用率', value: '23%', status: 'healthy' },
      memory: { label: '内存使用率', value: '67%', status: 'healthy' },
      disk: { label: '磁盤使用率', value: '45%', status: 'healthy' },
      network: { label: '網絡延遲', value: '12ms', status: 'healthy' },
      services: [
        { name: 'API 服務器', status: 'running', uptime: '5天 3小時' },
        { name: '數據庫', status: 'running', uptime: '5天 3小時' },
        { name: 'Redis 緩存', status: 'running', uptime: '5天 3小時' },
        { name: 'WebSocket 服務', status: 'running', uptime: '5天 3小時' },
      ],
    }
    setSystemStatus(mockData)
    setIsConnected(true)
  }, [])

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'running':
        return { text: '正常', colorClass: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' }
      case 'warning':
        return { text: '警告', colorClass: 'bg-amber-500/10 text-amber-500 border-amber-500/20' }
      case 'critical':
      case 'error':
        return { text: '錯誤', colorClass: 'bg-rose-500/10 text-rose-500 border-rose-500/20' }
      case 'stopped':
        return { text: '已停止', colorClass: 'bg-slate-500/10 text-slate-500 border-slate-500/20' }
      default:
        return { text: '未知', colorClass: 'bg-slate-500/10 text-slate-500 border-slate-500/20' }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'running':
        return 'text-emerald-400'
      case 'warning':
        return 'text-amber-400'
      case 'critical':
      case 'error':
        return 'text-rose-400'
      case 'stopped':
        return 'text-slate-400'
      default:
        return 'text-slate-400'
    }
  }

  return (
    <PageTemplate
      title="系統監控"
      description="實時監控系統狀態和性能指標"
      icon={Monitor}
      headerActions={
        <Badge className={isConnected ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 'bg-slate-500/10 text-slate-500 border-slate-500/20'}>
          <Activity className="h-3 w-3 mr-1" />
          {isConnected ? '已連接' : '未連接'}
        </Badge>
      }
    >
      {/* System Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300" style={{ animation: `fadeInUp 0.5s ease-out 0ms both` }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">CPU</span>
            <Cpu className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold font-['JetBrains_Mono']">{systemStatus?.cpu.value || '-'}</div>
          <p className="text-xs text-slate-500 mt-1">{systemStatus?.cpu.label}</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300" style={{ animation: `fadeInUp 0.5s ease-out 50ms both` }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">內存</span>
            <Database className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold font-['JetBrains_Mono']">{systemStatus?.memory.value || '-'}</div>
          <p className="text-xs text-slate-500 mt-1">{systemStatus?.memory.label}</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300" style={{ animation: `fadeInUp 0.5s ease-out 100ms both` }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">磁盤</span>
            <HardDrive className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold font-['JetBrains_Mono']">{systemStatus?.disk.value || '-'}</div>
          <p className="text-xs text-slate-500 mt-1">{systemStatus?.disk.label}</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300" style={{ animation: `fadeInUp 0.5s ease-out 150ms both` }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">網絡</span>
            <Network className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold font-['JetBrains_Mono']">{systemStatus?.network.value || '-'}</div>
          <p className="text-xs text-slate-500 mt-1">{systemStatus?.network.label}</p>
        </div>
      </div>

      {/* Services Status */}
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300 mb-6" style={{ animation: `fadeInUp 0.5s ease-out 200ms both` }}>
        <div className="flex items-center gap-3 mb-4">
          <Server className="h-5 w-5 text-cyan-400" />
          <h3 className="text-lg font-semibold text-slate-100">服務狀態</h3>
        </div>
        <p className="text-slate-400 text-sm mb-4">系統服務運行狀態</p>
        <div className="space-y-3">
          {systemStatus?.services.map((service, index) => {
            const config = getStatusConfig(service.status)
            return (
              <div
                key={service.name}
                className="flex items-center justify-between p-4 bg-slate-800/30 border border-slate-800/50 rounded-lg hover:bg-slate-800/50 transition-colors duration-200"
                style={{ animation: `fadeInUp 0.3s ease-out ${index * 50 + 250}ms both` }}
              >
                <div className="flex items-center gap-4">
                  <Zap className="h-5 w-5 text-slate-400" />
                  <div>
                    <p className="font-medium text-slate-100">{service.name}</p>
                    <p className="text-sm text-slate-400">運行時間: {service.uptime}</p>
                  </div>
                </div>
                <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${config.colorClass}`}>
                  {service.status === 'running' ? '運行中' : '已停止'}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Real-time Logs */}
      <div className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-6 backdrop-blur-sm hover:bg-slate-800/50 hover:border-slate-700/50 transition-all duration-300" style={{ animation: `fadeInUp 0.5s ease-out 350ms both` }}>
        <div className="flex items-center gap-3 mb-4">
          <Clock className="h-5 w-5 text-cyan-400" />
          <h3 className="text-lg font-semibold text-slate-100">系統日誌</h3>
        </div>
        <p className="text-slate-400 text-sm mb-4">最近的系統活動記錄</p>
        <div className="font-['JetBrains_Mono'] text-sm space-y-2">
          <div className="flex gap-3 p-2 bg-slate-800/30 rounded">
            <span className="text-slate-500">[2024-01-15 10:30:45]</span>
            <span className="text-emerald-400">[INFO]</span>
            <span className="text-slate-300">系統啟動完成</span>
          </div>
          <div className="flex gap-3 p-2 bg-slate-800/30 rounded">
            <span className="text-slate-500">[2024-01-15 10:30:46]</span>
            <span className="text-emerald-400">[INFO]</span>
            <span className="text-slate-300">API 服務器啟動成功</span>
          </div>
          <div className="flex gap-3 p-2 bg-slate-800/30 rounded">
            <span className="text-slate-500">[2024-01-15 10:30:47]</span>
            <span className="text-emerald-400">[INFO]</span>
            <span className="text-slate-300">WebSocket 服務連接正常</span>
          </div>
          <div className="flex gap-3 p-2 bg-slate-800/30 rounded">
            <span className="text-slate-500">[2024-01-15 10:30:50]</span>
            <span className="text-cyan-400">[DEBUG]</span>
            <span className="text-slate-300">處理請求: GET /api/health</span>
          </div>
        </div>
      </div>

      {/* Custom animations */}
      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </PageTemplate>
  )
}
