import React, { useEffect, useRef } from 'react';
import { X, Images } from 'lucide-react';
import { PhotoCarousel } from './shared/PhotoCarousel';
import { useActivityPhotos } from '../hooks/useActivityPhotos';
import { createPortal } from 'react-dom';   

interface ActivityPhotoModalProps {
  activityId: number;
  activityTitle: string;
  category?: string;
  onClose: () => void;
}

const SOURCE_LABELS: Record<string, { label: string; color: string; subtitle?: string }> = {
  google_images: { label: '📷 Google Images',             color: 'text-[#38BDF8]' },
  wikimedia:     { label: '📷 Wikimedia Commons',         color: 'text-[#22C55E]' },
  unsplash:      { label: '🖼️ Representative photos',     color: 'text-[#38BDF8]',
                   subtitle: 'Showing category photos for this place' },
  placeholder:   { label: '🔍 No photos found',           color: 'text-[#6B7280]' },
};

export const ActivityPhotoModal: React.FC<ActivityPhotoModalProps> = ({
  activityId,
  activityTitle,
  category,
  onClose,
}) => {
  const { photos, loading, error, source, fetchPhotos } = useActivityPhotos();
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchPhotos(activityId);
  }, [activityId, fetchPhotos]);

  // ESC to close
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  // Prevent background scroll
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  const sourceInfo = source ? SOURCE_LABELS[source] : null;

  return createPortal(
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.85)', backdropFilter: 'blur(8px)' }}
      role="dialog"
      aria-modal="true"
      aria-label={`Photos of ${activityTitle}`}
    >
      <div
        className="relative w-full max-w-2xl bg-[#111827] rounded-2xl border border-[rgba(148,163,184,0.15)] shadow-2xl animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[rgba(148,163,184,0.1)]">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 rounded-lg bg-[#F59E0B]/10 border border-[#F59E0B]/20 flex-shrink-0">
              <Images className="w-4 h-4 text-[#F59E0B]" />
            </div>
            <div className="min-w-0">
              <h2 className="text-white font-semibold text-base truncate">{activityTitle}</h2>
              {category && <span className="text-[#6B7280] text-xs capitalize">{category}</span>}
            </div>
          </div>
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
          {/* Loading */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <div className="w-10 h-10 border-2 border-[#F59E0B]/30 border-t-[#F59E0B] rounded-full animate-spin" />
              <p className="text-[#6B7280] text-sm">Finding photos for {activityTitle}...</p>
            </div>
          )}

          {/* Error */}
          {error && !loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <div className="text-4xl">📷</div>
              <p className="text-[#EF4444] text-sm font-medium">Could not load photos</p>
              <p className="text-[#6B7280] text-xs">{error}</p>
              <button
                onClick={() => fetchPhotos(activityId)}
                className="mt-2 px-4 py-2 rounded-lg bg-[#F59E0B]/10 border border-[#F59E0B]/30 text-[#F59E0B] text-sm hover:bg-[#F59E0B]/20 transition-all"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Carousel */}
          {!loading && !error && (
             <>
                {photos.length === 0 || (photos.length === 1 && !photos[0].url) ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                    <div className="text-5xl">🏛️</div>
                    <p className="text-[#9CA3AF] text-sm font-medium">No photos found for this activity</p>
                    <p className="text-[#6B7280] text-xs">Try searching for it online</p>
                </div>
                ) : (
                <PhotoCarousel photos={photos} name={activityTitle} />
                )}
            </>
          )}
        </div>

        {/* Footer */}
        {!loading && sourceInfo && source !== 'placeholder' && (
          <div className="px-5 pb-4 flex flex-col items-center gap-1">
            <span className={`text-xs font-medium ${sourceInfo.color}`}>
              {sourceInfo.label}
            </span>
            {sourceInfo.subtitle && (
              <span className="text-xs text-[#6B7280]">{sourceInfo.subtitle}</span>
            )}
          </div>
        )}
      </div>
    </div>,
    document.body
  );
};
