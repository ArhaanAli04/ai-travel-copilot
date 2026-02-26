/**
 * API service for Local Discovery
 */

import { type SuggestRequest, type SuggestResponse, type ChatSession, type Message } from '../types/local-discovery';
import { getErrorMessage } from '../utils/error-messages';
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
// ✨ NEW: Timeout configuration
const API_TIMEOUT = 30000; // 30 seconds

// ✨ NEW: Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

/**
 * ✨ NEW: Fetch with timeout
 */
const fetchWithTimeout = async (
  url: string,
  options: RequestInit = {},
  timeout: number = API_TIMEOUT
): Promise<Response> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout. Please try again.');
    }
    throw error;
  }
};

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
  if (error.status >= 500) {
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
      const response = await fetchWithTimeout(`${API_BASE_URL}/local/suggest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        const errorMessage = error.detail || 'Failed to get suggestions';
        throw Object.assign(new Error(errorMessage), { status: response.status });
      }

      const data = await response.json();
      return data;
    } catch (error: any) {
      console.error('Error fetching suggestions:', error);
      // Throw with user-friendly message
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
  userId: string,
  feedbackType: 'thumbs_up' | 'thumbs_down' | 'rating',
  rating?: number,
  comment?: string,
  tags?: string[]
) => {
  return retryFetch(async () => {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/local/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          poi_id: poiId,
          user_id: userId,
          feedback_type: feedbackType,
          rating,
          visited_at: new Date().toISOString(),
          comment,
          tags,
        }),
      });

      if (!response.ok) {
        throw Object.assign(new Error('Failed to submit feedback'), { status: response.status });
      }

      return await response.json();
    } catch (error) {
      console.error('Error submitting feedback:', error);
      throw error;
    }
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
    try {
      const params = new URLSearchParams({
        city,
        limit: limit.toString(),
        min_feedback: '3',
        days: '30',
      });

      if (category) {
        params.append('category', category);
      }

      const response = await fetchWithTimeout(`${API_BASE_URL}/local/trending?${params}`);

      if (!response.ok) {
        throw Object.assign(new Error('Failed to fetch trending POIs'), { status: response.status });
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching trending POIs:', error);
      throw error;
    }
  });
};
/**
 * Create a new chat session
 * ✨ ENHANCED with retry logic
 */
export const createChatSession = async (
  userId: string,
  city: string,
  location: { lat: number; lon: number },
  title: string = 'New Chat'
): Promise<ChatSession> => {
  return retryFetch(async () => {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/chat/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          city,
          location,
          title,
        }),
      });

      if (!response.ok) {
        throw Object.assign(new Error('Failed to create chat session'), { status: response.status });
      }

      const data = await response.json();
      return parseSession(data.session);
    } catch (error: any) {
      console.error('Error creating chat session:', error);
      throw new Error(getErrorMessage(error));
    }
  });
};
/**
 * Get all chat sessions from backend
 * ✨ ENHANCED with retry logic
 */
export const getChatSessions = async (userId: string): Promise<ChatSession[]> => {
  return retryFetch(async () => {
    try {
      const response = await fetchWithTimeout(
        `${API_BASE_URL}/chat/sessions?user_id=${userId}&limit=50`
      );

      if (!response.ok) {
        throw Object.assign(new Error('Failed to fetch chat sessions'), { status: response.status });
      }

      const data = await response.json();
      return data.sessions.map(parseSession);
    } catch (error) {
      console.error('Error fetching chat sessions:', error);
      return []; // Return empty array on error instead of throwing
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
      const response = await fetchWithTimeout(`${API_BASE_URL}/chat/sessions/${sessionId}`);

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      return parseSession(data.session);
    } catch (error) {
      console.error('Error fetching chat session:', error);
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
      const response = await fetchWithTimeout(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw Object.assign(new Error('Failed to delete session'), { status: response.status });
      }
    } catch (error: any) {
      console.error('Error deleting session:', error);
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
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });

      if (!response.ok) {
        throw Object.assign(new Error('Failed to update session title'), { status: response.status });
      }
    } catch (error) {
      console.error('Error updating session title:', error);
      throw error;
    }
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
    try {
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

      const response = await fetchWithTimeout(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw Object.assign(new Error('Failed to update session context'), { status: response.status });
      }
      
      console.log('✅ Session context updated');
    } catch (error) {
      console.error('Error updating session context:', error);
      throw error;
    }
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
    try {
      const response = await fetchWithTimeout(
        `${API_BASE_URL}/chat/sessions/${sessionId}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            role: message.role,
            content: message.content,
            pois: message.pois,
            location: message.location,
            preferences: message.preferences,
          }),
        }
      );

      if (!response.ok) {
        throw Object.assign(new Error('Failed to add message'), { status: response.status });
      }
    } catch (error) {
      console.error('Error adding message:', error);
      throw error;
    }
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

/**
 * Get or create user ID (stored in localStorage)
 */
export const getUserId = (): string => {
  let userId = localStorage.getItem('local_discovery_user_id');
  
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('local_discovery_user_id', userId);
  }
  
  return userId;
};

export const saveUserPreferences = async (
  userId: string,
  preferences: import('../types/local-discovery').UserPreferences
): Promise<void> => {
  return retryFetch(async () => {
    try {
      const response = await fetchWithTimeout(`${API_BASE_URL}/local/preferences`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          preferences,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save preferences');
      }

      console.log('✅ Preferences saved to backend');
    } catch (error) {
      console.error('Error saving preferences:', error);
      throw error;
    }
  });
};

/**
 * Get user preferences from backend
 */
export const getUserPreferences = async (
  userId: string
): Promise<import('../types/local-discovery').UserPreferences> => {
  return retryFetch(async () => {
    try {
      const response = await fetchWithTimeout(
        `${API_BASE_URL}/local/preferences?user_id=${userId}`
      );

      if (!response.ok) {
        return {};
      }

      const data = await response.json();
      return data.preferences || {};
    } catch (error) {
      console.error('Error fetching preferences:', error);
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
    try {
      const response = await fetchWithTimeout(
        `${API_BASE_URL}/local/pois/${poiId}/photos`
      );

      if (!response.ok) {
        throw Object.assign(
          new Error('Failed to fetch POI photos'),
          { status: response.status }
        );
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching POI photos:', error);
      throw error;
    }
  });
};