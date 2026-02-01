/**
 * Main Chat Interface Component
 * Combines messages, input, and context chips
 */

import React from 'react';
import { type ChatSession, type ContextChip as ContextChipType } from '../../types/local-discovery';
import { ChatMessages } from './ChatMessages';
import { ChatInput } from './ChatInput';
import { ContextChip } from './ContextChip';
import { Settings, MapPin } from 'lucide-react';

interface ChatInterfaceProps {
  session: ChatSession | null;
  loading: boolean;
  contextChips: ContextChipType[];
  onSendMessage: (message: string) => void;
  onRemoveChip?: (chipId: string) => void;
  onOpenPreferences?: () => void;
  onFeedback?: (poiId: string, feedbackType: 'thumbs_up' | 'thumbs_down') => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  session,
  loading,
  contextChips,
  onSendMessage,
  onRemoveChip,
  onOpenPreferences,
  onFeedback,
}) => {
  if (!session) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <MapPin className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <p className="text-lg mb-2">No chat selected</p>
          <p className="text-sm">Create a new chat to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-screen">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              {session.title}
            </h1>
            <p className="text-sm text-gray-500 capitalize">
              {session.city} • {session.messages.length} messages
            </p>
          </div>

          {onOpenPreferences && (
            <button
              onClick={onOpenPreferences}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Preferences"
            >
              <Settings className="w-5 h-5 text-gray-600" />
            </button>
          )}
        </div>

        {/* Context Chips */}
        {contextChips.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {contextChips.map((chip) => (
              <ContextChip
                key={chip.id}
                chip={chip}
                onRemove={onRemoveChip}
              />
            ))}
          </div>
        )}
      </div>

      {/* Messages */}
      <ChatMessages
        messages={session.messages}
        loading={loading}
        onFeedback={onFeedback}
      />

      {/* Input */}
      <ChatInput
        onSend={onSendMessage}
        loading={loading}
        disabled={!session}
      />
    </div>
  );
};
