import { X, Lock, Eye } from 'lucide-react';

interface ViewerRestrictedModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ViewerRestrictedModal = ({ isOpen, onClose }: ViewerRestrictedModalProps) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-sm bg-[#0a0e14]/95 backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-2xl shadow-2xl animate-scale-in">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[rgba(148,163,184,0.1)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#F59E0B]/10 flex items-center justify-center">
              <Lock className="w-5 h-5 text-[#F59E0B]" />
            </div>
            <h2 className="text-lg font-bold text-white">View Only Access</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="flex items-start gap-3 p-4 rounded-xl bg-[#F59E0B]/5 border border-[#F59E0B]/20 mb-4">
            <Eye className="w-5 h-5 text-[#F59E0B] flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-white font-medium text-sm mb-1">
                You have viewer access to this trip
              </p>
              <p className="text-[#9CA3AF] text-sm">
                Viewers can browse the itinerary but cannot add, edit, delete, or reorder activities.
              </p>
            </div>
          </div>
          <p className="text-[#6B7280] text-xs">
            Ask the trip owner to upgrade your role to <span className="text-[#38BDF8] font-medium">Editor</span> if you need to make changes.
          </p>
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t border-[rgba(148,163,184,0.1)]">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-lg bg-[#F59E0B]/10 hover:bg-[#F59E0B]/20 text-[#F59E0B] font-medium transition-colors"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
