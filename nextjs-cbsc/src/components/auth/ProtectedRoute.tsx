'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/providers/AuthProvider';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
  requiredPermission?: string;
}

export function ProtectedRoute({
  children,
  requiredRole,
  requiredPermission,
}: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    if (loading) return;

    if (!user) {
      router.push('/auth/login');
      return;
    }

    // Check role requirements
    if (requiredRole && user.role.name !== requiredRole) {
      router.push('/dashboard?error=unauthorized');
      return;
    }

    // Check permission requirements
    if (requiredPermission) {
      const hasPermission = user.role.permissions.some(
        (permission) => permission.name === requiredPermission
      );
      if (!hasPermission) {
        router.push('/dashboard?error=insufficient_permissions');
        return;
      }
    }

    setIsChecking(false);
  }, [user, loading, router, requiredRole, requiredPermission]);

  if (loading || isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}