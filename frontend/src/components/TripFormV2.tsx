import { useState } from 'react';
import { Plus, X, Minus, Plane, MapPin, Calendar, DollarSign } from 'lucide-react';
import type { TripCreate } from '../services/api';
import AirportAutocomplete from './AirportAutocomplete';
import FlightPreferences from './FlightPreferences';
import HotelPreferences from './HotelPreferences';

const INTERESTS = [
  "Adventure", "Beach", "Culture", "Food", "History", 
  "Nature", "Nightlife", "Shopping", "Wellness", "Art",
];

const TRIP_TYPES = [
  { value: 'solo', label: 'Solo', count: 1 },
  { value: 'couple', label: 'Couple', count: 2 },
  { value: 'family', label: 'Family', count: 4 },
  { value: 'group', label: 'Group', count: 5 },
];

const CURRENCIES = ["USD", "EUR", "GBP", "INR"];

interface TripFormV2Props {
  formData: TripCreate;
  setFormData: React.Dispatch<React.SetStateAction<TripCreate>>;
  onSubmit: (data: TripCreate) => void;
  loading: boolean;
  originCode: string;
  setOriginCode: (code: string) => void;
  destinationCodes: string[];
  setDestinationCodes: React.Dispatch<React.SetStateAction<string[]>>;
}

