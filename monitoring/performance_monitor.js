const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

class PerformanceMonitor {
  constructor(config) {
    this.config = config;
    this.metrics = {
      websocket: {
        connections: 0,
        messagesPerSecond: 0,
        latency: [],
        disconnections: 0
      },
      api: {
        requestsPerSecond: 0,
        responseTime: [],
        errorRate: 0,
        endpoints: {}
      },
      dashboard: {
        activeUsers: 0,
        chartRenderTime: [],
        dataUpdateTime: [],
        errors: []
      },
      system: {
        cpu: [],
        memory: [],
        network: []
      }
    };
    this.alerts = [];
    this.isRunning = false;
    this.intervalId = null;
  }

  // Start monitoring
  start() {
    if (this.isRunning) {
      console.log('⚠️ 性能監控已在運行中');
      return;
    }

    console.log('🔍 啟動性能監控...');
    this.isRunning = true;

    // Monitor WebSocket
    this.monitorWebSocket();

    // Monitor API endpoints
    this.monitorAPI();

    // Monitor dashboard performance
    this.monitorDashboard();

    // System metrics collection
    this.collectSystemMetrics();

    // Check alerts
    this.intervalId = setInterval(() => {
      this.checkAlerts();
      this.saveMetrics();
    }, 5000); // Every 5 seconds

    console.log('✅ 性能監控已啟動');
  }

  // Monitor WebSocket performance
  monitorWebSocket() {
    const ws = new WebSocket(this.config.endpoints.websocket);

    ws.on('open', () => {
      this.metrics.websocket.connections++;
      console.log('📡 WebSocket 連接已建立');
    });

    ws.on('message', (data) => {
      const timestamp = Date.now();
      const message = JSON.parse(data);

      // Calculate latency if message has timestamp
      if (message.timestamp) {
        const latency = timestamp - new Date(message.timestamp).getTime();
        this.metrics.websocket.latency.push(latency);
        this.metrics.websocket.latency = this.metrics.websocket.latency.slice(-100); // Keep last 100
      }

      // Count messages per second
      this.metrics.websocket.messagesPerSecond++;
    });

    ws.on('close', () => {
      this.metrics.websocket.connections--;
      this.metrics.websocket.disconnections++;
      console.log('📡 WebSocket 連接已斷開');
    });

    ws.on('error', (error) => {
      console.error('📡 WebSocket 錯誤:', error);
      this.metrics.dashboard.errors.push({
        type: 'websocket',
        message: error.message,
        timestamp: new Date().toISOString()
      });
    });

    // Reset messages per second counter every second
    setInterval(() => {
      this.metrics.websocket.messagesPerSecond = 0;
    }, 1000);
  }

  // Monitor API performance
  monitorAPI() {
    // Simulate API monitoring
    const endpoints = [
      '/api/indicators',
      '/api/market-data',
      '/api/strategies',
      '/api/performance'
    ];

    endpoints.forEach(endpoint => {
      this.monitorEndpoint(endpoint);
    });
  }

  // Monitor specific API endpoint
  async monitorEndpoint(endpoint) {
    const startTime = Date.now();

    try {
      const response = await fetch(this.config.endpoints.api_base + endpoint);
      const responseTime = Date.now() - startTime;

      // Track response time
      this.metrics.api.responseTime.push(responseTime);
      this.metrics.api.responseTime = this.metrics.api.responseTime.slice(-1000); // Keep last 1000

      // Track endpoint metrics
      if (!this.metrics.api.endpoints[endpoint]) {
        this.metrics.api.endpoints[endpoint] = {
          requests: 0,
          responseTime: [],
          errors: 0
        };
      }

      this.metrics.api.endpoints[endpoint].requests++;
      this.metrics.api.endpoints[endpoint].responseTime.push(responseTime);

      if (!response.ok) {
        this.metrics.api.endpoints[endpoint].errors++;
      }

      // Calculate requests per second
      this.metrics.api.requestsPerSecond++;
    } catch (error) {
      console.error(`❌ API 錯誤 ${endpoint}:`, error);
      this.metrics.dashboard.errors.push({
        type: 'api',
        endpoint,
        message: error.message,
        timestamp: new Date().toISOString()
      });
    }

    // Reset counter
    setTimeout(() => {
      this.metrics.api.requestsPerSecond = 0;
    }, 1000);
  }

