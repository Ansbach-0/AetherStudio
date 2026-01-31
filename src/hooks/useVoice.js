/**
 * useVoice Hook - Voice profile and synthesis state management
 */

import { useState, useCallback, useRef } from 'react';
import { voiceProfilesApi, synthesisApi, languageApi } from '../api';

/**
 * Hook for managing voice profiles
 */
export function useVoiceProfiles() {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchProfiles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await voiceProfilesApi.list();
      setProfiles(data || []);
      return data;
    } catch (err) {
      setError(err.message);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const createProfile = useCallback(async (profileData) => {
    setLoading(true);
    setError(null);
    try {
      const newProfile = await voiceProfilesApi.create(profileData);
      setProfiles((prev) => [...prev, newProfile]);
      return newProfile;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateProfile = useCallback(async (id, data) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await voiceProfilesApi.update(id, data);
      setProfiles((prev) =>
        prev.map((p) => (p.id === id ? { ...p, ...updated } : p))
      );
      return updated;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteProfile = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      await voiceProfilesApi.delete(id);
      setProfiles((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    profiles,
    loading,
    error,
    fetchProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
    clearError: () => setError(null),
  };
}

/**
 * Hook for voice synthesis
 */
export function useVoiceSynthesis() {
  const [generating, setGenerating] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const audioRef = useRef(null);

  const generate = useCallback(async (params) => {
    setGenerating(true);
    setError(null);
    setProgress(10);

    // Cleanup previous audio
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }

    try {
      setProgress(30);
      const response = await synthesisApi.generate(params);
      setProgress(80);

      // Handle blob or JSON response
      let blob;
      if (response instanceof Blob) {
        blob = response;
      } else if (response.audio_url) {
        // If backend returns URL, fetch the audio
        const audioResponse = await fetch(response.audio_url);
        blob = await audioResponse.blob();
      } else if (response.audio_base64) {
        // Handle base64 response
        const byteCharacters = atob(response.audio_base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        blob = new Blob([new Uint8Array(byteNumbers)], { type: 'audio/wav' });
      } else {
        throw new Error('Invalid response format');
      }

      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      setProgress(100);
      return url;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setGenerating(false);
    }
  }, [audioUrl]);

  const quickGenerate = useCallback(async (params) => {
    setGenerating(true);
    setError(null);
    setProgress(10);

    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }

    try {
      setProgress(30);
      const response = await synthesisApi.quickGenerate(params);
      setProgress(80);

      let blob;
      if (response instanceof Blob) {
        blob = response;
      } else if (response.audio_base64) {
        const byteCharacters = atob(response.audio_base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        blob = new Blob([new Uint8Array(byteNumbers)], { type: 'audio/wav' });
      } else {
        throw new Error('Invalid response format');
      }

      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      setProgress(100);
      return url;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setGenerating(false);
    }
  }, [audioUrl]);

  const cleanup = useCallback(() => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setProgress(0);
    setError(null);
  }, [audioUrl]);

  return {
    generating,
    audioUrl,
    error,
    progress,
    audioRef,
    generate,
    quickGenerate,
    cleanup,
    clearError: () => setError(null),
  };
}

/**
 * Hook for language detection
 */
export function useLanguageDetection() {
  const [detecting, setDetecting] = useState(false);
  const [detectedLanguage, setDetectedLanguage] = useState(null);
  const [supportedLanguages, setSupportedLanguages] = useState([]);
  const [error, setError] = useState(null);

  const detect = useCallback(async (text) => {
    if (!text?.trim()) {
      setDetectedLanguage(null);
      return null;
    }

    setDetecting(true);
    setError(null);
    try {
      const result = await languageApi.detect(text);
      setDetectedLanguage(result.language);
      return result.language;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setDetecting(false);
    }
  }, []);

  const fetchLanguages = useCallback(async () => {
    try {
      const data = await languageApi.list();
      setSupportedLanguages(data || []);
      return data;
    } catch (err) {
      setError(err.message);
      return [];
    }
  }, []);

  return {
    detecting,
    detectedLanguage,
    supportedLanguages,
    error,
    detect,
    fetchLanguages,
    clearError: () => setError(null),
  };
}

export default {
  useVoiceProfiles,
  useVoiceSynthesis,
  useLanguageDetection,
};
