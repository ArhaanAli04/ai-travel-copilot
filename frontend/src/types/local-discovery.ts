/**
 * Type definitions for Local Discovery feature
 */

export interface Location {
  lat: number;
  lon: number;
}

export interface UserPreferences {
  dietary?: string[];
  cuisines?: string[];
  categories?: string[];
  budget?: 'low' | 'moderate' | 'high';
  time_constraint?: string;
  group_size?: number;
}

export interface POI {
  poi_id: string;
  name: string;
  category: string;
  distance_km: number;
  distance_text: string;
  location: {
    type: string;
    coordinates: [number, number];
  };
  address?: string;
  phone?: string;
  website?: string;
  hours?: string;
  tags: Record<string, any>;
  reason: string;
  highlights: string[];
  best_for: string;
  relevance_score?: number;
  average_rating?: number;
  feedback_count?: number;
  positive_feedback_count?: number;
  negative_feedback_count?: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  pois?: POI[];
  timestamp: Date;
  location?: Location;
  preferences?: UserPreferences;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  created_at: Date;
  updated_at: Date;
  city: string;
  location: Location;
  manual_location?: Location | null;
  manual_city?: string | null;
  manual_time?: string | null;
}

export interface ContextChip {
  id: string;
  label: string;
  value: string;
  icon?: string;
  removable: boolean;
  type: 'location' | 'time' | 'weather' | 'dietary' | 'budget' | 'preference';
}

export interface SuggestRequest {
  query: string;
  user_location: Location;
  city: string;
  preferences?: UserPreferences;
  radius_km?: number;
  max_results?: number;
}

export interface SuggestResponse {
  recommendations: POI[];
  total_found: number;
  query: string;
  location: Location;
  city: string;
  sources: any[];
  search_radius_km: number;
}
export interface POIPhoto {
  url: string;
  thumbnail_url: string;
  width: number;
  height: number;
  source: 'wikimedia' | 'unsplash' | 'placeholder';
  attribution: string;
  alt_text: string;
}

export interface POIPhotosResponse {
  poi_id: string;
  poi_name: string;
  photos: POIPhoto[];
  total: number;
  source: 'wikimedia' | 'unsplash' | 'placeholder';
  cached: boolean;
}

// Separate type for activity photos (supports google_images source)
export interface ActivityPhoto {
  url: string;
  thumbnail_url: string;
  width: number;
  height: number;
  source: 'wikimedia' | 'unsplash' | 'placeholder' | 'google_images';
  attribution: string;
  alt_text: string;
}

export interface ActivityPhotosResponse {
  activity_id: number;
  activity_title: string;
  photos: ActivityPhoto[];
  source: 'wikimedia' | 'unsplash' | 'placeholder' | 'google_images';
  cached: boolean;
}
