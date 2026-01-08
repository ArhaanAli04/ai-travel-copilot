import { useState } from 'react';
import { tripApi, type Trip, type TripCreate} from '../services/api';
import AirportAutocomplete from '../components/AirportAutocomplete';
import FlightPreferences from '../components/FlightPreferences';
import FlightSection from '../components/FlightSection';
const Planner = () => {
  // Form state
  const [formData, setFormData] = useState<TripCreate>({
    title: '',
    origin: '',
    destinations: [''],
    start_date: '',
    end_date: '',
    budget: undefined,
    budget_currency: 'USD',
    interests: [],
    trip_type: 'solo',
    traveler_count: 1,
    traveler_ages: [],
    include_flights: false,
    flight_preferences: {},
    notes: '',
  });

  // UI state
  const [currentInterest, setCurrentInterest] = useState('');
  const [createdTrip, setCreatedTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'form' | 'result'>('form');
  const [originCode, setOriginCode] = useState('');
  const [destinationCodes, setDestinationCodes] = useState<string[]>(['']);

  

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else if (type === 'number') {
      setFormData(prev => ({ ...prev, [name]: value ? Number(value) : undefined }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  // Handle trip type change (updates traveler count)
  const handleTripTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const tripType = e.target.value as 'solo' | 'couple' | 'family' | 'group';
    let travelerCount = 1;
    
    if (tripType === 'couple') travelerCount = 2;
    else if (tripType === 'family') travelerCount = 4;
    else if (tripType === 'group') travelerCount = 5;
    
    setFormData(prev => ({ 
      ...prev, 
      trip_type: tripType,
      traveler_count: travelerCount 
    }));
  };

  // Handle destinations
  const addDestination = () => {
    setFormData(prev => ({
        ...prev,
        destinations: [...prev.destinations, '']
    }));
    setDestinationCodes(prev => [...prev, '']);  // ✅ ADD THIS LINE
    };

  const updateDestination = (index: number, value: string) => {
    const newDestinations = [...formData.destinations];
    newDestinations[index] = value;
    setFormData(prev => ({ ...prev, destinations: newDestinations }));
  };

  const removeDestination = (index: number) => {
    if (formData.destinations.length > 1) {
      const newDestinations = formData.destinations.filter((_, i) => i !== index);
      setFormData(prev => ({ ...prev, destinations: newDestinations }));
    }
  };

  // Handle interests
  const addInterest = () => {
    if (currentInterest.trim() && !formData.interests?.includes(currentInterest.trim())) {
      setFormData(prev => ({
        ...prev,
        interests: [...(prev.interests || []), currentInterest.trim()]
      }));
      setCurrentInterest('');
    }
  };

  const removeInterest = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests?.filter(i => i !== interest)
    }));
  };

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Validate
      if (!formData.title || !formData.origin || formData.destinations.some(d => !d.trim())) {
        throw new Error('Please fill all required fields');
      }

      // Clean destinations
      const cleanedData = {
        ...formData,
        destinations: formData.destinations.filter(d => d.trim()),
      };

      // Create trip
      const trip = await tripApi.createTrip(cleanedData);
      setCreatedTrip(trip);
      setViewMode('result');
      console.log('✅ Trip created:', trip);
      
    } catch (err: any) {
      console.error('❌ Error creating trip:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to create trip');
    } finally {
      setLoading(false);
    }
  };

  // Fetch trip by ID (for testing)
  const handleFetchTrip = async () => {
    if (!createdTrip) return;
    
    setLoading(true);
    try {
      const trip = await tripApi.getTrip(createdTrip.id);
      setCreatedTrip(trip);
      console.log('✅ Trip fetched:', trip);
    } catch (err: any) {
      console.error('❌ Error fetching trip:', err);
      setError(err.response?.data?.detail || 'Failed to fetch trip');
    } finally {
      setLoading(false);
    }
  };
  

  // Reset form
  const resetForm = () => {
    setFormData({
      title: '',
      origin: '',
      destinations: [''],
      start_date: '',
      end_date: '',
      budget: undefined,
      budget_currency: 'USD',
      interests: [],
      trip_type: 'solo',
      traveler_count: 1,
      traveler_ages: [],
      include_flights: false,
      flight_preferences: {},
      notes: '',
    });
    setCreatedTrip(null);
    setViewMode('form');
    setError(null);
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
      <h1 style={{ marginBottom: '2rem' }}>✈️ Trip Planner</h1>

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

      {viewMode === 'form' ? (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Trip Title */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Trip Title *
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              placeholder="e.g., European Summer Adventure"
              required
              style={{ 
                width: '100%', 
                padding: '0.75rem', 
                fontSize: '1rem',
                border: '1px solid #ddd',
                borderRadius: '8px'
              }}
            />
          </div>

          {/* Origin */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Starting From *
            </label>
            <AirportAutocomplete
                value={formData.origin}
                onChange={(display, code) => {
                setFormData(prev => ({ ...prev, origin: display }));
                setOriginCode(code);
                }}
                placeholder="Search city or airport (e.g., Mumbai, BOM)"
                required
            />
          </div>

          {/* Destinations */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Destinations *
            </label>
            {formData.destinations.map((dest, index) => (
              <div key={index} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <AirportAutocomplete
                    value={dest}
                    onChange={(display, code) => {
                        updateDestination(index, display);
                        const newCodes = [...destinationCodes];
                        newCodes[index] = code;
                        setDestinationCodes(newCodes);
                    }}
                    placeholder={`Search destination ${index + 1}`}
                    required
                />
                {formData.destinations.length > 1 && (
                  <button 
                    type="button"
                    onClick={() => removeDestination(index)}
                    style={{ 
                      padding: '0.75rem 1rem',
                      background: '#f44',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: 'pointer'
                    }}
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button 
              type="button"
              onClick={addDestination}
              style={{ 
                padding: '0.5rem 1rem',
                background: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                marginTop: '0.5rem'
              }}
            >
              + Add Destination
            </button>
          </div>

          {/* Dates */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Start Date *
              </label>
              <input
                type="datetime-local"
                name="start_date"
                value={formData.start_date}
                onChange={handleInputChange}
                required
                style={{ 
                  width: '100%', 
                  padding: '0.75rem', 
                  fontSize: '1rem',
                  border: '1px solid #ddd',
                  borderRadius: '8px'
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                End Date *
              </label>
              <input
                type="datetime-local"
                name="end_date"
                value={formData.end_date}
                onChange={handleInputChange}
                required
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

          {/* Budget */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Budget (Optional)
              </label>
              <input
                type="number"
                name="budget"
                value={formData.budget || ''}
                onChange={handleInputChange}
                placeholder="e.g., 3000"
                min="0"
                style={{ 
                  width: '100%', 
                  padding: '0.75rem', 
                  fontSize: '1rem',
                  border: '1px solid #ddd',
                  borderRadius: '8px'
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Currency
              </label>
              <select
                name="budget_currency"
                value={formData.budget_currency}
                onChange={handleInputChange}
                style={{ 
                  width: '100%', 
                  padding: '0.75rem', 
                  fontSize: '1rem',
                  border: '1px solid #ddd',
                  borderRadius: '8px'
                }}
              >
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="INR">INR</option>
              </select>
            </div>
          </div>

          {/* Trip Type */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Trip Type *
              </label>
              <select
                name="trip_type"
                value={formData.trip_type}
                onChange={handleTripTypeChange}
                style={{ 
                  width: '100%', 
                  padding: '0.75rem', 
                  fontSize: '1rem',
                  border: '1px solid #ddd',
                  borderRadius: '8px'
                }}
              >
                <option value="solo">Solo Trip</option>
                <option value="couple">Couple Trip</option>
                <option value="family">Family Trip</option>
                <option value="group">Group Trip</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Number of Travelers *
              </label>
              <input
                type="number"
                name="traveler_count"
                value={formData.traveler_count}
                onChange={handleInputChange}
                min="1"
                max="20"
                required
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

          {/* Interests */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Interests (Optional)
            </label>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <input
                type="text"
                value={currentInterest}
                onChange={(e) => setCurrentInterest(e.target.value)}
                placeholder="e.g., culture, food, adventure"
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addInterest())}
                style={{ 
                  flex: 1, 
                  padding: '0.75rem', 
                  fontSize: '1rem',
                  border: '1px solid #ddd',
                  borderRadius: '8px'
                }}
              />
              <button 
                type="button"
                onClick={addInterest}
                style={{ 
                  padding: '0.75rem 1rem',
                  background: '#2196F3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer'
                }}
              >
                Add
              </button>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {formData.interests?.map((interest) => (
                <span 
                  key={interest}
                  style={{ 
                    padding: '0.5rem 1rem',
                    background: '#e3f2fd',
                    borderRadius: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}
                >
                  {interest}
                  <button
                    type="button"
                    onClick={() => removeInterest(interest)}
                    style={{ 
                      background: 'none',
                      border: 'none',
                      color: '#666',
                      cursor: 'pointer',
                      fontSize: '1.2rem',
                      lineHeight: 1
                    }}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Include Flights */}
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="include_flights"
                checked={formData.include_flights}
                onChange={handleInputChange}
                style={{ width: '20px', height: '20px', cursor: 'pointer' }}
              />
              <span style={{ fontWeight: 'bold' }}>Include Flight Search</span>
            </label>
          </div>

          {/* Flight Preferences Component */}
          <FlightPreferences formData={formData} setFormData={setFormData} />

          {/* Notes */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Additional Notes (Optional)
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              placeholder="Any special requirements or preferences..."
              rows={4}
              style={{ 
                width: '100%', 
                padding: '0.75rem', 
                fontSize: '1rem',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontFamily: 'inherit'
              }}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={{ 
              padding: '1rem 2rem',
              background: loading ? '#ccc' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '1.1rem',
              fontWeight: 'bold',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background 0.3s'
            }}
          >
            {loading ? 'Creating Trip...' : '🚀 Create Trip'}
          </button>
        </form>
      ) : (
        // Result View
        <div>
    <div style={{ 
      padding: '2rem', 
      background: '#f0f9ff', 
      borderRadius: '12px',
      marginBottom: '2rem'
    }}>
      <h2 style={{ color: '#4CAF50', marginBottom: '1rem' }}>
        ✅ Trip Created Successfully!
      </h2>
      <p style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>
        <strong>Trip ID:</strong> {createdTrip?.id}
      </p>
      <p style={{ fontSize: '1.2rem' }}>
        <strong>Title:</strong> {createdTrip?.title}
      </p>
    </div>

    <FlightSection 
            trip={createdTrip!}
            originCode={originCode}
            destinationCodes={destinationCodes}
    />

    {/* Display Trip JSON */}
    <div style={{ marginBottom: '2rem' }}>
      <h3 style={{ marginBottom: '1rem' }}>Trip Details (JSON):</h3>
      <pre style={{ 
        background: '#1e1e1e', 
        color: '#d4d4d4',
        padding: '1.5rem',
        borderRadius: '8px',
        overflow: 'auto',
        fontSize: '0.9rem'
      }}>
        {JSON.stringify(createdTrip, null, 2)}
      </pre>
    </div>

    {/* Action Buttons */}
    <div style={{ display: 'flex', gap: '1rem' }}>
      <button
        onClick={handleFetchTrip}
        disabled={loading}
        style={{ 
          padding: '1rem 2rem',
          background: '#2196F3',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: loading ? 'not-allowed' : 'pointer',
          fontWeight: 'bold'
        }}
      >
        {loading ? 'Fetching...' : '🔄 Refresh Trip Data'}
      </button>
      <button
        onClick={resetForm}
        style={{ 
          padding: '1rem 2rem',
          background: '#ff9800',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontWeight: 'bold'
        }}
      >
        ➕ Create Another Trip
      </button>
    </div>
  </div>
      )}
    </div>
  );
};

export default Planner;
