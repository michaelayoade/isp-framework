'use client';

import { useEffect, useState } from 'react';

export function MSWProvider({ children }: { children: React.ReactNode }) {
  const [mswReady, setMswReady] = useState(false);

  useEffect(() => {
    const initMSW = async () => {
      if (process.env.NODE_ENV === 'development') {
        const { worker } = await import('../../__mocks__/browser');
        await worker.start({
          onUnhandledRequest: 'warn',
        });
        console.log('🔶 MSW enabled for development');
      }
      setMswReady(true);
    };

    initMSW();
  }, []);

  if (!mswReady) {
    return <div>Loading...</div>;
  }

  return <>{children}</>;
}
