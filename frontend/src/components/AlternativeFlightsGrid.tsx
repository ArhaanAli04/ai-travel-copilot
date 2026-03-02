import React, { useState, useEffect, useRef } from 'react';
import { disruptionApi } from '../services/api';
import type { DisruptionCase, DisruptionOption } from '../types/disruption';
import { Phone } from 'lucide-react';
import { InfoModal } from './InfoModal';

interface AlternativeFlightsGridProps {
  disruptionCase: DisruptionCase;
}

type DateTab = 'today' | 'tomorrow';

export const AlternativeFlightsGrid: React.FC<AlternativeFlightsGridProps> = ({ disruptionCase }) => {
  const [options, setOptions] = useState<DisruptionOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<DateTab>('today');
  const [todayOptions, setTodayOptions] = useState<DisruptionOption[]>([]);
  const [tomorrowOptions, setTomorrowOptions] = useState<DisruptionOption[]>([]);
  const [contactModal, setContactModal] = useState<{
    isOpen: boolean;
    airline: string;
    flightNumber: string;
    contactInfo: string;
  } | null>(null);
  const hasFetchedRef = useRef<Record<string, boolean>>({});
  const hasLoadedInitialRef = useRef(false);

  const disruptionDate = new Date(disruptionCase.disruption_date);
  const todayDate = disruptionDate.toISOString().split('T')[0];
  const tomorrowDate = new Date(disruptionDate.getTime() + 86400000)
    .toISOString().split('T')[0];

  const formatTabDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric'
    });
  };

  // On mount: check saved options first, search if none found
  useEffect(() => {
    if (hasLoadedInitialRef.current) return;
    hasLoadedInitialRef.current = true;
    loadInitialOptions();
  }, [disruptionCase.id]);

  // Switch tabs
  useEffect(() => {
    if (activeTab === 'today') {
      setOptions(todayOptions);
      if (!hasFetchedRef.current[todayDate]) searchFlightsForDate(todayDate);
    } else {
      setOptions(tomorrowOptions);
      if (!hasFetchedRef.current[tomorrowDate]) searchFlightsForDate(tomorrowDate);
    }
  }, [activeTab]);

  const loadInitialOptions = async () => {
    setLoading(true);
    setError(null);
    try {
      const saved = await disruptionApi.getOptions(disruptionCase.id);
      const savedFlights = saved.filter(o => o.option_type === 'alternative_flight');

      if (savedFlights.length > 0) {
        console.log(`⚡ CACHE HIT — ${savedFlights.length} saved flight option(s) from DB (no SerpAPI call)`);
        setTodayOptions(savedFlights);
        setOptions(savedFlights);
        hasFetchedRef.current[todayDate] = true; // mark as fetched so tab switch doesn't re-fetch
      } else {
        console.log('💨 No saved options found, calling SerpAPI...');
        await searchFlightsForDate(todayDate);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load alternatives');
    } finally {
      setLoading(false);
    }
  };

  const searchFlightsForDate = async (date: string, force = false) => {
    if (hasFetchedRef.current[date] && !force) {
      console.log(`⚡ CACHE HIT — already fetched for ${date}, skipping SerpAPI call`);
      return;
    }

    hasFetchedRef.current[date] = true;
    setLoading(true);
    setError(null);
    try {
      console.log(`🌐 SERPAPI CALL — searching flights for ${date}...`);
      const response = await disruptionApi.searchFlights(disruptionCase.id, date);
      const flights = response.options.filter(o => o.option_type === 'alternative_flight');
      console.log(`✅ SERPAPI RESULT — ${flights.length} flight(s) found for ${date}`);

      if (date === todayDate) {
        setTodayOptions(flights);
        if (activeTab === 'today') setOptions(flights);
      } else {
        setTomorrowOptions(flights);
        if (activeTab === 'tomorrow') setOptions(flights);
      }
    } catch (err) {
      console.error(`❌ Flight search failed for ${date}:`, err);
      setError('Failed to load flights');
      hasFetchedRef.current[date] = false;
    } finally {
      setLoading(false);
    }
  };

  const handleTabSwitch = (tab: DateTab) => {
    setActiveTab(tab);
  };

  const handleRefresh = () => {
    const date = activeTab === 'today' ? todayDate : tomorrowDate;
    console.log(`🔄 FORCED REFRESH — clearing guard for ${date}, new SerpAPI call incoming`);
    hasFetchedRef.current[date] = false;
    if (activeTab === 'today') setTodayOptions([]);
    else setTomorrowOptions([]);
    setOptions([]);
    searchFlightsForDate(date, true);
  };

  const parseFlightFromOption = (option: DisruptionOption) => {
    if (option.meta_data && typeof option.meta_data === 'object') {
      const fd = (option.meta_data as any).flight_details;
      if (fd) return fd;
    }
    return {
      flight_number: option.title.match(/([A-Z0-9]+)\s+\(/)?.[1] || 'Unknown',
      airline: disruptionCase.airline,
      departure_time: new Date().toISOString(),
      arrival_time: new Date().toISOString(),
      duration_minutes: 120,
      stops: 0,
      price_amount: option.estimated_cost || 0,
      price_currency: 'USD',
    };
  };

  const formatTime = (timeStr: string) => {
    return new Date(timeStr).toLocaleTimeString('en-US', {
      hour: '2-digit', minute: '2-digit', hour12: true,
    });
  };

  const formatDuration = (minutes: number) => {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return `${h}h ${m}m`;
  };

  const getPros = (option: DisruptionOption): string[] => {
    return (option.meta_data as any)?.pros || [];
  };
  const getCons = (option: DisruptionOption): string[] => {
    return (option.meta_data as any)?.cons || [];
  };

  return (
    <div className="bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl p-6">

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span>✈️</span> Alternative Flights
        </h3>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="text-xs text-gray-400 hover:text-white transition-colors disabled:opacity-50"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Date Tab Switcher */}
      <div className="flex gap-2 mb-5">
        {(['today', 'tomorrow'] as DateTab[]).map((tab) => {
          const date = tab === 'today' ? todayDate : tomorrowDate;
          const count = tab === 'today' ? todayOptions.length : tomorrowOptions.length;
          return (
            <button
              key={tab}
              onClick={() => handleTabSwitch(tab)}
              className={`flex-1 py-2.5 px-3 rounded-xl text-sm font-medium transition-all border ${
                activeTab === tab
                  ? 'bg-blue-500/20 border-blue-500/50 text-blue-400'
                  : 'bg-[rgba(15,23,42,0.4)] border-[rgba(148,163,184,0.15)] text-gray-400 hover:text-white hover:border-[rgba(148,163,184,0.3)]'
              }`}
            >
              <div className="capitalize">{tab === 'today' ? 'Today' : 'Tomorrow'}</div>
              <div className="text-xs opacity-70">{formatTabDate(date)}</div>
              {count > 0 && (
                <div className={`text-xs mt-0.5 font-semibold ${
                  activeTab === tab ? 'text-blue-300' : 'text-gray-500'
                }`}>
                  {count} flight{count !== 1 ? 's' : ''}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center space-y-3">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto" />
            <p className="text-gray-400 text-sm">
              Searching flights for {activeTab === 'today' ? formatTabDate(todayDate) : formatTabDate(tomorrowDate)}...
            </p>
          </div>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="text-center py-8 space-y-3">
          <p className="text-red-400 text-sm">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg text-sm"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && options.length === 0 && (
        <div className="text-center py-8">
          <p className="text-4xl mb-3">🔍</p>
          <p className="text-gray-400 text-sm">
            No flights found for {activeTab === 'today' ? formatTabDate(todayDate) : formatTabDate(tomorrowDate)}
          </p>
          <p className="text-gray-500 text-xs mt-1">
            Try switching to {activeTab === 'today' ? 'tomorrow' : 'today'}'s tab
          </p>
        </div>
      )}

      {/* Flight Cards */}
      {!loading && !error && options.length > 0 && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {options.map((option) => {
            const flight = parseFlightFromOption(option);
            const isRecommended = option.priority_rank >= 90;
            const pros = getPros(option);
            const cons = getCons(option);

            return (
              <div
                key={option.id}
                className={`relative p-4 rounded-xl border transition-all hover:scale-[1.02] ${
                  isRecommended
                    ? 'bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/40 shadow-lg shadow-green-500/10'
                    : 'bg-[rgba(15,23,42,0.5)] border-[rgba(148,163,184,0.2)] hover:border-[rgba(148,163,184,0.4)]'
                }`}
              >
                {isRecommended && (
                  <div className="absolute -top-2 -right-2 px-3 py-1 bg-green-500 text-white text-xs font-bold rounded-full shadow-lg">
                    ⭐ Best
                  </div>
                )}

                {/* Flight Header */}
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <div className="text-white font-bold text-lg">{flight.flight_number}</div>
                    <div className="text-gray-400 text-sm">{flight.airline}</div>
                  </div>
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
                    <div className="text-2xl font-bold text-white">{formatTime(flight.departure_time)}</div>
                    <div className="text-xs text-gray-500">{disruptionCase.origin}</div>
                  </div>
                  <div className="flex-1 flex flex-col items-center px-2">
                    <div className="text-xs text-gray-500 mb-1">{formatDuration(flight.duration_minutes)}</div>
                    <div className="w-full h-[2px] bg-gradient-to-r from-blue-500/30 via-blue-400 to-blue-500/30 relative">
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                        <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                  <div className="flex-1 text-right">
                    <div className="text-2xl font-bold text-white">{formatTime(flight.arrival_time)}</div>
                    <div className="text-xs text-gray-500">{disruptionCase.destination}</div>
                  </div>
                </div>

                {/* Price */}
                <div className="flex items-center justify-between mb-3 pt-3 border-t border-[rgba(148,163,184,0.2)]">
                  <span className="text-gray-400 text-sm">Estimated Cost</span>
                  <div className="text-xl font-bold text-white">
                    ${Math.abs(flight.price_amount)}
                    <span className="text-xs text-gray-500 ml-1">{flight.price_currency}</span>
                  </div>
                </div>

                {/* Pros / Cons */}
                {(pros.length > 0 || cons.length > 0) && (
                  <div className="flex gap-3 mb-3 text-xs">
                    {pros.length > 0 && (
                      <div className="flex-1 space-y-1">
                        {pros.map((p, i) => (
                          <div key={i} className="flex items-center gap-1 text-green-400">
                            <span>✓</span><span>{p}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {cons.length > 0 && (
                      <div className="flex-1 space-y-1">
                        {cons.map((c, i) => (
                          <div key={i} className="flex items-center gap-1 text-red-400">
                            <span>✗</span><span>{c}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

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
                    onClick={() => setContactModal({
                      isOpen: true,
                      airline: flight.airline,
                      flightNumber: flight.flight_number,
                      contactInfo: option.contact_info || '',
                    })}
                    className="px-4 py-2 bg-[rgba(148,163,184,0.1)] hover:bg-[rgba(148,163,184,0.2)] text-gray-300 text-sm rounded-lg transition-colors"
                  >
                    Contact
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
       {/* Contact Info Modal */}
      {contactModal && (
        <InfoModal
          isOpen={contactModal.isOpen}
          onClose={() => setContactModal(null)}
          title={`Contact ${contactModal.airline}`}
          icon={<Phone className="w-5 h-5 text-white" />}
        >
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-3 rounded-xl bg-[#1F2937]/50 border border-[rgba(148,163,184,0.1)]">
              <span className="text-2xl">✈️</span>
              <div>
                <p className="text-white font-semibold">{contactModal.flightNumber}</p>
                <p className="text-gray-400 text-sm">{contactModal.airline}</p>
              </div>
            </div>

            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">What to say</p>
              <p className="text-gray-300 leading-relaxed text-sm">
                Contact <span className="text-white font-medium">{contactModal.airline}</span> to
                rebook on flight <span className="text-blue-400 font-mono">{contactModal.flightNumber}</span>.
                Reference your original booking and request a same-day rebooking or compensation.
              </p>
            </div>

            {contactModal.contactInfo && (
              <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                <p className="text-xs text-blue-400 uppercase tracking-wider mb-1">Contact Details</p>
                <p className="text-gray-300 text-sm">{contactModal.contactInfo}</p>
              </div>
            )}

            <div className="p-3 rounded-xl bg-[#F59E0B]/10 border border-[#F59E0B]/20">
              <p className="text-xs text-[#F59E0B] font-semibold mb-1">💡 Tip</p>
              <p className="text-gray-400 text-xs leading-relaxed">
                Have your PNR / booking reference ready. Ask specifically for "involuntary rebooking" 
                to avoid change fees if your original flight was disrupted.
              </p>
            </div>
          </div>
        </InfoModal>
      )}
    </div>
  );
};

export default AlternativeFlightsGrid;
