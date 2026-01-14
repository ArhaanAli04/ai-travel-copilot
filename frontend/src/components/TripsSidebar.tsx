import { useState, useEffect } from 'react';
import { Plane, Star, Calendar, MapPin, Trash2, ChevronRight, RefreshCw } from 'lucide-react';
import { tripApi, type Trip } from '../services/api';

interface TripsSidebarProps {
  currentTripId?: number;
  onSelectTrip: (tripId: number) => void;
  onDeleteTrip?: (tripId: number) => void;
  refreshTrigger?: number;
}

type SidebarView = 'all' | 'favorites';

const TripsSidebar = ({ currentTripId, onSelectTrip, onDeleteTrip, refreshTrigger }: TripsSidebarProps) => {
  const [activeView, setActiveView] = useState<SidebarView | null>(null);
  const [allTrips, setAllTrips] = useState<Trip[]>([]);
  const [favoriteTrips, setFavoriteTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch trips on mount and when refreshTrigger changes
  useEffect(() => {
    fetchTrips();
  }, [refreshTrigger]);

  const fetchTrips = async () => {
    setLoading(true);
    setError(null);
    try {
      const trips = await tripApi.getAllTrips();
      setAllTrips(trips);
      setFavoriteTrips(trips.filter(t => t.is_favorite));
      console.log('✅ Loaded trips:', trips.length, 'Favorites:', trips.filter(t => t.is_favorite).length);
    } catch (err: any) {
      console.error('❌ Error loading trips:', err);
      setError('Failed to load trips');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFavorite = async (tripId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    
    try {
      const result = await tripApi.toggleFavorite(tripId);
      
      // Update local state
      setAllTrips(allTrips.map(t => 
        t.id === tripId ? { ...t, is_favorite: result.is_favorite } : t
      ));
      
      if (result.is_favorite) {
        const trip = allTrips.find(t => t.id === tripId);
        if (trip) {
          setFavoriteTrips([...favoriteTrips, { ...trip, is_favorite: true }]);
        }
      } else {
        setFavoriteTrips(favoriteTrips.filter(t => t.id !== tripId));
      }
      
      console.log('⭐', result.message);
    } catch (err: any) {
      console.error('❌ Error toggling favorite:', err);
      alert('Failed to update favorite status');
    }
  };

  const handleDeleteTrip = async (tripId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this trip?')) return;
    
    try {
      await tripApi.deleteTrip(tripId);
      setAllTrips(allTrips.filter(t => t.id !== tripId));
      setFavoriteTrips(favoriteTrips.filter(t => t.id !== tripId));
      
      if (onDeleteTrip) {
        onDeleteTrip(tripId);
      }
      
      console.log('✅ Trip deleted');
    } catch (err: any) {
      console.error('❌ Error deleting trip:', err);
      alert('Failed to delete trip');
    }
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
        onSelectTrip(trip.id);
        setActiveView(null);
      }}
      className={`group relative p-3 rounded-xl cursor-pointer transition-all ${
        currentTripId === trip.id
          ? 'bg-[#38BDF8]/20 border border-[#38BDF8]/50'
          : 'bg-[#1F2937]/30 border border-[rgba(148,163,184,0.1)] hover:bg-[#1F2937]/50 hover:border-[#38BDF8]/30'
      }`}
    >
      {/* Trip Title */}
      <h4 className="text-white font-semibold text-sm mb-2 pr-14 truncate">
        {trip.title}
      </h4>

      {/* Trip Details */}
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

      {/* Action Buttons */}
      <div className="absolute top-3 right-3 flex items-center gap-1">
        {/* Favorite Button */}
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

        {/* Delete Button */}
        <button
          onClick={(e) => handleDeleteTrip(trip.id, e)}
          className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-lg bg-[#EF4444]/10 hover:bg-[#EF4444]/20"
        >
          <Trash2 className="w-4 h-4 text-[#EF4444]" />
        </button>
      </div>

      {/* Active Indicator */}
      {currentTripId === trip.id && (
        <div className="absolute right-3 bottom-3">
          <ChevronRight className="w-4 h-4 text-[#38BDF8]" />
        </div>
      )}
    </div>
  );

  const currentTrips = activeView === 'favorites' ? favoriteTrips : activeView === 'all' ? allTrips : [];

  return (
    <>
      {/* Icon Sidebar - Always Visible */}
      <div className="fixed left-0 top-0 h-full w-20 bg-[#0a0e14]/95 backdrop-blur-xl border-r border-[rgba(148,163,184,0.2)] z-[100]">
        <div className="h-full flex flex-col items-center justify-center gap-8">
          {/* All Trips Icon */}
          <div
            className="cursor-pointer flex flex-col items-center gap-2"
            onMouseEnter={() => setActiveView('all')}
          >
            <div className="w-12 h-12 rounded-xl bg-[#38BDF8]/10 flex items-center justify-center hover:bg-[#38BDF8]/20 transition-all relative">
              <Plane className="w-7 h-7 text-[#38BDF8]" />
              {allTrips.length > 0 && (
                <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#F97316] text-white text-xs font-bold flex items-center justify-center">
                  {allTrips.length}
                </div>
              )}
            </div>
            <p className="text-xs font-semibold text-[#9CA3AF]">All Trips</p>
          </div>

          {/* Favorites Icon */}
          <div
            className="cursor-pointer flex flex-col items-center gap-2"
            onMouseEnter={() => setActiveView('favorites')}
          >
            <div className="w-12 h-12 rounded-xl bg-[#F59E0B]/10 flex items-center justify-center hover:bg-[#F59E0B]/20 transition-all relative">
              <Star className="w-7 h-7 text-[#F59E0B]" />
              {favoriteTrips.length > 0 && (
                <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#F59E0B] text-white text-xs font-bold flex items-center justify-center">
                  {favoriteTrips.length}
                </div>
              )}
            </div>
            <p className="text-xs font-semibold text-[#9CA3AF]">Favorites</p>
          </div>
        </div>
      </div>

      {/* Expanded Trip List - Slides in from left */}
      {activeView && (
        <div
          onMouseLeave={() => setActiveView(null)}
          className="fixed left-20 top-0 h-full w-64 bg-[#0a0e14]/95 backdrop-blur-xl border-r border-[rgba(148,163,184,0.2)] z-[99] animate-slide-in-left"
        >
          {/* Header */}
          <div className="flex items-center gap-3 p-5 border-b border-[rgba(148,163,184,0.2)]">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
              activeView === 'favorites' ? 'bg-[#F59E0B]/10' : 'bg-[#38BDF8]/10'
            }`}>
              {activeView === 'favorites' ? (
                <Star className="w-6 h-6 text-[#F59E0B]" />
              ) : (
                <Plane className="w-6 h-6 text-[#38BDF8]" />
              )}
            </div>
            <div className="flex-1 overflow-hidden flex items-center justify-between">
              <h3 className="text-lg font-bold text-white whitespace-nowrap">
                {activeView === 'favorites' ? 'Favorites' : 'All Trips'}
              </h3>
              <button
                onClick={fetchTrips}
                className="p-1.5 rounded-lg hover:bg-[#1F2937]/50 transition-colors"
                title="Refresh trips"
              >
                <RefreshCw className={`w-4 h-4 text-[#9CA3AF] ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Trips List */}
          <div className="overflow-y-auto flex-1 custom-scrollbar h-[calc(100vh-80px)]">
            <div className="p-3 space-y-2">
              {loading && currentTrips.length === 0 ? (
                <div className="text-center py-8">
                  <div className="w-8 h-8 border-2 border-[#38BDF8]/30 border-t-[#38BDF8] rounded-full animate-spin mx-auto mb-3" />
                  <p className="text-sm text-[#9CA3AF]">Loading trips...</p>
                </div>
              ) : error ? (
                <div className="text-center py-8 px-4">
                  <p className="text-sm text-[#EF4444] mb-2">{error}</p>
                  <button
                    onClick={fetchTrips}
                    className="text-xs text-[#38BDF8] hover:underline"
                  >
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
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default TripsSidebar;
