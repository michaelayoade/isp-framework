'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/api/client';

export interface User {
  id: number;
  email: string;
  name: string;
  role: 'admin' | 'customer' | 'reseller';
  is_active: boolean;
  created_at: string;
  exp?: number; // JWT expiry timestamp
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const isAuthenticated = !!user;

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          await refreshUser();
        } catch (error) {
          console.error('Failed to refresh user:', error);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      // Create form data for the backend authentication endpoint
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await apiClient.post('/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token, refresh_token, token_type } = response.data;
      
      // Get user data after successful login
      const userResponse = await apiClient.get('/auth/me', {
        headers: {
          'Authorization': `${token_type} ${access_token}`,
        },
      });
      
      const userData = userResponse.data;

      // Store tokens
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // Set user state
      setUser(userData);

      // Redirect based on role
      if (userData.role === 'admin') {
        router.push('/admin');
      } else if (userData.role === 'customer') {
        router.push('/customer');
      } else if (userData.role === 'reseller') {
        router.push('/reseller');
      }
    } catch (error: unknown) {
      console.error('Login failed:', error);
      const errorMessage = error instanceof Error ? error.message : 
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Login failed';
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    // Clear tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // Clear user state
    setUser(null);
    
    // Redirect to login
    router.push('/login');
  };

  const refreshUser = async () => {
    try {
      const response = await apiClient.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
