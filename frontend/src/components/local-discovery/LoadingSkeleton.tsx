/**
 * Loading Skeleton Component
 * Better loading UX than simple spinner
 */

import React from 'react';

export const ChatLoadingSkeleton: React.FC = () => {
  return (
    <div className="px-6 py-6 space-y-4 animate-pulse">
      {/* User message skeleton */}
      <div className="flex justify-end">
        <div className="max-w-[70%] bg-[#1F2937]/50 rounded-2xl rounded-br-sm p-4">
          <div className="h-4 bg-[#374151] rounded w-48 mb-2" />
          <div className="h-4 bg-[#374151] rounded w-32" />
        </div>
      </div>

      {/* Assistant message skeleton */}
      <div className="flex gap-3">
        <div className="w-8 h-8 rounded-full bg-[#8B5CF6]/20 flex-shrink-0" />
        <div className="flex-1 space-y-3">
          <div className="bg-[#1F2937]/50 rounded-2xl rounded-tl-sm p-4">
            <div className="h-4 bg-[#374151] rounded w-full mb-2" />
            <div className="h-4 bg-[#374151] rounded w-3/4 mb-2" />
            <div className="h-4 bg-[#374151] rounded w-5/6" />
          </div>

          {/* POI cards skeleton */}
          <div className="grid grid-cols-1 gap-3">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="bg-[#1F2937]/50 rounded-xl p-4 border border-[rgba(148,163,184,0.2)]"
              >
                <div className="flex gap-3">
                  <div className="w-20 h-20 bg-[#374151] rounded-lg flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-5 bg-[#374151] rounded w-3/4" />
                    <div className="h-3 bg-[#374151] rounded w-full" />
                    <div className="h-3 bg-[#374151] rounded w-5/6" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export const SessionsLoadingSkeleton: React.FC = () => {
  return (
    <div className="p-4 space-y-2 animate-pulse">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="p-3 rounded-lg bg-[#1F2937]/30 border border-[rgba(148,163,184,0.1)]"
        >
          <div className="h-4 bg-[#374151] rounded w-3/4 mb-2" />
          <div className="h-3 bg-[#374151] rounded w-1/2" />
        </div>
      ))}
    </div>
  );
};
