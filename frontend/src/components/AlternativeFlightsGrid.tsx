import React, { useState, useEffect } from 'react';
import { disruptionApi } from '../services/api';
import type { DisruptionCase, DisruptionOption } from '../types/disruption';

interface AlternativeFlightsGridProps {
  disruptionCase: DisruptionCase;
}

export const AlternativeFlightsGrid: React.FC<AlternativeFlightsGridProps> = ({ disruptionCase }) => {
  const [options, setOptions] = useState<DisruptionOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchOptions();
  }, [disruptionCase.id]);

  const fetchOptions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await disruptionApi.suggestOptions(disruptionCase.id);
      // Filter only alternative flight options
      const flightOptions = response.options.filter(
        opt => opt.option_type === 'alternative_flight'
      );
      console.log(`✈️ Found ${flightOptions.length} alternative flight options`);
      setOptions(flightOptions);
    } catch (err: any) {
      setError(err.message || 'Failed to load alternatives');
      console.error('Options fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const parseFlightFromOption = (option: DisruptionOption) => {
    // ✅ First try to use meta_data if available
    if (option.meta_data && typeof option.meta_data === 'object') {
        const flightDetails = (option.meta_data as any).flight_details;
        if (flightDetails) {
        console.log('✅ Using real flight data from meta_data:', flightDetails);
        return {
            flight_number: flightDetails.flight_number,
            airline: flightDetails.airline,
            departure_time: flightDetails.departure_time,
            arrival_time: flightDetails.arrival_time,
            duration_minutes: flightDetails.duration_minutes,
            stops: flightDetails.stops,
            price_amount: flightDetails.price_amount,
            price_currency: flightDetails.price_currency,
            booking_url: option.booking_url || undefined,
        };
        }
    }
    
    // ⚠️ Fallback: Parse from text if meta_data is missing
    console.warn('⚠️ meta_data missing, parsing from text (less accurate)');
    // Extract flight number and airline from title
    // Example: "Rebook on AA 295 (American)"
    const titleMatch = option.title.match(/([A-Z0-9]+)\s+\(([^)]+)\)/);
    const flightNumber = titleMatch ? titleMatch[1] : 'Unknown';
    const airline = titleMatch ? titleMatch[2] : disruptionCase.airline;

    // Extract departure time from description
    // Example: "Alternative flight departing at 09:00 AM"
    const timeMatch = option.description?.match(/(\d{1,2}:\d{2}\s*[AP]M)/i);
    const departureTime = timeMatch ? timeMatch[1] : '12:00 PM';

    // Extract stops and duration from ai_reasoning
    // Example: "Alternative flight with 0 stop(s), duration 494min"
    const stopsMatch = option.ai_reasoning?.match(/(\d+)\s+stop/i);
    const durationMatch = option.ai_reasoning?.match(/(\d+)min/i);
    
    const stops = stopsMatch ? parseInt(stopsMatch[1]) : 0;
    const durationMinutes = durationMatch ? parseInt(durationMatch[1]) : 120;

    // Calculate estimated arrival time
    const depTime = new Date();
    const [hours, minutesPart] = departureTime.split(':');
    const minutes = parseInt(minutesPart.replace(/[AP]M/i, '').trim());
    const isPM = departureTime.toUpperCase().includes('PM');
    let hour = parseInt(hours);
    if (isPM && hour !== 12) hour += 12;
    if (!isPM && hour === 12) hour = 0;
    
    depTime.setHours(hour, minutes, 0, 0);
    const arrTime = new Date(depTime.getTime() + durationMinutes * 60000);

    return {
      flight_number: flightNumber,
      airline: airline,
      departure_time: depTime.toISOString(),
      arrival_time: arrTime.toISOString(),
      duration_minutes: durationMinutes,
      stops: stops,
      price_amount: option.estimated_cost || 0,
      price_currency: 'USD',
      booking_url: option.booking_url || undefined,
    };
  };

  const formatTime = (timeStr: string) => {
    const date = new Date(timeStr);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  if (loading) {
    return (
      <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <span>✈️</span>
          Alternative Flights
        </h3>
        <div className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-gray-400 text-sm">Searching alternative flights...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <span>✈️</span>
          Alternative Flights
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
          <span>✈️</span>
          Alternative Flights
        </h3>
        <div className="text-center py-8">
          <p className="text-gray-400 text-sm">No alternative flights found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span>✈️</span>
          Alternative Flights
        </h3>
        <span className="text-sm text-gray-400">
          {options.length} option{options.length !== 1 ? 's' : ''} found
        </span>
      </div>

      {/* Flight Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-4">
        {options.map((option) => {
          // ✅ Parse flight details from option data
          const flight = parseFlightFromOption(option);
          const isRecommended = option.priority_rank >= 90;

          return (
            <div
              key={option.id}
              className={`relative p-4 rounded-xl border transition-all hover:scale-[1.02] ${
                isRecommended
                  ? 'bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/40 shadow-lg shadow-green-500/10'
                  : 'bg-[rgba(15,23,42,0.5)] border-[rgba(148,163,184,0.2)] hover:border-[rgba(148,163,184,0.4)]'
              }`}
            >
              {/* Recommended Badge */}
              {isRecommended && (
                <div className="absolute -top-2 -right-2 px-3 py-1 bg-green-500 text-white text-xs font-bold rounded-full shadow-lg">
                  ⭐ Best
                </div>
              )}

              {/* Flight Header */}
              <div className="flex items-center justify-between mb-3">
                <div>
                  <div className="text-white font-bold text-lg">
                    {flight.flight_number}
                  </div>
                  <div className="text-gray-400 text-sm">{flight.airline}</div>
                </div>
                
                {/* Stops Badge */}
                <div className={`px-2 py-1 rounded-lg text-xs font-medium ${
                  flight.stops === 0
                    ? 'bg-green-500/10 text-green-400 border border-green-500/30'
                    : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
                }`}>
                  {flight.stops === 0 ? 'Direct' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}
                </div>
              </div>

              {/* Times */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex-1">
                  <div className="text-2xl font-bold text-white">
                    {formatTime(flight.departure_time)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {disruptionCase.origin}
                  </div>
                </div>

                <div className="flex-1 flex flex-col items-center px-2">
                  <div className="text-xs text-gray-500 mb-1">
                    {formatDuration(flight.duration_minutes)}
                  </div>
                  <div className="w-full h-[2px] bg-gradient-to-r from-blue-500/30 via-blue-400 to-blue-500/30 relative">
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                      <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                      </svg>
                    </div>
                  </div>
                </div>

                <div className="flex-1 text-right">
                  <div className="text-2xl font-bold text-white">
                    {formatTime(flight.arrival_time)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {disruptionCase.destination}
                  </div>
                </div>
              </div>

              {/* Price */}
              <div className="flex items-center justify-between mb-3 pt-3 border-t border-[rgba(148,163,184,0.2)]">
                <span className="text-gray-400 text-sm">Estimated Cost</span>
                <div className="text-right">
                  <div className="text-xl font-bold text-white">
                    ${Math.abs(flight.price_amount)}
                  </div>
                </div>
              </div>

              {/* Description */}
              <div className="text-xs text-gray-400 mb-3">
                {option.description}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                {flight.booking_url && (
                  <a
                    href={flight.booking_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 py-2 px-4 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white text-sm font-semibold rounded-lg transition-all text-center"
                  >
                    Book Now →
                  </a>
                )}
                <button
                  onClick={() => {
                    const message = `Contact ${flight.airline} to rebook on flight ${flight.flight_number}.\n\n${option.contact_info || 'Check airline website for contact details.'}`;
                    alert(message);
                  }}
                  className="px-4 py-2 bg-[rgba(148,163,184,0.1)] hover:bg-[rgba(148,163,184,0.2)] text-gray-300 text-sm rounded-lg transition-colors"
                >
                  Contact
                </button>
              </div>

              {/* AI Reasoning */}
              {option.ai_reasoning && (
                <div className="mt-3 pt-3 border-t border-[rgba(148,163,184,0.2)]">
                  <div className="text-xs text-gray-500">
                    💡 {option.ai_reasoning}
                  </div>
                </div>
              )}
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
          🔄 Refresh alternatives
        </button>
      </div>
    </div>
  );
};

export default AlternativeFlightsGrid;
