/**
 * useAuth Hook - Gerenciamento de estado de autenticação
 * 
 * IMPORTANTE: Este hook foi otimizado para evitar condições de corrida
 * e re-renders desnecessários durante a verificação de auth.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { authApi, userApi, creditsApi } from '../api';

/**
 * Hook para autenticação
 */
export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  // Ref para controlar se a operação já foi completada (evita condição de corrida)
  const authCheckCompleted = useRef(false);

  // Verifica estado de auth inicial no mount - com timeout seguro
  useEffect(() => {
    let isMounted = true;
    
    const checkAuth = async () => {
      if (authApi.isAuthenticated()) {
        try {
          const userData = await userApi.getProfile();
          if (isMounted && !authCheckCompleted.current) {
            authCheckCompleted.current = true;
            setUser(userData);
            setIsAuthenticated(true);
            setLoading(false);
          }
        } catch {
          // Token inválido ou backend offline, limpa token
          if (isMounted && !authCheckCompleted.current) {
            authCheckCompleted.current = true;
            authApi.logout();
            setIsAuthenticated(false);
            setLoading(false);
          }
        }
      } else {
        // Não tem token, finaliza loading
        if (isMounted && !authCheckCompleted.current) {
          authCheckCompleted.current = true;
          setLoading(false);
        }
      }
    };
    
    // Timeout de segurança para não bloquear se backend estiver lento
    const timeoutId = setTimeout(() => {
      if (isMounted && !authCheckCompleted.current) {
        authCheckCompleted.current = true;
        setLoading(false);
        setIsAuthenticated(false);
        console.warn('[Auth] Timeout ao verificar autenticação - backend pode estar offline');
      }
    }, 3000);
    
    checkAuth();
    
    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, []);

  const login = useCallback(async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      await authApi.login({ email, password });
      const userData = await userApi.getProfile();
      setUser(userData);
      setIsAuthenticated(true);
      return userData;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (email, password, name) => {
    setLoading(true);
    setError(null);
    try {
      await authApi.register({ email, password, name });
      const userData = await userApi.getProfile();
      setUser(userData);
      setIsAuthenticated(true);
      return userData;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    authApi.logout();
    setUser(null);
    setIsAuthenticated(false);
    setError(null);
  }, []);

  const updateProfile = useCallback(async (data) => {
    setError(null);
    try {
      const updated = await userApi.updateProfile(data);
      setUser((prev) => ({ ...prev, ...updated }));
      return updated;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  return {
    user,
    loading,
    error,
    isAuthenticated,
    login,
    register,
    logout,
    updateProfile,
    clearError: () => setError(null),
  };
}

/**
 * Hook for credits management
 */
export function useCredits() {
  const [credits, setCredits] = useState(0);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBalance = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await creditsApi.getBalance();
      setCredits(data.credits || 0);
      return data.credits;
    } catch (err) {
      setError(err.message);
      return 0;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchHistory = useCallback(async (params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const data = await creditsApi.getHistory(params);
      setHistory(data || []);
      return data;
    } catch (err) {
      setError(err.message);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  // Update credits locally (after synthesis usage)
  const deductCredits = useCallback((amount) => {
    setCredits((prev) => Math.max(0, prev - amount));
  }, []);

  return {
    credits,
    history,
    loading,
    error,
    fetchBalance,
    fetchHistory,
    deductCredits,
    clearError: () => setError(null),
  };
}

export default {
  useAuth,
  useCredits,
};
