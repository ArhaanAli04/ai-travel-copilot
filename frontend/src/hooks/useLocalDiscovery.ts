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
  saveUserPreferences,
  getUserPreferences,
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
  const [currentTime, setCurrentTime] = useState(getTimeOfDay());
  // Initialize: Load location and sessions
  useEffect(() => {
    initializeApp();
  }, []);

  useEffect(() => {
    const updateTime = () => {
      const newTime = getTimeOfDay();
      setCurrentTime(newTime);
      
      // Update time chip
      setContextChips((prev) => {
        const filtered = prev.filter((chip) => chip.type !== 'time');
        return [
          ...filtered,
          {
            id: 'time',
            label: 'Time',
            value: newTime,
            type: 'time',
            removable: false,
            icon: '🕐',
          },
        ];
      });
    };

  // Update time every minute
  const interval = setInterval(updateTime, 60000); // 60 seconds

  return () => clearInterval(interval);
}, []);
  const initializeApp = async () => {
    setLoading(true);
    try {
      // Get user location
      await loadUserLocation();

      //load saved preferences
      await loadUserPreferences();
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
      // ✅ Keep only preference chips, remove ALL location and time chips
      const preferenceChips = prev.filter(
        (chip) => chip.type !== 'location' && chip.type !== 'time'
      );
      
      return [
        {
          id: 'location',
          label: 'Location',
          value: cityName.charAt(0).toUpperCase() + cityName.slice(1),
          type: 'location',
          removable: false,
          icon: '📍',
        },
        {
          id: 'time',
          label: 'Time',
          value: getTimeOfDay(),
          type: 'time',
          removable: false,
          icon: '🕐',
        },
        ...preferenceChips, // ✅ Add preference chips back at the end
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

  const addPreference =async (key: keyof UserPreferences, value: any) => {
    const updatedPreferences = {
      ...preferences,
      [key]: value,
    };
    
    setPreferences(updatedPreferences);

    // ✅ Save to backend
    try {
      await saveUserPreferences(userId, updatedPreferences);
    } catch (err) {
      console.error('Failed to save preferences:', err);
      setError('Failed to save preferences');
    }

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

  const removePreference =async (chipId: string) => {
    setContextChips((prev) => prev.filter((chip) => chip.id !== chipId));

    // Extract preference key from chip ID
    const key = chipId.replace('pref_', '') as keyof UserPreferences;
    const updatedPreferences = { ...preferences };
    delete updatedPreferences[key];
    setPreferences(updatedPreferences);
    
    // ✅ Save to backend
    try {
      await saveUserPreferences(userId, updatedPreferences);
    } catch (err) {
      console.error('Failed to save preferences:', err);
    }
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

  const loadUserPreferences = async () => {
  try {
    const savedPreferences = await getUserPreferences(userId);
    
    if (Object.keys(savedPreferences).length > 0) {
      setPreferences(savedPreferences);
      updatePreferenceChips(savedPreferences);
      console.log('✅ Loaded saved preferences:', savedPreferences);
    }
  } catch (err) {
    console.error('Error loading preferences:', err);
  }
};

const updatePreferenceChips = (prefs: UserPreferences) => {
  const chips: ContextChip[] = [];
  
  if (prefs.dietary && prefs.dietary.length > 0) {
    chips.push({
      id: 'pref_dietary',
      label: 'Dietary',
      value: prefs.dietary.join(', '),
      type: 'preference',
      removable: true,
    });
  }
  
  if (prefs.cuisines && prefs.cuisines.length > 0) {
    chips.push({
      id: 'pref_cuisines',
      label: 'Cuisines',
      value: prefs.cuisines.join(', '),
      type: 'preference',
      removable: true,
    });
  }
  
  if (prefs.categories && prefs.categories.length > 0) {
    chips.push({
      id: 'pref_categories',
      label: 'Categories',
      value: prefs.categories.join(', '),
      type: 'preference',
      removable: true,
    });
  }
  
  if (prefs.budget) {
    chips.push({
      id: 'pref_budget',
      label: 'Budget',
      value: prefs.budget,
      type: 'preference',
      removable: true,
    });
  }
  
  if (prefs.time_constraint) {
    chips.push({
      id: 'pref_time_constraint',
      label: 'Time_constraint',
      value: prefs.time_constraint,
      type: 'preference',
      removable: true,
    });
  }
  
  if (prefs.group_size) {
    chips.push({
      id: 'pref_group_size',
      label: 'Group_size',
      value: prefs.group_size.toString(),
      type: 'preference',
      removable: true,
    });
  }
  
  setContextChips((prev) => {
    // Keep location and time chips, replace preference chips
    const nonPrefChips = prev.filter((chip) => chip.type !== 'preference');
    return [...nonPrefChips, ...chips];
  });
};

const setManualTime = (timeOfDay: string) => {
  setContextChips((prev) => {
    const filtered = prev.filter((chip) => chip.type !== 'time');
    return [
      ...filtered,
      {
        id: 'time',
        label: 'Time',
        value: timeOfDay,
        type: 'time',
        removable: false,
        icon: '🕐',
      },
    ];
  });
  
  console.log(`✅ Time manually set to: ${timeOfDay}`);
};

const setManualLocation = async (location: Location, cityName: string) => {
  setUserLocation(location);
  setCity(cityName);
  
  // Update location chip
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
        icon: '📍',
      },
    ];
  });
  
  // Update active session location if exists
  if (activeSession) {
    const updatedSession = {
      ...activeSession,
      location,
      city: cityName,
    };
    setActiveSession(updatedSession);
  }
  
  console.log(`✅ Location manually set to: ${cityName} (${location.lat}, ${location.lon})`);
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
    setManualTime,
    setManualLocation,
  };
};