  // Monitor dashboard performance
  monitorDashboard() {
    // This would typically be injected into the frontend
    // For now, we'll simulate the collection
    setInterval(() => {
      // Simulate chart render times
      const chartRenderTime = Math.random() * 100; // 0-100ms
      this.metrics.dashboard.chartRenderTime.push(chartRenderTime);
      this.metrics.dashboard.chartRenderTime = this.metrics.dashboard.chartRenderTime.slice(-100);

      // Simulate data update times
      const dataUpdateTime = Math.random() * 500; // 0-500ms
      this.metrics.dashboard.dataUpdateTime.push(dataUpdateTime);
      this.metrics.dashboard.dataUpdateTime = this.metrics.dashboard.dataUpdateTime.slice(-100);

      // Simulate active users
      this.metrics.dashboard.activeUsers = Math.floor(Math.random() * 50) + 10; // 10-60 users
    }, 2000);
  }

  // Collect system metrics
  collectSystemMetrics() {
    const os = require('os');

    setInterval(() => {
      // CPU usage
      const cpuUsage = os.loadavg()[0] * 100 / os.cpus().length;
      this.metrics.system.cpu.push(cpuUsage);
      this.metrics.system.cpu = this.metrics.system.cpu.slice(-100); // Keep last 100

      // Memory usage
      const totalMemory = os.totalmem();
      const freeMemory = os.freemem();
      const memoryUsage = ((totalMemory - freeMemory) / totalMemory) * 100;
      this.metrics.system.memory.push(memoryUsage);
      this.metrics.system.memory = this.metrics.system.memory.slice(-100);

      // Network metrics (simplified)
      this.metrics.system.network.push({
        timestamp: Date.now(),
        bytesIn: Math.random() * 1000000,
        bytesOut: Math.random() * 1000000
      });
      this.metrics.system.network = this.metrics.system.network.slice(-100);
    }, 5000);
  }

  // Check for alerts
  checkAlerts() {
    const thresholds = this.config.monitoring.alerts;

    // Check WebSocket latency
    if (this.metrics.websocket.latency.length > 0) {
      const avgLatency = this.metrics.websocket.latency.reduce((a, b) => a + b, 0) / this.metrics.websocket.latency.length;
      if (avgLatency > thresholds.response_time_threshold_ms) {
        this.addAlert('high_ws_latency', `WebSocket 延遲過高: ${avgLatency.toFixed(2)}ms`);
      }
    }

    // Check API response time
    if (this.metrics.api.responseTime.length > 0) {
      const avgResponseTime = this.metrics.api.responseTime.reduce((a, b) => a + b, 0) / this.metrics.api.responseTime.length;
      if (avgResponseTime > thresholds.response_time_threshold_ms) {
        this.addAlert('high_api_latency', `API 響應時間過高: ${avgResponseTime.toFixed(2)}ms`);
      }
    }

    // Check error rate
    const totalRequests = Object.values(this.metrics.api.endpoints).reduce((sum, ep) => sum + ep.requests, 0);
    const totalErrors = Object.values(this.metrics.api.endpoints).reduce((sum, ep) => sum + ep.errors, 0);
    if (totalRequests > 0) {
      const errorRate = (totalErrors / totalRequests) * 100;
      if (errorRate > thresholds.error_rate_threshold) {
        this.addAlert('high_error_rate', `錯誤率過高: ${errorRate.toFixed(2)}%`);
      }
    }

    // Check memory usage
    if (this.metrics.system.memory.length > 0) {
      const latestMemory = this.metrics.system.memory[this.metrics.system.memory.length - 1];
      if (latestMemory > 90) {
        this.addAlert('high_memory', `內存使用率過高: ${latestMemory.toFixed(2)}%`);
      }
    }

    // Check CPU usage
    if (this.metrics.system.cpu.length > 0) {
      const latestCPU = this.metrics.system.cpu[this.metrics.system.cpu.length - 1];
      if (latestCPU > thresholds.cpu_threshold_percent) {
        this.addAlert('high_cpu', `CPU 使用率過高: ${latestCPU.toFixed(2)}%`);
      }
    }
  }

