/**
 * ImageCarousel Component
 * Netflix-style photo carousel with keyboard navigation
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight, ImageOff } from 'lucide-react';
import { type POIPhoto } from '../../types/local-discovery';

interface ImageCarouselProps {
  photos: POIPhoto[];
  poiName: string;
}

export const ImageCarousel: React.FC<ImageCarouselProps> = ({ photos, poiName }) => {
  const [currentIndex, setCurrentIndex]         = useState(0);
  const [imageLoaded, setImageLoaded]           = useState(false);
  const [imageError, setImageError]             = useState(false);
  const [isTransitioning, setIsTransitioning]   = useState(false);

  const total = photos.length;

  // Reset state when photos change
  useEffect(() => {
    setCurrentIndex(0);
    setImageLoaded(false);
    setImageError(false);
  }, [photos]);

  // Reset image state when index changes
  useEffect(() => {
    setImageLoaded(false);
    setImageError(false);
  }, [currentIndex]);

  const goTo = useCallback((index: number) => {
    if (isTransitioning || index === currentIndex) return;
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentIndex(index);
      setIsTransitioning(false);
    }, 150);
  }, [isTransitioning, currentIndex]);

  const goPrev = useCallback(() => {
    goTo(currentIndex === 0 ? total - 1 : currentIndex - 1);
  }, [currentIndex, total, goTo]);

  const goNext = useCallback(() => {
    goTo(currentIndex === total - 1 ? 0 : currentIndex + 1);
  }, [currentIndex, total, goTo]);

  // Keyboard navigation (handled here AND in modal — both work)
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft')  goPrev();
      if (e.key === 'ArrowRight') goNext();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [goPrev, goNext]);

  if (!photos || photos.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-[#111827] rounded-xl">
        <div className="text-center text-[#6B7280]">
          <ImageOff className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No photos available</p>
        </div>
      </div>
    );
  }

  const currentPhoto = photos[currentIndex];

  return (
    <div className="flex flex-col gap-3">

      {/* Main Image Container */}
      <div className="relative w-full bg-[#111827] rounded-xl overflow-hidden"
           style={{ aspectRatio: '16/9' }}>

        {/* Loading Skeleton */}
        {!imageLoaded && !imageError && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="absolute inset-0 bg-[#1F2937] animate-pulse" />
            <div className="relative z-10 flex flex-col items-center gap-2 text-[#6B7280]">
              <div className="w-8 h-8 border-2 border-[#38BDF8]/30 border-t-[#38BDF8] rounded-full animate-spin" />
              <span className="text-xs">Loading photo...</span>
            </div>
          </div>
        )}

        {/* Broken Image Fallback */}
        {imageError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-[#6B7280]">
            <ImageOff className="w-12 h-12 mb-2 opacity-40" />
            <p className="text-sm">Image unavailable</p>
          </div>
        )}

        {/* Actual Image */}
        <img
          key={currentPhoto.url}
          src={currentPhoto.url}
          alt={currentPhoto.alt_text || `${poiName} photo ${currentIndex + 1}`}
          onLoad={() => setImageLoaded(true)}
          onError={() => { setImageError(true); setImageLoaded(true); }}
          className={`
            w-full h-full object-cover transition-opacity duration-300
            ${imageLoaded && !imageError ? 'opacity-100' : 'opacity-0'}
            ${isTransitioning ? 'opacity-0' : ''}
          `}
        />

        {/* Image Counter — top right */}
        {total > 1 && (
          <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-sm text-white text-xs font-medium">
            {currentIndex + 1} / {total}
          </div>
        )}

        {/* Left Arrow */}
        {total > 1 && (
          <button
            onClick={goPrev}
            className="absolute left-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/60 backdrop-blur-sm text-white hover:bg-black/80 transition-all hover:scale-110 active:scale-95"
            aria-label="Previous photo"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        )}

        {/* Right Arrow */}
        {total > 1 && (
          <button
            onClick={goNext}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/60 backdrop-blur-sm text-white hover:bg-black/80 transition-all hover:scale-110 active:scale-95"
            aria-label="Next photo"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Pagination Dots */}
      {total > 1 && (
        <div className="flex items-center justify-center gap-1.5">
          {photos.map((_, index) => (
            <button
              key={index}
              onClick={() => goTo(index)}
              aria-label={`Go to photo ${index + 1}`}
              className={`rounded-full transition-all duration-300 ${
                index === currentIndex
                  ? 'w-6 h-2 bg-[#38BDF8]'
                  : 'w-2 h-2 bg-[#374151] hover:bg-[#6B7280]'
              }`}
            />
          ))}
        </div>
      )}

      {/* Attribution */}
      {currentPhoto.attribution && (
        <p className="text-center text-xs text-[#6B7280] px-4 truncate">
          {currentPhoto.attribution}
        </p>
      )}

    </div>
  );
};
