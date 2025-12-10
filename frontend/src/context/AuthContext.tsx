'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '@/types';
import { apiClient } from '@/lib/api-client';
import { tronWebManager } from '@/lib/tronweb';
import toast from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (walletAddress: string, signature: string) => Promise<boolean>;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing auth token and load user profile
    const initAuth = async () => {
      const token = apiClient.getAuthToken();
      if (token) {
        try {
          await refreshProfile();
        } catch (error) {
          console.error('Failed to load user profile:', error);
          apiClient.clearAuth();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (walletAddress: string, signature: string): Promise<boolean> => {
    try {
      setIsLoading(true);

      const response = await apiClient.post('/api/auth/login', {
        walletAddress,
        signature,
      });

      if (response.success && response.token) {
        apiClient.setAuthToken(response.token);
        setUser(response.user);
        toast.success('Successfully logged in!');
        return true;
      }

      return false;
    } catch (error) {
      console.error('Login failed:', error);
      toast.error('Login failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    apiClient.clearAuth();
    setUser(null);
    toast.success('Logged out successfully');
  };

  const updateUser = (updates: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...updates });
    }
  };

  const refreshProfile = async () => {
    try {
      const response = await apiClient.get('/api/auth/profile');
      if (response.success && response.user) {
        setUser(response.user);
      }
    } catch (error) {
      console.error('Failed to refresh profile:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        updateUser,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
