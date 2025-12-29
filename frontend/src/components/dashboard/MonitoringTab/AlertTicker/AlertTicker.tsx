/**
 * AlertTicker Component
 * Auto-scrolling alert ticker at bottom
 */

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Info, AlertCircle, AlertOctagon, X } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../../../hooks/redux';
import { markAlertAsRead } from '../../../../store/slices/monitoringSlice';
import { Alert } from '../../../../store/slices/monitoringSlice';
import './AlertTicker.css';

export const AlertTicker: React.FC = () => {
  const dispatch = useAppDispatch();
  const alerts = useAppSelector((state) => state.monitoring.alerts.filter((a) => !a.dismissed));
  const [isPaused, setIsPaused] = useState(false);
  const [position, setPosition] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();

  const getAlertIcon = (severity: Alert['severity']) => {
    switch (severity) {
      case 'info': return <Info size={14} />;
      case 'warning': return <AlertTriangle size={14} />;
      case 'error': return <AlertCircle size={14} />;
      case 'critical': return <AlertOctagon size={14} />;
    }
  };

  const getAlertColor = (severity: Alert['severity']) => {
    switch (severity) {
      case 'info': return '#3b82f6';
      case 'warning': return '#f59e0b';
      case 'error': return '#ef4444';
      case 'critical': return '#dc2626';
    }
  };

  // Auto-scroll animation
  useEffect(() => {
    if (!isPaused && alerts.length > 0 && containerRef.current) {
      const container = containerRef.current;
      const scroll = () => {
        setPosition((prev) => {
          if (container) {
            const maxScroll = container.scrollWidth - container.clientWidth;
            if (prev >= maxScroll) {
              return 0;
            }
            return prev + 1;
          }
          return 0;
        });
      };

      animationRef.current = requestAnimationFrame(scroll);
      return () => {
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
      };
    }
  }, [isPaused, alerts.length]);

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000 / 60);
    if (diff < 1) return '剛剛';
    if (diff < 60) return `${diff}分鐘前`;
    const hours = Math.floor(diff / 60);
    if (hours < 24) return `${hours}小時前`;
    return date.toLocaleDateString('zh-HK');
  };

  if (alerts.length === 0) {
    return null;
  }

  return (
    <div
      className="alert-ticker"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      ref={containerRef}
    >
      <div className="alert-ticker-content" style={{ transform: `translateX(-${position}px)` }}>
        <AnimatePresence>
          {alerts.map((alert) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="alert-item"
              style={{ borderLeftColor: getAlertColor(alert.severity) }}
            >
              <div className="alert-icon" style={{ color: getAlertColor(alert.severity) }}>
                {getAlertIcon(alert.severity)}
              </div>

              <div className="alert-content">
                <div className="alert-message">{alert.message}</div>
                <div className="alert-time">{formatTime(alert.timestamp)}</div>
              </div>

              {!alert.read && (
                <button
                  className="alert-dismiss"
                  onClick={() => dispatch(markAlertAsRead(alert.id))}
                >
                  <X size={14} />
                </button>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <div className="alert-ticker-controls">
        <button
          className={`ticker-control ${isPaused ? 'active' : ''}`}
          onClick={() => setIsPaused(!isPaused)}
        >
          {isPaused ? '▶ 繼續' : '⏸ 暫停'}
        </button>
      </div>
    </div>
  );
};

export default AlertTicker;
