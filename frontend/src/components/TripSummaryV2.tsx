import { Calendar, MapPin, Users, DollarSign, Sparkles, AlertCircle, RefreshCw, Plus } from 'lucide-react';
import type { Trip } from '../services/api';
import FlightSection from './FlightSection';
import ItineraryView from './ItineraryView';

interface TripSummaryV2Props {
  trip: Trip;
  itineraryGenerated: boolean;
  generatingItinerary: boolean;
  onGenerateItinerary: () => void;
  onCreateAnother: () => void;
  onRefreshTrip: () => void;
  loading: boolean;
  originCode: string;
  destinationCodes: string[];
}

export function TripSummaryV2({
  trip,
  itineraryGenerated,
  generatingItinerary,
  onGenerateItinerary,
  onCreateAnother,
  onRefreshTrip,
  loading,
  originCode,
  destinationCodes,
}: TripSummaryV2Props) {
  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Success Banner */}
      <div className="glass-card rounded-3xl p-6 border-[#22C55E]/30 bg-gradient-to-r from-[#22C55E]/10 to-[#38BDF8]/10">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5 text-[#22C55E]" />
              <h2 className="text-2xl font-bold text-white">{trip.title}</h2>
            </div>
            <div className="flex flex-wrap gap-3 text-sm text-[#E5E7EB]">
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4 text-[#38BDF8]" />
                {new Date(trip.start_date).toLocaleDateString()} - {new Date(trip.end_date).toLocaleDateString()}
              </div>
              <div className="flex items-center gap-1">
                <MapPin className="w-4 h-4 text-[#38BDF8]" />
                {trip.destinations.length} destination{trip.destinations.length > 1 ? 's' : ''}
              </div>
              <div className="flex items-center gap-1">
                <Users className="w-4 h-4 text-[#38BDF8]" />
                {trip.traveler_count} traveler{trip.traveler_count > 1 ? 's' : ''}
              </div>
              {trip.budget && (
                <div className="flex items-center gap-1">
                  <DollarSign className="w-4 h-4 text-[#38BDF8]" />
                  {trip.budget} {trip.budget_currency}
                </div>
              )}
            </div>
          </div>
          <div className="px-3 py-1 rounded-full bg-[#22C55E] text-white text-sm font-semibold shadow-lg shadow-[#22C55E]/30">
            {trip.status === 'planned' ? 'Planned' : 'Created'}
          </div>
        </div>
      </div>

      {/* Generate Itinerary Button */}
      {!itineraryGenerated && (
        <button
          onClick={onGenerateItinerary}
          disabled={generatingItinerary}
          className={`w-full h-16 text-lg font-semibold rounded-2xl shadow-lg transition-all ${
            generatingItinerary
              ? 'bg-gray-600 cursor-not-allowed'
              : 'bg-gradient-to-r from-[#F97316] to-[#38BDF8] hover:from-[#EA580C] hover:to-[#3B82F6] hover:scale-[1.02] shadow-[#F97316]/20'
          } text-white flex items-center justify-center gap-2`}
        >
          {generatingItinerary ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              Generating AI Itinerary... (30-60s)
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Generate AI Itinerary
            </>
          )}
        </button>
      )}

      {/* Empty State or Generated Itinerary */}
      {!itineraryGenerated ? (
        <div className="glass-card rounded-3xl p-12 border-[rgba(148,163,184,0.2)] text-center">
          <div className="max-w-md mx-auto">
            <div className="w-16 h-16 rounded-full bg-[#F97316]/10 flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-8 h-8 text-[#F97316]" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No Itinerary Generated Yet</h3>
            <p className="text-[#9CA3AF]">
              Click the button above to generate an AI-powered day-by-day itinerary with weather-aware suggestions
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Use your existing ItineraryView component */}
          <ItineraryView trip={trip} />
        </div>
      )}

      {/* Flight Search Section - Use your existing component */}
      {trip.include_flights && (
        <div className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <FlightSection
            trip={trip}
            originCode={originCode}
            destinationCodes={destinationCodes}
          />
        </div>
      )}

      {/* Trip JSON (Debug - Collapsible) */}
      {!itineraryGenerated && (
        <details className="glass-card rounded-2xl border-[rgba(148,163,184,0.2)] overflow-hidden">
          <summary className="cursor-pointer px-6 py-4 text-white font-semibold hover:bg-white/5 transition-colors">
            📄 View Trip JSON (Debug)
          </summary>
          <pre className="p-6 bg-[#0B1120] text-[#E5E7EB] text-xs overflow-auto max-h-96">
            {JSON.stringify(trip, null, 2)}
          </pre>
        </details>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={onRefreshTrip}
          disabled={loading}
          className={`flex-1 h-12 border border-[rgba(148,163,184,0.2)] text-white rounded-xl bg-transparent transition-all flex items-center justify-center gap-2 ${
            loading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-white/5'
          }`}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Trip Data
        </button>
        <button
          onClick={onCreateAnother}
          className="flex-1 h-12 border border-[#38BDF8] text-[#38BDF8] hover:bg-[#38BDF8]/10 rounded-xl bg-transparent transition-all flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create Another Trip
        </button>
      </div>
    </div>
  );
}
