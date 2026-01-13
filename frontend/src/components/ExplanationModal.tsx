import { X } from 'lucide-react';
import { type ActivityExplanation } from '../services/api';

interface ExplanationModalProps {
  isOpen: boolean;
  onClose: () => void;
  explanation: ActivityExplanation | null;
  activityTitle: string;
  loading: boolean;
}

export const ExplanationModal = ({
  isOpen,
  onClose,
  explanation,
  activityTitle,
  loading
}: ExplanationModalProps) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl bg-[#0a0e14]/95 backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-2xl shadow-2xl animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[rgba(148,163,184,0.1)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#60A5FA] to-[#3B82F6] flex items-center justify-center">
              <span className="text-xl">💡</span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Why We Recommended This</h2>
              <p className="text-sm text-gray-400 mt-0.5">{activityTitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-12 h-12 border-4 border-[#60A5FA]/30 border-t-[#60A5FA] rounded-full animate-spin"></div>
              <p className="text-gray-400 mt-4">Generating explanation...</p>
            </div>
          ) : explanation ? (
            <div className="space-y-6">
              {/* Explanation Text */}
              <div className="p-4 rounded-xl bg-[#1a1f2e]/50 border border-[rgba(148,163,184,0.1)]">
                <p className="text-gray-200 leading-relaxed">
                  {explanation.explanation}
                </p>
                {explanation.cached && (
                  <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                    <span>Cached response</span>
                  </div>
                )}
              </div>

              {/* Sources */}
              {explanation.has_sources && explanation.sources.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
                    <span>📚</span>
                    <span>Sources</span>
                  </h3>
                  <div className="space-y-2">
                    {explanation.sources.map((source, idx) => (
                      <a
                        key={idx}
                        href={source.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block p-3 rounded-lg bg-[#1a1f2e]/30 border border-[rgba(148,163,184,0.1)] hover:border-[#60A5FA]/50 transition-colors group"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-200 group-hover:text-[#60A5FA] transition-colors">
                              {source.source_title}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              {source.city} • {source.theme}
                            </p>
                          </div>
                          <div className="text-xs text-gray-500 flex items-center gap-1">
                            <span className="text-[#60A5FA]">↗</span>
                          </div>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400">
              <p>No explanation available</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-[rgba(148,163,184,0.1)]">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 text-white font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
