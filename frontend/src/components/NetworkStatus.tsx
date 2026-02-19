/**
 * Network Status Banner
 * Shows when user goes offline/online
 */

import React, { useEffect, useState } from 'react';
import { WifiOff, Wifi } from 'lucide-react';
import { useNetworkStatus } from '../hooks/useNetworkStatus';

export const NetworkStatus: React.FC = () => {
  const { isOnline, wasOffline } = useNetworkStatus();
  const [showBanner, setShowBanner] = useState(false);
  const [bannerType, setBannerType] = useState<'offline' | 'online'>('offline');

  useEffect(() => {
    if (!isOnline) {
      // Show offline banner
      setBannerType('offline');
      setShowBanner(true);
    } else if (wasOffline && isOnline) {
      // Show "back online" banner briefly
      setBannerType('online');
      setShowBanner(true);
      
      // Auto-hide after 3 seconds
      const timer = setTimeout(() => {
        setShowBanner(false);
      }, 3000);
      
      return () => clearTimeout(timer);
    } else {
      // Normal online state - hide banner
      setShowBanner(false);
    }
  }, [isOnline, wasOffline]);

  // Add/remove padding to body when banner shows/hides
  useEffect(() => {
    if (showBanner) {
      document.body.style.paddingTop = '48px'; // Banner height
    } else {
      document.body.style.paddingTop = '0';
    }
    
    return () => {
      document.body.style.paddingTop = '0';
    };
  }, [showBanner]);

  if (!showBanner) return null;

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-[9999] px-4 py-3 text-white text-center text-sm font-semibold transition-all duration-300 shadow-lg ${
        bannerType === 'offline'
          ? 'bg-[#EF4444]'
          : 'bg-[#10B981]'
      }`}
      role="alert"
    >
      <div className="flex items-center justify-center gap-2">
        {bannerType === 'offline' ? (
          <>
            <WifiOff className="w-5 h-5" />
            <span>No internet connection</span>
          </>
        ) : (
          <>
            <Wifi className="w-5 h-5" />
            <span>Back online</span>
          </>
        )}
      </div>
    </div>
  );
};
