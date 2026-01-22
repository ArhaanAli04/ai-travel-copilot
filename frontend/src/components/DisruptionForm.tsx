import React, { useState, useEffect } from 'react';
import { disruptionApi, airportApi } from '../services/api';
import type { CreateDisruptionRequest } from '../types/disruption';
import type { AirportSuggestion } from '../services/api';

interface DisruptionFormProps {
  onSuccess: (caseId: number) => void;
}

export const DisruptionForm: React.FC<DisruptionFormProps> = ({ onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Airport autocomplete state
  const [originSearch, setOriginSearch] = useState('');
  const [destinationSearch, setDestinationSearch] = useState('');
  const [originSuggestions, setOriginSuggestions] = useState<AirportSuggestion[]>([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState<AirportSuggestion[]>([]);
  const [showOriginDropdown, setShowOriginDropdown] = useState(false);
  const [showDestDropdown, setShowDestDropdown] = useState(false);
  
  const [formData, setFormData] = useState<CreateDisruptionRequest>({
    flight_number: '',
    airline: '',
    origin: '',
    destination: '',
    disruption_date: '',
    pnr: '',
    notes: '',
  });

  // Search origin airports
  useEffect(() => {
    const searchAirports = async () => {
      if (originSearch.length < 2) {
        setOriginSuggestions([]);
        return;
      }
      
      try {
        const results = await airportApi.searchAirports(originSearch);
        setOriginSuggestions(results);
      } catch (err) {
        console.error('Failed to search airports:', err);
      }
    };
    
    const timer = setTimeout(searchAirports, 300);
    return () => clearTimeout(timer);
  }, [originSearch]);

  // Search destination airports
  useEffect(() => {
    const searchAirports = async () => {
      if (destinationSearch.length < 2) {
        setDestinationSuggestions([]);
        return;
      }
      
      try {
        const results = await airportApi.searchAirports(destinationSearch);
        setDestinationSuggestions(results);
      } catch (err) {
        console.error('Failed to search airports:', err);
      }
    };
    
    const timer = setTimeout(searchAirports, 300);
    return () => clearTimeout(timer);
  }, [destinationSearch]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
  setError(null);
  
  // ✅ DEBUG: Log everything
  console.log('===== FORM SUBMISSION DEBUG =====');
  console.log('formData:', JSON.stringify(formData, null, 2));
  console.log('flight_number:', formData.flight_number, '| empty?', !formData.flight_number?.trim());
  console.log('airline:', formData.airline, '| empty?', !formData.airline?.trim());
  console.log('origin:', formData.origin, '| empty?', !formData.origin?.trim());
  console.log('destination:', formData.destination, '| empty?', !formData.destination?.trim());
  console.log('disruption_date:', formData.disruption_date, '| empty?', !formData.disruption_date?.trim());
  console.log('================================');

  // Validate required fields
  if (!formData.flight_number?.trim()) {
    setError('Please enter flight number');
    console.error('❌ Validation failed: flight_number is empty');
    return;
  }
  if (!formData.airline?.trim()) {
    setError('Please enter airline name');
    console.error('❌ Validation failed: airline is empty');
    return;
  }
  if (!formData.origin?.trim()) {
    setError('Please select origin airport');
    console.error('❌ Validation failed: origin is empty');
    return;
  }
  if (!formData.destination?.trim()) {
    setError('Please select destination airport');
    console.error('❌ Validation failed: destination is empty');
    return;
  }
  if (!formData.disruption_date?.trim()) {
    setError('Please select flight date');
    console.error('❌ Validation failed: disruption_date is empty');
    return;
  }

  setLoading(true);

  try {
    console.log('✅ Validation passed! Submitting to API...');
    console.log('📝 Submitting disruption case:', formData);

    // Create disruption case
    const response = await disruptionApi.createCase(formData);
    
    console.log('✅ Case created:', response);
    
    // Call success callback with case ID
    onSuccess(response.id);
  } catch (err: any) {
    const errorMsg = err.response?.data?.detail || err.message || 'Failed to create disruption case';
    setError(errorMsg);
    console.error('Form submission error:', err);
  } finally {
    setLoading(false);
  }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Select origin airport
  const selectOrigin = (airport: AirportSuggestion) => {
    const displayValue = `${airport.city}, ${airport.country} (${airport.code})`;
    setFormData(prev => ({ ...prev, origin: displayValue }));
    setOriginSearch(displayValue);
    setShowOriginDropdown(false);
    console.log('✅ Selected origin:', displayValue);
  };

  // Select destination airport
  const selectDestination = (airport: AirportSuggestion) => {
    const displayValue = `${airport.city}, ${airport.country} (${airport.code})`;
    setFormData(prev => ({ ...prev, destination: displayValue }));
    setDestinationSearch(displayValue);
    setShowDestDropdown(false);
    console.log('✅ Selected destination:', displayValue);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-2xl p-8 shadow-2xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-orange-500 to-red-500 mb-4">
            <span className="text-3xl">🚨</span>
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Report Flight Disruption</h2>
          <p className="text-gray-400">Enter your flight details to get instant assistance</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Flight Number & Airline */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Flight Number <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="flight_number"
                value={formData.flight_number}
                onChange={handleChange}
                placeholder="e.g., AA123"
                className="w-full px-4 py-3 bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all uppercase"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Airline <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="airline"
                value={formData.airline}
                onChange={handleChange}
                placeholder="e.g., American Airlines"
                className="w-full px-4 py-3 bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all"
                required
              />
            </div>
          </div>

          {/* Origin & Destination with Autocomplete */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  {/* Origin */}
  <div className="relative">
    <label className="block text-sm font-medium text-gray-300 mb-2">
      Origin Airport <span className="text-red-400">*</span>
    </label>
    <input
      type="text"
      value={originSearch}
      onChange={(e) => {
        const value = e.target.value;
        setOriginSearch(value);
        // ✅ IMMEDIATELY update formData as user types
        setFormData(prev => ({ ...prev, origin: value }));
        setShowOriginDropdown(true);
      }}
      onFocus={() => setShowOriginDropdown(true)}
      onBlur={() => {
        // ✅ Close dropdown after short delay
        setTimeout(() => setShowOriginDropdown(false), 200);
      }}
      placeholder="Type city or airport code..."
      className="w-full px-4 py-3 bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all"
      required
    />
    
    {/* Dropdown */}
    {showOriginDropdown && originSuggestions.length > 0 && (
      <div 
        className="absolute z-50 w-full mt-1 bg-[rgba(15,23,42,0.98)] backdrop-blur-xl border border-[rgba(148,163,184,0.3)] rounded-lg shadow-2xl max-h-60 overflow-y-auto"
      >
        {originSuggestions.map((airport, idx) => (
          <button
            key={idx}
            type="button"
            onMouseDown={(e) => {
              e.preventDefault(); // Prevent blur
              selectOrigin(airport);
            }}
            className="w-full px-4 py-3 text-left hover:bg-[rgba(249,115,22,0.1)] transition-colors text-white border-b border-[rgba(148,163,184,0.1)] last:border-b-0"
          >
            <div className="font-medium text-sm">{airport.city}, {airport.country}</div>
            <div className="text-xs text-gray-400 mt-1">
              <span className="font-mono bg-orange-500/20 px-2 py-0.5 rounded">{airport.code}</span>
              <span className="ml-2">{airport.name}</span>
            </div>
          </button>
        ))}
      </div>
    )}
    
    {/* Visual indicator */}
    {formData.origin && formData.origin.includes('(') && (
      <div className="mt-1 text-xs text-green-400 flex items-center gap-1">
        <span>✓</span>
        <span>Airport selected from list</span>
      </div>
    )}
    {formData.origin && !formData.origin.includes('(') && (
      <div className="mt-1 text-xs text-yellow-400 flex items-center gap-1">
        <span>⚠</span>
        <span>Manual entry - will be auto-resolved</span>
      </div>
    )}
  </div>

  {/* Destination */}
  <div className="relative">
    <label className="block text-sm font-medium text-gray-300 mb-2">
      Destination Airport <span className="text-red-400">*</span>
    </label>
    <input
      type="text"
      value={destinationSearch}
      onChange={(e) => {
        const value = e.target.value;
        setDestinationSearch(value);
        // ✅ IMMEDIATELY update formData as user types
        setFormData(prev => ({ ...prev, destination: value }));
        setShowDestDropdown(true);
      }}
      onFocus={() => setShowDestDropdown(true)}
      onBlur={() => {
        setTimeout(() => setShowDestDropdown(false), 200);
      }}
      placeholder="Type city or airport code..."
      className="w-full px-4 py-3 bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all"
      required
    />
    
    {/* Dropdown */}
    {showDestDropdown && destinationSuggestions.length > 0 && (
      <div 
        className="absolute z-50 w-full mt-1 bg-[rgba(15,23,42,0.98)] backdrop-blur-xl border border-[rgba(148,163,184,0.3)] rounded-lg shadow-2xl max-h-60 overflow-y-auto"
      >
        {destinationSuggestions.map((airport, idx) => (
          <button
            key={idx}
            type="button"
            onMouseDown={(e) => {
              e.preventDefault();
              selectDestination(airport);
            }}
            className="w-full px-4 py-3 text-left hover:bg-[rgba(249,115,22,0.1)] transition-colors text-white border-b border-[rgba(148,163,184,0.1)] last:border-b-0"
          >
            <div className="font-medium text-sm">{airport.city}, {airport.country}</div>
            <div className="text-xs text-gray-400 mt-1">
              <span className="font-mono bg-orange-500/20 px-2 py-0.5 rounded">{airport.code}</span>
              <span className="ml-2">{airport.name}</span>
            </div>
          </button>
        ))}
      </div>
    )}
    
    {/* Visual indicator */}
    {formData.destination && formData.destination.includes('(') && (
      <div className="mt-1 text-xs text-green-400 flex items-center gap-1">
        <span>✓</span>
        <span>Airport selected from list</span>
      </div>
    )}
    {formData.destination && !formData.destination.includes('(') && (
      <div className="mt-1 text-xs text-yellow-400 flex items-center gap-1">
        <span>⚠</span>
        <span>Manual entry - will be auto-resolved</span>
      </div>
    )}
  </div>
</div>

          {/* Disruption Date & PNR */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Flight Date & Time <span className="text-red-400">*</span>
              </label>
              <input
                type="datetime-local"
                name="disruption_date"
                value={formData.disruption_date}
                onChange={handleChange}
                className="w-full px-4 py-3 bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Booking Reference (PNR)
              </label>
              <input
                type="text"
                name="pnr"
                value={formData.pnr}
                onChange={handleChange}
                placeholder="e.g., ABC123"
                className="w-full px-4 py-3 bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all uppercase"
              />
            </div>
          </div>

          {/* Additional Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Additional Notes
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              placeholder="Describe your disruption (e.g., 'Flight delayed 3 hours', 'Cancelled due to weather')..."
              rows={3}
              className="w-full px-4 py-3 bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all resize-none"
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg animate-fade-in">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-orange-500/20"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Analyzing...
              </span>
            ) : (
              'Get Assistance →'
            )}
          </button>
        </form>

        {/* Info Footer */}
        <div className="mt-6 pt-6 border-t border-[rgba(148,163,184,0.2)]">
          <p className="text-xs text-gray-400 text-center">
            💡 We'll automatically check flight status, weather conditions, and your passenger rights
          </p>
        </div>
      </div>
    </div>
  );
};

export default DisruptionForm;
