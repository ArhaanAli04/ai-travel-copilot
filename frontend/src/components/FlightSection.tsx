import { useState } from 'react';
import { Plane, Search, CheckCircle, AlertCircle } from 'lucide-react';
import { type Trip, type Flight, type FlightSearchParams, flightApi } from '../services/api';
import FlightSearchResults from './FlightSearchResults';

interface FlightSectionProps {
  trip: Trip;
  originCode: string;
  destinationCodes: string[];
}

const FlightSection = ({ trip, originCode, destinationCodes }: FlightSectionProps) => {
  const [showFlightSearch, setShowFlightSearch] = useState(false);
  const [flights, setFlights] = useState<Flight[]>([]);
  const [selectedFlight, setSelectedFlight] = useState<Flight | null>(null);
  const [loadingFlights, setLoadingFlights] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search for flights
  const handleFlightSearch = async () => {
    setLoadingFlights(true);
    setError(null);
    try {
      const tripType = trip.flight_preferences?.trip_type || 'one_way';

      const searchParams: FlightSearchParams = {
        origin: originCode || 'BOM',
        destination: destinationCodes[0] || 'DEL',
        departure_date: trip.start_date.split('T')[0],
        return_date: tripType === 'round_trip' ? trip.end_date.split('T')[0] : undefined,
        passengers: trip.traveler_count,
        cabin_class: (trip.flight_preferences?.cabin_class as any) || 'economy',
        max_stops: trip.flight_preferences?.max_stops,
      };

      console.log('🔍 Searching flights with params:', searchParams);

      const flightResults = await flightApi.searchFlights(trip.id, searchParams);
      setFlights(flightResults);
      setShowFlightSearch(true);
      console.log('✅ Found flights:', flightResults);
    } catch (err: any) {
      console.error('❌ Error searching flights:', err);
      setError(err.response?.data?.detail || 'Failed to search flights');
    } finally {
      setLoadingFlights(false);
    }
  };

  // Select a flight
  const handleFlightSelect = async (flight: Flight) => {
    setLoadingFlights(true);
    setError(null);
    try {
      const saved = await flightApi.selectFlight(trip.id, flight);
      setSelectedFlight(saved);
      setShowFlightSearch(false);
      console.log('✅ Flight selected:', saved);
    } catch (err: any) {
      console.error('❌ Error selecting flight:', err);
      setError(err.response?.data?.detail || 'Failed to select flight');
    } finally {
      setLoadingFlights(false);
    }
  };

  if (!trip.include_flights) return null;

  return (
    <div className="mb-8 animate-fade-in">
      <div className="flex items-center gap-3 mb-4">
        <Plane className="w-6 h-6 text-[#38BDF8]" />
        <h3 className="text-2xl font-bold text-white">Flight Search</h3>
      </div>

      {error && (
        <div className="glass-card rounded-2xl p-4 mb-4 border-[#EF4444]/30 bg-[#EF4444]/10">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-[#EF4444]" />
            <p className="text-[#FCA5A5]">{error}</p>
          </div>
        </div>
      )}

      {!showFlightSearch ? (
        <button
          onClick={handleFlightSearch}
          disabled={loadingFlights}
          className={`px-6 py-3 rounded-xl font-bold text-white transition-all ${
            loadingFlights
              ? 'bg-[#6B7280] cursor-not-allowed'
              : 'bg-[#38BDF8] hover:bg-[#0EA5E9] hover:scale-105 active:scale-95'
          }`}
        >
          {loadingFlights ? (
            <span className="flex items-center gap-2">
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Searching Flights...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Search className="w-5 h-5" />
              Search Flights
            </span>
          )}
        </button>
      ) : (
        <FlightSearchResults
          flights={flights}
          onSelectFlight={handleFlightSelect}
          loading={loadingFlights}
          onClose={() => setShowFlightSearch(false)}
        />
      )}

      {/* Selected Flight Display */}
      {selectedFlight && (
      <div className="glass-card rounded-3xl p-6 mt-4 border-[#22C55E]/30 bg-gradient-to-br from-[#22C55E]/10 to-[#38BDF8]/10 animate-fade-in">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-[#22C55E]" />
            <h3 className="text-xl font-bold text-white">Flight Selected</h3>
          </div>
          
          {/* Booking Disclaimer Badge */}
          <div className="px-3 py-1.5 rounded-lg bg-[#F59E0B]/10 border border-[#F59E0B]/30">
            <p className="text-xs text-[#FCD34D] font-medium">Planning Only</p>
          </div>
        </div>

        {/* Info Message */}
        <div className="mb-4 p-3 rounded-xl bg-[#3B82F6]/10 border border-[#3B82F6]/30">
          <p className="text-sm text-[#93C5FD]">
            ℹ️ This flight is saved for planning purposes. To actually book this flight, visit the airline's website or your preferred booking platform.
          </p>
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-lg font-semibold text-white">
              {selectedFlight.airline} {selectedFlight.flight_number}
            </p>
            <p className="text-sm text-[#9CA3AF]">{selectedFlight.aircraft_type}</p>
          </div>

          <div className="flex items-center justify-between py-3 px-4 bg-[#1F2937]/50 rounded-xl">
            <div>
              <p className="text-sm text-[#9CA3AF]">From</p>
              <p className="text-white font-semibold">
                {selectedFlight.departure_city} ({selectedFlight.departure_airport})
              </p>
            </div>
            <Plane className="w-5 h-5 text-[#38BDF8]" />
            <div className="text-right">
              <p className="text-sm text-[#9CA3AF]">To</p>
              <p className="text-white font-semibold">
                {selectedFlight.arrival_city} ({selectedFlight.arrival_airport})
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-[#9CA3AF] mb-1">Departure</p>
              <p className="text-sm text-white">
                {new Date(selectedFlight.departure_time).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-[#9CA3AF] mb-1">Arrival</p>
              <p className="text-sm text-white">
                {new Date(selectedFlight.arrival_time).toLocaleString()}
              </p>
            </div>
          </div>

          <div className="pt-3 border-t border-[rgba(148,163,184,0.2)]">
            <div className="flex items-center justify-between">
              <span className="text-[#9CA3AF]">Total Price</span>
              <span className="text-2xl font-bold text-[#22C55E]">
                ${selectedFlight.price_amount} {selectedFlight.price_currency}
              </span>
            </div>
          </div>
        </div>
      </div>
      )}
    </div>
  );
};

export default FlightSection;
