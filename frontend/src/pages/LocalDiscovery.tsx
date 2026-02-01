/**
 * Local Discovery Page Component
 * For Vite + React Router setup
 */

import React, { useState } from 'react';
import { useLocalDiscovery } from '../hooks/useLocalDiscovery';
import { ChatSidebar } from '../components/local-discovery/ChatSidebar';
import { ChatInterface } from '../components/local-discovery/ChatInterface';
import { PreferencesPanel } from '../components/local-discovery/PreferencesPanel';
import { QuickActions } from '../components/local-discovery/QuickActions';
import { ContextDisplay } from '../components/local-discovery/ContextDisplay';
import { Menu, X } from 'lucide-react';

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

  const handleSendMessage = (message: string) => {
    sendMessage(message, false); // Set to true for mock responses during testing
  };

  const handleQuickAction = (query: string) => {
    if (activeSession) {
      sendMessage(query, false);
      setShowQuickActions(false);
    }
  };

  
  const handleFeedback = async (
    poiId: string,
    feedbackType: 'thumbs_up' | 'thumbs_down'
  ) => {
    await submitFeedback(poiId, feedbackType); // ✅ Call the hook function
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar Toggle (Mobile) */}
      <button
        onClick={() => setShowSidebar(!showSidebar)}
        className="fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-lg lg:hidden"
      >
        {showSidebar ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Sidebar */}
      <div
        className={`${
          showSidebar ? 'translate-x-0' : '-translate-x-full'
        } fixed lg:relative lg:translate-x-0 inset-y-0 left-0 z-40 transition-transform duration-300`}
      >
        <ChatSidebar
          sessions={sessions}
          activeSessionId={activeSession?.id || null}
          onSelectSession={selectSession}
          onNewSession={createNewSession}
          onDeleteSession={deleteSession}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Error Banner */}
        {error && (
          <div className="px-6 py-3 bg-red-50 border-b border-red-200">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Context Display */}
        {activeSession && contextChips.length > 0 && (
          <div className="px-6 py-4 bg-white border-b border-gray-200">
            <ContextDisplay
              chips={contextChips}
              onRemoveChip={removePreference}
              showInfo={activeSession.messages.length === 0}
            />
          </div>
        )}

        {/* Quick Actions (Show on new session or when explicitly toggled) */}
        {activeSession && showQuickActions && activeSession.messages.length <= 1 && (
          <QuickActions onSelectAction={handleQuickAction} disabled={loading} />
        )}

        {/* Chat Interface */}
        <ChatInterface
          session={activeSession}
          loading={loading}
          contextChips={contextChips}
          onSendMessage={handleSendMessage}
          onRemoveChip={removePreference}
          onOpenPreferences={() => setShowPreferences(true)}
          onFeedback={handleFeedback}
        />
      </div>

      {/* Preferences Panel */}
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
