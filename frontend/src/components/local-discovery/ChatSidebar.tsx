/**
 * Chat Sidebar Component
 * Shows list of chat sessions with icon sidebar + expandable list
 */

import React, { useState } from 'react';
import { type ChatSession } from '../../types/local-discovery';
import { MessageSquare, Plus, Trash2, MapPin, Clock } from 'lucide-react';
import { formatRelativeTime } from '../../utils/datetime';

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  const renderSessionCard = (session: ChatSession) => {
   

  return (
    <div
      key={session.id}
      onClick={() => {
        onSelectSession(session.id);
        setIsExpanded(false);
      }}
      className={`group relative p-3 rounded-xl cursor-pointer transition-all ${
        activeSessionId === session.id
          ? 'bg-[#38BDF8]/20 border border-[#38BDF8]/50'
          : 'bg-[#1F2937]/30 border border-[rgba(148,163,184,0.1)] hover:bg-[#1F2937]/50 hover:border-[#38BDF8]/30'
      }`}
    >
      {/* Session Title */}
      <h4 className="text-white font-semibold text-sm mb-2 pr-8 truncate">
        {session.title}
      </h4>

      {/* Session Details */}
      <div className="space-y-1.5 text-xs text-[#9CA3AF]">
        <div className="flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate capitalize">{session.city}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 flex-shrink-0" />
          <span className="truncate">{formatRelativeTime(new Date(session.updated_at))}</span>
        </div>
        {session.messages.length > 0 && (
          <div className="flex items-center gap-1.5">
            <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{session.messages.length} messages</span>
          </div>
        )}
      </div>

      {/* Delete Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDeleteSession(session.id);
        }}
        className={`absolute top-3 right-3 transition-all p-1.5 rounded-lg bg-[#EF4444]/10 hover:bg-[#EF4444]/20 hover:scale-110 backdrop-blur-sm cursor-pointer ${
          activeSessionId === session.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
        }`}
        aria-label="Delete chat"
      >
        <Trash2 className="w-4 h-4 text-[#EF4444]" />
      </button>
    </div>
  );
};

  return (
    <>
      {/* Icon Sidebar - Always Visible */}
      <div className="fixed left-0 top-16 h-[calc(100vh-64px)] w-20 bg-[#0a0e14]/95 backdrop-blur-xl border-r border-[rgba(148,163,184,0.2)] z-40">
        <div className="h-full flex flex-col items-center pt-8 gap-8">
          {/* All Chats Icon */}
          <div
            className="cursor-pointer flex flex-col items-center gap-2"
            onMouseEnter={() => setIsExpanded(true)}
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <div className="w-12 h-12 rounded-xl bg-[#38BDF8]/10 flex items-center justify-center hover:bg-[#38BDF8]/20 transition-all relative">
              <MessageSquare className="w-7 h-7 text-[#38BDF8]" />
              {sessions.length > 0 && (
                <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#F97316] text-white text-xs font-bold flex items-center justify-center">
                  {sessions.length}
                </div>
              )}
            </div>
            <p className="text-xs font-semibold text-[#9CA3AF]">Chats</p>
          </div>

          {/* New Chat Button */}
          <div
            className="cursor-pointer flex flex-col items-center gap-2"
            onClick={onNewSession}
          >
            <div className="w-12 h-12 rounded-xl bg-[#22C55E]/10 flex items-center justify-center hover:bg-[#22C55E]/20 transition-all">
              <Plus className="w-7 h-7 text-[#22C55E]" />
            </div>
            <p className="text-xs font-semibold text-[#9CA3AF]">New</p>
          </div>
        </div>
      </div>

      {/* Expanded Chat List - Slides in from left */}
      {isExpanded && (
        <div
          onMouseLeave={() => setIsExpanded(false)}
          className="fixed left-20 top-16 h-[calc(100vh-64px)] w-64 bg-[#0a0e14]/95 backdrop-blur-xl border-r border-[rgba(148,163,184,0.2)] z-30 animate-slide-in-left"
        >
          {/* Header */}
          <div className="flex items-center gap-3 p-5 border-b border-[rgba(148,163,184,0.2)]">
            <div className="w-10 h-10 rounded-xl bg-[#38BDF8]/10 flex items-center justify-center flex-shrink-0">
              <MessageSquare className="w-6 h-6 text-[#38BDF8]" />
            </div>
            <div className="flex-1 overflow-hidden">
              <h3 className="text-lg font-bold text-white whitespace-nowrap">
                Local Discovery
              </h3>
              <p className="text-xs text-[#9CA3AF]">
                {sessions.length} {sessions.length === 1 ? 'chat' : 'chats'}
              </p>
            </div>
          </div>

          {/* Sessions List */}
          <div className="overflow-y-auto flex-1 custom-scrollbar h-[calc(100vh-144px)]">
            <div className="p-3 space-y-2">
              {sessions.length === 0 ? (
                <div className="text-center py-8 px-4">
                  <MessageSquare className="w-12 h-12 text-[#6B7280] mx-auto mb-3" />
                  <p className="text-sm text-[#9CA3AF] mb-1">No chat history yet</p>
                  <p className="text-xs text-[#6B7280]">Start a new conversation!</p>
                </div>
              ) : (
                sessions.map((session) => renderSessionCard(session))
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};
