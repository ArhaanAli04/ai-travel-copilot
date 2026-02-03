/**
 * Chat Messages Container
 * Scrollable list of messages with auto-scroll
 */

import React, { useEffect, useRef } from 'react';
import { type Message } from '../../types/local-discovery';
import { MessageBubble } from './MessageBubble';
import { Loader2 } from 'lucide-react';

interface ChatMessagesProps {
  messages: Message[];
  loading: boolean;
  onFeedback?: (poiId: string, feedbackType: 'thumbs_up' | 'thumbs_down') => void;
  onOpenMap?: (pois: any[]) => void; // ✅ Already added
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  loading,
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
      className="flex-1 overflow-y-auto px-6 py-6 bg-gray-50"
    >
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <p className="text-lg mb-2">👋 Start a conversation</p>
            <p className="text-sm">Ask me to find places around you!</p>
          </div>
        </div>
      ) : (
        <div className="max-w-4xl mx-auto">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onFeedback={onFeedback}
              onOpenMap={onOpenMap} // ✅ ADD THIS LINE - Pass to MessageBubble
            />
          ))}

          {/* Loading indicator */}
          {loading && (
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center">
                <Loader2 className="w-5 h-5 text-white animate-spin" />
              </div>
              <div className="px-4 py-3 bg-gray-100 rounded-2xl rounded-tl-sm">
                <p className="text-sm text-gray-600">Searching for places...</p>
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
