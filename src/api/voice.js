/**
 * Voice API - Voice profile and synthesis endpoints
 */

import apiClient from './client';

const getUserId = () => {
  const raw = localStorage.getItem('user_data');
  if (!raw) return null;
  try {
    return JSON.parse(raw)?.id ?? null;
  } catch {
    return null;
  }
};

const withUserId = (endpoint) => {
  const userId = getUserId();
  if (!userId) return endpoint;
  const separator = endpoint.includes('?') ? '&' : '?';
  return `${endpoint}${separator}user_id=${encodeURIComponent(userId)}`;
};

/**
 * Voice Profiles API
 */
export const voiceProfilesApi = {
  /**
   * List all voice profiles for current user
   */
  list: () => apiClient.get('/api/v1/voice/profiles'),

  /**
   * Get a specific voice profile
   */
  get: (profileId) => apiClient.get(withUserId(`/api/v1/voice/profiles/${profileId}`)),

  /**
   * Create new voice profile with reference audio
   * @param {Object} data - Profile data
   * @param {string} data.name - Profile name
   * @param {File} data.referenceAudio - WAV audio file
   * @param {string} data.referenceText - Transcription of reference audio
   * @param {string} [data.language] - Language code (auto-detected if omitted)
   * @param {string} [data.description] - Optional description
   */
  create: async (data) => {
    const formData = new FormData();
    formData.append('name', data.name);
    formData.append('reference_audio', data.referenceAudio);
    formData.append('reference_text', data.referenceText);
    
    if (data.language) {
      formData.append('language', data.language);
    }
    if (data.description) {
      formData.append('description', data.description);
    }

    return apiClient.upload(withUserId('/api/v1/voice/profiles'), formData);
  },

  /**
   * Update voice profile
   */
  update: (profileId, data) => 
    apiClient.patch(withUserId(`/api/v1/voice/profiles/${profileId}`), data),

  /**
   * Delete voice profile
   */
  delete: (profileId) => 
    apiClient.delete(withUserId(`/api/v1/voice/profiles/${profileId}`)),
};

/**
 * Voice Synthesis API
 */
export const synthesisApi = {
  /**
   * Generate speech using voice profile
   * @param {Object} data - Synthesis parameters
   * @param {string} data.profileId - Voice profile ID
   * @param {string} data.text - Text to synthesize
   * @param {string} [data.emotion] - Emotion preset
   * @param {number} [data.speed] - Speech speed (0.5-2.0)
   * @returns {Promise<Blob>} Audio blob
   */
  generate: async (data) => {
    const response = await apiClient.post(withUserId('/api/v1/voice/pipeline'), {
      profile_id: data.profileId,
      text: data.text,
      emotion: data.emotion || 'neutral',
      speed: data.speed || 1.0,
      apply_rvc: data.applyRvc ?? true,
    }, { timeout: 120000 }); // 2 min for synthesis

    return response;
  },

  /**
   * Quick synthesis without profile (using hybrid pipeline)
   * @param {Object} data - Synthesis parameters
   * @param {File} data.referenceAudio - Reference audio file
   * @param {string} data.referenceText - Reference transcription
   * @param {string} data.text - Text to synthesize
   * @returns {Promise<Blob>} Audio blob
   */
  quickGenerate: async (data) => {
    const response = await apiClient.post(withUserId('/api/v1/voice/clone'), {
      profile_id: data.profileId,
      text: data.text,
      language: data.language,
      speed: data.speed,
    }, { timeout: 180000 }); // 3 min for quick synthesis

    return response;
  },

  /**
   * Preview synthesis (lower quality, faster)
   */
  preview: async (data) => {
    return apiClient.post(withUserId('/api/v1/voice/clone'), {
      profile_id: data.profileId,
      text: data.text.slice(0, 100), // Limit preview text
      language: data.language,
      speed: data.speed,
    }, { timeout: 30000 });
  },
};

/**
 * Language Detection API
 */
export const languageApi = {
  /**
   * Detect language from text
   */
  detect: async () => {
    const result = await apiClient.get('/api/v1/voice/pipeline/languages');
    const language = result?.languages?.[0] || null;
    return { language };
  },

  /**
   * Get supported languages
   */
  list: () => apiClient.get('/api/v1/voice/pipeline/languages'),
};

/**
 * RVC Voice Conversion API
 */
export const rvcApi = {
  /**
   * Get available RVC models
   */
  listModels: () => apiClient.get('/api/v1/voice/pipeline/emotions'),

  /**
   * Apply RVC conversion to audio
   * @param {Object} data - Conversion parameters
   * @param {File} data.audio - Input audio file
   * @param {string} data.modelId - RVC model ID
   * @param {number} [data.pitchShift] - Pitch shift in semitones
   */
  convert: async (data) => {
    const formData = new FormData();
    formData.append('audio_file', data.audio);
    formData.append('profile_id', data.modelId);
    
    if (data.pitchShift !== undefined) {
      formData.append('pitch_shift', data.pitchShift.toString());
    }

    return apiClient.upload(withUserId('/api/v1/voice/convert'), formData, {
      timeout: 120000,
    });
  },
};

export default {
  profiles: voiceProfilesApi,
  synthesis: synthesisApi,
  language: languageApi,
  rvc: rvcApi,
};
