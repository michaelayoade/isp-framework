'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export default function QueryProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            retry: (failureCount, error: unknown) => {
              // Don't retry on 4xx errors
              if (error && typeof error === 'object' && 'response' in error) {
                const errorResponse = error as { response?: { status?: number } };
                if (errorResponse.response?.status && errorResponse.response.status >= 400 && errorResponse.response.status < 500) {
                  return false;
                }
              }
              if (typeof error === 'object' && error && 'status' in error) {
                const statusError = error as { status?: number };
                if (statusError.status && statusError.status >= 400 && statusError.status < 500) {
                  return false;
                }
              }
              return failureCount < 3;
            },
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
