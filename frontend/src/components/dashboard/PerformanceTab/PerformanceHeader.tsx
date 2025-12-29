/**
 * PerformanceHeader Component
 * Control bar with time range selector, strategy selector, and export
 */

import React from 'react';
import { Space, Button, DatePicker } from 'antd';
import { Download } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '../../../hooks/redux';
import { setTimeRange, fetchPerformanceAnalytics, TimeRange, TimeRangePreset } from '../../../store/slices/performanceAnalyticsSlice';
import dayjs, { Dayjs } from 'dayjs';
import './PerformanceHeader.css';

const { RangePicker } = DatePicker;

export const PerformanceHeader: React.FC = () => {
  const dispatch = useAppDispatch();
  const selectedTimeRange = useAppSelector((state) => state.performanceAnalytics.selectedTimeRange);
  const isLoading = useAppSelector((state) => state.performanceAnalytics.isLoading);
  const lastUpdate = useAppSelector((state) => state.performanceAnalytics.lastUpdate);

  const isCustomRange = typeof selectedTimeRange === 'object' && 'start' in selectedTimeRange;

  const handleTimeRangeChange = async (value: TimeRangePreset) => {
    try {
      const newRange: TimeRange = value;
      dispatch(setTimeRange(newRange));
      await dispatch(fetchPerformanceAnalytics({ timeRange: newRange }));
    } catch (error) {
      console.error('Failed to update time range:', error);
    }
  };

  const handleCustomRangeChange = async (dates: null | [Dayjs | null, Dayjs | null]) => {
    try {
      if (dates && dates[0] && dates[1]) {
        const newRange: TimeRange = {
          start: dates[0].format('YYYY-MM-DD'),
          end: dates[1].format('YYYY-MM-DD'),
        };
        dispatch(setTimeRange(newRange));
        await dispatch(fetchPerformanceAnalytics({ timeRange: newRange }));
      }
    } catch (error) {
      console.error('Failed to update custom date range:', error);
    }
  };

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Exporting performance analytics...');
  };

  const formatLastUpdate = () => {
    if (!lastUpdate) return '未更新';
    const diff = Math.floor((Date.now() - lastUpdate.getTime()) / 1000 / 60);
    if (diff < 1) return '剛剛';
    if (diff < 60) return `${diff}分鐘前`;
    return lastUpdate.toLocaleTimeString('zh-HK', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="performance-header">
      <Space size="large">
        {/* Time Range Selector */}
        <div className="performance-header-section">
          <span className="performance-header-label">時間範圍：</span>
          <Space.Compact>
            <Button
              type={!isCustomRange && selectedTimeRange === '1w' ? 'primary' : 'default'}
              size="small"
              onClick={() => handleTimeRangeChange('1w')}
            >
              1週
            </Button>
            <Button
              type={!isCustomRange && selectedTimeRange === '1m' ? 'primary' : 'default'}
              size="small"
              onClick={() => handleTimeRangeChange('1m')}
            >
              1月
            </Button>
            <Button
              type={!isCustomRange && selectedTimeRange === '3m' ? 'primary' : 'default'}
              size="small"
              onClick={() => handleTimeRangeChange('3m')}
            >
              3月
            </Button>
            <Button
              type={!isCustomRange && selectedTimeRange === '1y' ? 'primary' : 'default'}
              size="small"
              onClick={() => handleTimeRangeChange('1y')}
            >
              1年
            </Button>
          </Space.Compact>
        </div>

        {/* Custom Date Range */}
        <div className="performance-header-section">
          <RangePicker
            value={isCustomRange ? [dayjs(selectedTimeRange.start), dayjs(selectedTimeRange.end)] : null}
            onChange={handleCustomRangeChange}
            format="YYYY-MM-DD"
            size="small"
            allowClear={false}
          />
        </div>

        {/* Last Updated */}
        <div className="performance-header-meta">
          <span className="performance-header-label">更新時間：</span>
          <span>{formatLastUpdate()}</span>
        </div>

        {/* Export Button */}
        <Button
          icon={<Download size={14} />}
          size="small"
          onClick={handleExport}
          loading={isLoading}
        >
          導出報告
        </Button>
      </Space>
    </div>
  );
};

export default PerformanceHeader;
