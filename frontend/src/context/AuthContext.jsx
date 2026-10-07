import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('nutrino_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => localStorage.getItem('nutrino_token') || null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem('nutrino_token');
    localStorage.removeItem('nutrino_user');
    setToken(null);
    setUser(null);
  }, []);

  // Sync / verify authenticated user session on mount
  useEffect(() => {
    async function verifySession() {
      const storedToken = localStorage.getItem('nutrino_token');
      if (!storedToken) {
        setIsLoading(false);
        return;
      }
      try {
        const currentUser = await authApi.getCurrentUser();
        setUser(currentUser);
        localStorage.setItem('nutrino_user', JSON.stringify(currentUser));
      } catch {
        logout();
      } finally {
        setIsLoading(false);
      }
    }

    verifySession();

    const handleAuthExpired = () => {
      logout();
    };

    window.addEventListener('nutrino_auth_expired', handleAuthExpired);
    return () => window.removeEventListener('nutrino_auth_expired', handleAuthExpired);
  }, [logout]);

  const login = async (email, password) => {
    const data = await authApi.login({ email, password });
    localStorage.setItem('nutrino_token', data.access_token);
    localStorage.setItem('nutrino_user', JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const register = async (name, email, password) => {
    const data = await authApi.register({ name, email, password });
    localStorage.setItem('nutrino_token', data.access_token);
    localStorage.setItem('nutrino_user', JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const value = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
