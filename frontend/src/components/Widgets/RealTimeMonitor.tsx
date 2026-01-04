import React from 'react';

interface RealTimeMonitorProps {
  data?: any;
}

export const RealTimeMonitor: React.FC<RealTimeMonitorProps> = ({ data }) => {
  return (
    <div className="realtime-monitor-widget">
      <h3>实时监控</h3>
      <div className="widget-content">
        <p>实时数据监控中...</p>
        <div className="status-indicator">
          <span className="dot active"></span>
          <span>系统运行正常</span>
        </div>
      </div>
    </div>
  );
};
