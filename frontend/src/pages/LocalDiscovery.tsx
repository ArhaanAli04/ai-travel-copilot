import React, { useState } from 'react';
import { useLocalDiscovery } from '../hooks/useLocalDiscovery';
import { ChatSidebar } from '../components/local-discovery/ChatSidebar';
import { ChatInterface } from '../components/local-discovery/ChatInterface';
import { PreferencesPanel } from '../components/local-discovery/PreferencesPanel';
import { QuickActions } from '../components/local-discovery/QuickActions';
import { ContextDisplay } from '../components/local-discovery/ContextDisplay';
import { Menu, X } from 'lucide-react';
import { MapView } from '../components/local-discovery/MapView';

const LocalDiscovery = () => {
  const {
    sessions,
    activeSession,
    loading,
    error,
    contextChips,
    preferences,
    createNewSession,
    selectSession,
    deleteSession,
    sendMessage,
    addPreference,
    removePreference,
    handleFeedback: submitFeedback,
  } = useLocalDiscovery();

  const [showPreferences, setShowPreferences] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [showMap, setShowMap] = useState(false);
  const [mapPOIs, setMapPOIs] = useState<any[]>([]);

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
    console.log('🗺️ Opening map with', pois.length, 'POIs'); // DEBUG
    setMapPOIs(pois);
    setShowMap(true);
    console.log('🗺️ showMap set to:', true); // DEBUG
  };

  const handleCloseMap = () => {
    console.log('❌ Closing map'); // DEBUG
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

  console.log('🔄 LocalDiscovery render - showMap:', showMap); // DEBUG

  return (
    <div className="flex h-screen bg-gray-50">
      {/* DEBUG INFO - REMOVE LATER */}
      

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
        <div className="w-2/5 h-screen flex-shrink-0 bg-red-100">
          {/* RED background to debug visibility */}
          <div className="h-full w-full bg-white">
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
        </div>
      ) : (
        <div
          className={`${
            showSidebar ? 'translate-x-0' : '-translate-x-full'
          } fixed lg:relative lg:translate-x-0 inset-y-0 left-0 z-40 transition-transform duration-300 w-80 bg-blue-100`}
        >
          {/* BLUE background to debug visibility */}
          <ChatSidebar
            sessions={sessions}
            activeSessionId={activeSession?.id || null}
            onSelectSession={selectSession}
            onNewSession={createNewSession}
            onDeleteSession={deleteSession}
          />
        </div>
      )}

      {/* RIGHT SIDE: Chat */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {error && (
          <div className="px-6 py-3 bg-red-50 border-b border-red-200">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {activeSession && contextChips.length > 0 && (
          <div className="px-6 py-4 bg-white border-b border-gray-200">
            <ContextDisplay
              chips={contextChips}
              onRemoveChip={removePreference}
              showInfo={activeSession.messages.length === 0}
            />
          </div>
        )}

        {activeSession && showQuickActions && activeSession.messages.length <= 1 && (
          <QuickActions onSelectAction={handleQuickAction} disabled={loading} />
        )}

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

      {showPreferences && (
        <PreferencesPanel
          preferences={preferences}
          onUpdatePreferences={addPreference}
          onClose={() => setShowPreferences(false)}
        />
      )}
    </div>
  );
};

export default LocalDiscovery;
