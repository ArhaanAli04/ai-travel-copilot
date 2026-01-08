import { type Flight } from '../services/api';

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

  // Group flights by direction
  const outboundFlights = flights.filter(f => 
    f.flight_direction === 'outbound' || f.flight_direction === 'one_way'
  );
  const returnFlights = flights.filter(f => f.flight_direction === 'return');

  const hasReturnFlights = returnFlights.length > 0;

  // Render individual flight card
  const renderFlightCard = (flight: Flight, index: number) => (
    <div 
      key={`${flight.flight_direction}-${index}`}
      style={{ 
        border: '1px solid #ddd',
        borderRadius: '12px',
        padding: '1.5rem',
        background: 'white',
        transition: 'box-shadow 0.3s',
        cursor: 'pointer'
      }}
      onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)'}
      onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}
    >
      {/* Airline Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
        <div>
          <h4 style={{ margin: 0, fontSize: '1.2rem' }}>
            {flight.airline} {flight.flight_number}
          </h4>
          <p style={{ margin: '0.25rem 0', color: '#666', fontSize: '0.9rem' }}>
            {flight.aircraft_type || 'Aircraft info not available'}
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#4CAF50' }}>
            ${flight.price_amount}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#666' }}>
            {flight.price_currency}
          </div>
        </div>
      </div>

      {/* Flight Route */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr auto 1fr', 
        gap: '1rem',
        alignItems: 'center',
        marginBottom: '1rem',
        padding: '1rem',
        background: '#f8f9fa',
        borderRadius: '8px'
      }}>
        {/* Departure */}
        <div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            {new Date(flight.departure_time).toLocaleTimeString('en-US', { 
              hour: '2-digit', 
              minute: '2-digit',
              hour12: false 
            })}
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 'bold' }}>
            {flight.departure_airport}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#666' }}>
            {flight.departure_city}
          </div>
        </div>

        {/* Duration & Stops */}
        <div style={{ textAlign: 'center', minWidth: '120px' }}>
          <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>
            {formatDuration(flight.duration_minutes)}
          </div>
          <div style={{ 
            borderTop: '2px solid #2196F3',
            position: 'relative',
            margin: '0.5rem 0'
          }}>
            <span style={{ 
              position: 'absolute',
              top: '-10px',
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'white',
              padding: '0 0.5rem',
              fontSize: '0.75rem',
              color: '#2196F3'
            }}>
              ✈️
            </span>
          </div>
          <div style={{ 
            fontSize: '0.85rem', 
            color: flight.stops === 0 ? '#4CAF50' : '#ff9800',
            fontWeight: 'bold'
          }}>
            {flight.stops === 0 ? 'Nonstop' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}
          </div>
        </div>

        {/* Arrival */}
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            {new Date(flight.arrival_time).toLocaleTimeString('en-US', { 
              hour: '2-digit', 
              minute: '2-digit',
              hour12: false 
            })}
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 'bold' }}>
            {flight.arrival_airport}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#666' }}>
            {flight.arrival_city}
          </div>
        </div>
      </div>

      {/* Flight Details */}
      <div style={{ 
        display: 'flex', 
        gap: '1rem', 
        flexWrap: 'wrap',
        marginBottom: '1rem',
        fontSize: '0.85rem'
      }}>
        <span style={{ 
          padding: '0.25rem 0.75rem',
          background: '#e3f2fd',
          borderRadius: '12px',
          color: '#1976d2'
        }}>
          {flight.cabin_class.charAt(0).toUpperCase() + flight.cabin_class.slice(1).replace('_', ' ')}
        </span>
        {flight.amenities?.map((amenity) => (
          <span 
            key={amenity}
            style={{ 
              padding: '0.25rem 0.75rem',
              background: '#f0f0f0',
              borderRadius: '12px',
              color: '#666'
            }}
          >
            {amenity}
          </span>
        ))}
        <span style={{ 
          padding: '0.25rem 0.75rem',
          background: '#fff3e0',
          borderRadius: '12px',
          color: '#e65100'
        }}>
          Source: {flight.source}
        </span>
      </div>

      {/* Book Button */}
      <button
        onClick={() => onSelectFlight(flight)}
        disabled={loading}
        style={{ 
          width: '100%',
          padding: '0.75rem',
          background: loading ? '#ccc' : '#4CAF50',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: loading ? 'not-allowed' : 'pointer',
          fontWeight: 'bold',
          fontSize: '1rem'
        }}
      >
        {loading ? 'Booking...' : '✅ Book This Flight'}
      </button>
    </div>
  );

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h4 style={{ margin: 0 }}>
          {hasReturnFlights 
            ? `Found ${outboundFlights.length} outbound + ${returnFlights.length} return flights`
            : `Found ${flights.length} flights`
          }
        </h4>
        <button
          onClick={onClose}
          style={{ 
            padding: '0.5rem 1rem',
            background: '#666',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer'
          }}
        >
          Close
        </button>
      </div>

      {/* Outbound Flights Section */}
      <div style={{ marginBottom: hasReturnFlights ? '2rem' : 0 }}>
        {hasReturnFlights && (
          <h3 style={{ 
            fontSize: '1.2rem', 
            marginBottom: '1rem',
            color: '#2196F3',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            borderBottom: '2px solid #e3f2fd',
            paddingBottom: '0.5rem'
          }}>
            ✈️ Outbound Flights
          </h3>
        )}
        <div style={{ display: 'grid', gap: '1rem' }}>
          {outboundFlights.map((flight, index) => renderFlightCard(flight, index))}
        </div>
      </div>

      {/* Return Flights Section */}
      {hasReturnFlights && (
        <div>
          <h3 style={{ 
            fontSize: '1.2rem', 
            marginBottom: '1rem',
            color: '#ff9800',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            borderBottom: '2px solid #fff3e0',
            paddingBottom: '0.5rem'
          }}>
            🔙 Return Flights
          </h3>
          <div style={{ display: 'grid', gap: '1rem' }}>
            {returnFlights.map((flight, index) => renderFlightCard(flight, index))}
          </div>
        </div>
      )}

      {/* No Results */}
      {flights.length === 0 && (
        <div style={{
          padding: '2rem',
          textAlign: 'center',
          color: '#666',
          background: '#f8f9fa',
          borderRadius: '12px'
        }}>
          <p style={{ fontSize: '1.2rem', margin: 0 }}>No flights found</p>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>Try adjusting your search criteria</p>
        </div>
      )}
    </div>
  );
};

export default FlightSearchResults;
