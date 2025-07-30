'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Building2, Users } from 'lucide-react';
import { resellerAuthApi, resellerAuthUtils } from '@/api/reseller-auth';

export default function ResellerLoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const credentials = {
        email,
        password
      };
      
      const response = await resellerAuthApi.login(credentials);
      resellerAuthUtils.setAuthData(response);
      
      // Redirect to reseller dashboard
      router.push('/reseller/dashboard');
    } catch (err: unknown) {
      console.error('Login error:', err);
      if (err && typeof err === 'object' && 'response' in err) {
        const errorWithResponse = err as { response?: { status?: number } };
        if (errorWithResponse.response?.status === 401) {
          setError('Invalid credentials. Please try again.');
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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="flex items-center space-x-2">
              <Building2 className="h-8 w-8 text-blue-600" />
              <Users className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-blue-800">Reseller Portal</CardTitle>
          <CardDescription>
            Partner access to manage customers and commissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Partner Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="partner@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700" disabled={isLoading}>
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
          <div className="mt-6 space-y-4">
            <div className="text-center">
              <a href="/reseller/forgot-password" className="text-sm text-blue-600 hover:underline">
                Forgot your password?
              </a>
            </div>
            <div className="border-t pt-4">
              <p className="text-sm text-gray-600 text-center mb-2">
                New partner? Contact us to get started
              </p>
              <div className="text-center space-x-4 text-sm">
                <a href="/admin/login" className="text-gray-600 hover:underline">
                  Admin Portal
                </a>
                <a href="/customer/login" className="text-green-600 hover:underline">
                  Customer Portal
                </a>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
