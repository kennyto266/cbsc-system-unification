import React from 'react';
import { Outlet } from 'react-router-dom';
import { useResponsive } from '../../hooks/useResponsive';
import { NavigationProvider } from '../../navigation/NavigationProvider';
import MainLayout from './MainLayout';
import MobileLayout from './MobileLayout';

/**
 * ResponsiveLayout - Automatically switches between desktop and mobile layouts
 */
const ResponsiveLayout: React.FC = () => {
  const { isMobile } = useResponsive();

  // Render mobile layout on mobile devices
  if (isMobile) {
    return (
      <NavigationProvider>
        <MobileLayout>
          <Outlet />
        </MobileLayout>
      </NavigationProvider>
    );
  }

  // Render desktop layout on larger screens
  return (
    <NavigationProvider>
      <MainLayout>
        <Outlet />
      </MainLayout>
    </NavigationProvider>
  );
};

export default ResponsiveLayout;