import React, { useState, useEffect, useRef } from 'react';
import { disruptionApi } from '../services/api';
import type { DisruptionCase } from '../types/disruption';

interface ChatMessage {
  id: number;
  case_id: number;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatWidgetProps {
  disruptionCase: DisruptionCase;
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({ disruptionCase }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetchHistory();
  }, [disruptionCase.id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

  const handleSend = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setError(null);

    // Add user message immediately
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
        // ✅ Call real chat API with conversation history
        const conversationHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
        }));
        
        const response = await disruptionApi.chat(
        disruptionCase.id, 
        userMessage,
        conversationHistory
        );
        
        // Add assistant response
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
        // Remove the temp user message on error
        setMessages(prev => prev.filter(m => m.id !== tempUserMsg.id));
        setInputValue(userMessage); // Restore input
    } finally {
        setLoading(false);
    }
    };


  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestedQuestions = [
    "What are my passenger rights?",
    "How do I claim compensation?",
    "What alternative flights are available?",
    "Can I get a refund?",
  ];

  return (
    <div className={`bg-[rgba(26,29,36,0.6)] backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-xl transition-all ${
      isMinimized ? 'h-16' : 'h-[600px]'
    } sticky top-24 flex flex-col`}>
      {/* Header */}
      <div 
        className="flex items-center justify-between p-4 border-b border-[rgba(148,163,184,0.2)] cursor-pointer"
        onClick={() => setIsMinimized(!isMinimized)}
      >
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span>💬</span>
          AI Assistant
        </h3>
        <button className="text-gray-400 hover:text-white transition-colors">
          {isMinimized ? '▲' : '▼'}
        </button>
      </div>

      {/* Chat Content */}
      {!isMinimized && (
        <>
          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-8">
                <div className="text-4xl mb-3">👋</div>
                <p className="text-gray-400 text-sm mb-4">
                  Hi! I'm your AI assistant. Ask me anything about your flight disruption.
                </p>
                
                {/* Suggested Questions */}
                <div className="space-y-2">
                  <div className="text-xs text-gray-500 uppercase mb-2">Suggested Questions</div>
                  {suggestedQuestions.map((question, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInputValue(question)}
                      className="block w-full text-left p-2 bg-[rgba(148,163,184,0.1)] hover:bg-[rgba(148,163,184,0.2)] rounded text-sm text-gray-300 transition-colors"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                      : 'bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] text-gray-300'
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap leading-relaxed">
                    {message.content}
                  </div>
                  <div className={`text-xs mt-1 ${
                    message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                  }`}>
                    {new Date(message.timestamp).toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-gray-400">Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-[rgba(148,163,184,0.2)]">
            <div className="flex gap-2">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything..."
                disabled={loading}
                rows={2}
                className="flex-1 bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.2)] rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500/50 transition-colors resize-none disabled:opacity-50"
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || loading}
                className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
              >
                {loading ? '...' : '→'}
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Press Enter to send, Shift+Enter for new line
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatWidget;
