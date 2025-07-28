'use client';

import QueryProvider from './QueryProvider';
import ThemeProvider from './ThemeProvider';
import { AuthProvider } from '@/contexts/AuthContext';
import { MSWProvider } from './msw-provider';

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>
      <MSWProvider>
        <QueryProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </QueryProvider>
      </MSWProvider>
    </ThemeProvider>
  );
}
