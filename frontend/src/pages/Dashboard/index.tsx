import React, { useEffect, useState, useCallback, useMemo, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Zap,
  BarChart3,
  Database,
  Webhook,
  RefreshCw,
  Settings,
  FileText,
  Eye,
  LayoutDashboard,
  LucideIcon,
} from 'lucide-react';
import { getDashboardStats, getSystemStatus, DashboardStats, SystemStatus } from '../../services/dashboardService';
import { WebSocketService } from '../../services/websocketService';

// Memoized StatCard component for performance
const StatCard = memo(({
  icon: Icon,
  label,
  value,
  suffix = '',
  colorClass,
  index,
}: {
  icon: LucideIcon;
  label: string;
  value: number | string;
  suffix?: string;
  colorClass: string;
  index: number;
}) => (
  <div
    className="bg-slate-900/50 border border-slate-800 backdrop-blur-sm rounded-xl overflow-hidden group hover:border-slate-700 transition-all duration-300"
    style={{
      animation: `fadeIn 0.4s ease-out ${index * 0.1}s both`,
    }}
  >
    <div className="p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 font-['Outfit']">{label}</p>
          <p className={`text-3xl font-bold mt-2 font-['JetBrains_Mono'] ${colorClass}`}>
            {value}{suffix}
          </p>
        </div>
        <div className={`p-4 rounded-xl bg-gradient-to-br ${colorClass.replace('text-', 'from-').replace('-600', '-500/20')} ${colorClass.replace('text-', 'to-').replace('-600', '-600/20')}`}>
          <Icon className={`h-6 w-6 ${colorClass}`} />
        </div>
      </div>
    </div>
  </div>
));
StatCard.displayName = 'StatCard';

// Memoized ActionCard component
const ActionCard = memo(({
  icon: Icon,
  title,
  description,
  onClick,
  colorClass,
  index,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  onClick: () => void;
  colorClass: string;
  index: number;
}) => (
  <button
    onClick={onClick}
    className="group p-6 bg-slate-900/50 border border-slate-800 rounded-xl text-left hover:border-slate-700 hover:bg-slate-800/50 transition-all duration-300"
    style={{
      animation: `fadeIn 0.4s ease-out ${index * 0.1 + 0.3}s both`,
    }}
  >
    <div className={`p-3 rounded-lg w-fit mb-4 bg-gradient-to-br ${colorClass}`}>
      <Icon className={`h-6 w-6 text-white`} />
    </div>
    <div className="font-semibold text-white text-lg font-['Outfit'] group-hover:text-cyan-400 transition-colors">
      {title}
    </div>
    <div className="text-sm text-slate-400 mt-2 font-['Outfit']">{description}</div>
  </button>
));
ActionCard.displayName = 'ActionCard';

