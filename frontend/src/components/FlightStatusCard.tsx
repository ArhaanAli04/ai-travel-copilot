import React from 'react';
import { Card } from './shared/Card';
import type { DisruptionCase } from '../types/disruption';

interface FlightStatusCardProps {
  disruptionCase: DisruptionCase;
  onRefresh?: () => void;
  expanded?: boolean;
}

const statusConfig = {
  scheduled: { color: 'text-blue-400',   bg: 'bg-blue-500/10',   icon: '🕐', label: 'Scheduled' },
  active:    { color: 'text-green-400',  bg: 'bg-green-500/10',  icon: '✈️', label: 'In Air'    },
  landed:    { color: 'text-gray-400',   bg: 'bg-gray-500/10',   icon: '🛬', label: 'Landed'    },
  cancelled: { color: 'text-red-400',    bg: 'bg-red-500/10',    icon: '❌', label: 'Cancelled' },
  delayed:   { color: 'text-orange-400', bg: 'bg-orange-500/10', icon: '⏰', label: 'Delayed'   },
};

const severityConfig = {
  low:      { color: 'text-green-400',  bg: 'bg-green-500/10'  },
  medium:   { color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
  high:     { color: 'text-orange-400', bg: 'bg-orange-500/10' },
  critical: { color: 'text-red-400',    bg: 'bg-red-500/10'    },
};

export const FlightStatusCard: React.FC<FlightStatusCardProps> = ({
  disruptionCase,
  onRefresh,
  expanded = false,
}) => {
  const flightStatus = disruptionCase.meta_data?.flight_status;
  const status = flightStatus?.status || 'scheduled';
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.scheduled;
  const sevConfig = severityConfig[disruptionCase.severity] || severityConfig.low;

  const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return 'N/A';
  // AviationStack returns local airport time with wrong UTC offset
  // Strip the timezone offset and display the time value directly
  const localStr = dateStr.replace(/([+-]\d{2}:\d{2}|Z)$/, '');
  const date = new Date(localStr);
  return date.toLocaleString('en-IN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });
};


  const formatDateOnly = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
    });
  };

  const getDelay = (delay?: number) => {
    if (!delay || delay === 0) return null;
    const hours = Math.floor(delay / 60);
    const mins = delay % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const departureIata = flightStatus?.departure?.iata || disruptionCase.origin;
  const arrivalIata   = flightStatus?.arrival?.iata   || disruptionCase.destination;

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
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        )}
      </div>

      {/* Flight number + status badge */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-bold text-white">{disruptionCase.flight_number}</div>
          <div className="text-sm text-gray-400">{disruptionCase.airline}</div>
        </div>
        <div className={`px-3 py-1.5 rounded-lg ${config.bg} flex items-center gap-2`}>
          <span>{config.icon}</span>
          <span className={`text-sm font-medium ${config.color} capitalize`}>{config.label}</span>
        </div>
      </div>

      {/* Route row */}
      <div
        className="flex items-center justify-between px-4 py-3 rounded-xl"
        style={{ background: 'rgba(148,163,184,0.06)', border: '1px solid rgba(148,163,184,0.1)' }}
      >
        <div className="text-center">
          <div className="text-xl font-bold text-white">{departureIata}</div>
          <div className="text-xs text-gray-500 mt-0.5">
            {flightStatus?.departure?.airport || 'Origin'}
          </div>
        </div>
        <div className="flex flex-col items-center gap-1 flex-1 px-3">
          <div className="text-xs text-gray-600">
            {flightStatus?.aircraft || disruptionCase.disruption_type.toUpperCase()}
          </div>
          <div className="w-full flex items-center gap-1">
            <div className="flex-1 h-[1px] bg-gradient-to-r from-transparent via-gray-500 to-transparent" />
            <span className="text-gray-400 text-xs">✈</span>
            <div className="flex-1 h-[1px] bg-gradient-to-r from-transparent via-gray-500 to-transparent" />
          </div>
          <div className="text-xs text-gray-600">Direct</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-bold text-white">{arrivalIata}</div>
          <div className="text-xs text-gray-500 mt-0.5">
            {flightStatus?.arrival?.airport || 'Destination'}
          </div>
        </div>
      </div>

      {/* Collapsed: severity + status note only */}
      {!expanded && (
        <div className="space-y-2">
          <div className={`px-3 py-2.5 rounded-lg ${sevConfig.bg}`} style={{ border: '1px solid rgba(148,163,184,0.08)' }}>
            <div className="text-xs text-gray-500 mb-1">Severity</div>
            <div className={`text-sm font-medium capitalize ${sevConfig.color}`}>{disruptionCase.severity}</div>
          </div>
          {disruptionCase.current_status && (
            <div className="px-3 py-2.5 rounded-lg text-sm text-gray-300" style={{ background: 'rgba(148,163,184,0.06)', border: '1px solid rgba(148,163,184,0.08)' }}>
              <span className="text-gray-500 text-xs block mb-1">Status Note</span>
              {disruptionCase.current_status}
            </div>
          )}
        </div>
      )}

      {/* Expanded: full 2-col grid */}
      {expanded && (
        <div className="grid grid-cols-2 gap-2">
          <div className="px-3 py-2.5 rounded-lg" style={{ background: 'rgba(148,163,184,0.06)', border: '1px solid rgba(148,163,184,0.08)' }}>
            <div className="text-xs text-gray-500 mb-1">Disruption Type</div>
            <div className="text-sm text-white font-medium capitalize">{disruptionCase.disruption_type}</div>
          </div>
          <div className={`px-3 py-2.5 rounded-lg ${sevConfig.bg}`} style={{ border: '1px solid rgba(148,163,184,0.08)' }}>
            <div className="text-xs text-gray-500 mb-1">Severity</div>
            <div className={`text-sm font-medium capitalize ${sevConfig.color}`}>{disruptionCase.severity}</div>
          </div>
          <div className="px-3 py-2.5 rounded-lg" style={{ background: 'rgba(148,163,184,0.06)', border: '1px solid rgba(148,163,184,0.08)' }}>
            <div className="text-xs text-gray-500 mb-1">Disruption Date</div>
            <div className="text-sm text-white font-medium">{formatDateOnly(disruptionCase.disruption_date)}</div>
          </div>
          {disruptionCase.pnr ? (
            <div className="px-3 py-2.5 rounded-lg" style={{ background: 'rgba(148,163,184,0.06)', border: '1px solid rgba(148,163,184,0.08)' }}>
              <div className="text-xs text-gray-500 mb-1">PNR</div>
              <div className="text-sm text-white font-mono font-medium">{disruptionCase.pnr}</div>
            </div>
          ) : <div />}
          {disruptionCase.booking_reference && (
            <div className="px-3 py-2.5 rounded-lg col-span-2" style={{ background: 'rgba(148,163,184,0.06)', border: '1px solid rgba(148,163,184,0.08)' }}>
              <div className="text-xs text-gray-500 mb-1">Booking Ref</div>
              <div className="text-sm text-white font-mono font-medium">{disruptionCase.booking_reference}</div>
            </div>
          )}
          {disruptionCase.current_status && (
            <div className="px-3 py-2.5 rounded-lg col-span-2 text-sm text-gray-300" style={{ background: 'rgba(148,163,184,0.06)', border: '1px solid rgba(148,163,184,0.08)' }}>
              <span className="text-gray-500 text-xs block mb-1">Status Note</span>
              {disruptionCase.current_status}
            </div>
          )}
        </div>
      )}

      {/* Departure Info — only if API returned data */}
      {flightStatus?.departure && (
        <div className="border-t border-[rgba(148,163,184,0.2)] pt-3 space-y-2">
          <div className="text-xs text-gray-500 uppercase tracking-wider">Departure</div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Scheduled</span>
              <span className="text-white font-medium">{formatDateTime(flightStatus.departure.scheduled)}</span>
            </div>
            {flightStatus.departure.actual && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Actual</span>
                <span className="text-green-400 font-medium">{formatDateTime(flightStatus.departure.actual)}</span>
              </div>
            )}
            {flightStatus.departure.delay && flightStatus.departure.delay > 0 && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Delay</span>
                <span className="text-orange-400 font-medium">+{getDelay(flightStatus.departure.delay)}</span>
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

      {/* Arrival Info — only if API returned data */}
      {flightStatus?.arrival && (
        <div className="border-t border-[rgba(148,163,184,0.2)] pt-3 space-y-2">
          <div className="text-xs text-gray-500 uppercase tracking-wider">Arrival</div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Scheduled</span>
              <span className="text-white font-medium">{formatDateTime(flightStatus.arrival.scheduled)}</span>
            </div>
            {flightStatus.arrival.estimated && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Estimated</span>
                <span className="text-blue-400 font-medium">{formatDateTime(flightStatus.arrival.estimated)}</span>
              </div>
            )}
            {flightStatus.arrival.delay && flightStatus.arrival.delay > 0 && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Delay</span>
                <span className="text-orange-400 font-medium">+{getDelay(flightStatus.arrival.delay)}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Last updated */}
      {flightStatus?.fetched_at && (
        <div className="text-xs text-gray-500 text-center pt-1 border-t border-[rgba(148,163,184,0.1)]">
          Updated {new Date(flightStatus.fetched_at).toLocaleTimeString()}
        </div>
      )}
    </Card>
  );
};

export default FlightStatusCard;
