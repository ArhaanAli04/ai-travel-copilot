import React, { useState, useEffect } from 'react';
import { disruptionApi, airportApi } from '../services/api';
import type { CreateDisruptionRequest } from '../types/disruption';

interface DisruptionFormProps {
  onSuccess: (caseId: number) => void;
}

export const DisruptionForm: React.FC<DisruptionFormProps> = ({ onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  
  
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
  

  // Search destination airports
  

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
  if (!formData.origin?.trim()|| formData.origin.length !== 3) {
    setError('Please enter a valid 3-letter origin airport code (e.g., JFK)');
    console.error('❌ Validation failed: origin is empty');
    return;
  }
  if (!formData.destination?.trim() || formData.destination.length !== 3) {
    setError('Please enter a valid 3-letter destination airport code (e.g., LHR)');
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
  

  // Select destination airport
  

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

           {/* Origin & Destination — IATA codes only */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            {/* Origin */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Origin Airport Code <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="origin"
                value={formData.origin}
                onChange={(e) => {
                  const val = e.target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 3);
                  setFormData(prev => ({ ...prev, origin: val }));
                }}
                placeholder="e.g., JFK"
                maxLength={3}
                className="w-full px-4 py-3 bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all font-mono tracking-widest uppercase"
                required
              />
              {formData.origin.length > 0 && formData.origin.length < 3 && (
                <p className="mt-1 text-xs text-yellow-400">IATA codes are 3 letters (e.g., BOM, DEL, JFK)</p>
              )}
              {formData.origin.length === 3 && (
                <p className="mt-1 text-xs text-green-400">✓ Valid IATA code format</p>
              )}
            </div>

            {/* Destination */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Destination Airport Code <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="destination"
                value={formData.destination}
                onChange={(e) => {
                  const val = e.target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 3);
                  setFormData(prev => ({ ...prev, destination: val }));
                }}
                placeholder="e.g., LHR"
                maxLength={3}
                className="w-full px-4 py-3 bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all font-mono tracking-widest uppercase"
                required
              />
              {formData.destination.length > 0 && formData.destination.length < 3 && (
                <p className="mt-1 text-xs text-yellow-400">IATA codes are 3 letters (e.g., BOM, DEL, JFK)</p>
              )}
              {formData.destination.length === 3 && (
                <p className="mt-1 text-xs text-green-400">✓ Valid IATA code format</p>
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
