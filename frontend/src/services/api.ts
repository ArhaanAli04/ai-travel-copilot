import axios from 'axios';
import type {
  DisruptionCase,
  CreateDisruptionRequest,
  DisruptionOption,
  PassengerRights,
  DraftMessage,
  GenerateMessageRequest,
} from '../types/disruption';
import type { ActivityPhoto } from '../types/local-discovery';

const draftGenerationCache = new Map<number, Promise<{ drafts: DraftMessage[] }>>();
// Base API URL (update if your backend runs on different port)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Trip Types
export interface Trip {
  id: number;
  title: string;
  origin: string;
  destinations: string[];
  start_date: string;
  end_date: string;
  budget?: number;
  budget_currency: string;
  interests?: string[];
  preferences?: Record<string, any>;
  trip_type: 'solo' | 'couple' | 'family' | 'group';
  traveler_count: number;
  traveler_ages?: number[];
  include_flights: boolean;
  flight_preferences?: Record<string, any>;
  notes?: string;
  status: string;
  created_at: string;
  updated_at?: string;
  is_favorite: boolean;
  days: TripDay[];
  flights?: Flight[];
  include_hotels: boolean;
  hotel_preferences?: Record<string, any>;
  hotels?: Hotel[];
}
// Activity Types
export interface Activity {
  id: number;
  trip_day_id: number;
  title: string;
  description?: string;
  category?: string;
  start_time?: string;  // "09:00"
  end_time?: string;    // "10:30"
  duration_minutes?: number;
  location?: string;
  address?: string;
  estimated_cost?: number;
  cost_currency?: string;
  order: number;
  source_refs?: Record<string, any>;
  ai_reasoning?: string;
  is_booked: boolean;
  booking_url?: string;
}

export interface TripDay {
  id: number;
  trip_id: number;
  day_number: number;
  date: string;  // "2026-02-15"
  city: string;
  theme?: string;
  description?: string;
  activities: Activity[];
  flights: Flight[];
  weather_temp_high?: number;
  weather_temp_low?: number;
  weather_condition?: string;
  weather_icon?: string;
  weather_precipitation_prob?: number;
}
export interface TripCreate {
  title: string;
  origin: string;
  destinations: string[];
  start_date: string;
  end_date: string;
  budget?: number;
  budget_currency?: string;
  interests?: string[];
  preferences?: Record<string, any>;
  trip_type: 'solo' | 'couple' | 'family' | 'group';
  traveler_count: number;
  traveler_ages?: number[];
  include_flights: boolean;
  flight_preferences?: Record<string, any>;
  notes?: string;
  include_hotels: boolean;
  hotel_preferences?: Record<string, any>;
}

export interface FlightSearchParams {
  origin: string;
  destination: string;
  departure_date: string;
  return_date?: string;
  passengers: number;
  cabin_class: 'economy' | 'premium_economy' | 'business' | 'first';
  max_stops?: number;
  max_price?: number;
}

export interface Flight {
  id?: number;
  airline: string;
  airline_code?: string;
  flight_number?: string;
  departure_airport: string;
  arrival_airport: string;
  departure_city?: string;
  arrival_city?: string;
  departure_time: string;
  arrival_time: string;
  duration_minutes: number;
  stops: number;
  layover_airports?: string[];
  cabin_class: string;
  price_amount: number;
  price_currency: string;
  booking_url?: string;
  aircraft_type?: string;
  baggage_allowance?: Record<string, string>;
  amenities?: string[];
  is_selected?: boolean;
  source?: string;
  flight_direction?: string;
}
export interface EmailItineraryRequest {
  email: string;
  include_pdf?: boolean;
}
// API Functions
export const tripApi = {
  // Create new trip
  createTrip: async (tripData: TripCreate): Promise<Trip> => {
    const response = await api.post('/trips/', tripData);
    return response.data;
  },

  // Get trip by ID
  getTrip: async (tripId: number): Promise<Trip> => {
    const response = await api.get(`/trips/${tripId}`);
    return response.data;
  },
  // List all trips (alias for better naming)
  getAllTrips: async (userId?: number): Promise<Trip[]> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/trips/', { params });
    return response.data;
  },

  // List all trips
  listTrips: async (userId?: number): Promise<Trip[]> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/trips/', { params });
    return response.data;
  },

  // Update trip
  updateTrip: async (tripId: number, tripData: Partial<TripCreate>): Promise<Trip> => {
    const response = await api.put(`/trips/${tripId}`, tripData);
    return response.data;
  },

  // Delete trip
  deleteTrip: async (tripId: number): Promise<void> => {
    await api.delete(`/trips/${tripId}`);
  },

  generateItinerary: async (tripId: number): Promise<Trip> => {
    const response = await api.post(`/trips/${tripId}/plan`);
    return response.data;
  },

  toggleFavorite: async (tripId: number): Promise<{ trip_id: number; is_favorite: boolean; message: string }> => {
    const response = await api.post(`/trips/${tripId}/favorite`);
    return response.data;
  },

  // NEW: Get favorite trips
  getFavoriteTrips: async (userId?: number): Promise<Trip[]> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/trips/favorites', { params });
    return response.data;
  },

  emailItinerary: async (tripId: number, data: EmailItineraryRequest): Promise<any> => {
    const response = await api.post(`/trips/${tripId}/email`, data);
    return response.data;
  },
};

