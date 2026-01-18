import React from 'react';
import { Card } from './shared/Card';
import type { DisruptionCase } from '../types/disruption';

interface FlightStatusCardProps {
  disruptionCase: DisruptionCase;
  onRefresh?: () => void;
}

const statusConfig = {
  scheduled: { color: 'text-blue-400', bg: 'bg-blue-500/10', icon: '🕐' },
  active: { color: 'text-green-400', bg: 'bg-green-500/10', icon: '✈️' },
  landed: { color: 'text-gray-400', bg: 'bg-gray-500/10', icon: '🛬' },
  cancelled: { color: 'text-red-400', bg: 'bg-red-500/10', icon: '❌' },
  delayed: { color: 'text-orange-400', bg: 'bg-orange-500/10', icon: '⏰' },
};

export const FlightStatusCard: React.FC<FlightStatusCardProps> = ({ 
  disruptionCase, 
  onRefresh 
}) => {
  const flightStatus = disruptionCase.meta_data?.flight_status;
  const status = flightStatus?.status || 'scheduled';
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.scheduled;

  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getDelay = (delay?: number) => {
    if (!delay || delay === 0) return null;
    const hours = Math.floor(delay / 60);
    const mins = delay % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  return (
    <Card className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span>📍</span>
          Flight Status
        </h3>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="text-gray-400 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
            title="Refresh status"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        )}
      </div>

      {/* Flight Number & Status */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-white">
              {disruptionCase.flight_number}
            </div>
            <div className="text-sm text-gray-400">
              {disruptionCase.airline}
            </div>
          </div>
          
          <div className={`px-3 py-1 rounded-lg ${config.bg} flex items-center gap-2`}>
            <span>{config.icon}</span>
            <span className={`text-sm font-medium ${config.color} capitalize`}>
              {status}
            </span>
          </div>
        </div>

        {/* Route */}
        <div className="flex items-center gap-2 text-gray-300">
          <span className="font-semibold">{flightStatus?.departure?.iata || disruptionCase.origin}</span>
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
          <span className="font-semibold">{flightStatus?.arrival?.iata || disruptionCase.destination}</span>
        </div>
      </div>

      {/* Departure Info */}
      {flightStatus?.departure && (
        <div className="border-t border-[rgba(148,163,184,0.2)] pt-3 space-y-2">
          <div className="text-xs text-gray-500 uppercase">Departure</div>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Scheduled</span>
              <span className="text-white font-medium">
                {formatDateTime(flightStatus.departure.scheduled)}
              </span>
            </div>
            
            {flightStatus.departure.actual && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Actual</span>
                <span className="text-green-400 font-medium">
                  {formatDateTime(flightStatus.departure.actual)}
                </span>
              </div>
            )}

            {flightStatus.departure.delay && flightStatus.departure.delay > 0 && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Delay</span>
                <span className="text-orange-400 font-medium">
                  +{getDelay(flightStatus.departure.delay)}
                </span>
              </div>
            )}

            {flightStatus.departure.terminal && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Terminal</span>
                <span className="text-white">
                  {flightStatus.departure.terminal}
                  {flightStatus.departure.gate && ` · Gate ${flightStatus.departure.gate}`}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Arrival Info */}
      {flightStatus?.arrival && (
        <div className="border-t border-[rgba(148,163,184,0.2)] pt-3 space-y-2">
          <div className="text-xs text-gray-500 uppercase">Arrival</div>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Scheduled</span>
              <span className="text-white font-medium">
                {formatDateTime(flightStatus.arrival.scheduled)}
              </span>
            </div>

            {flightStatus.arrival.estimated && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Estimated</span>
                <span className="text-blue-400 font-medium">
                  {formatDateTime(flightStatus.arrival.estimated)}
                </span>
              </div>
            )}

            {flightStatus.arrival.delay && flightStatus.arrival.delay > 0 && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Delay</span>
                <span className="text-orange-400 font-medium">
                  +{getDelay(flightStatus.arrival.delay)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Last Updated */}
      {flightStatus?.fetched_at && (
        <div className="text-xs text-gray-500 text-center pt-2 border-t border-[rgba(148,163,184,0.2)]">
          Updated {new Date(flightStatus.fetched_at).toLocaleTimeString()}
        </div>
      )}
    </Card>
  );
};

export default FlightStatusCard;
