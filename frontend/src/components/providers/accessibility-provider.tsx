'use client';

import { useAccessibility } from '@/hooks/use-accessibility';

export function AccessibilityProvider({ children }: { children: React.ReactNode }) {
  useAccessibility();
  return <>{children}</>;
}
