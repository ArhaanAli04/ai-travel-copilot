/**
 * Main Chat Interface Component
 * Combines messages, input, and context chips
 */

import React from 'react';
import { type ChatSession, type ContextChip as ContextChipType } from '../../types/local-discovery';
import { ChatMessages } from './ChatMessages';
import { ChatInput } from './ChatInput';
import { MapPin } from 'lucide-react';

interface ChatInterfaceProps {
  session: ChatSession | null;
  loading: boolean;
  contextChips: ContextChipType[];
  onSendMessage: (message: string) => void;
  onRemoveChip?: (chipId: string) => void;
  onOpenPreferences?: () => void;
  onFeedback?: (poiId: string, feedbackType: 'thumbs_up' | 'thumbs_down') => void;
  onOpenMap?: (pois: any[]) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  session,
  loading,
  contextChips,
  onSendMessage,
  onRemoveChip,
  onOpenPreferences,
  onFeedback,
  onOpenMap,
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
    <div className="flex-1 flex flex-col h-full">
      {/* ✅ Messages - Takes up available space */}
      <div className="flex-1 overflow-y-auto">
        <ChatMessages
          messages={session.messages}
          loading={loading}
          onFeedback={onFeedback}
          onOpenMap={onOpenMap} 
        />
      </div>

      {/* ✅ Input - Fixed at bottom */}
      <div className="flex-shrink-0 border-t border-gray-200 bg-white">
        <ChatInput
          onSend={onSendMessage}
          loading={loading}
          disabled={!session}
        />
      </div>

      {/* ❌ REMOVED: Map rendering - handled by parent LocalDiscovery.tsx */}
    </div>
  );
};