// Add to existing api object (after tripApi)
export const flightApi = {
  // Search flights
  searchFlights: async (tripId: number, params?: FlightSearchParams): Promise<Flight[]> => {
    const url = params 
      ? `/trips/${tripId}/flights/search`
      : `/trips/${tripId}/flights/search`;
    const response = await api.post(url, params || {});
    return response.data;
  },

  // Select flight
  selectFlight: async (tripId: number, flight: Flight): Promise<Flight> => {
    const response = await api.post(`/trips/${tripId}/flights/select`, {
      flight_data: flight
    });
    return response.data;
  },

  // Get trip flights
  getTripFlights: async (tripId: number): Promise<Flight[]> => {
    const response = await api.get(`/trips/${tripId}/flights`);
    return response.data;
  },

  deleteFlight: async (tripId: number, flightId: number): Promise<void> => {
    await api.delete(`/trips/${tripId}/flights/${flightId}`);
  },
};
// Add type
export interface AirportOption {
  code: string;
  name: string;
  city: string;
  country: string;
  state?: string;
  display: string;
}

// Airport autocomplete
export interface AirportSuggestion {
  code: string;
  name: string;
  city: string;
  country: string;
  display: string;
}

export const airportApi = {
  // Search airports
  searchAirports: async (query: string): Promise<AirportSuggestion[]> => {
    if (query.length < 2) return [];
    const response = await api.get('/trips/airports/search', {
      params: { q: query }
    });
    return response.data;
  },

  // ✅ NEW: Get all airports for a city
  getAirportsByCity: async (city: string): Promise<AirportOption[]> => {
    const response = await api.get('/trips/airports/by-city', {
      params: { city }
    });
    return response.data;
  },
};

// Activity explanation response
export interface ActivityExplanation {
  explanation: string;
  sources: Array<{
    city: string;
    theme: string;
    source_url: string;
    source_title: string;
    relevance_score: number;
    content_snippet: string;
  }>;
  has_sources: boolean;
  cached: boolean;
  generated_at?: number;
}

// Activity management API
export const activityApi = {
  // Get explanation for an activity
  explainActivity: async (activityId: number, forceRefresh = false): Promise<ActivityExplanation> => {
    const response = await api.get(`/trips/activities/${activityId}/explain`, {
      params: { force_refresh: forceRefresh }
    });
    return response.data;
  },

  // Delete an activity
  deleteActivity: async (activityId: number): Promise<void> => {
    await api.delete(`/trips/activities/${activityId}`);
  },

  // Reorder activities within a day
  reorderActivities: async (tripId: number, dayId: number, activityIds: number[]): Promise<void> => {
    await api.post(`/trips/${tripId}/days/${dayId}/reorder`, {
      activity_ids: activityIds
    });
  },

  // Update activity (title, times)
  updateActivity: async (
    activityId: number,
    updates: {
      title?: string;
      start_time?: string;
      end_time?: string;
      duration_minutes?: number;
    },
    autoAdjustSubsequent = true
  ): Promise<{
    activity: Activity;
    adjusted_activities: Array<{
      id: number;
      title: string;
      new_start_time: string;
      new_end_time: string;
    }>;
    time_shift_minutes: number;
  }> => {
    const response = await api.patch(
      `/trips/activities/${activityId}`,
      updates,
      {
        params: { auto_adjust_subsequent: autoAdjustSubsequent }
      }
    );
    return response.data;
  },
};

