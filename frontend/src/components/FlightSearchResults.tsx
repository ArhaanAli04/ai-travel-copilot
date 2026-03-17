import { Plane, X } from 'lucide-react';
import { type Flight } from '../services/api';
import { formatCurrency } from '../utils/currency';
interface FlightSearchResultsProps {
  flights: Flight[];
  onSelectFlight: (flight: Flight) => void;
  loading: boolean;
  onClose: () => void;
}

const FlightSearchResults = ({ flights, onSelectFlight, loading, onClose }: FlightSearchResultsProps) => {
  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const outboundFlights = flights.filter(
    (f) => f.flight_direction === 'outbound' || f.flight_direction === 'one_way'
  );
  const returnFlights = flights.filter((f) => f.flight_direction === 'return');
  const hasReturnFlights = returnFlights.length > 0;

  const renderFlightCard = (flight: Flight, index: number) => (
    <div
      key={`${flight.flight_direction}-${index}`}
      className="glass-card rounded-3xl p-6 border-[rgba(148,163,184,0.2)] hover:bg-[#1F2937]/70 transition-all group animate-fade-in"
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      {/* Airline Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="text-xl font-bold text-white mb-1">
            {flight.airline} {flight.flight_number}
          </h4>
          <p className="text-sm text-[#9CA3AF]">
            {flight.aircraft_type || 'Boeing 737'}
          </p>
          <p className="text-xs text-[#6B7280] mt-1">
          {new Date(flight.departure_time).toLocaleDateString('en-US', {
            weekday: 'short',
            day: 'numeric',
            month: 'short',
            year: 'numeric',
          })}
        </p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-[#22C55E]">
            {formatCurrency(flight.price_amount, flight.price_currency)}
          </div>
          <div className="text-sm text-[#9CA3AF]">{flight.price_currency}</div>
        </div>
      </div>

      {/* Flight Route */}
      <div className="grid grid-cols-[1fr,auto,1fr] gap-4 items-center mb-4 p-4 bg-[#1F2937]/50 rounded-2xl">
        {/* Departure */}
        <div>
          <div className="text-3xl font-bold text-white mb-1">
            {new Date(flight.departure_time).toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit',
              hour12: false,
            })}
          </div>
          <div className="text-lg font-semibold text-[#38BDF8]">
            {flight.departure_airport}
          </div>
          <div className="text-sm text-[#9CA3AF]">{flight.departure_city}</div>
        </div>

        {/* Duration & Stops */}
        <div className="text-center min-w-[120px]">
          <div className="text-sm text-[#9CA3AF] mb-2">
            {formatDuration(flight.duration_minutes)}
          </div>
          <div className="relative">
            <div className="h-0.5 bg-gradient-to-r from-[#38BDF8] to-[#0EA5E9] w-full" />
            <Plane className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-5 h-5 text-[#38BDF8] bg-[#111827] px-1" />
          </div>
          <div
            className={`text-sm font-bold mt-2 ${
              flight.stops === 0 ? 'text-[#22C55E]' : 'text-[#F97316]'
            }`}
          >
            {flight.stops === 0 ? 'Nonstop' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}
          </div>
        </div>

        {/* Arrival */}
        <div className="text-right">
          <div className="text-3xl font-bold text-white mb-1">
            {new Date(flight.arrival_time).toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit',
              hour12: false,
            })}
          </div>
          <div className="text-lg font-semibold text-[#38BDF8]">
            {flight.arrival_airport}
          </div>
          <div className="text-sm text-[#9CA3AF]">{flight.arrival_city}</div>
        </div>
      </div>

      {/* Flight Details Badges */}
      <div className="flex flex-wrap gap-2 mb-4">
        <span className="px-3 py-1 rounded-full bg-[#38BDF8]/10 text-[#38BDF8] text-sm font-medium border border-[#38BDF8]/30">
          {flight.cabin_class.charAt(0).toUpperCase() + flight.cabin_class.slice(1).replace('_', ' ')}
        </span>
        {flight.amenities?.map((amenity) => (
          <span
            key={amenity}
            className="px-3 py-1 rounded-full bg-[#1F2937]/50 text-[#9CA3AF] text-sm border border-[rgba(148,163,184,0.2)]"
          >
            {amenity}
          </span>
        ))}
        <span className="px-3 py-1 rounded-full bg-[#F97316]/10 text-[#F97316] text-sm font-medium border border-[#F97316]/30">
          Source: {flight.source}
        </span>
      </div>

      {/* Book Button */}
      <button
        onClick={() => onSelectFlight(flight)}
        disabled={loading}
        className={`w-full py-4 rounded-2xl font-bold transition-all cursor-pointer ${
          loading
            ? 'bg-[#1F2937] text-white/50 border-2 border-[#6B7280]/30 cursor-not-allowed'
            : 'bg-transparent text-white border-2 border-[#38BDF8] hover:bg-[#38BDF8] hover:shadow-lg hover:shadow-[#38BDF8]/50 hover:scale-[1.02] active:scale-95'
        }`}
      >
        <span className="flex items-center justify-center gap-2">
          {loading ? (
            <>
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Booking Flight...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Book This Flight
            </>
          )}
        </span>
      </button>
    </div>
  );

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="glass-card rounded-3xl p-6 border-[rgba(148,163,184,0.2)] mb-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Plane className="w-6 h-6 text-[#38BDF8]" />
            <h4 className="text-xl font-bold text-white">
              {hasReturnFlights
                ? `Found ${outboundFlights.length} round-trip option${outboundFlights.length !== 1 ? 's' : ''}`
                : `Found ${flights.length} flight${flights.length !== 1 ? 's' : ''}`}
            </h4>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#6B7280] hover:bg-[#4B5563] text-white font-semibold transition-all flex items-center gap-2 cursor-pointer"
          >
            Close
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Column labels for round-trip */}
      {hasReturnFlights && (
        <div className="grid grid-cols-2 gap-4 mb-2 px-1">
          <div className="flex items-center gap-2">
            <Plane className="w-4 h-4 text-[#38BDF8]" />
            <span className="text-sm font-semibold text-[#38BDF8]">Outbound</span>
          </div>
          <div className="flex items-center gap-2">
            <Plane className="w-4 h-4 text-[#F97316] rotate-180" />
            <span className="text-sm font-semibold text-[#F97316]">Return</span>
          </div>
        </div>
      )}

      {/* Flight Cards */}
      {hasReturnFlights ? (
        <div className="space-y-4">
          {outboundFlights.map((outbound, index) => {
            const ret = returnFlights[index] ?? returnFlights[0];
            return (
              <div
                key={index}
                className="grid grid-cols-2 gap-4 animate-fade-in"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                {renderFlightCard(outbound, index)}
                {renderFlightCard(ret, index)}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {outboundFlights.map((flight, index) => renderFlightCard(flight, index))}
        </div>
      )}

      {/* No Results */}
      {flights.length === 0 && (
        <div className="glass-card rounded-3xl p-12 border-[rgba(148,163,184,0.2)] text-center">
          <Plane className="w-16 h-16 text-[#6B7280] mx-auto mb-4" />
          <p className="text-xl text-white font-semibold mb-2">No flights found</p>
          <p className="text-[#9CA3AF]">Try adjusting your search criteria</p>
        </div>
      )}
    </div>
  );
};

export default FlightSearchResults;
