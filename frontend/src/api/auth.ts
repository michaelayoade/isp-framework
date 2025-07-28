import { apiClient } from './client';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: 'admin' | 'customer' | 'reseller';
}

// Auth API functions
export const authApi = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/jwt/login', credentials);
    return response.data;
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
    // Clear tokens from localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken
    });
    return response.data;
  }
};

// Auth utility functions
export const authUtils = {
  setTokens(tokens: AuthResponse): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
    }
  },

  getAccessToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('access_token');
    }
    return null;
  },

  getRefreshToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('refresh_token');
    }
    return null;
  },

  clearTokens(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }
};
