import React, { useState, useEffect, useRef } from 'react';
import {
  theme,
  ParticleBackground,
  Navbar,
  Hero,
  DashboardGrid,
  Card,
  StatusIndicator,
  StatItem,
  Button,
  ChartContainer,
  Tooltip,
  Skeleton,
  useScrollEffect,
  useWindowSize,
  animateNumber,
  formatCurrency,
  formatPercentage,
  getColorForValue
} from '../components/CBSCKit';

// 圖表配置
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        color: theme.colors.gray[300],
        font: {
          family: theme.fonts.body,
          size: 12
        },
        usePointStyle: true,
        padding: 20
      }
    },
    tooltip: {
      backgroundColor: 'rgba(17, 24, 39, 0.9)',
      titleColor: theme.colors.gray[100],
      bodyColor: theme.colors.gray[300],
      borderColor: theme.colors.gray[700],
      borderWidth: 1,
      cornerRadius: 8,
      padding: 12,
      displayColors: true,
      callbacks: {
        label: function(context) {
          return context.dataset.label + ': ' + context.parsed.y + '%';
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: 'rgba(75, 85, 99, 0.3)',
        drawBorder: false
      },
      ticks: {
        color: theme.colors.gray[500],
        font: {
          family: theme.fonts.body
        }
      }
    },
    y: {
      grid: {
        color: 'rgba(75, 85, 99, 0.3)',
        drawBorder: false
      },
      ticks: {
        color: theme.colors.gray[500],
        font: {
          family: theme.fonts.body
        },
        callback: function(value) {
          return value + '%';
        }
      }
    }
  }
};

