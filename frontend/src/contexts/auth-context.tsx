'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authUtils } from '@/api/auth';
import { AdminUser } from '@/api/admin-auth';
import { CustomerUser } from '@/api/customer-auth';
import { ResellerUser } from '@/api/reseller-auth';

interface AppAuthContextType {
  user: AdminUser | CustomerUser | ResellerUser | null;
  role: string | null;
  isAuthenticated: boolean;
  login: () => void;
  logout: () => void;
}

const AppAuthContext = createContext<AppAuthContextType | undefined>(undefined);

export function AppAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AdminUser | CustomerUser | ResellerUser | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check authentication status on initial load
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    const authRole = authUtils.getUserRole();
    
    if (authRole) {
      try {
        const currentUser = await authUtils.getCurrentUser();
        if (currentUser) {
          setRole(authRole);
          setUser(currentUser);
          setIsAuthenticated(true);
          return;
        }
      } catch (error) {
        console.error('Error getting current user:', error);
      }
    }
    
    setRole(null);
    setUser(null);
    setIsAuthenticated(false);
  };

  const login = async () => {
    await checkAuthStatus();
  };

  const logout = () => {
    authUtils.logout();
    setRole(null);
    setUser(null);
    setIsAuthenticated(false);
  };

  const value = {
    user,
    role,
    isAuthenticated,
    login,
    logout
  };

  return <AppAuthContext.Provider value={value}>{children}</AppAuthContext.Provider>;
}

export function useAppAuth() {
  const context = useContext(AppAuthContext);
  if (context === undefined) {
    throw new Error('useAppAuth must be used within an AppAuthProvider');
  }
  return context;
}
