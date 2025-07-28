'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'customer' | 'reseller';
  redirectTo?: string;
}

export function ProtectedRoute({ 
  children, 
  requiredRole,
  redirectTo = '/login' 
}: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push(redirectTo);
        return;
      }

      if (requiredRole && user?.role !== requiredRole) {
        // Redirect based on user role if they don't have required role
        if (user?.role === 'admin') {
          router.push('/admin');
        } else if (user?.role === 'customer') {
          router.push('/customer');
        } else if (user?.role === 'reseller') {
          router.push('/reseller');
        } else {
          router.push('/login');
        }
        return;
      }
    }
  }, [isLoading, isAuthenticated, user, requiredRole, router, redirectTo]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  if (requiredRole && user?.role !== requiredRole) {
    return null; // Will redirect in useEffect
  }

  return <>{children}</>;
}