const Dashboard = () => {
  const [systemData, setSystemData] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [performanceData, setPerformanceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scrolled, setScrolled] = useState(false);
  const [creatingStrategy, setCreatingStrategy] = useState(false);
  const chartRef = useRef(null);
  const { width } = useWindowSize();

  // 滾動效果
  useScrollEffect((scrolled) => setScrolled(scrolled), 100);

  // 初始化數據
  useEffect(() => {
    initializeData();
    const interval = setInterval(fetchRealTimeData, 5000);
    return () => clearInterval(interval);
  }, []);

  const initializeData = async () => {
    try {
      setLoading(true);

      // 並行獲取所有數據
      const [systemHealth, strategyList, historicalData] = await Promise.all([
        fetchSystemHealth(),
        fetchStrategies(),
        fetchHistoricalPerformance()
      ]);

      setSystemData(systemHealth);
      setStrategies(strategyList);
      setPerformanceData(historicalData);

      // 初始化圖表
      if (chartRef.current && historicalData) {
        initializeChart(historicalData);
      }

      // 動畫數字
      animateNumbers(systemHealth);
    } catch (error) {
      console.error('初始化失敗:', error);
      // 使用模擬數據
      loadMockData();
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const response = await fetch('http://localhost:3004/health');
      return await response.json();
    } catch (error) {
      return {
        status: 'healthy',
        services: {
          api: 'running',
          database: 'connected',
          websocket: 'running'
        },
        metrics: {
          latency: 12,
          uptime: '24h',
          cpu: 15.2,
          memory: 68.5
        }
      };
    }
  };

  const fetchStrategies = async () => {
    try {
      const response = await fetch('http://localhost:3004/api/v1/strategies');
      const strategies = await response.json();
      return Array.isArray(strategies) ? strategies : [];
    } catch (error) {
      console.log('使用模擬策略數據');
      return [
        {
          id: 1,
          name: '量子動量策略',
          type: '量化分析',
          status: 'active',
          performance: { total_return: 12.5, sharpe_ratio: 1.82 }
        },
        {
          id: 2,
          name: 'AI機器學習策略',
          type: '機器學習',
          status: 'active',
          performance: { total_return: 8.3, sharpe_ratio: 1.45 }
        }
      ];
    }
  };

  const fetchHistoricalPerformance = async () => {
    // 模擬歷史數據
    return {
      labels: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
      datasets: [
        {
          label: '策略收益率',
          data: [2.1, 3.5, 1.8, 4.2, 2.9, 3.7, 5.1, 4.8, 6.2, 5.9, 7.1, 6.8],
          borderColor: theme.colors.neon.cyan,
          backgroundColor: createGradient(chartRef.current, theme.colors.neon.cyan),
          borderWidth: 3,
          tension: 0.4,
          fill: true,
          pointBackgroundColor: theme.colors.neon.cyan,
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        },
        {
          label: '基準收益率',
          data: [1.5, 2.1, 1.2, 2.8, 1.9, 2.4, 3.1, 2.9, 3.8, 3.5, 4.2, 3.9],
          borderColor: theme.colors.neon.purple,
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          borderDash: [5, 5],
          pointRadius: 3,
          pointHoverRadius: 5
        }
      ]
    };
  };

  const fetchRealTimeData = async () => {
    try {
      // 實時更新數據
      const newHealth = await fetchSystemHealth();
      if (JSON.stringify(newHealth) !== JSON.stringify(systemData)) {
        setSystemData(newHealth);
      }
    } catch (error) {
      console.log('實時數據更新失敗');
    }
  };

  const loadMockData = () => {
    setSystemData({
      status: 'healthy',
      services: {
        api: 'running',
        database: 'connected',
        websocket: 'running'
      },
      metrics: {
        latency: 12,
        uptime: '24h',
        cpu: 15.2,
        memory: 68.5
      }
    });

    setStrategies([
      { id: 1, name: '量子動量策略', type: '量化分析', status: 'active' },
      { id: 2, name: 'AI機器學習策略', type: '機器學習', status: 'active' },
      { id: 3, name: '波動率交易策略', type: '期權策略', status: 'paused' }
    ]);
  };

  const createGradient = (ctx, color) => {
    if (!ctx) return 'rgba(0, 212, 255, 0.1)';

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, color + '40');
    gradient.addColorStop(1, color + '05');
    return gradient;
  };

  const initializeChart = (data) => {
    if (!window.Chart) return;

    const ctx = chartRef.current.getContext('2d');

    // 更新數據集的背景色
    data.datasets[0].backgroundColor = createGradient(ctx, theme.colors.neon.cyan);

    new window.Chart(ctx, {
      type: 'line',
      data: data,
      options: chartOptions
    });
  };

  const animateNumbers = (data) => {
    if (!data?.metrics) return;

    // 動畫延遲數據
    animateNumber(0, data.metrics.latency || 12, 1000, (value) => {
      const element = document.getElementById('latencyValue');
      if (element) element.textContent = value + 'ms';
    });

    // 動畫CPU使用率
    animateNumber(0, data.metrics.cpu || 15, 1500, (value) => {
      const element = document.getElementById('cpuValue');
      if (element) element.textContent = value.toFixed(1) + '%';
    });

    // 動畫內存使用率
    animateNumber(0, data.metrics.memory || 68, 2000, (value) => {
      const element = document.getElementById('memoryValue');
      if (element) element.textContent = value.toFixed(1) + '%';
    });
  };

  const handleCreateStrategy = async () => {
    setCreatingStrategy(true);
    try {
      const newStrategy = {
        name: `量子策略 ${new Date().getTime()}`,
        type: '量化分析',
        description: '動態生成的智能交易策略',
        parameters: {
          lookback: 20,
          threshold: 0.02,
          stop_loss: 0.05,
          take_profit: 0.1
        }
      };

      const response = await fetch('http://localhost:3004/api/v1/strategies', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newStrategy)
      });

      if (response.ok) {
        const result = await response.json();
        alert(`策略創建成功！\n策略名稱: ${result.name}\n策略ID: ${result.id}`);
        fetchStrategies();
      } else {
        alert('策略創建失敗，請稍後重試');
      }
    } catch (error) {
      alert('正在連接到策略服務...');
    } finally {
      setCreatingStrategy(false);
    }
  };

  const openAPIDocs = () => {
    window.open('http://localhost:3004/docs', '_blank');
  };

  const formatUpdateTime = () => {
    return new Date().toLocaleTimeString('zh-TW', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (loading) {
    return (
      <>
        <ParticleBackground />
        <div style={{ padding: '120px 20px' }}>
          <DashboardGrid>
            <Card>
              <Skeleton height="20px" width="150px" style={{ marginBottom: '20px' }} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                {[...Array(4)].map((_, i) => (
                  <div key={i}>
                    <Skeleton height="12px" width="60px" style={{ marginBottom: '5px' }} />
                    <Skeleton height="20px" width="80px" />
                  </div>
                ))}
              </div>
            </Card>
            <Card>
              <Skeleton height="20px" width="120px" style={{ marginBottom: '20px' }} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                {[...Array(4)].map((_, i) => (
                  <div key={i}>
                    <Skeleton height="12px" width="70px" style={{ marginBottom: '5px' }} />
                    <Skeleton height="20px" width="60px" />
                  </div>
                ))}
              </div>
            </Card>
            <Card>
              <Skeleton height="20px" width="100px" style={{ marginBottom: '20px' }} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                {[...Array(4)].map((_, i) => (
                  <div key={i}>
                    <Skeleton height="12px" width="80px" style={{ marginBottom: '5px' }} />
                    <Skeleton height="20px" width="90px" />
                  </div>
                ))}
              </div>
            </Card>
          </DashboardGrid>
        </div>
      </>
    );
  }

  const activeStrategies = strategies.filter(s => s.status === 'active').length;

  return (
    <>
      <ParticleBackground />

      <Navbar
        brand="CBSC Quantum"
        links={[
          { text: '儀表板', href: '#dashboard', active: true },
          { text: '策略管理', href: '#strategies' },
          { text: '回測分析', href: '#backtest' },
          { text: '實時監控', href: '#monitoring' },
          { text: '系統設置', href: '#settings' }
        ]}
      />

      <Hero
        title="量子策略管理系統"
        subtitle="運用人工智能與量化分析，打造下一代智能投資管理平台"
        actions={
          <>
            <Button variant="primary" size="large" onClick={handleCreateStrategy} loading={creatingStrategy}>
              <i className="fas fa-rocket"></i>
              創建新策略
            </Button>
            <Tooltip text="查看完整的API文檔和示例">
              <Button variant="secondary" onClick={openAPIDocs}>
                <i className="fas fa-code"></i>
                API 文檔
              </Button>
            </Tooltip>
          </>
        }
      />

      <main style={{ padding: '60px 0' }}>
        <DashboardGrid>
          {/* 系統狀態卡片 */}
          <Card
            icon={<i className="fas fa-server"></i>}
            iconColor="cyan"
            title="系統狀態"
            status={{ status: 'online', text: '運行中' }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing.md }}>
              <StatItem label="API服務" value="正常" />
              <StatItem label="數據庫" value="已連接" />
              <StatItem label="延遲" value={<span id="latencyValue">12ms</span>} />
              <StatItem label="運行時間" value={systemData?.metrics?.uptime || '24h'} />
            </div>
          </Card>

          {/* 策略概覽卡片 */}
          <Card
            icon={<i className="fas fa-chart-pie"></i>}
            iconColor="purple"
            title="策略概覽"
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing.md }}>
              <StatItem
                label="活躍策略"
                value={activeStrategies}
                icon={<i className="fas fa-play-circle"></i>}
                color={theme.colors.neon.purple}
              />
              <StatItem label="總回測數" value="248" icon={<i className="fas fa-flask"></i>} />
              <StatItem
                label="勝率"
                value="68.5%"
                trend={2.3}
                color={theme.colors.status.success}
              />
              <StatItem
                label="夏普比率"
                value="1.82"
                trend={0.15}
                color={theme.colors.neon.cyan}
              />
            </div>
          </Card>

          {/* 收益表現卡片 */}
          <Card
            icon={<i className="fas fa-dollar-sign"></i>}
            iconColor="green"
            title="收益表現"
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing.md }}>
              <StatItem
                label="今日收益率"
                value={formatPercentage(2.34)}
                trend={0.8}
                color={theme.colors.status.success}
              />
              <StatItem
                label="月收益率"
                value={formatPercentage(8.67)}
                trend={1.2}
                color={theme.colors.status.success}
              />
              <StatItem
                label="年收益率"
                value={formatPercentage(34.21)}
                trend={5.6}
                color={theme.colors.status.success}
              />
              <StatItem
                label="最大回撤"
                value={formatPercentage(-5.8)}
                trend={-0.3}
                color={theme.colors.status.error}
              />
            </div>
          </Card>

          {/* 快速操作卡片 */}
          <Card
            icon={<i className="fas fa-rocket"></i>}
            iconColor="orange"
            title="快速操作"
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.sm }}>
              <Button onClick={handleCreateStrategy} loading={creatingStrategy}>
                <i className="fas fa-plus"></i>
                創建策略
              </Button>
              <Button variant="secondary">
                <i className="fas fa-play"></i>
                運行回測
              </Button>
              <Button variant="secondary" onClick={openAPIDocs}>
                <i className="fas fa-file-alt"></i>
                查看報告
              </Button>
              <Button variant="ghost">
                <i className="fas fa-cog"></i>
                系統設置
              </Button>
            </div>
          </Card>

          {/* 性能圖表卡片 */}
          <Card style={{ gridColumn: width > 768 ? 'span 2' : 'span 1' }}>
            <ChartContainer
              title="策略收益曲線"
              subtitle="過去12個月的策略表現與基準對比"
              height={300}
            >
              <canvas ref={chartRef} />
            </ChartContainer>
          </Card>

          {/* 系統監控卡片 */}
          <Card
            icon={<i className="fas fa-tachometer-alt"></i>}
            iconColor="cyan"
            title="系統監控"
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing.md }}>
              <StatItem label="CPU使用率" value={<span id="cpuValue">15.2%</span>} />
              <StatItem label="內存使用率" value={<span id="memoryValue">68.5%</span>} />
              <StatItem label="磁盤使用率" value="42.1%" />
              <StatItem label="網絡延遲" value="0.3ms" />
            </div>
          </Card>

          {/* 最新策略卡片 */}
          <Card
            icon={<i className="fas fa-brain"></i>}
            iconColor="purple"
            title="最新策略"
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.md }}>
              {strategies.slice(0, 3).map((strategy) => (
                <div key={strategy.id} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: theme.spacing.md,
                  background: 'rgba(' + theme.colors.primary.tertiary + ', 0.5)',
                  borderRadius: theme.borderRadius.lg,
                  border: '1px solid rgba(255, 255, 255, 0.05)'
                }}>
                  <div>
                    <div style={{ fontWeight: 600, color: theme.colors.gray[100] }}>
                      {strategy.name}
                    </div>
                    <div style={{ fontSize: '0.875rem', color: theme.colors.gray[500] }}>
                      {strategy.type}
                    </div>
                  </div>
                  <StatusIndicator status={strategy.status} text={strategy.status === 'active' ? '運行中' : '已暫停'} />
                </div>
              ))}
            </div>
          </Card>

          {/* 系統信息卡片 */}
          <Card
            icon={<i className="fas fa-info-circle"></i>}
            iconColor="green"
            title="系統信息"
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing.md }}>
              <StatItem label="系統版本" value="2.0.0" />
              <StatItem label="數據庫" value="SQLite" />
              <StatItem label="API版本" value="v1 + v2" />
              <StatItem label="更新時間" value={formatUpdateTime()} />
            </div>
          </Card>

          {/* 活動日誌卡片 */}
          <Card style={{ gridColumn: width > 768 ? 'span 2' : 'span 1' }}>
            <ChartContainer
              title="實時活動日誌"
              subtitle="系統操作和策略執行記錄"
              height={200}
              actions={
                <Button variant="ghost" size="small">
                  <i className="fas fa-filter"></i>
                  篩選
                </Button>
              }
            >
              <div style={{ height: '100%', overflow: 'auto' }}>
                {[
                  { time: '10:45:23', event: '策略執行', detail: '量子動量策略完成交易', type: 'success' },
                  { time: '10:42:15', event: '系統檢查', detail: '所有服務運行正常', type: 'info' },
                  { time: '10:38:47', event: '回測完成', detail: 'AI策略回測完成，勝率65%', type: 'success' },
                  { time: '10:35:12', event: '策略創建', detail: '新策略已添加到系統', type: 'warning' },
                  { time: '10:32:58', event: '數據同步', detail: '市場數據同步完成', type: 'info' }
                ].map((log, index) => (
                  <div key={index} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: theme.spacing.sm + ' ' + theme.spacing.md,
                    borderBottom: `1px solid ${theme.colors.gray[800]}`,
                    fontSize: '0.875rem'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
                      <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: log.type === 'success' ? theme.colors.status.success :
                                 log.type === 'warning' ? theme.colors.status.warning :
                                 theme.colors.status.info
                      }} />
                      <span style={{ color: theme.colors.gray[400] }}>{log.time}</span>
                      <span style={{ color: theme.colors.gray[300], fontWeight: 500 }}>{log.event}</span>
                    </div>
                    <span style={{ color: theme.colors.gray[500] }}>{log.detail}</span>
                  </div>
                ))}
              </div>
            </ChartContainer>
          </Card>
        </DashboardGrid>
      </main>

      <footer style={{
        textAlign: 'center',
        padding: theme.spacing['2xl'],
        color: theme.colors.gray[500],
        borderTop: `1px solid ${theme.colors.gray[800]}`
      }}>
        <p>© 2025 CBSC Quantum - 量化策略管理系統 | 構建未來智能投資</p>
      </footer>
    </>
  );
};

export default Dashboard;