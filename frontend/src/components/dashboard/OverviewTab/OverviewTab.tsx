/**
 * Overview Tab Component
 * Main overview tab combining metrics cards, strategy list, and economic data
 */

import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useDispatch } from 'react-redux';
import { fetchDashboardStats, fetchSystemHealth, loadPreferences } from '../../../store/slices/dashboardSlice';
import { fetchAllEconomicIndicators } from '../../../store/slices/economicDataSlice';
import { MetricsCards } from './MetricsCards';
import { StrategyList } from './StrategyList';
import { EconomicMiniCards } from './EconomicMiniCards';
import { DashboardHeader } from '../shared/DashboardHeader';
import './OverviewTab.css';

/**
 * OverviewTab Component
 */
export const OverviewTab: React.FC = () => {
  const dispatch = useDispatch();

  // Load initial data
  useEffect(() => {
    // Load dashboard preferences from localStorage
    dispatch(loadPreferences());

    // Fetch dashboard data
    dispatch(fetchDashboardStats() as any);
    dispatch(fetchSystemHealth() as any);

    // Fetch economic data
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 1);

    dispatch(fetchAllEconomicIndicators({
      dateRange: {
        start: startDate.toISOString().split('T')[0],
        end: endDate.toISOString().split('T')[0]
      }
    }) as any).catch(() => {
      console.log('Using mock economic data for demo');
    });
  }, [dispatch]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="overview-tab"
    >
      {/* Quick Action Toolbar */}
      <DashboardHeader />

      {/* Key Metrics Cards */}
      <section className="overview-section">
        <MetricsCards />
      </section>

      {/* Strategy List and Economic Data Grid */}
      <div className="overview-grid">
        {/* Strategy Status List (Left - 60%) */}
        <section className="overview-grid-section overview-grid-section-left">
          <StrategyList />
        </section>

        {/* Economic Data Mini Cards (Right - 40%) */}
        <section className="overview-grid-section overview-grid-section-right">
          <EconomicMiniCards />
        </section>
      </div>
    </motion.div>
  );
};

export default OverviewTab;
