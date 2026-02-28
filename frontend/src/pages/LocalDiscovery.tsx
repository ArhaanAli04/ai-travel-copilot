import React, { useState,useEffect } from 'react';
import { useLocalDiscovery } from '../hooks/useLocalDiscovery';
import { ChatInterface } from '../components/local-discovery/ChatInterface';
import { PreferencesPanel } from '../components/local-discovery/PreferencesPanel';
import { QuickActions } from '../components/local-discovery/QuickActions';
import { ContextDisplay } from '../components/local-discovery/ContextDisplay';
import { Menu, X} from 'lucide-react';
import { MapView } from '../components/local-discovery/MapView';
import { TimePickerModal } from '../components/local-discovery/TimePickerModal';
import { LocationPickerModal } from '../components/local-discovery/LocationPickerModal';
import { Navigation } from '../components/Navigation';
import { ErrorBoundary } from '../components/ErrorBoundary'; // ✨ NEW
import { NetworkStatus } from '../components/NetworkStatus'; // ✨ NEW
import { GeolocationError } from '../components/local-discovery/GeolocationError'; // ✨ NEW
import { ErrorState } from '../components/local-discovery/ErrorState'; // ✨ NEW
import { useLocation } from 'react-router-dom';
import UnifiedSidebar from '../components/UnifiedSidebar';
const LocalDiscovery = () => {
  const {
    sessions,
    activeSession,
    loading,
    error,
    contextChips,
    preferences,
    userLocation,
    city,
    locationError, // ✨ NEW
    retrying, // ✨ NEW
    createNewSession,
    selectSession,
    deleteSession,
    sendMessage,
    addPreference,
    removePreference,
    handleFeedback: submitFeedback,
    setManualLocation,
    setManualTime,
    retryLocation, // ✨ NEW
    clearError, // ✨ NEW
  } = useLocalDiscovery();

  const [showPreferences, setShowPreferences] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [showMap, setShowMap] = useState(false);
  const [mapPOIs, setMapPOIs] = useState<any[]>([]);
  const [showTimeModal, setShowTimeModal] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const routerLocation = useLocation();

  useEffect(() => {
  if (routerLocation.state?.selectSessionId) {
    selectSession(routerLocation.state.selectSessionId);
    window.history.replaceState({}, '');
  }
}, []);

  const handleEditChip = (chipId: string) => {
    if (chipId === 'location') {
      setShowLocationModal(true);
    } else if (chipId === 'time') {
      setShowTimeModal(true);
    }
  };

  const handleTimeSelect = (time: string) => {
    setManualTime(time);
    setShowTimeModal(false);
  };

  const handleLocationSelect = (location: { lat: number; lon: number }, cityName: string) => {
    setManualLocation(location, cityName);
    setShowLocationModal(false);
  };

  const handleSendMessage = (message: string) => {
    clearError(); // ✨ NEW: Clear previous errors
    sendMessage(message, false);
  };

  const handleQuickAction = (query: string) => {
    if (activeSession) {
      clearError(); // ✨ NEW
      sendMessage(query, false);
      setShowQuickActions(false);
    }
  };

  const handleOpenMap = (pois: any[]) => {
    setMapPOIs(pois);
    setShowMap(true);
  };

  const handleCloseMap = () => {
    setShowMap(false);
    setMapPOIs([]);
  };

  const handlePOIClickFromMap = (poiId: string) => {
    const element = document.getElementById(`poi-${poiId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      element.classList.add('ring-2', 'ring-blue-500', 'ring-offset-2');
      setTimeout(() => {
        element.classList.remove('ring-2', 'ring-blue-500', 'ring-offset-2');
      }, 2000);
    }
  };

  const handleFeedback = async (
    poiId: string,
    feedbackType: 'thumbs_up' | 'thumbs_down'
  ) => {
    await submitFeedback(poiId, feedbackType);
  };

  // ✨ NEW: Handle location error retry
  const handleLocationRetry = () => {
    retryLocation();
  };

  // ✨ NEW: Handle manual location selection from error state
  const handleUseManualLocation = () => {
    setShowLocationModal(true);
  };

  return (
    <ErrorBoundary> {/* ✨ NEW: Wrap entire page */}
      <div className="min-h-screen bg-gradient-to-b from-[#05070a] to-[#0b1120]">
        {/* ✨ NEW: Network Status Banner */}
        <NetworkStatus />

        {/* Navigation Bar */}
        <div className='ml-20'><Navigation /></div>
        
        
        {/* Main Content */}
        <div className="flex h-[calc(100vh-64px)] overflow-hidden ml-20">
          {/* Mobile Toggle */}
          {!showMap && (
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-lg lg:hidden"
            >
              {showSidebar ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          )}

          {/* LEFT SIDE: Sidebar OR Map */}
          {showMap && activeSession ? (
            <div className="w-2/5 h-[calc(100vh-64px)] flex-shrink-0 ">
              <MapView
                pois={mapPOIs}
                userLocation={{
                  lat: activeSession.location.lat,
                  lon: activeSession.location.lon,
                }}
                onClose={handleCloseMap}
                onPOIClick={handlePOIClickFromMap}
              />
            </div>
          ) : (
            <UnifiedSidebar
              
              activeSessionId={activeSession?.id || null}
              onSelectSession={selectSession}
              onNewSession={createNewSession}
              onDeleteSession={deleteSession}
            />
          )}

          {/* RIGHT SIDE: Chat */}
          <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
            {/* ✨ NEW: Location Error Banner */}
            {locationError && !error && (
              <div className="px-6 py-3 bg-[#F59E0B]/10 border-b border-[#F59E0B]/30">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-[#F59E0B]">{locationError}</p>
                  <div className="flex gap-2">
                    <button
                      onClick={handleUseManualLocation}
                      className="text-xs px-3 py-1 bg-[#F59E0B]/20 text-[#F59E0B] rounded-md hover:bg-[#F59E0B]/30 transition-colors"
                    >
                      Choose Manually
                    </button>
                    <button
                      onClick={handleLocationRetry}
                      disabled={retrying}
                      className="text-xs px-3 py-1 bg-[#F59E0B]/20 text-[#F59E0B] rounded-md hover:bg-[#F59E0B]/30 transition-colors disabled:opacity-50"
                    >
                      {retrying ? 'Retrying...' : 'Retry'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* ✨ ENHANCED: Error Banner with Dismiss */}
            {error && (
              <div className="px-6 py-3 bg-[#EF4444]/10 border-b border-[#EF4444]/30">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-[#EF4444]">{error}</p>
                  <button
                    onClick={clearError}
                    className="text-xs px-3 py-1 bg-[#EF4444]/20 text-[#EF4444] rounded-md hover:bg-[#EF4444]/30 transition-colors"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            )}

            {activeSession && (
              <>
                {/* Context chips */}
                <div className="px-6 py-4 bg-[#0a0e14]/50 backdrop-blur-xl border-b border-[rgba(148,163,184,0.2)] flex-shrink-0">
                  <ContextDisplay
                    chips={contextChips}
                    onRemoveChip={removePreference}
                    onEditChip={handleEditChip}
                    onOpenPreferences={() => setShowPreferences(true)}
                    showInfo={true}
                  />
                </div>
              </>
            )}

            {/* Quick Actions */}
            {activeSession && showQuickActions && activeSession.messages.length <= 1 && !showMap && (
              <div className="flex-shrink-0">
                <QuickActions onSelectAction={handleQuickAction} disabled={loading} />
              </div>
            )}

            {/* Scrollable Chat Area */}
            <div className="flex-1 overflow-hidden">
              <ChatInterface
                session={activeSession}
                loading={loading}
                error={error} // ✨ NEW
                contextChips={contextChips}
                onSendMessage={handleSendMessage}
                onRemoveChip={removePreference}
                onOpenPreferences={() => setShowPreferences(true)}
                onFeedback={handleFeedback}
                onOpenMap={handleOpenMap}
              />
            </div>
          </div>

          {/* RIGHT SIDE: Preferences Sidebar */}
          {showPreferences && (
            <div className="w-96 h-screen flex-shrink-0 border-l border-gray-200 bg-white">
              <PreferencesPanel
                preferences={preferences}
                onUpdatePreferences={addPreference}
                onClose={() => setShowPreferences(false)}
              />
            </div>
          )}
          
          {/* Modals */}
          {showTimeModal && (
            <TimePickerModal
              currentTime={contextChips.find((c) => c.type === 'time')?.value || 'afternoon'}
              onSelectTime={handleTimeSelect}
              onClose={() => setShowTimeModal(false)}
            />
          )}

          {showLocationModal && activeSession && (
            <LocationPickerModal
              currentLocation={activeSession.location}
              currentCity={city}
              onSelectLocation={handleLocationSelect}
              onClose={() => setShowLocationModal(false)}
            />
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default LocalDiscovery;
