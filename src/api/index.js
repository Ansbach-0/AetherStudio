/**
 * API Module Index
 * Centralized exports for all API modules
 */

export { default as apiClient, ApiError, setAuthToken } from './client';
export { voiceProfilesApi, synthesisApi, languageApi, rvcApi } from './voice';
export { authApi, userApi, creditsApi } from './user';
export { healthApi, tasksApi, paymentApi } from './system';

// Default export with all APIs
import voiceApi from './voice';
import userApiModule from './user';
import systemApi from './system';

const api = {
  voice: voiceApi,
  user: userApiModule,
  system: systemApi,
};

export default api;
