import { useState, useEffect } from 'react';
import { Plane, Calendar, MapPin, Trash2, ChevronRight, RefreshCw } from 'lucide-react';
import { tripApi, type Trip } from '../services/api';

interface TripsSidebarProps {
  currentTripId?: number;
  onSelectTrip: (tripId: number) => void;
  onDeleteTrip?: (tripId: number) => void;
  refreshTrigger?: number;
}

const TripsSidebar = ({ currentTripId, onSelectTrip, onDeleteTrip, refreshTrigger }: TripsSidebarProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [savedTrips, setSavedTrips] = useState<Trip[]>([]);
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
      setSavedTrips(trips);
      console.log('✅ Loaded trips:', trips.length);
    } catch (err: any) {
      console.error('❌ Error loading trips:', err);
      setError('Failed to load trips');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTrip = async (tripId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this trip?')) return;
    
    try {
      await tripApi.deleteTrip(tripId);
      setSavedTrips(savedTrips.filter(t => t.id !== tripId));
      
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

  return (
    <div
      className={`fixed left-0 top-0 h-full bg-[#0a0e14]/95 backdrop-blur-xl border-r border-[rgba(148,163,184,0.2)] transition-all duration-300 z-[100] ${
        isExpanded ? 'w-72' : 'w-20'
      }`}
    >
      {!isExpanded ? (
        /* Collapsed State - Centered Icon */
        <div className="h-full flex flex-col items-center justify-center">
          <div
            className="cursor-pointer flex flex-col items-center gap-3"
            onMouseEnter={() => setIsExpanded(true)}
          >
            <div className="w-12 h-12 rounded-xl bg-[#38BDF8]/10 flex items-center justify-center hover:bg-[#38BDF8]/20 transition-all">
              <Plane className="w-7 h-7 text-[#38BDF8]" />
            </div>
            <p className="text-xs font-semibold text-[#9CA3AF]">Trips</p>
          </div>
        </div>
      ) : (
        /* Expanded State */
        <div
          onMouseLeave={() => setIsExpanded(false)}
          className="h-full flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center gap-3 p-5 border-b border-[rgba(148,163,184,0.2)]">
            <div className="w-10 h-10 rounded-xl bg-[#38BDF8]/10 flex items-center justify-center flex-shrink-0">
              <Plane className="w-6 h-6 text-[#38BDF8]" />
            </div>
            <div className="flex-1 overflow-hidden flex items-center justify-between">
              <h3 className="text-lg font-bold text-white whitespace-nowrap">Trips</h3>
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
          <div className="overflow-y-auto flex-1 custom-scrollbar">
            <div className="p-3 space-y-2">
              {loading && savedTrips.length === 0 ? (
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
              ) : savedTrips.length === 0 ? (
                <div className="text-center py-8 px-4">
                  <Plane className="w-12 h-12 text-[#6B7280] mx-auto mb-3" />
                  <p className="text-sm text-[#9CA3AF]">No saved trips yet</p>
                </div>
              ) : (
                savedTrips.map((trip) => (
                  <div
                    key={trip.id}
                    onClick={() => {
                      onSelectTrip(trip.id);
                      setIsExpanded(false);
                    }}
                    className={`group relative p-3 rounded-xl cursor-pointer transition-all ${
                      currentTripId === trip.id
                        ? 'bg-[#38BDF8]/20 border border-[#38BDF8]/50'
                        : 'bg-[#1F2937]/30 border border-[rgba(148,163,184,0.1)] hover:bg-[#1F2937]/50 hover:border-[#38BDF8]/30'
                    }`}
                  >
                    {/* Trip Title */}
                    <h4 className="text-white font-semibold text-sm mb-2 pr-6 truncate">
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

                    {/* Delete Button */}
                    <button
                      onClick={(e) => handleDeleteTrip(trip.id, e)}
                      className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-lg bg-[#EF4444]/10 hover:bg-[#EF4444]/20"
                    >
                      <Trash2 className="w-4 h-4 text-[#EF4444]" />
                    </button>

                    {/* Active Indicator */}
                    {currentTripId === trip.id && (
                      <div className="absolute right-3 bottom-3">
                        <ChevronRight className="w-4 h-4 text-[#38BDF8]" />
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TripsSidebar;
