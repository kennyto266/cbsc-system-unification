// CBSC Trading System - Protected Route Component
// Route guard that checks authentication status

import { Navigate, useLocation } from 'react-router-dom';
import { useAppSelector } from '@/store';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * Route guard component that redirects to login if user is not authenticated
 *
 * DEV MODE: Auth temporarily disabled for testing
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  // Safe selector access - don't destructure to avoid issues
  const authState = useAppSelector((state) => state?.auth);
  const location = useLocation();

  // Check for token with null safety
  const token = authState?.token;

  // DEV MODE: Skip auth check for testing - Comment out the next line to enable auth
  // if (!token) {
  //   // Redirect to login with return url
  //   return <Navigate to="/login" state={{ from: location }} replace />;
  // }

  return <>{children}</>;
};
