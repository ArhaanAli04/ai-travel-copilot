import { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';
import type { Trip } from '../services/api';

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
    budget: trip.budget || 0,
    budget_currency: trip.budget_currency,
    start_date: trip.start_date.split('T')[0],
    end_date: trip.end_date.split('T')[0],
    notes: trip.notes || '',
  });

  useEffect(() => {
    if (isOpen) {
      setFormData({
        title: trip.title,
        budget: trip.budget || 0,
        budget_currency: trip.budget_currency,
        start_date: trip.start_date.split('T')[0],
        end_date: trip.end_date.split('T')[0],
        notes: trip.notes || '',
      });
    }
  }, [isOpen, trip]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl bg-[#0a0e14]/95 backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-2xl shadow-2xl animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[rgba(148,163,184,0.1)]">
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
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Trip Title
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
                Start Date
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
                End Date
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

          {/* Budget */}
          <div className="grid grid-cols-3 gap-4">
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
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="INR">INR</option>
              </select>
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
        <div className="flex justify-end gap-3 p-6 border-t border-[rgba(148,163,184,0.1)]">
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
