/**
 * Message Bubble Component
 * Displays user or assistant messages in the chat
 */

import React from 'react';
import { type Message } from '../../types/local-discovery';
import { POICard } from './POICard';
import { User, Bot, MapPin } from 'lucide-react';
import { formatTime } from '../../utils/datetime';

interface MessageBubbleProps {
  message: Message;
  onFeedback?: (poiId: string, feedbackType: 'thumbs_up' | 'thumbs_down') => void;
  onOpenMap?: (pois: any[]) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ 
  message, 
  onFeedback, 
  onOpenMap 
}) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-6`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser 
            ? 'bg-gradient-to-br from-[#38BDF8] to-[#3B82F6]' 
            : 'bg-gradient-to-br from-[#8B5CF6] to-[#7C3AED]'
        }`}
      >
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-3xl ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        {/* Message Bubble */}
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-gradient-to-r from-[#38BDF8] to-[#3B82F6] text-white rounded-tr-sm shadow-lg shadow-[#38BDF8]/20'
              : 'bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] text-white rounded-tl-sm'
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* View on Map button (for assistant messages with POIs) */}
        {!isUser && message.pois && message.pois.length > 0 && onOpenMap && (
          <button
            onClick={() => onOpenMap(message.pois!)}
            className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-[#8B5CF6] text-white text-sm font-medium rounded-lg hover:bg-[#7C3AED] transition-all shadow-lg hover:shadow-[#8B5CF6]/20 cursor-pointer"
          >
            <MapPin className="w-4 h-4" />
            View {message.pois.length} {message.pois.length === 1 ? 'place' : 'places'} on map
          </button>
        )}

        {/* POI Cards (for assistant messages) */}
        {!isUser && message.pois && message.pois.length > 0 && (
          <div className="mt-4 space-y-3 w-full">
            {message.pois.map((poi) => (
              <POICard key={poi.poi_id} poi={poi} onFeedback={onFeedback} />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <div
          className={`mt-1 text-xs text-[#6B7280] ${
            isUser ? 'text-right' : 'text-left'
          }`}
        >
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
};
