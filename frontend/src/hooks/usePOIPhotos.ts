/**
 * Hook for fetching POI photos with lazy loading and in-memory cache
 */

import { useState, useCallback, useRef } from 'react';
import { getPOIPhotos } from '../services/local-discovery-api';
import { type POIPhoto } from '../types/local-discovery';

interface UsePOIPhotosReturn {
  photos: POIPhoto[];
  loading: boolean;
  error: string | null;
  source: 'wikimedia' | 'unsplash' | 'placeholder' | null;
  fetchPhotos: (poiId: string) => Promise<void>;
}

// Module-level cache so it persists across component mounts
const photoCache = new Map<string, {
  photos: POIPhoto[];
  source: 'wikimedia' | 'unsplash' | 'placeholder';
}>();

export const usePOIPhotos = (): UsePOIPhotosReturn => {
  const [photos, setPhotos]   = useState<POIPhoto[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [source, setSource]   = useState<'wikimedia' | 'unsplash' | 'placeholder' | null>(null);

  // Track in-flight requests to avoid duplicate calls
  const pendingRef = useRef<string | null>(null);

  const fetchPhotos = useCallback(async (poiId: string) => {
    // Already fetching this POI
    if (pendingRef.current === poiId) return;

    // Check frontend cache first
    if (photoCache.has(poiId)) {
      const cached = photoCache.get(poiId)!;
      setPhotos(cached.photos);
      setSource(cached.source);
      setError(null);
      return;
    }

    pendingRef.current = poiId;
    setLoading(true);
    setError(null);
    setPhotos([]);

    try {
      const result = await getPOIPhotos(poiId);

      // Filter out placeholder photos (empty URL)
      const validPhotos = result.photos.filter(p => p.url !== '');

      // Cache the result
      photoCache.set(poiId, {
        photos: validPhotos,
        source: result.source
      });

      setPhotos(validPhotos);
      setSource(result.source);
    } catch (err: any) {
      setError('Could not load photos. Please try again.');
      console.error('usePOIPhotos error:', err);
    } finally {
      setLoading(false);
      pendingRef.current = null;
    }
  }, []);

  return { photos, loading, error, source, fetchPhotos };
};
