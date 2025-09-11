import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { useApiTokenCreate, useApiTokenRefreshCreate } from '../api/generated/gitdmApi';
import { axiosClient } from '../api/http/axios-instance';
import { queryClient } from '../lib/queryClient';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

// SECURITY NOTE: Storing refresh tokens in localStorage is a security risk.
// TODO: Implement server-side changes to:
// 1. Issue refresh tokens as HttpOnly, Secure, SameSite cookies
// 2. Implement token rotation (new refresh token on each use)
// 3. Add shorter expiration times for refresh tokens
// Current implementation is temporary and should be replaced with cookie-based approach

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const loginMutation = useApiTokenCreate();
  const refreshMutation = useApiTokenRefreshCreate();

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    (async () => {
      if (token) {
        applyAuthHeader(token);
        try {
          await refreshToken();
          setIsAuthenticated(true);
        } catch {
          logout();
        }
      }
      setIsLoading(false);
    })();
  }, []);

  // Setup axios interceptor
  const applyAuthHeader = (token: string) => {
    axiosClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };

  // Setup response interceptor for token refresh
  useEffect(() => {
    // dedupe concurrent refresh calls
    let refreshPromise: Promise<void> | null = null;
    const ensureSingleRefresh = () => {
      if (!refreshPromise) {
        refreshPromise = refreshToken().finally(() => {
          refreshPromise = null;
        });
      }
      return refreshPromise;
    };

    const interceptor = axiosClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config as { _retry?: boolean; url?: string };
        if (!originalRequest) return Promise.reject(error);
        // Important: Do not intercept the refresh token request itself to avoid a loop
        if (originalRequest.url && /token\/refresh/i.test(originalRequest.url)) {
          return Promise.reject(error);
        }

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            await ensureSingleRefresh();
            return axiosClient(originalRequest);
          } catch (refreshError) {
            logout();
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );

    return () => {
      axiosClient.interceptors.response.eject(interceptor);
    };
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await loginMutation.mutateAsync({
        data: { email, password },
      });

      const { access, refresh } = response;
      
      localStorage.setItem(ACCESS_TOKEN_KEY, access);
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
      
      applyAuthHeader(access);
      setIsAuthenticated(true);
    } catch (error) {
      throw error;
    }
  };

  const logout = useCallback(() => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    delete axiosClient.defaults.headers.common['Authorization'];
    queryClient.clear(); // Clear React Query cache
    setIsAuthenticated(false);
  }, []);

  // Cross-tab logout sync
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === REFRESH_TOKEN_KEY && e.newValue === null) {
        // Refresh token was removed in another tab
        logout();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [logout]);

  const refreshToken = async () => {
    const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refresh) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await refreshMutation.mutateAsync({
        data: { refresh },
      });

      const { access } = response;
      
      localStorage.setItem(ACCESS_TOKEN_KEY, access);
      applyAuthHeader(access);
    } catch (error) {
      logout();
      throw error;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        login,
        logout,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}