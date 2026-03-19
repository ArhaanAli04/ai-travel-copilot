/**
 * Geolocation utilities for Local Discovery
 * ✨ ENHANCED with better error handling
 */

import {type Location } from '../types/local-discovery';
import { ERROR_MESSAGES } from './error-messages';

export interface GeolocationResult {
  location: Location;
  city: string;
  error?: string;
}

/**
 * Get user's current location using browser API
 * ✨ ENHANCED with better error messages
 */
export const getCurrentLocation = (): Promise<GeolocationResult> => {
return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error(ERROR_MESSAGES.LOCATION_NOT_SUPPORTED));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const location: Location = {
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        };

        // Reverse geocode to get city name
        try {
          const city = await reverseGeocode(location);
          resolve({ location, city });
        } catch (error) {
          console.warn('Reverse geocoding failed, using default city');
          resolve({ location, city: 'mumbai' });
        }
      },
      (error) => {
        let errorMessage:string = ERROR_MESSAGES.LOCATION_UNAVAILABLE;
        
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = ERROR_MESSAGES.LOCATION_DENIED;
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = ERROR_MESSAGES.LOCATION_UNAVAILABLE;
            break;
          case error.TIMEOUT:
            errorMessage = ERROR_MESSAGES.LOCATION_TIMEOUT;
            break;
        }

        // ✨ NEW: Attach error code for better handling
        const err: any = new Error(errorMessage);
        err.code = error.code;
        reject(err);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000, // ✨ CHANGED: Increased from 5s to 10s
        maximumAge: 0,
      }
    );
  });
};

/**
 * Reverse geocode coordinates to city name
 * Using Nominatim API (free, no API key required)
 * ✨ ENHANCED with better fallback logic
 */
export const reverseGeocode = async (
  location: Location,
  retries: number = 2
): Promise<string> => {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${location.lat}&lon=${location.lon}&format=json`,
      {
        headers: {
          'User-Agent': 'AI-Travel-Copilot/1.0', // ✨ NEW: Required by Nominatim
        },
      }
    );

    if (!response.ok) {
      throw new Error('Reverse geocoding failed');
    }

    const data = await response.json();
    
    const city = 
      data.address?.city || 
      data.address?.town || 
      data.address?.village || 
      data.address?.state || 
      'mumbai';

    return city.toLowerCase();
  } catch (error) {
    console.error('Reverse geocoding error:', error);
    
    // ✨ NEW: Retry logic
    if (retries > 0) {
      console.log(`⏳ Retrying reverse geocoding... (${2 - retries + 1}/2)`);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return reverseGeocode(location, retries - 1);
    }
    
    return 'mumbai'; // Default fallback
  }
};

/**
 * Format location for display
 */
export const formatLocation = (location: Location): string => {
  return `${location.lat.toFixed(4)}°N, ${location.lon.toFixed(4)}°E`;
};

/**
 * Calculate distance between two locations (Haversine formula)
 */
export const calculateDistance = (loc1: Location, loc2: Location): number => {
  const R = 6371; // Earth's radius in km
  const dLat = toRad(loc2.lat - loc1.lat);
  const dLon = toRad(loc2.lon - loc1.lon);

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(loc1.lat)) *
      Math.cos(toRad(loc2.lat)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

const toRad = (degrees: number): number => {
  return (degrees * Math.PI) / 180;
};

/**
 * Mock location for development/testing
 */
export const MOCK_LOCATIONS = {
  mumbai: { lat: 19.0760, lon: 72.8777 },
  delhi: { lat: 28.6139, lon: 77.2090 },
  bangalore: { lat: 12.9716, lon: 77.5946 },
  kolkata: { lat: 22.5726, lon: 88.3639 },
};

/**
 * Get mock location for testing
 */
export const getMockLocation = (city: keyof typeof MOCK_LOCATIONS = 'mumbai'): GeolocationResult => {
  return {
    location: MOCK_LOCATIONS[city],
    city,
  };
};
