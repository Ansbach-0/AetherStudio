/**
 * System API - Health checks and system status
 */

import apiClient from './client';

/**
 * Health Check API
 */
export const healthApi = {
  /**
   * Basic health check
   */
  check: () => apiClient.get('/health'),

  /**
   * Detailed health with GPU status
   */
  detailed: async () => {
    try {
      const [health, gpu] = await Promise.all([
        apiClient.get('/health'),
        apiClient.get('/health/gpu').catch(() => ({ available: false }))
      ]);
      return {
        ...health,
        gpu
      };
    } catch {
      return {
        status: 'unhealthy',
        gpu: { available: false }
      };
    }
  },

  /**
   * Get GPU information
   */
  gpuInfo: () => apiClient.get('/health/gpu'),

  /**
   * Readiness check
   */
  ready: () => apiClient.get('/health/ready'),
};

/**
 * Background Tasks API
 */
export const tasksApi = {
  /**
   * Get status of a task
   */
  getStatus: (taskId) => apiClient.get(`/api/v1/tasks/${taskId}`),

  /**
   * List active tasks
   */
  list: () => apiClient.get('/api/v1/tasks'),

  /**
   * Cancel a task
   */
  cancel: (taskId) => apiClient.post(`/api/v1/tasks/${taskId}/cancel`),
};

/**
 * Payment API (Placeholder)
 */
export const paymentApi = {
  /**
   * Get available plans
   */
  getPlans: () => apiClient.get('/api/v1/payments/plans'),

  /**
   * Create checkout session
   */
  createCheckout: (planId) => apiClient.post('/api/v1/payments/checkout', { plan_id: planId }),

  /**
   * Get user transactions
   */
  getTransactions: () => apiClient.get('/api/v1/payments/transactions'),
};

export default {
  health: healthApi,
  tasks: tasksApi,
  payment: paymentApi,
};
