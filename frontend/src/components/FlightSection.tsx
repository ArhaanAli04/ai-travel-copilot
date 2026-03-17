import { useState, useEffect } from 'react';
import { Plane, Search, CheckCircle, AlertCircle, X } from 'lucide-react';
import { type Trip, type Flight, flightApi } from '../services/api';
import FlightSearchResults from './FlightSearchResults';
import FlightSearchModal from './FlightSearchModal'; // ✅ NEW IMPORT
import ConfirmModal from './ConfirmModal';
import { formatCurrency } from '../utils/currency';
interface FlightSectionProps {
  trip: Trip;
}

const FlightSection = ({ trip }: FlightSectionProps) => {
  const [showFlightSearch, setShowFlightSearch] = useState(false);
  const [showSearchModal, setShowSearchModal] = useState(false); // ✅ NEW STATE
  const [flights, setFlights] = useState<Flight[]>([]);
  const [selectedFlights, setSelectedFlights] = useState<Flight[]>([]);
  const [loadingFlights, setLoadingFlights] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Modal state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [flightToDelete, setFlightToDelete] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Load selected flights from trip
  useEffect(() => {
    if (trip.flights && trip.flights.length > 0) {
      const selected = trip.flights.filter(f => f.is_selected);
      setSelectedFlights(selected);
      console.log('✅ Loaded', selected.length, 'selected flights from trip');
    }
  }, [trip.flights]);

  // ✅ NEW: Handle search completion from modal
  const handleSearchComplete = (flightResults: Flight[]) => {
    setFlights(flightResults);
    setShowFlightSearch(true);
    console.log('✅ Search complete:', flightResults.length, 'flights found');
  };

  // Select a flight
  const handleFlightSelect = async (flight: Flight) => {
    setLoadingFlights(true);
    setError(null);
    try {
      const saved = await flightApi.selectFlight(trip.id, flight);
      setSelectedFlights(prev => [...prev, saved]);
      setShowFlightSearch(false);
      console.log('✅ Flight selected:', saved);
    } catch (err: any) {
      console.error('❌ Error selecting flight:', err);
      setError(err.response?.data?.detail || 'Failed to select flight');
    } finally {
      setLoadingFlights(false);
    }
  };

  // Open delete confirmation
  const openDeleteModal = (flightId: number) => {
    setFlightToDelete(flightId);
    setShowDeleteModal(true);
  };

  // Confirm delete
  const confirmDelete = async () => {
    if (!flightToDelete) return;

    setDeleting(true);
    try {
      await flightApi.deleteFlight(trip.id, flightToDelete);
      setSelectedFlights(prev => prev.filter(f => f.id !== flightToDelete));
      console.log('✅ Flight deleted successfully');
      setShowDeleteModal(false);
      setFlightToDelete(null);
    } catch (err: any) {
      console.error('❌ Error removing flight:', err);
      setError(err.response?.data?.detail || 'Failed to remove flight');
    } finally {
      setDeleting(false);
    }
  };

  if (!trip.include_flights) return null;

  return (
    <div className="mb-8 animate-fade-in">
      <div className="flex items-center gap-3 mb-4">
        <Plane className="w-6 h-6 text-[#38BDF8]" />
        <h3 className="text-2xl font-bold text-white">Flights</h3>
      </div>

      {error && (
        <div className="glass-card rounded-2xl p-4 mb-4 border-[#EF4444]/30 bg-[#EF4444]/10">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-[#EF4444]" />
            <p className="text-[#FCA5A5]">{error}</p>
          </div>
        </div>
      )}

      {/* Selected Flights */}
      {selectedFlights.length > 0 && (
        <div className="space-y-4 mb-6">
          {selectedFlights.map((flight) => (
            <div
              key={flight.id}
              className="glass-card rounded-3xl p-6 border-[#22C55E]/30 bg-gradient-to-br from-[#22C55E]/10 to-[#38BDF8]/10 animate-fade-in"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-6 h-6 text-[#22C55E]" />
                  <h3 className="text-xl font-bold text-white">
                    {flight.flight_direction === 'return' ? '🔙 Return Flight' : '✈️ Outbound Flight'}
                  </h3>
                </div>

                <div className="flex items-center gap-2">
                  {/* Planning Badge */}
                  <div className="px-3 py-1.5 rounded-lg bg-[#F59E0B]/10 border border-[#F59E0B]/30">
                    <p className="text-xs text-[#FCD34D] font-medium">Saved</p>
                  </div>

                  {/* Remove Button */}
                  <button
                    onClick={() => openDeleteModal(flight.id!)}
                    className="p-1.5 rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444] hover:bg-[#EF4444]/20 transition-all cursor-pointer"
                    title="Remove flight"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Info Message */}
              <div className="mb-4 p-3 rounded-xl bg-[#3B82F6]/10 border border-[#3B82F6]/30">
                <p className="text-sm text-[#93C5FD]">
                  ℹ️ This flight is saved for planning. To book, visit the airline's website.
                </p>
              </div>

              <div className="space-y-3">
                {/* Airline Info */}
                <div>
                  <p className="text-lg font-semibold text-white">
                    {flight.airline} {flight.flight_number}
                  </p>
                  <p className="text-sm text-[#9CA3AF]">{flight.aircraft_type || 'Aircraft TBA'}</p>
                </div>

                {/* Route */}
                <div className="flex items-center justify-between py-3 px-4 bg-[#1F2937]/50 rounded-xl">
                  <div>
                    <p className="text-sm text-[#9CA3AF]">From</p>
                    <p className="text-white font-semibold">
                      {flight.departure_city} ({flight.departure_airport})
                    </p>
                  </div>
                  <Plane className="w-5 h-5 text-[#38BDF8]" />
                  <div className="text-right">
                    <p className="text-sm text-[#9CA3AF]">To</p>
                    <p className="text-white font-semibold">
                      {flight.arrival_city} ({flight.arrival_airport})
                    </p>
                  </div>
                </div>

                {/* Times */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs text-[#9CA3AF] mb-1">Departure</p>
                    <p className="text-sm text-white font-medium">
                      {new Date(flight.departure_time).toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-[#9CA3AF] mb-1">Arrival</p>
                    <p className="text-sm text-white font-medium">
                      {new Date(flight.arrival_time).toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>

                {/* Flight Details */}
                <div className="flex flex-wrap gap-2">
                  <span className="px-3 py-1 rounded-full bg-[#38BDF8]/10 text-[#38BDF8] text-xs font-medium border border-[#38BDF8]/30">
                    {flight.cabin_class.replace('_', ' ')}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium border ${
                    flight.stops === 0
                      ? 'bg-[#22C55E]/10 text-[#22C55E] border-[#22C55E]/30'
                      : 'bg-[#F97316]/10 text-[#F97316] border-[#F97316]/30'
                  }`}>
                    {flight.stops === 0 ? 'Nonstop' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}
                  </span>
                  <span className="px-3 py-1 rounded-full bg-[#6B7280]/10 text-[#9CA3AF] text-xs font-medium border border-[#6B7280]/30">
                    {Math.floor(flight.duration_minutes / 60)}h {flight.duration_minutes % 60}m
                  </span>
                </div>

                {/* Price */}
                <div className="pt-3 border-t border-[rgba(148,163,184,0.2)]">
                  <div className="flex items-center justify-between">
                    <span className="text-[#9CA3AF]">Total Price</span>
                    <span className="text-2xl font-bold text-[#22C55E]">
                      {formatCurrency(flight.price_amount, flight.price_currency, { showCode: true })}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ✅ CHANGED: Button now opens modal instead of searching directly */}
      {!showFlightSearch ? (
        <button
          onClick={() => setShowSearchModal(true)} // ✅ Open modal
          className="px-6 py-3 rounded-xl font-bold text-white bg-[#38BDF8] hover:bg-[#0EA5E9] hover:scale-105 active:scale-95 transition-all cursor-pointer"
        >
          <span className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            {selectedFlights.length > 0 ? 'Search Different Flights' : 'Search Flights'}
          </span>
        </button>
      ) : (
        <FlightSearchResults
          flights={flights}
          onSelectFlight={handleFlightSelect}
          loading={loadingFlights}
          onClose={() => setShowFlightSearch(false)}
        />
      )}

      {/* ✅ NEW: Flight Search Modal */}
      <FlightSearchModal
        trip={trip}
        isOpen={showSearchModal}
        onClose={() => setShowSearchModal(false)}
        onSearchComplete={handleSearchComplete}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setFlightToDelete(null);
        }}
        onConfirm={confirmDelete}
        title="Remove Flight?"
        message="Are you sure you want to remove this flight from your trip? This action cannot be undone."
        confirmText="Remove Flight"
        cancelText="Keep It"
        type="danger"
        loading={deleting}
      />
    </div>
  );
};

export default FlightSection;
