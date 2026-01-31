/**
 * API Client - Centralized HTTP client for backend communication
 * Uses native fetch with interceptors-like behavior
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Get auth token from localStorage
 */
const getAuthToken = () => localStorage.getItem('auth_token');

/**
 * Set auth token in localStorage
 */
export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
};

/**
 * Build headers for requests
 */
const buildHeaders = (customHeaders = {}, isFormData = false) => {
  const headers = {
    ...customHeaders,
  };

  // Don't set Content-Type for FormData (browser sets it with boundary)
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }

  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
};

/**
 * Handle API response
 */
const handleResponse = async (response) => {
  // Handle no content response
  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get('content-type');
  
  // Handle blob responses (audio files)
  if (contentType?.includes('audio/')) {
    if (!response.ok) {
      throw new ApiError('Failed to fetch audio', response.status);
    }
    return response.blob();
  }

  // Try to parse JSON
  let data;
  try {
    data = await response.json();
  } catch {
    if (!response.ok) {
      throw new ApiError('Request failed', response.status);
    }
    return null;
  }

  // Handle error responses
  if (!response.ok) {
    const message = data?.detail || data?.message || 'Request failed';
    throw new ApiError(message, response.status, data);
  }

  return data;
};

/**
 * Main request function
 */
const request = async (endpoint, options = {}) => {
  const {
    method = 'GET',
    body,
    headers = {},
    isFormData = false,
    timeout = 30000,
  } = options;

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      method,
      headers: buildHeaders(headers, isFormData),
      body: isFormData ? body : body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return await handleResponse(response);

  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new ApiError('Request timeout', 408);
    }
    
    if (error instanceof ApiError) {
      throw error;
    }

    // Network error
    throw new ApiError('Network error - server may be offline', 0);
  }
};

/**
 * API client methods
 */
export const apiClient = {
  get: (endpoint, options = {}) => 
    request(endpoint, { ...options, method: 'GET' }),

  post: (endpoint, body, options = {}) => 
    request(endpoint, { ...options, method: 'POST', body }),

  put: (endpoint, body, options = {}) => 
    request(endpoint, { ...options, method: 'PUT', body }),

  patch: (endpoint, body, options = {}) => 
    request(endpoint, { ...options, method: 'PATCH', body }),

  delete: (endpoint, options = {}) => 
    request(endpoint, { ...options, method: 'DELETE' }),

  /**
   * Upload file with form data
   */
  upload: (endpoint, formData, options = {}) =>
    request(endpoint, { 
      ...options, 
      method: 'POST', 
      body: formData, 
      isFormData: true,
      timeout: 120000, // 2 min for uploads
    }),
};

export default apiClient;
