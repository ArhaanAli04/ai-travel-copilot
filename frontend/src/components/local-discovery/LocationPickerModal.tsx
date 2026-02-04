/**
 * Location Picker Modal - Allow user to select location on map
 */
import React, { useState, useEffect } from 'react';
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
    html: '<div style="background: #2563eb; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
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
    <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm"
  style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
  onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl mx-4 max-h-[90vh] flex flex-col"
      onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Select Location</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
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
            className="absolute top-4 right-4 z-[1000] bg-white px-4 py-2 rounded-lg shadow-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <Navigation className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium">Use My Location</span>
          </button>

          {/* Info Box */}
          <div className="absolute bottom-4 left-4 right-4 z-[1000] bg-white rounded-lg shadow-lg p-4">
            <p className="text-sm text-gray-600 mb-2">
              Click anywhere on the map to select a location
            </p>
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-600" />
              <div>
                <div className="text-sm font-medium text-gray-900">
                  {isLoadingCity ? 'Loading...' : cityName}
                </div>
                <div className="text-xs text-gray-500">
                  {selectedLocation.lat.toFixed(4)}, {selectedLocation.lon.toFixed(4)}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 px-6 py-4 border-t bg-gray-50 rounded-b-xl">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={isLoadingCity}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Confirm Location
          </button>
        </div>
      </div>
    </div>
  );
};
