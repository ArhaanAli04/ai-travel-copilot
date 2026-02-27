/**
 * ImageModal Component
 * Full-screen photo modal with smooth animation
 */

import React, { useEffect, useRef } from 'react';
import { X, Images } from 'lucide-react';
import { ImageCarousel } from './ImageCarousel';
import { usePOIPhotos } from '../../hooks/usePOIPhotos';

interface ImageModalProps {
  poiId: string;
  poiName: string;
  category: string;
  onClose: () => void;
}

// Source label mapping
const SOURCE_LABELS: Record<string, { label: string; color: string; subtitle?: string }> = {
  wikimedia:   { label: '📷 Wikimedia Commons',        color: 'text-[#22C55E]' },
  unsplash:    { label: '🖼️ Representative photos',    color: 'text-[#38BDF8]',
                 subtitle: 'Showing category photos for this place' },
  placeholder: { label: '🔍 No photos found',          color: 'text-[#6B7280]' },
};
export const ImageModal: React.FC<ImageModalProps> = ({
  poiId,
  poiName,
  category,
  onClose
}) => {
  const { photos, loading, error, source, fetchPhotos } = usePOIPhotos();
  const overlayRef = useRef<HTMLDivElement>(null);

  // Fetch photos when modal opens
  useEffect(() => {
    fetchPhotos(poiId);
  }, [poiId, fetchPhotos]);

  // Close on ESC key
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  // Prevent background scroll
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  // Close on backdrop click (not on modal content)
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  const sourceInfo = source ? SOURCE_LABELS[source] : null;

  return (
    // Full-screen overlay
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.85)', backdropFilter: 'blur(8px)' }}
      role="dialog"
      aria-modal="true"
      aria-label={`Photos of ${poiName}`}
    >
      {/* Modal Content */}
      <div
        className="relative w-full max-w-2xl bg-[#111827] rounded-2xl border border-[rgba(148,163,184,0.15)] shadow-2xl animate-fade-in"
        onClick={e => e.stopPropagation()}
      >

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[rgba(148,163,184,0.1)]">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 rounded-lg bg-[#38BDF8]/10 border border-[#38BDF8]/20 flex-shrink-0">
              <Images className="w-4 h-4 text-[#38BDF8]" />
            </div>
            <div className="min-w-0">
              <h2 className="text-white font-semibold text-base truncate">
                {poiName}
              </h2>
              <span className="text-[#6B7280] text-xs capitalize">{category}</span>
            </div>
          </div>

          {/* Close Button */}
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-white/5 border border-[rgba(148,163,184,0.15)] text-[#9CA3AF] hover:bg-white/10 hover:text-white transition-all flex-shrink-0 ml-3"
            aria-label="Close photo gallery"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5">

          {/* Loading State */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <div className="w-10 h-10 border-2 border-[#38BDF8]/30 border-t-[#38BDF8] rounded-full animate-spin" />
              <p className="text-[#6B7280] text-sm">Finding photos for {poiName}...</p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <div className="text-4xl">📷</div>
              <p className="text-[#EF4444] text-sm font-medium">Could not load photos</p>
              <p className="text-[#6B7280] text-xs">{error}</p>
              <button
                onClick={() => fetchPhotos(poiId)}
                className="mt-2 px-4 py-2 rounded-lg bg-[#38BDF8]/10 border border-[#38BDF8]/30 text-[#38BDF8] text-sm hover:bg-[#38BDF8]/20 transition-all"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Carousel */}
          {!loading && !error && (
            <ImageCarousel photos={photos} poiName={poiName} />
          )}

        </div>

        {/* Footer — Source Label */}
        {!loading && sourceInfo && source !== 'placeholder' && (
        <div className="px-5 pb-4 flex flex-col items-center gap-1">
            <span className={`text-xs font-medium ${sourceInfo.color}`}>
            {sourceInfo.label}
            </span>
            {sourceInfo.subtitle && (
            <span className="text-xs text-[#6B7280]">
                {sourceInfo.subtitle}
            </span>
            )}
        </div>
        )}

      </div>
    </div>
  );
};