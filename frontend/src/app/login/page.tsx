'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Wifi, Users, CreditCard, BarChart3, Shield, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export default function LoginPage() {
  const [formData, setFormData] = useState({
    username: 'admin',
    password: 'admin123',
  });
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.username || !formData.password) {
      toast({
        title: 'Error',
        description: 'Please enter both username and password',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    try {
      await login(formData.username, formData.password);
      toast({
        title: 'Success',
        description: 'Logged in successfully',
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Invalid credentials';
      toast({
        title: 'Login Failed',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo and Title */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-green-600 rounded-lg">
              <Wifi className="h-8 w-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">ISP Framework</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">Enterprise ISP Management Platform</p>
        </div>

        {/* Demo Credentials Alert */}
        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription>
            <strong>Demo Credentials:</strong><br />
            Admin: admin / admin123<br />
            Customer: customer@example.com / customer123
          </AlertDescription>
        </Alert>

        {/* Login Form */}
        <Card>
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>
              Enter your credentials to access your account
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="Enter your username"
                  value={formData.username}
                  onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                  required
                  disabled={isLoading}
                />
              </div>
              <Button 
                type="submit" 
                className="w-full" 
                size="lg"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing In...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Feature Preview */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Platform Features</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <Users className="h-4 w-4 text-green-600" />
                <span className="text-sm">Customer Management</span>
              </div>
              <div className="flex items-center space-x-2">
                <CreditCard className="h-4 w-4 text-green-600" />
                <span className="text-sm">Billing & Invoicing</span>
              </div>
              <div className="flex items-center space-x-2">
                <Wifi className="h-4 w-4 text-green-600" />
                <span className="text-sm">Network Monitoring</span>
              </div>
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-4 w-4 text-green-600" />
                <span className="text-sm">Analytics & Reports</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
