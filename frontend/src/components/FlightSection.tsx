import { useState } from 'react';
import { type Trip, type Flight,type FlightSearchParams, flightApi } from '../services/api';
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
      // Get trip type and return date
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
    <div style={{ marginBottom: '2rem' }}>
      <h3 style={{ marginBottom: '1rem' }}>✈️ Flight Search</h3>
      
      {error && (
        <div style={{ 
          padding: '1rem', 
          background: '#fee', 
          color: '#c00', 
          borderRadius: '8px',
          marginBottom: '1rem' 
        }}>
          {error}
        </div>
      )}
      
      {!showFlightSearch ? (
        <button
          onClick={handleFlightSearch}
          disabled={loadingFlights}
          style={{ 
            padding: '1rem 2rem',
            background: loadingFlights ? '#ccc' : '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: loadingFlights ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            fontSize: '1rem'
          }}
        >
          {loadingFlights ? '🔍 Searching Flights...' : '🔍 Search Flights'}
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
        <div style={{ 
          marginTop: '1rem',
          padding: '1.5rem',
          background: '#e8f5e9',
          borderRadius: '12px',
          border: '2px solid #4CAF50'
        }}>
          <h3 style={{ color: '#4CAF50', marginBottom: '1rem' }}>
            ✅ Flight Booked!
          </h3>
          <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
            <strong>{selectedFlight.airline} {selectedFlight.flight_number}</strong>
          </p>
          <p style={{ margin: '0.25rem 0' }}>
            {selectedFlight.departure_city} ({selectedFlight.departure_airport}) → {selectedFlight.arrival_city} ({selectedFlight.arrival_airport})
          </p>
          <p style={{ margin: '0.25rem 0' }}>
            {new Date(selectedFlight.departure_time).toLocaleString()} → {new Date(selectedFlight.arrival_time).toLocaleString()}
          </p>
          <p style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#4CAF50', marginTop: '0.5rem' }}>
            ${selectedFlight.price_amount} {selectedFlight.price_currency}
          </p>
        </div>
      )}
    </div>
  );
};

export default FlightSection;
