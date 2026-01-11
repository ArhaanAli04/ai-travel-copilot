import { useState , useEffect } from 'react';
import { tripApi, type Trip, type TripCreate } from '../services/api';
import { Navigation } from '../components/Navigation';
import { Hero } from '../components/Hero';
import { TripFormV2 } from '../components/TripFormV2';
import { TripSummaryV2 } from '../components/TripSummaryV2';
import TripsSidebar from '../components/TripsSidebar';

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

  // Sync selectedTripId with createdTrip
  useEffect(() => {
    if (createdTrip) {
      setSelectedTripId(createdTrip.id);
    }
  }, [createdTrip]);
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
    <TripsSidebar
      currentTripId={selectedTripId}
      onSelectTrip={handleSelectTrip}
      onDeleteTrip={handleDeleteTrip}
      refreshTrigger={refreshSidebar} 
    />
    <div className="ml-20 transition-all duration-300">
      <Navigation />
      <Hero />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
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
            loading={loading}
            originCode={originCode}
            destinationCodes={destinationCodes}
          />
        )}
      </main>
    </div>
    </div>
  );
};

export default Planner;
