import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Plane, Star, Calendar, MapPin, Trash2,
  ChevronRight, RefreshCw, MessageSquare, Plus, Clock, AlertTriangle
} from 'lucide-react';
import { tripApi,disruptionApi, type Trip } from '../services/api';
import { type ChatSession } from '../types/local-discovery';
import type { DisruptionCase } from '../types/disruption';
import { formatRelativeTime } from '../utils/datetime';
import { getChatSessions, getUserId } from '../services/local-discovery-api';
import { DeleteConfirmModal } from './DeleteConfirmModal';

type ActiveView = 'all' | 'favorites' | 'chats' | 'cases' | null;

interface UnifiedSidebarProps {
  // Trip props (used on Planner page)
  currentTripId?: number;
  onSelectTrip?: (tripId: number) => void;
  onDeleteTrip?: (tripId: number) => void;
  refreshTrigger?: number;
  // Chat props (used on Local Discovery page)
  activeSessionId?: string | null;
  onSelectSession?: (sessionId: string) => void;
  onNewSession?: () => void;
  onDeleteSession?: (sessionId: string) => void;
  currentCaseId?: number;
}

const UnifiedSidebar = ({
  currentTripId,
  onSelectTrip,
  onDeleteTrip,
  refreshTrigger,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  currentCaseId,
}: UnifiedSidebarProps) => {
  const [activeView, setActiveView] = useState<ActiveView>(null);
  const [allTrips, setAllTrips] = useState<Trip[]>([]);
  const [favoriteTrips, setFavoriteTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [cases, setCases] = useState<DisruptionCase[]>([]);
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    type: 'trip' | 'session' | 'case' | null;
    id: number | string | null;
    loading: boolean;
  }>({ isOpen: false, type: null, id: null, loading: false });
  const navigate = useNavigate();
  const location = useLocation();

  const isPlanner = location.pathname.includes('planner') || location.pathname === '/';
  const isDiscovery = location.pathname.includes('local-discovery');

  useEffect(() => {
    fetchTrips();
    fetchSessions();
    fetchCases();
  }, [refreshTrigger]);

  const fetchCases = async () => {
    try {
      const data = await disruptionApi.listCases();
      setCases(data.cases);
    } catch (err) {
      console.error('❌ Error loading disruption cases:', err);
    }
  };

  const handleDeleteCase = async (caseId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteModal({ isOpen: true, type: 'case', id: caseId, loading: false });
  };

  const confirmDelete = async () => {
  if (!deleteModal.id || !deleteModal.type) return;
  setDeleteModal(prev => ({ ...prev, loading: true }));

  try {
    if (deleteModal.type === 'trip') {
      const tripId = deleteModal.id as number;
      await tripApi.deleteTrip(tripId);
      setAllTrips(allTrips.filter(t => t.id !== tripId));
      setFavoriteTrips(favoriteTrips.filter(t => t.id !== tripId));
      if (onDeleteTrip) onDeleteTrip(tripId);

    } else if (deleteModal.type === 'session') {
      const sessionId = deleteModal.id as string;
      if (onDeleteSession) onDeleteSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));

    } else if (deleteModal.type === 'case') {
      const caseId = deleteModal.id as number;
      await disruptionApi.deleteCase(caseId);
      setCases(cases.filter(c => c.id !== caseId));
    }

    setDeleteModal({ isOpen: false, type: null, id: null, loading: false });

  } catch (err) {
    console.error(`❌ Error deleting ${deleteModal.type}:`, err);
    setDeleteModal(prev => ({ ...prev, loading: false }));
  }
};
  const fetchTrips = async () => {
    setLoading(true);
    setError(null);
    try {
      const trips = await tripApi.getAllTrips();
      setAllTrips(trips);
      setFavoriteTrips(trips.filter(t => t.is_favorite));
    } catch (err: any) {
      console.error('❌ Error loading trips:', err);
      setError('Failed to load trips');
    } finally {
      setLoading(false);
    }
  };

  const fetchSessions = async () => {
    try {
        const userId = getUserId();
        const data = await getChatSessions(userId);
        setSessions(data);
    } catch (err) {
        console.error('❌ Error loading sessions:', err);
    }
    };

  const handleToggleFavorite = async (tripId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const result = await tripApi.toggleFavorite(tripId);
      setAllTrips(allTrips.map(t =>
        t.id === tripId ? { ...t, is_favorite: result.is_favorite } : t
      ));
      if (result.is_favorite) {
        const trip = allTrips.find(t => t.id === tripId);
        if (trip) setFavoriteTrips([...favoriteTrips, { ...trip, is_favorite: true }]);
      } else {
        setFavoriteTrips(favoriteTrips.filter(t => t.id !== tripId));
      }
    } catch (err: any) {
      console.error('❌ Error toggling favorite:', err);
      alert('Failed to update favorite status');
    }
  };

  const handleDeleteTrip = async (tripId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteModal({ isOpen: true, type: 'trip', id: tripId, loading: false });
  };

  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteModal({ isOpen: true, type: 'session', id: sessionId, loading: false });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  const renderTripCard = (trip: Trip) => (
    <div
      key={trip.id}
      onClick={() => {
        setActiveView(null);
        if (!isPlanner) {
            navigate('/planner', { state: { selectTripId: trip.id } });
        } else {
            if (onSelectTrip) onSelectTrip(trip.id);
        }
      }}
      className={`group relative p-3 rounded-xl cursor-pointer transition-all ${
        currentTripId === trip.id
          ? 'bg-[#38BDF8]/20 border border-[#38BDF8]/50'
          : 'bg-[#1F2937]/30 border border-[rgba(148,163,184,0.1)] hover:bg-[#1F2937]/50 hover:border-[#38BDF8]/30'
      }`}
    >
      <h4 className="text-white font-semibold text-sm mb-2 pr-14 truncate">{trip.title}</h4>
      <div className="space-y-1.5 text-xs text-[#9CA3AF]">
        <div className="flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate">
            {formatDate(trip.start_date)} - {formatDate(trip.end_date)}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate">{trip.destinations.join(', ')}</span>
        </div>
      </div>
      <div className="absolute top-3 right-3 flex items-center gap-1">
        <button
          onClick={(e) => handleToggleFavorite(trip.id, e)}
          className={`p-1 rounded-lg transition-all ${
            trip.is_favorite
              ? 'bg-[#F59E0B]/20 text-[#F59E0B]'
              : 'opacity-0 group-hover:opacity-100 bg-[#6B7280]/10 text-[#9CA3AF] hover:text-[#F59E0B] hover:bg-[#F59E0B]/10'
          }`}
          title={trip.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
        >
          <Star className={`w-4 h-4 ${trip.is_favorite ? 'fill-current' : ''}`} />
        </button>
        <button
          onClick={(e) => handleDeleteTrip(trip.id, e)}
          className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-lg bg-[#EF4444]/10 hover:bg-[#EF4444]/20"
        >
          <Trash2 className="w-4 h-4 text-[#EF4444]" />
        </button>
      </div>
      {currentTripId === trip.id && (
        <div className="absolute right-3 bottom-3">
          <ChevronRight className="w-4 h-4 text-[#38BDF8]" />
        </div>
      )}
    </div>
  );

  const renderSessionCard = (session: ChatSession) => (
    <div
      key={session.id}
      onClick={() => {
        setActiveView(null);
        if (!isDiscovery) {
            navigate('/local-discovery', { state: { selectSessionId: session.id } });
        } else {
            if (onSelectSession) onSelectSession(session.id);
        }
      }}
      className={`group relative p-3 rounded-xl cursor-pointer transition-all ${
        activeSessionId === session.id
          ? 'bg-[#38BDF8]/20 border border-[#38BDF8]/50'
          : 'bg-[#1F2937]/30 border border-[rgba(148,163,184,0.1)] hover:bg-[#1F2937]/50 hover:border-[#38BDF8]/30'
      }`}
    >
      <h4 className="text-white font-semibold text-sm mb-2 pr-8 truncate">{session.title}</h4>
      <div className="space-y-1.5 text-xs text-[#9CA3AF]">
        <div className="flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate capitalize">{session.city}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate">{formatRelativeTime(new Date(session.updated_at))}</span>
        </div>
        {session.messages.length > 0 && (
          <div className="flex items-center gap-1.5">
            <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{session.messages.length} messages</span>
          </div>
        )}
      </div>
      <button
         onClick={(e) => handleDeleteSession(session.id, e)}
        className={`absolute top-3 right-3 transition-all p-1.5 rounded-lg bg-[#EF4444]/10 hover:bg-[#EF4444]/20 hover:scale-110 cursor-pointer ${
          activeSessionId === session.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
        }`}
        aria-label="Delete chat"
      >
        <Trash2 className="w-4 h-4 text-[#EF4444]" />
      </button>
    </div>
  );

  const renderCaseCard = (c: DisruptionCase) => {
    const severityColor: Record<string, string> = {
      low:      'text-[#22C55E] bg-[#22C55E]/10',
      medium:   'text-[#F59E0B] bg-[#F59E0B]/10',
      high:     'text-[#EF4444] bg-[#EF4444]/10',
      critical: 'text-[#EF4444] bg-[#EF4444]/20',
    };

    const typeIcon: Record<string, string> = {
      delay:        '⏱️',
      cancellation: '❌',
      weather:      '🌩️',
      strike:       '✊',
      other:        '⚠️',
    };

     return (
      <div
        key={c.id}
        onClick={() => {
          setActiveView(null);
          navigate('/disruptions', { state: { selectCaseId: c.id } });
        }}
        className={`group relative p-3 rounded-xl cursor-pointer transition-all ${
          currentCaseId === c.id
            ? 'bg-[#F97316]/20 border border-[#F97316]/50'
            : 'bg-[#1F2937]/30 border border-[rgba(148,163,184,0.1)] hover:bg-[#1F2937]/50 hover:border-[#F97316]/30'
        }`}
      >
        {/* Flight number + type icon */}
        <div className="flex items-center justify-between mb-2 pr-8">
          <h4 className="text-white font-semibold text-sm truncate">
            {typeIcon[c.disruption_type] || '⚠️'} {c.flight_number}
          </h4>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full flex-shrink-0 ${severityColor[c.severity] || 'text-[#9CA3AF]'}`}>
            {c.severity}
          </span>
        </div>

        {/* Route */}
        <div className="flex items-center gap-1.5 text-xs text-[#9CA3AF] mb-1.5">
          <Plane className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate">{c.origin} → {c.destination}</span>
        </div>

        {/* Airline + date */}
        <div className="flex items-center gap-1.5 text-xs text-[#9CA3AF]">
          <Clock className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate">
            {c.airline} · {new Date(c.disruption_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
        </div>

         {/* Active indicator */}
        {currentCaseId === c.id && (
          <div className="absolute right-3 bottom-3">
            <ChevronRight className="w-4 h-4 text-[#F97316]" />
          </div>
        )}
        
        {/* ✅ Delete button — shows on hover, top-right like session cards */}
        <button
          onClick={(e) => handleDeleteCase(c.id, e)}
          className="absolute top-3 right-3 transition-all p-1.5 rounded-lg
            bg-[#EF4444]/10 hover:bg-[#EF4444]/20 hover:scale-110 cursor-pointer
            opacity-0 group-hover:opacity-100"
          aria-label="Delete case"
        >
          <Trash2 className="w-4 h-4 text-[#EF4444]" />
        </button>
      </div>
    );
  };

  const currentTrips = activeView === 'favorites' ? favoriteTrips : allTrips;

  return (
    <>
      {/* ── Icon Rail ── Always Visible */}
      <div className="fixed left-0 top-0 h-full w-20 bg-[#0a0e14]/95 backdrop-blur-xl border-r border-[rgba(148,163,184,0.2)] z-[100]">
        <div className="h-full flex flex-col items-center justify-center gap-8">

          {/* All Trips */}
          <div
            className="cursor-pointer flex flex-col items-center gap-2"
            onMouseEnter={() => setActiveView('all')}
            onClick={() => { if (!isPlanner) navigate('/planner'); }}
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all relative
              ${activeView === 'all' || isPlanner ? 'bg-[#38BDF8]/20' : 'bg-[#38BDF8]/10 hover:bg-[#38BDF8]/20'}`}>
              <Plane className="w-7 h-7 text-[#38BDF8]" />
              {allTrips.length > 0 && (
                <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#F97316] text-white text-xs font-bold flex items-center justify-center">
                  {allTrips.length}
                </div>
              )}
            </div>
            <p className="text-xs font-semibold text-[#9CA3AF]">All Trips</p>
          </div>

          {/* Favorites */}
          <div
            className="cursor-pointer flex flex-col items-center gap-2"
            onMouseEnter={() => setActiveView('favorites')}
            onClick={() => { if (!isPlanner) navigate('/planner'); }}
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all relative
              ${activeView === 'favorites' ? 'bg-[#F59E0B]/20' : 'bg-[#F59E0B]/10 hover:bg-[#F59E0B]/20'}`}>
              <Star className="w-7 h-7 text-[#F59E0B]" />
              {favoriteTrips.length > 0 && (
                <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#F59E0B] text-white text-xs font-bold flex items-center justify-center">
                  {favoriteTrips.length}
                </div>
              )}
            </div>
            <p className="text-xs font-semibold text-[#9CA3AF]">Favorites</p>
          </div>

          {/* Divider */}
          <div className="w-10 border-t border-slate-700/60" />

          {/* Chats */}
          <div
            className="cursor-pointer flex flex-col items-center gap-2"
            onMouseEnter={() => setActiveView('chats')}
            onClick={() => { if (!isDiscovery) navigate('/local-discovery'); }}
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all relative
              ${activeView === 'chats' || isDiscovery ? 'bg-[#38BDF8]/20' : 'bg-[#38BDF8]/10 hover:bg-[#38BDF8]/20'}`}>
              <MessageSquare className="w-7 h-7 text-[#38BDF8]" />
              {sessions.length > 0 && (
                <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#F97316] text-white text-xs font-bold flex items-center justify-center">
                  {sessions.length}
                </div>
              )}
            </div>
            <p className="text-xs font-semibold text-[#9CA3AF]">Chats</p>
          </div>
          
          {/* ✅ CASES — Disruption Cases icon */}
          <div
            className="cursor-pointer flex flex-col items-center gap-2"
            onMouseEnter={() => setActiveView('cases')}
            onClick={() => navigate('/disruptions')}
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all relative
              ${activeView === 'cases' || location.pathname.includes('disruption')
                ? 'bg-[#F97316]/20'
                : 'bg-[#F97316]/10 hover:bg-[#F97316]/20'}`}>
              <AlertTriangle className="w-7 h-7 text-[#F97316]" />
              {cases.length > 0 && (
                <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#F97316] text-white text-xs font-bold flex items-center justify-center">
                  {cases.length}
                </div>
              )}
            </div>
            <p className="text-xs font-semibold text-[#9CA3AF]">Cases</p>
          </div>

          {/* New Chat */}
          <div
            className="cursor-pointer flex flex-col items-center gap-2"
            onClick={() => {
              if (!isDiscovery) navigate('/local-discovery');
              if (onNewSession) onNewSession();
            }}
          >
            <div className="w-12 h-12 rounded-xl bg-[#22C55E]/10 flex items-center justify-center hover:bg-[#22C55E]/20 transition-all">
              <Plus className="w-7 h-7 text-[#22C55E]" />
            </div>
            <p className="text-xs font-semibold text-[#9CA3AF]">New</p>
          </div>

        </div>
      </div>

      {/* ── Expanded Panel ── Slides in on hover */}
      {activeView && (
        <div
          onMouseLeave={() => setActiveView(null)}
          className="fixed left-20 top-0 h-full w-64 bg-[#0a0e14]/95 backdrop-blur-xl border-r border-[rgba(148,163,184,0.2)] z-[99] animate-slide-in-left"
        >
          {/* Header */}
          <div className="flex items-center gap-3 p-5 border-b border-[rgba(148,163,184,0.2)]">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
              activeView === 'favorites' ? 'bg-[#F59E0B]/10' :
              activeView === 'chats'     ? 'bg-[#38BDF8]/10' : 
              activeView === 'cases'     ? 'bg-[#F97316]/10' :
                                            'bg-[#38BDF8]/10'
            }`}>
              {activeView === 'favorites' && <Star className="w-6 h-6 text-[#F59E0B]" />}
              {activeView === 'all'       && <Plane className="w-6 h-6 text-[#38BDF8]" />}
              {activeView === 'chats'     && <MessageSquare className="w-6 h-6 text-[#38BDF8]" />}
              {activeView === 'cases'     && <AlertTriangle className="w-6 h-6 text-[#F97316]" />}
            </div>
            <div className="flex-1 overflow-hidden flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white whitespace-nowrap">
                  {activeView === 'favorites' ? 'Favorites' :
                   activeView === 'all'       ? 'All Trips' : 
                    activeView === 'cases'     ? 'Disruptions' :
                                                'Local Discovery'}
                </h3>
                {activeView === 'chats' && (
                  <p className="text-xs text-[#9CA3AF]">
                    {sessions.length} {sessions.length === 1 ? 'chat' : 'chats'}
                  </p>
                )}
                {activeView === 'cases' && (
                  <p className="text-xs text-[#9CA3AF]">
                    {cases.length} {cases.length === 1 ? 'case' : 'cases'}
                  </p>
                )}

              </div>
              {(activeView === 'all' || activeView === 'favorites') && (
                <button
                  onClick={fetchTrips}
                  className="p-1.5 rounded-lg hover:bg-[#1F2937]/50 transition-colors"
                  title="Refresh trips"
                >
                  <RefreshCw className={`w-4 h-4 text-[#9CA3AF] ${loading ? 'animate-spin' : ''}`} />
                </button>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="overflow-y-auto custom-scrollbar h-[calc(100vh-80px)]">
            <div className="p-3 space-y-2">

              {/* Trip panels */}
              {(activeView === 'all' || activeView === 'favorites') && (
                loading && currentTrips.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="w-8 h-8 border-2 border-[#38BDF8]/30 border-t-[#38BDF8] rounded-full animate-spin mx-auto mb-3" />
                    <p className="text-sm text-[#9CA3AF]">Loading trips...</p>
                  </div>
                ) : error ? (
                  <div className="text-center py-8 px-4">
                    <p className="text-sm text-[#EF4444] mb-2">{error}</p>
                    <button onClick={fetchTrips} className="text-xs text-[#38BDF8] hover:underline">
                      Try again
                    </button>
                  </div>
                ) : currentTrips.length === 0 ? (
                  <div className="text-center py-8 px-4">
                    {activeView === 'favorites' ? (
                      <>
                        <Star className="w-12 h-12 text-[#6B7280] mx-auto mb-3" />
                        <p className="text-sm text-[#9CA3AF] mb-1">No favorite trips yet</p>
                        <p className="text-xs text-[#6B7280]">Click the star icon on any trip to add it here</p>
                      </>
                    ) : (
                      <>
                        <Plane className="w-12 h-12 text-[#6B7280] mx-auto mb-3" />
                        <p className="text-sm text-[#9CA3AF]">No saved trips yet</p>
                      </>
                    )}
                  </div>
                ) : (
                  currentTrips.map((trip) => renderTripCard(trip))
                )
              )}

              {/* Cases panel */}
              {activeView === 'cases' && (
                cases.length === 0 ? (
                  <div className="text-center py-8 px-4">
                    <AlertTriangle className="w-12 h-12 text-[#6B7280] mx-auto mb-3" />
                    <p className="text-sm text-[#9CA3AF] mb-1">No disruption cases yet</p>
                    <p className="text-xs text-[#6B7280]">Create a case on the Disruptions page</p>
                  </div>
                ) : (
                  cases.map((c) => renderCaseCard(c))
                )
              )}

              {/* Chat panel */}
              {activeView === 'chats' && (
                sessions.length === 0 ? (
                  <div className="text-center py-8 px-4">
                    <MessageSquare className="w-12 h-12 text-[#6B7280] mx-auto mb-3" />
                    <p className="text-sm text-[#9CA3AF] mb-1">No chat history yet</p>
                    <p className="text-xs text-[#6B7280]">Start a new conversation!</p>
                  </div>
                ) : (
                  sessions.map((session) => renderSessionCard(session))
                )
              )}

            </div>
          </div>
        </div>
      )}
      <DeleteConfirmModal
        isOpen={deleteModal.isOpen}
        onClose={() => setDeleteModal({ isOpen: false, type: null, id: null, loading: false })}
        onConfirm={confirmDelete}
        loading={deleteModal.loading}
        title={
          deleteModal.type === 'trip'    ? 'Delete Trip'             :
          deleteModal.type === 'session' ? 'Delete Chat'             :
                                          'Delete Disruption Case'
        }
        message={
          deleteModal.type === 'trip'
            ? 'Are you sure you want to delete this trip? This will permanently remove the trip and all its data.'
            : deleteModal.type === 'session'
            ? 'Are you sure you want to delete this chat? All messages in this conversation will be lost.'
            : 'Are you sure you want to delete this disruption case? This will permanently remove the case and all associated options and messages.'
        }
      />
    </>
  );
};

export default UnifiedSidebar;
