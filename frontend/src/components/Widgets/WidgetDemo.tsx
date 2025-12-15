import React from 'react';
import { WidgetProvider } from '../../contexts/WidgetContext';
import { WidgetDashboardDemo } from '../../pages/WidgetDashboardDemo';

export function WidgetDemo() {
  return (
    <WidgetProvider>
      <WidgetDashboardDemo />
    </WidgetProvider>
  );
}