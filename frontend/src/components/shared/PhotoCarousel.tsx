/**
 * Shared PhotoCarousel Component
 * Reusable across Local Discovery (POI cards) and Planner (activity cards)
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight, ImageOff } from 'lucide-react';
import { type POIPhoto, type ActivityPhoto } from '../../types/local-discovery';

interface PhotoCarouselProps {
  photos: POIPhoto[] | ActivityPhoto[];
  name: string;
  compact?: boolean; // true = shorter height for activity cards
}

export const PhotoCarousel: React.FC<PhotoCarouselProps> = ({ photos, name, compact = false }) => {
  const [currentIndex, setCurrentIndex]       = useState(0);
  const [imageLoaded, setImageLoaded]         = useState(false);
  const [imageError, setImageError]           = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const total = photos.length;

  useEffect(() => {
    setCurrentIndex(0);
    setImageLoaded(false);
    setImageError(false);
  }, [photos]);

  useEffect(() => {
    setImageLoaded(false);
    setImageError(false);
  }, [currentIndex]);
  
  const goTo = useCallback((index: number) => {
  if (index === currentIndex) return;
  setIsTransitioning(true);
  setTimeout(() => {
    setCurrentIndex(index);
    setIsTransitioning(false);
  }, 150);
}, [currentIndex]);

  const goPrev = useCallback(() => goTo(currentIndex === 0 ? total - 1 : currentIndex - 1), [currentIndex, total, goTo]);
  const goNext = useCallback(() => goTo(currentIndex === total - 1 ? 0 : currentIndex + 1), [currentIndex, total, goTo]);

  useEffect(() => {
  if (total <= 1) return;
  const handleKey = (e: KeyboardEvent) => {
    if (e.key === 'ArrowLeft')  { e.stopPropagation(); goPrev(); }
    if (e.key === 'ArrowRight') { e.stopPropagation(); goNext(); }
  };
  window.addEventListener('keydown', handleKey);
  return () => window.removeEventListener('keydown', handleKey);
}, [goPrev, goNext, total]);

  if (!photos || photos.length === 0) {
    return (
      <div className={`flex items-center justify-center ${compact ? 'h-40' : 'h-64'} bg-[#111827] rounded-xl`}>
        <div className="text-center text-[#6B7280]">
          <ImageOff className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-xs">No photos available</p>
        </div>
      </div>
    );
  }

  const currentPhoto = photos[currentIndex];

  return (
    <div className="flex flex-col gap-2">
      {/* Main Image */}
      <div
        className={`relative w-full bg-[#111827] rounded-xl overflow-hidden ${compact ? 'h-44' : ''}`}
        style={compact ? undefined : { aspectRatio: '16/9' }}
      >
        {/* Loading Skeleton */}
        {!imageLoaded && !imageError && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="absolute inset-0 bg-[#1F2937] animate-pulse" />
            <div className="relative z-10 flex flex-col items-center gap-2 text-[#6B7280]">
              <div className="w-6 h-6 border-2 border-[#38BDF8]/30 border-t-[#38BDF8] rounded-full animate-spin" />
              <span className="text-xs">Loading...</span>
            </div>
          </div>
        )}

        {/* Error Fallback */}
        {imageError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-[#6B7280]">
            <ImageOff className="w-8 h-8 mb-1 opacity-40" />
            <p className="text-xs">Image unavailable</p>
          </div>
        )}

        {/* Image */}
        <img
          key={currentPhoto.url}
          src={currentPhoto.url}
          alt={currentPhoto.alt_text || `${name} photo ${currentIndex + 1}`}
          onLoad={() => setImageLoaded(true)}
          onError={() => { setImageError(true); setImageLoaded(true); }}
          className={`w-full h-full object-cover transition-opacity duration-300
            ${imageLoaded && !imageError ? 'opacity-100' : 'opacity-0'}
            ${isTransitioning ? 'opacity-0' : ''}`}
        />

        {/* Counter */}
        {total > 1 && (
          <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-sm text-white text-xs font-medium">
            {currentIndex + 1} / {total}
          </div>
        )}

        {/* Source badge */}
        {currentPhoto.source === 'google_images' && (
          <div className="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-sm text-white text-xs">
            📷 Google
          </div>
        )}

        {/* Arrows */}
        {total > 1 && (
          <>
            <button
              onClick={goPrev}
              className="absolute left-2 top-1/2 -translate-y-1/2 p-1.5 rounded-full bg-black/60 backdrop-blur-sm text-white hover:bg-black/80 transition-all hover:scale-110 active:scale-95"
              aria-label="Previous photo"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={goNext}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-full bg-black/60 backdrop-blur-sm text-white hover:bg-black/80 transition-all hover:scale-110 active:scale-95"
              aria-label="Next photo"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </>
        )}
      </div>

      {/* Dots */}
      {total > 1 && (
        <div className="flex items-center justify-center gap-1">
          {photos.map((_, index) => (
            <button
              key={index}
              onClick={() => goTo(index)}
              aria-label={`Go to photo ${index + 1}`}
              className={`rounded-full transition-all duration-300 ${
                index === currentIndex
                  ? 'w-5 h-1.5 bg-[#38BDF8]'
                  : 'w-1.5 h-1.5 bg-[#374151] hover:bg-[#6B7280]'
              }`}
            />
          ))}
        </div>
      )}

      {/* Attribution */}
      {currentPhoto.attribution && (
        <p className="text-center text-xs text-[#6B7280] px-2 truncate">
          {currentPhoto.attribution}
        </p>
      )}
    </div>
  );
};
