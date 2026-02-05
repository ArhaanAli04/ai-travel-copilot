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
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-[#38BDF8]/10 flex items-center justify-center mx-auto mb-4">
            <MapPin className="w-8 h-8 text-[#38BDF8]" />
          </div>
          <p className="text-lg font-semibold text-white mb-2">No chat selected</p>
          <p className="text-sm text-[#9CA3AF]">Create a new chat to get started</p>
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
      <div className="flex-shrink-0 border-t border-[rgba(148,163,184,0.2)] bg-[#0a0e14]/50 backdrop-blur-xl">
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
