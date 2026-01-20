import React, { useState, useEffect } from 'react';
import { X, Plane, Calendar, Users } from 'lucide-react';
import { type Trip,type FlightSearchParams } from '../services/api';
import { airportApi, flightApi } from '../services/api';

interface AirportOption {
  code: string;
  name: string;
  city: string;
  country: string;
  state?: string;
  display: string;
}

interface FlightSearchModalProps {
  trip: Trip;
  isOpen: boolean;
  onClose: () => void;
  onSearchComplete: (flights: any[]) => void;
}

const FlightSearchModal: React.FC<FlightSearchModalProps> = ({
  trip,
  isOpen,
  onClose,
  onSearchComplete
}) => {
  const [originOptions, setOriginOptions] = useState<AirportOption[]>([]);
  const [destinationOptions, setDestinationOptions] = useState<AirportOption[]>([]);
  const [selectedOrigin, setSelectedOrigin] = useState<string>('');
  const [selectedDestination, setSelectedDestination] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [loadingAirports, setLoadingAirports] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form fields (pre-filled from trip)
  const [departureDate, setDepartureDate] = useState(trip.start_date.split('T')[0]);
  const [returnDate, setReturnDate] = useState(
    trip.flight_preferences?.trip_type === 'round_trip' 
      ? trip.end_date.split('T')[0] 
      : ''
  );
  const [passengers, setPassengers] = useState(trip.traveler_count || 1);
  const [cabinClass, setCabinClass] = useState(
    trip.flight_preferences?.cabin_class || 'economy'
  );
  const [tripType, setTripType] = useState(
    trip.flight_preferences?.trip_type || 'one_way'
  );

  // Load airport options when modal opens
  useEffect(() => {
    if (isOpen) {
      loadAirportOptions();
    }
  }, [isOpen, trip]);

  const loadAirportOptions = async () => {
    setLoadingAirports(true);
    setError(null);
    try {
      // Load origin airports
      const originAirports = await airportApi.getAirportsByCity(trip.origin);
      setOriginOptions(originAirports);
      
      // Auto-select if only one option
      if (originAirports.length === 1) {
        setSelectedOrigin(originAirports[0].code);
      }

      // Load destination airports
      const destination = trip.destinations[0];
      const destAirports = await airportApi.getAirportsByCity(destination);
      setDestinationOptions(destAirports);
      
      // Auto-select if only one option
      if (destAirports.length === 1) {
        setSelectedDestination(destAirports[0].code);
      }

      console.log('✅ Loaded airport options:', {
        origin: originAirports.length,
        destination: destAirports.length
      });
    } catch (err: any) {
      console.error('❌ Error loading airports:', err);
      setError('Failed to load airport options');
    } finally {
      setLoadingAirports(false);
    }
  };

  const handleSearch = async () => {
    if (!selectedOrigin || !selectedDestination) {
      setError('Please select both origin and destination airports');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const searchParams: FlightSearchParams = {
        origin: selectedOrigin,
        destination: selectedDestination,
        departure_date: departureDate,
        return_date: tripType === 'round_trip' ? returnDate : undefined,
        passengers: passengers,
        cabin_class: cabinClass as any,
        max_stops: trip.flight_preferences?.max_stops
      };

      console.log('🔍 Searching flights:', searchParams);

      const flights = await flightApi.searchFlights(trip.id, searchParams);
      
      console.log('✅ Found', flights.length, 'flights');
      onSearchComplete(flights);
      onClose();
    } catch (err: any) {
      console.error('❌ Error searching flights:', err);
      setError(err.response?.data?.detail || 'Failed to search flights');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="glass-card rounded-3xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto border border-[#38BDF8]/30 animate-fade-in">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-[rgba(148,163,184,0.2)]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-[#38BDF8]/10 border border-[#38BDF8]/30">
              <Plane className="w-6 h-6 text-[#38BDF8]" />
            </div>
            <h2 className="text-2xl font-bold text-white">Search Flights</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] hover:text-white hover:bg-[#1F2937] transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {error && (
            <div className="glass-card rounded-2xl p-4 border-[#EF4444]/30 bg-[#EF4444]/10 animate-fade-in">
              <p className="text-[#FCA5A5] text-sm">{error}</p>
            </div>
          )}

          {loadingAirports ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 border-4 border-[#38BDF8]/30 border-t-[#38BDF8] rounded-full animate-spin mx-auto"></div>
              <p className="mt-4 text-[#9CA3AF]">Loading airport options...</p>
            </div>
          ) : (
            <>
              {/* Trip Type */}
              <div>
                <label className="block text-sm font-medium text-[#9CA3AF] mb-3">
                  Trip Type
                </label>
                <div className="flex gap-3">
                  <label className="flex-1">
                    <input
                      type="radio"
                      value="one_way"
                      checked={tripType === 'one_way'}
                      onChange={(e) => setTripType(e.target.value)}
                      className="sr-only peer"
                    />
                    <div className="px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/30 text-[#9CA3AF] text-center cursor-pointer transition-all peer-checked:border-[#38BDF8] peer-checked:bg-[#38BDF8]/10 peer-checked:text-[#38BDF8] hover:border-[#38BDF8]/50">
                      One Way
                    </div>
                  </label>
                  <label className="flex-1">
                    <input
                      type="radio"
                      value="round_trip"
                      checked={tripType === 'round_trip'}
                      onChange={(e) => setTripType(e.target.value)}
                      className="sr-only peer"
                    />
                    <div className="px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/30 text-[#9CA3AF] text-center cursor-pointer transition-all peer-checked:border-[#38BDF8] peer-checked:bg-[#38BDF8]/10 peer-checked:text-[#38BDF8] hover:border-[#38BDF8]/50">
                      Round Trip
                    </div>
                  </label>
                </div>
              </div>

              {/* Origin Airport */}
              <div>
                <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                  From {originOptions.length > 1 && (
                    <span className="text-[#38BDF8] text-xs ml-1">
                      ({originOptions.length} airports found)
                    </span>
                  )}
                </label>
                <select
                  value={selectedOrigin}
                  onChange={(e) => setSelectedOrigin(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-all"
                  required
                >
                  <option value="" className="bg-[#1F2937] text-[#9CA3AF]">
                    Select departure airport
                  </option>
                  {originOptions.map((airport) => (
                    <option key={airport.code} value={airport.code} className="bg-[#1F2937] text-white">
                      {airport.display}
                    </option>
                  ))}
                </select>
              </div>

              {/* Destination Airport */}
              <div>
                <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                  To {destinationOptions.length > 1 && (
                    <span className="text-[#38BDF8] text-xs ml-1">
                      ({destinationOptions.length} airports found)
                    </span>
                  )}
                </label>
                <select
                  value={selectedDestination}
                  onChange={(e) => setSelectedDestination(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-all"
                  required
                >
                  <option value="" className="bg-[#1F2937] text-[#9CA3AF]">
                    Select arrival airport
                  </option>
                  {destinationOptions.map((airport) => (
                    <option key={airport.code} value={airport.code} className="bg-[#1F2937] text-white">
                      {airport.display}
                    </option>
                  ))}
                </select>
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                    <Calendar className="w-4 h-4 inline mr-1" />
                    Departure Date
                  </label>
                  <input
                    type="date"
                    value={departureDate}
                    onChange={(e) => setDepartureDate(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-all"
                    required
                  />
                </div>
                {tripType === 'round_trip' && (
                  <div>
                    <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                      <Calendar className="w-4 h-4 inline mr-1" />
                      Return Date
                    </label>
                    <input
                      type="date"
                      value={returnDate}
                      onChange={(e) => setReturnDate(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-all"
                      required
                    />
                  </div>
                )}
              </div>

              {/* Passengers & Cabin Class */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                    <Users className="w-4 h-4 inline mr-1" />
                    Passengers
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="9"
                    value={passengers}
                    onChange={(e) => setPassengers(parseInt(e.target.value))}
                    className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                    Cabin Class
                  </label>
                  <select
                    value={cabinClass}
                    onChange={(e) => setCabinClass(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-white focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-all"
                  >
                    <option value="economy" className="bg-[#1F2937]">Economy</option>
                    <option value="premium_economy" className="bg-[#1F2937]">Premium Economy</option>
                    <option value="business" className="bg-[#1F2937]">Business</option>
                    <option value="first" className="bg-[#1F2937]">First Class</option>
                  </select>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-[rgba(148,163,184,0.2)]">
          <button
            onClick={onClose}
            className="px-6 py-3 rounded-xl border border-[rgba(148,163,184,0.2)] bg-[#1F2937]/50 text-[#9CA3AF] hover:text-white hover:bg-[#1F2937] transition-all"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={handleSearch}
            disabled={loading || loadingAirports || !selectedOrigin || !selectedDestination}
            className="px-6 py-3 bg-gradient-to-r from-[#38BDF8] to-[#0EA5E9] text-white rounded-xl font-bold hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 transition-all flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                Searching...
              </>
            ) : (
              <>
                <Plane className="w-5 h-5" />
                Search Flights
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FlightSearchModal;
