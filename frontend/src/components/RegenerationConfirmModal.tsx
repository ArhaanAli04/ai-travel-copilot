import { AlertTriangle, RefreshCw, Save } from 'lucide-react';

interface RegenerationConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onKeepCurrent: () => void;
  onRegenerate: () => void;
  loading?: boolean;
  oldDates: { start: string; end: string };
  newDates: { start: string; end: string };
  oldTravelers?: number;
  newTravelers?: number;
  changes: {
    datesChanged: boolean;
    travelersChanged: boolean;
    tripTypeChanged: boolean;
    interestsChanged: boolean;
  };
}

export const RegenerationConfirmModal = ({
  isOpen,
  onClose,
  onKeepCurrent,
  onRegenerate,
  loading = false,
  oldDates,
  newDates,
  oldTravelers,
  newTravelers,
  changes,
}: RegenerationConfirmModalProps) => {
  if (!isOpen) return null;

  const calculateDays = (start: string, end: string) => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    const diffTime = Math.abs(endDate.getTime() - startDate.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
    return diffDays;
  };

  const oldDays = calculateDays(oldDates.start, oldDates.end);
  const newDays = calculateDays(newDates.start, newDates.end);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg bg-[#0a0e14]/95 backdrop-blur-xl border border-[#F59E0B]/30 rounded-2xl shadow-2xl animate-scale-in">
        {/* Header */}
        <div className="flex items-start gap-4 p-6 border-b border-[rgba(148,163,184,0.1)]">
          <div className="w-12 h-12 rounded-xl bg-[#F59E0B]/10 border border-[#F59E0B]/30 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-6 h-6 text-[#F59E0B]" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white mb-1">Important Changes Detected</h2>
            <p className="text-sm text-[#9CA3AF]">
              These changes will affect your itinerary
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Changes Summary */}
          <div className="space-y-3">
            {changes.datesChanged && (
              <div className="p-4 rounded-xl bg-[#3B82F6]/10 border border-[#3B82F6]/30">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">📅</span>
                  <h3 className="font-semibold text-white">Date Change</h3>
                </div>
                <div className="text-sm space-y-1">
                  <div className="flex items-center gap-2 text-[#9CA3AF]">
                    <span>Old:</span>
                    <span className="text-white font-medium">
                      {oldDays} days ({new Date(oldDates.start).toLocaleDateString()} - {new Date(oldDates.end).toLocaleDateString()})
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[#9CA3AF]">
                    <span>New:</span>
                    <span className="text-[#38BDF8] font-medium">
                      {newDays} days ({new Date(newDates.start).toLocaleDateString()} - {new Date(newDates.end).toLocaleDateString()})
                    </span>
                  </div>
                </div>
              </div>
            )}

            {changes.travelersChanged && (
              <div className="p-4 rounded-xl bg-[#8B5CF6]/10 border border-[#8B5CF6]/30">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">👥</span>
                  <h3 className="font-semibold text-white">Traveler Count Changed</h3>
                </div>
                <div className="text-sm flex items-center gap-2">
                  <span className="text-[#9CA3AF]">Old: {oldTravelers} travelers</span>
                  <span className="text-[#9CA3AF]">→</span>
                  <span className="text-[#8B5CF6] font-medium">New: {newTravelers} travelers</span>
                </div>
              </div>
            )}

            {(changes.tripTypeChanged || changes.interestsChanged) && (
              <div className="p-4 rounded-xl bg-[#22C55E]/10 border border-[#22C55E]/30">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">🎯</span>
                  <h3 className="font-semibold text-white">Preferences Updated</h3>
                </div>
                <ul className="text-sm text-[#9CA3AF] space-y-1">
                  {changes.tripTypeChanged && <li>• Trip type changed</li>}
                  {changes.interestsChanged && <li>• Interests updated</li>}
                </ul>
              </div>
            )}
          </div>

          {/* Warning */}
          <div className="p-4 rounded-xl bg-[#F59E0B]/10 border border-[#F59E0B]/30">
            <p className="text-sm text-[#FCD34D]">
              ⚠️ Your current itinerary was planned for the old dates and preferences. What would you like to do?
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t border-[rgba(148,163,184,0.1)]">
          <button
            type="button"
            onClick={onKeepCurrent}
            disabled={loading}
            className="flex-1 px-6 py-3 rounded-lg bg-white/5 hover:bg-white/10 text-white font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            Keep Current Itinerary
          </button>
          <button
            type="button"
            onClick={onRegenerate}
            disabled={loading}
            className="flex-1 px-6 py-3 rounded-lg bg-gradient-to-r from-[#F97316] to-[#38BDF8] hover:from-[#EA580C] hover:to-[#3B82F6] text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Regenerating...</span>
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                <span>Regenerate Itinerary</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
