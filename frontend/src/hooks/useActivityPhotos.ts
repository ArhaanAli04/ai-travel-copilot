import { useState, useCallback,useRef } from 'react';
import { activityPhotosApi } from '../services/api';
import { type ActivityPhoto } from '../types/local-discovery';

export const useActivityPhotos = () => {
  const [photos, setPhotos]   = useState<ActivityPhoto[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [source, setSource]   = useState<string | null>(null);
  const fetchedRef = useRef(false);

  const fetchPhotos = useCallback(async (activityId: number) => {
    if (fetchedRef.current|| loading) return; // lazy: only fetch once per mount
    fetchedRef.current = true;
    setLoading(true);
    setError(null);
    try {
      const result = await activityPhotosApi.getPhotos(activityId);
      setPhotos(result.photos);
      setSource(result.source);
    } catch (err: any) {
      fetchedRef.current = false; // allow retry on error
      setError(err.message || 'Failed to load photos');
    } finally {
      setLoading(false);
    }
  }, []);

  return { photos, loading, error, source, fetchPhotos };
};