// Memoized StatusRow component
const StatusRow = memo(({
  icon: Icon,
  label,
  status,
  index,
}: {
  icon: LucideIcon;
  label: string;
  status: string;
  index: number;
}) => {
  const statusConfig = useMemo(() => {
    const map: Record<string, { text: string; colorClass: string }> = {
      running: { text: '运行中', colorClass: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' },
      connected: { text: '正常', colorClass: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' },
      connecting: { text: '连接中', colorClass: 'bg-amber-500/10 text-amber-500 border-amber-500/20' },
      latest: { text: '最新', colorClass: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' },
      stopped: { text: '已停止', colorClass: 'bg-rose-500/10 text-rose-500 border-rose-500/20' },
      error: { text: '错误', colorClass: 'bg-rose-500/10 text-rose-500 border-rose-500/20' },
      disconnected: { text: '断开', colorClass: 'bg-rose-500/10 text-rose-500 border-rose-500/20' },
      syncing: { text: '同步中', colorClass: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20' },
      outdated: { text: '过期', colorClass: 'bg-orange-500/10 text-orange-500 border-orange-500/20' },
    };
    return map[status] || { text: status, colorClass: 'bg-slate-500/10 text-slate-500 border-slate-500/20' };
  }, [status]);

  return (
    <div
      className="flex items-center justify-between py-4 px-4 rounded-lg hover:bg-slate-800/30 transition-colors duration-200"
      style={{
        animation: `fadeIn 0.3s ease-out ${index * 0.05 + 0.5}s both`,
      }}
    >
      <div className="flex items-center">
        <div className="p-2 rounded-lg bg-slate-800 mr-4">
          <Icon className="h-5 w-5 text-slate-400" />
        </div>
        <span className="text-slate-300 font-medium font-['Outfit']">{label}</span>
      </div>
      <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${statusConfig.colorClass} font-['JetBrains_Mono']`}>
        {statusConfig.text}
      </span>
    </div>
  );
});
StatusRow.displayName = 'StatusRow';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats>({
    totalStrategies: 0,
    activeStrategies: 0,
    totalReturn: 0,
    dailyReturn: 0,
    totalTrades: 0,
    winRate: 0,
  });
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    api: 'running',
    database: 'connected',
    websocket: 'connecting',
    dataSync: 'latest',
  });
  const [loading, setLoading] = useState(true);
  const [wsService, setWsService] = useState<WebSocketService | null>(null);

  // Memoized stats configuration
  const statsConfig = useMemo(() => [
    {
      icon: LayoutDashboard,
      label: '總策略數',
      value: stats.totalStrategies,
      colorClass: 'text-blue-400',
    },
    {
      icon: Zap,
      label: '活躍策略',
      value: stats.activeStrategies,
      colorClass: 'text-emerald-400',
    },
    {
      icon: TrendingUp,
      label: '總收益率',
      value: stats.totalReturn,
      suffix: '%',
      colorClass: 'text-cyan-400',
    },
    {
      icon: Activity,
      label: '今日收益',
      value: stats.dailyReturn,
      suffix: '%',
      colorClass: 'text-violet-400',
    },
  ], [stats]);

  // Memoized actions configuration
  const actionsConfig = useMemo(() => [
    {
      icon: FileText,
      title: '管理策略',
      description: '查看和管理所有交易策略',
      onClick: () => navigate('/strategies'),
      colorClass: 'from-blue-500 to-cyan-500',
    },
    {
      icon: BarChart3,
      title: '運行回測',
      description: '測試策略歷史表現',
      onClick: () => navigate('/backtest'),
      colorClass: 'from-violet-500 to-purple-500',
    },
    {
      icon: Eye,
      title: '實時監控',
      description: '監控策略實時運行狀態',
      onClick: () => navigate('/monitoring'),
      colorClass: 'from-emerald-500 to-teal-500',
    },
  ], [navigate]);

  // Memoized system status configuration
  const systemStatusConfig = useMemo(() => [
    { icon: Activity, label: 'API 服務', status: systemStatus.api },
    { icon: Database, label: '數據庫連接', status: systemStatus.database },
    { icon: Webhook, label: 'WebSocket 服務', status: systemStatus.websocket },
    { icon: RefreshCw, label: '數據同步', status: systemStatus.dataSync },
  ], [systemStatus]);

  // Fetch data with useCallback
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsData, statusData] = await Promise.all([
        getDashboardStats(),
        getSystemStatus(),
      ]);
      setStats(statsData);
      setSystemStatus(statusData);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Initialize WebSocket connection
    const websocket = new WebSocketService();
    setWsService(websocket);

    // Subscribe to WebSocket updates
    const unsubscribeConnect = websocket.on('connect', () => {
      console.log('WebSocket connected in Dashboard');
      setSystemStatus(prev => ({ ...prev, websocket: 'connected' }));
    });

    const unsubscribeDisconnect = websocket.on('disconnect', () => {
      console.log('WebSocket disconnected in Dashboard');
      setSystemStatus(prev => ({ ...prev, websocket: 'disconnected' }));
    });

    const unsubscribeMessage = websocket.on('message', (data: any) => {
      console.log('WebSocket message received:', data);

      if (data.type === 'dashboard_update') {
        if (data.data?.stats) {
          setStats(prev => ({ ...prev, ...data.data.stats }));
        }
        if (data.data?.systemStatus) {
          setSystemStatus(prev => ({ ...prev, ...data.data.systemStatus }));
        }
      }

      if (data.type === 'notification') {
        toast.info(data.data?.message || '新通知');
      }
    });

    fetchData();

    // Refresh data every 30 seconds
    const interval = setInterval(fetchData, 30000);

    // Cleanup
    return () => {
      clearInterval(interval);
      if (typeof unsubscribeConnect === 'function') unsubscribeConnect();
      if (typeof unsubscribeDisconnect === 'function') unsubscribeDisconnect();
      if (typeof unsubscribeMessage === 'function') unsubscribeMessage();
      if (websocket) websocket.disconnect();
    };
  }, [fetchData]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent"></div>
          <p className="mt-6 text-slate-400 font-['Outfit'] text-lg">載入中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 font-['Outfit']">
      {/* Custom animations */}
      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .fade-in {
          animation: fadeIn 0.4s ease-out;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }

        ::-webkit-scrollbar-track {
          background: rgba(15, 23, 42, 0.5);
        }

        ::-webkit-scrollbar-thumb {
          background: rgba(51, 65, 85, 0.8);
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: rgba(71, 85, 105, 0.9);
        }
      `}</style>

      {/* Header */}
      <div className="bg-slate-900/50 border-b border-slate-800 backdrop-blur-sm px-6 py-6 sticky top-0 z-10">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div>
            <h1 className="text-3xl font-bold text-white font-['Outfit']">
              CBSC 量化交易策略管理系統
            </h1>
            <p className="text-slate-400 mt-2 font-['Outfit']">策略管理與監控儀表板</p>
          </div>
          <button
            onClick={() => navigate('/strategies')}
            className="px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-lg transition-all duration-300 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30"
          >
            策略管理
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6 max-w-7xl mx-auto">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statsConfig.map((config, index) => (
            <StatCard key={config.label} {...config} index={index} />
          ))}
        </div>

        {/* Quick Actions */}
        <div className="bg-slate-900/50 border border-slate-800 backdrop-blur-sm rounded-xl p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center font-['Outfit']">
            <Zap className="mr-3 h-6 w-6 text-amber-400" />
            快捷操作
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {actionsConfig.map((config, index) => (
              <ActionCard key={config.title} {...config} index={index} />
            ))}
          </div>
        </div>

        {/* System Status */}
        <div className="bg-slate-900/50 border border-slate-800 backdrop-blur-sm rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center font-['Outfit']">
            <Settings className="mr-3 h-6 w-6 text-cyan-400" />
            系統狀態
          </h2>
          <div className="space-y-2">
            {systemStatusConfig.map((config, index) => (
              <StatusRow key={config.label} {...config} index={index} />
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-12 py-6 border-t border-slate-800">
        <div className="text-center text-slate-500 text-sm font-['JetBrains_Mono']">
          CBSC 量化交易策略管理系統 © {new Date().getFullYear()} | 最後更新: {new Date().toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  );
};

export default memo(Dashboard);