export function TripFormV2({
  formData,
  setFormData,
  onSubmit,
  loading,
  originCode,
  setOriginCode,
  destinationCodes,
  setDestinationCodes,
}: TripFormV2Props) {
  const [currentInterest, setCurrentInterest] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'number') {
      setFormData(prev => ({ ...prev, [name]: value ? Number(value) : undefined }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleTripTypeChange = (type: 'solo' | 'couple' | 'family' | 'group') => {
    const typeConfig = TRIP_TYPES.find(t => t.value === type);
    setFormData(prev => ({ 
      ...prev, 
      trip_type: type,
      traveler_count: typeConfig?.count || 1
    }));
  };

  const addDestination = () => {
    setFormData(prev => ({
      ...prev,
      destinations: [...prev.destinations, '']
    }));
    setDestinationCodes(prev => [...prev, '']);
  };

  const updateDestination = (index: number, display: string, code: string) => {
    const newDestinations = [...formData.destinations];
    newDestinations[index] = display;
    setFormData(prev => ({ ...prev, destinations: newDestinations }));
    
    const newCodes = [...destinationCodes];
    newCodes[index] = code;
    setDestinationCodes(newCodes);
  };

  const removeDestination = (index: number) => {
    if (formData.destinations.length > 1) {
      setFormData(prev => ({
        ...prev,
        destinations: prev.destinations.filter((_, i) => i !== index)
      }));
      setDestinationCodes(prev => prev.filter((_, i) => i !== index));
    }
  };

  const toggleInterest = (interest: string) => {
    const interests = formData.interests || [];
    if (interests.includes(interest)) {
      setFormData(prev => ({
        ...prev,
        interests: interests.filter(i => i !== interest)
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        interests: [...interests, interest]
      }));
    }
  };

  const addCustomInterest = () => {
    if (currentInterest.trim() && !formData.interests?.includes(currentInterest.trim())) {
      setFormData(prev => ({
        ...prev,
        interests: [...(prev.interests || []), currentInterest.trim()]
      }));
      setCurrentInterest('');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate
    if (!formData.title || !formData.origin || formData.destinations.some(d => !d.trim())) {
      alert('Please fill all required fields');
      return;
    }

    // Clean and submit
    const cleanedData = {
      ...formData,
      destinations: formData.destinations.filter(d => d.trim()),
    };

    onSubmit(cleanedData);
  };

  return (
    <div className="glass-card rounded-3xl p-6 sm:p-12 max-w-5xl mx-auto animate-fade-in border-[rgba(148,163,184,0.2)]">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2">Create Your Trip</h2>
          <p className="text-[#9CA3AF]">Tell us your travel preferences and let AI plan your perfect journey</p>
        </div>
        <div className="px-3 py-1 rounded-full border border-[#38BDF8] text-[#38BDF8] bg-[#38BDF8]/10 text-sm whitespace-nowrap">
          Step 1 of 2
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Trip Title */}
        <div className="space-y-2">
          <label htmlFor="title" className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
            Trip Title *
          </label>
          <input
            id="title"
            name="title"
            value={formData.title}
            onChange={handleInputChange}
            placeholder="My Amazing Adventure"
            required
            className="w-full bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white placeholder:text-[#6B7280] rounded-lg h-12 px-4 focus:ring-2 focus:ring-[#38BDF8] focus:outline-none transition-all"
          />
        </div>

        {/* Starting From & Destinations */}
        <div className="grid sm:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
              Starting From *
            </label>
            <div className="relative">
              <Plane className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6B7280] z-10 pointer-events-none" />
              <AirportAutocomplete
                value={formData.origin}
                onChange={(display, code) => {
                  setFormData(prev => ({ ...prev, origin: display }));
                  setOriginCode(code);
                }}
                placeholder="San Francisco (SFO)"
                required
                className="pl-11"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
              Destinations *
            </label>
            <div className="space-y-2">
              {formData.destinations.map((dest, index) => (
                <div key={index} className="relative flex gap-2">
                  <div className="relative flex-1">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6B7280] z-10 pointer-events-none" />
                    <AirportAutocomplete
                      value={dest}
                      onChange={(display, code) => updateDestination(index, display, code)}
                      placeholder="Tokyo, Japan"
                      required
                      className="pl-11"
                    />
                  </div>
                  {formData.destinations.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeDestination(index)}
                      className="h-12 w-12 text-[#EF4444] hover:bg-[#EF4444]/10 rounded-lg transition-colors flex items-center justify-center"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                onClick={addDestination}
                className="w-full border border-[#38BDF8] text-[#38BDF8] hover:bg-[#38BDF8]/10 rounded-lg h-10 bg-transparent transition-colors flex items-center justify-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Destination
              </button>
            </div>
          </div>
        </div>

        {/* Dates */}
        <div className="grid sm:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label htmlFor="start_date" className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
              Start Date *
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6B7280] pointer-events-none z-10" />
              <input
                id="start_date"
                name="start_date"
                type="datetime-local"
                value={formData.start_date}
                onChange={handleInputChange}
                required
                className="w-full bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white rounded-lg h-12 pl-11 pr-4 focus:ring-2 focus:ring-[#38BDF8] focus:outline-none transition-all"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="end_date" className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
              End Date *
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6B7280] pointer-events-none z-10" />
              <input
                id="end_date"
                name="end_date"
                type="datetime-local"
                value={formData.end_date}
                onChange={handleInputChange}
                required
                className="w-full bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white rounded-lg h-12 pl-11 pr-4 focus:ring-2 focus:ring-[#38BDF8] focus:outline-none transition-all"
              />
            </div>
          </div>
        </div>

        {/* Budget & Currency */}
        <div className="grid sm:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label htmlFor="budget" className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
              Budget (Optional)
            </label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6B7280]" />
              <input
                id="budget"
                name="budget"
                type="number"
                value={formData.budget || ''}
                onChange={handleInputChange}
                placeholder="5000"
                className="w-full bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white placeholder:text-[#6B7280] rounded-lg h-12 pl-11 pr-4 focus:ring-2 focus:ring-[#38BDF8] focus:outline-none transition-all"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">Currency</label>
            <div className="flex gap-2">
              {CURRENCIES.map((curr) => (
                <button
                  key={curr}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, budget_currency: curr }))}
                  className={`flex-1 h-12 rounded-lg transition-all ${
                    formData.budget_currency === curr
                      ? "bg-[#38BDF8] text-white hover:bg-[#3B82F6]"
                      : "border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] hover:bg-white/5"
                  }`}
                >
                  {curr}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Trip Type & Travelers */}
        <div className="grid sm:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">Trip Type *</label>
            <div className="grid grid-cols-2 gap-2">
              {TRIP_TYPES.map((type) => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => handleTripTypeChange(type.value as any)}
                  className={`h-12 rounded-lg transition-all ${
                    formData.trip_type === type.value
                      ? "bg-[#38BDF8] text-white hover:bg-[#3B82F6]"
                      : "border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] hover:bg-white/5"
                  }`}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">Travelers *</label>
            <div className="flex items-center gap-4 h-12">
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, traveler_count: Math.max(1, prev.traveler_count - 1) }))}
                className="h-12 w-12 border border-[rgba(148,163,184,0.2)] text-white hover:bg-white/5 rounded-lg flex items-center justify-center"
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="flex-1 text-center text-2xl font-semibold text-white">{formData.traveler_count}</span>
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, traveler_count: prev.traveler_count + 1 }))}
                className="h-12 w-12 border border-[rgba(148,163,184,0.2)] text-white hover:bg-white/5 rounded-lg flex items-center justify-center"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Interests */}
        <div className="space-y-3">
          <label className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">Interests</label>
          <div className="flex flex-wrap gap-2">
            {INTERESTS.map((interest) => (
              <button
                key={interest}
                type="button"
                onClick={() => toggleInterest(interest)}
                className={`px-4 py-2 text-sm rounded-full transition-all hover:scale-105 ${
                  formData.interests?.includes(interest)
                    ? "bg-[#38BDF8] text-white border border-[#38BDF8]"
                    : "border border-[rgba(148,163,184,0.2)] text-[#9CA3AF] hover:bg-white/5"
                }`}
              >
                {interest}
              </button>
            ))}
          </div>
          
          {/* Custom Interest Input */}
          <div className="flex gap-2 mt-3">
            <input
              type="text"
              value={currentInterest}
              onChange={(e) => setCurrentInterest(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomInterest())}
              placeholder="Add custom interest..."
              className="flex-1 bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white placeholder:text-[#6B7280] rounded-lg h-10 px-4 focus:ring-2 focus:ring-[#38BDF8] focus:outline-none transition-all"
            />
            <button
              type="button"
              onClick={addCustomInterest}
              className="px-4 h-10 bg-[#38BDF8] text-white rounded-lg hover:bg-[#3B82F6] transition-colors"
            >
              Add
            </button>
          </div>
        </div>

        {/* Include Flights Toggle */}
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-lg bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)]">
            <div>
              <label htmlFor="include_flights" className="text-base font-semibold text-white cursor-pointer">
                Include Flight Search
              </label>
              <p className="text-sm text-[#9CA3AF] mt-1">Find and compare flights for your trip</p>
            </div>
            <input
              type="checkbox"
              id="include_flights"
              checked={formData.include_flights}
              onChange={(e) => setFormData(prev => ({ ...prev, include_flights: e.target.checked }))}
              className="w-11 h-6 bg-gray-700 rounded-full appearance-none cursor-pointer relative
                         checked:bg-[#38BDF8] transition-colors
                         before:content-[''] before:absolute before:w-5 before:h-5 before:rounded-full 
                         before:bg-white before:top-0.5 before:left-0.5 before:transition-transform
                         checked:before:translate-x-5"
            />
          </div>

          {/* Flight Preferences - Use existing component */}
          {formData.include_flights && (
            <div className="animate-fade-in">
              <FlightPreferences formData={formData} setFormData={setFormData} />
            </div>
          )}
        </div>

        {/* Include Hotels Toggle */}
        <div className="flex items-center justify-between p-4 rounded-lg bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)]">
          <div>
            <label htmlFor="include_hotels" className="text-base font-semibold text-white cursor-pointer">
              Include Hotel Search
            </label>
            <p className="text-sm text-[#9CA3AF] mt-1">Find and save hotels for your trip</p>
          </div>
          <input
            type="checkbox"
            id="include_hotels"
            checked={formData.include_hotels ?? false}
            onChange={(e) => setFormData(prev => ({ ...prev, include_hotels: e.target.checked }))}
            className="w-11 h-6 bg-gray-700 rounded-full appearance-none cursor-pointer relative
                      checked:bg-[#F59E0B] transition-colors
                      before:content-[''] before:absolute before:w-5 before:h-5 before:rounded-full
                      before:bg-white before:top-0.5 before:left-0.5 before:transition-transform
                      checked:before:translate-x-5"
          />
        </div>

        {formData.include_hotels && (
          <div className="animate-fade-in">
            <HotelPreferences formData={formData} setFormData={setFormData} />
          </div>
        )}

        {/* Notes */}
        <div className="space-y-2">
          <label htmlFor="notes" className="text-xs font-semibold tracking-wide uppercase text-[#9CA3AF]">
            Additional Notes
          </label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes}
            onChange={handleInputChange}
            placeholder="Any special requests or preferences..."
            rows={4}
            className="w-full bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white placeholder:text-[#6B7280] rounded-lg p-4 focus:ring-2 focus:ring-[#38BDF8] focus:outline-none transition-all resize-none"
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className={`w-full h-14 text-lg font-semibold rounded-xl shadow-lg transition-all ${
            loading
              ? 'bg-gray-600 cursor-not-allowed'
              : 'bg-gradient-to-r from-[#F97316] to-[#38BDF8] hover:from-[#EA580C] hover:to-[#3B82F6] hover:scale-[1.02] shadow-[#F97316]/20'
          } text-white`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              Creating Trip...
            </span>
          ) : (
            '🚀 Create Trip'
          )}
        </button>
      </form>
    </div>
  );
}
