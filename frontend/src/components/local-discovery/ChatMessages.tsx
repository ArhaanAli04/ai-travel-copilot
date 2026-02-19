/**
 * Chat Messages Container
 * Scrollable list of messages with auto-scroll
 */

import React, { useEffect, useRef } from 'react';
import { type Message } from '../../types/local-discovery';
import { MessageBubble } from './MessageBubble';
import { Loader2 } from 'lucide-react';
import { ChatLoadingSkeleton } from './LoadingSkeleton'; // ✨ NEW
import { ErrorState } from './ErrorState'; // ✨ NEW

interface ChatMessagesProps {
  messages: Message[];
  loading: boolean;
  error?: string | null; // ✨ NEW
  onFeedback?: (poiId: string, feedbackType: 'thumbs_up' | 'thumbs_down') => void;
  onOpenMap?: (pois: any[]) => void; // ✅ Already added
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  loading,
  error, // ✨ NEW
  onFeedback,
  onOpenMap, // ✅ Already added
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
  <div
      ref={containerRef}
      className="flex-1 overflow-y-auto px-6 py-6 custom-scrollbar"
    >
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-[#8B5CF6]/10 flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">👋</span>
            </div>
            <p className="text-lg font-semibold text-white mb-2">Start a conversation</p>
            <p className="text-sm text-[#9CA3AF]">Ask me to find places around you!</p>
          </div>
        </div>
      ) : (
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onFeedback={onFeedback}
              onOpenMap={onOpenMap}
            />
          ))}

          {/* ✨ NEW: Error State */}
          {error && !loading && (
            <ErrorState
              title="Message Failed"
              message={error}
              onRetry={undefined} // Retry handled at parent level
            />
          )}

          {/* ✨ ENHANCED: Loading with skeleton */}
          {loading && messages.length === 0 && (
            <ChatLoadingSkeleton />
          )}

          {/* Loading indicator for new message */}
          {loading && messages.length > 0 && (
            <div className="flex items-center gap-3 mb-6 animate-fade-in">
              <div className="w-8 h-8 rounded-full bg-[#8B5CF6] flex items-center justify-center flex-shrink-0">
                <Loader2 className="w-5 h-5 text-white animate-spin" />
              </div>
              <div className="px-4 py-3 bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] rounded-2xl rounded-tl-sm">
                <p className="text-sm text-[#E5E7EB]">Searching for places...</p>
              </div>
            </div>
          )}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  );
};