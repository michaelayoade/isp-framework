'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, AlertCircle } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
  requiredRole?: 'customer' | 'reseller' | 'admin';
  fallbackPath?: string;
}

export function AuthGuard({ 
  children, 
  requiredRole, 
  fallbackPath = '/login' 
}: AuthGuardProps) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      // Wait for auth context to finish loading
      if (isLoading) return;

      // Not authenticated - redirect to login
      if (!isAuthenticated || !user) {
        router.push(fallbackPath);
        return;
      }

      // Check role if required
      if (requiredRole && user.role !== requiredRole) {
        // Redirect based on actual role
        switch (user.role) {
          case 'customer':
            router.push('/customer-portal');
            break;
          case 'reseller':
            router.push('/reseller-portal');
            break;
          case 'admin':
            router.push('/admin');
            break;
          default:
            router.push('/login');
        }
        return;
      }

      // Check token expiry
      if (user.exp && Date.now() >= user.exp * 1000) {
        // Token expired - redirect to login
        router.push('/login?expired=true');
        return;
      }

      setIsChecking(false);
    };

    checkAuth();
  }, [isAuthenticated, isLoading, user, requiredRole, router, fallbackPath]);

  // Show loading while checking auth
  if (isLoading || isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-96">
          <CardHeader className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
            <CardTitle>Verifying Access</CardTitle>
            <CardDescription>
              Please wait while we verify your authentication...
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  // Show error if not authenticated (shouldn't reach here due to redirect)
  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-96">
          <CardHeader className="text-center">
            <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>
              You need to be logged in to access this page.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Button onClick={() => router.push('/login')}>
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show role mismatch error (shouldn't reach here due to redirect)
  if (requiredRole && user.role !== requiredRole) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-96">
          <CardHeader className="text-center">
            <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
            <CardTitle>Insufficient Permissions</CardTitle>
            <CardDescription>
              You do not have permission to access this page.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Button onClick={() => router.back()}>
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
