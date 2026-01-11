import React, { useState, useEffect } from 'react';
import {
  User,
  TrendingUp,
  Settings,
  Shield,
  Download,
  Bell,
  Activity,
  Clock,
  MapPin,
  Monitor,
  Star,
  Target,
  BarChart3,
  Calendar
} from 'lucide-react';

const PersonalDashboard = () => {
  const [userProfile, setUserProfile] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  const [quickActions, setQuickActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');

      if (!token) {
        setError('请先登录');
        return;
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // 并行加载所有数据
      const [
        profileResponse,
        statsResponse,
        activityResponse,
        actionsResponse
      ] = await Promise.all([
        fetch('/api/user/profile', { headers }),
        fetch('/api/user/statistics?period=30', { headers }),
        fetch('/api/user/recent-activity?limit=10', { headers }),
        fetch('/api/user/quick-actions', { headers })
      ]);

      if (!profileResponse.ok) throw new Error('获取用户资料失败');
      if (!statsResponse.ok) throw new Error('获取统计数据失败');
      if (!activityResponse.ok) throw new Error('获取活动记录失败');
      if (!actionsResponse.ok) throw new Error('获取快捷操作失败');

      const profile = await profileResponse.json();
      const stats = await statsResponse.json();
      const activityData = await activityResponse.json();
      const actionsData = await actionsResponse.json();

      setUserProfile(profile);
      setStatistics(stats);
      setRecentActivity(activityData.activities || []);
      setQuickActions(actionsData.actions || []);

    } catch (err) {
      setError(err.message || '加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;

    return date.toLocaleDateString('zh-CN');
  };

  const getActivityIcon = (type) => {
    const icons = {
      'login': <User className="w-4 h-4" />,
      'trade': <TrendingUp className="w-4 h-4" />,
      'strategy': <Target className="w-4 h-4" />,
      'settings': <Settings className="w-4 h-4" />,
      'export': <Download className="w-4 h-4" />
    };
    return icons[type] || <Activity className="w-4 h-4" />;
  };

  const getActivityColor = (type) => {
    const colors = {
      'login': 'text-blue-600 bg-blue-100',
      'trade': 'text-green-600 bg-green-100',
      'strategy': 'text-purple-600 bg-purple-100',
      'settings': 'text-gray-600 bg-gray-100',
      'export': 'text-orange-600 bg-orange-100'
    };
    return colors[type] || 'text-gray-600 bg-gray-100';
  };

  const getPerformanceColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-blue-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceGrade = (score) => {
    if (score >= 90) return '优秀';
    if (score >= 70) return '良好';
    if (score >= 50) return '一般';
    return '需改进';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载仪表板...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 mb-4">
            <Activity className="w-12 h-12 mx-auto" />
          </div>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={loadDashboardData}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部 */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">个人中心</h1>
              <p className="text-sm text-gray-600">管理您的账户和查看使用统计</p>
            </div>
            <div className="text-sm text-gray-500">
              {new Date().toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                weekday: 'long'
              })}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧栏 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 用户资料卡片 */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="text-center">
                <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gray-200 flex items-center justify-center">
                  {userProfile?.avatar_url ? (
                    <img
                      src={userProfile.avatar_url}
                      alt="用户头像"
                      className="w-24 h-24 rounded-full object-cover"
                    />
                  ) : (
                    <User className="w-12 h-12 text-gray-400" />
                  )}
                </div>

                <h2 className="text-xl font-semibold text-gray-900">
                  {userProfile?.user?.username || '用户'}
                </h2>

                <p className="text-sm text-gray-600 mb-4">
                  {userProfile?.user?.email || '未设置邮箱'}
                </p>

                {/* 统计数据 */}
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-indigo-600">
                      {statistics?.login_count || 0}
                    </div>
                    <div className="text-xs text-gray-500">登录次数</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {statistics?.active_days || 0}
                    </div>
                    <div className="text-xs text-gray-500">活跃天数</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">
                      {statistics?.strategy_count || 0}
                    </div>
                    <div className="text-xs text-gray-500">使用策略</div>
                  </div>
                </div>

                <button className="mt-4 w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm">
                  编辑资料
                </button>
              </div>
            </div>

            {/* 快捷操作 */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">快捷操作</h3>
              <div className="space-y-2">
                {quickActions.map((action) => (
                  <button
                    key={action.id}
                    className="w-full flex items-center p-3 text-left rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-colors"
                  >
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-${action.color}-100 mr-3`}>
                      {React.createElement(action.icon, { className: `w-5 h-5 text-${action.color}-600` })}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{action.title}</div>
                      <div className="text-xs text-gray-500">{action.description}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* 系统状态 */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">系统状态</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">API服务</span>
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">数据库</span>
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">缓存</span>
                  <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                </div>
              </div>
            </div>
          </div>

          {/* 右侧内容 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 使用统计 */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">使用统计</h3>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {statistics?.login_count || 0}
                  </div>
                  <div className="text-xs text-gray-500">总登录数</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {statistics?.trade_count || 0}
                  </div>
                  <div className="text-xs text-gray-500">交易执行</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {statistics?.strategy_count || 0}
                  </div>
                  <div className="text-xs text-gray-500">活跃策略</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getPerformanceColor(statistics?.performance_score || 0)}`}>
                    {Math.round(statistics?.performance_score || 0)}
                  </div>
                  <div className="text-xs text-gray-500">性能评分</div>
                </div>
              </div>

              {/* 性能评级 */}
              {statistics && (
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">性能评级</span>
                    <span className={`text-sm font-medium ${getPerformanceColor(statistics.performance_score)}`}>
                      {getPerformanceGrade(statistics.performance_score)}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">活跃频率</span>
                      <p className="font-medium">{statistics.login_frequency || '偶尔'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">日均登录</span>
                      <p className="font-medium">{statistics.avg_daily_logins || 0} 次</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 最近活动 */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">最近活动</h3>
                <button className="text-sm text-indigo-600 hover:text-indigo-500">
                  查看全部
                </button>
              </div>

              <div className="space-y-3">
                {recentActivity.length > 0 ? (
                  recentActivity.map((activity) => (
                    <div key={activity.id} className="flex items-start space-x-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getActivityColor(activity.type)}`}>
                        {getActivityIcon(activity.type)}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-gray-900">{activity.description}</p>
                        <p className="text-xs text-gray-500 flex items-center mt-1">
                          <Clock className="w-3 h-3 mr-1" />
                          {formatDate(activity.timestamp)}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>暂无活动记录</p>
                  </div>
                )}
              </div>
            </div>

            {/* 活动趋势 */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">活动趋势</h3>
              <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                <div className="text-center text-gray-500">
                  <BarChart3 className="w-12 h-12 mx-auto mb-2" />
                  <p>活动趋势图表</p>
                  <p className="text-xs mt-1">需要集成图表库来显示数据</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PersonalDashboard;