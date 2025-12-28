/**
 * MarketDataPanel Component
 * Economic indicators, calendar, and market sentiment
 */

import React from 'react';
import { EconomicIndicators } from './EconomicIndicators';
import { EconomicCalendar } from './EconomicCalendar';
import { MarketSentiment } from './MarketSentiment';
import './MarketDataPanel.css';

export const MarketDataPanel: React.FC = () => {
  return (
    <div className="market-data-panel">
      <div className="panel-header">
        <h2>市場數據監控</h2>
      </div>

      <div className="market-data-content">
        {/* Economic Indicators */}
        <div className="market-data-section">
          <h3>核心經濟指標</h3>
          <EconomicIndicators />
        </div>

        {/* Economic Calendar */}
        <div className="market-data-section">
          <h3>經濟日曆</h3>
          <EconomicCalendar />
        </div>

        {/* Market Sentiment */}
        <div className="market-data-section">
          <h3>市場情緒</h3>
          <MarketSentiment />
        </div>
      </div>
    </div>
  );
};

export default MarketDataPanel;
