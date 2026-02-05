import React, { useState } from 'react';
import { useLocalDiscovery } from '../hooks/useLocalDiscovery';
import { ChatSidebar } from '../components/local-discovery/ChatSidebar';
import { ChatInterface } from '../components/local-discovery/ChatInterface';
import { PreferencesPanel } from '../components/local-discovery/PreferencesPanel';
import { QuickActions } from '../components/local-discovery/QuickActions';
import { ContextDisplay } from '../components/local-discovery/ContextDisplay';
import { Menu, X, Settings } from 'lucide-react';
import { MapView } from '../components/local-discovery/MapView';
import { TimePickerModal } from '../components/local-discovery/TimePickerModal';
import { LocationPickerModal } from '../components/local-discovery/LocationPickerModal';
import { Navigation } from '../components/Navigation';

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
    createNewSession,
    selectSession,
    deleteSession,
    sendMessage,
    addPreference,
    removePreference,
    handleFeedback: submitFeedback,
    setManualLocation,
    setManualTime,
  } = useLocalDiscovery();

  const [showPreferences, setShowPreferences] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [showMap, setShowMap] = useState(false);
  const [mapPOIs, setMapPOIs] = useState<any[]>([]);
  const [showTimeModal, setShowTimeModal] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);

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
    sendMessage(message, false);
  };

  const handleQuickAction = (query: string) => {
    if (activeSession) {
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#05070a] to-[#0b1120]">
    {/* Navigation Bar */}
    <Navigation />
    
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
        <div className="w-2/5 h-[calc(100vh-64px)] flex-shrink-0 ml-20">
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
        
          <ChatSidebar
            sessions={sessions}
            activeSessionId={activeSession?.id || null}
            onSelectSession={selectSession}
            onNewSession={createNewSession}
            onDeleteSession={deleteSession}
          />
        
      )}

      {/* RIGHT SIDE: Chat */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden ">
        {error && (
          <div className="px-6 py-3 bg-[#EF4444]/10 border-b border-[#EF4444]/30">
            <p className="text-sm text-[#EF4444]">{error}</p>
          </div>
        )}

        {activeSession && (
          <>
            {/* Title bar with settings */}
            <div className="px-6 py-4 bg-[#0a0e14]/50 backdrop-blur-xl border-b border-[rgba(148,163,184,0.2)] flex-shrink-0">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-xl font-semibold text-white">
                    {activeSession.title}
                  </h1>
                  <p className="text-sm text-[#9CA3AF] capitalize">
                    {activeSession.city} • {activeSession.messages.length} messages
                  </p>
                </div>
                <button
                  onClick={() => setShowPreferences(true)}
                  className="p-2 hover:bg-white/5 rounded-lg transition-colors"
                  aria-label="Preferences"
                >
                  <Settings className="w-5 h-5 text-[#9CA3AF]" />
                </button>
              </div>
            </div>

            {/* Context chips */}
            <div className="px-6 py-4 bg-[#0a0e14]/50 backdrop-blur-xl border-b border-[rgba(148,163,184,0.2)] flex-shrink-0">
              <ContextDisplay
                chips={contextChips}
                onRemoveChip={removePreference}
                onEditChip={handleEditChip}
                showInfo={activeSession.messages.length === 0}
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
  );
};

export default LocalDiscovery;
