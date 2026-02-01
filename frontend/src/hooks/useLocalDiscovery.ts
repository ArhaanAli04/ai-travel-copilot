/**
 * Custom hook for Local Discovery chat management
 */

import { useState, useEffect, useCallback } from 'react';
import type {
  ChatSession,
  Message,
  Location,
  UserPreferences,
  ContextChip,
} from '../types/local-discovery';
import {
  getChatSessions,
  createChatSession,
  getChatSession,
  addMessageToSession,
  deleteChatSession,
  getSuggestions,
  getUserId,
  submitFeedback,
} from '../services/local-discovery-api';
import { getCurrentLocation, getMockLocation } from '../utils/geolocation';
import { getTimeOfDay, getGreeting } from '../utils/datetime';
import { generateMockResponse } from '../utils/mock-data';

export const useLocalDiscovery = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<Location | null>(null);
  const [city, setCity] = useState<string>('mumbai');
  const [contextChips, setContextChips] = useState<ContextChip[]>([]);
  const [preferences, setPreferences] = useState<UserPreferences>({});
  const [userId] = useState(getUserId());

  // Initialize: Load location and sessions
  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    setLoading(true);
    try {
      // Get user location
      await loadUserLocation();

      // Load chat sessions
      await loadSessions();
    } catch (err) {
      console.error('Initialization error:', err);
      setError('Failed to initialize app');
    } finally {
      setLoading(false);
    }
  };

  const loadUserLocation = async () => {
    try {
      const result = await getCurrentLocation();
      setUserLocation(result.location);
      setCity(result.city);
      updateLocationChip(result.location, result.city);
    } catch (err) {
      console.warn('Using mock location:', err);
      // Fallback to mock location
      const mock = getMockLocation('mumbai');
      setUserLocation(mock.location);
      setCity(mock.city);
      updateLocationChip(mock.location, mock.city);
    }
  };

  const loadSessions = async () => {
    try {
      const fetchedSessions = await getChatSessions(userId);
      setSessions(fetchedSessions);

      // Set most recent session as active if none selected
      if (!activeSession && fetchedSessions.length > 0) {
        setActiveSession(fetchedSessions[0]);
      }
    } catch (err) {
      console.error('Error loading sessions:', err);
    }
  };

  const updateLocationChip = (location: Location, cityName: string) => {
    setContextChips((prev) => {
      const filtered = prev.filter((chip) => chip.type !== 'location');
      return [
        ...filtered,
        {
          id: 'location',
          label: 'Location',
          value: cityName.charAt(0).toUpperCase() + cityName.slice(1),
          type: 'location',
          removable: false,
        },
        {
          id: `time-${Date.now()}`,
          label: 'Time',
          value: getTimeOfDay(),
          type: 'time',
          removable: false,
        },
      ];
    });
  };

  const createNewSession = async () => {
    if (!userLocation) {
      setError('Location not available');
      return;
    }

    setLoading(true);
    try {
      const newSession = await createChatSession(userId, city, userLocation);

      // Add welcome message
      const welcomeMessage: Message = {
        id: `${newSession.id}_0`,
        role: 'assistant',
        content: `${getGreeting()}! 👋 I'm your local discovery assistant. I can help you find amazing places around ${city}.

Try asking me things like:
• "Find me a cozy cafe for working"
• "Best restaurants for dinner tonight"
• "Where can I get authentic street food?"

What are you looking for today?`,
        timestamp: new Date(),
      };

      await addMessageToSession(newSession.id, welcomeMessage);

      // Reload session with message
      const updatedSession = await getChatSession(newSession.id);
      if (updatedSession) {
        setSessions((prev) => [updatedSession, ...prev]);
        setActiveSession(updatedSession);
      }
    } catch (err) {
      console.error('Error creating session:', err);
      setError('Failed to create new chat');
    } finally {
      setLoading(false);
    }
  };

  const selectSession = async (sessionId: string) => {
    const session = sessions.find((s) => s.id === sessionId);
    if (session) {
      setActiveSession(session);
    } else {
      // Fetch from backend if not in local state
      const fetchedSession = await getChatSession(sessionId);
      if (fetchedSession) {
        setActiveSession(fetchedSession);
      }
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await deleteChatSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));

      if (activeSession?.id === sessionId) {
        setActiveSession(sessions[0] || null);
      }
    } catch (err) {
      console.error('Error deleting session:', err);
      setError('Failed to delete chat');
    }
  };

  const sendMessage = async (content: string, useMock: boolean = false) => {
    if (!activeSession || !userLocation) {
      setError('No active session or location');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Add user message
      const userMessage: Message = {
        id: `${activeSession.id}_${activeSession.messages.length}`,
        role: 'user',
        content,
        timestamp: new Date(),
        location: userLocation,
        preferences,
      };

      await addMessageToSession(activeSession.id, userMessage);

      // Update local state
      const updatedSession = {
        ...activeSession,
        messages: [...activeSession.messages, userMessage],
        updated_at: new Date(),
      };
      setActiveSession(updatedSession);
      updateSessionInList(updatedSession);

      // Get AI response
      let assistantMessage: Message;

      if (useMock) {
        // Use mock response for testing
        assistantMessage = generateMockResponse(content);
      } else {
        // Call real API
        const response = await getSuggestions({
          query: content,
          user_location: userLocation,
          city,
          preferences,
          radius_km: 5,
          max_results: 5,
        });

        assistantMessage = {
          id: `${activeSession.id}_${activeSession.messages.length + 1}`,
          role: 'assistant',
          content: `I found ${response.recommendations.length} great options for you:`,
          pois: response.recommendations,
          timestamp: new Date(),
        };
      }

      await addMessageToSession(activeSession.id, assistantMessage);

      // Update local state with assistant message
      const finalSession = {
        ...updatedSession,
        messages: [...updatedSession.messages, assistantMessage],
      };
      setActiveSession(finalSession);
      updateSessionInList(finalSession);
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const updateSessionInList = (updatedSession: ChatSession) => {
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== updatedSession.id);
      return [updatedSession, ...filtered];
    });
  };

  const addPreference = (key: keyof UserPreferences, value: any) => {
    setPreferences((prev) => ({
      ...prev,
      [key]: value,
    }));

    // Add context chip
    const chipId = `pref_${key}`;
    const chipValue = Array.isArray(value) ? value.join(', ') : value.toString();

    setContextChips((prev) => {
      const filtered = prev.filter((chip) => chip.id !== chipId);
      return [
        ...filtered,
        {
          id: chipId,
          label: key.charAt(0).toUpperCase() + key.slice(1),
          value: chipValue,
          type: 'preference',
          removable: true,
        },
      ];
    });
  };

  const removePreference = (chipId: string) => {
    setContextChips((prev) => prev.filter((chip) => chip.id !== chipId));

    // Extract preference key from chip ID
    const key = chipId.replace('pref_', '') as keyof UserPreferences;
    setPreferences((prev) => {
      const updated = { ...prev };
      delete updated[key];
      return updated;
    });
  };
  const handleFeedback = async (
      poiId: string,
      feedbackType: 'thumbs_up' | 'thumbs_down'
    ) => {
      try {
        await submitFeedback(
          poiId,
          userId,
          feedbackType,
          feedbackType === 'thumbs_up' ? 5 : 1, // rating: 5 for thumbs up, 1 for thumbs down
          undefined, // comment
          [] // tags
        );
        console.log(`✅ Feedback submitted: ${feedbackType} for POI ${poiId}`);
      } catch (err) {
        console.error('Error submitting feedback:', err);
        setError('Failed to submit feedback');
      }
    };
  return {
    // State
    sessions,
    activeSession,
    loading,
    error,
    userLocation,
    city,
    contextChips,
    preferences,

    // Actions
    createNewSession,
    selectSession,
    deleteSession,
    sendMessage,
    addPreference,
    removePreference,
    refreshSessions: loadSessions,
    handleFeedback,
  };
};
