'use client';

import { useEffect } from 'react';

export function useAccessibility() {
  useEffect(() => {
    // Only run accessibility checks in development
    if (process.env.NODE_ENV !== 'development') return;
    
    // Only run if accessibility checks are enabled
    if (process.env.NEXT_PUBLIC_ENABLE_ACCESSIBILITY !== 'true') return;

    let axe: typeof import('@axe-core/react') | null = null;
    
    const initAxe = async () => {
      try {
        axe = await import('@axe-core/react');
        const React = await import('react');
        const ReactDOM = await import('react-dom');
        
        axe.default(React, ReactDOM, 1000);
        console.log('♿ Accessibility checks enabled');
      } catch (error) {
        console.warn('Failed to initialize accessibility checks:', error);
      }
    };

    initAxe();

    return () => {
      if (axe) {
        // Cleanup if needed
      }
    };
  }, []);
}
