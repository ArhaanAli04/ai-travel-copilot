/**
 * Chat Input Component
 * Text input with send button and loading state
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  loading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  loading,
  disabled = false,
  placeholder = 'Ask me anything about local places...',
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (input.trim() && !loading && !disabled) {
      onSend(input.trim());
      setInput('');
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  return (
    <form onSubmit={handleSubmit} className="relative">
    <div className="flex items-end gap-2 p-4">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled || loading}
        rows={1}
        className="flex-1 resize-none rounded-lg bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white placeholder:text-[#6B7280] px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent disabled:bg-[#1F2937]/50 disabled:text-[#6B7280] max-h-32 overflow-y-auto custom-scrollbar"
      />
      
      <button
        type="submit"
        disabled={!input.trim() || loading || disabled}
        className="flex-shrink-0 p-3 bg-gradient-to-r from-[#F97316] to-[#38BDF8] text-white rounded-lg hover:from-[#EA580C] hover:to-[#3B82F6] disabled:from-[#6B7280] disabled:to-[#6B7280] disabled:cursor-not-allowed transition-all shadow-lg"
      >
        {loading ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <Send className="w-5 h-5" />
        )}
      </button>
    </div>
  </form>
  );
};
