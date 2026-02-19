/**
 * Error State Component
 * Shows error message with retry button
 */

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retrying?: boolean;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message,
  onRetry,
  retrying = false,
}) => {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="max-w-md w-full text-center">
        <div className="w-16 h-16 rounded-full bg-[#EF4444]/10 flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-8 h-8 text-[#EF4444]" />
        </div>
        
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
        <p className="text-sm text-[#9CA3AF] mb-6">{message}</p>

        {onRetry && (
          <button
            onClick={onRetry}
            disabled={retrying}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#F97316] to-[#38BDF8] text-white rounded-lg hover:from-[#EA580C] hover:to-[#3B82F6] disabled:from-[#6B7280] disabled:to-[#6B7280] disabled:cursor-not-allowed transition-all shadow-lg"
          >
            <RefreshCw className={`w-4 h-4 ${retrying ? 'animate-spin' : ''}`} />
            {retrying ? 'Retrying...' : 'Try Again'}
          </button>
        )}
      </div>
    </div>
  );
};
