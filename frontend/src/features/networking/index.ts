// Networking module exports
export * from './types';

// Export a placeholder hook for testing
export function useNetworking() {
  return {
    devices: [],
    loading: false,
    error: null
  };
}
