/**
 * Alert Management Dashboard Page
 * Complete dashboard for managing economic alerts and notifications
 */

import React, { useState } from 'react';
import { EconomicAlerts, AlertRules, AlertHistory } from '../components/Alerts';
import { NotificationCenter, NotificationSettings } from '../components/Notifications';

const AlertManagementDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'alerts' | 'rules' | 'history' | 'notifications' | 'settings'>('alerts');

  const tabs = [
    { id: 'alerts', label: '警報', icon: '🔔' },
    { id: 'rules', label: '警報規則', icon: '⚙️' },
    { id: 'history', label: '警報歷史', icon: '📊' },
    { id: 'notifications', label: '通知中心', icon: '📱' },
    { id: 'settings', label: '通知設置', icon: '🔧' }
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'alerts':
        return (
          <EconomicAlerts
            showStatistics={true}
            showBulkActions={true}
            maxDisplayCount={50}
            autoRefresh={true}
          />
        );
      case 'rules':
        return (
          <AlertRules
            showInactive={true}
            allowCreate={true}
            allowEdit={true}
            allowDelete={true}
          />
        );
      case 'history':
        return (
          <AlertHistory
            showStatistics={true}
            showFilters={true}
            allowExport={true}
            maxRecordsPerPage={100}
          />
        );
      case 'notifications':
        return (
          <NotificationCenter
            showSettings={false}
            showHistory={true}
            maxDisplayCount={20}
            autoRefresh={true}
          />
        );
      case 'settings':
        return <NotificationSettings />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-xl font-bold text-gray-900">警報管理系統</h1>
            <div className="text-sm text-gray-500">
              實時監控經濟指標和策略警報
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderContent()}
      </div>
    </div>
  );
};

export default AlertManagementDashboard;