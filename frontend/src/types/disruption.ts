// Disruption-related types

export type DisruptionType = 'delay' | 'cancellation' | 'weather' | 'strike' | 'other';
export type DisruptionSeverity = 'low' | 'medium' | 'high' | 'critical';
export type OptionType = 
  | 'alternative_flight' 
  | 'refund' 
  | 'hotel_voucher' 
  | 'compensation' 
  | 'meal_voucher' 
  | 'rebooking';

export interface DisruptionCase {
  id: number;
  user_id?: number;
  flight_number: string;
  airline: string;
  origin: string;
  destination: string;
  disruption_date: string;
  disruption_type: DisruptionType;
  current_status?: string;
  severity: DisruptionSeverity;
  pnr?: string;
  booking_reference?: string;
  notes?: string;
  meta_data?: {
    flight_status?: FlightStatus;
    weather?: WeatherInfo;
    travel_alerts?: any[];
    last_enriched?: string;
  };
  created_at: string;
  updated_at?: string;
  options?: DisruptionOption[];
}

export interface FlightStatus {
  flight_number: string;
  airline: string;
  status: string; // 'scheduled', 'active', 'landed', 'cancelled', 'delayed'
  departure: {
    airport: string;
    iata: string;
    scheduled?: string;
    estimated?: string;
    actual?: string;
    delay?: number;
    terminal?: string;
    gate?: string;
  };
  arrival: {
    airport: string;
    iata: string;
    scheduled?: string;
    estimated?: string;
    actual?: string;
    delay?: number;
    terminal?: string;
    gate?: string;
  };
  aircraft?: string;
  fetched_at: string;
}

export interface WeatherInfo {
  airport_code: string;
  temperature?: number;
  temperature_apparent?: number;
  humidity?: number;
  wind_speed?: number;
  precipitation_probability?: number;
  weather_code?: number;
  visibility?: number;
  cloud_cover?: number;
  condition: string;
  severity: string; // 'low', 'medium', 'high'
  fetched_at: string;
}

export interface DisruptionOption {
  id: number;
  disruption_case_id: number;
  option_type: OptionType;
  title: string;
  description?: string;
  estimated_cost?: number;
  action_required?: string;
  booking_url?: string;
  contact_info?: string;
  priority_rank: number;
  ai_reasoning?: string;
  created_at: string;
  meta_data?: {
    flight_details?: AlternativeFlight;
    refund_details?: RefundDetails;
    hotel_details?: HotelDetails;
    insurance_details?: InsuranceDetails;
    pros?: string[];
    cons?: string[];
    recommended?: boolean;
  };
}

export interface AlternativeFlight {
  flight_number: string;
  airline: string;
  departure_time: string;
  arrival_time: string;
  duration_minutes: number;
  stops: number;
  price_amount: number;
  price_currency: string;
  price_difference?: number;
  booking_url?: string;
}

export interface RefundDetails {
  ticket_refund: number;
  compensation?: number;
  total: number;
  currency: string;
  regulation?: string;
}

export interface HotelDetails {
  estimated_refund: number;
  currency: string;
}

export interface InsuranceDetails {
  covered_expenses: {
    hotel?: number;
    meals?: number;
    rebooking?: number;
    total: number;
  };
  currency: string;
}

export interface PassengerRights {
  summary: string;
  rights_bullets: string[];
  compensation_amount?: number;
  compensation_currency: string;
  next_steps: string[];
  source_links: Array<{
    title: string;
    url: string;
    type: string;
    region: string;
  }>;
  cached: boolean;
  region: string;
  applicable_regulation: string;
  generated_at: string;
}

export interface DraftMessage {
  id: number;  // ✅ Remove optional (backend always returns this)
  disruption_case_id: number;
  disruption_option_id?: number | null;
  recipient_type: string;  // ✅ Change from union to string (backend returns 'AIRLINE', 'HOTEL', etc.)
  recipient_name?: string | null;
  recipient_email?: string | null;
  subject: string;
  body: string;
  tone: string;  // ✅ Change from union to string (backend returns 'FORMAL', 'FIRM', etc.)
  language: string;
  attachments_needed?: string | null;
  next_steps?: string[];
  created_at: string;  // ✅ Remove optional (backend always returns this)
}


// Request types
export interface CreateDisruptionRequest {
  flight_number: string;
  airline: string;
  origin: string;
  destination: string;
  disruption_date: string;
  pnr?: string;
  notes?: string;
}

export interface GenerateMessageRequest {
  option_id?: number;
  recipient_type: 'airline' | 'hotel' | 'insurance';
  tone: 'formal' | 'firm' | 'friendly';
  recipient_name?: string;
}
