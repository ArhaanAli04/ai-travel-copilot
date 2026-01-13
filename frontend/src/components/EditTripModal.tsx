import { useState, useEffect } from 'react';
import { X, Save, Plus, Minus } from 'lucide-react';
import type { Trip } from '../services/api';


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

interface EditTripModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (updates: Partial<Trip>) => void;
  trip: Trip;
  loading?: boolean;
}

export const EditTripModal = ({
  isOpen,
  onClose,
  onSave,
  trip,
  loading = false
}: EditTripModalProps) => {
  const [formData, setFormData] = useState({
    title: trip.title,
    start_date: trip.start_date.split('T')[0],
    end_date: trip.end_date.split('T')[0],
    budget: trip.budget || 0,
    budget_currency: trip.budget_currency,
    interests: trip.interests || [],
    trip_type: trip.trip_type,
    traveler_count: trip.traveler_count,
    notes: trip.notes || '',
  });

  
  const [currentInterest, setCurrentInterest] = useState('');

  useEffect(() => {
    if (isOpen) {
      setFormData({
        title: trip.title,
        start_date: trip.start_date.split('T')[0],
        end_date: trip.end_date.split('T')[0],
        budget: trip.budget || 0,
        budget_currency: trip.budget_currency,
        interests: trip.interests || [],
        trip_type: trip.trip_type,
        traveler_count: trip.traveler_count,
        notes: trip.notes || '',
      });
      
    }
  }, [isOpen, trip]);

  const handleTripTypeChange = (type: 'solo' | 'couple' | 'family' | 'group') => {
    const typeConfig = TRIP_TYPES.find(t => t.value === type);
    setFormData(prev => ({ 
      ...prev, 
      trip_type: type,
      traveler_count: typeConfig?.count || 1
    }));
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
    onSave(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-[#0a0e14]/95 backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-2xl shadow-2xl animate-scale-in my-8">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[rgba(148,163,184,0.1)] sticky top-0 bg-[#0a0e14]/95 backdrop-blur-xl z-10 rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#60A5FA] to-[#3B82F6] flex items-center justify-center">
              <Save className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-bold text-white">Edit Trip</h2>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6 max-h-[calc(100vh-200px)] overflow-y-auto">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Trip Title *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-4 py-3 bg-[#1a1f2e]/50 border border-[rgba(148,163,184,0.2)] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-[#60A5FA] transition-colors"
              disabled={loading}
              required
            />
          </div>

          

          {/* Dates */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Start Date *
              </label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="w-full px-4 py-3 bg-[#1a1f2e]/50 border border-[rgba(148,163,184,0.2)] rounded-xl text-white focus:outline-none focus:border-[#60A5FA] transition-colors"
                disabled={loading}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                End Date *
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="w-full px-4 py-3 bg-[#1a1f2e]/50 border border-[rgba(148,163,184,0.2)] rounded-xl text-white focus:outline-none focus:border-[#60A5FA] transition-colors"
                disabled={loading}
                required
              />
            </div>
          </div>

          {/* Budget & Currency */}
          <div className="grid sm:grid-cols-3 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Budget
              </label>
              <input
                type="number"
                value={formData.budget}
                onChange={(e) => setFormData({ ...formData, budget: Number(e.target.value) })}
                className="w-full px-4 py-3 bg-[#1a1f2e]/50 border border-[rgba(148,163,184,0.2)] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-[#60A5FA] transition-colors"
                disabled={loading}
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Currency
              </label>
              <select
                value={formData.budget_currency}
                onChange={(e) => setFormData({ ...formData, budget_currency: e.target.value })}
                className="w-full px-4 py-3 bg-[#1a1f2e]/50 border border-[rgba(148,163,184,0.2)] rounded-xl text-white focus:outline-none focus:border-[#60A5FA] transition-colors"
                disabled={loading}
              >
                {CURRENCIES.map(curr => (
                  <option key={curr} value={curr}>{curr}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Trip Type & Travelers */}
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Trip Type *
              </label>
              <div className="grid grid-cols-2 gap-2">
                {TRIP_TYPES.map((type) => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => handleTripTypeChange(type.value as any)}
                    className={`h-10 rounded-lg transition-all text-sm ${
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

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Travelers *
              </label>
              <div className="flex items-center gap-4 h-10">
                <button
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, traveler_count: Math.max(1, prev.traveler_count - 1) }))}
                  className="h-10 w-10 border border-[rgba(148,163,184,0.2)] text-white hover:bg-white/5 rounded-lg flex items-center justify-center"
                >
                  <Minus className="w-4 h-4" />
                </button>
                <span className="flex-1 text-center text-xl font-semibold text-white">{formData.traveler_count}</span>
                <button
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, traveler_count: prev.traveler_count + 1 }))}
                  className="h-10 w-10 border border-[rgba(148,163,184,0.2)] text-white hover:bg-white/5 rounded-lg flex items-center justify-center"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Interests */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Interests
            </label>
            <div className="flex flex-wrap gap-2 mb-3">
              {INTERESTS.map((interest) => (
                <button
                  key={interest}
                  type="button"
                  onClick={() => toggleInterest(interest)}
                  className={`px-3 py-1.5 text-sm rounded-full transition-all ${
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
            <div className="flex gap-2">
              <input
                type="text"
                value={currentInterest}
                onChange={(e) => setCurrentInterest(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomInterest())}
                placeholder="Add custom interest..."
                className="flex-1 bg-[#1a1f2e]/50 border border-[rgba(148,163,184,0.2)] text-white placeholder-gray-500 rounded-lg h-10 px-4 focus:outline-none focus:border-[#60A5FA] transition-colors"
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

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Notes
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Add any notes about your trip..."
              className="w-full px-4 py-3 bg-[#1a1f2e]/50 border border-[rgba(148,163,184,0.2)] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-[#60A5FA] transition-colors resize-none"
              rows={3}
              disabled={loading}
            />
          </div>
        </form>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-[rgba(148,163,184,0.1)] sticky bottom-0 bg-[#0a0e14]/95 backdrop-blur-xl rounded-b-2xl">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-6 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 text-white font-medium transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={loading}
            className="px-6 py-2.5 rounded-lg bg-gradient-to-r from-[#60A5FA] to-[#3B82F6] hover:from-[#3B82F6] hover:to-[#2563EB] text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Save Changes</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
