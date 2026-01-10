import axios from 'axios';

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
  days: TripDay[];
  flights?: Flight[];
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
};

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
    const response = await api.get('/airports/search', {
      params: { q: query }
    });
    return response.data;
  },
};

export default api;
