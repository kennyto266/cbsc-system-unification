import React from 'react';
import { Outlet } from 'react-router-dom';
import { useResponsive } from '../../hooks/useResponsive';
import { NavigationProvider } from '../../navigation/NavigationProvider';
import MainLayout from './MainLayout';
import MobileLayout from './MobileLayout';

interface ResponsiveLayoutProps {
  children?: React.ReactNode;
}

/**
 * ResponsiveLayout - Automatically switches between desktop and mobile layouts
 */
const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({ children }) => {
  const { isMobile } = useResponsive();

  // Render mobile layout on mobile devices
  if (isMobile) {
    return (
      <NavigationProvider>
        <MobileLayout>
          {children || <Outlet />}
        </MobileLayout>
      </NavigationProvider>
    );
  }

  // Render desktop layout on larger screens
  return (
    <NavigationProvider>
      <MainLayout>
        {children || <Outlet />}
      </MainLayout>
    </NavigationProvider>
  );
};

export default ResponsiveLayout;