  // Add alert
  addAlert(type, message) {
    // Check if alert already exists in the last 5 minutes
    const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
    const existingAlert = this.alerts.find(a => a.type === type && a.timestamp > fiveMinutesAgo);

    if (!existingAlert) {
      this.alerts.push({
        type,
        message,
        timestamp: Date.now(),
        resolved: false
      });

      console.log(`🚨 警報: ${message}`);
    }
  }

  // Save metrics to file
  saveMetrics() {
    const metricsDir = path.join(__dirname, '../test_results/metrics');
    if (!fs.existsSync(metricsDir)) {
      fs.mkdirSync(metricsDir, { recursive: true });
    }

    const metricsPath = path.join(metricsDir, `metrics_${Date.now()}.json`);
    const metricsData = {
      timestamp: new Date().toISOString(),
      metrics: this.metrics,
      alerts: this.alerts.filter(a => !a.resolved)
    };

    fs.writeFileSync(metricsPath, JSON.stringify(metricsData, null, 2));

    // Keep only last 10 metrics files
    const files = fs.readdirSync(metricsDir);
    if (files.length > 10) {
      files.sort();
      files.slice(0, files.length - 10).forEach(file => {
        fs.unlinkSync(path.join(metricsDir, file));
      });
    }
  }

  // Get current metrics summary
  getSummary() {
    return {
      websocket: {
        connections: this.metrics.websocket.connections,
        avgLatency: this.metrics.websocket.latency.length > 0
          ? (this.metrics.websocket.latency.reduce((a, b) => a + b, 0) / this.metrics.websocket.latency.length).toFixed(2)
          : 0,
        messagesPerSecond: this.metrics.websocket.messagesPerSecond
      },
      api: {
        requestsPerSecond: this.metrics.api.requestsPerSecond,
        avgResponseTime: this.metrics.api.responseTime.length > 0
          ? (this.metrics.api.responseTime.reduce((a, b) => a + b, 0) / this.metrics.api.responseTime.length).toFixed(2)
          : 0,
        totalErrors: Object.values(this.metrics.api.endpoints).reduce((sum, ep) => sum + ep.errors, 0)
      },
      dashboard: {
        activeUsers: this.metrics.dashboard.activeUsers,
        avgChartRenderTime: this.metrics.dashboard.chartRenderTime.length > 0
          ? (this.metrics.dashboard.chartRenderTime.reduce((a, b) => a + b, 0) / this.metrics.dashboard.chartRenderTime.length).toFixed(2)
          : 0,
        recentErrors: this.metrics.dashboard.errors.filter(e =>
          Date.now() - new Date(e.timestamp).getTime() < 5 * 60 * 1000
        ).length
      },
      system: {
        cpu: this.metrics.system.cpu.length > 0
          ? this.metrics.system.cpu[this.metrics.system.cpu.length - 1].toFixed(2)
          : 0,
        memory: this.metrics.system.memory.length > 0
          ? this.metrics.system.memory[this.metrics.system.memory.length - 1].toFixed(2)
          : 0
      },
      activeAlerts: this.alerts.filter(a => !a.resolved).length
    };
  }

  // Stop monitoring
  stop() {
    if (!this.isRunning) {
      console.log('⚠️ 性能監控未在運行');
      return;
    }

    console.log('🛑 停止性能監控...');
    this.isRunning = false;

    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    // Save final metrics
    this.saveMetrics();

    console.log('✅ 性能監控已停止');
  }
}

// Export for use in other modules
module.exports = PerformanceMonitor;

// Run standalone if needed
if (require.main === module) {
  const config = require('../config/test_config.json');
  const monitor = new PerformanceMonitor(config);

  // Start monitoring
  monitor.start();

  // Graceful shutdown
  process.on('SIGINT', () => {
    monitor.stop();
    process.exit(0);
  });

  // Print summary every 10 seconds
  setInterval(() => {
    console.log('\n📊 性能指標總結:');
    const summary = monitor.getSummary();
    console.log(JSON.stringify(summary, null, 2));
  }, 10000);
}