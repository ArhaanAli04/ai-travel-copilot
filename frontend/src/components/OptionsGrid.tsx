import React, { useState, useEffect } from 'react';
import { disruptionApi } from '../services/api';
import type { DisruptionCase, DisruptionOption } from '../types/disruption';

interface OptionsGridProps {
  disruptionCase: DisruptionCase;
}

const optionIcons: Record<string, string> = {
  refund: '💰',
  hotel_voucher: '🏨',
  compensation: '🎫',
  meal_voucher: '🍽️',
  rebooking: '📞',
};

const optionColors: Record<string, { bg: string; border: string; text: string }> = {
  refund: {
    bg: 'bg-gradient-to-br from-green-500/10 to-emerald-500/10',
    border: 'border-green-500/30',
    text: 'text-green-400',
  },
  hotel_voucher: {
    bg: 'bg-gradient-to-br from-blue-500/10 to-cyan-500/10',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
  },
  compensation: {
    bg: 'bg-gradient-to-br from-purple-500/10 to-pink-500/10',
    border: 'border-purple-500/30',
    text: 'text-purple-400',
  },
  meal_voucher: {
    bg: 'bg-gradient-to-br from-orange-500/10 to-red-500/10',
    border: 'border-orange-500/30',
    text: 'text-orange-400',
  },
  rebooking: {
    bg: 'bg-gradient-to-br from-yellow-500/10 to-orange-500/10',
    border: 'border-yellow-500/30',
    text: 'text-yellow-400',
  },
};

export const OptionsGrid: React.FC<OptionsGridProps> = ({ disruptionCase }) => {
  const [options, setOptions] = useState<DisruptionOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    fetchOptions();
  }, [disruptionCase.id]);

  const fetchOptions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await disruptionApi.suggestOptions(disruptionCase.id);
      // Filter out alternative flights (shown separately)
      const otherOptions = response.options.filter(
        opt => opt.option_type !== 'alternative_flight'
      );
      setOptions(otherOptions);
    } catch (err: any) {
      setError(err.message || 'Failed to load options');
      console.error('Options fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCost = (cost?: number) => {
    if (!cost) return 'Free';
    if (cost < 0) return `+${Math.abs(cost)} refund`;
    return `${cost}`;
  };

  if (loading) {
    return (
      <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <span>💡</span>
          Your Options
        </h3>
        <div className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-gray-400 text-sm">Loading options...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <span>💡</span>
          Your Options
        </h3>
        <div className="text-center py-8 space-y-4">
          <p className="text-red-400 text-sm">{error}</p>
          <button
            onClick={fetchOptions}
            className="px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (options.length === 0) {
    return (
      <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <span>💡</span>
          Your Options
        </h3>
        <div className="text-center py-8">
          <p className="text-gray-400 text-sm">No options available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span>💡</span>
          Your Options
        </h3>
        <span className="text-sm text-gray-400">
          {options.length} option{options.length !== 1 ? 's' : ''} available
        </span>
      </div>

      {/* Options Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-4">
        {options.map((option) => {
          const icon = optionIcons[option.option_type] || '📋';
          const colors = optionColors[option.option_type] || optionColors.compensation;
          const isExpanded = expandedId === option.id;
          const pros = option.meta_data?.pros || [];
          const cons = option.meta_data?.cons || [];

          return (
            <div
              key={option.id}
              className={`p-4 rounded-xl border ${colors.bg} ${colors.border} transition-all hover:scale-[1.02]`}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start gap-3 flex-1">
                  <span className="text-3xl flex-shrink-0">{icon}</span>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-white font-semibold text-lg mb-1">
                      {option.title}
                    </h4>
                    {option.description && (
                      <p className="text-gray-300 text-sm">
                        {option.description}
                      </p>
                    )}
                  </div>
                </div>
                
                {/* Priority Badge */}
                <div className={`px-2 py-1 rounded-lg ${colors.bg} border ${colors.border} text-xs font-medium ${colors.text}`}>
                  #{Math.floor(option.priority_rank / 10)}
                </div>
              </div>

              {/* Cost */}
              {option.estimated_cost !== undefined && option.estimated_cost !== 0 && (
                <div className="mb-3 p-3 bg-[rgba(15,23,42,0.5)] rounded-lg border border-[rgba(148,163,184,0.2)]">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 text-sm">Estimated Cost</span>
                    <span className={`font-bold text-lg ${
                      option.estimated_cost < 0 ? 'text-green-400' : 'text-white'
                    }`}>
                      {option.estimated_cost < 0 ? '+' : ''}
                      {Math.abs(option.estimated_cost)}
                      {option.estimated_cost < 0 && (
                        <span className="text-xs text-green-500 ml-1">refund</span>
                      )}
                    </span>
                  </div>
                </div>
              )}

              {/* Pros/Cons */}
              {(pros.length > 0 || cons.length > 0) && (
                <div className="space-y-2 mb-3">
                  {pros.slice(0, isExpanded ? undefined : 2).map((pro, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm">
                      <span className="text-green-400 flex-shrink-0">✓</span>
                      <span className="text-gray-300">{pro}</span>
                    </div>
                  ))}
                  {cons.slice(0, isExpanded ? undefined : 1).map((con, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-sm">
                      <span className="text-orange-400 flex-shrink-0">•</span>
                      <span className="text-gray-400">{con}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Expanded Details */}
              {isExpanded && (
                <div className="space-y-3 mb-3 pt-3 border-t border-[rgba(148,163,184,0.2)]">
                  {option.action_required && (
                    <div>
                      <div className="text-xs text-gray-500 uppercase mb-1">Action Required</div>
                      <p className="text-gray-300 text-sm">{option.action_required}</p>
                    </div>
                  )}
                  
                  {option.contact_info && (
                    <div>
                      <div className="text-xs text-gray-500 uppercase mb-1">Contact</div>
                      <p className="text-gray-300 text-sm">{option.contact_info}</p>
                    </div>
                  )}

                  {option.ai_reasoning && (
                    <div className="p-2 bg-[rgba(148,163,184,0.1)] rounded text-xs text-gray-400">
                      💡 {option.ai_reasoning}
                    </div>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={() => setExpandedId(isExpanded ? null : option.id)}
                  className="flex-1 py-2 px-4 bg-[rgba(148,163,184,0.1)] hover:bg-[rgba(148,163,184,0.2)] text-gray-300 text-sm rounded-lg transition-colors"
                >
                  {isExpanded ? 'Show Less' : 'View Details'}
                </button>
                
                {option.booking_url && (
                  <a
                    href={option.booking_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="py-2 px-4 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white text-sm font-semibold rounded-lg transition-all"
                  >
                    Start →
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Refresh Button */}
      <div className="mt-4 pt-4 border-t border-[rgba(148,163,184,0.2)] text-center">
        <button
          onClick={fetchOptions}
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          🔄 Refresh options
        </button>
      </div>
    </div>
  );
};

export default OptionsGrid;
