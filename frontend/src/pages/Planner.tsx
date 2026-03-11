import { useState, useEffect,useRef, useCallback } from 'react';
import { useAuth,useUser } from '@clerk/react';
import { tripApi, type Trip, type TripCreate } from '../services/api';
import { Navigation } from '../components/Navigation';
import { Hero } from '../components/Hero';
import { TripFormV2 } from '../components/TripFormV2';
import { TripSummaryV2 } from '../components/TripSummaryV2';
import { useLocation } from 'react-router-dom';
import UnifiedSidebar from '../components/UnifiedSidebar';
import { useWebSocket } from '../hooks/useWebSocket';              // ADD
import { usePolling } from '../hooks/usePolling';                  // ADD
import { ToastContainer, useToast } from '../components/Toast';   // ADD
import { PresenceIndicator } from '../components/PresenceIndicator'; // ADD
import type { WSMessage } from '../types/collaborator';    
const Planner = () => {
  // Form state
  const [formData, setFormData] = useState<TripCreate>({
    title: '',
    origin: '',
    destinations: [''],
    start_date: '',
    end_date: '',
    budget: undefined,
    budget_currency: 'USD',
    interests: [],
    trip_type: 'solo',
    traveler_count: 1,
    traveler_ages: [],
    include_flights: false,
    flight_preferences: {},
    include_hotels: false,
    hotel_preferences: {},  
    notes: '',
  });

  // UI state
  const [createdTrip, setCreatedTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [originCode, setOriginCode] = useState('');
  const [destinationCodes, setDestinationCodes] = useState<string[]>(['']);
  const [generatingItinerary, setGeneratingItinerary] = useState(false);
  const [itineraryGenerated, setItineraryGenerated] = useState(false);
  const [selectedTripId, setSelectedTripId] = useState<number | undefined>(undefined);
  const [refreshSidebar, setRefreshSidebar] = useState(0);
  const location = useLocation();

  // ── ADD: New state ──────────────────────────────────────────────
  const [wsToken, setWsToken] = useState<string | null>(null);
  const [viewers, setViewers] = useState<string[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [lastUpdatedLabel, setLastUpdatedLabel] = useState<string>('');
  const prevTripRef = useRef<Trip | null>(null);
  const { toasts, addToast, dismissToast } = useToast();
  const { getToken } = useAuth();
  const { user } = useUser();

  // ── ADD: Fetch WS token once ────────────────────────────────────
  useEffect(() => {
    getToken().then(t => setWsToken(t));
  }, [getToken]);

  // ── ADD: "Last updated X ago" label ────────────────────────────
  useEffect(() => {
    if (!lastUpdated) return;
    const update = () => {
      const sec = Math.floor((Date.now() - lastUpdated.getTime()) / 1000);
      if (sec < 10) setLastUpdatedLabel('just now');
      else if (sec < 60) setLastUpdatedLabel(`${sec}s ago`);
      else setLastUpdatedLabel(`${Math.floor(sec / 60)}m ago`);
    };
    update();
    const t = setInterval(update, 10000);
    return () => clearInterval(t);
  }, [lastUpdated]);

  
  // Sync selectedTripId with createdTrip
  useEffect(() => {
    if (createdTrip) {
      setSelectedTripId(createdTrip.id);
    }
  }, [createdTrip]);

  useEffect(() => {
  if (location.state?.selectTripId) {
    handleSelectTrip(location.state.selectTripId);
    window.history.replaceState({}, '');
  }else if (location.state?.newTrip) {
    // Reset to form view
    setCreatedTrip(null);
    setSelectedTripId(undefined);
    setOriginCode('');
    setDestinationCodes(['']);
    setItineraryGenerated(false);
    window.history.replaceState({}, '');
  }
}, [location.state]);

   // ── ADD: WS message handler ─────────────────────────────────────
  const handleWsMessage = useCallback((msg: WSMessage) => {
    const REFRESH_TYPES = [
      'trip_updated', 'itinerary_generated', 'activity_deleted',
      'activity_updated', 'activities_reordered', 'day_replanned',
    ];

    if (msg.type === 'presence_join' || msg.type === 'presence_leave') {
      setViewers(msg.payload.viewers ?? []);
      if (msg.type === 'presence_join' && msg.payload.display_name) {
        addToast(`${msg.payload.display_name} joined`, 'info');
      }
      return;
    }

    if (msg.type === 'collaborator_joined') {
      addToast('A new collaborator joined the trip!', 'success');
      setRefreshSidebar(prev => prev + 1);
      return;
    }

    if (msg.type === 'collaborator_removed') {
      addToast('A collaborator was removed from this trip', 'info');
      setRefreshSidebar(prev => prev + 1);
      return;
    }

    if (REFRESH_TYPES.includes(msg.type) && createdTrip && msg.payload.trip_id === createdTrip.id) {
      // Fetch fresh trip data and check if something actually changed
      tripApi.getTrip(createdTrip.id).then(fresh => {
        const prev = prevTripRef.current;
        const changed = !prev || fresh.updated_at !== prev.updated_at;
        prevTripRef.current = fresh;
        setCreatedTrip(fresh);
        setLastUpdated(new Date());
        if (changed && msg.type !== 'trip_updated') {
          const labels: Record<string, string> = {
            itinerary_generated: '✨ Itinerary was generated',
            activity_deleted: 'An activity was removed',
            activity_updated: 'An activity was updated',
            activities_reordered: 'Activities were reordered',
            day_replanned: 'A day was replanned',
          };
          addToast(labels[msg.type] ?? 'Trip updated', 'info');
        }
      });
    }
  }, [createdTrip, addToast]);

  // ── ADD: WebSocket hook ─────────────────────────────────────────
  const { status: wsStatus } = useWebSocket({
    tripId: selectedTripId ?? null,
    token: wsToken,
    onMessage: handleWsMessage,
    onConnected: () => addToast('Live sync connected', 'success'),
    onDisconnected: () => {},
  });

  // ── ADD: Polling fallback (only when WS disconnected) ──────────
  usePolling({
    fn: async () => {
      if (!createdTrip) return;
      const fresh = await tripApi.getTrip(createdTrip.id);
      if (fresh.updated_at && fresh.updated_at !== createdTrip.updated_at) {
        setCreatedTrip(fresh);
        setLastUpdated(new Date());
        addToast('Trip updated by collaborator', 'info');
      }
    },
    interval: 30000,
    enabled: wsStatus === 'disconnected' && !!createdTrip,
  });
  // Create trip
  const handleTripCreate = async (data: TripCreate) => {
    setLoading(true);
    setError(null);

    try {
      console.log('🚀 Creating trip:', data);
      const trip = await tripApi.createTrip(data);
      setCreatedTrip(trip);
      setItineraryGenerated(false);
      setRefreshSidebar(prev => prev + 1);
      console.log('✅ Trip created:', trip);
    } catch (err: any) {
      console.error('❌ Error creating trip:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to create trip');
    } finally {
      setLoading(false);
    }
  };

  // Generate itinerary
  const handleGenerateItinerary = async () => {
    if (!createdTrip) return;

    setGeneratingItinerary(true);
    setError(null);

    try {
      console.log('🎯 Generating itinerary for trip', createdTrip.id);
      const tripWithItinerary = await tripApi.generateItinerary(createdTrip.id);
      setCreatedTrip(tripWithItinerary);
      setItineraryGenerated(true);
      console.log('✅ Itinerary generated:', tripWithItinerary);
    } catch (err: any) {
      console.error('❌ Error generating itinerary:', err);
      setError(err.response?.data?.detail || 'Failed to generate itinerary');
    } finally {
      setGeneratingItinerary(false);
    }
  };

  // Update trip
  const handleUpdateTrip = async (updates: Partial<Trip>) => {
    if (!createdTrip) return;

    setLoading(true);
    setError(null);

    try {
      console.log('✏️ Updating trip:', updates);
      const updatedTrip = await tripApi.updateTrip(createdTrip.id, updates);
      setCreatedTrip(updatedTrip);
      setRefreshSidebar(prev => prev + 1);
      console.log('✅ Trip updated:', updatedTrip);
    } catch (err: any) {
      console.error('❌ Error updating trip:', err);
      setError(err.response?.data?.detail || 'Failed to update trip');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Delete current trip
  const handleDeleteCurrentTrip = async () => {
    if (!createdTrip) return;

    setLoading(true);
    setError(null);

    try {
      console.log('🗑️ Deleting trip:', createdTrip.id);
      await tripApi.deleteTrip(createdTrip.id);
      
      // Reset state
      setCreatedTrip(null);
      setSelectedTripId(undefined);
      setItineraryGenerated(false);
      setRefreshSidebar(prev => prev + 1);
      
      console.log('✅ Trip deleted');
    } catch (err: any) {
      console.error('❌ Error deleting trip:', err);
      setError(err.response?.data?.detail || 'Failed to delete trip');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Create another trip
  const handleCreateAnother = () => {
    setFormData({
      title: '',
      origin: '',
      destinations: [''],
      start_date: '',
      end_date: '',
      budget: undefined,
      budget_currency: 'USD',
      interests: [],
      trip_type: 'solo',
      traveler_count: 1,
      traveler_ages: [],
      include_flights: false,
      flight_preferences: {},
      include_hotels: false,
      hotel_preferences: {},
      notes: '',
    });
    setCreatedTrip(null);
    setError(null);
    setItineraryGenerated(false);
    setOriginCode('');
    setDestinationCodes(['']);
    setSelectedTripId(undefined);
  };

  // Refresh trip data
  const handleRefreshTrip = async () => {
    if (!createdTrip) return;

    setLoading(true);
    try {
      const trip = await tripApi.getTrip(createdTrip.id);
      setCreatedTrip(trip);
      console.log('✅ Trip refreshed:', trip);
    } catch (err: any) {
      console.error('❌ Error refreshing trip:', err);
      setError(err.response?.data?.detail || 'Failed to refresh trip');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTrip = async (tripId: number) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Loading trip:', tripId);
      const trip = await tripApi.getTrip(tripId);
      setCreatedTrip(trip);
      setSelectedTripId(tripId);
      
      // Check if itinerary was already generated
      setItineraryGenerated(trip.days && trip.days.length > 0);
      
      console.log('✅ Trip loaded:', trip);
    } catch (err: any) {
      console.error('❌ Error loading trip:', err);
      setError(err.response?.data?.detail || 'Failed to load trip');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTrip = async (tripId: number) => {
    if (!confirm('Are you sure you want to delete this trip?')) return;
    
    setLoading(true);
    try {
      console.log('Deleting trip:', tripId);
      await tripApi.deleteTrip(tripId);
      
      // If deleted trip was currently selected, reset state
      if (selectedTripId === tripId) {
        setCreatedTrip(null);
        setSelectedTripId(undefined);
        setItineraryGenerated(false);
      }
      
      setRefreshSidebar(prev => prev + 1);
      console.log('✅ Trip deleted');
    } catch (err: any) {
      console.error('❌ Error deleting trip:', err);
      setError(err.response?.data?.detail || 'Failed to delete trip');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#05070a] to-[#0b1120]">
      {/* Trips Sidebar */}
      <UnifiedSidebar
        currentTripId={selectedTripId}
        onSelectTrip={handleSelectTrip}
        onDeleteTrip={handleDeleteTrip}
        refreshTrigger={refreshSidebar}
      />
      <div className="ml-20 transition-all duration-300">
        <Navigation />
        <Hero />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
          {/* ADD: Presence + sync status bar */}
          {createdTrip && (
            <div className="flex items-center justify-between mb-4 px-1">
              <PresenceIndicator
                viewers={viewers}
                currentUserName={user?.fullName || user?.primaryEmailAddress?.emailAddress || ''}
              />
              <div className="flex items-center gap-2 text-xs text-[#6B7280]">
                {wsStatus === 'connected' && (
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]" />
                    Live
                  </span>
                )}
                {wsStatus === 'connecting' && (
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B] animate-pulse" />
                    Connecting...
                  </span>
                )}
                {wsStatus === 'disconnected' && (
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#6B7280]" />
                    Polling
                  </span>
                )}
                {lastUpdated && (
                  <span>· Updated {lastUpdatedLabel}</span>
                )}
              </div>
            </div>
          )}
          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444] animate-fade-in">
              <p className="font-semibold">❌ Error</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          )}

          {!createdTrip ? (
            <TripFormV2
              formData={formData}
              setFormData={setFormData}
              onSubmit={handleTripCreate}
              loading={loading}
              originCode={originCode}
              setOriginCode={setOriginCode}
              destinationCodes={destinationCodes}
              setDestinationCodes={setDestinationCodes}
            />
          ) : (
            <TripSummaryV2
              trip={createdTrip}
              itineraryGenerated={itineraryGenerated}
              generatingItinerary={generatingItinerary}
              onGenerateItinerary={handleGenerateItinerary}
              onCreateAnother={handleCreateAnother}
              onRefreshTrip={handleRefreshTrip}
              onUpdateTrip={handleUpdateTrip}
              onDeleteTrip={handleDeleteCurrentTrip}
              loading={loading}
              originCode={originCode}
              destinationCodes={destinationCodes}
            />
          )}
        </main>
      </div>
      {/* ADD: Toast container */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
};

export default Planner;
