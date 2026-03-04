import React, { useEffect, useRef, useState } from 'react';
import { X, Images } from 'lucide-react';
import { PhotoCarousel } from './shared/PhotoCarousel';
import { createPortal } from 'react-dom';

interface HotelPhotoModalProps {
  hotelName: string;
  images: string[];  // raw URL strings from SerpAPI
  onClose: () => void;
}

const HotelPhotoModal: React.FC<HotelPhotoModalProps> = ({
  hotelName,
  images,
  onClose,
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);

  // Convert raw URL strings → PhotoCarousel-compatible shape
  const photos = images.map((url, i) => ({
    url,
    thumbnail_url: url,   // ADD — same URL works fine
    width: 0,             // ADD — not used by PhotoCarousel
    height: 0,            // ADD — not used by PhotoCarousel
    alt_text: `${hotelName} photo ${i + 1}`,
    source: 'hotel' as any,
    attribution: '',
  }));

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  return createPortal(
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      style={{ backgroundColor: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(8px)' }}
      role="dialog"
      aria-modal="true"
      aria-label={`Photos of ${hotelName}`}
    >
      <div
        className="relative w-full max-w-2xl bg-[#111827] rounded-2xl border border-[rgba(148,163,184,0.15)] shadow-2xl animate-fade-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[rgba(148,163,184,0.1)]">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 rounded-lg bg-[#F59E0B]/10 border border-[#F59E0B]/20 flex-shrink-0">
              <Images className="w-4 h-4 text-[#F59E0B]" />
            </div>
            <div className="min-w-0">
              <h2 className="text-white font-semibold text-base truncate">{hotelName}</h2>
              <span className="text-[#6B7280] text-xs">{images.length} photo{images.length !== 1 ? 's' : ''}</span>
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

        {/* Carousel */}
        <div className="p-5">
          <PhotoCarousel photos={photos} name={hotelName} />
        </div>

        {/* Footer */}
        <div className="px-5 pb-4 flex justify-center">
          <span className="text-xs text-[#6B7280]">📷 Photos via Google Hotels</span>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default HotelPhotoModal;
