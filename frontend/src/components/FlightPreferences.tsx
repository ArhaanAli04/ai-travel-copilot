import {type TripCreate } from '../services/api';

interface FlightPreferencesProps {
  formData: TripCreate;
  setFormData: React.Dispatch<React.SetStateAction<TripCreate>>;
}

const FlightPreferences = ({ formData, setFormData }: FlightPreferencesProps) => {
  if (!formData.include_flights) return null;

  return (
    <div style={{ 
      padding: '1.5rem', 
      background: '#f8f9fa', 
      borderRadius: '12px',
      border: '2px solid #e3f2fd'
    }}>
      <h3 style={{ marginBottom: '1rem', color: '#2196F3' }}>✈️ Flight Preferences</h3>
      
      <div style={{ display: 'grid', gap: '1rem' }}>
        {/* Trip Type */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Trip Type
          </label>
          <select
            value={formData.flight_preferences?.trip_type || 'one_way'}
            onChange={(e) => setFormData(prev => ({
              ...prev,
              flight_preferences: {
                ...prev.flight_preferences,
                trip_type: e.target.value
              }
            }))}
            style={{ 
              width: '100%', 
              padding: '0.75rem', 
              fontSize: '1rem',
              border: '1px solid #ddd',
              borderRadius: '8px'
            }}
          >
            <option value="one_way">One-way</option>
            <option value="round_trip">Round Trip</option>
          </select>
        </div>

        {/* Cabin Class */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Cabin Class
          </label>
          <select
            value={formData.flight_preferences?.cabin_class || 'economy'}
            onChange={(e) => setFormData(prev => ({
              ...prev,
              flight_preferences: {
                ...prev.flight_preferences,
                cabin_class: e.target.value
              }
            }))}
            style={{ 
              width: '100%', 
              padding: '0.75rem', 
              fontSize: '1rem',
              border: '1px solid #ddd',
              borderRadius: '8px'
            }}
          >
            <option value="economy">Economy</option>
            <option value="premium_economy">Premium Economy</option>
            <option value="business">Business</option>
            <option value="first">First Class</option>
          </select>
        </div>

        {/* Max Stops */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Maximum Stops
          </label>
          <select
            value={formData.flight_preferences?.max_stops ?? 'any'}
            onChange={(e) => setFormData(prev => ({
              ...prev,
              flight_preferences: {
                ...prev.flight_preferences,
                max_stops: e.target.value === 'any' ? undefined : parseInt(e.target.value)
              }
            }))}
            style={{ 
              width: '100%', 
              padding: '0.75rem', 
              fontSize: '1rem',
              border: '1px solid #ddd',
              borderRadius: '8px'
            }}
          >
            <option value="any">Any number of stops</option>
            <option value="0">Nonstop only</option>
            <option value="1">1 stop max</option>
            <option value="2">2 stops max</option>
          </select>
        </div>

        {/* Preferred Airlines */}
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Preferred Airlines (Optional)
          </label>
          <input
            type="text"
            value={formData.flight_preferences?.preferred_airlines || ''}
            onChange={(e) => setFormData(prev => ({
              ...prev,
              flight_preferences: {
                ...prev.flight_preferences,
                preferred_airlines: e.target.value
              }
            }))}
            placeholder="e.g., Air India, IndiGo"
            style={{ 
              width: '100%', 
              padding: '0.75rem', 
              fontSize: '1rem',
              border: '1px solid #ddd',
              borderRadius: '8px'
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default FlightPreferences;
