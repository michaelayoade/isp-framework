'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { User, Wifi, Eye, EyeOff } from 'lucide-react';
import { customerAuthApi, customerAuthUtils } from '@/api/customer-auth';

export default function CustomerLoginPage() {
  const [portalId, setPortalId] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const credentials = {
        portal_id: portalId,
        password
      };
      
      const response = await customerAuthApi.login(credentials);
      
      if (response.success) {
        customerAuthUtils.setAuthData(response);
        // Redirect to customer dashboard
        router.push('/customer/dashboard');
      } else {
        setError(response.message || 'Invalid portal ID or password. Please try again.');
      }
    } catch (err: unknown) {
      console.error('Login error:', err);
      if (err && typeof err === 'object' && 'response' in err) {
        const errorWithResponse = err as { response?: { status?: number } };
        if (errorWithResponse.response?.status === 401) {
          setError('Invalid portal ID or password. Please try again.');
        } else {
          setError('An error occurred during login. Please try again.');
        }
      } else {
        setError('An error occurred during login. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-blue-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="flex items-center space-x-2">
              <User className="h-8 w-8 text-green-600" />
              <Wifi className="h-8 w-8 text-green-600" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-green-800">Customer Portal</CardTitle>
          <CardDescription>
            Access your account and manage your services
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="portalId">Portal ID</Label>
              <Input
                id="portalId"
                type="text"
                placeholder="Enter your portal ID"
                value={portalId}
                onChange={(e) => setPortalId(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Button type="submit" className="w-full bg-green-600 hover:bg-green-700" disabled={isLoading}>
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
          <div className="mt-6 space-y-4">
            <div className="text-center">
              <a href="/customer/forgot-password" className="text-sm text-green-600 hover:underline">
                Forgot your password?
              </a>
            </div>
            <div className="text-center text-sm text-gray-600">
              <p>Need help? Contact support</p>
              <div className="mt-2 space-x-4">
                <a href="/admin/login" className="text-gray-600 hover:underline">
                  Admin Portal
                </a>
                <a href="/reseller/login" className="text-blue-600 hover:underline">
                  Reseller Portal
                </a>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