// Activity Photos
export const activityPhotosApi = {
  getPhotos: async (activityId: number): Promise<{ photos: ActivityPhoto[]; source: string; cached: boolean }> => {
    const response = await fetch(`${API_BASE_URL}/trips/activities/${activityId}/photos`);
    if (!response.ok) throw new Error('Failed to fetch activity photos');
    return response.json();
  }
};

// Day re-planning API
export const dayApi = {
  // Re-plan a specific day
  replanDay: async (
    tripId: number,
    dayId: number,
    additionalPreferences: string,
    keepExistingActivities = false
  ): Promise<Trip> => {
    const response = await api.post(`/trips/${tripId}/days/${dayId}/replan`, {
      additional_preferences: additionalPreferences,
      keep_existing_activities: keepExistingActivities
    });
    return response.data;
  },
};

// ── Hotel Types ────────────────────────────────────────────────────────────
export interface Hotel {
  id?: number;
  name: string;
  property_type?: string;
  city: string;
  address?: string;
  coordinates?: { lat: number; lng: number };
  rating?: number;
  reviews_count?: number;
  rating_breakdown?: Record<string, number>;
  price_per_night: number;
  price_currency: string;
  total_price?: number;
  check_in_date?: string;
  check_out_date?: string;
  nights?: number;
  thumbnail?: string;
  images?: string[];
  amenities?: string[];
  highlights?: string[];
  booking_url?: string;
  source?: string;
  serpapi_property_id?: string;
  is_selected?: boolean;
  trip_id?: number;
}

export interface HotelSearchParams {
  city: string;
  check_in_date: string;
  check_out_date: string;
  adults: number;
  sort_by?: 'relevance' | 'lowest_price' | 'highest_rating' | 'most_reviewed';
  max_price?: number;
  min_rating?: number;
}

// ── Hotel API ──────────────────────────────────────────────────────────────
export const hotelApi = {
  searchHotels: async (tripId: number, params?: HotelSearchParams): Promise<Hotel[]> => {
    const response = await api.post(`/trips/${tripId}/hotels/search`, params || {});
    return response.data;
  },

  selectHotel: async (tripId: number, hotel: Hotel): Promise<Hotel> => {
    const response = await api.post(`/trips/${tripId}/hotels/select`, {
      hotel_data: hotel,
    });
    return response.data;
  },

  getTripHotels: async (tripId: number): Promise<Hotel[]> => {
    const response = await api.get(`/trips/${tripId}/hotels`);
    return response.data;
  },

  deleteHotel: async (tripId: number, hotelId: number): Promise<void> => {
    await api.delete(`/trips/${tripId}/hotels/${hotelId}`);
  },
};

// ===== DISRUPTION API (Day 15) =====

