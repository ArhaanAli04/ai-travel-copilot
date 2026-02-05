/**
 * Location Picker Modal - Allow user to select location on map
 */
import React, { useState } from 'react';
import { X, MapPin, Navigation } from 'lucide-react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface LocationPickerModalProps {
  currentLocation: { lat: number; lon: number };
  currentCity: string;
  onSelectLocation: (location: { lat: number; lon: number }, city: string) => void;
  onClose: () => void;
}

// Custom marker icon
const createMarkerIcon = () => {
  return L.divIcon({
    html: '<div style="background: #8B5CF6; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(236,72,153,0.5);"></div>',
    className: '',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
};

// Component to handle map clicks
const LocationSelector: React.FC<{
  onLocationSelect: (lat: number, lon: number) => void;
}> = ({ onLocationSelect }) => {
  useMapEvents({
    click: (e) => {
      onLocationSelect(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
};

export const LocationPickerModal: React.FC<LocationPickerModalProps> = ({
  currentLocation,
  currentCity,
  onSelectLocation,
  onClose,
}) => {
  const [selectedLocation, setSelectedLocation] = useState(currentLocation);
  const [cityName, setCityName] = useState(currentCity);
  const [isLoadingCity, setIsLoadingCity] = useState(false);

  // Reverse geocode to get city name
  const getCityFromCoordinates = async (lat: number, lon: number) => {
    setIsLoadingCity(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`
      );
      const data = await response.json();
      
      const city = data.address?.city || 
                   data.address?.town || 
                   data.address?.village || 
                   data.address?.county || 
                   'Unknown';
      
      setCityName(city);
    } catch (error) {
      console.error('Error getting city name:', error);
      setCityName('Unknown');
    } finally {
      setIsLoadingCity(false);
    }
  };

  const handleLocationSelect = (lat: number, lon: number) => {
    setSelectedLocation({ lat, lon });
    getCityFromCoordinates(lat, lon);
  };

  const handleUseCurrentLocation = () => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        handleLocationSelect(lat, lon);
      },
      (error) => {
        console.error('Error getting location:', error);
        alert('Could not get your current location');
      }
    );
  };

  const handleConfirm = () => {
    onSelectLocation(selectedLocation, cityName);
    onClose();
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.7)' }}
      onClick={onClose}
    >
      <div 
        className="bg-[#0a0e14] rounded-xl shadow-2xl border border-[rgba(148,163,184,0.2)] w-full max-w-3xl mx-4 max-h-[90vh] flex flex-col animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(148,163,184,0.2)]">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-[#8B5CF6]" />
            <h2 className="text-lg font-semibold text-white">Select Location</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/5 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-[#9CA3AF]" />
          </button>
        </div>

        {/* Map */}
        <div className="flex-1 relative">
          <MapContainer
            center={[selectedLocation.lat, selectedLocation.lon]}
            zoom={13}
            style={{ height: '400px', width: '100%' }}
            scrollWheelZoom={true}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <Marker
              position={[selectedLocation.lat, selectedLocation.lon]}
              icon={createMarkerIcon()}
            />
            <LocationSelector onLocationSelect={handleLocationSelect} />
          </MapContainer>

          {/* Use Current Location Button */}
          <button
            onClick={handleUseCurrentLocation}
            className="absolute top-4 right-4 z-[1000] bg-[#1F2937] border border-[rgba(148,163,184,0.2)] px-4 py-2 rounded-lg shadow-lg hover:bg-[#1F2937]/80 transition-all flex items-center gap-2"
          >
            <Navigation className="w-4 h-4 text-[#8B5CF6]" />
            <span className="text-sm font-medium text-white">Use My Location</span>
          </button>

          {/* Info Box */}
          <div className="absolute bottom-4 left-4 right-4 z-[1000] bg-[#1F2937] border border-[rgba(148,163,184,0.2)] rounded-lg shadow-lg p-4">
            <p className="text-sm text-[#9CA3AF] mb-2">
              Click anywhere on the map to select a location
            </p>
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-[#8B5CF6]" />
              <div>
                <div className="text-sm font-medium text-white">
                  {isLoadingCity ? 'Loading...' : cityName}
                </div>
                <div className="text-xs text-[#6B7280]">
                  {selectedLocation.lat.toFixed(4)}, {selectedLocation.lon.toFixed(4)}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 px-6 py-4 border-t border-[rgba(148,163,184,0.2)] bg-[#0a0e14]/50">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-[#1F2937] border border-[rgba(148,163,184,0.2)] text-white rounded-lg hover:bg-[#1F2937]/70 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={isLoadingCity}
            className="flex-1 px-4 py-2 bg-[#8B5CF6] text-white rounded-lg hover:bg-[#7C3AED] transition-colors shadow-lg hover:shadow-[#8B5CF6]/20"
          >
            Confirm Location
          </button>
        </div>
      </div>
    </div>
  );
};
