import React from 'react';
import { PersonalStrategyDashboard } from '../components/PersonalStrategy/PersonalStrategyDashboard';

export const PersonalStrategyPage: React.FC = () => {
  // This would typically come from authentication context
  const userId = 'user-123'; // Mock user ID

  return (
    <PersonalStrategyDashboard
      userId={userId}
      apiUrl="/api"
      wsUrl="ws://localhost:3003/ws"
      theme="light"
      onThemeChange={(theme) => {
        // Handle theme change
        document.documentElement.setAttribute('data-theme', theme);
      }}
    />
  );
};

export default PersonalStrategyPage;