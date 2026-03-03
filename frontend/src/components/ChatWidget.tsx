import React, { useState, useEffect, useRef } from 'react';
import { ArrowUp, Loader2 } from 'lucide-react';
import { disruptionApi } from '../services/api';
import type { DisruptionCase } from '../types/disruption';
import ReactMarkdown from 'react-markdown';

interface ChatMessage {
  id: number;
  case_id: number;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatWidgetProps {
  disruptionCase: DisruptionCase;
  hideHeader?: boolean;
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({ disruptionCase, hideHeader = false }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => { fetchHistory(); }, [disruptionCase.id]);
  useEffect(() => { scrollToBottom(); }, [messages]);

  const fetchHistory = async () => {
    try {
      const response = await disruptionApi.getChatHistory(disruptionCase.id);
      setMessages(response.messages || []);
    } catch (err: any) {
      console.error('Failed to fetch chat history:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setShowScrollBtn(distanceFromBottom > 100);
  };

  const handleSend = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setError(null);

    // Reset textarea height
    if (inputRef.current) inputRef.current.style.height = 'auto';

    const tempUserMsg: ChatMessage = {
      id: Date.now(),
      case_id: disruptionCase.id,
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const conversationHistory = messages.map(msg => ({ role: msg.role, content: msg.content }));
      const response = await disruptionApi.chat(disruptionCase.id, userMessage, conversationHistory);
      const assistantMsg: ChatMessage = {
        id: Date.now() + 1,
        case_id: disruptionCase.id,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.message || 'Failed to send message');
      setMessages(prev => prev.filter(m => m.id !== tempUserMsg.id));
      setInputValue(userMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  const suggestedQuestions = [
    "What are my passenger rights?",
    "How do I claim compensation?",
    "What alternative flights are available?",
    "Can I get a refund?",
  ];

  return (
    <div
      className={`bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl transition-all duration-300 sticky top-24 flex flex-col overflow-hidden h-full ${
        isMinimized ? 'h-14' : ''
      }`}
    >
      {/* Header — matches local discovery panel header style */}
      {!hideHeader && (
      <div
        className="flex items-center justify-between px-4 py-3 border-b border-[rgba(148,163,184,0.2)] cursor-pointer hover:bg-[rgba(148,163,184,0.04)] transition-colors flex-shrink-0"
        onClick={() => setIsMinimized(!isMinimized)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[#8B5CF6] flex items-center justify-center flex-shrink-0">
            <span className="text-white text-sm">✦</span>
          </div>
          <div>
            <p className="text-white font-semibold text-sm">AI Assistant</p>
            <p className="text-[#9CA3AF] text-xs">Flight disruption specialist</p>
          </div>
        </div>
        <button className="text-[#9CA3AF] hover:text-white transition-colors p-1 hover:bg-[rgba(148,163,184,0.1)] rounded-lg">
          {isMinimized ? '▲' : '▼'}
        </button>
      </div>
      )}

      {(!isMinimized || hideHeader) && (
        <>
          {/* Messages — matches ChatMessages.tsx scroll container */}
          <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-4 py-4 custom-scrollbar" onScroll={handleScroll}>
            {messages.length === 0 ? (
              /* Empty state — matches ChatMessages empty state */
              <div className="flex items-center justify-center h-full">
                <div className="text-center px-4">
                  
                  <p className="text-lg font-semibold text-white mb-2">
                    Hi! I'm your AI assistant
                  </p>
                  <p className="text-sm text-[#9CA3AF] mb-6">
                    Ask me anything about your flight disruption.
                  </p>

                  {/* Suggested questions */}
                  <div className="space-y-2 text-left">
                    <p className="text-xs text-[#6B7280] uppercase tracking-wider mb-3 text-center">
                      Suggested Questions
                    </p>
                    {suggestedQuestions.map((question, idx) => (
                      <button
                        key={idx}
                        onClick={() => setInputValue(question)}
                        className="block w-full text-left px-4 py-2.5 rounded-xl bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-sm text-[#E5E7EB] hover:border-[#38BDF8]/40 hover:bg-[#1F2937]/80 transition-all"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              /* Message list — matches MessageBubble layout pattern */
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 animate-fade-in ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {/* Assistant avatar */}
                    {message.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-[#8B5CF6] flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-white text-xs">✦</span>
                      </div>
                    )}

                    <div className={`max-w-[80%] group`}>
                      <div className={`px-4 py-3 text-sm leading-relaxed ${
                        message.role === 'user'
                          ? 'bg-white text-[#111827] rounded-2xl rounded-tr-sm font-medium'
                          : 'bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] text-[#E5E7EB] rounded-2xl rounded-tl-sm'
                      }`}>
                        {message.role === 'user' ? (
                          message.content
                        ) : (
                          <ReactMarkdown
                            components={{
                              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                              strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                              ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2">{children}</ol>,
                              ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>,
                              li: ({ children }) => <li className="text-[#E5E7EB]">{children}</li>,
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        )}
                      </div>
                      {/* Timestamp on hover */}
                      <div className={`text-[10px] mt-1 text-[#6B7280] opacity-0 group-hover:opacity-100 transition-opacity ${
                        message.role === 'user' ? 'text-right' : 'text-left'
                      }`}>
                        {new Date(message.timestamp).toLocaleTimeString([], {
                          hour: '2-digit', minute: '2-digit'
                        })}
                      </div>
                    </div>

                    {/* User avatar */}
                    {message.role === 'user' && (
                      <div className="w-8 h-8 rounded-full bg-[#374151] flex items-center justify-center flex-shrink-0 mt-0.5 text-white text-xs font-bold">
                        Y
                      </div>
                    )}
                  </div>
                ))}

                {/* Error state — matches ErrorState pattern */}
                {error && !loading && (
                  <div className="flex items-start gap-3 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-2xl">
                    <span className="text-red-400 text-sm">⚠️</span>
                    <p className="text-red-400 text-sm">{error}</p>
                  </div>
                )}

                {/* Loading indicator — matches ChatMessages loading pattern */}
                {loading && (
                  <div className="flex items-center gap-3 animate-fade-in">
                    <div className="w-8 h-8 rounded-full bg-[#8B5CF6] flex items-center justify-center flex-shrink-0">
                      <Loader2 className="w-4 h-4 text-white animate-spin" />
                    </div>
                    <div className="px-4 py-3 bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] rounded-2xl rounded-tl-sm">
                      <p className="text-sm text-[#E5E7EB]">Thinking...</p>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
          {/* Scroll to bottom button */}
          <div className="relative">
            {showScrollBtn && (
              <div className="absolute -top-10 left-1/2 -translate-x-1/2 z-10">
                <button
                  onClick={() => {
                    if (messagesContainerRef.current) {
                      messagesContainerRef.current.scrollTo({
                        top: messagesContainerRef.current.scrollHeight,
                        behavior: 'smooth',
                      });
                    }
                    setShowScrollBtn(false);
                  }}
                  className="w-8 h-8 rounded-full bg-[#1F2937] border border-[rgba(148,163,184,0.3)] text-gray-400 hover:text-white hover:border-[rgba(148,163,184,0.6)] transition-all flex items-center justify-center shadow-lg"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              </div>
            )}
          </div>
          {/* Input — exact ChatInput.tsx pattern */}
          <div className="flex-shrink-0 border-t border-[rgba(148,163,184,0.2)] bg-[#0a0e14]/50 backdrop-blur-xl">
            <div className="flex items-end gap-2 p-4">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything about your disruption..."
                disabled={loading}
                rows={1}
                className="flex-1 resize-none rounded-lg bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white placeholder:text-[#6B7280] px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent disabled:bg-[#1F2937]/50 disabled:text-[#6B7280] max-h-32 overflow-y-auto custom-scrollbar"
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || loading}
                className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-full bg-white text-[#111827] hover:bg-[#E5E7EB] disabled:bg-[#374151] disabled:text-[#6B7280] disabled:cursor-not-allowed transition-all shadow-md"
              >
                {loading
                  ? <Loader2 className="w-5 h-5 animate-spin" />
                  : <ArrowUp className="w-5 h-5" />
                }
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatWidget;
