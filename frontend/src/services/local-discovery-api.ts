/**
 * API service for Local Discovery
 */

import { type SuggestRequest, type SuggestResponse, type ChatSession, type Message } from '../types/local-discovery';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Get personalized local recommendations
 */
export const getSuggestions = async (request: SuggestRequest): Promise<SuggestResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/local/suggest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get suggestions');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching suggestions:', error);
    throw error;
  }
};

/**
 * Submit feedback for a POI
 */
export const submitFeedback = async (
  poiId: string,
  userId: string,
  feedbackType: 'thumbs_up' | 'thumbs_down' | 'rating',
  rating?: number,
  comment?: string,
  tags?: string[]
) => {
  try {
    const response = await fetch(`${API_BASE_URL}/local/feedback`, {
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
      throw new Error('Failed to submit feedback');
    }

    return await response.json();
  } catch (error) {
    console.error('Error submitting feedback:', error);
    throw error;
  }
};

/**
 * Get trending POIs
 */
export const getTrendingPOIs = async (
  city: string,
  category?: string,
  limit: number = 10
) => {
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

    const response = await fetch(`${API_BASE_URL}/local/trending?${params}`);

    if (!response.ok) {
      throw new Error('Failed to fetch trending POIs');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching trending POIs:', error);
    throw error;
  }
};


/**
 * Create a new chat session
 */
export const createChatSession = async (
  userId: string,
  city: string,
  location: { lat: number; lon: number },
  title: string = 'New Chat'
): Promise<ChatSession> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
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
      throw new Error('Failed to create chat session');
    }

    const data = await response.json();
    return parseSession(data.session);
  } catch (error) {
    console.error('Error creating chat session:', error);
    throw error;
  }
};
/**
 * Get all chat sessions from localStorage
 */
export const getChatSessions = async (userId: string): Promise<ChatSession[]> => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/chat/sessions?user_id=${userId}&limit=50`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch chat sessions');
    }

    const data = await response.json();
    return data.sessions.map(parseSession);
  } catch (error) {
    console.error('Error fetching chat sessions:', error);
    return [];
  }
};
/**
 * Get a specific chat session
 */
export const getChatSession = async (sessionId: string): Promise<ChatSession | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`);

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    return parseSession(data.session);
  } catch (error) {
    console.error('Error fetching chat session:', error);
    return null;
  }
};
/**
 * Save chat session
 */

/**
 * Delete chat session
 */
export const deleteChatSession = async (sessionId: string): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete session');
    }
  } catch (error) {
    console.error('Error deleting session:', error);
    throw error;
  }
};
/**
 * Update session title based on first user message
 */
export const updateSessionTitle = async (
  sessionId: string,
  title: string
): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title }),
    });

    if (!response.ok) {
      throw new Error('Failed to update session title');
    }
  } catch (error) {
    console.error('Error updating session title:', error);
    throw error;
  }
};

/**
 * Update session context (manual location/time overrides)
 */
export const updateSessionContext = async (
  sessionId: string,
  manualLocation?: { lat: number; lon: number } | null,
  manualCity?: string | null,
  manualTime?: string | null
): Promise<void> => {
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

    const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error('Failed to update session context');
    }
    
    console.log('✅ Session context updated');
  } catch (error) {
    console.error('Error updating session context:', error);
    throw error;
  }
};
/**
 * Add message to session
 */
export const addMessageToSession = async (
  sessionId: string,
  message: Message
): Promise<void> => {
  try {
    const response = await fetch(
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
      throw new Error('Failed to add message');
    }
  } catch (error) {
    console.error('Error adding message:', error);
    throw error;
  }
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
  try {
    const response = await fetch(`${API_BASE_URL}/local/preferences`, {
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
};

/**
 * Get user preferences from backend
 */
export const getUserPreferences = async (
  userId: string
): Promise<import('../types/local-discovery').UserPreferences> => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/local/preferences?user_id=${userId}`
    );

    if (!response.ok) {
      return {}; // Return empty preferences if not found
    }

    const data = await response.json();
    return data.preferences || {};
  } catch (error) {
    console.error('Error fetching preferences:', error);
    return {};
  }
};