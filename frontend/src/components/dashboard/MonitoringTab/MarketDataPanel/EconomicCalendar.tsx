/**
 * EconomicCalendar Component
 * Upcoming economic data releases
 */

import React from 'react';
import { List, Tag } from 'antd';
import { Calendar } from 'lucide-react';

interface CalendarEvent {
  id: string;
  name: string;
  date: Date;
  importance: 'low' | 'medium' | 'high';
}

const mockEvents: CalendarEvent[] = [
  {
    id: '1',
    name: '美國非農就業數據',
    date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
    importance: 'high'
  },
  {
    id: '2',
    name: '香港 CPI 數據',
    date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000),
    importance: 'medium'
  },
  {
    id: '3',
    name: '中國貿易數據',
    date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    importance: 'medium'
  }
];

export const EconomicCalendar: React.FC = () => {
  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'default';
    }
  };

  const formatDate = (date: Date) => {
    const days = Math.ceil((date.getTime() - Date.now()) / (24 * 60 * 60 * 1000));
    if (days === 0) return '今天';
    if (days === 1) return '明天';
    return `${days}天后`;
  };

  return (
    <List
      size="small"
      dataSource={mockEvents}
      renderItem={(event) => (
        <List.Item>
          <div className="calendar-event">
            <Calendar size={14} />
            <div className="event-info">
              <div className="event-name">{event.name}</div>
              <div className="event-meta">
                <Tag color={getImportanceColor(event.importance)}>
                  {event.importance === 'high' ? '重要' : event.importance === 'medium' ? '中等' : '一般'}
                </Tag>
                <span className="event-date">{formatDate(event.date)}</span>
              </div>
            </div>
          </div>
        </List.Item>
      )}
    />
  );
};

export default EconomicCalendar;
