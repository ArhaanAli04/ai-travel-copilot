/**
 * Message Bubble Component
 * Displays user or assistant messages in the chat
 */

import React from 'react';
import {type  Message } from '../../types/local-discovery';
import { POICard } from './POICard';
import { User, Bot } from 'lucide-react';
import { formatTime } from '../../utils/datetime';

interface MessageBubbleProps {
  message: Message;
  onFeedback?: (poiId: string, feedbackType: 'thumbs_up' | 'thumbs_down') => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onFeedback }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-6`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-blue-600' : 'bg-purple-600'
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
              ? 'bg-blue-600 text-white rounded-tr-sm'
              : 'bg-gray-100 text-gray-900 rounded-tl-sm'
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>

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
          className={`mt-1 text-xs text-gray-500 ${
            isUser ? 'text-right' : 'text-left'
          }`}
        >
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
};
