/**
 * API Context - Gerenciamento global de estado para interações com API
 * 
 * IMPORTANTE: Este contexto foi otimizado para evitar re-renders infinitos.
 * Todas as funções são memoizadas e o value do contexto usa useMemo.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { useAuth, useCredits, useVoiceProfiles, useVoiceSynthesis } from '../hooks';
import { healthApi } from '../api';

// Context
const ApiContext = createContext(null);

// Configuração de retry com exponential backoff
const INITIAL_RETRY_DELAY = 3000;  // 3 segundos
const MAX_RETRY_DELAY = 30000;     // 30 segundos max
const RETRY_MULTIPLIER = 1.5;      // Fator de backoff exponencial

/**
 * API Provider Component
 * 
 * Gerencia estado global da aplicação incluindo auth, créditos,
 * perfis de voz e status do sistema.
 */
export function ApiProvider({ children }) {
  // Auth state
  const auth = useAuth();
  
  // Credits state
  const credits = useCredits();
  
  // Voice profiles state
  const voiceProfiles = useVoiceProfiles();
  
  // Synthesis state
  const synthesis = useVoiceSynthesis();
  
  // System status com retry automático
  const [systemStatus, setSystemStatus] = useState({
    online: false,
    gpuAvailable: false,
    gpuName: null,
    loading: true,
    retryCount: 0,
    nextRetryIn: 0,
  });
  
  // Refs para gerenciamento de retry (evita re-renders)
  const retryTimeoutRef = useRef(null);
  const countdownIntervalRef = useRef(null);
  
  // Ref para evitar carregamento duplicado de dados do usuário
  const initialDataLoadedRef = useRef(false);

  // Verifica saúde do sistema com auto-retry
  const checkHealth = useCallback(async (retryDelay = INITIAL_RETRY_DELAY, retryCount = 0) => {
    // Limpa timers existentes
    if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
    if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    
    try {
      const health = await healthApi.detailed();
      setSystemStatus({
        online: health.status === 'healthy',
        gpuAvailable: health.gpu?.available ?? false,
        gpuName: health.gpu?.name ?? null,
        loading: false,
        retryCount: 0,
        nextRetryIn: 0,
      });
      console.log('[API] Backend conectado com sucesso!', health.gpu?.name || 'Modo CPU');
      return true;
    } catch (error) {
      // Backend offline - agenda retry com exponential backoff
      const nextDelay = Math.min(retryDelay * RETRY_MULTIPLIER, MAX_RETRY_DELAY);
      const newRetryCount = retryCount + 1;
      
      console.log(`[API] Backend offline (tentativa ${newRetryCount}). Retentando em ${retryDelay/1000}s...`);
      
      // Define countdown inicial
      setSystemStatus(prev => ({
        ...prev,
        online: false,
        loading: false,
        retryCount: newRetryCount,
        nextRetryIn: Math.ceil(retryDelay / 1000),
      }));
      
      // Timer de countdown para UI
      let countdown = Math.ceil(retryDelay / 1000);
      countdownIntervalRef.current = setInterval(() => {
        countdown--;
        if (countdown > 0) {
          setSystemStatus(prev => ({ ...prev, nextRetryIn: countdown }));
        }
      }, 1000);
      
      // Agenda próximo retry
      retryTimeoutRef.current = setTimeout(() => {
        if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
        checkHealth(nextDelay, newRetryCount);
      }, retryDelay);
      
      return false;
    }
  }, []);

  // Função de retry manual
  const retryConnection = useCallback(() => {
    if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
    if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    
    setSystemStatus(prev => ({ ...prev, loading: true, nextRetryIn: 0 }));
    checkHealth(INITIAL_RETRY_DELAY, 0);
  }, [checkHealth]);

  // Health check inicial no mount
  useEffect(() => {
    checkHealth();
    
    return () => {
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    };
  }, [checkHealth]);

  // Carrega dados do usuário após autenticação (com proteção contra duplicatas)
  useEffect(() => {
    if (auth.isAuthenticated && !initialDataLoadedRef.current) {
      initialDataLoadedRef.current = true;
      // Batch das chamadas para reduzir re-renders
      Promise.all([
        credits.fetchBalance(),
        voiceProfiles.fetchProfiles()
      ]).catch(err => {
        console.error('[API] Erro ao carregar dados do usuário:', err);
      });
    }
    
    // Reset flag quando deslogar
    if (!auth.isAuthenticated) {
      initialDataLoadedRef.current = false;
    }
  }, [auth.isAuthenticated, credits.fetchBalance, voiceProfiles.fetchProfiles]);

  // Estado de erro global
  const [globalError, setGlobalError] = useState(null);
  
  // Handler de erro global (memoizado)
  const handleError = useCallback((error) => {
    console.error('[API Error]', error);
    setGlobalError(error.message || 'Ocorreu um erro');
    
    // Auto-clear após 5 segundos
    setTimeout(() => setGlobalError(null), 5000);
  }, []);

  // Limpa todos os erros (memoizado com refs corretas)
  const clearErrors = useCallback(() => {
    setGlobalError(null);
    if (auth.clearError) auth.clearError();
    if (credits.clearError) credits.clearError();
    if (voiceProfiles.clearError) voiceProfiles.clearError();
    if (synthesis.clearError) synthesis.clearError();
  }, [auth.clearError, credits.clearError, voiceProfiles.clearError, synthesis.clearError]);

  // Funções wrapper memoizadas para auth
  const wrappedLogin = useCallback(async (email, password) => {
    try {
      return await auth.login(email, password);
    } catch (error) {
      handleError(error);
      throw error;
    }
  }, [auth.login, handleError]);

  const wrappedRegister = useCallback(async (email, password, name) => {
    try {
      return await auth.register(email, password, name);
    } catch (error) {
      handleError(error);
      throw error;
    }
  }, [auth.register, handleError]);

  // Função wrapper memoizada para criar perfil
  const wrappedCreateProfile = useCallback(async (data) => {
    try {
      return await voiceProfiles.createProfile(data);
    } catch (error) {
      handleError(error);
      throw error;
    }
  }, [voiceProfiles.createProfile, handleError]);

  // Função wrapper memoizada para deletar perfil
  const wrappedDeleteProfile = useCallback(async (id) => {
    try {
      return await voiceProfiles.deleteProfile(id);
    } catch (error) {
      handleError(error);
      throw error;
    }
  }, [voiceProfiles.deleteProfile, handleError]);

  // Função wrapper memoizada para atualizar perfil
  const wrappedUpdateProfile = useCallback(async (id, data) => {
    try {
      return await voiceProfiles.updateProfile(id, data);
    } catch (error) {
      handleError(error);
      throw error;
    }
  }, [voiceProfiles.updateProfile, handleError]);

  // Função wrapper memoizada para síntese
  const wrappedGenerate = useCallback(async (params) => {
    try {
      const result = await synthesis.generate(params);
      // Debita créditos após síntese bem sucedida
      credits.deductCredits(params.creditsUsed || 1);
      return result;
    } catch (error) {
      handleError(error);
      throw error;
    }
  }, [synthesis.generate, credits.deductCredits, handleError]);

  // Value memoizado do contexto (CRÍTICO para evitar re-renders)
  const value = useMemo(() => ({
    // Auth com wrappers
    auth: {
      ...auth,
      login: wrappedLogin,
      register: wrappedRegister,
    },
    
    // Credits
    credits,
    
    // Voice Profiles com wrappers
    voiceProfiles: {
      ...voiceProfiles,
      createProfile: wrappedCreateProfile,
      updateProfile: wrappedUpdateProfile,
      deleteProfile: wrappedDeleteProfile,
    },
    
    // Synthesis com wrapper
    synthesis: {
      ...synthesis,
      generate: wrappedGenerate,
    },
    
    // System
    systemStatus,
    retryConnection,
    
    // Estado de erro global
    globalError,
    clearErrors,
    handleError,
  }), [
    auth,
    wrappedLogin,
    wrappedRegister,
    credits,
    voiceProfiles,
    wrappedCreateProfile,
    wrappedUpdateProfile,
    wrappedDeleteProfile,
    synthesis,
    wrappedGenerate,
    systemStatus,
    retryConnection,
    globalError,
    clearErrors,
    handleError,
  ]);

  return (
    <ApiContext.Provider value={value}>
      {children}
    </ApiContext.Provider>
  );
}

/**
 * Hook to use API context
 */
export function useApi() {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
}

export default ApiContext;
