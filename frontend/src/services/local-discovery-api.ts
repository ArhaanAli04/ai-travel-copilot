/**
 * API service for Local Discovery
 */
import api from './api';
import { type SuggestRequest, type SuggestResponse, type ChatSession, type Message } from '../types/local-discovery';
import { getErrorMessage } from '../utils/error-messages';


// ✨ NEW: Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second


/**
 * ✨ NEW: Retry wrapper for API calls
 */
const retryFetch = async <T>(
  fetchFn: () => Promise<T>,
  retries: number = MAX_RETRIES
): Promise<T> => {
  try {
    return await fetchFn();
  } catch (error: any) {
    if (retries > 0 && isRetryable(error)) {
      console.log(`⏳ Retrying... (${MAX_RETRIES - retries + 1}/${MAX_RETRIES})`);
      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY * (MAX_RETRIES - retries + 1)));
      return retryFetch(fetchFn, retries - 1);
    }
    throw error;
  }
};

/**
 * ✨ NEW: Check if error is retryable
 */
const isRetryable = (error: any): boolean => {
  // Network errors
  if (error.message?.includes('Failed to fetch') || error.message?.includes('Network')) {
    return true;
  }
  // Timeout errors
  if (error.message?.includes('timeout') || error.message?.includes('aborted')) {
    return true;
  }
  // 5xx server errors
  if (error.response?.status >= 500) {
    return true;
  }
  return false;
};

/**
 * Get personalized local recommendations
 *  ✨ ENHANCED with retry logic
 */
export const getSuggestions = async (request: SuggestRequest): Promise<SuggestResponse> => {
  return retryFetch(async () => {
    try {
      const response = await api.post('/local/suggest', request);
      return response.data;
    } catch (error: any) {
      throw new Error(getErrorMessage(error));
    }
  });
};

/**
 * Submit feedback for a POI
 * ✨ ENHANCED with retry logic
 */
export const submitFeedback = async (
  poiId: string,
  feedbackType: 'thumbs_up' | 'thumbs_down' | 'rating',
  rating?: number,
  comment?: string,
  tags?: string[]
) => {
  return retryFetch(async () => {
    const response = await api.post('/local/feedback', {
      poi_id: poiId,
      // user_id removed — backend reads from JWT
      feedback_type: feedbackType,
      rating,
      visited_at: new Date().toISOString(),
      comment,
      tags,
    });
    return response.data;
  });
};
/**
 * Get trending POIs
 * ✨ ENHANCED with retry logic
 */
export const getTrendingPOIs = async (
  city: string,
  category?: string,
  limit: number = 10
) => {
  return retryFetch(async () => {
    const params: Record<string, string> = {
      city,
      limit: limit.toString(),
      min_feedback: '3',
      days: '30',
    };
    if (category) params.category = category;
    const response = await api.get('/local/trending', { params });
    return response.data;
  });
};
/**
 * Create a new chat session
 * ✨ ENHANCED with retry logic
 */
export const createChatSession = async (
  city: string,
  location: { lat: number; lon: number },
  title: string = 'New Chat'
): Promise<ChatSession> => {
  return retryFetch(async () => {
    try {
      const response = await api.post('/chat/sessions', {
        // user_id removed — backend reads from JWT
        city,
        location,
        title,
      });
      return parseSession(response.data.session);
    } catch (error: any) {
      throw new Error(getErrorMessage(error));
    }
  });
};
/**
 * Get all chat sessions from backend
 * ✨ ENHANCED with retry logic
 */
export const getChatSessions = async (): Promise<ChatSession[]> => {
  return retryFetch(async () => {
    try {
      const response = await api.get('/chat/sessions', { params: { limit: 50 } });
      return response.data.sessions.map(parseSession);
    } catch {
      return [];
    }
  });
};
/**
 * Get a specific chat session
 * ✨ ENHANCED with retry logic
 */
export const getChatSession = async (sessionId: string): Promise<ChatSession | null> => {
  return retryFetch(async () => {
    try {
      const response = await api.get(`/chat/sessions/${sessionId}`);
      return parseSession(response.data.session);
    } catch {
      return null;
    }
  });
};
/**
 * Delete chat session
 * ✨ ENHANCED with retry logic
 */
export const deleteChatSession = async (sessionId: string): Promise<void> => {
  return retryFetch(async () => {
   try {
      await api.delete(`/chat/sessions/${sessionId}`);
    } catch (error: any) {
      throw new Error(getErrorMessage(error));
    }
  });
};
/**
 * Update session title based on first user message
 * ✨ ENHANCED with retry logic
 */
export const updateSessionTitle = async (
  sessionId: string,
  title: string
): Promise<void> => {
  return retryFetch(async () => {
    await api.put(`/chat/sessions/${sessionId}`, { title });
  });
};
/**
 * Update session context (manual location/time overrides)
 * ✨ ENHANCED with retry logic
 */
export const updateSessionContext = async (
  sessionId: string,
  manualLocation?: { lat: number; lon: number } | null,
  manualCity?: string | null,
  manualTime?: string | null
): Promise<void> => {
  return retryFetch(async () => {
      const body: any = {};
      if (manualLocation !== undefined) {
        body.manual_location = manualLocation;
      }
      if (manualCity !== undefined) {
        body.manual_city = manualCity;
      }
      if (manualTime !== undefined) {
        body.manual_time = manualTime;
      }
      await api.put(`/chat/sessions/${sessionId}`, body);
  });
};
/**
 * Add message to session
 * ✨ ENHANCED with retry logic
 */
export const addMessageToSession = async (
  sessionId: string,
  message: Message
): Promise<void> => {
  return retryFetch(async () => {
    await api.post(`/chat/sessions/${sessionId}/messages`, {
      role: message.role,
      content: message.content,
      pois: message.pois,
      location: message.location,
      preferences: message.preferences,
    });
  });
};

const parseSession = (session: any): ChatSession => {
  // Parse dates properly - handle both ISO strings and Date objects
  const parseDate = (dateValue: any): Date => {
    if (!dateValue) return new Date();
    if (dateValue instanceof Date) return dateValue;
    // If it's a string, parse it
    const parsed = new Date(dateValue);
    
    // Check if valid date
    if (isNaN(parsed.getTime())) {
      console.warn('Invalid date:', dateValue);
      return new Date();
    }
    
    return parsed;
  };

  return {
    ...session,
    created_at: parseDate(session.created_at),
    updated_at: parseDate(session.updated_at),
    messages: session.messages.map((msg: any) => ({
      ...msg,
      timestamp: parseDate(msg.timestamp),
    })),
  };
};

export const saveUserPreferences = async (
  preferences: import('../types/local-discovery').UserPreferences
): Promise<void> => {
  return retryFetch(async () => {
    await api.post('/local/preferences', { preferences });
  });
};

/**
 * Get user preferences from backend
 */
export const getUserPreferences = async (): Promise<import('../types/local-discovery').UserPreferences> => {
  return retryFetch(async () => {
    try {
      const response = await api.get('/local/preferences');
      return response.data.preferences || {};
    } catch {
      return {};
    }
  });
};
/**
 * Get photos for a POI
 * Tries Wikimedia Commons first, falls back to Unsplash
 */
export const getPOIPhotos = async (
  poiId: string
): Promise<import('../types/local-discovery').POIPhotosResponse> => {
  return retryFetch(async () => {
    const response = await api.get(`/local/pois/${poiId}/photos`);
    return response.data;
  });
};