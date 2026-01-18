import React from 'react';
import type { DisruptionCase } from '../types/disruption';

interface AlertBannerProps {
  disruptionCase: DisruptionCase;
  onDismiss: () => void;
}

const severityConfig = {
  low: {
    icon: '⚠️',
    title: 'Minor Disruption',
    gradient: 'from-yellow-500/20 to-orange-500/20',
    border: 'border-yellow-500/30',
    text: 'text-yellow-400',
  },
  medium: {
    icon: '🚨',
    title: 'Moderate Disruption',
    gradient: 'from-orange-500/20 to-red-500/20',
    border: 'border-orange-500/30',
    text: 'text-orange-400',
  },
  high: {
    icon: '🔴',
    title: 'Severe Disruption',
    gradient: 'from-red-500/20 to-red-600/20',
    border: 'border-red-500/40',
    text: 'text-red-400',
  },
  critical: {
    icon: '🚫',
    title: 'Critical Disruption',
    gradient: 'from-red-600/30 to-red-700/30',
    border: 'border-red-600/50',
    text: 'text-red-300',
  },
};

export const AlertBanner: React.FC<AlertBannerProps> = ({ disruptionCase, onDismiss }) => {
  const config = severityConfig[disruptionCase.severity] || severityConfig.medium;

  // Get disruption type display text
  const disruptionTypeText = disruptionCase.disruption_type
    .replace('_', ' ')
    .toUpperCase();

  return (
    <div
      className={`bg-gradient-to-r ${config.gradient} border ${config.border} rounded-xl p-4 backdrop-blur-xl animate-slideDown`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          {/* Icon */}
          <span className="text-3xl flex-shrink-0">{config.icon}</span>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h3 className={`font-bold text-lg ${config.text} mb-1`}>
              {disruptionTypeText} - {config.title}
            </h3>
            
            <div className="flex flex-wrap items-center gap-3 text-sm text-gray-300">
              <span className="font-semibold">
                {disruptionCase.flight_number}
              </span>
              <span className="text-gray-500">|</span>
              <span>
                {disruptionCase.origin} → {disruptionCase.destination}
              </span>
              
              {disruptionCase.current_status && (
                <>
                  <span className="text-gray-500">|</span>
                  <span className="text-gray-400">
                    {disruptionCase.current_status}
                  </span>
                </>
              )}
            </div>

            {/* Weather Alert (if severe) */}
            {disruptionCase.meta_data?.weather?.severity === 'high' && (
              <div className="mt-2 flex items-center gap-2 text-sm text-yellow-400">
                <span>🌧️</span>
                <span>Severe weather conditions detected</span>
              </div>
            )}
          </div>
        </div>

        {/* Dismiss Button */}
        <button
          onClick={onDismiss}
          className="text-gray-400 hover:text-white transition-colors flex-shrink-0 p-1 hover:bg-white/10 rounded"
          aria-label="Dismiss alert"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default AlertBanner;
