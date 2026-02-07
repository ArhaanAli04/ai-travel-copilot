/**
 * Custom hook for Local Discovery chat management
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
  updateSessionContext,
} from '../services/local-discovery-api';
import { getCurrentLocation, getMockLocation } from '../utils/geolocation';
import { getTimeOfDay, getGreeting } from '../utils/datetime';
import { generateMockResponse } from '../utils/mock-data';

export const useLocalDiscovery = () => {
  const navigate = useNavigate(); //  ADD
  const { sessionId } = useParams(); 
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
    if (sessions.length > 0) {
      if (sessionId) {
        // Try to find and load the session from URL
        const session = sessions.find(s => s.id === sessionId);
        if (session && session.id !== activeSession?.id) {
          setActiveSession(session);
          // ✅ NEW: Apply session context
          applySessionContext(session);
        } else if (!session) {
          // Session not found in list, try to fetch it
          loadSessionFromId(sessionId);
        }
      } else if (!activeSession && sessions.length > 0) {
        // No sessionId in URL, use most recent
        const latest = sessions[0];
        setActiveSession(latest);
        navigate(`/local-discovery/${latest.id}`, { replace: true });

        // ✅ NEW: Apply session context
        applySessionContext(latest);
      }
    }
  }, [sessions, sessionId]);

  const applySessionContext = async (session: ChatSession) => {
  // Apply manual overrides if they exist
  if (session.manual_location && session.manual_city) {
    setUserLocation(session.manual_location);
    setCity(session.manual_city);
    updateLocationChip(session.manual_location, session.manual_city);
    console.log(`✅ Applied manual location: ${session.manual_city}`);
  } else {
    // No manual override, use session's original location
    setUserLocation(session.location);
    setCity(session.city);
    updateLocationChip(session.location, session.city);
    console.log(`✅ Applied session location: ${session.city}`);
  }
  
  if (session.manual_time) {
    setContextChips((prev) => {
      const filtered = prev.filter((chip) => chip.type !== 'time');
      return [
        ...filtered,
        {
          id: 'time',
          label: 'Time',
          value: session.manual_time!,
          type: 'time',
          removable: false,
          icon: '🕐',
        },
      ];
    });
    console.log(`✅ Applied manual time: ${session.manual_time}`);
  } else {
    // No manual override, use current time
    const currentTime = getTimeOfDay();
    setContextChips((prev) => {
      const filtered = prev.filter((chip) => chip.type !== 'time');
      return [
        ...filtered,
        {
          id: 'time',
          label: 'Time',
          value: currentTime,
          type: 'time',
          removable: false,
          icon: '🕐',
        },
      ];
    });
    console.log(`✅ Applied current time: ${currentTime}`);
  }
};
  const loadSessionFromId = async (sessionId: string) => {
    try {
      const session = await getChatSession(sessionId);
      if (session) {
        setActiveSession(session);

        // ✅ CHANGED: Use helper function
        applySessionContext(session);
        // Add to sessions list if not present
        setSessions(prev => {
          if (!prev.find(s => s.id === sessionId)) {
            return [session, ...prev];
          }
          return prev;
        });
      } else {
        // Session not found, redirect to latest
        const latest = sessions[0];
        if (latest) {
          setActiveSession(latest);
          navigate(`/local-discovery/${latest.id}`, { replace: true });
          applySessionContext(latest);
        }
      }
    } catch (err) {
      console.error('Error loading session:', err);
    }
  };

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
      //await loadUserLocation();

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
  setLoading(true);
  try {
    // ✅ NEW: Get fresh current location for new session
    let freshLocation: Location;
    let freshCity: string;
    
    try {
      const result = await getCurrentLocation();
      freshLocation = result.location;
      freshCity = result.city;
      console.log(`✅ Got fresh location for new session: ${freshCity}`);
    } catch (err) {
      console.warn('Using mock location for new session:', err);
      const mock = getMockLocation('mumbai');
      freshLocation = mock.location;
      freshCity = mock.city;
    }
    
    // Create session with fresh location
    const newSession = await createChatSession(userId, freshCity, freshLocation);

    // ✅ NEW: Get fresh current time
    const freshTime = getTimeOfDay();

    // Add welcome message
    const welcomeMessage: Message = {
      id: `${newSession.id}_0`,
      role: 'assistant',
      content: `${getGreeting()}! 👋 I'm your local discovery assistant. I can help you find amazing places around ${freshCity}.

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
      
      // ✅ NEW: Apply fresh location and time to UI
      setUserLocation(freshLocation);
      setCity(freshCity);
      updateLocationChip(freshLocation, freshCity);
      
      // Update time chip with fresh current time
      setContextChips((prev) => {
        const filtered = prev.filter((chip) => chip.type !== 'time');
        return [
          ...filtered,
          {
            id: 'time',
            label: 'Time',
            value: freshTime,
            type: 'time',
            removable: false,
            icon: '🕐',
          },
        ];
      });
      
      navigate(`/local-discovery/${updatedSession.id}`, { replace: true });
      console.log(`✅ New session created with fresh context: ${freshCity}, ${freshTime}`);
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
    navigate(`/local-discovery/${sessionId}`);
    
    // ✅ CHANGED: Use helper function
    applySessionContext(session);
  } else {
    // Fetch from backend if not in local state
    const fetchedSession = await getChatSession(sessionId);
    if (fetchedSession) {
      setActiveSession(fetchedSession);
      navigate(`/local-discovery/${sessionId}`);
      applySessionContext(fetchedSession);
    }
  }
};

  const deleteSession = async (sessionId: string) => {
    try {
      await deleteChatSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));

      if (activeSession?.id === sessionId) {
        const remainingSessions = sessions.filter((s) => s.id !== sessionId);
        if (remainingSessions.length > 0) {
          setActiveSession(remainingSessions[0]);
          navigate(`/local-discovery/${remainingSessions[0].id}`, { replace: true });
        } else {
          setActiveSession(null);
          navigate('/local-discovery', { replace: true });
        }
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

const setManualTime = async (timeOfDay: string) => {
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
  
  // ✅ NEW: Save to backend
  if (activeSession) {
    try {
      await updateSessionContext(
        activeSession.id,
        undefined, // don't change location
        undefined, // don't change city
        timeOfDay  // update time
      );
      
      // Update local session state
      const updatedSession = {
        ...activeSession,
        manual_time: timeOfDay,
      };
      setActiveSession(updatedSession);
      updateSessionInList(updatedSession);
      
      console.log(`✅ Time manually set to: ${timeOfDay} and saved to backend`);
    } catch (err) {
      console.error('Failed to save manual time:', err);
      setError('Failed to save time preference');
    }
  }
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
  
  // ✅ NEW: Save to backend
  if (activeSession) {
    try {
      await updateSessionContext(
        activeSession.id,
        location,   // update location
        cityName,   // update city
        undefined   // don't change time
      );
      
      // Update local session state
      const updatedSession = {
        ...activeSession,
        manual_location: location,
        manual_city: cityName,
      };
      setActiveSession(updatedSession);
      updateSessionInList(updatedSession);
      
      console.log(`✅ Location manually set to: ${cityName} (${location.lat}, ${location.lon}) and saved to backend`);
    } catch (err) {
      console.error('Failed to save manual location:', err);
      setError('Failed to save location preference');
    }
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
    setManualTime,
    setManualLocation,
  };
};
