import { useState } from 'react';
import { X, Sparkles } from 'lucide-react';

interface ReplanDayModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReplan: (preferences: string, keepExisting: boolean) => void;
  dayNumber: number;
  city: string;
  loading?: boolean;
}

export const ReplanDayModal = ({
  isOpen,
  onClose,
  onReplan,
  dayNumber,
  city,
  loading = false
}: ReplanDayModalProps) => {
  const [preferences, setPreferences] = useState('');
  const [keepExisting, setKeepExisting] = useState(false);

  const handleSubmit = () => {
    if (preferences.trim()) {
      onReplan(preferences, keepExisting);
    }
  };

  const handleClose = () => {
    setPreferences('');
    setKeepExisting(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl bg-[#0a0e14]/95 backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-2xl shadow-2xl animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[rgba(148,163,184,0.1)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Re-plan Day {dayNumber}</h2>
              <p className="text-sm text-gray-400 mt-0.5">{city}</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={loading}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              What would you like to change about this day?
            </label>
            <textarea
              value={preferences}
              onChange={(e) => setPreferences(e.target.value)}
              placeholder="E.g., I want more outdoor activities, add a sunset spot, less museums..."
              className="w-full px-4 py-3 bg-[#1a1f2e]/50 border border-[rgba(148,163,184,0.2)] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-[#60A5FA] transition-colors resize-none"
              rows={4}
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-2">
              Tip: Be specific about what you want to add, remove, or change
            </p>
          </div>

          <div className="flex items-center gap-3 p-4 rounded-xl bg-[#1a1f2e]/30 border border-[rgba(148,163,184,0.1)]">
            <input
              type="checkbox"
              id="keepExisting"
              checked={keepExisting}
              onChange={(e) => setKeepExisting(e.target.checked)}
              disabled={loading}
              className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-[#60A5FA] focus:ring-[#60A5FA] focus:ring-offset-0"
            />
            <label htmlFor="keepExisting" className="text-sm text-gray-300 cursor-pointer">
              Keep existing activities and add new ones
            </label>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-[rgba(148,163,184,0.1)]">
          <button
            onClick={handleClose}
            disabled={loading}
            className="px-6 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 text-white font-medium transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !preferences.trim()}
            className="px-6 py-2.5 rounded-lg bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Re-planning...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Re-plan Day</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