export const disruptionApi = {
  // Create new disruption case
  createCase: async (data: CreateDisruptionRequest): Promise<DisruptionCase> => {
    const response = await api.post('/disruptions/', data);
    return response.data;
  },

  // Get disruption case by ID
  getCase: async (caseId: number): Promise<DisruptionCase> => {
    const response = await api.get(`/disruptions/${caseId}`);
    return response.data;
  },

  // List all disruption cases
  listCases: async (userId?: number): Promise<{ total: number; cases: DisruptionCase[] }> => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/disruptions/', { params });
    return response.data;
  },

  // Refresh flight/weather data
  refreshCase: async (caseId: number): Promise<DisruptionCase> => {
    const response = await api.post(`/disruptions/${caseId}/refresh`);
    return response.data;
  },

  // Explain passenger rights
  explainRights: async (
    caseId: number,
    options?: {
      airline_code?: string;
      booking_class?: string;
      insurance_provider?: string;
    }
  ): Promise<PassengerRights> => {
    const response = await api.post(`/disruptions/${caseId}/explain-rights`, options || {});
    return response.data;
  },

  // Suggest resolution options
  suggestOptions: async (caseId: number): Promise<{
    options: DisruptionOption[];
    total_options: number;
    generated_at: string;
  }> => {
    const response = await api.post(`/disruptions/${caseId}/suggest-options`);
    return response.data;
  },

  // Generate draft message
  generateMessage: async (
    caseId: number,
    request: GenerateMessageRequest
  ): Promise<DraftMessage> => {
    const response = await api.post(`/disruptions/${caseId}/generate-message`, request);
    return response.data;
  },

  // Get all draft messages for a case
  getMessages: async (caseId: number): Promise<DraftMessage[]> => {
    const response = await api.get(`/disruptions/${caseId}/messages`);
    return response.data;
  },

  // ✅ Generate multiple drafts with caching
  generateDrafts: async (caseId: number): Promise<{ drafts: DraftMessage[] }> => {
    // ✅ Check if already generating for this case
    if (draftGenerationCache.has(caseId)) {
      console.log(`⏳ Already generating drafts for case ${caseId}, waiting...`);
      return draftGenerationCache.get(caseId)!;
    }
    
    const tones: Array<'formal' | 'firm' | 'friendly'> = ['formal', 'firm', 'friendly'];
    
    // ✅ Create promise and cache it
    const generationPromise = (async () => {
      try {
        console.log(`🔄 Generating ${tones.length} drafts for case ${caseId}...`);
        
        // Generate all 3 drafts in parallel
        const draftPromises = tones.map(tone =>
          disruptionApi.generateMessage(caseId, {
            recipient_type: 'airline',
            tone: tone,
          }).catch(err => {
            console.error(`❌ Failed to generate ${tone} draft:`, err);
            return null; // Return null for failed drafts
          })
        );

        const results = await Promise.all(draftPromises);
        console.log(`✅ Draft generation complete:`, results.filter(r => r).length, 'succeeded');
        
        // ✅ Fetch all drafts from DB after generation
        const allDrafts = await disruptionApi.getMessages(caseId);
        
        console.log(`✅ Retrieved ${allDrafts.length} total drafts for case ${caseId}`);
        
        return { 
          drafts: allDrafts.slice(0, 3) 
        };
        
      } catch (error) {
        console.error('❌ Failed to generate drafts:', error);
        
        // Fallback: Try to fetch any existing drafts
        try {
          const existingDrafts = await disruptionApi.getMessages(caseId);
          return { drafts: existingDrafts.slice(0, 3) };
        } catch {
          return { drafts: [] };
        }
      } finally {
        // ✅ Clear cache after 10 seconds
        setTimeout(() => {
          draftGenerationCache.delete(caseId);
          console.log(`🧹 Cleared draft cache for case ${caseId}`);
        }, 10000);
      }
    })();
    
    // ✅ Store in cache
    draftGenerationCache.set(caseId, generationPromise);
    
    return generationPromise;
  },

  // ✅ Chat with AI assistant (placeholder for Day 16)
  chat: async (caseId: number, message: string, history?: any[]): Promise<{ response: string }> => {
  const response = await api.post(`/disruptions/${caseId}/chat`, {
    message: message,
    history: history || []
  });
  return response.data;
},

  // ✅ Get chat history (placeholder for Day 16)
  getChatHistory: async (caseId: number): Promise<{ messages: any[] }> => {
  const response = await api.get(`/disruptions/${caseId}/chat-history`);
  return response.data;
},

  // Delete disruption case
  deleteCase: async (caseId: number): Promise<void> => {
    await api.delete(`/disruptions/${caseId}`);
  },

   // Get saved options (no regeneration — fast)
  getOptions: async (caseId: number): Promise<DisruptionOption[]> => {
    const response = await api.get(`/disruptions/${caseId}/options`);
    return response.data;
  },

  // Search alternative flights for a specific date
  searchFlights: async (caseId: number, date?: string, force = false): Promise<{
    options: DisruptionOption[];
    total_options: number;
    generated_at: string;
  }> => {
    const params: Record<string, string> = {};
    if (date) params.search_date = date;
    if (force) params.force = 'true';
    const response = await api.post(`/disruptions/${caseId}/search-flights`, {}, { params });
    return response.data;
  },
  getWeather: async (caseId: number): Promise<{
    weather: {
      condition: string;
      icon: string;
      temp_max: number;
      temp_min: number;
      precipitation_probability: number;
      severity: string;
      airport_code: string;
      city: string;
      fetched_at: string;
    } | null;
    error?: string;
  }> => {
    const response = await api.get(`/disruptions/${caseId}/weather`);
    return response.data;
  },
};

export default api;
