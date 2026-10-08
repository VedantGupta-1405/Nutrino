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

  // Initialize or restore personal single-user session
  const initSession = useCallback(async () => {
    try {
      const sessionData = await authApi.getSession();
      localStorage.setItem('nutrino_token', sessionData.access_token);
      localStorage.setItem('nutrino_user', JSON.stringify(sessionData.user));
      setToken(sessionData.access_token);
      setUser(sessionData.user);
      return sessionData.user;
    } catch (err) {
      console.error('Failed to initialize single-user session:', err);
      return null;
    }
  }, []);

  useEffect(() => {
    async function verifyOrInitSession() {
      const storedToken = localStorage.getItem('nutrino_token');
      if (storedToken) {
        try {
          const currentUser = await authApi.getCurrentUser();
          setUser(currentUser);
          localStorage.setItem('nutrino_user', JSON.stringify(currentUser));
          setIsLoading(false);
          return;
        } catch {
          // Stored token expired or invalid; fall through to get a fresh session
        }
      }

      await initSession();
      setIsLoading(false);
    }

    verifyOrInitSession();

    const handleAuthExpired = () => {
      initSession();
    };

    window.addEventListener('nutrino_auth_expired', handleAuthExpired);
    return () => window.removeEventListener('nutrino_auth_expired', handleAuthExpired);
  }, [initSession]);

  const value = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    refreshSession: initSession,
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
