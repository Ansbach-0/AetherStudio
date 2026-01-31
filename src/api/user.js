/**
 * User API - Authentication and user management
 */

import apiClient, { setAuthToken } from './client';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Authentication API
 */
export const authApi = {
  /**
   * Register new user
   * @param {Object} data - Registration data
   * @param {string} data.email - User email
   * @param {string} data.password - User password
   * @param {string} [data.name] - User display name
   */
  register: async (data) => {
    const response = await apiClient.post('/api/v1/users/register', {
      email: data.email,
      password: data.password,
      name: data.name,
    });
    
    // Auto-store token on successful registration
    if (response.access_token) {
      setAuthToken(response.access_token);
    }
    
    return response;
  },

  /**
   * Login user
   * @param {Object} data - Login credentials
   * @param {string} data.email - User email
   * @param {string} data.password - User password
   */
  login: async (data) => {
    // OAuth2 form format
    const formData = new URLSearchParams();
    formData.append('username', data.email);
    formData.append('password', data.password);

    const response = await fetch(
      `${API_URL}/api/v1/users/login`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Login failed');
    }

    const result = await response.json();
    
    if (result.access_token) {
      setAuthToken(result.access_token);
      // Store user data
      if (result.user) {
        localStorage.setItem('user_data', JSON.stringify(result.user));
      }
    }
    
    return result;
  },

  /**
   * Logout user
   */
  logout: () => {
    setAuthToken(null);
    localStorage.removeItem('user_data');
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: () => !!localStorage.getItem('auth_token'),

  /**
   * Get stored token
   */
  getToken: () => localStorage.getItem('auth_token'),
};

/**
 * User Profile API
 */
export const userApi = {
  /**
   * Get current user profile
   */
  getProfile: () => apiClient.get('/api/v1/users/me'),

  /**
   * Update user profile
   */
  updateProfile: (data) => apiClient.patch('/api/v1/users/me', data),

  /**
   * Delete user account
   */
  deleteAccount: () => apiClient.delete('/api/v1/users/me'),
};

/**
 * Credits API
 */
export const creditsApi = {
  /**
   * Get current credits balance
   */
  getBalance: () => apiClient.get('/api/v1/users/credits'),

  /**
   * Get credits usage history
   */
  getHistory: (params = {}) => {
    const query = new URLSearchParams();
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);
    
    const queryStr = query.toString();
    return apiClient.get(`/api/v1/users/credits/history${queryStr ? `?${queryStr}` : ''}`);
  },
};

/**
 * API Key Management
 */
export const apiKeyApi = {
  /**
   * Generate new API key
   * @returns {Promise<{api_key: string, message: string}>}
   */
  generate: () => apiClient.post('/api/v1/users/api-key/generate'),

  /**
   * Revoke current API key
   */
  revoke: () => apiClient.delete('/api/v1/users/api-key'),
};

export default {
  auth: authApi,
  user: userApi,
  credits: creditsApi,
  apiKey: apiKeyApi,
};
