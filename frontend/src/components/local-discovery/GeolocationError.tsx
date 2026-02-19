/**
 * Geolocation Error Component
 * Shows when location access is denied or unavailable
 */

import React from 'react';
import { MapPin, Settings } from 'lucide-react';

interface GeolocationErrorProps {
  error: string;
  onUseManualLocation?: () => void;
  onRetry?: () => void;
}

export const GeolocationError: React.FC<GeolocationErrorProps> = ({
  error,
  onUseManualLocation,
  onRetry,
}) => {
  const isPermissionDenied = error.includes('denied') || error.includes('permission');

  return (
    <div className="flex items-center justify-center p-8">
      <div className="max-w-md w-full text-center">
        <div className="w-16 h-16 rounded-full bg-[#F59E0B]/10 flex items-center justify-center mx-auto mb-4">
          <MapPin className="w-8 h-8 text-[#F59E0B]" />
        </div>

        <h3 className="text-lg font-semibold text-white mb-2">Location Access Needed</h3>
        <p className="text-sm text-[#9CA3AF] mb-6">{error}</p>

        {isPermissionDenied && (
          <div className="bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] rounded-lg p-4 mb-6 text-left">
            <div className="flex items-start gap-3">
              <Settings className="w-5 h-5 text-[#38BDF8] flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-white mb-2">How to enable location:</p>
                <ol className="text-xs text-[#9CA3AF] space-y-1 list-decimal list-inside">
                  <li>Click the lock icon in your browser's address bar</li>
                  <li>Find "Location" permissions</li>
                  <li>Select "Allow"</li>
                  <li>Reload the page</li>
                </ol>
              </div>
            </div>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          {onUseManualLocation && (
            <button
              onClick={onUseManualLocation}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-[#F97316] to-[#38BDF8] text-white rounded-lg hover:from-[#EA580C] hover:to-[#3B82F6] transition-all shadow-lg text-sm font-medium"
            >
              Choose Location Manually
            </button>
          )}

          {onRetry && (
            <button
              onClick={onRetry}
              className="flex-1 px-4 py-3 bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white rounded-lg hover:bg-[#374151] transition-all text-sm font-medium"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
