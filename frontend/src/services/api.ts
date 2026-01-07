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
  days: any[];
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
};

export default api;
